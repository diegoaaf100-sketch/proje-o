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


    if "anos_requerimento" not in df.columns and "dias_requerimento" in df.columns:
        df["anos_requerimento"] = df["dias_requerimento"] / 365.25

    if "anos_compulsoria" not in df.columns and "dias_compulsoria" in df.columns:
        df["anos_compulsoria"] = df["dias_compulsoria"] / 365.25

    st.write("Colunas recebidas da planilha:")
    st.write(list(df.columns))

    return df


# ============================================================
# CARREGAR DADOS
# ============================================================

try:

    df = carregar_dados()

except Exception as e:

    st.error("Não foi possível carregar os dados da planilha.")

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

st.sidebar.header("Filtros")


# Posto / Graduação

postos = sorted(
    df["posto_graduacao"]
    .dropna()
    .unique()
    .tolist()
)

filtro_posto = st.sidebar.selectbox(
    "Posto / Graduação",
    ["Todos"] + postos
)


# Ano de Requerimento

anos_requerimento = sorted(
    df["ano_requerimento"]
    .dropna()
    .unique()
    .tolist()
)

filtro_ano_requerimento = st.sidebar.selectbox(
    "Ano de Requerimento",
    ["Todos"] + anos_requerimento
)


# Ano de Compulsória

anos_compulsoria = sorted(
    df["ano_compulsoria"]
    .dropna()
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

st.subheader("Dados")


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
# PROJEÇÃO DE EFETIVO — 2026 A 2035
# ============================================================

ANO_INICIAL = 2026
ANO_FINAL = 2035

NOVOS_P1 = 300
NOVOS_P2 = 260
NOVOS_P3 = 300
NOVOS_P4 = 260

# O total atual da planilha representa o efetivo inicial de 2026
efetivo_inicial = len(df)

anos = list(range(ANO_INICIAL, ANO_FINAL + 1))

# Quantidade de saídas em cada ano
saidas_requerimento = {
    ano: int(df["ano_requerimento"].eq(ano).sum())
    for ano in anos
}

saidas_compulsoria = {
    ano: int(df["ano_compulsoria"].eq(ano).sum())
    for ano in anos
}

# Projeções acumuladas ano a ano
projecoes = []

efetivo_p1 = efetivo_inicial
efetivo_p2 = efetivo_inicial
efetivo_p3 = efetivo_inicial
efetivo_p4 = efetivo_inicial

for ano in anos:

    saidas_req = saidas_requerimento[ano]
    saidas_comp = saidas_compulsoria[ano]

    efetivo_p1 = efetivo_p1 - saidas_req + NOVOS_P1
    efetivo_p2 = efetivo_p2 - saidas_req + NOVOS_P2

    efetivo_p3 = efetivo_p3 - saidas_comp + NOVOS_P3
    efetivo_p4 = efetivo_p4 - saidas_comp + NOVOS_P4

    projecoes.append({
        "Ano": ano,
        "Saídas Requerimento": saidas_req,
        "Saídas Compulsória": saidas_comp,
        "P1 — Req. +300": efetivo_p1,
        "P2 — Req. +260": efetivo_p2,
        "P3 — Comp. +300": efetivo_p3,
        "P4 — Comp. +260": efetivo_p4
    })

df_projecoes = pd.DataFrame(projecoes)

st.divider()

st.subheader("📈 Projeção de Efetivo — 2026 a 2035")

st.dataframe(
    df_projecoes,
    use_container_width=True,
    hide_index=True
)

st.subheader("Evolução projetada")

st.line_chart(
    df_projecoes.set_index("Ano")[
        [
            "P1 — Req. +300",
            "P2 — Req. +260",
            "P3 — Comp. +300",
            "P4 — Comp. +260"
        ]
    ]
)

resumo_2035 = df_projecoes.iloc[-1]

st.subheader("Resumo — 2035")

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.metric(
        "P1 — Requerimento +300",
        int(resumo_2035["P1 — Req. +300"])
    )

with r2:
    st.metric(
        "P2 — Requerimento +260",
        int(resumo_2035["P2 — Req. +260"])
    )

with r3:
    st.metric(
        "P3 — Compulsória +300",
        int(resumo_2035["P3 — Comp. +300"])
    )

with r4:
    st.metric(
        "P4 — Compulsória +260",
        int(resumo_2035["P4 — Comp. +260"])
    )
