import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sqlalchemy import create_engine
import urllib
from datetime import datetime

# Configuração da página em modo wide
st.set_page_config(layout="wide")

# Configuração de conexão com o banco de dados
DADOS_CONEXAO = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=teste2;"
    "Trusted_Connection=yes;"
)

# Função para obter os dados do primeiro gráfico
@st.cache_data
def CARREGAR_DADOS():
    try:
        consulta_sql = """
        SELECT * 
        FROM Vendas WHERE nome IS NOT NULL AND nome <> '' ORDER BY Nome
        """
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        dados = pd.read_sql(consulta_sql, engine)
        return dados
    except Exception as e:
        st.error(f"Erro ao executar a consulta SQL: {e}")
        return None

df = CARREGAR_DADOS()

# Verifica se os dados foram carregados corretamente
if df is None or df.empty:
    st.warning("Nenhum dado foi carregado. Verifique a consulta SQL.")
    st.stop()

col1, col2 = st.columns(2)

# Título com emoji e cor customizada
with col1:
    #st.markdown("<h2 style='text-align: center;'>👥👥 Segmentação de Clientes</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>👥👥 Segmentação de Clientes</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("""---""")

    # Converter a coluna de data para o formato datetime
    df['Data_cx'] = pd.to_datetime(df['Data_cx'], errors='coerce')

    # Remover entradas inválidas
    linhas_antes = len(df)
    df.dropna(subset=['Data_cx', 'Nome', 'Valor_Liquido'], inplace=True)
    linhas_depois = len(df)
    if linhas_depois < linhas_antes:
        st.info(f"🔄 {linhas_antes - linhas_depois} registros foram removidos devido a dados ausentes.")

    # Cálculo da Frequência de Compras e Valor Gasto
    frequencia_gasto = df.groupby('Nome').agg({
    'Data_cx': 'count',  # Conta quantas compras por cliente
    'Valor_Liquido': 'sum'  # Soma total de gastos por cliente
    }).rename(columns={'Data_cx': 'FREQUENCIA_COMPRA', 'Valor_Liquido': 'VALOR_GASTO'})

    # Normalização dos Dados
    scaler = StandardScaler()
    X = frequencia_gasto[['FREQUENCIA_COMPRA', 'VALOR_GASTO']]
    X_scaled = scaler.fit_transform(X)

    # Seção de K-Means com cor e slider
    st.markdown("<h3 style='color:#FAFAFA;'>📊 Aplicação do K-Means</h3>", unsafe_allow_html=True)
    n_clusters = st.slider("Escolha o número de clusters:", min_value=2, max_value=10, value=3)

    # Aplicação do K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    frequencia_gasto['Cluster'] = kmeans.fit_predict(X_scaled)

    # Calcular a média das características por cluster
    cluster_summary = frequencia_gasto.groupby('Cluster').mean().reset_index()

    # Renomear colunas, verificando os nomes existentes
    if 'FREQUENCIA_COMPRA' in cluster_summary.columns:
       freq_col = 'FREQUENCIA_COMPRA'
    elif 'FREQUÊNCIA_COMPRA' in cluster_summary.columns:
       freq_col = 'FREQUÊNCIA_COMPRA'
    else:
       freq_col = cluster_summary.columns[1]  # Supondo que a coluna de frequência seja a segunda

    if 'VALOR_GASTO' in cluster_summary.columns:
       valor_col = 'VALOR_GASTO'
    else:
       valor_col = cluster_summary.columns[2]  # Supondo que a coluna de valor gasto seja a terceira


    # Ordenar o DataFrame pelas colunas encontradas
    cluster_summary = cluster_summary.sort_values(by=[freq_col, valor_col], ascending=False)

    # Renomear as colunas para uma melhor visualização
    cluster_summary.columns = ['Cluster', 'FREQUÊNCIA_COMPRA (média)', 'VALOR_GASTO (média)']

    # Formatar os valores para uma exibição amigável
    cluster_summary['FREQUÊNCIA_COMPRA (média)'] = cluster_summary['FREQUÊNCIA_COMPRA (média)'].map("{:.1f}".format)
    cluster_summary['VALOR_GASTO (média)'] = cluster_summary['VALOR_GASTO (média)'].map("R$ {:,.2f}".format) 

    # Exibir o DataFrame formatado
    st.markdown("<h4>📋 Média das características por Cluster:</h4>", unsafe_allow_html=True)
    #st.dataframe(cluster_summary.style.highlight_max(axis=0, color='#AED6F1'))
    st.dataframe(cluster_summary)

    # Interpretação dos clusters
    st.markdown("<h4>📈 Interpretação por Cluster:</h4>", unsafe_allow_html=True)
    interpretacoes = []
    for index, row in cluster_summary.iterrows():
        cluster_id = int(row['Cluster'])
        # Pega os valores das colunas específicas e tenta convertê-los para float
        try:
            # Remove caracteres como 'R$', ',' e espaços antes de converter
            freq_media = float(str(row['FREQUÊNCIA_COMPRA (média)']).replace(',', '').strip())
            #gasto_medio = float(str(row['VALOR_GASTO (média)']).replace('R$', '').replace('.', '').replace(',', '.').strip())
            gasto_medio = float(str(row['VALOR_GASTO (média)']).replace('R$', '').replace('.', '').replace(',', '').strip()) / 100
        except ValueError:
            st.write(f"Erro ao converter os valores para números no cluster {cluster_id}. Verifique os dados.")
            freq_media = 0.0
            gasto_medio = 0.0

        # Aplicando as condições para interpretar com base nos valores
        if (freq_media > 20.0) and (gasto_medio > 20000.0):
           interpretacao = f"🎯 **Cluster {cluster_id}**: Alta frequência e alto gasto, clientes VIP."
        elif (2.0 < freq_media < 10.0) and (gasto_medio < 10000.0):
           interpretacao = f"🎯 **Cluster {cluster_id}**: Compras e gastos moderados, clientes regulares."
        elif (freq_media < 2.0) and (gasto_medio < 1000.0):
          interpretacao = f"🎯 **Cluster {cluster_id}**: Baixa frequência e baixo gasto, clientes inativos."
        else:
          interpretacao = f"🎯 **Cluster {cluster_id}**: Perfil variado, requer análise adicional."

        # Adicionando a interpretação à lista
        interpretacoes.append(interpretacao)

    # Exibir as interpretações
    for interpretacao in interpretacoes:
        st.write(interpretacao)

    # Seção de filtros interativos
    st.markdown("<h4>🔍 Filtrar clientes por Cluster:</h4>", unsafe_allow_html=True)
    clusters_selecionados = st.multiselect(
        'Selecione os clusters para exibir os detalhes dos clientes:',
        frequencia_gasto['Cluster'].unique(),
        default=frequencia_gasto['Cluster'].unique()
      )

    # Filtrar e exibir os clientes
    clientes_filtrados = frequencia_gasto[frequencia_gasto['Cluster'].isin(clusters_selecionados)]
    clientes_ordenados = clientes_filtrados.sort_values(by=['FREQUENCIA_COMPRA', 'VALOR_GASTO'], ascending=[False, False])
    st.write(clientes_ordenados)

