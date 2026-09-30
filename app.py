import streamlit as st
import pandas as pd
import gspread
import re
import unicodedata

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
# CABEÇALHO
# ============================================================

# Espaçamento superior
st.markdown(
    "<div style='height:20px'></div>",
    unsafe_allow_html=True
)


# Container central para os brasões
col_esquerda, col_centro, col_direita = st.columns(
    [1, 2, 1]
)


with col_centro:

    col_img1, col_img2 = st.columns(2)

    with col_img1:

        st.image(
            "brasao_dgp.png",
            width=150
        )

    with col_img2:

        st.image(
            "brasao_cbmpe.png",
            width=150
        )


# ============================================================
# TÍTULO
# ============================================================

st.html(
    """
    <h1 style="
        text-align:center;
        font-size:42px;
        margin-top:15px;
        margin-bottom:10px;
        font-weight:700;
    ">
        Dashboard de Efetivo
    </h1>
    """
)


st.markdown(
    "<div style='height:25px'></div>",
    unsafe_allow_html=True
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
# FUNÇÃO PARA CONVERTER NÚMEROS
# ============================================================

def converter_numero(valor):

    if pd.isna(valor):
        return pd.NA

    valor = str(valor).strip()

    if valor == "":
        return pd.NA

    valor = valor.replace(
        " ",
        ""
    )

    # Exemplo:
    # 1.234,56
    if "." in valor and "," in valor:

        valor = valor.replace(
            ".",
            ""
        )

        valor = valor.replace(
            ",",
            "."
        )

    # Exemplo:
    # 1234,56
    elif "," in valor:

        valor = valor.replace(
            ",",
            "."
        )

    try:

        return float(valor)

    except Exception:

        return pd.NA


# ============================================================
# LOCALIZAR COLUNA
# ============================================================

def encontrar_coluna(
    mapa,
    possibilidades
):

    for possibilidade in possibilidades:

        chave = normalizar_coluna(
            possibilidade
        )

        if chave in mapa:

            return mapa[chave]

    return None


# ============================================================
# CLASSIFICAÇÃO DE GRUPO
# ============================================================

def classificar_grupo(posto):

    texto = str(
        posto
    ).strip()

    # Padroniza º para °
    texto = texto.replace(
        "º",
        "°"
    )

    # Remove espaços duplicados
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    texto = texto.lower()

    oficiais = {

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
    }

    if texto in oficiais:

        return "Oficiais"

    return "Praças"


# ============================================================
# CARREGAR DADOS DO GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=300)
def carregar_dados():

    # --------------------------------------------------------
    # PERMISSÕES
    # --------------------------------------------------------

    scopes = [

        "https://www.googleapis.com/auth/spreadsheets.readonly",

        "https://www.googleapis.com/auth/drive.readonly"

    ]

    # --------------------------------------------------------
    # CREDENCIAIS
    # --------------------------------------------------------

    credentials = Credentials.from_service_account_info(

        st.secrets[
            "google_service_account"
        ],

        scopes=scopes
    )

    # --------------------------------------------------------
    # CONEXÃO
    # --------------------------------------------------------

    client = gspread.authorize(
        credentials
    )

    # --------------------------------------------------------
    # PLANILHA
    # --------------------------------------------------------

    spreadsheet = client.open_by_key(
        st.secrets[
            "spreadsheet_id"
        ]
    )

    # --------------------------------------------------------
    # ABA
    # --------------------------------------------------------

    worksheet = spreadsheet.worksheet(
        "Página4"
    )

    # --------------------------------------------------------
    # LER TODOS OS VALORES
    #
    # Usamos get_all_values() para preservar
    # os valores exibidos no Google Sheets.
    # --------------------------------------------------------

    valores = worksheet.get_all_values()

    if not valores:

        raise ValueError(
            "A aba Página4 está vazia."
        )

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    cabecalho = valores[0]

    # --------------------------------------------------------
    # DADOS
    # --------------------------------------------------------

    dados = valores[1:]

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(
        dados,
        columns=cabecalho
    )

    # --------------------------------------------------------
    # MAPA DAS COLUNAS
    # --------------------------------------------------------

    mapa_normalizado = {}

    for coluna in df.columns:

        chave = normalizar_coluna(
            coluna
        )

        mapa_normalizado[
            chave
        ] = coluna

    # ========================================================
    # LOCALIZAR COLUNAS
    # ========================================================

    coluna_numero = encontrar_coluna(

        mapa_normalizado,

        [
            "numero",
            "nº",
            "n°",
            "no",
            "n"
        ]
    )


    coluna_matricula = encontrar_coluna(

        mapa_normalizado,

        [
            "matricula",
            "matrícula"
        ]
    )


    coluna_posto = encontrar_coluna(

        mapa_normalizado,

        [
            "posto / graduação",
            "posto/graduação",
            "posto graduacao",
            "posto graduação",
            "posto",
            "graduação",
            "graduacao"
        ]
    )


    coluna_nome = encontrar_coluna(

        mapa_normalizado,

        [
            "nome"
        ]
    )


    coluna_reserva_requerimento = encontrar_coluna(

        mapa_normalizado,

        [
            "reserva requerimento",
            "reserva_requerimento"
        ]
    )


    coluna_reserva_compulsoria = encontrar_coluna(

        mapa_normalizado,

        [
            "reserva compulsória",
            "reserva compulsoria",
            "reserva_compulsoria"
        ]
    )


    coluna_dias_requerimento = encontrar_coluna(

        mapa_normalizado,

        [
            "dias para requerimento",
            "dias p/ requerimento",
            "dias_requerimento"
        ]
    )


    coluna_dias_compulsoria = encontrar_coluna(

        mapa_normalizado,

        [
            "dias para compulsória",
            "dias para compulsoria",
            "dias p/ compulsória",
            "dias p/ compulsoria",
            "dias_compulsoria"
        ]
    )


    coluna_ano_requerimento = encontrar_coluna(

        mapa_normalizado,

        [
            "ano de requerimento",
            "ano requerimento",
            "ano_requerimento"
        ]
    )


    coluna_ano_compulsoria = encontrar_coluna(

        mapa_normalizado,

        [
            "ano de compulsória",
            "ano de compulsoria",
            "ano compulsoria",
            "ano_compulsoria"
        ]
    )


    # ========================================================
    # VERIFICAR COLUNAS OBRIGATÓRIAS
    # ========================================================

    colunas_obrigatorias = {

        "Nº":
            coluna_numero,

        "Matrícula":
            coluna_matricula,

        "Posto / Graduação":
            coluna_posto,

        "Nome":
            coluna_nome,

        "Dias para Requerimento":
            coluna_dias_requerimento,

        "Dias para Compulsória":
            coluna_dias_compulsoria,

        "Ano de Requerimento":
            coluna_ano_requerimento,

        "Ano de Compulsória":
            coluna_ano_compulsoria
    }


    faltantes = [

        nome

        for nome, coluna
        in colunas_obrigatorias.items()

        if coluna is None
    ]


    if faltantes:

        raise ValueError(

            "As seguintes colunas não foram "
            "encontradas na aba Página4:\n\n"

            + "\n".join(

                f"- {item}"

                for item in faltantes
            )
        )


    # ========================================================
    # RENOMEAR COLUNAS
    # ========================================================

    renomear = {

        coluna_numero:
            "numero",

        coluna_matricula:
            "matricula",

        coluna_posto:
            "posto_graduacao",

        coluna_nome:
            "nome",

        coluna_dias_requerimento:
            "dias_requerimento",

        coluna_dias_compulsoria:
            "dias_compulsoria",

        coluna_ano_requerimento:
            "ano_requerimento",

        coluna_ano_compulsoria:
            "ano_compulsoria"
    }


    # Colunas opcionais
    if coluna_reserva_requerimento is not None:

        renomear[
            coluna_reserva_requerimento
        ] = "reserva_requerimento"


    if coluna_reserva_compulsoria is not None:

        renomear[
            coluna_reserva_compulsoria
        ] = "reserva_compulsoria"


    df = df.rename(
        columns=renomear
    )


    # ========================================================
    # GARANTIR COLUNAS OPCIONAIS
    # ========================================================

    if "reserva_requerimento" not in df.columns:

        df[
            "reserva_requerimento"
        ] = ""


    if "reserva_compulsoria" not in df.columns:

        df[
            "reserva_compulsoria"
        ] = ""


    # ========================================================
    # CONVERTER DIAS
    # ========================================================

    df[
        "dias_requerimento"
    ] = (

        df[
            "dias_requerimento"
        ]

        .apply(
            converter_numero
        )
    )


    df[
        "dias_compulsoria"
    ] = (

        df[
            "dias_compulsoria"
        ]

        .apply(
            converter_numero
        )
    )


    # ========================================================
    # CONVERTER ANOS
    # ========================================================

    df[
        "ano_requerimento"
    ] = (

        df[
            "ano_requerimento"
        ]

        .apply(
            converter_numero
        )
    )


    df[
        "ano_compulsoria"
    ] = (

        df[
            "ano_compulsoria"
        ]

        .apply(
            converter_numero
        )
    )


    # ========================================================
    # CLASSIFICAR GRUPO
    # ========================================================

    df[
        "grupo"
    ] = (

        df[
            "posto_graduacao"
        ]

        .apply(
            classificar_grupo
        )
    )


    return df


# ============================================================
# CARREGAR DADOS
# ============================================================

try:

    df = carregar_dados()

except Exception as erro:

    st.error(
        "Erro ao carregar os dados da planilha."
    )

    st.exception(
        erro
    )

    st.stop()


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
)


