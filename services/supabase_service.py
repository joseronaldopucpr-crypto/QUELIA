import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO SUPABASE
# ==========================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ==========================================
# FUNÇÃO GENÉRICA
# ==========================================

def _request(method, endpoint, **kwargs):

    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"

    try:

        response = requests.request(
            method=method,
            url=url,
            headers=HEADERS,
            timeout=15,
            **kwargs
        )

        return response

    except Exception as e:

        st.error(f"Erro Supabase: {e}")
        return None


# ==========================================
# TRANSAÇÕES
# ==========================================

@st.cache_data(ttl=30)
def carregar_transacoes():

    response = _request(
        "GET",
        "transacoes?select=*&order=data_prevista.asc"
    )

    if response and response.status_code == 200:
        return pd.DataFrame(response.json())

    return pd.DataFrame()


def adicionar_transacao(data):

    response = _request(
        "POST",
        "transacoes",
        json=data
    )

    return response and response.status_code in [200, 201]


def atualizar_transacao(id_transacao, data):

    response = _request(
        "PATCH",
        f"transacoes?id=eq.{id_transacao}",
        json=data
    )

    return response and response.status_code in [200, 204]


def excluir_transacao(id_transacao):

    response = _request(
        "DELETE",
        f"transacoes?id=eq.{id_transacao}"
    )

    return response and response.status_code == 204

    return response and response.status_code == 204


# ==========================================
# CATEGORIAS
# ==========================================

@st.cache_data(ttl=60)
def carregar_categorias():

    response = _request(
        "GET",
        "categorias?select=*&ativa=eq.true&order=nome.asc"
    )

    if response and response.status_code == 200:
        return pd.DataFrame(response.json())

    return pd.DataFrame()


def adicionar_categoria(nome, tipo):

    payload = {
        "nome": nome.upper(),
        "tipo": tipo
    }

    response = _request(
        "POST",
        "categorias",
        json=payload
    )

    if response is not None:
        st.write("STATUS:", response.status_code)
        st.write("RESPOSTA:", response.text)

    return response and response.status_code in [200, 201]


def desativar_categoria(id_categoria):

    response = _request(
        "PATCH",
        f"categorias?id=eq.{id_categoria}",
        json={"ativa": False}
    )

    return response and response.status_code in [200, 204]


def reativar_categoria(id_categoria):

    response = _request(
        "PATCH",
        f"categorias?id=eq.{id_categoria}",
        json={"ativa": True}
    )

    return response and response.status_code in [200, 204]


# ==========================================
# CONFIGURAÇÕES
# ==========================================

@st.cache_data(ttl=120)
def carregar_configuracoes():

    response = _request(
        "GET",
        "configuracoes?select=*&order=id.asc&limit=1"
    )

    if response and response.status_code == 200:

        dados = response.json()

        if len(dados) > 0:
            return dados[0]

    return {
        "id": None,
        "reserva_meta": 10000,
        "saldo_inicial": 0
    }


def salvar_configuracoes(
        reserva_meta,
        saldo_inicial
):

    dados = carregar_configuracoes()

    payload = {
        "reserva_meta": float(reserva_meta),
        "saldo_inicial": float(saldo_inicial)
    }

    # Atualiza sempre o registro mais antigo
    if dados.get("id"):

        response = _request(
            "PATCH",
            f"configuracoes?id=eq.{dados['id']}",
            json=payload
        )

    else:

        response = _request(
            "POST",
            "configuracoes",
            json=payload
        )

    return response and response.status_code in [200, 201, 204]

# ==========================================
# RESERVA DE EMERGÊNCIA
# ==========================================

@st.cache_data(ttl=30)
def carregar_movimentacoes_reserva():

    response = _request(
        "GET",
        "movimentacoes_reserva?select=*&order=created_at.desc"
    )

    if response and response.status_code == 200:
        return pd.DataFrame(response.json())

    return pd.DataFrame()


def registrar_movimentacao_reserva(
        tipo,
        valor,
        motivo
):

    payload = {
        "tipo": tipo,
        "valor": float(valor),
        "motivo": motivo,
        "created_at": datetime.now().isoformat()
    }

    response = _request(
        "POST",
        "movimentacoes_reserva",
        json=payload
    )

    return response and response.status_code in [200, 201]


# ==========================================
# LIMPAR CACHE
# ==========================================

def limpar_cache():

    st.cache_data.clear()