with col2:
    #st.markdown("<h2 style='text-align: center; '>📊 Criação de Campanhas de Marketing</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>📊 Criação de Campanhas de Marketing</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("""---""")

    # Criando as abas
    abas = st.tabs(["Clientes de Alto Valor", "Clientes Inativos"])

    threshold_valor = frequencia_gasto['VALOR_GASTO'].quantile(0.75)
    threshold_frequencia = frequencia_gasto['FREQUENCIA_COMPRA'].quantile(0.25)

    clientes_alto_valor = frequencia_gasto[frequencia_gasto['VALOR_GASTO'] >= threshold_valor]
    clientes_alto_valor = clientes_alto_valor.sort_values(by='FREQUENCIA_COMPRA', ascending=False)
    clientes_inativos = frequencia_gasto[frequencia_gasto['FREQUENCIA_COMPRA'] <= threshold_frequencia]

    with abas[0]:
        st.markdown("<h3 style='text-align: center; color:#2196F3;'>Clientes de Alto Valor - com maior VALOR_GASTO</h3>", unsafe_allow_html=True)

        st.markdown("""*Ações a serem realizadas*:""")
        
        # 1. Programa de Fidelidade Personalizado
        with st.expander("1 - Programa de Fidelidade Personalizado"):
            st.markdown("""
            **Objetivo**: Recompensar a lealdade desses clientes.
                    
            *Ações*:
            - Ofereça **pontos de fidelidade**.
            - Dê **descontos progressivos**.
            - Forneça **produtos exclusivos** como recompensa.
            """)
        
        # 2. Ofertas Exclusivas e Acesso Antecipado
        with st.expander("2 - Ofertas Exclusivas e Acesso Antecipado"):
            st.markdown("""
            **Objetivo**: Criar um senso de exclusividade.
                    
            *Ações*:
            - Ofereça **acesso antecipado** a novos produtos.
            - Promova **promoções especiais** que só eles podem acessar.
            - Fortaleça a relação ao fazê-los sentir-se parte de um **grupo privilegiado**.
            """)
        
        # 3. Consultoria Personalizada
        with st.expander("3 - Consultoria Personalizada"):
            st.markdown("""
            **Objetivo**: Melhorar a experiência e aumentar o valor percebido.
                    
            *Ações*:
            - Ofereça **suporte VIP**.
            - Priorize o atendimento ao cliente.
            - Ofereça **consultoria personalizada** com base nos interesses de compra e histórico de consumo.
            """)
        
        # 4. Incentivos de Indicação
        with st.expander("4 - Incentivos de Indicação"):
            st.markdown("""
            **Objetivo**: Atrair novos clientes de perfil semelhante.
                    
            *Ações*:
            - Crie programas de **indicação**.
            - Ofereça benefícios para cada **cliente novo** trazido por eles.
            - Expanda a base de clientes mantendo o foco em perfis de **alto valor**.
            """)
        
        st.write(clientes_alto_valor)

    with abas[1]:
        st.markdown("<h3 style='text-align: center; color:#FF5722;'>Clientes Inativos - com baixa FREQUENCIA_COMPRA</h3>", unsafe_allow_html=True)

        st.markdown("""*Ações a serem realizadas*:""")
        
        # 1. Campanhas de Reativação
        with st.expander("1 - Campanhas de Reativação"):
            st.markdown("""
            **Objetivo**: Incentivar a compra de clientes inativos.
                    
            *Ações*:
            - Envie uma oferta tentadora com um **desconto significativo** ou **frete grátis** para incentivar uma nova compra.
            """)
        
        # 2. Ofereça Produtos com Preço Acessível
        with st.expander("2 - Ofereça Produtos com Preço Acessível"):
            st.markdown("""
            **Objetivo**: Oferecer produtos adequados às restrições financeiras.
                    
            *Ações*:
            - Se o baixo gasto está relacionado a **restrições financeiras**, considere oferecer **produtos ou serviços mais acessíveis** para esse grupo.
            """)
        
        # 3. Pesquisa de Satisfação
        with st.expander("3 - Pesquisa de Satisfação"):
            st.markdown("""
            **Objetivo**: Entender por que os clientes estão inativos.
                    
            *Ações*:
            - Envie uma **pesquisa de feedback** para descobrir as razões da inatividade (ex.: **preço**, **falta de interesse**, **problemas com a experiência de compra**).
            """)
        
        # 4. Campanha de Desengajamento Inteligente
        with st.expander("4 - Campanha de Desengajamento Inteligente"):
            st.markdown("""
            **Objetivo**: Focar nos clientes mais engajados.
                    
            *Ações*:
            - Se os clientes não responderem às campanhas de reativação, **remova-os** das campanhas ativas e foque em **novos clientes potenciais**.
            """)
        
        st.write(clientes_inativos)

st.markdown("""---""")   
