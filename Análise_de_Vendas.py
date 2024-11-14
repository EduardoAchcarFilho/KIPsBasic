import pandas as pd
from sqlalchemy import create_engine
import urllib
import pyodbc
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import locale

# Configuração de conexão com o banco de dados
DADOS_CONEXAO = (
    "Driver={SQL Server};"
    "Server=DUXPC;"
    "Database=teste2;"
    "Trusted_Connection=yes;"
)

# Função para conectar ao banco de dados e executar a consulta
def get_data():
    try:
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        
        # Consulta SQL
        query = """
    WITH Top_Clientes AS (
        -- Seleciona os top 5 clientes com mais compras
        SELECT 
            v.ID_Cliente, 
            v.Nome AS Cliente, 
            COUNT(v.ID_venda) AS Total_Compras
        FROM 
            Vendas v
        WHERE 
            v.Nome IS NOT NULL AND v.Nome <> ''
        GROUP BY 
            v.ID_Cliente, 
            v.Nome
    ),
    Top_Clientes_Ordenados AS (
        -- Seleciona os 5 clientes com mais compras
        SELECT TOP 5 
            ID_Cliente, 
            Cliente, 
            Total_Compras
        FROM 
            Top_Clientes
        ORDER BY 
            Total_Compras DESC
    ),
    Top_Produtos_Clientes AS (
        -- Seleciona os produtos comprados pelos top 5 clientes, agrupando e somando a quantidade por produto
        SELECT 
            vi.ID_Cliente, 
            vi.Descricao AS Produto, 
            SUM(vi.QUANTIDADE) AS Total_Produtos,
            ROW_NUMBER() OVER (PARTITION BY vi.ID_Cliente ORDER BY SUM(vi.QUANTIDADE) DESC) AS rn
        FROM 
            Vendas_Itens vi
        JOIN 
            Top_Clientes_Ordenados tc ON vi.ID_Cliente = tc.ID_Cliente
        GROUP BY 
            vi.ID_Cliente, 
            vi.Descricao
    ),
    Ticket_Medio_Clientes AS (
        -- Calcula o ticket médio de cada cliente
        SELECT 
            v.ID_Cliente, 
            SUM(v.valor_liquido) / COUNT(v.ID_venda) AS Ticket_Medio
        FROM 
            Vendas v
        WHERE 
            v.valor_liquido > 0.00
            AND v.cancelamento IS NULL
            AND v.exclusao IS NULL
        GROUP BY 
            v.ID_Cliente
    )
    SELECT 
        tc.Cliente, 
        tp.Produto, 
        CAST(tp.Total_Produtos AS INT) AS Total_Produtos,
        CAST(tm.Ticket_Medio AS DECIMAL(10,2)) AS Ticket_Medio  -- Adiciona o ticket médio ao resultado
    FROM 
        Top_Clientes_Ordenados tc
    JOIN 
        Top_Produtos_Clientes tp ON tc.ID_Cliente = tp.ID_Cliente
    JOIN 
        Ticket_Medio_Clientes tm ON tc.ID_Cliente = tm.ID_Cliente  -- Faz o join com o CTE que calcula o ticket médio
    WHERE 
        tp.rn <= 5  -- Limita a 5 produtos por cliente
    ORDER BY 
        tc.Total_Compras DESC,  -- Primeira ordenação: total de compras dos clientes
        tp.Total_Produtos DESC;  -- Segunda ordenação: produtos mais comprados
        """

        # Executar a consulta e armazenar os resultados em um DataFrame
        df = pd.read_sql(query, engine )

        return df

    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return None
    
