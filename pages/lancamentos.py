import streamlit as st
from datetime import date

from services.supabase_service import (
    carregar_transacoes,
    carregar_categorias,
    adicionar_transacao,
    excluir_transacao,
    limpar_cache
)

from services.financeiro_service import (
    gerar_grupo_recorrencia,
    gerar_datas_recorrentes,
    obter_nome_mes
)

# ==========================================
# TÍTULO
# ==========================================

st.title("💰 Lançamentos")

# ==========================================
# CATEGORIAS
# ==========================================

df_categorias = carregar_categorias()

if df_categorias.empty:
    st.warning("Nenhuma categoria cadastrada.")
    st.stop()

# ==========================================
# FORMULÁRIO
# ==========================================

with st.form("form_lancamento"):

    tipo = st.selectbox(
        "Tipo",
        ["receita", "despesa"]
    )

    categorias_filtradas = (
        df_categorias[
            df_categorias["tipo"] == tipo
        ]["nome"]
        .sort_values()
        .tolist()
    )

    categoria = st.selectbox(
        "Categoria",
        categorias_filtradas
    )

    item = st.text_input(
        "Descrição"
    )

    valor = st.number_input(
        "Valor (R$)",
        min_value=0.0,
        step=0.01,
        format="%.2f"
    )

    data_prevista = st.date_input(
        "Data Prevista",
        value=date.today()
    )

    if tipo == "receita":

        status = st.selectbox(
            "Status",
            ["Pendente", "Recebido"]
        )

    else:

        status = st.selectbox(
            "Status",
            ["Pendente", "Pago"]
        )

    observacao = st.text_area(
        "Observação"
    )

    st.divider()

    modo = st.radio(
        "Tipo de lançamento",
        [
            "Único",
            "Recorrente Mensal",
            "Parcelado"
        ]
    )

    quantidade = 1

    if modo == "Recorrente Mensal":

        quantidade = st.number_input(
            "Quantidade de meses",
            min_value=1,
            max_value=120,
            value=12
        )

    elif modo == "Parcelado":

        quantidade = st.number_input(
            "Quantidade de parcelas",
            min_value=2,
            max_value=120,
            value=12
        )

    salvar = st.form_submit_button(
        "Salvar"
    )

# ==========================================
# PROCESSAMENTO
# ==========================================

if salvar:

    if not item.strip():

        st.error(
            "Informe uma descrição."
        )

    elif valor <= 0:

        st.error(
            "Informe um valor maior que zero."
        )

    else:

        grupo_recorrencia = None

        if modo != "Único":

            grupo_recorrencia = (
                gerar_grupo_recorrencia()
            )

        datas = gerar_datas_recorrentes(
            data_prevista,
            quantidade
        )

        sucesso = 0

        for indice, data_ref in enumerate(
                datas,
                start=1
        ):

            descricao = item.upper()

            if modo == "Parcelado":

                descricao = (
                    f"{item.upper()} "
                    f"({indice}/{quantidade})"
                )

            payload = {

                "mes": obter_nome_mes(
                    data_ref
                ),

                "tipo": tipo,

                "item": descricao,

                "valor": float(valor),

                "categoria": categoria,

                "status": status,

                "observacao": observacao,

                "data_prevista": str(
                    data_ref
                ),

                "recorrente":
                    modo == "Recorrente Mensal",

                "parcelado":
                    modo == "Parcelado",

                "numero_parcela":
                    indice
                    if modo == "Parcelado"
                    else None,

                "total_parcelas":
                    quantidade
                    if modo == "Parcelado"
                    else None,

                "tipo_recorrencia":
                    "mensal"
                    if modo == "Recorrente Mensal"
                    else None,

                "meses_recorrencia":
                    quantidade
                    if modo == "Recorrente Mensal"
                    else None,

                "grupo_recorrencia":
                    grupo_recorrencia
            }

            if adicionar_transacao(
                    payload
            ):
                sucesso += 1

        limpar_cache()

        if sucesso > 0:

            if modo == "Único":

                st.success(
                    "Lançamento criado com sucesso."
                )

            elif modo == "Recorrente Mensal":

                st.success(
                    f"{sucesso} lançamentos recorrentes criados com sucesso."
                )

            else:

                st.success(
                    f"{sucesso} parcelas criadas com sucesso."
                )

            st.rerun()

        else:

            st.error(
                "Erro ao salvar lançamento."
            )

# ==========================================
# EXCLUIR LANÇAMENTO
# ==========================================

st.divider()

st.subheader(
    "🗑️ Excluir Lançamento"
)

df = carregar_transacoes()

if df.empty:

    st.info(
        "Nenhum lançamento cadastrado."
    )

else:

    opcoes = {
        f"{row['id']} - {row['item']}":
        row["id"]
        for _, row in df.iterrows()
    }

    selecionado = st.selectbox(
        "Selecione o lançamento",
        list(opcoes.keys())
    )

    if st.button(
        "Excluir Lançamento"
    ):

        id_excluir = opcoes[
            selecionado
        ]

        if excluir_transacao(
                id_excluir
        ):

            limpar_cache()

            st.success(
                "Lançamento excluído com sucesso."
            )

            st.rerun()

        else:

            st.error(
                "Erro ao excluir lançamento."
            )

