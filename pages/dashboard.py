import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from services.local_service import carregar_transacoes
from fpdf import FPDF
import tempfile
import os as os_module
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Financeiro - Fluxo de Caixa")


# ==========================================
# FUNÇÕES
# ==========================================

def formatar_moeda(valor):
    try:
        if valor == 0 or valor < 0.01:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def formatar_data_br(data):
    if isinstance(data, str):
        data = datetime.strptime(data, "%Y-%m-%d")
    return data.strftime("%d/%m/%Y")


def calcular_fluxo_caixa(df, ano, mes_inicio=1, mes_fim=12):
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    resultados = []
    saldo_anterior = 0

    for mes in range(mes_inicio, mes_fim + 1):
        df_mes = df[(df['data_prevista'].dt.year == ano) & (df['data_prevista'].dt.month == mes)]

        total_receitas = df_mes[df_mes['tipo'] == 'receita']['valor'].sum()
        total_despesas = df_mes[df_mes['tipo'] == 'despesa']['valor'].sum()
        fluxo_mes = total_receitas - total_despesas
        saldo_atual = saldo_anterior + fluxo_mes

        resultados.append({
            'Mês': meses[mes - 1],
            'Mês Nº': mes,
            'Receitas': total_receitas,
            'Despesas': total_despesas,
            'Fluxo do Mês': fluxo_mes,
            'Saldo Anterior': saldo_anterior,
            'Saldo Atual': saldo_atual
        })
        saldo_anterior = saldo_atual

    return pd.DataFrame(resultados)


