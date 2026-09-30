import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Projeção do Efetivo",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# CONEXÃO COM GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=300)
def carregar_dados():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        st.secrets["spreadsheet_id"]
    )

    worksheet = spreadsheet.worksheet("Página4")

    dados = worksheet.get_all_records()

    df = pd.DataFrame(dados)

    # ========================================================
    # NORMALIZAR NOMES DAS COLUNAS
    # ========================================================

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ", regex=False)
        .str.strip()
    )

    # ========================================================
    # RENOMEAR COLUNAS
    # ========================================================

    mapa_colunas = {
        "Nº": "numero",
        "Matrícula": "matricula",
        "Posto / Graduação": "posto_graduacao",
        "Nome": "nome",
        "Reserva Requerimento": "reserva_requerimento",
        "Reserva Compulsória": "reserva_compulsoria",
        "Anos para Requerimento": "anos_requerimento",
        "Anos para Compulsória": "anos_compulsoria",
        "Dias para Requerimento": "dias_requerimento",
        "Dias para Compulsória": "dias_compulsoria",
        "Ano de Requerimento": "ano_requerimento",
        "Ano de Compulsória": "ano_compulsoria"
    }

    df = df.rename(columns=mapa_colunas)

    # ========================================================
    # CONVERTER CAMPOS NUMÉRICOS
    # ========================================================

    colunas_numericas = [
        "numero",
        "anos_requerimento",
        "anos_compulsoria",
        "dias_requerimento",
        "dias_compulsoria",
        "ano_requerimento",
        "ano_compulsoria"
    ]

    for coluna in colunas_numericas:

        if coluna in df.columns:

            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

    # ========================================================
    # CRIAR ANOS A PARTIR DOS DIAS, CASO NECESSÁRIO
    # ========================================================

    if (
        "anos_requerimento" not in df.columns
        and "dias_requerimento" in df.columns
    ):

        df["anos_requerimento"] = (
            df["dias_requerimento"] / 365.25
        )

    if (
        "anos_compulsoria" not in df.columns
        and "dias_compulsoria" in df.columns
    ):

        df["anos_compulsoria"] = (
            df["dias_compulsoria"] / 365.25
        )

    return df


# ============================================================
# CARREGAR DADOS
# ============================================================

try:

    df = carregar_dados()

except Exception as e:

    st.error(
        "Não foi possível carregar os dados da planilha."
    )

    st.exception(e)

    st.stop()


# ============================================================
# TÍTULO
# ============================================================

st.title("📊 Projeção do Efetivo")

st.caption(
    "Dados atualizados diretamente da planilha Google Sheets."
)


# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("🔎 Filtros")


# ============================================================
# FILTRO — POSTO / GRADUAÇÃO
# ============================================================