# Função para formatar o DataFrame para exibir o nome do cliente apenas uma vez
def format_data(df):
    formatted_data = []
    
    for i, row in df.iterrows():
        # Mostra o nome do cliente e o ticket médio apenas na primeira linha ou se o cliente mudar
        if i == 0 or df.iloc[i - 1]['Cliente'] != row['Cliente']:
            # Adiciona um dicionário com as informações formatadas na lista
            ticket_medio = row['Ticket_Medio']
        
            # Verifica se ticket_medio não é NaN e é do tipo string
            if isinstance(ticket_medio, str):
                # Realiza a substituição e conversão para float
                ticket_medio = ticket_medio.replace('R$', '').replace(',', '')
                ticket_medio = float(ticket_medio)
            elif isinstance(ticket_medio, (int, float)):
                # Se já for um número, apenas atribui
                ticket_medio = float(ticket_medio)
            else:
                # Caso contrário, atribui um valor padrão ou NaN
                ticket_medio = None

            formatted_data.append({
                'Cliente                                                                                                                                 ': row['Cliente'],
                'Ticket_Medio':  f"R$ {str(ticket_medio)}",  # Converte para string para manter a consistência,
                'Produto                                                                                                                             ': row['Produto'],
                'Total_Produtos': row['Total_Produtos']
            })
        else:
            # Deixa "Cliente" e "Ticket_Medio" em branco nas outras linhas do mesmo cliente
            formatted_data.append({
                'Cliente                                                                                                                                 ': '',  # Deixa em branco nas outras linhas
                'Ticket_Medio': '',  # Deixa em branco nas outras linhas
                'Produto                                                                                                                             ': row['Produto'],
                'Total_Produtos': row['Total_Produtos']
            })
    
    return pd.DataFrame(formatted_data)    

def display_metric(title, value, subtitle, subtitle2, target, change, is_positive):
    # Condicional para setas e cores
    arrow = "⬆️" if is_positive else "🔻"
    arrow_color = "green" if is_positive else "red"

    # Exibe a métrica no layout
    st.markdown(f"""
    <div style="border:2px solid #e1e1e1; padding:10px; border-radius:10px; text-align:center; background-color: #c8d6dd;">
        <h3 style="background-color: #00539C; color: white; padding: 5px; border-radius: 5px 5px 0 0;">{title}</h3>
        <p style="font-size: 45px; color: black; font-weight: bold; margin: 0;">{value}</p>
        <p style="color: gray; font-size: 16px; margin-top: -10px;">{subtitle}</p>
        <p style="color: gray; font-size: 16px; margin-top: -10px;">{subtitle2}</p>
        <p style="color: #c8d6dd; font-size: 16px; margin-top: -10px;">{target}</p>
        <p style="color: {arrow_color}; font-size: 14px; font-weight: bold;">Porcentagem: {change}% {arrow}</p>
    </div>
    """, unsafe_allow_html=True)

def display_metric2(title, value):
    # Formatação do valor para exibir com porcentagem
    formatted_value = f"R$ {value:,.2f}".replace('.', ',').replace(',', '.', 1)

    # Exibe a métrica no layout
    st.markdown(f"""
    <div style="border:2px solid #e1e1e1; padding:10px; border-radius:10px; text-align:center; background-color: #c8d6dd;">
        <h3 style="background-color: #00539C; color: white; padding: 5px; border-radius: 5px 5px 0 0;">{title}</h3>
        <p style="color: #c8d6dd; font-size: 15px; margin-top: -10px;">|</p>
        <p style="color: #c8d6dd; font-size: 17px; margin-top: -10px;">|</p>
        <p style="font-size: 45px; color: black; font-weight: bold; margin: 0;">{formatted_value}</p>
        <p style="color: #c8d6dd; font-size: 18px; margin-top: -10px;">|</p>
        <p style="color: #c8d6dd; font-size: 18px; margin-top: -10px;">|</p>
        
        
    </div>
    """, unsafe_allow_html=True)    

