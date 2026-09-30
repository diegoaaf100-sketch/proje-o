import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
page_title="Dashboard de Reserva",
page_icon="📊",
layout="wide"
)

st.title("📊 Dashboard de Reserva")

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

return pd.DataFrame(dados)

try:

df = carregar_dados()

except Exception as e:

st.error("Não foi possível carregar os dados da planilha.")
st.exception(e)
st.stop()

df.columns = (
df.columns
.astype(str)
.str.replace("\n", " ", regex=False)
.str.strip()
)

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

Compatibilidade com versões antigas da planilha

if (
"dias_requerimento" not in df.columns
and "anos_requerimento" in df.columns
):

df["dias_requerimento"] = (
    pd.to_numeric(
        df["anos_requerimento"],
        errors="coerce"
    ) * 365.25
)

if (
"dias_compulsoria" not in df.columns
and "anos_compulsoria" in df.columns
):

df["dias_compulsoria"] = (
    pd.to_numeric(
        df["anos_compulsoria"],
        errors="coerce"
    ) * 365.25
)

colunas_obrigatorias = [
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

st.error(
    "A planilha não possui todas as colunas necessárias."
)

st.write("Colunas encontradas na planilha:")

st.code(
    "\n".join(df.columns.astype(str).tolist())
)

st.error(
    "Colunas ausentes: "
    + ", ".join(colunas_faltantes)
)

st.stop()

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

df["anos_requerimento"] = (
df["dias_requerimento"] / 365.25
)

df["anos_compulsoria"] = (
df["dias_compulsoria"] / 365.25
)

st.sidebar.header("🔎 Filtros")

if "posto_graduacao" in df.columns:

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

else:

filtro_posto = "Todos"

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

resultado = df.copy()

if filtro_posto != "Todos":

resultado = resultado[
    resultado["posto_graduacao"].astype(str)
    == str(filtro_posto)
]

if filtro_ano_requerimento != "Todos":

resultado = resultado[
    resultado["ano_requerimento"]
    == filtro_ano_requerimento
]

if filtro_ano_compulsoria != "Todos":

resultado = resultado[
    resultado["ano_compulsoria"]
    == filtro_ano_compulsoria
]

col1, col2, col3, col4 = st.columns(4)

with col1:

st.metric(
    "Total de registros",
    len(resultado)
)

with col2:

quantidade = (
    resultado["dias_requerimento"]
    .le(365)
    .sum()
)

st.metric(
    "Requerimento ≤ 1 ano",
    int(quantidade)
)

with col3:

quantidade = (
    resultado["dias_requerimento"]
    .le(365 * 5)
    .sum()
)

st.metric(
    "Requerimento ≤ 5 anos",
    int(quantidade)
)

with col4:

quantidade = (
    resultado["dias_compulsoria"]
    .le(365 * 5)
    .sum()
)

st.metric(
    "Compulsória ≤ 5 anos",
    int(quantidade)
)

st.divider()

st.subheader("📋 Registros")

colunas_exibicao = [
"numero",
"matricula",
"posto_graduacao",
"nome",
"dias_requerimento",
"dias_compulsoria",
"anos_requerimento",
"anos_compulsoria",
"ano_requerimento",
"ano_compulsoria"
]

colunas_exibicao = [
coluna
for coluna in colunas_exibicao
if coluna in resultado.columns
]

tabela = resultado[colunas_exibicao].copy()

if "anos_requerimento" in tabela.columns:

tabela["anos_requerimento"] = (
    tabela["anos_requerimento"]
    .round(2)
)

if "anos_compulsoria" in tabela.columns:

tabela["anos_compulsoria"] = (
    tabela["anos_compulsoria"]
    .round(2)
)

st.dataframe(
tabela,
use_container_width=True,
hide_index=True
)

st.caption(
f"Total de registros exibidos: {len(resultado)}"
)
