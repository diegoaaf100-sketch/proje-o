import streamlit as st
import pandas as pd
import gspread
import re
import unicodedata

from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Planejamento de Efetivo",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# FUNÇÃO PARA NORMALIZAR NOMES DE COLUNAS
# ============================================================

def normalizar_coluna(texto):

    texto = str(texto).strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    texto = texto.lower()

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# CARREGAR DADOS DO GOOGLE SHEETS
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

    worksheet = spreadsheet.worksheet(
        "Página4"
    )

    dados = worksheet.get_all_records()

    df = pd.DataFrame(dados)

    # ========================================================
    # VERIFICA SE A PLANILHA POSSUI DADOS
    # ========================================================

    if df.empty:

        raise ValueError(
            "A aba 'Página4' não possui registros."
        )

    # ========================================================
    # IDENTIFICAÇÃO DAS COLUNAS
    # ========================================================

    colunas_originais = df.columns.tolist()

    mapa_normalizado = {
        normalizar_coluna(coluna): coluna
        for coluna in colunas_originais
    }

    def encontrar_coluna(nome):

        chave = normalizar_coluna(nome)

        return mapa_normalizado.get(chave)

    # ========================================================
    # LOCALIZA AS COLUNAS
    # ========================================================

    coluna_numero = encontrar_coluna("Nº")

    coluna_matricula = encontrar_coluna(
        "Matrícula"
    )

    coluna_posto = encontrar_coluna(
        "Posto / Graduação"
    )

    coluna_nome = encontrar_coluna(
        "Nome"
    )

    coluna_reserva_req = encontrar_coluna(
        "Reserva Requerimento"
    )

    coluna_reserva_comp = encontrar_coluna(
        "Reserva Compulsória"
    )

    coluna_dias_req = encontrar_coluna(
        "Dias para Requerimento"
    )

    coluna_dias_comp = encontrar_coluna(
        "Dias para Compulsória"
    )

    coluna_ano_req = encontrar_coluna(
        "Ano de Requerimento"
    )

    coluna_ano_comp = encontrar_coluna(
        "Ano de Compulsória"
    )

    # ========================================================
    # MAPA DE RENOMEAÇÃO
    # ========================================================

    mapa_colunas = {}

    if coluna_numero:
        mapa_colunas[coluna_numero] = "numero"

    if coluna_matricula:
        mapa_colunas[coluna_matricula] = "matricula"

    if coluna_posto:
        mapa_colunas[coluna_posto] = "posto_graduacao"

    if coluna_nome:
        mapa_colunas[coluna_nome] = "nome"

    if coluna_reserva_req:
        mapa_colunas[coluna_reserva_req] = (
            "reserva_requerimento"
        )

    if coluna_reserva_comp:
        mapa_colunas[coluna_reserva_comp] = (
            "reserva_compulsoria"
        )

    if coluna_dias_req:
        mapa_colunas[coluna_dias_req] = (
            "dias_requerimento"
        )

    if coluna_dias_comp:
        mapa_colunas[coluna_dias_comp] = (
            "dias_compulsoria"
        )

    if coluna_ano_req:
        mapa_colunas[coluna_ano_req] = (
            "ano_requerimento"
        )

    if coluna_ano_comp:
        mapa_colunas[coluna_ano_comp] = (
            "ano_compulsoria"
        )

    # ========================================================
    # RENOMEIA
    # ========================================================

    df = df.rename(
        columns=mapa_colunas
    )

    # ========================================================
    # VERIFICA COLUNAS IMPORTANTES
    # ========================================================

    colunas_obrigatorias = [

        "posto_graduacao",

        "nome",

        "dias_requerimento",

        "dias_compulsoria",

        "ano_requerimento",

        "ano_compulsoria"
    ]

    colunas_faltantes = [

        coluna

        for coluna in colunas_obrigatorias

        if coluna not in df.columns
    ]

    if colunas_faltantes:

        raise ValueError(
            "As seguintes colunas não foram encontradas "
            "na aba Página4: "
            + ", ".join(colunas_faltantes)
        )

    # ========================================================
    # CAMPOS VAZIOS
    # ========================================================

    df = df.replace(
        {
            None: pd.NA,
            "": pd.NA
        }
    )

    # ========================================================
    # CONVERSÃO NUMÉRICA
    # ========================================================

    colunas_numericas = [

        "numero",

        "dias_requerimento",

        "dias_compulsoria",

        "ano_requerimento",

        "ano_compulsoria"
    ]

    for coluna in colunas_numericas:

        if coluna in df.columns:

            # Primeiro tenta conversão normal
            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

    # ========================================================
    # CLASSIFICAÇÃO OFICIAIS / PRAÇAS
    # ========================================================

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

        texto = texto.replace(
            "º",
            "°"
        )

        texto = " ".join(
            texto.split()
        )

        return texto.lower()


    def classificar_grupo(valor):

        posto = normalizar_posto(
            valor
        )

        if posto in postos_oficiais:

            return "Oficiais"

        return "Praças"


    df["grupo"] = df[
        "posto_graduacao"
    ].apply(
        classificar_grupo
    )

    return df


