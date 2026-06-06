import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import re
import base64

from services.local_service import (
    carregar_transacoes,
    carregar_categorias,
    adicionar_transacao,
    excluir_transacao,
    limpar_cache,
    carregar_transacao_por_id,
    atualizar_transacao
)

from services.financeiro_service import (
    gerar_grupo_recorrencia,
    gerar_datas_recorrentes,
    obter_nome_mes
)

st.set_page_config(
    page_title="Lançamentos",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# FUNÇÕES
# ==========================================

def formatar_moeda(valor):
    try:
        if valor == 0 or valor < 0.01:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def converter_moeda_para_float(valor_str):
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    if not valor_str:
        return 0.0
    valor_str = str(valor_str).strip()
    valor_str = valor_str.replace('R$', '').strip()

    if valor_str.isdigit() and len(valor_str) > 2:
        inteiro = valor_str[:-2]
        centavos = valor_str[-2:]
        valor_str = f"{inteiro}.{centavos}"
    else:
        valor_str = valor_str.replace('.', '')
        valor_str = valor_str.replace(',', '.')

    valor_str = re.sub(r'[^0-9.-]', '', valor_str)
    try:
        return float(valor_str)
    except:
        return 0.0


def formatar_data_br(data):
    if isinstance(data, str):
        data = datetime.strptime(data, "%Y-%m-%d")
    return data.strftime("%d/%m/%Y")


def salvar_comprovante(arquivo):
    if arquivo is None:
        return None
    try:
        dados = arquivo.read()
        return base64.b64encode(dados).decode('utf-8')
    except:
        return None


def carregar_transacao_para_edicao(id_transacao):
    transacao = carregar_transacao_por_id(id_transacao)
    if transacao:
        st.session_state.editando_id = id_transacao
        st.session_state.editando_item = transacao.get('item', '')
        st.session_state.editando_valor_input = str(transacao.get('valor', 0))
        st.session_state.editando_categoria = transacao.get('categoria', '')
        st.session_state.editando_tipo = transacao.get('tipo', 'despesa')
        st.session_state.editando_status = transacao.get('status', 'Pendente')
        st.session_state.editando_observacao = transacao.get('observacao', '')
        st.session_state.editando_data = transacao.get('data_prevista', date.today())
        st.session_state.editando_modo = "Editar"
        st.rerun()


# ==========================================
# TÍTULO
# ==========================================

st.title("💰 Lançamentos")

# ==========================================
# AUTO-REFRESH
# ==========================================

st_autorefresh(interval=10 * 1000, key="auto_refresh")

# ==========================================
# CARREGAR CATEGORIAS
# ==========================================

df_categorias = carregar_categorias()

if df_categorias.empty:
    st.warning("Nenhuma categoria cadastrada. Vá na página 'categorias' para adicionar.")
    st.stop()

# ==========================================
# INICIALIZAR SESSION STATE
# ==========================================

if 'qtd_recorrente' not in st.session_state:
    st.session_state.qtd_recorrente = 10
if 'qtd_parcelas' not in st.session_state:
    st.session_state.qtd_parcelas = 6
if 'item' not in st.session_state:
    st.session_state.item = ""
if 'valor_input' not in st.session_state:
    st.session_state.valor_input = ""

# ==========================================
# FORMULÁRIO PRINCIPAL
# ==========================================

with st.form("form_lancamento"):
    col1, col2 = st.columns(2)

    with col1:
        tipo = st.selectbox("📌 Tipo", ["receita", "despesa"], key="tipo_select")

    with col2:
        if df_categorias.empty:
            st.warning("⚠️ Nenhuma categoria cadastrada.")
            categoria = "Nenhuma categoria disponível"
        else:
            categoria = st.selectbox("📂 Categoria", df_categorias["nome"].sort_values().tolist(),
                                     key="categoria_select")

    item = st.text_input("📝 Descrição", placeholder="Ex: Salário, Aluguel...", value=st.session_state.get("item", ""))

    valor_input = st.text_input("💰 Valor (R$)", placeholder="Digite 1001 para R$ 10,01",
                                value=st.session_state.get("valor_input", ""))
    valor = converter_moeda_para_float(valor_input)

    data_prevista = st.date_input("📅 Data Prevista", value=date.today(), key="data_prevista")
    st.caption(f"📅 Data: {data_prevista.strftime('%d/%m/%Y')}")

    col1, col2 = st.columns(2)
    with col1:
        status_options = ["Pendente", "Pago"] if tipo == "despesa" else ["Pendente", "Recebido"]
        status = st.selectbox("📊 Status", status_options, key="status_select")
    with col2:
        observacao = st.text_area("📋 Observação", placeholder="Opcional", key="observacao")

    # Comprovante
    st.subheader("📎 Comprovante (opcional)")
    comprovante_file = st.file_uploader(
        "Anexar comprovante",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Anexe foto da nota fiscal, comprovante de pagamento, etc.",
        key="comprovante_upload"
    )

    if comprovante_file:
        st.success(f"✅ Arquivo '{comprovante_file.name}' selecionado")
        if comprovante_file.type.startswith('image/'):
            st.image(comprovante_file, caption="Pré-visualização", width=200)

    st.divider()

    modo = st.radio("🔄 Tipo de lançamento", ["Único", "Recorrente Mensal", "Parcelado"], horizontal=True, key="modo")

    quantidade = 1

    if modo == "Recorrente Mensal":
        quantidade = st.number_input("📆 Quantidade de meses", min_value=1, max_value=120,
                                     value=st.session_state.qtd_recorrente, key="qtd_recorrente_input")
        st.session_state.qtd_recorrente = quantidade
        if valor > 0:
            st.info(f"📊 Serão {quantidade} meses de {formatar_moeda(valor)}")
    elif modo == "Parcelado":
        quantidade = st.number_input("🔢 Quantidade de parcelas", min_value=2, max_value=24,
                                     value=st.session_state.qtd_parcelas, key="qtd_parcelas_input")
        st.session_state.qtd_parcelas = quantidade
        if valor > 0 and quantidade > 0:
            st.info(f"💰 Cada parcela: {formatar_moeda(valor / quantidade)}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        preview = st.form_submit_button("👁️ Visualizar", use_container_width=True)
    with col2:
        salvar = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)

# ==========================================
# VISUALIZAR
# ==========================================

if preview and item.strip() and valor > 0:
    st.subheader("📋 Pré-visualização")
    datas = gerar_datas_recorrentes(data_prevista, quantidade)

    if modo == "Parcelado":
        st.success(f"🎯 {quantidade}x de {formatar_moeda(valor / quantidade)} = {formatar_moeda(valor)}")
    elif modo == "Recorrente Mensal":
        st.success(f"🎯 {quantidade} meses de {formatar_moeda(valor)}")
    else:
        st.success(f"🎯 Lançamento único de {formatar_moeda(valor)}")

    for i, data_ref in enumerate(datas, 1):
        if modo == "Parcelado":
            desc = f"{item.upper()} ({i}/{quantidade})"
            valor_show = valor / quantidade
        elif modo == "Recorrente Mensal":
            desc = f"{item.upper()} (Mês {i})"
            valor_show = valor
        else:
            desc = item.upper()
            valor_show = valor

        st.write(f"📌 {desc} - 📅 {formatar_data_br(data_ref)} - 💰 {formatar_moeda(valor_show)}")

    st.info(f"✅ Serão criados {quantidade} lançamento(s)")

# ==========================================
# SALVAR
# ==========================================

if salvar:
    if not item.strip():
        st.error("❌ Informe uma descrição")
    elif valor <= 0:
        st.error("❌ Informe um valor válido")
    elif df_categorias.empty:
        st.error("❌ Nenhuma categoria cadastrada. Vá na página 'categorias' para adicionar.")
    else:
        grupo_recorrencia = None
        if modo != "Único":
            grupo_recorrencia = gerar_grupo_recorrencia()

        datas = gerar_datas_recorrentes(data_prevista, quantidade)
        sucesso = 0

        for i, data_ref in enumerate(datas, 1):
            if modo == "Parcelado":
                desc = f"{item.upper()} ({i}/{quantidade})"
                valor_atual = valor / quantidade
            elif modo == "Recorrente Mensal":
                desc = f"{item.upper()} (Mês {i})"
                valor_atual = valor
            else:
                desc = item.upper()
                valor_atual = valor

            payload = {
                "mes": obter_nome_mes(data_ref),
                "tipo": tipo,
                "item": desc,
                "valor": float(valor_atual),
                "categoria": categoria,
                "status": status,
                "observacao": observacao,
                "data_prevista": str(data_ref),
                "recorrente": modo == "Recorrente Mensal",
                "parcelado": modo == "Parcelado",
                "numero_parcela": i if modo == "Parcelado" else None,
                "total_parcelas": quantidade if modo == "Parcelado" else None,
                "tipo_recorrencia": "mensal" if modo == "Recorrente Mensal" else None,
                "meses_recorrencia": quantidade if modo == "Recorrente Mensal" else None,
                "grupo_recorrencia": grupo_recorrencia,
                "comprovante": salvar_comprovante(comprovante_file) if comprovante_file else None
            }

            if adicionar_transacao(payload):
                sucesso += 1

        limpar_cache()

        if sucesso > 0:
            if modo == "Único":
                st.success(f"✅ Lançamento de {formatar_moeda(valor)} criado com sucesso!")
            elif modo == "Recorrente Mensal":
                st.success(f"✅ {sucesso} lançamentos mensais de {formatar_moeda(valor)} criados!")
            else:
                st.success(
                    f"✅ {sucesso} parcelas de {formatar_moeda(valor / quantidade)} criadas! Total: {formatar_moeda(valor)}")

            st.balloons()
            st.session_state.item = ""
            st.session_state.valor_input = ""
            st.rerun()
        else:
            st.error("❌ Erro ao salvar")

# ==========================================
# FORMULÁRIO DE EDIÇÃO (FORA DO FORMULÁRIO PRINCIPAL)
# ==========================================

if st.session_state.get('editando_modo') == "Editar":
    st.divider()
    st.subheader("✏️ Editando Lançamento")

    with st.form("form_edicao"):
        col1, col2 = st.columns(2)

        with col1:
            tipo_edit = st.selectbox("📌 Tipo", ["receita", "despesa"],
                                     index=0 if st.session_state.editando_tipo == 'receita' else 1,
                                     key="edit_tipo")

        with col2:
            categorias_lista = df_categorias["nome"].sort_values().tolist() if not df_categorias.empty else []
            categoria_edit = st.selectbox("📂 Categoria", categorias_lista,
                                          index=categorias_lista.index(
                                              st.session_state.editando_categoria) if st.session_state.editando_categoria in categorias_lista else 0,
                                          key="edit_categoria")

        item_edit = st.text_input("📝 Descrição", value=st.session_state.editando_item, key="edit_item")

        valor_edit = st.text_input("💰 Valor (R$)", value=st.session_state.editando_valor_input, key="edit_valor")
        valor_convertido = converter_moeda_para_float(valor_edit)

        if isinstance(st.session_state.editando_data, str):
            data_edit = st.date_input("📅 Data Prevista",
                                      value=datetime.strptime(st.session_state.editando_data, "%Y-%m-%d").date(),
                                      key="edit_data")
        else:
            data_edit = st.date_input("📅 Data Prevista", value=st.session_state.editando_data, key="edit_data")

        status_edit = st.selectbox("📊 Status",
                                   ["Pendente", "Pago"] if tipo_edit == "despesa" else ["Pendente", "Recebido"],
                                   index=0 if st.session_state.editando_status == "Pendente" else 1,
                                   key="edit_status")

        observacao_edit = st.text_area("📋 Observação", value=st.session_state.editando_observacao,
                                       key="edit_observacao")

        st.subheader("📎 Comprovante (opcional)")
        comprovante_edit = st.file_uploader("Anexar novo comprovante", type=['png', 'jpg', 'jpeg', 'pdf'],
                                            key="edit_comprovante")

        if comprovante_edit:
            st.success(f"✅ Arquivo '{comprovante_edit.name}' selecionado")

        col1, col2 = st.columns(2)
        with col1:
            salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
        with col2:
            cancelar_edicao = st.form_submit_button("❌ Cancelar", use_container_width=True)

        if salvar_edicao:
            if not item_edit.strip():
                st.error("❌ Informe uma descrição")
            elif valor_convertido <= 0:
                st.error("❌ Informe um valor válido")
            else:
                payload = {
                    "mes": obter_nome_mes(data_edit),
                    "tipo": tipo_edit,
                    "item": item_edit.upper(),
                    "valor": float(valor_convertido),
                    "categoria": categoria_edit,
                    "status": status_edit,
                    "observacao": observacao_edit,
                    "data_prevista": str(data_edit),
                    "recorrente": False,
                    "parcelado": False,
                    "numero_parcela": None,
                    "total_parcelas": None,
                    "tipo_recorrencia": None,
                    "meses_recorrencia": None,
                    "grupo_recorrencia": None,
                    "comprovante": salvar_comprovante(comprovante_edit) if comprovante_edit else None
                }

                if atualizar_transacao(st.session_state.editando_id, payload):
                    limpar_cache()
                    st.success("✅ Lançamento atualizado com sucesso!")
                    st.session_state.editando_modo = None
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar")

        if cancelar_edicao:
            st.session_state.editando_modo = None
            st.rerun()

# ==========================================
# EDITAR / EXCLUIR LANÇAMENTO
# ==========================================

st.divider()
st.subheader("✏️ Editar / 🗑️ Excluir Lançamento")

df_transacoes = carregar_transacoes()

if df_transacoes.empty:
    st.info("📭 Nenhum lançamento cadastrado")
else:
    for _, row in df_transacoes.iterrows():
        cor = "#2ecc71" if row['tipo'] == 'receita' else "#e74c3c"
        valor_fmt = formatar_moeda(row['valor'])
        data_fmt = formatar_data_br(row['data_prevista'])

        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            st.markdown(f"""
            <div style="background-color: #2d2d44; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 4px solid {cor};">
                <span style="font-weight: bold;">{row['id']}</span> - 
                <span style="color: {cor};">{row['item']}</span> - 
                <span>{valor_fmt}</span> - 
                <span>{data_fmt}</span> - 
                <span>{row['categoria']}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button(f"✏️ Editar", key=f"edit_{row['id']}"):
                carregar_transacao_para_edicao(row['id'])

        with col3:
            if st.button(f"🗑️ Excluir", key=f"del_{row['id']}"):
                if excluir_transacao(row['id']):
                    limpar_cache()
                    st.success("✅ Lançamento excluído com sucesso!")
                    st.rerun()

        st.divider()