import streamlit as st
import pandas as pd
from datetime import date
from services.local_service import carregar_transacoes, adicionar_transacao, limpar_cache
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


st.set_page_config(
    page_title="Reserva de Emergência",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Reserva de Emergência")

# ==========================================
# INICIALIZAR SESSION STATE
# ==========================================

if 'reserva' not in st.session_state:
    st.session_state.reserva = 0.0


def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


# ==========================================
# CALCULAR RESERVA RECOMENDADA
# ==========================================

df = carregar_transacoes()

if not df.empty:
    # Calcular média de despesas dos últimos 6 meses
    df['data_prevista'] = pd.to_datetime(df['data_prevista'])
    df_despesas = df[df['tipo'] == 'despesa']

    if not df_despesas.empty:
        ultimos_6_meses = df_despesas[df_despesas['data_prevista'] >= (date.today() - pd.DateOffset(months=6))]
        media_mensal = ultimos_6_meses['valor'].mean() if not ultimos_6_meses.empty else df_despesas['valor'].mean()

        # Reserva recomendada: 3 a 6 meses de despesas
        reserva_minima = media_mensal * 3
        reserva_ideal = media_mensal * 6
    else:
        media_mensal = 0
        reserva_minima = 0
        reserva_ideal = 0
else:
    media_mensal = 0
    reserva_minima = 0
    reserva_ideal = 0

# ==========================================
# MÉTRICAS
# ==========================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 Reserva Atual", formatar_moeda(st.session_state.reserva))

with col2:
    st.metric("🎯 Reserva Mínima (3 meses)", formatar_moeda(reserva_minima))

with col3:
    st.metric("🌟 Reserva Ideal (6 meses)", formatar_moeda(reserva_ideal))

# Progresso
if reserva_ideal > 0:
    percentual = (st.session_state.reserva / reserva_ideal) * 100
    percentual = min(100, percentual)
    st.progress(percentual / 100)
    st.caption(f"Progresso: {percentual:.1f}% da reserva ideal")

# Status da reserva
if st.session_state.reserva >= reserva_ideal:
    st.success("🎉 Excelente! Você atingiu a reserva de emergência ideal!")
elif st.session_state.reserva >= reserva_minima:
    st.info("✅ Bom trabalho! Você tem a reserva mínima garantida.")
else:
    st.warning(
        f"⚠️ Você ainda precisa de {formatar_moeda(reserva_minima - st.session_state.reserva)} para atingir a reserva mínima.")

# ==========================================
# FORMULÁRIO PARA ADICIONAR À RESERVA
# ==========================================

st.divider()
st.subheader("➕ Adicionar à Reserva")

with st.form("form_reserva"):
    valor_reserva = st.number_input(
        "Valor (R$)",
        min_value=0.01,
        step=0.01,
        format="%.2f",
        key="valor_reserva"
    )

    descricao = st.text_input(
        "Descrição",
        placeholder="Ex: Depósito na reserva"
    )

    submitted = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)

    if submitted and valor_reserva > 0:
        # Atualizar session state
        st.session_state.reserva += valor_reserva

        # Salvar no banco como uma transação especial
        payload = {
            "mes": date.today().strftime("%B"),
            "tipo": "reserva",
            "item": descricao if descricao else "Adição à reserva",
            "valor": float(valor_reserva),
            "categoria": "Reserva de Emergência",
            "status": "Confirmado",
            "observacao": "Movimentação da reserva de emergência",
            "data_prevista": str(date.today()),
            "recorrente": False,
            "parcelado": False,
            "numero_parcela": None,
            "total_parcelas": None,
            "tipo_recorrencia": None,
            "meses_recorrencia": None,
            "grupo_recorrencia": None
        }

        if adicionar_transacao(payload):
            limpar_cache()
            st.success(f"✅ {formatar_moeda(valor_reserva)} adicionado à reserva!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar")

# ==========================================
# HISTÓRICO DA RESERVA
# ==========================================

st.divider()
st.subheader("📜 Histórico da Reserva")

# Buscar movimentações da reserva no banco
if not df.empty:
    df_reserva = df[df['tipo'] == 'reserva']

    if not df_reserva.empty:
        df_historico = df_reserva.sort_values('data_prevista', ascending=False)
        df_historico['data_prevista'] = pd.to_datetime(df_historico['data_prevista']).dt.strftime('%d/%m/%Y')
        df_historico['valor'] = df_historico['valor'].apply(formatar_moeda)
        df_historico = df_historico[['data_prevista', 'item', 'valor', 'observacao']]
        df_historico.columns = ['Data', 'Descrição', 'Valor', 'Observação']

        st.dataframe(df_historico, use_container_width=True)
    else:
        st.info("Nenhuma movimentação na reserva ainda.")
else:
    st.info("Nenhuma movimentação na reserva ainda.")

# ==========================================
# BOTÃO PARA RESETAR RESERVA (NÃO LIMPA O BANCO)
# ==========================================

with st.expander("⚠️ Administração da Reserva"):
    if st.button("Zerar Reserva (apenas visual)", use_container_width=True):
        st.session_state.reserva = 0.0
        st.success("Reserva zerada visualmente!")
        st.rerun()