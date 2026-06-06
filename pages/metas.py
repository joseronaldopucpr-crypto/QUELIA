import streamlit as st
import sys
import os
import pandas as pd
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import (
    carregar_transacoes,
    carregar_metas,
    adicionar_meta,
    excluir_meta,
    atualizar_progresso_meta,
    carregar_categorias
)

st.set_page_config(
    page_title="Metas Financeiras",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Metas Financeiras")


def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def calcular_progresso(valor_atual, valor_meta):
    if valor_meta <= 0:
        return 0
    progresso = (valor_atual / valor_meta) * 100
    return min(progresso, 100)


# ==========================================
# FORMULÁRIO PARA ADICIONAR META
# ==========================================

with st.expander("➕ Adicionar Nova Meta", expanded=False):
    with st.form("form_meta"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome da Meta", placeholder="Ex: Viagem, Carro, Reserva...")
            valor_meta = st.number_input("Valor da Meta (R$)", min_value=0.01, step=100.0, format="%.2f")

        with col2:
            data_inicio = st.date_input("Data Início", value=date.today())
            data_fim = st.date_input("Data Final", value=date.today() + timedelta(days=365))

        # Carregar categorias para filtro
        df_cat = carregar_categorias()
        categorias_lista = ["Todas"] + df_cat["nome"].tolist() if not df_cat.empty else ["Todas"]
        categoria = st.selectbox("Categoria (opcional)", categorias_lista)

        submitted = st.form_submit_button("💾 Salvar Meta", use_container_width=True)

        if submitted and nome.strip() and valor_meta > 0:
            cat_selecionada = categoria if categoria != "Todas" else None
            if adicionar_meta(nome, valor_meta, data_inicio, data_fim, cat_selecionada):
                st.success(f"✅ Meta '{nome}' criada com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao criar meta")

# ==========================================
# LISTAR METAS EXISTENTES
# ==========================================

st.subheader("📋 Suas Metas")

df_metas = carregar_metas()

if df_metas.empty:
    st.info("Nenhuma meta cadastrada ainda. Clique em 'Adicionar Nova Meta' para começar.")
else:
    for _, meta in df_metas.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"**🎯 {meta['nome']}**")
                st.caption(f"📅 {meta['data_inicio'][:10]} até {meta['data_fim'][:10]}")
                if meta['categoria']:
                    st.caption(f"📂 Categoria: {meta['categoria']}")

            with col2:
                progresso = calcular_progresso(meta['valor_atual'], meta['valor_meta'])
                st.metric("Progresso", f"{progresso:.1f}%")
                st.progress(progresso / 100)
                st.caption(f"💰 {formatar_moeda(meta['valor_atual'])} / {formatar_moeda(meta['valor_meta'])}")

            with col3:
                # Botão para adicionar progresso
                if st.button(f"➕ Adicionar", key=f"add_{meta['id']}"):
                    st.session_state[f"add_progresso_{meta['id']}"] = True

                # Botão para excluir
                if st.button(f"🗑️ Excluir", key=f"del_{meta['id']}"):
                    if excluir_meta(meta['id']):
                        st.rerun()

            # Modal para adicionar progresso
            if st.session_state.get(f"add_progresso_{meta['id']}", False):
                with st.expander(f"Adicionar à meta '{meta['nome']}'", expanded=True):
                    valor_adicao = st.number_input("Valor (R$)", min_value=0.01, step=50.0, key=f"valor_{meta['id']}")
                    if st.button("Confirmar", key=f"conf_{meta['id']}"):
                        novo_valor = meta['valor_atual'] + valor_adicao
                        atualizar_progresso_meta(meta['id'], novo_valor)
                        st.session_state[f"add_progresso_{meta['id']}"] = False
                        st.rerun()
                    if st.button("Cancelar", key=f"can_{meta['id']}"):
                        st.session_state[f"add_progresso_{meta['id']}"] = False
                        st.rerun()

            st.divider()

# ==========================================
# RESUMO DAS METAS
# ==========================================

st.subheader("📊 Resumo Financeiro")

if not df_metas.empty:
    total_meta = df_metas['valor_meta'].sum()
    total_atual = df_metas['valor_atual'].sum()
    progresso_geral = calcular_progresso(total_atual, total_meta)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💰 Total das Metas", formatar_moeda(total_meta))

    with col2:
        st.metric("💵 Total Economizado", formatar_moeda(total_atual))

    with col3:
        st.metric("📈 Progresso Geral", f"{progresso_geral:.1f}%")

    st.progress(progresso_geral / 100)