def gerar_pdf_relatorio(df_fluxo, df_filtrado, ano, periodo):
    """Gera PDF completo com tabelas e gráficos organizados"""
    from fpdf import FPDF
    import tempfile
    import matplotlib.pyplot as plt

    def formatar_moeda_local(valor):
        try:
            if valor == 0 or valor < 0.01:
                return "R$ 0,00"
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    def formatar_data_br_local(data):
        if isinstance(data, str):
            data = datetime.strptime(data, "%Y-%m-%d")
        return data.strftime("%d/%m/%Y")

    pdf = FPDF(orientation='L')
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATORIO FINANCEIRO COMPLETO", 0, 1, 'C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Periodo: {periodo} - {ano}", 0, 1, 'C')
    pdf.cell(0, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. RESUMO DO PERIODO", 0, 1, 'L')
    pdf.set_font("Arial", "", 10)

    total_receitas = df_filtrado[df_filtrado['tipo'] == 'receita']['valor'].sum()
    total_despesas = df_filtrado[df_filtrado['tipo'] == 'despesa']['valor'].sum()
    saldo = total_receitas - total_despesas

    pdf.cell(0, 7, f"Total Receitas: {formatar_moeda_local(total_receitas)}", 0, 1)
    pdf.cell(0, 7, f"Total Despesas: {formatar_moeda_local(total_despesas)}", 0, 1)
    pdf.cell(0, 7, f"Saldo do Periodo: {formatar_moeda_local(saldo)}", 0, 1)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. FLUXO DE CAIXA MENSAL", 0, 1, 'L')

    pdf.set_font("Arial", "B", 9)
    larguras = [30, 30, 30, 30, 30]
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(larguras[0], 8, "Mes", 1, 0, 'C', 1)
    pdf.cell(larguras[1], 8, "Receitas", 1, 0, 'C', 1)
    pdf.cell(larguras[2], 8, "Despesas", 1, 0, 'C', 1)
    pdf.cell(larguras[3], 8, "Fluxo", 1, 0, 'C', 1)
    pdf.cell(larguras[4], 8, "Saldo", 1, 1, 'C', 1)

    pdf.set_font("Arial", "", 8)
    for i, (_, row) in enumerate(df_fluxo.iterrows()):
        if i % 2 == 0:
            pdf.set_fill_color(240, 240, 240)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.cell(larguras[0], 7, row['Mês'][:10], 1, 0, 'L', 1)
        pdf.set_text_color(0, 150, 0)
        pdf.cell(larguras[1], 7, formatar_moeda_local(row['Receitas']), 1, 0, 'R', 1)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(larguras[2], 7, formatar_moeda_local(row['Despesas']), 1, 0, 'R', 1)

        fluxo = row['Fluxo do Mês']
        pdf.set_text_color(0, 150, 0) if fluxo >= 0 else pdf.set_text_color(200, 0, 0)
        pdf.cell(larguras[3], 7, formatar_moeda_local(fluxo), 1, 0, 'R', 1)

        saldo = row['Saldo Atual']
        pdf.set_text_color(0, 150, 0) if saldo >= 0 else pdf.set_text_color(200, 0, 0)
        pdf.cell(larguras[4], 7, formatar_moeda_local(saldo), 1, 1, 'R', 1)
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5)

    # GRÁFICO DE PIZZA - RECEITAS
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. DISTRIBUICAO POR CATEGORIA - RECEITAS", 0, 1, 'L')

    receitas_categoria = df_filtrado[df_filtrado['tipo'] == 'receita'].groupby('categoria')['valor'].sum().sort_values(ascending=False)

    if not receitas_categoria.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        cores_receitas = ['#2ecc71', '#27ae60', '#1e8449', '#58d68d', '#7dcea0', '#a9dfbf', '#1f8a4c', '#3a9e6d']

        total = receitas_categoria.sum()
        valores = list(receitas_categoria.values)

        wedges, texts, autotexts = ax.pie(valores, labels=None, autopct='%1.1f%%',
                                          colors=cores_receitas[:len(receitas_categoria)], startangle=90,
                                          textprops={'fontsize': 9, 'fontweight': 'bold'}, pctdistance=0.85)

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')

        ax.legend(wedges, [f"{cat}\n({val / total * 100:.1f}%)" for cat, val in
                           zip(receitas_categoria.index, receitas_categoria.values)],
                  title="Categorias", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)

        ax.set_title('Receitas por Categoria', fontsize=12, fontweight='bold')
        ax.axis('equal')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as img_temp:
            plt.savefig(img_temp.name, format='PNG', dpi=150, bbox_inches='tight')
            img_path = img_temp.name
        plt.close()

        pdf.image(img_path, x=30, y=pdf.get_y(), w=250)
        try:
            os.unlink(img_path)
        except:
            pass

    pdf.ln(120)

    # GRÁFICO DE PIZZA - DESPESAS
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "4. DISTRIBUICAO POR CATEGORIA - DESPESAS", 0, 1, 'L')

    despesas_categoria = df_filtrado[df_filtrado['tipo'] == 'despesa'].groupby('categoria')['valor'].sum().sort_values(ascending=False)

    if not despesas_categoria.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        cores_despesas = ['#e74c3c', '#c0392b', '#e67e22', '#f39c12', '#d35400', '#e67e22', '#ff6b6b', '#ee5a24']

        total = despesas_categoria.sum()
        valores = list(despesas_categoria.values)

        wedges, texts, autotexts = ax.pie(valores, labels=None, autopct='%1.1f%%',
                                          colors=cores_despesas[:len(despesas_categoria)], startangle=90,
                                          textprops={'fontsize': 9, 'fontweight': 'bold'}, pctdistance=0.85)

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')

        ax.legend(wedges, [f"{cat}\n({val / total * 100:.1f}%)" for cat, val in
                           zip(despesas_categoria.index, despesas_categoria.values)],
                  title="Categorias", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)

        ax.set_title('Despesas por Categoria', fontsize=12, fontweight='bold')
        ax.axis('equal')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as img_temp:
            plt.savefig(img_temp.name, format='PNG', dpi=150, bbox_inches='tight')
            img_path = img_temp.name
        plt.close()

        pdf.image(img_path, x=30, y=pdf.get_y(), w=250)
        try:
            os.unlink(img_path)
        except:
            pass

    pdf.ln(120)

    # ==========================================
    # ÚLTIMOS LANÇAMENTOS (200 REGISTROS)
    # ==========================================
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "5. ULTIMOS LANCAMENTOS", 0, 1, 'L')

    # Aumentar para 200 registros
    df_ultimos = df_filtrado.sort_values('data_prevista', ascending=False).head(200)

    if not df_ultimos.empty:
        # Cabeçalho mais compacto
        pdf.set_font("Arial", "B", 7)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(12, 5, "ID", 1, 0, 'C', 1)
        pdf.cell(22, 5, "Data", 1, 0, 'C', 1)
        pdf.cell(15, 5, "Tipo", 1, 0, 'C', 1)
        pdf.cell(50, 5, "Descricao", 1, 0, 'C', 1)
        pdf.cell(25, 5, "Categoria", 1, 0, 'C', 1)
        pdf.cell(22, 5, "Valor", 1, 1, 'C', 1)

        pdf.set_font("Arial", "", 6)
        linha_atual = pdf.get_y()

        for i, (_, row) in enumerate(df_ultimos.iterrows()):
            # Nova página quando necessário
            if linha_atual > 270:
                pdf.add_page()
                pdf.set_font("Arial", "B", 7)
                pdf.set_fill_color(200, 200, 200)
                pdf.cell(12, 5, "ID", 1, 0, 'C', 1)
                pdf.cell(22, 5, "Data", 1, 0, 'C', 1)
                pdf.cell(15, 5, "Tipo", 1, 0, 'C', 1)
                pdf.cell(50, 5, "Descricao", 1, 0, 'C', 1)
                pdf.cell(25, 5, "Categoria", 1, 0, 'C', 1)
                pdf.cell(22, 5, "Valor", 1, 1, 'C', 1)
                pdf.set_font("Arial", "", 6)
                linha_atual = pdf.get_y()

            # Alternar cores
            if i % 2 == 0:
                pdf.set_fill_color(230, 230, 230)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.cell(12, 4.5, str(row['id']), 1, 0, 'C', 1)
            pdf.cell(22, 4.5, formatar_data_br_local(row['data_prevista']), 1, 0, 'C', 1)

            if row['tipo'] == 'receita':
                pdf.set_text_color(0, 150, 0)
            else:
                pdf.set_text_color(200, 0, 0)
            pdf.cell(15, 4.5, row['tipo'][:10], 1, 0, 'C', 1)
            pdf.set_text_color(0, 0, 0)

            descricao = row['item'][:40] if len(row['item']) > 40 else row['item']
            pdf.cell(50, 4.5, descricao, 1, 0, 'L', 1)

            categoria = row['categoria'][:20] if len(row['categoria']) > 20 else row['categoria']
            pdf.cell(25, 4.5, categoria, 1, 0, 'L', 1)

            if row['tipo'] == 'receita':
                pdf.set_text_color(0, 150, 0)
            else:
                pdf.set_text_color(200, 0, 0)
            pdf.cell(22, 4.5, formatar_moeda_local(row['valor']), 1, 1, 'R', 1)
            pdf.set_text_color(0, 0, 0)

            linha_atual = pdf.get_y()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name