postos = sorted(
    df["posto_graduacao"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

filtro_posto = st.sidebar.selectbox(
    "Posto / Graduação",
    ["Todos"] + postos
)


# ============================================================
# FILTRO — ANO DE REQUERIMENTO
# ============================================================

anos_requerimento = sorted(
    df["ano_requerimento"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

filtro_ano_requerimento = st.sidebar.selectbox(
    "Ano de Requerimento",
    ["Todos"] + anos_requerimento
)


# ============================================================
# FILTRO — ANO DE COMPULSÓRIA
# ============================================================

anos_compulsoria = sorted(
    df["ano_compulsoria"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

filtro_ano_compulsoria = st.sidebar.selectbox(
    "Ano de Compulsória",
    ["Todos"] + anos_compulsoria
)


# ============================================================
# APLICAR FILTROS
# ============================================================

resultado = df.copy()


if filtro_posto != "Todos":

    resultado = resultado[
        resultado["posto_graduacao"] == filtro_posto
    ]


if filtro_ano_requerimento != "Todos":

    resultado = resultado[
        resultado["ano_requerimento"] == filtro_ano_requerimento
    ]


if filtro_ano_compulsoria != "Todos":

    resultado = resultado[
        resultado["ano_compulsoria"] == filtro_ano_compulsoria
    ]


# ============================================================
# INDICADORES
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total de registros",
        len(resultado)
    )


with col2:

    quantidade = (
        resultado["anos_requerimento"]
        .le(1)
        .sum()
    )

    st.metric(
        "Requerimento ≤ 1 ano",
        int(quantidade)
    )


with col3:

    quantidade = (
        resultado["anos_requerimento"]
        .le(5)
        .sum()
    )

    st.metric(
        "Requerimento ≤ 5 anos",
        int(quantidade)
    )


with col4:

    quantidade = (
        resultado["anos_compulsoria"]
        .le(5)
        .sum()
    )

    st.metric(
        "Compulsória ≤ 5 anos",
        int(quantidade)
    )


# ============================================================
# TABELA DE DADOS
# ============================================================

st.divider()

st.subheader("👥 Dados")


colunas_exibicao = [
    "numero",
    "matricula",
    "posto_graduacao",
    "nome",
    "anos_requerimento",
    "anos_compulsoria",
    "ano_requerimento",
    "ano_compulsoria"
]


st.dataframe(
    resultado[colunas_exibicao],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PAINEL DE PLANEJAMENTO
# ============================================================

st.divider()

st.header("📊 Painel de Planejamento de Efetivo")

st.caption(
    "Projeção do efetivo entre 2026 e 2035. "
    "O ano de 2026 representa o efetivo atual da planilha. "
    "As alterações começam a partir de 2027."
)


# ============================================================
# PARÂMETROS DOS CENÁRIOS
# ============================================================

ANO_INICIAL = 2026
ANO_FINAL = 2035

NOVOS_CENARIO_01 = 300
NOVOS_CENARIO_02 = 260
NOVOS_CENARIO_03 = 300
NOVOS_CENARIO_04 = 260

anos = list(
    range(
        ANO_INICIAL,
        ANO_FINAL + 1
    )
)


# ============================================================
# EFETIVO INICIAL
# ============================================================

# O efetivo inicial corresponde ao total de registros
# existentes na planilha.
#
# Esse valor representa o efetivo de 2026.
#
# A projeção não sofre influência dos filtros.

efetivo_inicial = len(df)


# ============================================================
# SAÍDAS POR ANO
# ============================================================

saidas_requerimento = {
    ano: int(
        df["ano_requerimento"].eq(ano).sum()
    )
    for ano in anos
}


saidas_compulsoria = {
    ano: int(
        df["ano_compulsoria"].eq(ano).sum()
    )
    for ano in anos
}


# ============================================================
# FUNÇÃO PARA CONSTRUIR CENÁRIO
# ============================================================

def construir_cenario(
    tipo_saida,
    novas_entradas
):

    linhas = []

    # O efetivo atual da planilha será o efetivo de 2026.
    efetivo_atual = efetivo_inicial

    for ano in anos:

        # ====================================================
        # 2026 — MANTER O EFETIVO ATUAL
        # ====================================================

        if ano == ANO_INICIAL:

            linhas.append({

                "Ano": ano,

                "Efetivo inicial":
                    efetivo_atual,

                "Saídas":
                    0,

                "Entradas":
                    0,

                "Saldo do ano":
                    0,

                "Efetivo projetado":
                    efetivo_atual

            })

            continue


        # ====================================================
        # A PARTIR DE 2027 — APLICAR PROJEÇÃO
        # ====================================================

        if tipo_saida == "requerimento":

            saidas = saidas_requerimento[ano]

        else:

            saidas = saidas_compulsoria[ano]


        # ====================================================
        # ENTRADAS
        # ====================================================

        entradas = novas_entradas


        # ====================================================
        # SALDO DO ANO
        # ====================================================

        saldo = entradas - saidas


        # ====================================================
        # EFETIVO PROJETADO
        # ====================================================

        efetivo_projetado = (
            efetivo_atual + saldo
        )


        # ====================================================
        # REGISTRAR ANO
        # ====================================================

        linhas.append({

            "Ano": ano,

            "Efetivo inicial":
                efetivo_atual,

            "Saídas":
                saidas,

            "Entradas":
                entradas,

            "Saldo do ano":
                saldo,

            "Efetivo projetado":
                efetivo_projetado

        })


        # ====================================================
        # PRÓXIMO ANO
        # ====================================================

        efetivo_atual = efetivo_projetado


    return pd.DataFrame(linhas)


# ============================================================
# CONSTRUIR OS 4 CENÁRIOS
# ============================================================

df_cenario_01 = construir_cenario(
    "requerimento",
    NOVOS_CENARIO_01
)


df_cenario_02 = construir_cenario(
    "requerimento",
    NOVOS_CENARIO_02
)


df_cenario_03 = construir_cenario(
    "compulsoria",
    NOVOS_CENARIO_03
)


df_cenario_04 = construir_cenario(
    "compulsoria",
    NOVOS_CENARIO_04
)


# ============================================================
# INDICADORES DO PLANEJAMENTO
# ============================================================

st.subheader("📌 Indicadores do Planejamento")


# As saídas do planejamento são consideradas somente
# a partir de 2027.

total_saidas_requerimento = sum(
    df_cenario_01["Saídas"]
)


total_saidas_compulsoria = sum(
    df_cenario_03["Saídas"]
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Efetivo inicial — 2026",
        f"{efetivo_inicial:,}".replace(",", ".")
    )


with c2:

    st.metric(
        "Saídas por requerimento",
        f"{total_saidas_requerimento:,}".replace(",", ".")
    )


with c3:

    st.metric(
        "Saídas por compulsória",
        f"{total_saidas_compulsoria:,}".replace(",", ".")
    )


with c4:

    st.metric(
        "Período",
        f"{ANO_INICIAL}–{ANO_FINAL}"
    )


# ============================================================
# RESULTADOS DOS CENÁRIOS
# ============================================================

st.subheader("📈 Cenários de Planejamento")


cenario_01_final = int(
    df_cenario_01.iloc[-1]["Efetivo projetado"]
)

cenario_02_final = int(
    df_cenario_02.iloc[-1]["Efetivo projetado"]
)

cenario_03_final = int(
    df_cenario_03.iloc[-1]["Efetivo projetado"]
)

cenario_04_final = int(
    df_cenario_04.iloc[-1]["Efetivo projetado"]
)


variacao_cenario_01 = (
    cenario_01_final - efetivo_inicial
)

variacao_cenario_02 = (
    cenario_02_final - efetivo_inicial
)

variacao_cenario_03 = (
    cenario_03_final - efetivo_inicial
)

variacao_cenario_04 = (
    cenario_04_final - efetivo_inicial
)


s1, s2, s3, s4 = st.columns(4)


with s1:

    st.metric(
        "Cenário 01 — Requerimento +300",
        f"{cenario_01_final:,}".replace(",", "."),
        f"{variacao_cenario_01:+,}".replace(",", ".")
    )


with s2:

    st.metric(
        "Cenário 02 — Requerimento +260",
        f"{cenario_02_final:,}".replace(",", "."),
        f"{variacao_cenario_02:+,}".replace(",", ".")
    )


with s3:

    st.metric(
        "Cenário 03 — Compulsória +300",
        f"{cenario_03_final:,}".replace(",", "."),
        f"{variacao_cenario_03:+,}".replace(",", ".")
    )


with s4:

    st.metric(
        "Cenário 04 — Compulsória +260",
        f"{cenario_04_final:,}".replace(",", "."),
        f"{variacao_cenario_04:+,}".replace(",", ".")
    )


# ============================================================
# PLANEJAMENTO ANUAL
# ============================================================

st.subheader("📋 Planejamento Anual por Cenário")


tab1, tab2, tab3, tab4 = st.tabs([
    "Cenário 01",
    "Cenário 02",
    "Cenário 03",
    "Cenário 04"
])


# ============================================================
# CENÁRIO 01
# ============================================================

with tab1:

    st.markdown(
        """
        ### Cenário 01 — Requerimento +300

        **2026:** mantém o efetivo atual.

        **A partir de 2027:** saem os servidores que atingirem
        o ano de requerimento e entram 300 novos efetivos por ano.
        """
    )

    st.dataframe(
        df_cenario_01,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CENÁRIO 02
# ============================================================

with tab2:

    st.markdown(
        """
        ### Cenário 02 — Requerimento +260

        **2026:** mantém o efetivo atual.

        **A partir de 2027:** saem os servidores que atingirem
        o ano de requerimento e entram 260 novos efetivos por ano.
        """
    )

    st.dataframe(
        df_cenario_02,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CENÁRIO 03
# ============================================================

with tab3:

    st.markdown(
        """
        ### Cenário 03 — Compulsória +300

        **2026:** mantém o efetivo atual.

        **A partir de 2027:** saem os servidores que atingirem
        o ano de compulsória e entram 300 novos efetivos por ano.
        """
    )

    st.dataframe(
        df_cenario_03,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CENÁRIO 04
# ============================================================

with tab4:

    st.markdown(
        """
        ### Cenário 04 — Compulsória +260

        **2026:** mantém o efetivo atual.

        **A partir de 2027:** saem os servidores que atingirem
        o ano de compulsória e entram 260 novos efetivos por ano.
        """
    )

    st.dataframe(
        df_cenario_04,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# COMPARAÇÃO DOS CENÁRIOS
# ============================================================

st.subheader("📊 Comparação dos Cenários")


df_comparacao = pd.DataFrame({

    "Ano": anos,

    "Cenário 01 — Req. +300":
        df_cenario_01["Efetivo projetado"].values,

    "Cenário 02 — Req. +260":
        df_cenario_02["Efetivo projetado"].values,

    "Cenário 03 — Comp. +300":
        df_cenario_03["Efetivo projetado"].values,

    "Cenário 04 — Comp. +260":
        df_cenario_04["Efetivo projetado"].values

})


# ============================================================
# GRÁFICO DE BARRAS
# ============================================================

st.bar_chart(
    df_comparacao.set_index("Ano")
)


# ============================================================
# TABELA CONSOLIDADA
# ============================================================

st.subheader("📋 Tabela Consolidada")


st.dataframe(
    df_comparacao,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# RESUMO — 2035
# ============================================================

st.subheader("🎯 Situação Projetada para 2035")


r1, r2, r3, r4 = st.columns(4)


with r1:

    st.markdown("### Cenário 01")

    st.metric(
        "Efetivo em 2035",
        f"{cenario_01_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação desde 2026: "
        f"{variacao_cenario_01:+,}".replace(",", ".")
    )


with r2:

    st.markdown("### Cenário 02")

    st.metric(
        "Efetivo em 2035",
        f"{cenario_02_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação desde 2026: "
        f"{variacao_cenario_02:+,}".replace(",", ".")
    )


with r3:

    st.markdown("### Cenário 03")

    st.metric(
        "Efetivo em 2035",
        f"{cenario_03_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação desde 2026: "
        f"{variacao_cenario_03:+,}".replace(",", ".")
    )


with r4:

    st.markdown("### Cenário 04")

    st.metric(
        "Efetivo em 2035",
        f"{cenario_04_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação desde 2026: "
        f"{variacao_cenario_04:+,}".replace(",", ".")
    )


# ============================================================
# RESUMO GERENCIAL
# ============================================================

st.subheader("📌 Resumo Gerencial")


resumo_gerencial = pd.DataFrame({

    "Cenário": [

        "Cenário 01 — Requerimento +300",

        "Cenário 02 — Requerimento +260",

        "Cenário 03 — Compulsória +300",

        "Cenário 04 — Compulsória +260"

    ],

    "Efetivo Inicial — 2026": [

        efetivo_inicial,

        efetivo_inicial,

        efetivo_inicial,

        efetivo_inicial

    ],

    "Saídas Acumuladas": [

        int(
            df_cenario_01["Saídas"].sum()
        ),

        int(
            df_cenario_02["Saídas"].sum()
        ),

        int(
            df_cenario_03["Saídas"].sum()
        ),

        int(
            df_cenario_04["Saídas"].sum()
        )

    ],

    "Entradas Acumuladas": [

        int(
            df_cenario_01["Entradas"].sum()
        ),

        int(
            df_cenario_02["Entradas"].sum()
        ),

        int(
            df_cenario_03["Entradas"].sum()
        ),

        int(
            df_cenario_04["Entradas"].sum()
        )

    ],

    "Saldo Acumulado": [

        int(
            df_cenario_01["Saldo do ano"].sum()
        ),

        int(
            df_cenario_02["Saldo do ano"].sum()
        ),

        int(
            df_cenario_03["Saldo do ano"].sum()
        ),

        int(
            df_cenario_04["Saldo do ano"].sum()
        )

    ],

    "Efetivo Projetado 2035": [

        cenario_01_final,

        cenario_02_final,

        cenario_03_final,

        cenario_04_final

    ]

})


st.dataframe(
    resumo_gerencial,
    use_container_width=True,
    hide_index=True
)
