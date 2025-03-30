import streamlit as st
import pandas as pd
import os

st.title("Projeto de Contabilidade de Custos e Gerencial")

st.markdown("---")

try:
    # Lê a planilha diretamente do diretório raiz (sem usar __file__)
    caminho_arquivo = "dados.xlsx"

    # Lê a planilha com caminho absoluto
    planilhas = pd.read_excel(caminho_arquivo, sheet_name=None)
    movimentacao = planilhas["Movimentacao Bancaria"]
    plano_contas = planilhas["Plano de Contas"]

    st.subheader("💰 Receita Bruta Mensal (com defasagem de 1 mês)")

    # Converte a coluna de data para datetime
    movimentacao["Data"] = pd.to_datetime(movimentacao["Data"])

    # Filtra apenas entradas (receitas)
    receitas = movimentacao[movimentacao["Entrada"].notnull()].copy()

    # Junta com o plano de contas para verificar qual natureza é receita
    plano_contas["Codigo"] = plano_contas["Codigo"].astype(str)
    receitas["Natureza"] = receitas["Natureza"].astype(str)

    receitas = receitas.merge(plano_contas, how="left", left_on="Natureza", right_on="Codigo")

    # Filtra receitas cujo código comece com 111010 (ex: MARKETING DIRETO, PUBLICIDADE)
    receitas_filtradas = receitas[receitas["Natureza"].str.startswith("111010")]

    # Agrupa por mês de prestação (Data) e soma os valores
    receita_mensal = receitas_filtradas.groupby(receitas_filtradas["Data"].dt.to_period("M"))["Entrada"].sum()

    # Aplica defasagem de 1 mês (faturamento ocorre 1 mês depois da prestação)
    receita_mensal.index = receita_mensal.index.to_timestamp()
    receita_mensal_defasada = receita_mensal.shift(1)

    # Formata índice da data para "Jan/2023"
    receita_formatada = receita_mensal_defasada.copy()
    receita_formatada.index = receita_formatada.index.strftime("%b/%Y")

    # Formata os valores em reais
    receita_formatada = receita_formatada.apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Remove valores nulos da tabela formatada (ex: R$ nan)
    receita_formatada = receita_formatada.dropna()

    # Mostra a tabela formatada
    st.write("Receita por mês (faturada com defasagem de 1 mês):")
    st.dataframe(receita_formatada)

    # Gráfico usa os dados reais (não formatados)
    st.line_chart(receita_mensal_defasada)

    st.markdown("---")

    # --- DESPESAS MENSAIS POR COMPETÊNCIA ---
    st.subheader("💸 Despesas Mensais por Competência")

    # Filtra apenas Saidas com valor positivo
    despesas = movimentacao[pd.to_numeric(movimentacao["Saida"], errors="coerce") > 0].copy()

    # Corrige os tipos para garantir o merge correto
    despesas["Natureza"] = despesas["Natureza"].astype(str).str.split(".").str[0]
    plano_contas["Codigo"] = plano_contas["Codigo"].astype(str)

    # Faz o merge corretamente agora
    despesas = despesas.merge(plano_contas, how="left", left_on="Natureza", right_on="Codigo")

    # Cria coluna "Mês" no formato bonito
    despesas["Mês"] = despesas["Data"].dt.strftime("%b/%Y")

    # Agrupa por Mês e Tipo de Despesa (apenas se tiver descrição)
    despesas_validas = despesas[despesas["Descricao"].notnull()]
    despesas_agrupadas = despesas_validas.groupby(["Mês", "Descricao"])["Saida"].sum().unstack().fillna(0)


    # Salva uma versão formatada com valores em R$
    despesas_formatadas = despesas_agrupadas.applymap(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Mostra a tabela com colunas por tipo de despesa
    st.write("Despesas por mês e por tipo:")
    st.dataframe(despesas_formatadas)

    # Gráfico de barras empilhadas (valores reais)
    st.bar_chart(despesas_agrupadas)

    st.markdown("---")

    # --- CUSTO ESTIMADO POR CONTRATO/CLIENTE ---
    st.subheader("📦 Custo Estimado por Contrato/Cliente")

    # Agrupa as receitas por cliente
    receitas_clientes = movimentacao[movimentacao["Entrada"].notnull()]
    receita_por_cliente = receitas_clientes.groupby("Historico")["Entrada"].sum()

    # Soma total das receitas e despesas

    total_receita = receita_por_cliente.sum()
    total_despesas = despesas["Saida"].sum()

    # Estima o custo proporcional por cliente
    custo_estimado = (receita_por_cliente / total_receita) * total_despesas

    # Calcula margem estimada
    margem = receita_por_cliente - custo_estimado

    # Cria DataFrame final
    df_clientes = pd.DataFrame({
        "Receita Total": receita_por_cliente,
        "Custo Estimado": custo_estimado,
        "Margem Estimada": margem
    })

    # Formatação
    df_formatado = df_clientes.copy()
    for coluna in ["Receita Total", "Custo Estimado", "Margem Estimada"]:
        df_formatado[coluna] = df_formatado[coluna].apply(lambda x: 
        f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Mostra tabela formatada
    st.dataframe(df_formatado)

    # Gráfico: Receita vs. Custo (Top 20 clientes por receita)
    top_20_clientes = df_clientes.sort_values("Receita Total", ascending=False).head(20)
    st.write("Comparativo Receita vs. Custo dos 20 principais clientes")
    st.bar_chart(top_20_clientes[["Receita Total", "Custo Estimado"]])

except Exception as e:
    st.error("⚠️ Ocorreu um erro ao carregar os dados. Verifique se o arquivo 'dados.xlsx' está presente e no formato correto.")