# ==========================================
# CARREGAR DADOS
# ==========================================

df = carregar_transacoes()

if df.empty:
    st.warning("Nenhum dado cadastrado ainda. Vá para a página de Lançamentos para adicionar.")
    st.stop()

df['data_prevista'] = pd.to_datetime(df['data_prevista'])

# ==========================================
# INICIALIZAR SESSION STATE
# ==========================================

if 'tipo_relatorio' not in st.session_state:
    st.session_state.tipo_relatorio = "anual"
if 'ano_selecionado' not in st.session_state:
    st.session_state.ano_selecionado = 2026
if 'mes_selecionado' not in st.session_state:
    st.session_state.mes_selecionado = datetime.now().month

# ==========================================
# SELEÇÃO DE PERÍODO
# ==========================================

st.subheader("📆 Período de Análise")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📅 Mês a Mês", use_container_width=True):
        st.session_state.tipo_relatorio = "mensal"

with col2:
    if st.button("📊 Ano Completo", use_container_width=True):
        st.session_state.tipo_relatorio = "anual"

with col3:
    if st.button("📆 Personalizado", use_container_width=True):
        st.session_state.tipo_relatorio = "personalizado"

# ==========================================
# FILTROS
# ==========================================

ano_atual = 2026
anos_futuros = list(range(2026, 2037))

if st.session_state.tipo_relatorio == "mensal":
    anos_existentes = sorted(df['data_prevista'].dt.year.unique())
    anos_disponiveis = sorted(set(anos_existentes + anos_futuros))

    col1, col2 = st.columns(2)
    with col1:
        ano_sel = st.selectbox("Ano", anos_disponiveis, index=anos_disponiveis.index(2026) if 2026 in anos_disponiveis else 0)
    with col2:
        mes_sel = st.selectbox("Mês", range(1, 13), format_func=lambda x: ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][x-1])

    if ano_sel in df['data_prevista'].dt.year.unique():
        df_filtrado = df[(df['data_prevista'].dt.year == ano_sel) & (df['data_prevista'].dt.month == mes_sel)]
    else:
        df_filtrado = pd.DataFrame()
        st.info(f"Nenhum dado cadastrado para o ano {ano_sel}")

    ano_selecionado = ano_sel
    mes_inicio = mes_sel
    mes_fim = mes_sel

