## KPI's Vendas
Este é um pequeno exemplo de KPIs para análise de vendas. Utilizei o Plotly para exibir alguns gráficos e incluí os códigos SQL responsáveis pelas consultas, juntamente com os códigos do Plotly para a visualização.
As KPIs apresentadas são:

    Top 5 Clientes  e seus Top 5 Produtos: Esta métrica identifica os cinco principais clientes, com base no valor ou na frequência de compras, e lista os cinco produtos que esses clientes mais compram. Esse insight ajuda a personalizar ofertas e compreender melhor as preferências dos principais clientes.
   
    Quantidade de Vendas por Hora: Mostra o número de vendas realizadas em diferentes horas do dia. Essa visualização ajuda a entender o comportamento das vendas ao longo de um período de 24 horas, permitindo identificar os horários de maior e menor atividade.
    
    Meios de Pagamento mais utilizados: Compara as diferentes formas de pagamento que os consumidores escolhem ao realizar compras. Essa análise pode ajudar a ajustar as opções de pagamento, melhorar a experiência de compra e até mesmo identificar oportunidades de otimização, como a introdução de novas tecnologias ou serviços de pagamento.
    
    Top 10 Produtos mais vendidos: Lista os dez produtos mais populares e frequentemente comprados pelos clientes. Essa análise é essencial para identificar quais produtos têm o maior volume de vendas ou geram mais receita, facilitando decisões sobre estoque e promoções.
    
    Top 6 Categorias mais rentáveis: Identifica as seis categorias de produtos ou serviços que geram mais lucro para a empresa. Essas categorias são as mais lucrativas e têm um impacto significativo nas finanças, seja pelo alto volume de vendas ou pelas margens de lucro elevadas.
    
![Capturar](https://github.com/user-attachments/assets/6cb34853-0340-4aa0-99bc-32083a4c8929)

Na página seguinte, criei uma segmentação de clientes utilizando o algoritmo K-Means para realizar o agrupamento com base na frequência de compra e no valor gasto pelos clientes. A partir das médias das características de cada grupo, foi possível criar uma interpretação dos segmentos, classificando-os como: Clientes VIP, Clientes com Baixa Frequência e Clientes Inativos.
Essas informações são usadas para fornecer insights sobre o comportamento dos clientes , neste caso aqui elaborei um exemplo de como trabalhar em conjunto com outros setores,  usei o setor de Marketing,
Deixei exemplos de ações específicas que seriam tomadas para os diferentes segmentos, no caso aqui para criar campanhas focadas em fidelização ou reativação de clientes inativos. 
Tudo isso é exibido por meio de gráficos, tabelas e textos interativos no Streamlit.

![Capturar1](https://github.com/user-attachments/assets/83795a7f-49dd-4e1b-97c9-3cb92c45c5c1)