def display_metric3(title, subtitle, subtitle2):

    # Exibe a métrica no layout
    st.markdown(f"""
    <div style="border:2px solid #e1e1e1; padding:10px; border-radius:10px; text-align:center; background-color: #c8d6dd;">
        <h3 style="background-color: #00539C; color: white; padding: 5px; border-radius: 5px 5px 0 0;">{title}</h3>
        <p style="color: #c8d6dd; font-size: 15px; margin-top: -10px;">|</p>
        <p style="color: black; font-size: 20px; margin-top: -10px;">{subtitle}</p>
        <p style="font-size: 35px; color: black; font-weight: bold; margin: 0;">QTDE Vendida:{subtitle2}</p>
        <p style="color: #c8d6dd; font-size: 18px; margin-top: -10px;">|</p>
        <p style="color: #c8d6dd; font-size: 24px; margin-top: -10px;">|</p>
        
        
    </div>
    """, unsafe_allow_html=True)     

# Função para obter os limites de data no banco de dados
def obter_limites_data():
    try:
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        consulta_limites = """
        SELECT 
            MIN(data_cx) AS menor_data,
            MAX(data_cx) AS maior_data
        FROM Vendas
        WHERE Vendas.Exclusao IS NULL AND Vendas.Cancelamento IS NULL
        """

        # Executar a consulta e obter os resultados
        limites = pd.read_sql(consulta_limites, engine)

        # Converter os resultados para o tipo datetime.date
        menor_data = limites.iloc[0]['menor_data'].date() if pd.notna(limites.iloc[0]['menor_data']) else None
        maior_data = limites.iloc[0]['maior_data'].date() if pd.notna(limites.iloc[0]['maior_data']) else None

        return menor_data, maior_data
    except Exception as e:
        print(f"Erro ao obter os limites de data: {e}")
        return None, None

# Função para obter os dados do primeiro gráfico
def obter_dados_vendas(data_inicio, data_fim):
    try:
        data_inicio_formatada = data_inicio.strftime('%d-%m-%Y')
        data_fim_formatada = data_fim.strftime('%d-%m-%Y')
        
        consulta_sql = f"""
        WITH Totalizaçao AS (
            SELECT 
                DATEPART(HOUR, Vendas.Hora) AS hora,
                COUNT(id_venda) AS valor
            FROM Vendas
            WHERE TRY_CONVERT(datetime, data_cx) BETWEEN '{data_inicio_formatada}' AND '{data_fim_formatada}'
              AND (CAST(Vendas.Hora AS TIME) BETWEEN '05:00:00' AND '23:00:00')
            GROUP BY DATEPART(HOUR, Vendas.Hora)
        )
        SELECT 
            FORMAT(GETDATE(), 'dd/MM/yyyy') AS Data,
            CONCAT(FORMAT(hora, '00'), ':00') AS Horas,
            SUM(valor) AS QTDE
        FROM Totalizaçao
        WHERE hora BETWEEN 5 AND 22
        GROUP BY hora
        ORDER BY hora;
        """
        
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        dados = pd.read_sql(consulta_sql, engine)
        return dados, consulta_sql
    except Exception as e:
        return f"Erro ao executar a consulta SQL: {e}", None

# Função para obter os dados do segundo gráfico
def obter_dados_meios_pagamento(data_inicio, data_fim):
    try:
        data_inicio_formatada = data_inicio.strftime('%d-%m-%Y')
        data_fim_formatada = data_fim.strftime('%d-%m-%Y')
        
        consulta_sql = f"""
        SELECT 
            Meio AS Meios_de_Pagamentos, 
            SUM(Valor) AS Valor
        FROM 
            Vendas_Receber
        WHERE 
            Exclusao IS NULL 
            AND Meio IS NOT NULL 
            AND Data_Turno BETWEEN '{data_inicio_formatada}' AND '{data_fim_formatada}'
        GROUP BY 
            Meio
        ORDER BY 
            Valor DESC;
        """
        
        conexao_string = DADOS_CONEXAO
        
        # Criar a string de conexão com o SQLAlchemy
        try:
            params = urllib.parse.quote_plus(conexao_string)
            engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        except Exception as e:
            return f"Erro ao criar engine: {e}", None

        # Executando a consulta SQL
        try:
            dados = pd.read_sql(consulta_sql, engine)
            return dados, consulta_sql
        except Exception as e:
            return f"Erro ao executar a consulta SQL Meios: {e}", None
    except Exception as e:
        return f"Erro inesperado: {e}", None
    
