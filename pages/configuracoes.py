import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import carregar_transacoes, excluir_transacao, limpar_cache

st.set_page_config(
    page_title="Configurações",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Configurações do Sistema")

# ==========================================
# SEÇÃO DE BANCO DE DADOS
# ==========================================

st.subheader("🗄️ Banco de Dados")

# Carregar estatísticas
df = carregar_transacoes()
total_registros = len(df)

col1, col2 = st.columns(2)

with col1:
    st.metric("📊 Total de Lançamentos", total_registros)

with col2:
    if total_registros > 0:
        receitas = df[df['tipo'] == 'receita']['valor'].sum()
        despesas = df[df['tipo'] == 'despesa']['valor'].sum()
        st.metric("💰 Saldo Total",
                  f"R$ {receitas - despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.metric("💰 Saldo Total", "R$ 0,00")

st.divider()

# ==========================================
# BOTÃO ZERAR BANCO
# ==========================================

st.subheader("⚠️ Área de Risco")

st.warning("⚠️ CUIDADO: Esta ação é irreversível!")

with st.expander("🔴 ZERAR BANCO DE DADOS", expanded=False):
    st.error("Isso irá remover TODOS os lançamentos permanentemente!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ SIM, ZERAR BANCO", type="primary", use_container_width=True):
            st.session_state.confirm_zerar = True

    with col2:
        if st.button("❌ CANCELAR", use_container_width=True):
            st.session_state.confirm_zerar = False

    if st.session_state.get('confirm_zerar', False):
        st.warning("🔴 ÚLTIMA CONFIRMAÇÃO! Tem certeza?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SIM, TENHO CERTEZA", use_container_width=True):
                df = carregar_transacoes()
                ids = df['id'].tolist()
                for id_excluir in ids:
                    excluir_transacao(id_excluir)
                limpar_cache()
                st.success(f"✅ Banco zerado! {len(ids)} registros removidos.")
                st.session_state.confirm_zerar = False
                st.rerun()
        with col2:
            if st.button("❌ NÃO, CANCELAR", use_container_width=True):
                st.session_state.confirm_zerar = False
                st.rerun()

st.divider()

# ==========================================
# INFORMAÇÕES DO SISTEMA
# ==========================================

st.subheader("ℹ️ Informações do Sistema")

col1, col2 = st.columns(2)

with col1:
    st.write("**Banco de Dados:** SQLite Local")
    st.write("**Arquivo:** database_local.db")

with col2:
    st.write("**Status:** 🟢 Funcionando")
    st.write(f"**Registros:** {total_registros}")

st.caption("💡 O banco de dados está armazenado localmente no arquivo 'database_local.db'")