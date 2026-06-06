import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import carregar_categorias, carregar_transacoes, get_connection, limpar_cache

st.set_page_config(
    page_title="Orçamentos",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Orçamentos por Categoria")


def formatar_moeda(valor):
    try:
        if valor == 0 or valor < 0.01:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


# Carregar dados
df_categorias = carregar_categorias()
df_transacoes = carregar_transacoes()

# Carregar orçamentos existentes
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT categoria, limite FROM orcamentos")
orcamentos = {row[0]: row[1] for row in cursor.fetchall()}
conn.close()

st.subheader("🎯 Definir Limites por Categoria")

# Filtrar apenas categorias de despesa
categorias_despesa = df_categorias[df_categorias['tipo'] == 'despesa']['nome'].sort_values().tolist()

if not categorias_despesa:
    st.warning("Nenhuma categoria de despesa cadastrada.")
else:
    for categoria in categorias_despesa:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.write(f"**{categoria}**")

        with col2:
            limite_atual = orcamentos.get(categoria, 0)
            novo_limite = st.number_input(f"Limite (R$)", min_value=0.0, step=50.0, value=float(limite_atual),
                                          key=f"limite_{categoria}", label_visibility="collapsed")

        with col3:
            if st.button(f"💾 Salvar", key=f"salvar_{categoria}"):
                conn = get_connection()
                cursor = conn.cursor()
                if novo_limite > 0:
                    cursor.execute("INSERT OR REPLACE INTO orcamentos (categoria, limite) VALUES (?, ?)",
                                   (categoria, novo_limite))
                else:
                    cursor.execute("DELETE FROM orcamentos WHERE categoria = ?", (categoria,))
                conn.commit()
                conn.close()
                limpar_cache()
                st.success(f"✅ Limite de {categoria} salvo!")
                st.rerun()

        with col4:
            # Botão REMOVER aparece apenas se a categoria tem orçamento
            if categoria in orcamentos:
                if st.button(f"🗑️ Remover", key=f"remover_{categoria}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM orcamentos WHERE categoria = ?", (categoria,))
                    conn.commit()
                    conn.close()
                    limpar_cache()
                    st.success(f"✅ Orçamento de {categoria} removido!")
                    st.rerun()

        st.divider()

# ==========================================
# RESUMO DOS ORÇAMENTOS (APENAS COM LIMITES)
# ==========================================

st.subheader("📊 Acompanhamento Mensal")

if orcamentos:
    from datetime import datetime

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    df_transacoes['data_prevista'] = pd.to_datetime(df_transacoes['data_prevista'])

    df_mes = df_transacoes[(df_transacoes['tipo'] == 'despesa') &
                           (df_transacoes['data_prevista'].dt.month == mes_atual) &
                           (df_transacoes['data_prevista'].dt.year == ano_atual)]

    for categoria, limite in orcamentos.items():
        gasto = df_mes[df_mes['categoria'] == categoria]['valor'].sum()
        percentual = (gasto / limite * 100) if limite > 0 else 0

        if percentual >= 100:
            status = "🔴 Estourou!"
        elif percentual >= 80:
            status = "🟠 Atenção!"
        else:
            status = "🟢 OK"

        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])

        with col1:
            st.markdown(f"**{categoria}**")
        with col2:
            st.markdown(f"Limite: {formatar_moeda(limite)}")
        with col3:
            st.progress(min(percentual / 100, 1.0))
        with col4:
            st.markdown(f"{status} {formatar_moeda(gasto)} ({percentual:.0f}%)")
else:
    st.info("Nenhum limite definido. Utilize o formulário acima para definir orçamentos por categoria.")