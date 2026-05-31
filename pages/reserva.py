import streamlit as st
import pandas as pd

from services.supabase_service import (
    carregar_movimentacoes_reserva,
    registrar_movimentacao_reserva,
    limpar_cache
)

st.title("🛟 Reserva de Emergência")

df = carregar_movimentacoes_reserva()

# ==========================================
# SALDO
# ==========================================

saldo = 0

if not df.empty:

    entradas = (
        df[df["tipo"] == "Entrada"]["valor"]
        .astype(float)
        .sum()
    )

    saidas = (
        df[df["tipo"] == "Saída"]["valor"]
        .astype(float)
        .sum()
    )

    saldo = entradas - saidas

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Saldo Atual",
        f"R$ {saldo:,.2f}"
    )

with col2:
    st.metric(
        "Entradas",
        f"R$ {entradas if not df.empty else 0:,.2f}"
    )

with col3:
    st.metric(
        "Saídas",
        f"R$ {saidas if not df.empty else 0:,.2f}"
    )

st.divider()

# ==========================================
# NOVA MOVIMENTAÇÃO
# ==========================================

with st.form("movimentacao_reserva"):

    tipo = st.selectbox(
        "Tipo",
        [
            "Entrada",
            "Saída"
        ]
    )

    valor = st.number_input(
        "Valor",
        min_value=0.01,
        step=0.01
    )

    motivo = st.text_input(
        "Motivo"
    )

    salvar = st.form_submit_button(
        "Registrar"
    )

if salvar:

    if not motivo.strip():

        st.error(
            "Informe um motivo."
        )

    else:

        sucesso = registrar_movimentacao_reserva(
            tipo,
            valor,
            motivo
        )

        if sucesso:

            limpar_cache()

            st.success(
                "Movimentação registrada."
            )

            st.rerun()

        else:

            st.error(
                "Erro ao registrar movimentação."
            )

st.divider()

# ==========================================
# HISTÓRICO
# ==========================================

st.subheader("Histórico")

if df.empty:

    st.info(
        "Nenhuma movimentação registrada."
    )

else:

    df_exibir = df.copy()

    df_exibir["valor"] = (
        df_exibir["valor"]
        .astype(float)
        .map(lambda x: f"R$ {x:,.2f}")
    )

    st.dataframe(
        df_exibir,
        use_container_width=True
    )