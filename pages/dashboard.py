import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from services.supabase_service import (
    carregar_transacoes,
    carregar_movimentacoes_reserva
)

from services.financeiro_service import (
    moeda
)

st.title("📊 Dashboard Financeiro")

# ==========================================
# TRANSAÇÕES
# ==========================================

df = carregar_transacoes()

receitas = 0
despesas = 0
saldo = 0

if not df.empty:

    df["valor"] = (
        pd.to_numeric(
            df["valor"],
            errors="coerce"
        )
        .fillna(0)
    )

    receitas = (
        df[
            df["tipo"] == "receita"
        ]["valor"]
        .sum()
    )

    despesas = (
        df[
            df["tipo"] == "despesa"
        ]["valor"]
        .sum()
    )

    saldo = receitas - despesas

# ==========================================
# RESERVA
# ==========================================

df_reserva = carregar_movimentacoes_reserva()

saldo_reserva = 0

if not df_reserva.empty:

    entradas = (
        df_reserva[
            df_reserva["tipo"] == "Entrada"
        ]["valor"]
        .astype(float)
        .sum()
    )

    saidas = (
        df_reserva[
            df_reserva["tipo"] == "Saída"
        ]["valor"]
        .astype(float)
        .sum()
    )

    saldo_reserva = entradas - saidas

# ==========================================
# RESUMO FINANCEIRO
# ==========================================

st.subheader("Resumo Financeiro")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <h4>💵 Receitas</h4>
        <h2 style='color:#16a34a;'>{moeda(receitas)}</h2>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <h4>💸 Despesas</h4>
        <h2 style='color:#dc2626;'>{moeda(despesas)}</h2>
        """,
        unsafe_allow_html=True
    )

col3, col4 = st.columns(2)

with col3:
    cor_saldo = "#16a34a" if saldo >= 0 else "#dc2626"

    st.markdown(
        f"""
        <h4>💰 Saldo</h4>
        <h2 style='color:{cor_saldo};'>{moeda(saldo)}</h2>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <h4>🛟 Reserva</h4>
        <h2 style='color:#2563eb;'>{moeda(saldo_reserva)}</h2>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# GRÁFICO DE PIZZA
# ==========================================

st.subheader(
    "Distribuição Financeira"
)

if receitas > 0 or despesas > 0:

    fig, ax = plt.subplots(
        figsize=(6, 6)
    )

    ax.pie(
        [receitas, despesas],
        labels=[
            "Receitas",
            "Despesas"
        ],
        autopct="%1.1f%%"
    )

    ax.axis("equal")

    st.pyplot(fig)

else:

    st.info(
        "Sem dados para exibir."
    )

st.divider()

# ==========================================
# ÚLTIMOS LANÇAMENTOS
# ==========================================

st.subheader(
    "Últimos Lançamentos"
)

if df.empty:

    st.info(
        "Nenhum lançamento encontrado."
    )

else:

    exibir = (
        df.sort_values(
            "data_prevista",
            ascending=False
        )
        .head(10)
        .copy()
    )

    exibir["valor"] = (
        exibir["valor"]
        .astype(float)
        .apply(moeda)
    )


    def colorir_linha(row):

        if row["tipo"] == "receita":
            return [
                "color: #16a34a; font-weight: bold;"
            ] * len(row)

        return [
            "color: #dc2626; font-weight: bold;"
        ] * len(row)


    st.dataframe(
        exibir.style.apply(
            colorir_linha,
            axis=1
        ),
        use_container_width=True
    )