# Função para obter dados para o gráfico dos 10 principais produtos
def obter_dados_produtos(data_inicio, data_fim):
    try:
        data_inicio_formatada = data_inicio.strftime('%d-%m-%Y')
        data_fim_formatada = data_fim.strftime('%d-%m-%Y')

        consulta_sql = f"""
        SELECT TOP 10 
            Descricao AS Produto, 
            ROUND(SUM(Valor_liquido), 2) AS Valor
        FROM 
            Vendas_Itens
        WHERE 
            Exclusao IS NULL 
            AND Cancelamento IS NULL 
            AND Data_cx BETWEEN '{data_inicio_formatada}' AND '{data_fim_formatada}'
        GROUP BY 
            Descricao
        ORDER BY 
            Valor DESC;
        """
        
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        dados = pd.read_sql(consulta_sql, engine)
        
        return dados, consulta_sql
    except Exception as e:
        return f"Erro ao executar a consulta SQL Produtos: {e}"   

# Função para obter os dados das categorias
def obter_dados_categorias(data_inicio, data_fim):
    try:
        data_inicio_formatada = data_inicio.strftime('%d-%m-%Y')
        data_fim_formatada = data_fim.strftime('%d-%m-%Y')

        consulta_sql = f"""
        SELECT TOP 6 
            ItensGrupos.Descricao AS Categoria, 
            ROUND(SUM(Vendas_Itens.Valor_liquido), 2) AS Valor
        FROM 
            Vendas_Itens
        LEFT JOIN 
            Itens ON Itens.ID_Item = Vendas_Itens.ID_Item
        LEFT JOIN 
            ItensGrupos ON Vendas_Itens.ID_Grupo = ItensGrupos.ID_Grupo
        WHERE 
            Vendas_Itens.Exclusao IS NULL 
            AND Data_cx BETWEEN '{data_inicio_formatada}' AND '{data_fim_formatada}'
        GROUP BY 
            ItensGrupos.Descricao
        ORDER BY 
            Valor DESC;
        """

        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        dados = pd.read_sql(consulta_sql, engine)
        return dados, consulta_sql
    except Exception as e:
        return f"Erro ao executar a consulta SQL Categorias: {e}", None     
    
# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Função para calcular o total de vendas com base no intervalo de datas
def calcular_total_vendas(data_inicio, data_fim):
    try:
        data_inicio_str = data_inicio.strftime('%d-%m-%Y')
        data_fim_str = data_fim.strftime('%d-%m-%Y')

        consulta_sql = f"""
        SELECT SUM(Valor_itens) AS valor
        FROM Vendas
        WHERE Exclusao IS NULL 
        AND Cancelamento IS NULL
        AND Data_cx BETWEEN '{data_inicio_str}' AND '{data_fim_str}';
        """

        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        total_vendas = pd.read_sql(consulta_sql, engine)

        return total_vendas.iloc[0]['valor'] if not total_vendas.empty and total_vendas.iloc[0]['valor'] is not None else 0
    except Exception as e:
        st.error(f"Erro ao calcular o total de vendas: {e}")
        return 0  # Retornar 0 em caso de erro
    