filtro_posto = st.sidebar.selectbox(

    "Posto / Graduação",

    [
        "Todos"
    ] + postos
)


# ============================================================
# FILTRO ANO DE REQUERIMENTO
# ============================================================

anos_requerimento = sorted(

    pd.to_numeric(

        df[
            "ano_requerimento"
        ],

        errors="coerce"
    )

    .dropna()

    .astype(int)

    .unique()
)


filtro_ano_requerimento = st.sidebar.selectbox(

    "Ano de Requerimento",

    [
        "Todos"
    ] + anos_requerimento
)


# ============================================================
# FILTRO ANO DE COMPULSÓRIA
# ============================================================

anos_compulsoria = sorted(

    pd.to_numeric(

        df[
            "ano_compulsoria"
        ],

        errors="coerce"
    )

    .dropna()

    .astype(int)

    .unique()
)


filtro_ano_compulsoria = st.sidebar.selectbox(

    "Ano de Compulsória",

    [
        "Todos"
    ] + anos_compulsoria
)


# ============================================================
# APLICAR FILTROS
# ============================================================

resultado = df.copy()


if filtro_grupo != "Todos":

    resultado = resultado[
        resultado[
            "grupo"
        ] == filtro_grupo
    ]


if filtro_posto != "Todos":

    resultado = resultado[

        resultado[
            "posto_graduacao"
        ]

        .astype(str)

        == str(
            filtro_posto
        )
    ]


