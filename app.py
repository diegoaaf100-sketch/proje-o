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
============================================================
CARREGAMENTO DOS DADOS
============================================================

try:
df = carregar_dados()

except Exception as e:
st.error("Não foi possível carregar os dados da planilha.")
st.exception(e)
st.stop()

============================================================
PADRONIZAÇÃO DAS COLUNAS
============================================================

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

============================================================
COMPATIBILIDADE COM VERSÕES ANTIGAS DA PLANILHA
============================================================

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

============================================================
VERIFICAÇÃO DAS COLUNAS
============================================================

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
    "\n".join(
        df.columns.astype(str).tolist()
    )
)

st.error(
    "Colunas ausentes: "
    + ", ".join(colunas_faltantes)
)

st.stop()
============================================================
CONVERSÃO NUMÉRICA
============================================================

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
============================================================
CÁLCULO DOS ANOS
============================================================

df["anos_requerimento"] = (
df["dias_requerimento"] / 365.25
)

df["anos_compulsoria"] = (
df["dias_compulsoria"] / 365.25
)

============================================================
FILTROS
============================================================

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

============================================================
APLICAÇÃO DOS FILTROS
============================================================

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
============================================================
INDICADORES
============================================================

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
============================================================
TABELA DE REGISTROS
============================================================

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

#============================================================
#PROJEÇÕES DE EFETIVO — 2026 A 2035
#============================================================

st.divider()

st.subheader(
"📈 Projeções de Efetivo — 2026 a 2035"
)

st.write(
"O efetivo atual da planilha é utilizado como "
"efetivo inicial de 2026. As projeções são "
"calculadas de forma acumulativa."
)

ANO_INICIAL = 2026
ANO_FINAL = 2035

NOVOS_P1 = 300
NOVOS_P2 = 260
NOVOS_P3 = 300
NOVOS_P4 = 260

efetivo_inicial = len(df)

anos = list(
range(
ANO_INICIAL,
ANO_FINAL + 1
)
)

============================================================
SAÍDAS POR ANO
============================================================

saidas_requerimento = {}
saidas_compulsoria = {}

for ano in anos:

saidas_requerimento[ano] = int(
    df["ano_requerimento"]
    .eq(ano)
    .sum()
)

saidas_compulsoria[ano] = int(
    df["ano_compulsoria"]
    .eq(ano)
    .sum()
)
============================================================
CÁLCULO DAS PROJEÇÕES
============================================================

projecoes = []

efetivo_p1 = efetivo_inicial
efetivo_p2 = efetivo_inicial
efetivo_p3 = efetivo_inicial
efetivo_p4 = efetivo_inicial

for ano in anos:

saidas_req = saidas_requerimento[ano]

saidas_comp = saidas_compulsoria[ano]


efetivo_p1 = (
    efetivo_p1
    - saidas_req
    + NOVOS_P1
)


efetivo_p2 = (
    efetivo_p2
    - saidas_req
    + NOVOS_P2
)


efetivo_p3 = (
    efetivo_p3
    - saidas_comp
    + NOVOS_P3
)


efetivo_p4 = (
    efetivo_p4
    - saidas_comp
    + NOVOS_P4
)


projecoes.append(
    {
        "Ano": ano,
        "Saídas Requerimento": saidas_req,
        "Saídas Compulsória": saidas_comp,
        "P1 — Req. +300": efetivo_p1,
        "P2 — Req. +260": efetivo_p2,
        "P3 — Comp. +300": efetivo_p3,
        "P4 — Comp. +260": efetivo_p4
    }
)

projecoes_df = pd.DataFrame(
projecoes
)

============================================================
TABELA DAS PROJEÇÕES
============================================================

st.subheader(
"📋 Tabela das Projeções"
)

colunas_projecao = [
"Ano",
"Saídas Requerimento",
"Saídas Compulsória",
"P1 — Req. +300",
"P2 — Req. +260",
"P3 — Comp. +300",
"P4 — Comp. +260"
]

st.dataframe(
projecoes_df[colunas_projecao],
use_container_width=True,
hide_index=True
)

============================================================
GRÁFICO
============================================================

st.subheader(
"📊 Evolução das Projeções"
)

grafico = projecoes_df.set_index(
"Ano"
)[
[
"P1 — Req. +300",
"P2 — Req. +260",
"P3 — Comp. +300",
"P4 — Comp. +260"
]
]

st.line_chart(grafico)

#============================================================
#RESUMO FINAL — 2035
#============================================================

st.subheader(
"📌 RESUMO FINAL — 2035"
)

ultima_linha = projecoes_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

with col1:

st.metric(
    "P1 — Requerimento +300",
    int(
        ultima_linha["P1 — Req. +300"]
    )
)

with col2:

st.metric(
    "P2 — Requerimento +260",
    int(
        ultima_linha["P2 — Req. +260"]
    )
)

with col3:

st.metric(
    "P3 — Compulsória +300",
    int(
        ultima_linha["P3 — Comp. +300"]
    )
)

with col4:

st.metric(
    "P4 — Compulsória +260",
    int(
        ultima_linha["P4 — Comp. +260"]
    )
)
#============================================================
#RODAPÉ
#============================================================

st.divider()

st.caption(
f"Total de registros exibidos nos filtros: {len(resultado)}"
)

st.caption(
f"Efetivo inicial utilizado nas projeções: {efetivo_inicial}"
)