elif st.session_state.tipo_relatorio == "anual":
    anos_existentes = sorted(df['data_prevista'].dt.year.unique())
    anos_disponiveis = sorted(set(anos_existentes + anos_futuros))

    ano_selecionado = st.selectbox("Selecione o ano", anos_disponiveis, index=anos_disponiveis.index(2026) if 2026 in anos_disponiveis else 0)

    if ano_selecionado in df['data_prevista'].dt.year.unique():
        df_filtrado = df[df['data_prevista'].dt.year == ano_selecionado]
    else:
        df_filtrado = pd.DataFrame()
        st.info(f"Nenhum dado cadastrado para o ano {ano_selecionado}")

    mes_inicio = 1
    mes_fim = 12

else:
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data inicial", df['data_prevista'].min())
    with col2:
        data_fim = st.date_input("Data final", df['data_prevista'].max())
    df_filtrado = df[(df['data_prevista'].dt.date >= data_inicio) & (df['data_prevista'].dt.date <= data_fim)]
    ano_selecionado = data_inicio.year
    mes_inicio = data_inicio.month
    mes_fim = data_fim.month

# ==========================================
# CALCULAR FLUXO
# ==========================================

if not df_filtrado.empty:
    df_fluxo = calcular_fluxo_caixa(df, ano_selecionado, mes_inicio, mes_fim)
else:
    df_fluxo = pd.DataFrame()
    st.warning("Nenhum dado encontrado para o período selecionado.")
    st.stop()

# ==========================================
# MÉTRICAS
# ==========================================

st.subheader("📊 Resumo do Período")

total_receitas = df_filtrado[df_filtrado['tipo'] == 'receita']['valor'].sum()
total_despesas = df_filtrado[df_filtrado['tipo'] == 'despesa']['valor'].sum()
saldo = total_receitas - total_despesas
percentual = (total_despesas / total_receitas * 100) if total_receitas > 0 else 0

col1, col2 = st.columns(2)

with col1:
    st.metric("💰 Total Receitas", formatar_moeda(total_receitas))

with col2:
    st.metric("💸 Total Despesas", formatar_moeda(total_despesas))

col3, col4 = st.columns(2)

with col3:
    st.metric("📊 Saldo", formatar_moeda(saldo), delta_color="normal" if saldo >= 0 else "inverse")

with col4:
    st.metric("📈 Comprometimento", f"{percentual:.1f}%")

# ==========================================
# TABELA DE FLUXO DE CAIXA
# ==========================================

st.subheader("📋 Fluxo de Caixa Mensal")

if not df_fluxo.empty:
    df_exibicao = df_fluxo.copy()
    for col in ['Receitas', 'Despesas', 'Fluxo do Mês', 'Saldo Anterior', 'Saldo Atual']:
        df_exibicao[col] = df_exibicao[col].apply(formatar_moeda)
    st.dataframe(df_exibicao, use_container_width=True, height=400)

    # ==========================================
    # ALERTAS DE ORÇAMENTO
    # ==========================================

    st.subheader("⚠️ Alertas de Orçamento")

    from services.local_service import get_connection
    from datetime import datetime

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria, limite FROM orcamentos")
    orcamentos = cursor.fetchall()
    conn.close()

    if orcamentos:
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year

        alertas_ativos = False

        for categoria, limite in orcamentos:
            gasto = df_filtrado[(df_filtrado['tipo'] == 'despesa') &
                                (df_filtrado['categoria'] == categoria)]['valor'].sum()
            percentual = (gasto / limite * 100) if limite > 0 else 0

            if percentual >= 100:
                st.error(f"🔴 **{categoria}** - Limite estourado! {formatar_moeda(gasto)} / {formatar_moeda(limite)}")
                alertas_ativos = True
            elif percentual >= 70:
                st.warning(f"🟠 **{categoria}** - Atenção! {formatar_moeda(gasto)} / {formatar_moeda(limite)} ({percentual:.0f}%)")
                alertas_ativos = True
            else:
                st.success(f"🟢 **{categoria}** - OK. {formatar_moeda(gasto)} / {formatar_moeda(limite)}")

        if not alertas_ativos:
            st.success("🎉 Todos os orçamentos estão dentro do limite!")
    else:
        st.info("📊 Nenhum orçamento definido. Vá para a página 'Orçamentos' para definir limites por categoria.")

