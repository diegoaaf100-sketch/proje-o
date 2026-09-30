import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dashboard de Efetivo",
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

    # Normalizar nomes das colunas
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ", regex=False)
        .str.strip()
    )

    # Renomear colunas
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

    # Converter campos numéricos
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

    # Criar anos a partir dos dias, caso necessário
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

st.title("📊 Dashboard de Efetivo")

st.caption(
    "Dados atualizados diretamente da planilha Google Sheets."
)


# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("🔎 Filtros")


# ------------------------------------------------------------
# Posto / Graduação
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Ano de Requerimento
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Ano de Compulsória
# ------------------------------------------------------------

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
# TABELA
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
    "Projeção do efetivo entre 2026 e 2035, considerando "
    "saídas por requerimento ou compulsória e novas entradas "
    "conforme cada cenário."
)


# ============================================================
# PARÂMETROS
# ============================================================

ANO_INICIAL = 2026
ANO_FINAL = 2035

NOVOS_P1 = 300
NOVOS_P2 = 260
NOVOS_P3 = 300
NOVOS_P4 = 260

anos = list(
    range(
        ANO_INICIAL,
        ANO_FINAL + 1
    )
)


# ============================================================
# EFETIVO INICIAL
# ============================================================

# A projeção utiliza o total da planilha,
# independentemente dos filtros selecionados.

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

    efetivo_atual = efetivo_inicial

    for ano in anos:

        # ----------------------------------------------------
        # SAÍDAS
        # ----------------------------------------------------

        if tipo_saida == "requerimento":

            saidas = saidas_requerimento[ano]

        else:

            saidas = saidas_compulsoria[ano]


        # ----------------------------------------------------
        # ENTRADAS
        # ----------------------------------------------------

        entradas = novas_entradas


        # ----------------------------------------------------
        # SALDO DO ANO
        # ----------------------------------------------------

        saldo = entradas - saidas


        # ----------------------------------------------------
        # EFETIVO PROJETADO
        # ----------------------------------------------------

        efetivo_projetado = (
            efetivo_atual + saldo
        )


        # ----------------------------------------------------
        # REGISTRAR ANO
        # ----------------------------------------------------

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


        # Próximo ano começa com o efetivo projetado
        efetivo_atual = efetivo_projetado


    return pd.DataFrame(linhas)


# ============================================================
# CONSTRUIR OS QUATRO CENÁRIOS
# ============================================================

df_p1 = construir_cenario(
    "requerimento",
    NOVOS_P1
)


df_p2 = construir_cenario(
    "requerimento",
    NOVOS_P2
)


df_p3 = construir_cenario(
    "compulsoria",
    NOVOS_P3
)


df_p4 = construir_cenario(
    "compulsoria",
    NOVOS_P4
)


# ============================================================
# INDICADORES DO PLANEJAMENTO
# ============================================================

st.subheader("📌 Indicadores do Planejamento")


total_saidas_req = sum(
    saidas_requerimento.values()
)


total_saidas_comp = sum(
    saidas_compulsoria.values()
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Efetivo inicial",
        f"{efetivo_inicial:,}".replace(",", ".")
    )


with c2:

    st.metric(
        "Saídas por requerimento",
        f"{total_saidas_req:,}".replace(",", ".")
    )


with c3:

    st.metric(
        "Saídas por compulsória",
        f"{total_saidas_comp:,}".replace(",", ".")
    )


with c4:

    st.metric(
        "Período",
        f"{ANO_INICIAL}–{ANO_FINAL}"
    )


# ============================================================
# CENÁRIOS
# ============================================================

st.subheader("📈 Cenários de Planejamento")


p1_final = int(
    df_p1.iloc[-1]["Efetivo projetado"]
)

p2_final = int(
    df_p2.iloc[-1]["Efetivo projetado"]
)

p3_final = int(
    df_p3.iloc[-1]["Efetivo projetado"]
)

p4_final = int(
    df_p4.iloc[-1]["Efetivo projetado"]
)


var_p1 = p1_final - efetivo_inicial
var_p2 = p2_final - efetivo_inicial
var_p3 = p3_final - efetivo_inicial
var_p4 = p4_final - efetivo_inicial


s1, s2, s3, s4 = st.columns(4)


with s1:

    st.metric(
        "P1 — Requerimento +300",
        f"{p1_final:,}".replace(",", "."),
        f"{var_p1:+,}".replace(",", ".")
    )


with s2:

    st.metric(
        "P2 — Requerimento +260",
        f"{p2_final:,}".replace(",", "."),
        f"{var_p2:+,}".replace(",", ".")
    )


