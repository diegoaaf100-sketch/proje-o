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
        "Ano de Requerimento": "ano_requerimento",
        "Ano de Compulsória": "ano_compulsoria"
    }

    df = df.rename(columns=mapa_colunas)

        # Converter campos numéricos
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
        resultado["dias_requerimento"]
        .le(1)
        .sum()
    )

    st.metric(
        "Requerimento ≤ 1 ano",
        int(quantidade)
    )


with col3:

    quantidade = (
        resultado["dias_requerimento"]
        .le(5)
        .sum()
    )

    st.metric(
        "Requerimento ≤ 5 anos",
        int(quantidade)
    )


with col4:

    quantidade = (
        resultado["dias_compulsoria"]
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
    "dias_requerimento",
    "dias_compulsoria",
    "ano_requerimento",
    "ano_compulsoria"
]


st.dataframe(
    resultado[colunas_exibicao],
    use_container_width=True,
    hide_index=True
)
