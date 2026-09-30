import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
page_title="Dashboard de Reserva",
page_icon="📊",
layout="wide"
)

st.title("Dashboard de Reserva")

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
st.error("Erro ao carregar a planilha.")
st.exception(e)
st.stop()

df.columns = (
df.columns
.astype(str)
.str.replace("\n", " ", regex=False)
.str.strip()
)

mapa = {
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

df = df.rename(columns=mapa)

if "dias_requerimento" not in df.columns:
if "anos_requerimento" in df.columns:
df["dias_requerimento"] = (
pd.to_numeric(
df["anos_requerimento"],
errors="coerce"
) * 365.25
)

if "dias_compulsoria" not in df.columns:
if "anos_compulsoria" in df.columns:
df["dias_compulsoria"] = (
pd.to_numeric(
df["anos_compulsoria"],
errors="coerce"
) * 365.25
)

obrigatorias = [
"dias_requerimento",
"dias_compulsoria",
"ano_requerimento",
"ano_compulsoria"
]

faltantes = [
coluna
for coluna in obrigatorias
if coluna not in df.columns
]

if faltantes:
st.error("Existem colunas obrigatórias ausentes.")

st.write("Colunas encontradas:")

st.write(df.columns.tolist())

st.write("Colunas ausentes:")

st.write(faltantes)

st.stop()

numericas = [
"numero",
"dias_requerimento",
"dias_compulsoria",
"ano_requerimento",
"ano_compulsoria"
]

for coluna in numericas:
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

st.sidebar.header("Filtros")

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

anos_req = sorted(
df["ano_requerimento"]
.dropna()
.unique()
.tolist()
)

filtro_req = st.sidebar.selectbox(
"Ano de Requerimento",
["Todos"] + anos_req
)

anos_comp = sorted(
df["ano_compulsoria"]
.dropna()
.unique()
.tolist()
)

filtro_comp = st.sidebar.selectbox(
"Ano de Compulsória",
["Todos"] + anos_comp
)

resultado = df.copy()

if filtro_posto != "Todos":

resultado = resultado[
    resultado["posto_graduacao"].astype(str)
    == str(filtro_posto)
]

if filtro_req != "Todos":

resultado = resultado[
    resultado["ano_requerimento"]
    == filtro_req
]

if filtro_comp != "Todos":

resultado = resultado[
    resultado["ano_compulsoria"]
    == filtro_comp
]

col1, col2, col3, col4 = st.columns(4)

with col1:
st.metric(
"Total de registros",
len(resultado)
)

with col2:

qtd = resultado[
    "dias_requerimento"
].le(365).sum()

st.metric(
    "Requerimento ate 1 ano",
    int(qtd)
)

with col3:

qtd = resultado[
    "dias_requerimento"
].le(365 * 5).sum()

st.metric(
    "Requerimento ate 5 anos",
    int(qtd)
)

with col4:

qtd = resultado[
    "dias_compulsoria"
].le(365 * 5).sum()

st.metric(
    "Compulsoria ate 5 anos",
    int(qtd)
)

st.divider()

st.subheader("Registros")

colunas = [
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

colunas = [
coluna
for coluna in colunas
if coluna in resultado.columns
]

tabela = resultado[colunas].copy()

if "anos_requerimento" in tabela.columns:
tabela["anos_requerimento"] = (
tabela["anos_requerimento"].round(2)
)

if "anos_compulsoria" in tabela.columns:
tabela["anos_compulsoria"] = (
tabela["anos_compulsoria"].round(2)
)

st.dataframe(
tabela,
use_container_width=True,
hide_index=True
)

st.divider()

st.subheader("Projecoes de Efetivo 2026 a 2035")

st.write(
"O total atual da planilha e utilizado como "
"efetivo inicial da projecao."
)

ano_inicial = 2026
ano_final = 2035

novos_p1 = 300
novos_p2 = 260
novos_p3 = 300
novos_p4 = 260

efetivo_inicial = len(df)

anos = list(
range(
ano_inicial,
ano_final + 1
)
)

saidas_req = {}
saidas_comp = {}

for ano in anos:

saidas_req[ano] = int(
    df["ano_requerimento"]
    .eq(ano)
    .sum()
)

saidas_comp[ano] = int(
    df["ano_compulsoria"]
    .eq(ano)
    .sum()
)

p1 = efetivo_inicial
p2 = efetivo_inicial
p3 = efetivo_inicial
p4 = efetivo_inicial

projecoes = []

for ano in anos:

saida_req = saidas_req[ano]
saida_comp = saidas_comp[ano]


p1 = p1 - saida_req + novos_p1

p2 = p2 - saida_req + novos_p2

p3 = p3 - saida_comp + novos_p3

p4 = p4 - saida_comp + novos_p4


projecoes.append(
    {
        "Ano": ano,
        "Saidas Requerimento": saida_req,
        "Saidas Compulsoria": saida_comp,
        "P1 - Req +300": p1,
        "P2 - Req +260": p2,
        "P3 - Comp +300": p3,
        "P4 - Comp +260": p4
    }
)

projecoes_df = pd.DataFrame(
projecoes
)

st.subheader("Tabela das Projecoes")

st.dataframe(
projecoes_df,
use_container_width=True,
hide_index=True
)

st.subheader("Evolucao das Projecoes")

grafico = projecoes_df.set_index(
"Ano"
)[
[
"P1 - Req +300",
"P2 - Req +260",
"P3 - Comp +300",
"P4 - Comp +260"
]
]

st.line_chart(grafico)

st.subheader("Resumo Final - 2035")

ultima = projecoes_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

with col1:

st.metric(
    "P1 - Req +300",
    int(ultima["P1 - Req +300"])
)

with col2:

st.metric(
    "P2 - Req +260",
    int(ultima["P2 - Req +260"])
)

with col3:

st.metric(
    "P3 - Comp +300",
    int(ultima["P3 - Comp +300"])
)

with col4:

st.metric(
    "P4 - Comp +260",
    int(ultima["P4 - Comp +260"])
)

st.divider()

st.caption(
"Efetivo inicial das projecoes: "
+ str(efetivo_inicial)
)

st.caption(
"Total de registros exibidos: "
+ str(len(resultado))
)
