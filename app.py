import streamlit as st

st.title("Teste de Secrets")

st.write("Secrets carregados:", list(st.secrets.keys()))
