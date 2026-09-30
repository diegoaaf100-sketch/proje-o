import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Planejamento de Efetivo",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# CARREGAMENTO DOS DADOS
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

    # --------------------------------------------------------
    # Limpeza dos nomes das colunas
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ", regex=False)
        .str.strip()
    )

    # --------------------------------------------------------
    # Mapeamento das colunas da planilha
    #
    # IMPORTANTE:
    # A planilha agora possui DIAS, e não ANOS.
    # --------------------------------------------------------

    mapa_colunas = {

        "Nº": "numero",

        "Matrícula": "matricula",

        "Posto / Graduação": "posto_graduacao",

        "Nome": "nome",

        "Reserva Requerimento": "reserva_requerimento",

        "Reserva Compulsória": "reserva_compulsoria",

        "Dias para Requerimento": "dias_requerimento",

        "Dias para Compulsória": "dias_compulsoria",

        "Ano de Requerimento": "ano_requerimento",

        "Ano de Compulsória": "ano_compulsoria"
    }

    df = df.rename(columns=mapa_colunas)

    # --------------------------------------------------------
    # Substitui None por NA
    # --------------------------------------------------------

    df = df.replace({None: pd.NA})

    # --------------------------------------------------------
    # Conversão das colunas numéricas
    # --------------------------------------------------------

    colunas_numericas = [

        "numero",

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

    # --------------------------------------------------------
    # CÁLCULO DOS ANOS A PARTIR DOS DIAS
    #
    # 365,25 dias = 1 ano
    # --------------------------------------------------------

    if "dias_requerimento" in df.columns:

        df["anos_requerimento"] = (
            df["dias_requerimento"] / 365.25
        )

    else:

        df["anos_requerimento"] = pd.NA


    if "dias_compulsoria" in df.columns:

        df["anos_compulsoria"] = (
            df["dias_compulsoria"] / 365.25
        )

    else:

        df["anos_compulsoria"] = pd.NA

    # --------------------------------------------------------
    # CLASSIFICAÇÃO OFICIAIS / PRAÇAS
    # --------------------------------------------------------

    postos_oficiais = [

        "cel",

        "tem cel",

        "maj qoc",

        "maj qoa",

        "cap qoa",

        "cap qoc",

        "1° ten qoc",

        "1° ten qoa",

        "2° ten qoc",

        "2° ten qoa",

        "aspirante"
    ]

    def normalizar_posto(valor):

        if pd.isna(valor):

            return ""

        texto = str(valor).strip()

        # Padroniza ordinal
        texto = texto.replace("º", "°")

        # Remove espaços duplicados
        texto = " ".join(texto.split())

        return texto.lower()


    def classificar_grupo(valor):

        posto = normalizar_posto(valor)

        if posto in postos_oficiais:

            return "Oficiais"

        return "Praças"


    if "posto_graduacao" in df.columns:

        df["grupo"] = df["posto_graduacao"].apply(
            classificar_grupo
        )

    else:

        df["grupo"] = "Praças"

    return df


# ============================================================
# CARREGA OS DADOS
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

st.html(
    """
    <div style="
        text-align:center;
        margin-top:10px;
        margin-bottom:20px;
    ">
        <h1>📊 Planejamento de Efetivo</h1>
    </div>
    """
)

st.caption(
    "Painel de acompanhamento e projeção do efetivo"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filtros")


# ------------------------------------------------------------
# GRUPO
# ------------------------------------------------------------

filtro_grupo = st.sidebar.selectbox(

    "Grupo",

    [
        "Todos",
        "Oficiais",
        "Praças"
    ]
)


# ------------------------------------------------------------
# POSTO / GRADUAÇÃO
# ------------------------------------------------------------

postos = sorted(

    df["posto_graduacao"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


filtro_posto = st.sidebar.multiselect(

    "Posto / Graduação",

    options=postos
)


# ------------------------------------------------------------
# ANO DE REQUERIMENTO
# ------------------------------------------------------------

anos_requerimento = sorted(

    df["ano_requerimento"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)


filtro_ano_requerimento = st.sidebar.multiselect(

    "Ano de Requerimento",

    options=anos_requerimento
)


# ------------------------------------------------------------
# ANO DE COMPULSÓRIA
# ------------------------------------------------------------

anos_compulsoria = sorted(

    df["ano_compulsoria"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)


filtro_ano_compulsoria = st.sidebar.multiselect(

    "Ano de Compulsória",

    options=anos_compulsoria
)


# ============================================================
# FILTRAGEM DA TABELA
# ============================================================

resultado = df.copy()


# ------------------------------------------------------------
# FILTRO GRUPO
# ------------------------------------------------------------

if filtro_grupo != "Todos":

    resultado = resultado[
        resultado["grupo"] == filtro_grupo
    ]


# ------------------------------------------------------------
# FILTRO POSTO
# ------------------------------------------------------------

if filtro_posto:

    resultado = resultado[
        resultado["posto_graduacao"].isin(
            filtro_posto
        )
    ]


# ------------------------------------------------------------
# FILTRO ANO REQUERIMENTO
# ------------------------------------------------------------

if filtro_ano_requerimento:

    resultado = resultado[
        resultado["ano_requerimento"]
        .isin(filtro_ano_requerimento)
    ]


# ------------------------------------------------------------
# FILTRO ANO COMPULSÓRIA
# ------------------------------------------------------------

if filtro_ano_compulsoria:

    resultado = resultado[
        resultado["ano_compulsoria"]
        .isin(filtro_ano_compulsoria)
    ]


# ============================================================
# INDICADORES
# ============================================================

total_registros = len(resultado)


requerimento_1_ano = (
    resultado["anos_requerimento"]
    .le(1)
    .sum()
)


requerimento_5_anos = (
    resultado["anos_requerimento"]
    .le(5)
    .sum()
)


compulsoria_5_anos = (
    resultado["anos_compulsoria"]
    .le(5)
    .sum()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total de registros",
        total_registros
    )


with col2:

    st.metric(
        "Requerimento ≤ 1 ano",
        requerimento_1_ano
    )


with col3:

    st.metric(
        "Requerimento ≤ 5 anos",
        requerimento_5_anos
    )


with col4:

    st.metric(
        "Compulsória ≤ 5 anos",
        compulsoria_5_anos
    )


# ============================================================
# TABELA PRINCIPAL
# ============================================================

st.subheader("📋 Efetivo")


colunas_exibicao = [

    "numero",

    "matricula",

    "grupo",

    "posto_graduacao",

    "nome",

    "dias_requerimento",

    "anos_requerimento",

    "dias_compulsoria",

    "anos_compulsoria",

    "ano_requerimento",

    "ano_compulsoria"
]


# Só utiliza as colunas que realmente existem
colunas_exibicao = [

    coluna

    for coluna in colunas_exibicao

    if coluna in resultado.columns
]


resultado_exibicao = resultado[
    colunas_exibicao
].copy()


# ------------------------------------------------------------
# Arredondamento dos anos calculados
# ------------------------------------------------------------

if "anos_requerimento" in resultado_exibicao.columns:

    resultado_exibicao["anos_requerimento"] = (
        pd.to_numeric(
            resultado_exibicao["anos_requerimento"],
            errors="coerce"
        )
        .round(2)
    )


if "anos_compulsoria" in resultado_exibicao.columns:

    resultado_exibicao["anos_compulsoria"] = (
        pd.to_numeric(
            resultado_exibicao["anos_compulsoria"],
            errors="coerce"
        )
        .round(2)
    )


# ------------------------------------------------------------
# Nomes amigáveis para exibição
# ------------------------------------------------------------

nomes_colunas = {

    "numero": "Nº",

    "matricula": "Matrícula",

    "grupo": "Grupo",

    "posto_graduacao": "Posto / Graduação",

    "nome": "Nome",

    "dias_requerimento": "Dias p/ Requerimento",

    "anos_requerimento": "Anos p/ Requerimento",

    "dias_compulsoria": "Dias p/ Compulsória",

    "anos_compulsoria": "Anos p/ Compulsória",

    "ano_requerimento": "Ano de Requerimento",

    "ano_compulsoria": "Ano de Compulsória"
}


resultado_exibicao = resultado_exibicao.rename(
    columns=nomes_colunas
)


# ------------------------------------------------------------
# Campos vazios ficam em branco
# ------------------------------------------------------------

resultado_exibicao = resultado_exibicao.fillna("")


st.dataframe(

    resultado_exibicao,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.html(
    "<div style='height:45px'></div>"
)


# ============================================================
# PLANEJAMENTO
# ============================================================

st.html(
    """
    <div style="
        text-align:center;
        margin-top:10px;
        margin-bottom:20px;
    ">
        <h2>📈 Cenários de Planejamento</h2>
    </div>
    """
)


st.write(
    "As projeções consideram o grupo selecionado no filtro "
    "de Grupo. Os filtros de posto e ano não alteram a base "
    "do planejamento."
)


# ============================================================
# CONFIGURAÇÃO DA PROJEÇÃO
# ============================================================

ANO_INICIAL = 2026

ANO_FINAL = 2035


anos = list(
    range(
        ANO_INICIAL,
        ANO_FINAL + 1
    )
)


# ============================================================
# BASE DO EFETIVO
#
# IMPORTANTE:
# A base considera apenas o filtro de GRUPO.
# ============================================================

if filtro_grupo == "Todos":

    df_planejamento = df.copy()

else:

    df_planejamento = df[
        df["grupo"] == filtro_grupo
    ].copy()


efetivo_inicial = len(
    df_planejamento
)


# ============================================================
# SAÍDAS POR REQUERIMENTO
# ============================================================

saidas_requerimento = {}


for ano in anos:

    if "ano_requerimento" in df_planejamento.columns:

        saidas_requerimento[ano] = int(
            df_planejamento[
                "ano_requerimento"
            ].eq(ano).sum()
        )

    else:

        saidas_requerimento[ano] = 0


# ============================================================
# SAÍDAS POR COMPULSÓRIA
# ============================================================

saidas_compulsoria = {}


for ano in anos:

    if "ano_compulsoria" in df_planejamento.columns:

        saidas_compulsoria[ano] = int(
            df_planejamento[
                "ano_compulsoria"
            ].eq(ano).sum()
        )

    else:

        saidas_compulsoria[ano] = 0


# ============================================================
# FUNÇÃO PARA CONSTRUIR CADA CENÁRIO
# ============================================================

def construir_cenario(

    tipo_saida,

    entradas_oficiais,

    entradas_pracas

):

    linhas = []

    efetivo_atual = efetivo_inicial


    for ano in anos:

        # ----------------------------------------------------
        # 2026 É O ANO-BASE
        #
        # Não existem entradas nem saídas em 2026.
        # ----------------------------------------------------

        if ano == ANO_INICIAL:

            linhas.append({

                "Ano": ano,

                "Efetivo inicial": efetivo_atual,

                "Saídas": 0,

                "Novos Oficiais": 0,

                "Novas Praças": 0,

                "Entradas": 0,

                "Saldo do ano": 0,

                "Efetivo projetado": efetivo_atual
            })

            continue


        # ----------------------------------------------------
        # SAÍDAS
        # ----------------------------------------------------

        if tipo_saida == "requerimento":

            saidas = saidas_requerimento.get(
                ano,
                0
            )

        else:

            saidas = saidas_compulsoria.get(
                ano,
                0
            )


        # ----------------------------------------------------
        # ENTRADAS
        #
        # Respeita o filtro de grupo.
        # ----------------------------------------------------

        if filtro_grupo == "Oficiais":

            novos_oficiais = entradas_oficiais

            novas_pracas = 0


        elif filtro_grupo == "Praças":

            novos_oficiais = 0

            novas_pracas = entradas_pracas


        else:

            novos_oficiais = entradas_oficiais

            novas_pracas = entradas_pracas


        entradas = (
            novos_oficiais
            +
            novas_pracas
        )


        # ----------------------------------------------------
        # SALDO
        # ----------------------------------------------------

        saldo = entradas - saidas


        # ----------------------------------------------------
        # EFETIVO PROJETADO
        #
        # A projeção é acumulativa.
        # ----------------------------------------------------

        efetivo_projetado = (
            efetivo_atual
            +
            saldo
        )


        linhas.append({

            "Ano": ano,

            "Efetivo inicial": efetivo_atual,

            "Saídas": saidas,

            "Novos Oficiais": novos_oficiais,

            "Novas Praças": novas_pracas,

            "Entradas": entradas,

            "Saldo do ano": saldo,

            "Efetivo projetado": efetivo_projetado
        })


        # ----------------------------------------------------
        # O resultado passa a ser a base do ano seguinte
        # ----------------------------------------------------

        efetivo_atual = efetivo_projetado


    return pd.DataFrame(linhas)


# ============================================================
# CENÁRIOS
# ============================================================

# ------------------------------------------------------------
# CENÁRIO 01
# Requerimento
# +30 Oficiais
# +270 Praças
# Total = +300
# ------------------------------------------------------------

cenario_01 = construir_cenario(

    tipo_saida="requerimento",

    entradas_oficiais=30,

    entradas_pracas=270
)


# ------------------------------------------------------------
# CENÁRIO 02
# Requerimento
# +20 Oficiais
# +240 Praças
# Total = +260
# ------------------------------------------------------------

cenario_02 = construir_cenario(

    tipo_saida="requerimento",

    entradas_oficiais=20,

    entradas_pracas=240
)


# ------------------------------------------------------------
# CENÁRIO 03
# Compulsória
# +30 Oficiais
# +270 Praças
# Total = +300
# ------------------------------------------------------------

cenario_03 = construir_cenario(

    tipo_saida="compulsoria",

    entradas_oficiais=30,

    entradas_pracas=270
)


# ------------------------------------------------------------
# CENÁRIO 04
# Compulsória
# +20 Oficiais
# +240 Praças
# Total = +260
# ------------------------------------------------------------

cenario_04 = construir_cenario(

    tipo_saida="compulsoria",

    entradas_oficiais=20,

    entradas_pracas=240
)


# ============================================================
# INDICADORES DOS CENÁRIOS
# ============================================================

st.subheader("📊 Resumo dos Cenários")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(

        "Cenário 01",

        f"{cenario_01.iloc[-1]['Efetivo projetado']:.0f}",

        "Requerimento | +300/ano"
    )


with col2:

    st.metric(

        "Cenário 02",

        f"{cenario_02.iloc[-1]['Efetivo projetado']:.0f}",

        "Requerimento | +260/ano"
    )


with col3:

    st.metric(

        "Cenário 03",

        f"{cenario_03.iloc[-1]['Efetivo projetado']:.0f}",

        "Compulsória | +300/ano"
    )


with col4:

    st.metric(

        "Cenário 04",

        f"{cenario_04.iloc[-1]['Efetivo projetado']:.0f}",

        "Compulsória | +260/ano"
    )


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.html(
    "<div style='height:45px'></div>"
)


# ============================================================
# CARDS DOS CENÁRIOS
# ============================================================

st.subheader("📌 Cenários")


col1, col2 = st.columns(2)


with col1:

    st.markdown(
        """
        ### Cenário 01

        **Saída:** Requerimento

        **Entrada anual:**
        - 30 Oficiais
        - 270 Praças
        - **Total: 300**
        """
    )


with col2:

    st.markdown(
        """
        ### Cenário 02

        **Saída:** Requerimento

        **Entrada anual:**
        - 20 Oficiais
        - 240 Praças
        - **Total: 260**
        """
    )


col3, col4 = st.columns(2)


with col3:

    st.markdown(
        """
        ### Cenário 03

        **Saída:** Compulsória

        **Entrada anual:**
        - 30 Oficiais
        - 270 Praças
        - **Total: 300**
        """
    )


with col4:

    st.markdown(
        """
        ### Cenário 04

        **Saída:** Compulsória

        **Entrada anual:**
        - 20 Oficiais
        - 240 Praças
        - **Total: 260**
        """
    )


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.html(
    "<div style='height:45px'></div>"
)


# ============================================================
# PLANEJAMENTO ANUAL
# ============================================================

st.subheader(
    "📅 Planejamento Anual por Cenário"
)


tab1, tab2, tab3, tab4 = st.tabs([

    "Cenário 01",

    "Cenário 02",

    "Cenário 03",

    "Cenário 04"
])


# ------------------------------------------------------------
# CENÁRIO 01
# ------------------------------------------------------------

with tab1:

    st.dataframe(

        cenario_01,

        use_container_width=True,

        hide_index=True
    )


# ------------------------------------------------------------
# CENÁRIO 02
# ------------------------------------------------------------

with tab2:

    st.dataframe(

        cenario_02,

        use_container_width=True,

        hide_index=True
    )


# ------------------------------------------------------------
# CENÁRIO 03
# ------------------------------------------------------------

with tab3:

    st.dataframe(

        cenario_03,

        use_container_width=True,

        hide_index=True
    )


# ------------------------------------------------------------
# CENÁRIO 04
# ------------------------------------------------------------

with tab4:

    st.dataframe(

        cenario_04,

        use_container_width=True,

        hide_index=True
    )


# ============================================================
# GRÁFICO COMPARATIVO
# ============================================================

st.subheader(
    "📈 Comparação dos Cenários"
)


df_comparacao = pd.DataFrame({

    "Ano": anos,

    "Cenário 01": cenario_01[
        "Efetivo projetado"
    ].values,

    "Cenário 02": cenario_02[
        "Efetivo projetado"
    ].values,

    "Cenário 03": cenario_03[
        "Efetivo projetado"
    ].values,

    "Cenário 04": cenario_04[
        "Efetivo projetado"
    ].values
})


st.bar_chart(

    df_comparacao.set_index(
        "Ano"
    )
)


# ============================================================
# TABELA CONSOLIDADA
# ============================================================

st.subheader(
    "📋 Efetivo Projetado por Cenário"
)


tabela_consolidada = pd.DataFrame({

    "Ano": anos,

    "Cenário 01": cenario_01[
        "Efetivo projetado"
    ].values,

    "Cenário 02": cenario_02[
        "Efetivo projetado"
    ].values,

    "Cenário 03": cenario_03[
        "Efetivo projetado"
    ].values,

    "Cenário 04": cenario_04[
        "Efetivo projetado"
    ].values
})


st.dataframe(

    tabela_consolidada,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# RESULTADO EM 2035
# ============================================================

st.subheader(
    "🎯 Projeção para 2035"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(

        "Cenário 01",

        f"{cenario_01.iloc[-1]['Efetivo projetado']:.0f}"
    )


with col2:

    st.metric(

        "Cenário 02",

        f"{cenario_02.iloc[-1]['Efetivo projetado']:.0f}"
    )


with col3:

    st.metric(

        "Cenário 03",

        f"{cenario_03.iloc[-1]['Efetivo projetado']:.0f}"
    )


with col4:

    st.metric(

        "Cenário 04",

        f"{cenario_04.iloc[-1]['Efetivo projetado']:.0f}"
    )


# ============================================================
# RESUMO FINAL
# ============================================================

st.subheader(
    "📌 Resumo da Projeção"
)


resumo = pd.DataFrame({

    "Cenário": [

        "Cenário 01",

        "Cenário 02",

        "Cenário 03",

        "Cenário 04"
    ],

    "Tipo de saída": [

        "Requerimento",

        "Requerimento",

        "Compulsória",

        "Compulsória"
    ],

    "Novos Oficiais/ano": [

        30,

        20,

        30,

        20
    ],

    "Novas Praças/ano": [

        270,

        240,

        270,

        240
    ],

    "Entradas/ano": [

        300,

        260,

        300,

        260
    ],

    "Efetivo em 2035": [

        int(
            cenario_01.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        int(
            cenario_02.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        int(
            cenario_03.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        int(
            cenario_04.iloc[-1][
                "Efetivo projetado"
            ]
        )
    ]
})


st.dataframe(

    resumo,

    use_container_width=True,

    hide_index=True
)
