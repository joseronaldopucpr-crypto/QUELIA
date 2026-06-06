import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

SUPABASE_URL = "https://djazuglbjofnbyjslftr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRqYXp1Z2xiam9mbmJ5anNsZnRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAxMTUwNDMsImV4cCI6MjA5NTY5MTA0M30.NjLQUC7oy9-yPEL-eYRCaBYO26JNHq6wPjGePnEyqf4"


@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_data(ttl=30, show_spinner=False)
def carregar_transacoes():
    supabase = get_supabase()
    try:
        response = supabase.table("transacoes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar transações: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def carregar_categorias():
    supabase = get_supabase()
    try:
        response = supabase.table("categorias").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar categorias: {e}")
        return pd.DataFrame()


def adicionar_transacao(payload):
    supabase = get_supabase()
    try:
        response = supabase.table("transacoes").insert(payload).execute()
        if response.data:
            carregar_transacoes.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False


def excluir_transacao(id_transacao):
    supabase = get_supabase()
    try:
        response = supabase.table("transacoes").delete().eq("id", id_transacao).execute()
        if response.data:
            carregar_transacoes.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False


def limpar_cache():
    carregar_transacoes.clear()
    carregar_categorias.clear()
    carregar_configuracoes.clear()


# ==========================================
# CONFIGURAÇÕES DO SISTEMA
# ==========================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_configuracoes():
    """Carrega configurações do sistema"""
    supabase = get_supabase()
    try:
        response = supabase.table("configuracoes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        # Tabela pode não existir ainda
        return pd.DataFrame()


def salvar_configuracao(chave, valor):
    """Salva ou atualiza uma configuração"""
    supabase = get_supabase()
    try:
        # Verificar se já existe
        response = supabase.table("configuracoes").select("*").eq("chave", chave).execute()

        if response.data:
            # Atualizar
            supabase.table("configuracoes").update({"valor": valor}).eq("chave", chave).execute()
        else:
            # Inserir
            supabase.table("configuracoes").insert({"chave": chave, "valor": valor}).execute()

        carregar_configuracoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configuração: {e}")
        return False


def excluir_configuracao(chave):
    """Exclui uma configuração"""
    supabase = get_supabase()
    try:
        supabase.table("configuracoes").delete().eq("chave", chave).execute()
        carregar_configuracoes.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir configuração: {e}")
        return False