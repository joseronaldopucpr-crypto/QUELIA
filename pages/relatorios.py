import streamlit as st
import pandas as pd
from datetime import date, datetime
from services.local_service import carregar_transacoes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


st.set_page_config(
    page_title="Relatórios",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Relatórios Financeiros")

# Carregar dados
df = carregar_transacoes()

if df.empty:
    st.warning("Nenhum dado cadastrado ainda.")
    st.stop()

# Converter data_prevista para datetime
df['data_prevista'] = pd.to_datetime(df['data_prevista'])

# ==========================================
# FILTROS
# ==========================================

st.subheader("🔍 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    data_inicio = st.date_input("Data Início", df['data_prevista'].min().date())
with col2:
    data_fim = st.date_input("Data Fim", df['data_prevista'].max().date())
with col3:
    tipo_filtro = st.selectbox("Tipo", ["Todos", "Receitas", "Despesas"])

# Aplicar filtros
df_filtrado = df[(df['data_prevista'].dt.date >= data_inicio) & (df['data_prevista'].dt.date <= data_fim)]

if tipo_filtro == "Receitas":
    df_filtrado = df_filtrado[df_filtrado['tipo'] == 'receita']
elif tipo_filtro == "Despesas":
    df_filtrado = df_filtrado[df_filtrado['tipo'] == 'despesa']

# ==========================================
# RESUMO
# ==========================================

total_receitas = df_filtrado[df_filtrado['tipo'] == 'receita']['valor'].sum()
total_despesas = df_filtrado[df_filtrado['tipo'] == 'despesa']['valor'].sum()
saldo = total_receitas - total_despesas

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 Receitas", f"R$ {total_receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col2:
    st.metric("💸 Despesas", f"R$ {total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col3:
    cor = "normal" if saldo >= 0 else "inverse"
    st.metric("📊 Saldo", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta_color=cor)

# ==========================================
# GRÁFICO DE BARRAS (VERDE E VERMELHO)
# ==========================================

st.subheader("📊 Comparativo por Categoria")

import plotly.graph_objects as go

# Agrupar por categoria e tipo
df_categorias = df_filtrado.groupby(['categoria', 'tipo'])['valor'].sum().reset_index()

# Separar receitas e despesas
receitas_cat = df_categorias[df_categorias['tipo'] == 'receita'].set_index('categoria')['valor']
despesas_cat = df_categorias[df_categorias['tipo'] == 'despesa'].set_index('categoria')['valor']

categorias = sorted(set(receitas_cat.index) | set(despesas_cat.index))

fig = go.Figure()

# Barras de receitas (VERDE)
fig.add_trace(go.Bar(
    x=categorias,
    y=[receitas_cat.get(cat, 0) for cat in categorias],
    name='Receitas',
    marker_color='#2ecc71',
    text=[f'R$ {receitas_cat.get(cat, 0):,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".") for cat in categorias],
    textposition='auto'
))

# Barras de despesas (VERMELHO)
fig.add_trace(go.Bar(
    x=categorias,
    y=[despesas_cat.get(cat, 0) for cat in categorias],
    name='Despesas',
    marker_color='#e74c3c',
    text=[f'R$ {despesas_cat.get(cat, 0):,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".") for cat in categorias],
    textposition='auto'
))

fig.update_layout(
    title="Receitas e Despesas por Categoria",
    xaxis_title="Categoria",
    yaxis_title="Valor (R$)",
    barmode='group',
    height=500,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TABELA DETALHADA
# ==========================================

st.subheader("📋 Lançamentos Detalhados")

df_exibicao = df_filtrado.copy()
df_exibicao['data_prevista'] = df_exibicao['data_prevista'].dt.strftime('%d/%m/%Y')
df_exibicao['valor'] = df_exibicao['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

df_exibicao = df_exibicao[['data_prevista', 'tipo', 'item', 'categoria', 'valor', 'status']]
df_exibicao.columns = ['Data', 'Tipo', 'Descrição', 'Categoria', 'Valor', 'Status']

st.dataframe(df_exibicao, use_container_width=True, height=400)

# Botão para exportar
if st.button("📥 Exportar para CSV", use_container_width=True):
    csv = df_exibicao.to_csv(index=False)
    st.download_button(
        label="Baixar CSV",
        data=csv,
        file_name=f"relatorio_{date.today()}.csv",
        mime="text/csv"
    )