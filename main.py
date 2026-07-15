import streamlit as st
import pandas as pd

def calc_stats(df: pd.DataFrame):
    df_data = df.groupby(by="Data")[["Valor"]].sum()   
    df_data["Diferença Mensal ABS"] = df_data["Valor"] - df_data["Valor"].shift(1)
    df_data["Diferença Mensal Relativa"] = df_data["Valor"] / df_data["Valor"].shift(1) - 1
    df_data["Média 6M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(6).mean().round(2)
    df_data["Média 12M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(12).mean().round(2)
    df_data["Média 24M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(24).mean().round(2)
    return df_data

st.set_page_config(page_title="Loja AAAA", page_icon="🌎")
st.markdown("""
        # Bem-vindo!
        ## App Financeiro

        Espero que curta a experiência! 
        """)
upload_file = st.file_uploader(label="Faça upload dos dados aqui", type=['csv'])
rs_coluna = {"Valor": st.column_config.NumberColumn("Valor", format="RS %f")}
columns_config = {
    "Valor": st.column_config.NumberColumn("Valor",format="R$ %f"),
    "Diferença Mensal ABS": st.column_config.NumberColumn("Diferença Mensal ABS",format="R$ %f"),
    "Diferença Mensal Relativa": st.column_config.NumberColumn("Diferença Mensal Relativa",format="percent"),
    "Média 6M Diferença Mensal": st.column_config.NumberColumn("Média 6M Diferença Mensal",format="R$ %f"),
    "Média 12M Diferença Mensal": st.column_config.NumberColumn("Média 12M Diferença Mensal",format="R$ %f"),
    "Média 24M Diferença Mensal": st.column_config.NumberColumn("Média 24M Diferença Mensal",format="R$ %f")
}
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
    df_stats = calc_stats(df)
    exp3 = st.expander("Estatísticas Gerais")
    tab_est, tab_linha = exp3.tabs(["Estatísticas", "Gráfico"])
    with tab_est:
        st.dataframe(df_stats,column_config=columns_config)
    with tab_linha:
        st.line_chart(data=[df_stats["Valor"], df_stats["Diferença Mensal ABS"], df_stats["Média 6M Diferença Mensal"]])
    
    with st.expander("Metas"):
        col1, col2 = st.columns(2)
        data_inicio_meta = col2.date_input("Início da Meta", max_value=df_stats.index.max())
        data_filtrada = df_stats.index[df_stats.index<=data_inicio_meta][-1]
        valor_inicio = df_stats.loc[data_filtrada]["Valor"]
        st.markdown(f"**Valor no Início da Meta**: R$ {valor_inicio:.2f}")
        sal_bruto = col1.number_input("Salário Bruto", min_value=0.)
        sal_liquido = col1.number_input("Salário Líquido", min_value=0.)
        custos_fixos = col2.number_input("Custos Fixos", min_value=0.)
        mensal = sal_liquido - custos_fixos
        with st.container(border=True):
            col1_pot, col2_pot = st.columns(2)
            col1_pot.markdown(f"**Potencial Arrecadação do Mês**: R$ {mensal:.2f}")
            col2_pot.markdown(f"**Potencial Arrecadação do Ano**: R$ {(mensal*12):.2f}")
        with st.container(border=True):
            pat1, pat2 = st.columns(2)
            with pat1:
                meta_estipulada = st.number_input("Meta Estipulada", min_value=0.,format="%.2f", value=mensal*12)
            with pat2:
                patrimonio_final = meta_estipulada + valor_inicio
                st.markdown(f"Patrimônio Estipulado pós meta: \n\n R$ {patrimonio_final:.2f}")
            