if filtro_ano_requerimento != "Todos":

    resultado = resultado[

        resultado[
            "ano_requerimento"
        ]

        == float(
            filtro_ano_requerimento
        )
    ]


if filtro_ano_compulsoria != "Todos":

    resultado = resultado[

        resultado[
            "ano_compulsoria"
        ]

        == float(
            filtro_ano_compulsoria
        )
    ]


# ============================================================
# INDICADORES
# ============================================================

st.subheader(
    "📌 Indicadores"
)


total_efetivo = len(
    resultado
)


total_oficiais = (

    resultado[
        "grupo"
    ]

    .eq(
        "Oficiais"
    )

    .sum()
)


total_pracas = (

    resultado[
        "grupo"
    ]

    .eq(
        "Praças"
    )

    .sum()
)


requerimento_1_ano = (

    resultado[
        "dias_requerimento"
    ]

    .le(
        365.25
    )

    .sum()
)


requerimento_5_anos = (

    resultado[
        "dias_requerimento"
    ]

    .le(
        5 * 365.25
    )

    .sum()
)


compulsoria_5_anos = (

    resultado[
        "dias_compulsoria"
    ]

    .le(
        5 * 365.25
    )

    .sum()
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Efetivo",
        total_efetivo
    )


with col2:

    st.metric(
        "Oficiais",
        total_oficiais
    )


