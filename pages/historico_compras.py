import streamlit as st
import sys
import os
import pandas as pd
import base64
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import carregar_transacoes, carregar_categorias

st.set_page_config(
    page_title="Historico de Compras",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Historico de Compras")


def formatar_moeda(valor):
    try:
        if valor == 0 or valor < 0.01:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def verificar_tipo_comprovante(comprovante_base64):
    """Verifica se o comprovante é imagem ou PDF"""
    if not comprovante_base64:
        return None

    # Verificar os primeiros bytes
    primeiros_bytes = comprovante_base64[:20].lower()

    # PDF começa com JVBERi0xLjM (base64 do %PDF)
    if 'jvberi0xlj' in primeiros_bytes or 'jvber' in primeiros_bytes:
        return 'pdf'

    # PNG começa com iVBORw0KGgo
    if 'ivborw0kggo' in primeiros_bytes:
        return 'png'

    # JPEG começa com /9j/
    if '/9j/' in primeiros_bytes:
        return 'jpeg'

    return 'desconhecido'


df_categorias = carregar_categorias()
df_transacoes = carregar_transacoes()

if df_transacoes.empty:
    st.info("Nenhuma transacao cadastrada.")
    st.stop()

df_transacoes['data_prevista'] = pd.to_datetime(df_transacoes['data_prevista'])

categorias_despesa = df_categorias[df_categorias['tipo'] == 'despesa']['nome'].sort_values().tolist()
categoria_selecionada = st.selectbox("Selecione a categoria:", ["Todas"] + categorias_despesa)

if categoria_selecionada == "Todas":
    df_filtrado = df_transacoes[df_transacoes['tipo'] == 'despesa']
else:
    df_filtrado = df_transacoes[
        (df_transacoes['tipo'] == 'despesa') & (df_transacoes['categoria'] == categoria_selecionada)]

df_filtrado = df_filtrado.sort_values('data_prevista', ascending=False)

if df_filtrado.empty:
    st.info("Nenhum lancamento encontrado.")
else:
    total = df_filtrado['valor'].sum()

    for _, row in df_filtrado.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])

        with col1:
            st.markdown(f"**{row['item']}**")
            st.caption(f"📅 {row['data_prevista'].strftime('%d/%m/%Y')}")

        with col2:
            st.markdown(f"**{formatar_moeda(row['valor'])}**")

        with col3:
            obs = row.get('observacao')
            if obs and obs.strip():
                st.caption(f"📝 {obs[:50]}")
            else:
                st.caption("📝 Sem observacao")

        with col4:
            comprovante = row.get('comprovante')
            if comprovante and len(str(comprovante)) > 10:
                if st.button("📎 Ver", key=f"btn_{row['id']}"):
                    st.session_state[f"show_{row['id']}"] = True
            else:
                st.caption("Sem comprovante")

        if st.session_state.get(f"show_{row['id']}", False):
            with st.expander("Comprovante", expanded=True):
                try:
                    dados = base64.b64decode(row['comprovante'])
                    tipo = verificar_tipo_comprovante(row['comprovante'][:50].lower())

                    if tipo == 'pdf':
                        # Para PDF, oferecer download
                        st.download_button(
                            label="📥 Baixar PDF",
                            data=dados,
                            file_name=f"comprovante_{row['id']}.pdf",
                            mime="application/pdf"
                        )
                        st.info("PDF anexado. Clique no botão acima para baixar.")
                    else:
                        # Para imagens, exibir
                        st.image(dados, caption="Comprovante", use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao exibir: {e}")

                if st.button("Fechar", key=f"close_{row['id']}"):
                    st.session_state[f"show_{row['id']}"] = False
                    st.rerun()

        st.divider()

    st.markdown(f"### Total: {formatar_moeda(total)}")