import streamlit as st
import pandas as pd

from services.supabase_service import (
    carregar_transacoes
)

from services.financeiro_service import (
    moeda
)

st.title("📈 Relatórios")

# ==========================================
# CARREGAR DADOS
# ==========================================

df = carregar_transacoes()

if df.empty:

    st.warning(
        "Nenhum lançamento encontrado."
    )

    st.stop()

# ==========================================
# TRATAMENTO
# ==========================================

df["valor"] = (
    pd.to_numeric(
        df["valor"],
        errors="coerce"
    )
    .fillna(0)
)

# ==========================================
# FILTROS
# ==========================================

st.subheader("Filtros")

col1, col2 = st.columns(2)

with col1:

    meses = (
        ["Todos"]
        + sorted(
            df["mes"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    filtro_mes = st.selectbox(
        "Mês",
        meses
    )

with col2:

    categorias = (
        ["Todas"]
        + sorted(
            df["categoria"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    filtro_categoria = st.selectbox(
        "Categoria",
        categorias
    )

# ==========================================
# APLICAR FILTROS
# ==========================================

df_filtrado = df.copy()

if filtro_mes != "Todos":

    df_filtrado = (
        df_filtrado[
            df_filtrado["mes"]
            == filtro_mes
        ]
    )

if filtro_categoria != "Todas":

    df_filtrado = (
        df_filtrado[
            df_filtrado["categoria"]
            == filtro_categoria
        ]
    )

# ==========================================
# INDICADORES
# ==========================================

receitas = (
    df_filtrado[
        df_filtrado["tipo"]
        == "receita"
    ]["valor"]
    .sum()
)

despesas = (
    df_filtrado[
        df_filtrado["tipo"]
        == "despesa"
    ]["valor"]
    .sum()
)

saldo = receitas - despesas

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Receitas",
        moeda(receitas)
    )

with col2:

    st.metric(
        "Despesas",
        moeda(despesas)
    )

with col3:

    st.metric(
        "Saldo",
        moeda(saldo)
    )

# ==========================================
# GRÁFICO
# ==========================================

st.subheader("Receitas x Despesas")

grafico = pd.DataFrame(
    {
        "Valor": [
            receitas,
            despesas
        ]
    },
    index=[
        "Receitas",
        "Despesas"
    ]
)

st.bar_chart(grafico)

# ==========================================
# TABELA
# ==========================================

st.subheader("Lançamentos")

df_exibir = df_filtrado.copy()

if "valor" in df_exibir.columns:

    df_exibir["valor"] = (
        df_exibir["valor"]
        .astype(float)
        .apply(moeda)
    )

st.dataframe(
    df_exibir,
    use_container_width=True
)

# ==========================================
# RESUMO POR CATEGORIA
# ==========================================

st.subheader(
    "Resumo por Categoria"
)

resumo = (
    df_filtrado
    .groupby(
        "categoria",
        dropna=False
    )["valor"]
    .sum()
    .reset_index()
)

resumo["valor"] = (
    resumo["valor"]
    .astype(float)
    .apply(moeda)
)

st.dataframe(
    resumo,
    use_container_width=True
)