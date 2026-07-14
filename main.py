import streamlit as st
import pandas as pd

st.set_page_config(page_title="Loja AAAA", page_icon="🌎")
st.markdown("""
        # Bem-vindo!
        ## App Financeiro

        Espero que curta a experiência! 
        """)
upload_file = st.file_uploader(label="Faça upload dos dados aqui", type=['csv'])
rs_coluna = {"Valor": st.column_config.NumberColumn("Valor", format="RS %f")}
if upload_file:
    df = pd.read_csv(upload_file)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date
    exp1 = st.expander("Dados Brutos")
    exp1.dataframe(df, hide_index=True, column_config=rs_coluna)
    exp2 = st.expander("Instituição")
    df_instituicao = df.pivot_table(index="Data",columns="Instituição", values="Valor")

    tab_dados, tab_historico, tab_graf = exp2.tabs(["Dados", "Histórico", "Distribuição"])
    tab_dados.dataframe(df_instituicao)
    with tab_historico:
        st.line_chart(df_instituicao)
    ultima_data = df_instituicao.sort_index().iloc[-1]
    with tab_graf:
        escolha_data = st.selectbox("Filtro Data", options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[escolha_data])
