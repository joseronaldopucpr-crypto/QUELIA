import streamlit as st

from services.supabase_service import (
    carregar_configuracoes,
    salvar_configuracoes,
    limpar_cache
)

st.title("⚙️ Configurações")

config = carregar_configuracoes()

reserva_meta = float(
    config.get(
        "reserva_meta",
        10000
    )
)

saldo_inicial = float(
    config.get(
        "saldo_inicial",
        0
    )
)

with st.form("configuracoes"):

    nova_meta = st.number_input(
        "Meta da Reserva",
        min_value=0.0,
        value=reserva_meta,
        step=100.0
    )

    novo_saldo = st.number_input(
        "Saldo Inicial",
        value=saldo_inicial,
        step=100.0
    )

    salvar = st.form_submit_button(
        "Salvar"
    )

if salvar:

    sucesso = salvar_configuracoes(
        nova_meta,
        novo_saldo
    )

    if sucesso:

        limpar_cache()

        st.success(
            "Configurações salvas."
        )

        st.rerun()

    else:

        st.error(
            "Erro ao salvar configurações."
        )