# Função para calcular o crescimento percentual de vendas
def calcular_crescimento_percentual_vendas():
    try:
        # Calcular as datas para o mês atual
        hoje = datetime.today()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_atual = (primeiro_dia_mes_atual + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Calcular as datas para o mês anterior
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

        # Formatar as datas para o formato 'dd-mm-yyyy'
        data_inicial_atual_formatada = primeiro_dia_mes_atual.strftime('%d-%m-%Y')
        data_final_atual_formatada = ultimo_dia_mes_atual.strftime('%d-%m-%Y')
        data_inicial_anterior_formatada = primeiro_dia_mes_anterior.strftime('%d-%m-%Y')
        data_final_anterior_formatada = ultimo_dia_mes_anterior.strftime('%d-%m-%Y')

        # Consulta SQL para o período atual
        consulta_sql_atual = f"""
        SELECT SUM(Valor_itens) AS valor
        FROM Vendas
        WHERE Data_cx BETWEEN '{data_inicial_atual_formatada}' AND '{data_final_atual_formatada}'
          AND Exclusao IS NULL AND Cancelamento IS NULL;
        """

        # Consulta SQL para o período anterior
        consulta_sql_anterior = f"""
        SELECT SUM(Valor_itens) AS valor
        FROM Vendas
        WHERE Data_cx BETWEEN '{data_inicial_anterior_formatada}' AND '{data_final_anterior_formatada}'
          AND Exclusao IS NULL AND Cancelamento IS NULL;
        """

        # Criar a string de conexão com o SQLAlchemy
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        # Obter os resultados para os dois períodos
        vendas_atual = pd.read_sql(consulta_sql_atual, engine)
        vendas_anterior = pd.read_sql(consulta_sql_anterior, engine)
        

        # Extrair os valores, considerando 0 se o resultado for vazio
        valor_atual = vendas_atual.iloc[0]['valor'] if not vendas_atual.empty and vendas_atual.iloc[0]['valor'] is not None else 0
        valor_anterior = vendas_anterior.iloc[0]['valor'] if not vendas_anterior.empty and vendas_anterior.iloc[0]['valor'] is not None else 0
        
        # Calcular o crescimento percentual, evitando divisão por zero
        if valor_anterior == 0:
            crescimento_percentual = 0 if valor_atual == 0 else 100.0
        else:
            crescimento_percentual = ((valor_atual - valor_anterior) / valor_anterior) * 100.0

        # Retornar os valores formatados e o crescimento percentual
        resultado = {
            "Total vendas mês anterior": f"R$ {valor_anterior:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Total vendas mês atual": f"R$ {valor_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Crescimento percentual": f"{crescimento_percentual:.2f}%"
        }
        
        return resultado

    except Exception as e:
        return f"Erro ao calcular o crescimento percentual de vendas: {e}"
    
def calcular_ticket_medio(data_inicio, data_fim):
    try:
        # Formatar as datas no formato aceito pelo SQL Server
        data_inicio_str = data_inicio.strftime('%d-%m-%Y')
        data_fim_str = data_fim.strftime('%d-%m-%Y')

        # Consulta SQL para calcular o ticket médio no intervalo de datas
        consulta_sql = f"""
        SELECT SUM(valor_liquido) / COUNT(id_venda) AS ticket_medio
        FROM vendas
        WHERE valor_liquido > 0.00
          AND cancelamento IS NULL
          AND exclusao IS NULL
          AND Data_cx BETWEEN '{data_inicio_str}' AND '{data_fim_str}';
        """

        # Criar a string de conexão com o SQLAlchemy
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        # Executar a consulta e obter o resultado
        resultado = pd.read_sql(consulta_sql, engine)

        # Verificar se o resultado é válido e retornar o valor do ticket médio
        return resultado.iloc[0]['ticket_medio'] if not resultado.empty and resultado.iloc[0]['ticket_medio'] is not None else 0
    except Exception as e:
        # Exibir a mensagem de erro no Streamlit
        st.error(f"Erro ao calcular o ticket médio: {e}")
        return 0  # Retornar 0 em caso de erro   

def vendedor_com_mais_vendas(data_inicio, data_fim):
    try:
        # Formatar as datas no formato aceito pelo SQL Server
        data_inicio_str = data_inicio.strftime('%d-%m-%Y')
        data_fim_str = data_fim.strftime('%d-%m-%Y')

        # Consulta SQL para encontrar o vendedor com mais vendas no intervalo de datas
        consulta_sql = f"""
        SELECT TOP 1 
            Vendedor, 
            COUNT(ID_Venda) AS QTDE_Total_vendas
        FROM Vendas
        WHERE Exclusao IS NULL 
          AND Cancelamento IS NULL
          AND Data_cx BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        GROUP BY Vendedor
        ORDER BY QTDE_Total_vendas DESC;
        """

        # Criar a string de conexão com o SQLAlchemy
        params = urllib.parse.quote_plus(DADOS_CONEXAO)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        # Executar a consulta e obter o resultado
        resultado = pd.read_sql(consulta_sql, engine)

        # Verificar se o resultado é válido e retornar o nome do vendedor e o total de vendas
        if not resultado.empty:
            vendedor = resultado.iloc[0]['Vendedor']
            total_vendas = str(int(resultado.iloc[0]['QTDE_Total_vendas']))
            return {"Vendedor": vendedor, "Total Vendas": total_vendas}
        else:
            return {"Mensagem": "Nenhum dado encontrado para o período especificado."}
    except Exception as e:
        # Exibir a mensagem de erro no Streamlit
        st.error(f"Erro ao buscar o vendedor com mais vendas: {e}")
        return {"Mensagem": "Erro ao buscar dados"}    

# Configuração do layout em modo wide
st.set_page_config(layout="wide")

st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>KPIs - 🛒Análise de Vendas🛒</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

# Obter os limites de data para configurar o slider
menor_data, maior_data = obter_limites_data()

# Selecionar o período de datas usando um slider
data_intervalo = st.slider(
        'Selecione o Período',
        min_value=menor_data,
        max_value=maior_data,
        value=(menor_data, maior_data),
        format="DD/MM/YYYY"
    )

# Obter as datas de início e fim
data_inicio, data_fim = data_intervalo

# Criar as colunas para o layout
col11, col12, col13, col14 = st.columns([1, 1, 1 ,1])

with col11:
 # Uso da função no Streamlit para calcular o crescimento percentual de vendas
 resultado = calcular_crescimento_percentual_vendas()

 # Verifica se não houve erro no cálculo
 if resultado and "erro" not in resultado:
    # Configura os parâmetros para exibição
    valor_anterior = resultado.get("Total vendas mês anterior")
    valor_atual = resultado.get("Total vendas mês atual")
    crescimento_percentual = resultado.get("Crescimento percentual")

    # Inicializa is_positive como False por padrão
    is_positive = False

    #  Verifica se crescimento_percentual não é None
    if crescimento_percentual is not None:
        try:
            # Converte crescimento_percentual para float
            crescimento_percentual = float(crescimento_percentual)
            # Define se o crescimento é positivo ou negativo
            is_positive = crescimento_percentual >= 0
        except ValueError:
            # Tratamento para o caso de conversão falhar
            print("Erro: crescimento_percentual não é um número válido.")     
    else:
        # Tratamento para o caso de crescimento_percentual ser None
        print("Erro: crescimento_percentual não foi calculado corretamente.")

    # Exibe a métrica usando a função display_metric
    display_metric(
        title="Crescimento de Vendas",
        value=crescimento_percentual,
        subtitle=f"Vendas Mês Anterior: R$ {valor_anterior}",
        subtitle2=f"Vendas Mês Atual: R$ {valor_atual}",
        target=f"Vendas Atuais: R$ {valor_atual}",
        change=f"{(crescimento_percentual)}",
        is_positive=is_positive
    )
 else:
    # Exibe o erro caso ocorra
    st.error(f"Erro ao calcular o crescimento percentual de vendas: {resultado.get('erro', 'Erro desconhecido')}")

with col12:
    # Calcular o total de vendas com base no período selecionado
    total_vendas = calcular_total_vendas(data_inicio, data_fim)

    # Exibe a métrica usando a função display_metric
    display_metric2(
        title="Total de Vendas Geral",
        value=total_vendas,
    )

with col13:
    # Calcular o total de vendas com base no período selecionado
    ticket_medio = calcular_ticket_medio(data_inicio, data_fim)

    # Exibe a métrica usando a função display_metric
    display_metric2(
        title="Ticket Médio Geral",
        value=ticket_medio,
    )    

with col14:
    # Calcular o total de vendas com base no período selecionado
    resultado = vendedor_com_mais_vendas(data_inicio, data_fim)

    vendedor = resultado.get("Vendedor")
    total_vendas = resultado.get("Total Vendas")

    # Exibe a métrica usando a função display_metric
    display_metric3(
        title="Vendedor TOP 1",
        subtitle=vendedor,
        subtitle2=total_vendas
    )
       
st.markdown("""---""")

st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>🥇 Top 5 Clientes 🥇 e seus Top 5 Produtos</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

st.write("Aqui está uma lista dos top 5 clientes e os 5 produtos mais comprados por cada um deles:")

# Obter os dados do banco de dados
data = get_data()

# Exibir os dados se a consulta for bem-sucedida
if data is not None:
    formatted_data = format_data(data)
    
    # Aplica o estilo para destacar o produto mais vendido na coluna Total_Produtos
    styled_df = formatted_data.style.highlight_max(subset=['Total_Produtos','Ticket_Medio'], color='yellow')
    
    # Exibe o DataFrame estilizado no Streamlit
    st.dataframe(styled_df)        

st.markdown("""---""")
st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>📈 Quantidade de Vendas por Hora ⏰</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )


