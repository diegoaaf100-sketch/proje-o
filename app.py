import streamlit as st
import pandas as pd
import gspread
import re
import unicodedata
from pathlib import Path
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
# CAMINHO DAS IMAGENS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

IMAGEM_DGP = BASE_DIR / "imagens" / "brasao_dgp.png"
IMAGEM_CBMPE = BASE_DIR / "imagens" / "brasao_cbmpe.png"


# ============================================================
# CABEÇALHO COM OS BRASÕES
# ============================================================

col_esquerda, col_centro, col_direita = st.columns([1, 2, 1])

with col_centro:

    col_img1, col_img2 = st.columns(2)

    with col_img1:
        if IMAGEM_DGP.exists():
            st.image(
                str(IMAGEM_DGP),
                width=150
            )
        else:
            st.warning("Imagem DGP não encontrada.")

    with col_img2:
        if IMAGEM_CBMPE.exists():
            st.image(
                str(IMAGEM_CBMPE),
                width=150
            )
        else:
            st.warning("Imagem CBMPE não encontrada.")


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


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_coluna(texto):

    texto = str(texto).strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    texto = texto.lower()

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def encontrar_coluna(mapa_colunas, nomes_possiveis):

    for nome in nomes_possiveis:

        chave = normalizar_coluna(nome)

        if chave in mapa_colunas:
            return mapa_colunas[chave]

    return None


def converter_numero(valor):

    if pd.isna(valor):
        return pd.NA

    valor = str(valor).strip()

    if valor == "":
        return pd.NA

    valor = valor.replace(" ", "")

    # Exemplo: 1.234,56
    if "." in valor and "," in valor:

        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    # Exemplo: 1234,56
    elif "," in valor:

        valor = valor.replace(",", ".")

    try:

        return float(valor)

    except:

        return pd.NA


# ============================================================
# CLASSIFICAÇÃO DE GRUPO
# ============================================================

