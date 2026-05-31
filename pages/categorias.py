import streamlit as st
import pandas as pd

from services.supabase_service import (
    carregar_categorias,
    adicionar_categoria,
    desativar_categoria,
    reativar_categoria,
    limpar_cache
)

st.title("🏷️ Categorias")

st.divider()

# ==========================================
# NOVA CATEGORIA
# ==========================================

st.subheader("Nova Categoria")

with st.form("form_categoria"):

    nome = st.text_input(
        "Nome da categoria"
    )

    tipo = st.selectbox(
        "Tipo",
        ["receita", "despesa"]
    )

    salvar = st.form_submit_button(
        "Cadastrar"
    )

if salvar:

    if not nome.strip():

        st.error(
            "Informe o nome da categoria."
        )

    else:

        sucesso = adicionar_categoria(
            nome,
            tipo
        )

        if sucesso:

            limpar_cache()

            st.success(
                "Categoria cadastrada com sucesso."
            )

            st.rerun()

        else:

            st.error(
                "Erro ao cadastrar categoria."
            )

st.divider()

# ==========================================
# LISTAGEM
# ==========================================

st.subheader("Categorias")

df = carregar_categorias()

if df.empty:

    st.info(
        "Nenhuma categoria cadastrada."
    )

else:

    colunas = [
        "id",
        "nome",
        "tipo"
    ]

    st.dataframe(
        df[colunas],
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "Desativar Categoria"
    )

    categoria_id = st.selectbox(
        "Selecione",
        df["id"].tolist()
    )

    if st.button(
        "Desativar"
    ):

        if desativar_categoria(
            categoria_id
        ):

            limpar_cache()

            st.success(
                "Categoria desativada."
            )

            st.rerun()

        else:

            st.error(
                "Erro ao desativar."
            )