# Criar as colunas para o layout
col1, col2 = st.columns([2, 1])
# Colocar o slider e os gráficos na coluna 1
with col1:
    # Verificar se o período é válido
    if data_inicio > data_fim:
        st.error('A data de início não pode ser maior que a data de fim.')
    else:
        # Obter os dados para o primeiro gráfico
        dados_vendas, consulta_sql_vendas = obter_dados_vendas(data_inicio, data_fim)
        
        # Verificar se 'dados_vendas' é um DataFrame e se há dados para exibir
        if isinstance(dados_vendas, pd.DataFrame) and not dados_vendas.empty:
            # Criar o gráfico de linha para quantidade de vendas por hora
            fig_vendas = px.line(dados_vendas, x='Horas', y='QTDE', text='QTDE', markers=True)
            # Exibir o gráfico
            st.plotly_chart(fig_vendas)
        elif isinstance(dados_vendas, pd.DataFrame) and dados_vendas.empty:
            st.warning('Nenhum dado encontrado para o período selecionado.')
        else:
            st.error(dados_vendas)

        st.text_area('Criação do gráfico de linha acima(plotly)', "px.line(dados_vendas, x='Horas', y='QTDE', title='Quantidade de Vendas por Hora', text='QTDE', markers=True)", height=30)    