# ============================================================
# CARREGAMENTO
# ============================================================

try:

    df = carregar_dados()

except Exception as erro:

    st.error(
        "Erro ao carregar os dados da planilha."
    )

    st.error(
        str(erro)
    )

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

st.sidebar.header(
    "🔎 Filtros"
)


# ============================================================
# FILTRO GRUPO
# ============================================================

filtro_grupo = st.sidebar.selectbox(

    "Grupo",

    [
        "Todos",
        "Oficiais",
        "Praças"
    ]
)


# ============================================================
# FILTRO POSTO / GRADUAÇÃO
# ============================================================

postos = sorted(

    df[
        "posto_graduacao"
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


filtro_posto = st.sidebar.multiselect(

    "Posto / Graduação",

    options=postos
)


# ============================================================
# FILTRO ANO REQUERIMENTO
# ============================================================

anos_requerimento = sorted(

    df[
        "ano_requerimento"
    ]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)


filtro_ano_requerimento = st.sidebar.multiselect(

    "Ano de Requerimento",

    options=anos_requerimento
)


# ============================================================
# FILTRO ANO COMPULSÓRIA
# ============================================================

anos_compulsoria = sorted(

    df[
        "ano_compulsoria"
    ]
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
# APLICA FILTROS NA TABELA
# ============================================================

resultado = df.copy()


if filtro_grupo != "Todos":

    resultado = resultado[
        resultado["grupo"] == filtro_grupo
    ]


if filtro_posto:

    resultado = resultado[
        resultado[
            "posto_graduacao"
        ].isin(
            filtro_posto
        )
    ]


if filtro_ano_requerimento:

    resultado = resultado[
        resultado[
            "ano_requerimento"
        ].isin(
            filtro_ano_requerimento
        )
    ]


if filtro_ano_compulsoria:

    resultado = resultado[
        resultado[
            "ano_compulsoria"
        ].isin(
            filtro_ano_compulsoria
        )
    ]


# ============================================================
# INDICADORES
# ============================================================

total_registros = len(
    resultado
)


requerimento_1_ano = (
    resultado[
        "dias_requerimento"
    ]
    .le(365.25)
    .sum()
)


requerimento_5_anos = (
    resultado[
        "dias_requerimento"
    ]
    .le(5 * 365.25)
    .sum()
)


compulsoria_5_anos = (
    resultado[
        "dias_compulsoria"
    ]
    .le(5 * 365.25)
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
#
# ATENÇÃO:
# NÃO MOSTRA MAIS:
# - Anos p/ Requerimento
# - Anos p/ Compulsória
#
# MOSTRA:
# - Dias para Requerimento
# - Dias para Compulsória
# ============================================================

st.subheader(
    "📋 Efetivo"
)


colunas_exibicao = [

    "numero",

    "matricula",

    "grupo",

    "posto_graduacao",

    "nome",

    "dias_requerimento",

    "dias_compulsoria",

    "ano_requerimento",

    "ano_compulsoria"
]


colunas_exibicao = [

    coluna

    for coluna in colunas_exibicao

    if coluna in resultado.columns
]


resultado_exibicao = resultado[
    colunas_exibicao
].copy()


# ============================================================
# NOMES PARA EXIBIÇÃO
# ============================================================

nomes_colunas = {

    "numero":
        "Nº",

    "matricula":
        "Matrícula",

    "grupo":
        "Grupo",

    "posto_graduacao":
        "Posto / Graduação",

    "nome":
        "Nome",

    "dias_requerimento":
        "Dias para Requerimento",

    "dias_compulsoria":
        "Dias para Compulsória",

    "ano_requerimento":
        "Ano de Requerimento",

    "ano_compulsoria":
        "Ano de Compulsória"
}


resultado_exibicao = resultado_exibicao.rename(
    columns=nomes_colunas
)


# ============================================================
# VAZIOS APARECEM EM BRANCO
# ============================================================

resultado_exibicao = resultado_exibicao.fillna(
    ""
)


st.dataframe(

    resultado_exibicao,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# ESPAÇO
# ============================================================

st.html(
    "<div style='height:45px'></div>"
)


# ============================================================
# CENÁRIOS DE PLANEJAMENTO
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
    "As projeções consideram o grupo selecionado "
    "no filtro de Grupo."
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
# BASE DO PLANEJAMENTO
#
# SOMENTE O FILTRO DE GRUPO É CONSIDERADO.
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

    saidas_requerimento[ano] = int(

        df_planejamento[
            "ano_requerimento"
        ]
        .eq(ano)
        .sum()

    )


# ============================================================
# SAÍDAS POR COMPULSÓRIA
# ============================================================

saidas_compulsoria = {}


for ano in anos:

    saidas_compulsoria[ano] = int(

        df_planejamento[
            "ano_compulsoria"
        ]
        .eq(ano)
        .sum()

    )


# ============================================================
# FUNÇÃO DOS CENÁRIOS
# ============================================================

def construir_cenario(

    tipo_saida,

    entradas_oficiais,

    entradas_pracas

):

    linhas = []

    efetivo_atual = efetivo_inicial


    for ano in anos:

        # ====================================================
        # 2026 = ANO BASE
        #
        # NÃO TEM ENTRADAS
        # NÃO TEM SAÍDAS
        # ====================================================

        if ano == ANO_INICIAL:

            linhas.append({

                "Ano":
                    ano,

                "Efetivo inicial":
                    efetivo_atual,

                "Saídas":
                    0,

                "Novos Oficiais":
                    0,

                "Novas Praças":
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
        # SAÍDAS
        # ====================================================

        if tipo_saida == "requerimento":

            saidas = (
                saidas_requerimento
                .get(
                    ano,
                    0
                )
            )

        else:

            saidas = (
                saidas_compulsoria
                .get(
                    ano,
                    0
                )
            )


        # ====================================================
        # ENTRADAS
        # ====================================================

        if filtro_grupo == "Oficiais":

            novos_oficiais = (
                entradas_oficiais
            )

            novas_pracas = 0


        elif filtro_grupo == "Praças":

            novos_oficiais = 0

            novas_pracas = (
                entradas_pracas
            )


        else:

            novos_oficiais = (
                entradas_oficiais
            )

            novas_pracas = (
                entradas_pracas
            )


        entradas = (
            novos_oficiais
            +
            novas_pracas
        )


        # ====================================================
        # SALDO
        # ====================================================

        saldo = (
            entradas
            -
            saidas
        )


        # ====================================================
        # PROJEÇÃO
        # ====================================================

        efetivo_projetado = (
            efetivo_atual
            +
            saldo
        )


        linhas.append({

            "Ano":
                ano,

            "Efetivo inicial":
                efetivo_atual,

            "Saídas":
                saidas,

            "Novos Oficiais":
                novos_oficiais,

            "Novas Praças":
                novas_pracas,

            "Entradas":
                entradas,

            "Saldo do ano":
                saldo,

            "Efetivo projetado":
                efetivo_projetado
        })


        # ====================================================
        # PASSA O RESULTADO PARA O ANO SEGUINTE
        # ====================================================

        efetivo_atual = (
            efetivo_projetado
        )


    return pd.DataFrame(
        linhas
    )


# ============================================================
# CENÁRIO 01
# ============================================================

cenario_01 = construir_cenario(

    "requerimento",

    30,

    270
)


# ============================================================
# CENÁRIO 02
# ============================================================

cenario_02 = construir_cenario(

    "requerimento",

    20,

    240
)


# ============================================================
# CENÁRIO 03
# ============================================================

cenario_03 = construir_cenario(

    "compulsoria",

    30,

    270
)


# ============================================================
# CENÁRIO 04
# ============================================================

cenario_04 = construir_cenario(

    "compulsoria",

    20,

    240
)


# ============================================================
# RESUMO DOS CENÁRIOS
# ============================================================

st.subheader(
    "📊 Resumo dos Cenários"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(

        "Cenário 01",

        int(
            cenario_01.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        "+300/ano"
    )


with col2:

    st.metric(

        "Cenário 02",

        int(
            cenario_02.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        "+260/ano"
    )


with col3:

    st.metric(

        "Cenário 03",

        int(
            cenario_03.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        "+300/ano"
    )


with col4:

    st.metric(

        "Cenário 04",

        int(
            cenario_04.iloc[-1][
                "Efetivo projetado"
            ]
        ),

        "+260/ano"
    )


# ============================================================
# ESPAÇO
# ============================================================

st.html(
    "<div style='height:45px'></div>"
)


# ============================================================
# CARDS
# ============================================================

st.subheader(
    "📌 Cenários"
)


col1, col2 = st.columns(2)


with col1:

    st.markdown(
        """
        ### Cenário 01

        **Saída:** Requerimento

        **Entradas anuais:**

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

        **Entradas anuais:**

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

        **Entradas anuais:**

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

        **Entradas anuais:**

        - 20 Oficiais
        - 240 Praças
        - **Total: 260**
        """
    )


# ============================================================
# ESPAÇO
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


with tab1:

    st.dataframe(

        cenario_01,

        use_container_width=True,

        hide_index=True
    )


with tab2:

    st.dataframe(

        cenario_02,

        use_container_width=True,

        hide_index=True
    )


with tab3:

    st.dataframe(

        cenario_03,

        use_container_width=True,

        hide_index=True
    )


with tab4:

    st.dataframe(

        cenario_04,

        use_container_width=True,

        hide_index=True
    )


# ============================================================
# COMPARAÇÃO DOS CENÁRIOS
# ============================================================

st.subheader(
    "📈 Comparação dos Cenários"
)


df_comparacao = pd.DataFrame({

    "Ano":
        anos,

    "Cenário 01":
        cenario_01[
            "Efetivo projetado"
        ].values,

    "Cenário 02":
        cenario_02[
            "Efetivo projetado"
        ].values,

    "Cenário 03":
        cenario_03[
            "Efetivo projetado"
        ].values,

    "Cenário 04":
        cenario_04[
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

    "Ano":
        anos,

    "Cenário 01":
        cenario_01[
            "Efetivo projetado"
        ].values,

    "Cenário 02":
        cenario_02[
            "Efetivo projetado"
        ].values,

    "Cenário 03":
        cenario_03[
            "Efetivo projetado"
        ].values,

    "Cenário 04":
        cenario_04[
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

        int(
            cenario_01.iloc[-1][
                "Efetivo projetado"
            ]
        )
    )


with col2:

    st.metric(

        "Cenário 02",

        int(
            cenario_02.iloc[-1][
                "Efetivo projetado"
            ]
        )
    )


with col3:

    st.metric(

        "Cenário 03",

        int(
            cenario_03.iloc[-1][
                "Efetivo projetado"
            ]
        )
    )


with col4:

    st.metric(

        "Cenário 04",

        int(
            cenario_04.iloc[-1][
                "Efetivo projetado"
            ]
        )
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
