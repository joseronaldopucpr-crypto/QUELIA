import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import (
    carregar_categorias,
    adicionar_categoria,
    excluir_categoria,
    atualizar_categoria,
    limpar_cache,
    get_connection,
    carregar_transacoes
)

st.set_page_config(
    page_title="Categorias",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Gerenciar Categorias")

# ==========================================
# CARREGAR CATEGORIAS
# ==========================================

df_categorias = carregar_categorias()

# ==========================================
# FORMULÁRIO PARA ADICIONAR
# ==========================================

with st.expander("➕ Adicionar Nova Categoria", expanded=False):
    with st.form("form_categoria"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome da categoria", placeholder="Ex: Alimentação, Transporte...")

        with col2:
            tipo = st.selectbox("Tipo", ["receita", "despesa"])

        submitted = st.form_submit_button("💾 Salvar Categoria", use_container_width=True)

        if submitted and nome.strip():
            if adicionar_categoria(nome.strip().capitalize(), tipo):
                limpar_cache()
                st.success(f"✅ Categoria '{nome}' adicionada com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao adicionar categoria")

# ==========================================
# LISTAR E EDITAR CATEGORIAS
# ==========================================

st.subheader("📋 Categorias Existentes")

if df_categorias.empty:
    st.info("Nenhuma categoria cadastrada ainda.")
else:
    receitas_df = df_categorias[df_categorias['tipo'] == 'receita']
    despesas_df = df_categorias[df_categorias['tipo'] == 'despesa']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 Receitas")
        for _, row in receitas_df.iterrows():
            with st.container():
                col_a, col_b, col_c = st.columns([3, 1, 1])
                col_a.write(f"📌 {row['nome']}")

                if col_b.button("✏️", key=f"edit_{row['id']}"):
                    st.session_state[f"editando_{row['id']}"] = True

                if col_c.button("🗑️", key=f"del_{row['id']}"):
                    if excluir_categoria(row['id']):
                        limpar_cache()
                        st.rerun()

                if st.session_state.get(f"editando_{row['id']}", False):
                    novo_nome = st.text_input("Novo nome", value=row['nome'], key=f"input_{row['id']}")
                    novo_tipo = st.selectbox("Tipo", ["receita", "despesa"], index=0 if row['tipo'] == 'receita' else 1, key=f"tipo_{row['id']}")
                    if st.button("Salvar", key=f"save_{row['id']}"):
                        if atualizar_categoria(row['id'], novo_nome, novo_tipo):
                            limpar_cache()
                            st.session_state[f"editando_{row['id']}"] = False
                            st.rerun()

                st.divider()

    with col2:
        st.markdown("### 🔴 Despesas")
        for _, row in despesas_df.iterrows():
            with st.container():
                col_a, col_b, col_c = st.columns([3, 1, 1])
                col_a.write(f"📌 {row['nome']}")

                if col_b.button("✏️", key=f"edit_{row['id']}_desp"):
                    st.session_state[f"editando_{row['id']}"] = True

                if col_c.button("🗑️", key=f"del_{row['id']}_desp"):
                    if excluir_categoria(row['id']):
                        limpar_cache()
                        st.rerun()

                if st.session_state.get(f"editando_{row['id']}", False):
                    novo_nome = st.text_input("Novo nome", value=row['nome'], key=f"input_{row['id']}_desp")
                    novo_tipo = st.selectbox("Tipo", ["receita", "despesa"], index=0 if row['tipo'] == 'receita' else 1, key=f"tipo_{row['id']}_desp")
                    if st.button("Salvar", key=f"save_{row['id']}_desp"):
                        if atualizar_categoria(row['id'], novo_nome, novo_tipo):
                            limpar_cache()
                            st.session_state[f"editando_{row['id']}"] = False
                            st.rerun()

                st.divider()

# ==========================================
# LIMPAR CATEGORIAS ÓRFÃS (NÃO UTILIZADAS)
# ==========================================

st.divider()
st.subheader("🧹 Limpeza de Categorias")

with st.expander("🗑️ Remover Categorias Não Utilizadas", expanded=False):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.nome, c.tipo
        FROM categorias c
        LEFT JOIN transacoes t ON c.nome = t.categoria
        WHERE t.categoria IS NULL
    """)
    categorias_nao_usadas = cursor.fetchall()
    conn.close()

    if not categorias_nao_usadas:
        st.success("✅ Todas as categorias estão sendo utilizadas! Nada para limpar.")
    else:
        st.warning(f"⚠️ Encontradas {len(categorias_nao_usadas)} categorias não utilizadas:")

        for cat in categorias_nao_usadas:
            st.write(f"   • **{cat[1]}** ({cat[2]})")

        st.caption("Estas categorias não aparecem em nenhum lançamento e podem ser removidas com segurança.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ REMOVER NÃO UTILIZADAS", type="primary", use_container_width=True):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM categorias
                    WHERE id IN (
                        SELECT c.id FROM categorias c
                        LEFT JOIN transacoes t ON c.nome = t.categoria
                        WHERE t.categoria IS NULL
                    )
                """)
                removidas = cursor.rowcount
                conn.commit()
                conn.close()

                limpar_cache()
                st.success(f"✅ {removidas} categorias removidas com sucesso!")
                st.rerun()

        with col2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.rerun()

# ==========================================
# EXCLUIR CATEGORIA ESPECÍFICA COM TRANSAÇÕES
# ==========================================

st.divider()
st.subheader("🗑️ Excluir Categoria Específica")

with st.expander("⚠️ Remover Categoria e Todos os Lançamentos Vinculados", expanded=False):
    st.warning("⚠️ CUIDADO: Esta ação irá remover a categoria E TODOS os lançamentos associados a ela!")

    df_cat = carregar_categorias()
    df_trans = carregar_transacoes()

    if df_cat.empty:
        st.info("Nenhuma categoria cadastrada.")
    else:
        categorias_com_transacoes = []
        for _, row in df_cat.iterrows():
            quantidade = len(df_trans[df_trans['categoria'] == row['nome']])
            categorias_com_transacoes.append(f"{row['nome']} ({quantidade} lançamento(s))")

        categoria_selecionada = st.selectbox("Selecione a categoria para excluir:", categorias_com_transacoes)

        nome_categoria = categoria_selecionada.split(" (")[0]
        quantidade_transacoes = len(df_trans[df_trans['categoria'] == nome_categoria])

        if quantidade_transacoes > 0:
            st.error(f"⚠️ Esta categoria possui {quantidade_transacoes} lançamento(s) que também serão removidos!")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ EXCLUIR CATEGORIA E LANÇAMENTOS", type="primary", use_container_width=True):
                st.session_state.confirm_exclusao_categoria = True

        with col2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.session_state.confirm_exclusao_categoria = False

        if st.session_state.get('confirm_exclusao_categoria', False):
            st.error("🔴 ÚLTIMA CONFIRMAÇÃO!")
            st.warning(f"Tem certeza que deseja excluir a categoria **'{nome_categoria}'** e seus **{quantidade_transacoes} lançamento(s)**?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ SIM, EXCLUIR TUDO", use_container_width=True):
                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("DELETE FROM transacoes WHERE categoria = ?", (nome_categoria,))
                    transacoes_removidas = cursor.rowcount

                    cursor.execute("DELETE FROM categorias WHERE nome = ?", (nome_categoria,))

                    conn.commit()
                    conn.close()

                    limpar_cache()
                    st.success(f"✅ Categoria '{nome_categoria}' e {transacoes_removidas} lançamento(s) removidos com sucesso!")
                    st.session_state.confirm_exclusao_categoria = False
                    st.rerun()

            with col2:
                if st.button("❌ NÃO, CANCELAR", use_container_width=True):
                    st.session_state.confirm_exclusao_categoria = False
                    st.rerun()

# ==========================================
# ESTATÍSTICAS
# ==========================================

st.divider()
st.subheader("📊 Estatísticas")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Categorias", len(df_categorias))

with col2:
    st.metric("Receitas", len(df_categorias[df_categorias['tipo'] == 'receita']))

with col3:
    st.metric("Despesas", len(df_categorias[df_categorias['tipo'] == 'despesa']))