with col2:
    if consulta_sql_vendas:
        st.text_area('Código SQL para o Gráfico de Vendas por Hora', consulta_sql_vendas, height=560)    

st.markdown("""---""")
st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>💰 Meios de Pagamento mais utilizados 💳</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

col3, col4 = st.columns([2, 1])
with col3:
        # Obter os dados para o segundo gráfico
        dados_meios, consulta_sql_meios = obter_dados_meios_pagamento(data_inicio, data_fim)

        # Verificar se 'dados_meios' é um DataFrame e se há dados para exibir
        if isinstance(dados_meios, pd.DataFrame) and not dados_meios.empty:
            # Criar o gráfico de barras para os meios de pagamento
            fig_meios = px.bar(dados_meios, x='Meios_de_Pagamentos', y='Valor', text='Valor')
            # Formatação do texto para o formato R$ 3.091.840,48
            fig_meios.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            #fig_meios.update_traces(texttemplate='R$ %{text:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
            # Exibir o gráfico
            st.plotly_chart(fig_meios)
        elif isinstance(dados_meios, pd.DataFrame) and dados_meios.empty:
            st.warning('Nenhum dado encontrado para os meios de pagamento no período selecionado.')
        else:
            st.error(dados_meios)

        st.text_area('Criação do gráfico de barras acima(plotly)', "px.bar(dados_meios, x='Meios_de_Pagamentos', y='Valor', title='Meios de Pagamento mais utilizados', text='Valor')", height=30)


