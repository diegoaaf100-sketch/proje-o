import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Dashboard de Reserva", page_icon="📊", layout="wide")

st.title("Dashboard de Reserva")

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

for coluna in [
"numero",
"dias_requerimento",
"dias_compulsoria",
"ano_requerimento",
"ano_compulsoria"
]:

```
if coluna in df.columns:

    df[coluna] = pd.to_numeric(
        df[coluna],
        errors="coerce"
    )
```

if "dias_requerimento" not in df.columns:

```
st.error("A coluna Dias para Requerimento não foi encontrada.")

st.write(df.columns.tolist())

st.stop()
```

if "dias_compulsoria" not in df.columns:

```
st.error("A coluna Dias para Compulsória não foi encontrada.")

st.write(df.columns.tolist())

st.stop()
```

if "ano_requerimento" not in df.columns:

```
st.error("A coluna Ano de Requerimento não foi encontrada.")

st.write(df.columns.tolist())

st.stop()
```

if "ano_compulsoria" not in df.columns:

```
st.error("A coluna Ano de Compulsória não foi encontrada.")

st.write(df.columns.tolist())

st.stop()
```

df["anos_requerimento"] = (
df["dias_requerimento"] / 365.25
)

df["anos_compulsoria"] = (
df["dias_compulsoria"] / 365.25
)

st.sidebar.header("Filtros")

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

```
resultado = resultado[
    resultado["posto_graduacao"].astype(str)
    == str(filtro_posto)
]
```

if filtro_req != "Todos":

```
resultado = resultado[
    resultado["ano_requerimento"]
    == filtro_req
]
```

if filtro_comp != "Todos":

```
resultado = resultado[
    resultado["ano_compulsoria"]
    == filtro_comp
]
```

col1, col2, col3, col4 = st.columns(4)

with col1:

```
st.metric(
    "Total de registros",
    len(resultado)
)
```

with col2:

```
quantidade = (
    resultado["dias_requerimento"]
    .le(365)
    .sum()
)

st.metric(
    "Requerimento até 1 ano",
    int(quantidade)
)
```

with col3:

```
quantidade = (
    resultado["dias_requerimento"]
    .le(365 * 5)
    .sum()
)

st.metric(
    "Requerimento até 5 anos",
    int(quantidade)
)
```

with col4:

```
quantidade = (
    resultado["dias_compulsoria"]
    .le(365 * 5)
    .sum()
)

st.metric(
    "Compulsória até 5 anos",
    int(quantidade)
)
```

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

tabela = resultado[colunas].copy()

tabela["anos_requerimento"] = (
tabela["anos_requerimento"].round(2)
)

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

p1 = efetivo_inicial

p2 = efetivo_inicial

p3 = efetivo_inicial

p4 = efetivo_inicial

projecoes = []

for ano in anos:

```
saidas_req = int(
    df["ano_requerimento"]
    .eq(ano)
    .sum()
)

saidas_comp = int(
    df["ano_compulsoria"]
    .eq(ano)
    .sum()
)


p1 = p1 - saidas_req + novos_p1

p2 = p2 - saidas_req + novos_p2

p3 = p3 - saidas_comp + novos_p3

p4 = p4 - saidas_comp + novos_p4


projecoes.append(
    {
        "Ano": ano,
        "Saidas Requerimento": saidas_req,
        "Saidas Compulsoria": saidas_comp,
        "P1 - Req +300": p1,
        "P2 - Req +260": p2,
        "P3 - Comp +300": p3,
        "P4 - Comp +260": p4
    }
)
```

projecoes_df = pd.DataFrame(projecoes)

st.subheader("Tabela das Projecoes")

st.dataframe(
projecoes_df,
use_container_width=True,
hide_index=True
)

st.subheader("Evolucao das Projecoes")

grafico = projecoes_df.set_index("Ano")[
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

```
st.metric(
    "P1 - Req +300",
    int(ultima["P1 - Req +300"])
)
```

with col2:

```
st.metric(
    "P2 - Req +260",
    int(ultima["P2 - Req +260"])
)
```

with col3:

```
st.metric(
    "P3 - Comp +300",
    int(ultima["P3 - Comp +300"])
)
```

with col4:

```
st.metric(
    "P4 - Comp +260",
    int(ultima["P4 - Comp +260"])
)
```

st.divider()

st.caption(
"Efetivo inicial: "
+ str(efetivo_inicial)
)

st.caption(
"Total de registros: "
+ str(len(resultado))
)