# ==========================================
# GRÁFICOS DE BARRAS
# ==========================================

st.subheader("📈 Evolução Mensal")

if not df_fluxo.empty:
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df_fluxo['Mês'], y=df_fluxo['Receitas'], name='Receitas', marker_color='#2ecc71',
                         text=df_fluxo['Receitas'].apply(formatar_moeda), textposition='outside'))
    fig.add_trace(go.Bar(x=df_fluxo['Mês'], y=df_fluxo['Despesas'], name='Despesas', marker_color='#e74c3c',
                         text=df_fluxo['Despesas'].apply(formatar_moeda), textposition='outside'))
    fig.add_trace(go.Scatter(x=df_fluxo['Mês'], y=df_fluxo['Saldo Atual'], name='Saldo Acumulado',
                             mode='lines+markers', line=dict(color='#3498db', width=3), marker=dict(size=8), yaxis='y2',
                             text=df_fluxo['Saldo Atual'].apply(formatar_moeda), textposition='top center'))

    fig.update_layout(title="Receitas, Despesas e Saldo Acumulado", xaxis_title="Mês", yaxis_title="Valor (R$)",
                      yaxis2=dict(title="Saldo Acumulado (R$)", overlaying='y', side='right'), barmode='group',
                      height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💰 Evolução do Saldo")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_fluxo['Mês'], y=df_fluxo['Saldo Anterior'], name='Saldo Anterior (início do mês)',
                              mode='lines+markers', line=dict(color='#f39c12', width=2, dash='dash'), marker=dict(size=6)))
    fig2.add_trace(go.Scatter(x=df_fluxo['Mês'], y=df_fluxo['Saldo Atual'], name='Saldo Atual (fim do mês)',
                              mode='lines+markers', line=dict(color='#2ecc71', width=3), marker=dict(size=8)))
    fig2.update_layout(title="Evolução do Saldo - Início vs Fim do Mês", xaxis_title="Mês", yaxis_title="Saldo (R$)",
                       height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# GRÁFICOS DE PIZZA
# ==========================================

st.subheader("🥧 Distribuição por Categoria")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Receitas por Categoria")
    receitas_categoria = df_filtrado[df_filtrado['tipo'] == 'receita'].groupby('categoria')['valor'].sum().sort_values(ascending=False)

    if not receitas_categoria.empty:
        labels_receitas = []
        valores_receitas = []
        for cat, val in receitas_categoria.items():
            labels_receitas.append(f"{cat}<br>R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            valores_receitas.append(val)

        fig_pie_receitas = go.Figure(data=[go.Pie(
            labels=labels_receitas,
            values=valores_receitas,
            hole=0.3,
            marker_colors=['#2ecc71', '#27ae60', '#1e8449', '#58d68d', '#7dcea0', '#a9dfbf'],
            textinfo='label+percent',
            texttemplate='%{label}<br>%{percent:.1f}%'
        )])
        fig_pie_receitas.update_layout(title="Receitas por Categoria", height=400, showlegend=False)
        st.plotly_chart(fig_pie_receitas, use_container_width=True)
    else:
        st.info("Nenhuma receita cadastrada neste período")

with col2:
    st.markdown("### 🔴 Despesas por Categoria")
    despesas_categoria = df_filtrado[df_filtrado['tipo'] == 'despesa'].groupby('categoria')['valor'].sum().sort_values(ascending=False)

    if not despesas_categoria.empty:
        labels_despesas = []
        valores_despesas = []
        for cat, val in despesas_categoria.items():
            labels_despesas.append(f"{cat}<br>R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            valores_despesas.append(val)

        fig_pie_despesas = go.Figure(data=[go.Pie(
            labels=labels_despesas,
            values=valores_despesas,
            hole=0.3,
            marker_colors=['#e74c3c', '#c0392b', '#e67e22', '#f39c12', '#d35400', '#e67e22'],
            textinfo='label+percent',
            texttemplate='%{label}<br>%{percent:.1f}%'
        )])
        fig_pie_despesas.update_layout(title="Despesas por Categoria", height=400, showlegend=False)
        st.plotly_chart(fig_pie_despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa cadastrada neste período")

# ==========================================
# GRÁFICO DE PROJEÇÃO MENSAL
# ==========================================

st.subheader("📅 Projeção Mensal - Últimos 6 Meses")

meses_ordenados = sorted(df_filtrado['data_prevista'].dt.to_period('M').unique())[-6:]
if len(meses_ordenados) > 0:
    df_projecao = df_filtrado[df_filtrado['data_prevista'].dt.to_period('M').isin(meses_ordenados)]

    fig_proj = go.Figure()

    for mes in meses_ordenados:
        mes_nome = mes.strftime('%B')
        receita_mes = df_projecao[(df_projecao['tipo'] == 'receita') & (df_projecao['data_prevista'].dt.to_period('M') == mes)]['valor'].sum()
        despesa_mes = df_projecao[(df_projecao['tipo'] == 'despesa') & (df_projecao['data_prevista'].dt.to_period('M') == mes)]['valor'].sum()

        fig_proj.add_trace(go.Bar(name=f'{mes_nome} - Receitas', x=[mes_nome], y=[receita_mes],
                                  marker_color='#2ecc71', text=[formatar_moeda(receita_mes)], textposition='outside'))
        fig_proj.add_trace(go.Bar(name=f'{mes_nome} - Despesas', x=[mes_nome], y=[despesa_mes],
                                  marker_color='#e74c3c', text=[formatar_moeda(despesa_mes)], textposition='outside'))

    fig_proj.update_layout(title="Receitas vs Despesas por Mês (últimos 6 meses)", xaxis_title="Mês",
                           yaxis_title="Valor (R$)", barmode='group', height=450,
                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_proj, use_container_width=True)
else:
    st.info("Adicione mais lançamentos para ver a projeção mensal")

# ==========================================
# ÚLTIMOS LANÇAMENTOS
# ==========================================

st.subheader("📋 Últimos Lançamentos")

df_ultimos = df_filtrado.sort_values('data_prevista', ascending=False).head(10)

if not df_ultimos.empty:
    df_ultimos_exibicao = df_ultimos[['data_prevista', 'tipo', 'item', 'categoria', 'valor']].copy()
    df_ultimos_exibicao['data_prevista'] = df_ultimos_exibicao['data_prevista'].apply(formatar_data_br)
    df_ultimos_exibicao['valor'] = df_ultimos_exibicao['valor'].apply(formatar_moeda)
    df_ultimos_exibicao.columns = ['Data', 'Tipo', 'Descrição', 'Categoria', 'Valor']

    def colorir_linha(row):
        if row['Tipo'] == 'receita':
            return ['color: #2ecc71'] * len(row)
        elif row['Tipo'] == 'despesa':
            return ['color: #e74c3c'] * len(row)
        return [''] * len(row)

    st.dataframe(df_ultimos_exibicao.style.apply(colorir_linha, axis=1), use_container_width=True, height=300)

# ==========================================
# BOTÃO PDF
# ==========================================

st.divider()
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("📑 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
        with st.spinner("Gerando PDF..."):
            if st.session_state.tipo_relatorio == "mensal":
                periodo_texto = f"{mes_sel:02d}/{ano_sel}"
            elif st.session_state.tipo_relatorio == "anual":
                periodo_texto = f"Ano {ano_selecionado}"
            else:
                periodo_texto = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"

            pdf_path = gerar_pdf_relatorio(df_fluxo, df_filtrado, ano_selecionado, periodo_texto)

            if pdf_path is not None and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()

                st.download_button(label="📥 BAIXAR PDF", data=pdf_data,
                                   file_name=f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d')}.pdf",
                                   mime="application/pdf", use_container_width=True)
                try:
                    os_module.unlink(pdf_path)
                except:
                    pass
            else:
                st.error("❌ Erro ao gerar o PDF. Tente novamente.")

# ==========================================
# RODAPÉ
# ==========================================

st.caption("💡 **Legenda:** Saldo Anterior = saldo do mês anterior | Fluxo = Receitas - Despesas | Saldo Atual = Saldo Anterior + Fluxo")
st.caption("📊 **Gráficos de Pizza:** Mostram a distribuição de receitas e despesas por categoria")
st.caption("📅 **Projeção Mensal:** Mostra os valores dos últimos 6 meses")