with s3:

    st.metric(
        "P3 — Compulsória +300",
        f"{p3_final:,}".replace(",", "."),
        f"{var_p3:+,}".replace(",", ".")
    )


with s4:

    st.metric(
        "P4 — Compulsória +260",
        f"{p4_final:,}".replace(",", "."),
        f"{var_p4:+,}".replace(",", ".")
    )


# ============================================================
# PLANEJAMENTO ANUAL POR CENÁRIO
# ============================================================

st.subheader("📋 Planejamento Anual")


tab1, tab2, tab3, tab4 = st.tabs([
    "P1 — Requerimento +300",
    "P2 — Requerimento +260",
    "P3 — Compulsória +300",
    "P4 — Compulsória +260"
])


# ============================================================
# P1
# ============================================================

with tab1:

    st.markdown(
        "**Regra:** saídas por ano de requerimento "
        "+ 300 novos efetivos."
    )

    st.dataframe(
        df_p1,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# P2
# ============================================================

with tab2:

    st.markdown(
        "**Regra:** saídas por ano de requerimento "
        "+ 260 novos efetivos."
    )

    st.dataframe(
        df_p2,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# P3
# ============================================================

with tab3:

    st.markdown(
        "**Regra:** saídas por ano de compulsória "
        "+ 300 novos efetivos."
    )

    st.dataframe(
        df_p3,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# P4
# ============================================================

with tab4:

    st.markdown(
        "**Regra:** saídas por ano de compulsória "
        "+ 260 novos efetivos."
    )

    st.dataframe(
        df_p4,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# COMPARAÇÃO DOS CENÁRIOS
# ============================================================

st.subheader("📊 Comparação dos Cenários")


df_comparacao = pd.DataFrame({

    "Ano": anos,

    "P1 — Req. +300":
        df_p1["Efetivo projetado"].values,

    "P2 — Req. +260":
        df_p2["Efetivo projetado"].values,

    "P3 — Comp. +300":
        df_p3["Efetivo projetado"].values,

    "P4 — Comp. +260":
        df_p4["Efetivo projetado"].values

})


st.line_chart(
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
# RESUMO PARA 2035
# ============================================================

st.subheader("🎯 Situação Projetada para 2035")


r1, r2, r3, r4 = st.columns(4)


with r1:

    st.markdown("### P1")

    st.metric(
        "Efetivo em 2035",
        f"{p1_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação: {var_p1:+,}".replace(",", ".")
    )


with r2:

    st.markdown("### P2")

    st.metric(
        "Efetivo em 2035",
        f"{p2_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação: {var_p2:+,}".replace(",", ".")
    )


with r3:

    st.markdown("### P3")

    st.metric(
        "Efetivo em 2035",
        f"{p3_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação: {var_p3:+,}".replace(",", ".")
    )


with r4:

    st.markdown("### P4")

    st.metric(
        "Efetivo em 2035",
        f"{p4_final:,}".replace(",", ".")
    )

    st.caption(
        f"Variação: {var_p4:+,}".replace(",", ".")
    )


# ============================================================
# RESUMO GERENCIAL
# ============================================================

st.subheader("📌 Resumo Gerencial")


resumo_gerencial = pd.DataFrame({

    "Cenário": [
        "P1 — Requerimento +300",
        "P2 — Requerimento +260",
        "P3 — Compulsória +300",
        "P4 — Compulsória +260"
    ],

    "Efetivo Inicial": [
        efetivo_inicial,
        efetivo_inicial,
        efetivo_inicial,
        efetivo_inicial
    ],

    "Saídas Acumuladas": [
        int(df_p1["Saídas"].sum()),
        int(df_p2["Saídas"].sum()),
        int(df_p3["Saídas"].sum()),
        int(df_p4["Saídas"].sum())
    ],

    "Entradas Acumuladas": [
        int(df_p1["Entradas"].sum()),
        int(df_p2["Entradas"].sum()),
        int(df_p3["Entradas"].sum()),
        int(df_p4["Entradas"].sum())
    ],

    "Saldo Acumulado": [
        int(df_p1["Saldo do ano"].sum()),
        int(df_p2["Saldo do ano"].sum()),
        int(df_p3["Saldo do ano"].sum()),
        int(df_p4["Saldo do ano"].sum())
    ],

    "Efetivo Projetado 2035": [
        p1_final,
        p2_final,
        p3_final,
        p4_final
    ]

})


st.dataframe(
    resumo_gerencial,
    use_container_width=True,
    hide_index=True
)
