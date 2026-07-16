import streamlit as st
import pandas as pd
from datetime import datetime
import requests

@st.cache_data(ttl="1day")
def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()["conteudo"])
    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(datetime.today().date())
    return df

def calc_stats(df: pd.DataFrame):
    df_data = df.groupby(by="Data")[["Valor"]].sum()   
    df_data["Diferença Mensal ABS"] = df_data["Valor"] - df_data["Valor"].shift(1)
    df_data["Diferença Mensal Relativa"] = df_data["Valor"] / df_data["Valor"].shift(1) - 1
    df_data["Média 6M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(6).mean().round(2)
    df_data["Média 12M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(12).mean().round(2)
    df_data["Média 24M Diferença Mensal"] = df_data["Diferença Mensal ABS"].rolling(24).mean().round(2)
    return df_data

st.set_page_config(page_title="AAAA", page_icon="🌎")
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
        tab_config, tab_info, tab_info_grap = st.tabs(["Configuração", "Dados da Meta", "Gráfico da Meta"])
        with tab_config:
            col1, col2 = st.columns(2)
            data_inicio_meta = col2.date_input("Início da Meta", max_value=df_stats.index.max())
            data_filtrada = df_stats.index[df_stats.index<=data_inicio_meta][-1]
            valor_inicio = df_stats.loc[data_filtrada]["Valor"]

            sal_bruto = col1.number_input("Salário Bruto", min_value=0.)
            sal_liquido = col1.number_input("Salário Líquido", min_value=0.)
            custos_fixos = col2.number_input("Custos Fixos", min_value=0.)
            col1.markdown(f"**Valor no Início da Meta**: R$ {valor_inicio:.2f}")
            
            gov_selic = get_selic()
            filter_selic_date = (gov_selic["DataInicioVigencia"] < data_inicio_meta) & (gov_selic["DataFimVigencia"] > data_inicio_meta)
            default_selic = gov_selic[filter_selic_date]["MetaSelic"].iloc[0]
            selic = col2.number_input("Selic", min_value=0.,value=default_selic/100, format="%.2f")
            selic_anual = default_selic / 100
            selic_mensal = (selic_anual + 1) ** (1/12) -1
            mensal = sal_liquido - custos_fixos + (valor_inicio*selic_mensal)
            anual = sal_liquido - custos_fixos + (valor_inicio*selic_anual)

            with st.container(border=True):
                col1_pot, col2_pot = st.columns(2)
                col1_pot.markdown(f"**Potencial Arrecadação do Mês**: R$ {mensal:.2f}")
                col2_pot.markdown(f"**Potencial Arrecadação do Ano**: R$ {anual:.2f}")

            with st.container(border=True):
                pat1, pat2 = st.columns(2)
                with pat1:
                    meta_estipulada = st.number_input("Meta Estipulada", min_value=0.,format="%.2f", value=anual)
                with pat2:
                    patrimonio_final = meta_estipulada + valor_inicio
                    st.markdown(f"Patrimônio Estipulado pós meta: \n\n R$ {patrimonio_final:.2f}")

        with tab_info:
            meses = pd.DataFrame({"Data Referência": [(data_inicio_meta + pd.DateOffset(months=i)) for i in range(1, 13)],
                                "Meta Mensal": [valor_inicio + round(meta_estipulada/12,2) * i for i in range(1, 13)]})
            meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime("%Y-%m")
            meses = meses.merge(df_patrimonio, how="left", on="Data Referência")
            meses = meses[["Data Referência", "Meta Mensal", "Valor"]]
            meses["Atingimento (%)"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Ano"] = meses["Valor"]/ patrimonio_final
            meses["Atingimento Esperado (%)"] = meses["Meta Mensal"]/ patrimonio_final

            columns_config_meta = {
                "Meta Mensal": st.column_config.NumberColumn("Meta Mensal",format="R$ %.2f"),
                "Valor": st.column_config.NumberColumn("Valor",format="R$ %f"),
                "Atingimento (%)": st.column_config.NumberColumn("Atingimento (%)",format="percent"),
                "Atingimento Ano": st.column_config.NumberColumn("Atingimento Ano",format="percent"),
                "Atingimento Esperado (%)": st.column_config.NumberColumn("Atingimento Esperado (%)",format="percent")
            }
            st.dataframe(meses, column_config=columns_config_meta)

        with tab_info_grap:
            st.line_chart(meses[["Atingimento Ano", "Atingimento Esperado (%)"]])
