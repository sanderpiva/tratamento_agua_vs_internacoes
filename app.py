import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.figure_factory as ff
import io
import re
import numpy as np

@st.cache_data
def fetch_and_clean_data():
    url_internacoes = 'ibge_dados/ret_internacoes_tabela898.xlsx'
    url_tratamento = 'ibge_dados/ret_tratamento_tabela1773.xlsx' 
    url_final = 'ibge_dados/df_final.xlsx'
    
    try:
        d_frame_internacoes = pd.read_excel(url_internacoes)
        d_frame_tratamento = pd.read_excel(url_tratamento)
        d_frame_final = pd.read_excel(url_final)   
        
        return d_frame_internacoes, d_frame_tratamento, d_frame_final
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados. Verifique a URL ou o formato: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_internacoes, df_tratamento, df_final = fetch_and_clean_data()

#
# --- BARRA LATERAL ---
st.sidebar.header('Configurações', divider='blue')

data_expander = st.sidebar.expander(label="# **Dados Tabulares**", icon=":material/table:")
with data_expander:
    # O form é crucial para agrupar as ações de filtro e só atualizar a tela quando o botão for pressionado
    with st.form("settings_form", clear_on_submit=False):
        st.markdown("**Selecione as Visualizações**")
        data_in_table_internacoes = st.checkbox("Exibir Tabela de Dados Internações", key="table_internacoes")
        data_in_table_tratamento = st.checkbox("Exibir Tabela de Dados Tratamento", key="table_tratamento")
        data_in_table_final = st.checkbox("Exibir Tabela de Dados Final (Modelo)", key="table_final")
        data_info = st.checkbox("Informações dataframe final", key="info")
        data_described = st.checkbox("Resumir dados dataframe final (Describe)", key="describe")
        
        # O botão de submissão é necessário para que as checagens acima sejam processadas
        settings_form_submitted = st.form_submit_button("Carregar")

#

graph_expander = st.sidebar.expander("# **Gráficos**", icon=":material/monitoring:")
# st.sidebar.subheader('Gráficos')
with graph_expander:
    # Formulário dos gráficos
    with st.form("graphs_form", clear_on_submit=False):
        
        grap_outliers = st.checkbox("Identificando outliers")
        grap_todas_regioes_com_outliers = st.checkbox("Saldo Sanitário (ISP) vs Nº Internações")
        #grap_todas_regioes_sem_outliers = st.checkbox("Saldo Sanitário (ISP) vs Nº Internações (Sem outliers)")
        
        graphs_form_submitted = st.form_submit_button("Gerar")

# === Página Principal ===
st.header('Tratamento de Água e número internações hospitalares', divider='blue')

# Ao submeter o form de dados tabulares
if settings_form_submitted:
    
    if data_in_table_internacoes:
        st.subheader("Tabela de Dados Internações", divider="gray")
        st.write(df_internacoes)
    
    if data_in_table_tratamento:
        st.subheader("Tabela de Dados Tratamento de Água", divider="gray")
        st.write(df_tratamento)

    if data_in_table_final:
        st.subheader("Tabela de Dados Final", divider="gray")
        st.write(df_final)
    
    if data_info:
        st.subheader("Informações sobre os dados: dataframe final", divider="gray")
        try:
            df_final['Data'] = pd.to_datetime(df_final['Data'], errors='coerce')
        except KeyError:
            st.warning("Aviso: A coluna 'Data' não foi encontrada no DataFrame. Verifique o nome da coluna.")

        buffer_captura = io.StringIO()
        
        df_final.info(buf=buffer_captura)
        
        st.code(buffer_captura.getvalue(), language='text')
    
    if data_described:
        st.subheader("Resumo dos dados: dataframe final (Modelo)", divider="gray")
        st.write(df_final.describe())
    
#

# Ao submeter o form de gráficos

if graphs_form_submitted:
    
    
    if  grap_outliers:
        st.subheader("Identificando outliers", divider="gray")

        df_usado = df_final.copy() 

        df_usado['Data'] = pd.to_datetime(df_usado['Data'], errors='coerce')

        acoes_retornos = ['RETORNO_LOG_CAMBIO', 'RETORNO_LOG_CDS']

        fig, axes = plt.subplots(2, 1, figsize=(15, 18), sharex=False) 

        for i, acao in enumerate(acoes_retornos):
        
            sns.lineplot(ax=axes[i], x='Data', y=acao, data=df_usado, color=plt.cm.magma(i/len(acoes_retornos)))
            
            axes[i].set_title(f'Série Temporal do Retorno Logarítmico: {acao}', fontsize=16)
            axes[i].set_ylabel('Retorno Logarítmico', fontsize=12)
            axes[i].tick_params(axis='y', labelsize=10)
            axes[i].grid(True, linestyle='--', alpha=0.7)
            
            axes[i].tick_params(axis='x', rotation=45, labelsize=10)
            
            axes[i].set_xlabel('Data', fontsize=12) 

        plt.tight_layout()

        st.pyplot(fig)
    
    
    if grap_todas_regioes_com_outliers:
        st.subheader("Saldo Sanitário (ISP) vs Nº Internações", divider="gray")

        df_usado = df_final.copy() 

        df_usado['Data'] = pd.to_datetime(df_usado['Data'], errors='coerce')

        acoes_retornos = ['RETORNO_LOG_Itau', 'RETORNO_LOG_Petrobras', 'RETORNO_LOG_Vale Rio Doce']

        fig, axes = plt.subplots(3, 1, figsize=(15, 18), sharex=False) 

        for i, acao in enumerate(acoes_retornos):
        
            sns.lineplot(ax=axes[i], x='Data', y=acao, data=df_usado, color=plt.cm.viridis(i/len(acoes_retornos)))
            
            axes[i].set_title(f'Série Temporal do Retorno Logarítmico: {acao}', fontsize=16)
            axes[i].set_ylabel('Retorno Logarítmico', fontsize=12)
            axes[i].tick_params(axis='y', labelsize=10)
            axes[i].grid(True, linestyle='--', alpha=0.7)
            
            axes[i].tick_params(axis='x', rotation=45, labelsize=10)
            
            axes[i].set_xlabel('Data', fontsize=12) 


        plt.tight_layout()

        st.pyplot(fig)
    
    #if  grap_todas_regioes_sem_outliers:

