import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.figure_factory as ff
import io
from sklearn.ensemble import IsolationForest
import numpy as np

@st.cache_data
def fetch_and_clean_data():
    url_internacoes = 'ibge_dados/ret_internacoes_tabela898.xlsx'
    url_tratamento = 'ibge_dados/ret_tratamento_tabela1773.xlsx' 
    url_final = 'ibge_dados/df_final.xlsx'
    
    try:
        d_frame_internacoes = pd.read_excel(url_internacoes, dtype=str)
        d_frame_tratamento = pd.read_excel(url_tratamento, dtype=str)
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

with graph_expander:
    # Formulário dos gráficos
    with st.form("graphs_form", clear_on_submit=False):
        
        grap_outliers = st.checkbox("Identificando outliers")
        grap_all_areas = st.checkbox("Indice Saneamento Positivo (ISP) vs Nº Internações")
        grap_all_areas_less_outliers = st.checkbox("Indice Saneamento Positivo (ISP) vs Nº Internações (Sem outliers)")
        conclusion = st.checkbox("Conclusão")
        graphs_form_submitted = st.form_submit_button("Gerar")

# === Página Principal ===
st.header('Tratamento de Água vs Nº Internações Hospitalares', divider='blue')

def process_graph(frame, flag):
        
        st.subheader(f"Indice Saneamento Positivo (ISP) {flag} vs. Nº Internações", divider="gray")

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

        ax.set_title('Indice Saneamento Positivo (ISP) vs. Nº Internações', fontsize=18, pad=25)
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
        st.subheader("Tabela Bruta de Dados Internações", divider="gray")
        st.write(df_internacoes)
    
    if data_in_table_tratamento:
        st.subheader("Tabela Bruta de Dados Tratamento de Água", divider="gray")
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
        st.subheader("Estatísticas das principais variáveis do dataframe final", divider="gray")
        st.write(df_final[["Vol_Tratamento_Total",	"Tratamento_Convencional",	"Tratamento_Nao_Convencional",	"Simples_Desinfeccao",	"Sem_Tratamento",	"Internacao_Feco_Oral",	"Internacao_Total"]].describe())
    
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

    
    if grap_all_areas:
        
        flag_with_outliers = "com outliers"

        process_graph(df_final, flag_with_outliers)
    
    
    if grap_all_areas_less_outliers:

        flag_less_outliers = "sem outliers"

        iso_forest = IsolationForest(contamination=0.11, random_state=42)

        # Treinando o modelo
        df_final['Outlier_IF'] = iso_forest.fit_predict(df_final[['ISP', 'Internacao_Total']])

        df_padrao = df_final[df_final['Outlier_IF'] == 1]
        df_critico = df_final[df_final['Outlier_IF'] == -1]
        
        process_graph(df_padrao, flag_less_outliers)
    #

    if conclusion:

        if grap_outliers and grap_all_areas and grap_all_areas_less_outliers:
            # Título da seção de análise
            st.subheader("Análise e Conclusões dos Dados", divider="blue")

            # Texto introdutório com destaque
            st.info("""
            **Observação Geral:** Mesmo retirando os outliers, nota-se que o comportamento geral se manteve. 
            Todavia, a grande maioria dos casos em que o **ISP foi positivo**, o risco de internação foi **baixo**, salvo exceções.
            """)

            # Destaque para os casos específicos usando colunas
            st.write("### Casos de Estudo: AM e CE")
            col1, col2 = st.columns(2)

            with col1:
                st.error("**Amazonas (AM)**")
                st.write("""
                * **Perfil:** ISP Negativo / Risco Médio.
                * **Análise:** Embora o ISP seja negativo, o número de internações em relação aos outros estados foi menor, desafiando a tendência geral.
                """)

            with col2:
                st.success("**Ceará (CE)**")
                st.write("""
                * **Perfil:** ISP Positivo / Risco Baixo.
                * **Análise:** Apresenta um número de internações alto, apesar do saldo de tratamento positivo.
                """)

            # Conclusão final em um bloco de destaque
            st.markdown("---")
            st.markdown("""
            ### **Conclusão Final**
            O tratamento de água é fundamental para um saneamento básico de qualidade e influência diretamente o número de internações. 
            Contudo, o saneamento abrange diversas áreas e não é o único fator na ocorrência desse fenômeno.

            Ainda assim, os dados provaram uma **ligação inversamente proporcional** em grande parte do país. 
            Estados como **SP, RJ, DF, PE, RS, PR, AL, GO, MT, ES, SE e TO** confirmam essa tese, mantendo um ISP positivo com menos de **2.000 internações totais**.
            """)
        else:
            st.info("### 💡 Lembrete Importante\nA visualização de todos os gráficos é obrigatória para esta etapa.")
#   
        
            

