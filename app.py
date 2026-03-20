import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.figure_factory as ff
import io
import re
from sklearn.ensemble import IsolationForest
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
        grap_todas_regioes_sem_outliers = st.checkbox("Saldo Sanitário (ISP) vs Nº Internações (Sem outliers)")
        
        graphs_form_submitted = st.form_submit_button("Gerar")

# === Página Principal ===
st.header('Tratamento de Água e número internações hospitalares', divider='blue')

def processa(frame):
        st.subheader("ISP vs. Nº Internações", divider="gray")

        fig, ax = plt.subplots(figsize=(14, 9))
        sns.set_style("whitegrid")

        sns.scatterplot(
            data=frame,
            x='ISP',
            y='Internacao_Total',
            hue='Perfil_Sanitario',
            hue_order=['Risco Baixo', 'Risco Médio', 'Risco Alto'],
            palette={'Risco Baixo': 'green', 'Risco Médio': 'orange', 'Risco Alto': 'red'},
            s=200,
            edgecolor='black',
            alpha=0.7,
            ax=ax
        )

        for i in range(frame.shape[0]):
            ax.text(
                frame['ISP'].iloc[i] + 0.05,
                frame['Internacao_Total'].iloc[i],
                frame['UF'].iloc[i],
                fontsize=9,
                fontweight='bold'
            )

        ax.set_title('Saldo Sanitário (ISP) vs. Nº Internações', fontsize=18, pad=25)
        ax.set_xlabel('Índice de Saneamento Positivo (ISP)', fontsize=13)
        ax.set_ylabel('Internações Totais', fontsize=13)

        ax.axvline(0, color='black', linestyle='--', alpha=0.5)
        y_max = ax.get_ylim()[1]
        ax.text(0.2, y_max * 0.9, 'Prevalência de Tratamento', color='green', fontweight='bold')
        ax.text(-1.5, y_max * 0.9, 'Prevalência de Sem Tratamento', color='red', fontweight='bold')

        plt.tight_layout()

        st.pyplot(fig)

        st.write("### Resumo Estatístico por Perfil Sanitário")

        resumo = frame.groupby('Perfil_Sanitario').agg({
            'ISP': 'mean',
            'Internacao_Total': 'mean'
        }).sort_values('ISP', ascending=False)

        st.table(resumo)


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

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.set_theme(style="whitegrid")

        sns.boxplot(x=df_usado['Internacao_Total'], color='#ff9999', fliersize=8, ax=ax)
        sns.stripplot(x=df_usado['Internacao_Total'], color='#333', alpha=0.5, ax=ax)

        ax.set_title('Distribuição e Outliers de Internações por UF', fontsize=14)
        ax.set_xlabel('Número de Internações', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()
        st.pyplot(fig)

        Q1 = df_usado['Internacao_Total'].quantile(0.25)
        Q3 = df_usado['Internacao_Total'].quantile(0.75)
        IQR = Q3 - Q1
        limite_superior = Q3 + 1.5 * IQR

        outliers = df_usado[df_usado['Internacao_Total'] > limite_superior]

        if not outliers.empty:
            st.warning(f"**Estados Outliers:** {', '.join(outliers['UF'].unique())}")

    
    if grap_todas_regioes_com_outliers:

        processa(df_final)
    
    
    if grap_todas_regioes_sem_outliers:

        iso_forest = IsolationForest(contamination=0.11, random_state=42)

        # Treinando o modelo
        df_final['Outlier_IF'] = iso_forest.fit_predict(df_final[['ISP', 'Internacao_Total']])

        df_padrao = df_final[df_final['Outlier_IF'] == 1]
        df_critico = df_final[df_final['Outlier_IF'] == -1]
        
        processa(df_padrao)

#
        
            