with col4:
    if consulta_sql_meios:
       st.text_area('Código SQL para o Gráfico de Meios de Pagamento', consulta_sql_meios, height=560)


st.markdown("""---""")
st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>🏅 Top 10 Produtos mais vendidos 🛒</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

col5, col6 = st.columns([2, 1])
with col5:
        # Obter os dados com base no intervalo selecionado no slider
        dados_produtos,consulta_sql_produtos = obter_dados_produtos(data_inicio, data_fim)

        # Verificar se 'dados_produtos' é um DataFrame e se há dados para exibir
        if isinstance(dados_produtos, pd.DataFrame) and not dados_produtos.empty:
            # Criar o gráfico de barras
            fig_produtos = px.bar(dados_produtos, x='Produto', y='Valor', text='Valor')
            fig_produtos.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            

            # Exibir o gráfico
            st.plotly_chart(fig_produtos)
        elif isinstance(dados_produtos, pd.DataFrame) and dados_produtos.empty:
            st.warning('Nenhum dado encontrado para o período selecionado.')
        else:
            st.error(dados_produtos)  
  
        st.text_area('Criação do gráfico de barras acima(plotly)', "fig_produtos = px.bar(dados_produtos, x='Produto', y='Valor', title='Top 10 Produtos mais vendidos', text='Valor')                                                                  fig_produtos.update_traces(texttemplate='%{text:.2f}', textposition='outside') ", height=30) 


with col6:
  if consulta_sql_produtos:         
     st.text_area('Código SQL para o Gráfico Top 10 Produtos', consulta_sql_produtos, height=562)  

st.markdown("""---""")
st.markdown(
        """
        <div style="background-color:#262730; padding: 5px; border-radius: 10px;">
            <h2 style='text-align: center;'>🎖️ Top 6 Categorias mais rentáveis 📚</h2>
            <p></p>
        </div>
        """, unsafe_allow_html=True
    )

col7, col8 = st.columns([2, 1])
with col7:
        # Obter os dados das categorias
        dados_categorias, consulta_sql_categorias = obter_dados_categorias(data_inicio, data_fim)

        # Verificar se 'dados_categorias' é um DataFrame e se há dados para exibir
        if isinstance(dados_categorias, pd.DataFrame) and not dados_categorias.empty:
            # Criar o gráfico de pizza para as categorias
            fig_categorias = px.pie(dados_categorias, names='Categoria', values='Valor', title='Top 6 Categorias mais rentabelizadas', hole=0.3)
            # Exibir o gráfico
            st.plotly_chart(fig_categorias)
        elif isinstance(dados_categorias, pd.DataFrame) and dados_categorias.empty:
            st.warning('Nenhum dado encontrado para as categorias no período selecionado.')
        else:
            st.error(dados_categorias)

        st.text_area('Criação do gráfico de pizza acima(plotly)', "px.pie(dados_categorias, names='Categoria', values='Valor', title='Top 6 Categorias mais rentabelizadas', hole=0.3)", height=30)     
  

with col8:
    if consulta_sql_categorias: 
        st.text_area('Código SQL para o Gráfico de Categorias', consulta_sql_categorias, height=562)  



  

st.markdown("""---""")        