def classificar_grupo(posto):

    posto_normalizado = normalizar_coluna(posto)

    # Normaliza º para °
    posto_normalizado = posto_normalizado.replace("º", "°")

    # Lista de oficiais
    oficiais = [

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

    if posto_normalizado in oficiais:
        return "Oficiais"

    return "Praças"


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

    worksheet = spreadsheet.worksheet(
        "Página4"
    )

    valores = worksheet.get_all_values()

    if not valores:
        raise ValueError(
            "A aba Página4 está vazia."
        )

    cabecalho = valores[0]

    dados = valores[1:]

    df = pd.DataFrame(
        dados,
        columns=cabecalho
    )

    return df


# ============================================================
# CARREGAR DADOS
# ============================================================

try:

    df = carregar_dados()

except Exception as e:

    st.error(
        "Erro ao carregar os dados do Google Sheets."
    )

    st.exception(e)

    st.stop()


# ============================================================
# MAPA DE COLUNAS
# ============================================================

mapa_normalizado = {
    normalizar_coluna(coluna): coluna
    for coluna in df.columns
}


# ============================================================
# LOCALIZAR COLUNAS
# ============================================================

col_numero = encontrar_coluna(
    mapa_normalizado,
    [
        "Nº",
        "No",
        "Numero",
        "Número"
    ]
)

col_matricula = encontrar_coluna(
    mapa_normalizado,
    [
        "Matrícula",
        "Matricula"
    ]
)

col_posto = encontrar_coluna(
    mapa_normalizado,
    [
        "Posto / Graduação",
        "Posto/Graduação",
        "Posto Graduação",
        "Posto",
        "Graduação"
    ]
)

col_nome = encontrar_coluna(
    mapa_normalizado,
    [
        "Nome"
    ]
)

col_reserva_requerimento = encontrar_coluna(
    mapa_normalizado,
    [
        "Reserva Requerimento"
    ]
)

col_reserva_compulsoria = encontrar_coluna(
    mapa_normalizado,
    [
        "Reserva Compulsória",
        "Reserva Compulsoria"
    ]
)

col_dias_requerimento = encontrar_coluna(
    mapa_normalizado,
    [
        "Dias para Requerimento"
    ]
)

col_dias_compulsoria = encontrar_coluna(
    mapa_normalizado,
    [
        "Dias para Compulsória",
        "Dias para Compulsoria"
    ]
)

col_ano_requerimento = encontrar_coluna(
    mapa_normalizado,
    [
        "Ano de Requerimento"
    ]
)

col_ano_compulsoria = encontrar_coluna(
    mapa_normalizado,
    [
        "Ano de Compulsória",
        "Ano de Compulsoria"
    ]
)


# ============================================================
# VALIDAR COLUNAS IMPORTANTES
# ============================================================

colunas_obrigatorias = {

    "Nº": col_numero,

    "Matrícula": col_matricula,

    "Posto / Graduação": col_posto,

    "Nome": col_nome,

    "Dias para Requerimento": col_dias_requerimento,

    "Dias para Compulsória": col_dias_compulsoria,

    "Ano de Requerimento": col_ano_requerimento,

    "Ano de Compulsória": col_ano_compulsoria

}


colunas_faltantes = [
    nome
    for nome, coluna in colunas_obrigatorias.items()
    if coluna is None
]


if colunas_faltantes:

    st.error(
        "As seguintes colunas não foram encontradas na planilha:"
    )

    for coluna in colunas_faltantes:
        st.write(f"- {coluna}")

    st.write("Colunas encontradas:")

    st.write(
        list(df.columns)
    )

    st.stop()


# ============================================================
# PADRONIZAR NOMES INTERNOS
# ============================================================

df["numero"] = df[col_numero]

df["matricula"] = df[col_matricula]

df["posto_graduacao"] = df[col_posto]

df["nome"] = df[col_nome]

df["dias_requerimento"] = df[col_dias_requerimento]

df["dias_compulsoria"] = df[col_dias_compulsoria]

df["ano_requerimento"] = df[col_ano_requerimento]

df["ano_compulsoria"] = df[col_ano_compulsoria]


# ============================================================
# CONVERSÃO NUMÉRICA
# ============================================================

df["dias_requerimento"] = (
    df["dias_requerimento"]
    .apply(converter_numero)
)

df["dias_compulsoria"] = (
    df["dias_compulsoria"]
    .apply(converter_numero)
)

df["ano_requerimento"] = (
    df["ano_requerimento"]
    .apply(converter_numero)
)

df["ano_compulsoria"] = (
    df["ano_compulsoria"]
    .apply(converter_numero)
)


# ============================================================
# CLASSIFICAR GRUPO
# ============================================================

df["grupo"] = (
    df["posto_graduacao"]
    .apply(classificar_grupo)
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Filtros"
)


# ------------------------------------------------------------
# FILTRO GRUPO
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
# FILTRO POSTO / GRADUAÇÃO
# ------------------------------------------------------------

postos = sorted(
    df["posto_graduacao"]
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


# ------------------------------------------------------------
# FILTRO ANO REQUERIMENTO
# ------------------------------------------------------------

anos_requerimento = sorted(
    pd.to_numeric(
        df["ano_requerimento"],
        errors="coerce"
    )
    .dropna()
    .astype(int)
    .unique()
)

filtro_ano_requerimento = st.sidebar.selectbox(
    "Ano de Requerimento",
    ["Todos"] + anos_requerimento
)


# ------------------------------------------------------------
# FILTRO ANO COMPULSÓRIA
# ------------------------------------------------------------

anos_compulsoria = sorted(
    pd.to_numeric(
        df["ano_compulsoria"],
        errors="coerce"
    )
    .dropna()
    .astype(int)
    .unique()
)

filtro_ano_compulsoria = st.sidebar.selectbox(
    "Ano de Compulsória",
    ["Todos"] + anos_compulsoria
)


# ============================================================
# APLICAR FILTROS
# ============================================================

resultado = df.copy()


if filtro_grupo != "Todos":

    resultado = resultado[
        resultado["grupo"] == filtro_grupo
    ]


if filtro_posto != "Todos":

    resultado = resultado[
        resultado["posto_graduacao"]
        .astype(str)
        == str(filtro_posto)
    ]


if filtro_ano_requerimento != "Todos":

    resultado = resultado[
        resultado["ano_requerimento"]
        == float(filtro_ano_requerimento)
    ]


if filtro_ano_compulsoria != "Todos":

    resultado = resultado[
        resultado["ano_compulsoria"]
        == float(filtro_ano_compulsoria)
    ]


# ============================================================
# INDICADORES
# ============================================================

efetivo = len(resultado)

oficiais = (
    resultado["grupo"]
    .eq("Oficiais")
    .sum()
)

pracas = (
    resultado["grupo"]
    .eq("Praças")
    .sum()
)

requerimento_1_ano = (
    resultado["dias_requerimento"]
    .le(365.25)
    .sum()
)

requerimento_5_anos = (
    resultado["dias_requerimento"]
    .le(5 * 365.25)
    .sum()
)

compulsoria_5_anos = (
    resultado["dias_compulsoria"]
    .le(5 * 365.25)
    .sum()
)


# ============================================================
# INDICADORES NA TELA
# ============================================================

st.subheader(
    "Indicadores"
)

m1, m2, m3, m4, m5 = st.columns(5)

with m1:

    st.metric(
        "Efetivo",
        f"{efetivo:,}".replace(",", ".")
    )

with m2:

    st.metric(
        "Oficiais",
        f"{oficiais:,}".replace(",", ".")
    )

with m3:

    st.metric(
        "Praças",
        f"{pracas:,}".replace(",", ".")
    )

with m4:

    st.metric(
        "Requerimento ≤ 1 ano",
        f"{requerimento_1_ano:,}".replace(",", ".")
    )

with m5:

    st.metric(
        "Compulsória ≤ 5 anos",
        f"{compulsoria_5_anos:,}".replace(",", ".")
    )


# Espaçamento
st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


# ============================================================
# TABELA PRINCIPAL
# ============================================================

st.subheader(
    "Efetivo"
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


tabela = resultado[
    colunas_exibicao
].copy()


tabela = tabela.rename(
    columns={

        "numero": "Nº",

        "matricula": "Matrícula",

        "grupo": "Grupo",

        "posto_graduacao": "Posto / Graduação",

        "nome": "Nome",

        "dias_requerimento":
            "Dias para Requerimento",

        "dias_compulsoria":
            "Dias para Compulsória",

        "ano_requerimento":
            "Ano de Requerimento",

        "ano_compulsoria":
            "Ano de Compulsória"

    }
)


tabela = tabela.fillna("")


st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# ESPAÇAMENTO
# ============================================================

st.markdown(
    "<div style='height:45px'></div>",
    unsafe_allow_html=True
)


# ============================================================
# CENÁRIOS DE PLANEJAMENTO
# ============================================================

st.header(
    "Cenários de Planejamento"
)


# ============================================================
# DEFINIÇÃO DOS CENÁRIOS
# ============================================================

cenarios = {

    "Cenário 01": {
        "tipo": "Requerimento",
        "oficiais": 30,
        "pracas": 270
    },

    "Cenário 02": {
        "tipo": "Requerimento",
        "oficiais": 20,
        "pracas": 240
    },

    "Cenário 03": {
        "tipo": "Compulsória",
        "oficiais": 30,
        "pracas": 270
    },

    "Cenário 04": {
        "tipo": "Compulsória",
        "oficiais": 20,
        "pracas": 240
    }

}


# ============================================================
# BASE PARA PROJEÇÃO
# ============================================================

# A projeção respeita APENAS o filtro de Grupo.
# Os filtros de posto e ano não alteram a base da projeção.

base_projecao = df.copy()


if filtro_grupo != "Todos":

    base_projecao = base_projecao[
        base_projecao["grupo"] == filtro_grupo
    ]


efetivo_inicial = len(
    base_projecao
)


# ============================================================
# FUNÇÃO PARA CALCULAR SAÍDAS
# ============================================================

def calcular_saidas(
    base,
    ano,
    tipo
):

    if tipo == "Requerimento":

        coluna = "ano_requerimento"

    else:

        coluna = "ano_compulsoria"


    saidas = (
        base[coluna]
        .eq(float(ano))
        .sum()
    )

    return int(saidas)


# ============================================================
# FUNÇÃO DE PROJEÇÃO
# ============================================================

def gerar_projecao(
    base,
    ano_inicio,
    ano_fim,
    tipo_saida,
    novos_oficiais,
    novas_pracas
):

    linhas = []

    efetivo_atual = len(base)


    for ano in range(
        ano_inicio,
        ano_fim + 1
    ):

        # ----------------------------------------------------
        # 2026
        # ----------------------------------------------------
        # O ano de 2026 permanece exatamente igual ao
        # efetivo atual.
        # Não existem saídas nem entradas em 2026.

        if ano == 2026:

            saidas = 0

            entradas = 0

            saldo = 0

            efetivo_projetado = efetivo_atual

            efetivo_inicial_ano = efetivo_atual

        else:

            efetivo_inicial_ano = efetivo_atual

            saidas = calcular_saidas(
                base,
                ano,
                tipo_saida
            )

            entradas = (
                novos_oficiais
                + novas_pracas
            )

            saldo = (
                entradas
                - saidas
            )

            efetivo_projetado = (
                efetivo_atual
                - saidas
                + entradas
            )

            efetivo_atual = (
                efetivo_projetado
            )


        linhas.append({

            "Ano": ano,

            "Efetivo inicial":
                efetivo_inicial_ano,

            "Saídas":
                saidas,

            "Novos Oficiais":
                novos_oficiais
                if ano != 2026
                else 0,

            "Novas Praças":
                novas_pracas
                if ano != 2026
                else 0,

            "Entradas":
                entradas,

            "Saldo do ano":
                saldo,

            "Efetivo projetado":
                efetivo_projetado

        })


    return pd.DataFrame(linhas)


# ============================================================
# GERAR OS QUATRO CENÁRIOS
# ============================================================

projecoes = {}


for nome_cenario, configuracao in cenarios.items():

    projecoes[nome_cenario] = gerar_projecao(

        base=base_projecao,

        ano_inicio=2026,

        ano_fim=2035,

        tipo_saida=configuracao["tipo"],

        novos_oficiais=configuracao["oficiais"],

        novas_pracas=configuracao["pracas"]

    )


# ============================================================
# CARDS DOS CENÁRIOS
# ============================================================

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.info(
        f"""
        **Cenário 01**

        Saída: Requerimento

        Novos Oficiais: **30**

        Novas Praças: **270**

        Entradas anuais: **300**
        """
    )


with c2:

    st.info(
        f"""
        **Cenário 02**

        Saída: Requerimento

        Novos Oficiais: **20**

        Novas Praças: **240**

        Entradas anuais: **260**
        """
    )


with c3:

    st.info(
        f"""
        **Cenário 03**

        Saída: Compulsória

        Novos Oficiais: **30**

        Novas Praças: **270**

        Entradas anuais: **300**
        """
    )


with c4:

    st.info(
        f"""
        **Cenário 04**

        Saída: Compulsória

        Novos Oficiais: **20**

        Novas Praças: **240**

        Entradas anuais: **260**
        """
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

st.header(
    "Planejamento Anual por Cenário"
)


# ============================================================
# TABELAS DOS CENÁRIOS
# ============================================================

for nome_cenario, tabela_cenario in projecoes.items():

    st.subheader(
        nome_cenario
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

st.header(
    "Comparação dos Cenários"
)


# ============================================================
# DATAFRAME PARA COMPARAÇÃO
# ============================================================

df_comparacao = pd.DataFrame({

    "Ano":
        projecoes[
            "Cenário 01"
        ]["Ano"],

    "Cenário 01":
        projecoes[
            "Cenário 01"
        ]["Efetivo projetado"],

    "Cenário 02":
        projecoes[
            "Cenário 02"
        ]["Efetivo projetado"],

    "Cenário 03":
        projecoes[
            "Cenário 03"
        ]["Efetivo projetado"],

    "Cenário 04":
        projecoes[
            "Cenário 04"
        ]["Efetivo projetado"]

})


# ============================================================
# GRÁFICO
# ============================================================

st.bar_chart(
    df_comparacao.set_index(
        "Ano"
    )
)


# ============================================================
# TABELA COMPARATIVA
# ============================================================

st.subheader(
    "Tabela Comparativa"
)


st.dataframe(
    df_comparacao,
    use_container_width=True,
    hide_index=True
)