with col3:

    st.metric(
        "Praças",
        total_pracas
    )


with col4:

    st.metric(
        "Requerimento ≤ 1 ano",
        requerimento_1_ano
    )


with col5:

    st.metric(
        "Compulsória ≤ 5 anos",
        compulsoria_5_anos
    )


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


# ============================================================
# TABELA DO EFETIVO
# ============================================================

st.subheader(
    "👥 Efetivo"
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


resultado_exibicao = (

    resultado[
        colunas_exibicao
    ]

    .copy()
)


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


resultado_exibicao = (

    resultado_exibicao

    .rename(
        columns=nomes_colunas
    )
)


# Valores vazios em vez de NaN
resultado_exibicao = (

    resultado_exibicao

    .fillna("")
)


st.dataframe(

    resultado_exibicao,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# PLANEJAMENTO
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


st.subheader(
    "📈 Cenários de Planejamento"
)


# ============================================================
# BASE DO PLANEJAMENTO
# ============================================================

# O planejamento utiliza somente o filtro de GRUPO.
#
# Os filtros de Posto/Graduação e Ano não alteram
# o efetivo inicial utilizado na projeção.


df_planejamento = df.copy()


if filtro_grupo != "Todos":

    df_planejamento = df_planejamento[

        df_planejamento[
            "grupo"
        ] == filtro_grupo
    ]


# ============================================================
# EFETIVO INICIAL DE 2026
# ============================================================

efetivo_inicial = len(
    df_planejamento
)


efetivo_oficiais = (

    df_planejamento[
        "grupo"
    ]

    .eq(
        "Oficiais"
    )

    .sum()
)


efetivo_pracas = (

    df_planejamento[
        "grupo"
    ]

    .eq(
        "Praças"
    )

    .sum()
)


# ============================================================
# CENÁRIOS
# ============================================================

cenarios = {

    "Cenário 01": {

        "tipo_saida":
            "Requerimento",

        "oficiais":
            30,

        "pracas":
            270
    },


    "Cenário 02": {

        "tipo_saida":
            "Requerimento",

        "oficiais":
            20,

        "pracas":
            240
    },


    "Cenário 03": {

        "tipo_saida":
            "Compulsória",

        "oficiais":
            30,

        "pracas":
            270
    },


    "Cenário 04": {

        "tipo_saida":
            "Compulsória",

        "oficiais":
            20,

        "pracas":
            240
    }
}


# ============================================================
# CALCULAR SAÍDAS
# ============================================================

def calcular_saidas(
    base,
    ano,
    tipo_saida
):

    # 2026 não possui saídas
    if ano == 2026:

        return 0


    if tipo_saida == "Requerimento":

        coluna = (
            "ano_requerimento"
        )

    else:

        coluna = (
            "ano_compulsoria"
        )


    return int(

        (
            base[
                coluna
            ]

            == ano
        )

        .sum()
    )


# ============================================================
# PROJETAR CENÁRIO
# ============================================================

def projetar_cenario(

    base,

    tipo_saida,

    novas_vagas_oficiais,

    novas_vagas_pracas,

    ano_inicial=2026,

    ano_final=2035

):

    registros = []


    # Efetivo de 2026
    efetivo_atual = len(
        base
    )


    # --------------------------------------------------------
    # LOOP DOS ANOS
    # --------------------------------------------------------

    for ano in range(

        ano_inicial,

        ano_final + 1

    ):


        # ====================================================
        # 2026
        # ====================================================

        if ano == 2026:

            saidas = 0

            novos_oficiais = 0

            novas_pracas = 0


        # ====================================================
        # 2027 EM DIANTE
        # ====================================================

        else:

            saidas = calcular_saidas(

                base,

                ano,

                tipo_saida
            )


            novos_oficiais = (

                novas_vagas_oficiais
            )


            novas_pracas = (

                novas_vagas_pracas
            )


        # ====================================================
        # ENTRADAS
        # ====================================================

        entradas = (

            novos_oficiais

            +

            novas_pracas
        )


        # ====================================================
        # SALDO DO ANO
        # ====================================================

        saldo = (

            entradas

            -

            saidas
        )


        # ====================================================
        # EFETIVO PROJETADO
        # ====================================================

        efetivo_projetado = (

            efetivo_atual

            +

            saldo
        )


        # ====================================================
        # REGISTRO
        # ====================================================

        registros.append({

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
        # PRÓXIMO ANO
        # ====================================================

        efetivo_atual = (
            efetivo_projetado
        )


    return pd.DataFrame(
        registros
    )


# ============================================================
# GERAR OS 4 CENÁRIOS
# ============================================================

resultados_cenarios = {}


for nome_cenario, configuracao in cenarios.items():

    resultados_cenarios[
        nome_cenario
    ] = projetar_cenario(

        df_planejamento,

        configuracao[
            "tipo_saida"
        ],

        configuracao[
            "oficiais"
        ],

        configuracao[
            "pracas"
        ],

        2026,

        2035
    )


# ============================================================
# CARDS DOS CENÁRIOS
# ============================================================

cols = st.columns(4)


for coluna, (
    nome,
    configuracao
) in zip(
    cols,
    cenarios.items()
):


    df_cenario = (

        resultados_cenarios[
            nome
        ]
    )


    efetivo_2035 = int(

        df_cenario.loc[

            df_cenario[
                "Ano"
            ] == 2035,

            "Efetivo projetado"

        ]

        .iloc[0]
    )


    saidas_total = int(

        df_cenario[
            "Saídas"
        ]

        .sum()
    )


    entradas_total = int(

        df_cenario[
            "Entradas"
        ]

        .sum()
    )


    with coluna:

        st.markdown(

            f"""
            <div style="
                border:1px solid #ddd;
                border-radius:10px;
                padding:15px;
                min-height:190px;
                background-color:#fafafa;
            ">

                <h4 style="
                    margin-top:0;
                ">
                    {nome}
                </h4>

                <p>
                    <b>Saída:</b>
                    {configuracao["tipo_saida"]}
                </p>

                <p>
                    <b>Novos Oficiais/ano:</b>
                    {configuracao["oficiais"]}
                </p>

                <p>
                    <b>Novas Praças/ano:</b>
                    {configuracao["pracas"]}
                </p>

                <p>
                    <b>Efetivo em 2035:</b>
                    {efetivo_2035}
                </p>

            </div>
            """,

            unsafe_allow_html=True
        )


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


# ============================================================
# PLANEJAMENTO ANUAL
# ============================================================

st.subheader(
    "📅 Planejamento Anual por Cenário"
)


# ============================================================
# ABAS
# ============================================================

abas = st.tabs(
    list(
        cenarios.keys()
    )
)


for aba, nome_cenario in zip(

    abas,

    cenarios.keys()

):


    with aba:

        configuracao = (

            cenarios[
                nome_cenario
            ]
        )


        st.markdown(

            f"""
            ### {nome_cenario}

            **Tipo de saída:** {configuracao["tipo_saida"]}

            **Novos Oficiais por ano:** {configuracao["oficiais"]}

            **Novas Praças por ano:** {configuracao["pracas"]}
            """
        )


        tabela_cenario = (

            resultados_cenarios[
                nome_cenario
            ]

            .copy()
        )


        st.dataframe(

            tabela_cenario,

            use_container_width=True,

            hide_index=True
        )


# ============================================================
# COMPARAÇÃO DOS CENÁRIOS
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


st.subheader(
    "📊 Comparação dos Cenários"
)


df_comparacao = pd.DataFrame({

    "Ano":

        resultados_cenarios[
            "Cenário 01"
        ][
            "Ano"
        ],


    "Cenário 01":

        resultados_cenarios[
            "Cenário 01"
        ][
            "Efetivo projetado"
        ],


    "Cenário 02":

        resultados_cenarios[
            "Cenário 02"
        ][
            "Efetivo projetado"
        ],


    "Cenário 03":

        resultados_cenarios[
            "Cenário 03"
        ][
            "Efetivo projetado"
        ],


    "Cenário 04":

        resultados_cenarios[
            "Cenário 04"
        ][
            "Efetivo projetado"
        ]
})


st.bar_chart(

    df_comparacao.set_index(
        "Ano"
    )
)


# ============================================================
# TABELA CONSOLIDADA
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


st.subheader(
    "📋 Efetivo Projetado por Cenário"
)


df_consolidado = pd.DataFrame({

    "Ano":

        resultados_cenarios[
            "Cenário 01"
        ][
            "Ano"
        ],


    "Cenário 01":

        resultados_cenarios[
            "Cenário 01"
        ][
            "Efetivo projetado"
        ],


    "Cenário 02":

        resultados_cenarios[
            "Cenário 02"
        ][
            "Efetivo projetado"
        ],


    "Cenário 03":

        resultados_cenarios[
            "Cenário 03"
        ][
            "Efetivo projetado"
        ],


    "Cenário 04":

        resultados_cenarios[
            "Cenário 04"
        ][
            "Efetivo projetado"
        ]
})


st.dataframe(

    df_consolidado,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# INDICADORES DE 2035
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


st.subheader(
    "🎯 Indicadores para 2035"
)


colunas_2035 = st.columns(4)


for coluna, nome_cenario in zip(

    colunas_2035,

    cenarios.keys()

):


    df_cenario = (

        resultados_cenarios[
            nome_cenario
        ]
    )


    linha_2035 = (

        df_cenario[

            df_cenario[
                "Ano"
            ] == 2035

        ]

        .iloc[0]
    )


    efetivo_2035 = int(

        linha_2035[
            "Efetivo projetado"
        ]
    )


    saidas = int(

        df_cenario[
            "Saídas"
        ]

        .sum()
    )


    entradas = int(

        df_cenario[
            "Entradas"
        ]

        .sum()
    )


    with coluna:

        st.metric(

            f"{nome_cenario} — Efetivo 2035",

            efetivo_2035
        )


        st.write(

            f"Saídas acumuladas: **{saidas}**"
        )


        st.write(

            f"Entradas acumuladas: **{entradas}**"
        )


# ============================================================
# RESUMO
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


st.subheader(
    "📝 Resumo"
)


st.write(

    f"""
    O efetivo considerado como base para o planejamento
    em **2026** é de **{efetivo_inicial} servidores**.

    A projeção mantém o efetivo de 2026 sem entradas ou
    saídas. As alterações começam a partir de **2027**.

    A cada ano, o cálculo é acumulativo:

    **Efetivo projetado = efetivo do ano anterior
    - saídas + entradas.**

    Os quatro cenários consideram diferentes combinações
    de saídas por requerimento ou compulsória e de reposição
    anual de Oficiais e Praças.
    """
)
