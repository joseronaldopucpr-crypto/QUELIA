import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
import base64

# ==========================================
# CAMINHO DO BANCO LOCAL
# ==========================================

DB_PATH = "database_local.db"


def get_connection():
    """Retorna conexão com o banco SQLite"""
    return sqlite3.connect(DB_PATH)


# ==========================================
# INICIALIZAR BANCO (CRIAR TABELAS)
# ==========================================

def init_database():
    """Cria as tabelas se não existirem"""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de transações (com coluna comprovante)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT,
            tipo TEXT,
            item TEXT,
            valor REAL,
            categoria TEXT,
            status TEXT,
            observacao TEXT,
            data_prevista DATE,
            recorrente BOOLEAN,
            parcelado BOOLEAN,
            numero_parcela INTEGER,
            total_parcelas INTEGER,
            tipo_recorrencia TEXT,
            meses_recorrencia INTEGER,
            grupo_recorrencia TEXT,
            comprovante TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de metas financeiras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_meta REAL NOT NULL,
            valor_atual REAL DEFAULT 0,
            data_inicio TEXT,
            data_fim TEXT,
            categoria TEXT,
            status TEXT DEFAULT 'ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# ==========================================
# FUNÇÕES DE CATEGORIAS
# ==========================================

def carregar_categorias():
    """Carrega todas as categorias"""
    init_database()
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM categorias ORDER BY nome", conn)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar categorias: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def adicionar_categoria(nome, tipo):
    """Adiciona uma nova categoria"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    conn.commit()
    conn.close()
    return True


def excluir_categoria(id_categoria):
    """Exclui uma categoria"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
    conn.commit()
    conn.close()
    return True


def atualizar_categoria(id_categoria, nome, tipo):
    """Atualiza uma categoria"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE categorias SET nome = ?, tipo = ? WHERE id = ?", (nome, tipo, id_categoria))
    conn.commit()
    conn.close()
    return True


# ==========================================
# FUNÇÕES DE TRANSAÇÕES
# ==========================================

def carregar_transacoes():
    """Carrega todas as transações"""
    init_database()
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM transacoes ORDER BY data_prevista DESC", conn)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar transações: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def adicionar_transacao(payload):
    """Adiciona uma nova transação"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO transacoes (
            mes, tipo, item, valor, categoria, status, observacao,
            data_prevista, recorrente, parcelado, numero_parcela,
            total_parcelas, tipo_recorrencia, meses_recorrencia, grupo_recorrencia, comprovante
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payload.get('mes'), payload.get('tipo'), payload.get('item'),
        payload.get('valor'), payload.get('categoria'), payload.get('status'),
        payload.get('observacao'), payload.get('data_prevista'),
        payload.get('recorrente', False), payload.get('parcelado', False),
        payload.get('numero_parcela'), payload.get('total_parcelas'),
        payload.get('tipo_recorrencia'), payload.get('meses_recorrencia'),
        payload.get('grupo_recorrencia'), payload.get('comprovante')
    ))

    conn.commit()
    conn.close()
    return True


def excluir_transacao(id_transacao):
    """Exclui uma transação"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (id_transacao,))
    conn.commit()
    conn.close()
    return True


def limpar_cache():
    """Limpa cache - versão segura (sem cache ativo)"""
    pass


# ==========================================
# FUNÇÕES DE METAS FINANCEIRAS
# ==========================================

def carregar_metas():
    """Carrega todas as metas"""
    init_database()
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM metas ORDER BY id DESC", conn)
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()


def adicionar_meta(nome, valor_meta, data_inicio, data_fim, categoria):
    """Adiciona uma nova meta"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO metas (nome, valor_meta, data_inicio, data_fim, categoria, valor_atual, status)
            VALUES (?, ?, ?, ?, ?, 0, 'ativo')
        ''', (nome, valor_meta, str(data_inicio), str(data_fim), categoria))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao adicionar meta: {e}")
        return False
    finally:
        conn.close()


def excluir_meta(id_meta):
    """Exclui uma meta"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM metas WHERE id = ?", (id_meta,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao excluir meta: {e}")
        return False
    finally:
        conn.close()


def atualizar_progresso_meta(id_meta, valor_atual):
    """Atualiza o progresso da meta"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE metas SET valor_atual = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (valor_atual, id_meta))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao atualizar meta: {e}")
        return False
    finally:
        conn.close()


# ==========================================
# FUNÇÕES DE COMPROVANTES
# ==========================================

def salvar_comprovante(arquivo):
    """Salva o arquivo como base64 no banco"""
    if arquivo is None:
        return None
    try:
        dados = arquivo.read()
        return base64.b64encode(dados).decode('utf-8')
    except:
        return None


def carregar_comprovante(comprovante_base64):
    """Carrega o comprovante para exibição"""
    if comprovante_base64 is None:
        return None
    try:
        return base64.b64decode(comprovante_base64)
    except:
        return None


# ==========================================
# FUNÇÕES DE ORÇAMENTOS
# ==========================================

def carregar_orcamentos():
    """Carrega todos os orçamentos"""
    init_database()
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM orcamentos", conn)
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()


def salvar_orcamento(categoria, limite):
    """Salva ou atualiza um orçamento"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO orcamentos (categoria, limite) VALUES (?, ?)", (categoria, limite))
    conn.commit()
    conn.close()
    return True


def excluir_orcamento(categoria):
    """Exclui um orçamento"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orcamentos WHERE categoria = ?", (categoria,))
    conn.commit()
    conn.close()
    return True


# ==========================================
# FUNÇÕES DE EDIÇÃO DE TRANSAÇÕES
# ==========================================

def carregar_transacao_por_id(id_transacao):
    """Carrega uma transação específica pelo ID"""
    init_database()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transacoes WHERE id = ?", (id_transacao,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        st.error(f"Erro ao carregar transação: {e}")
        return None
    finally:
        conn.close()


def atualizar_transacao(id_transacao, payload):
    """Atualiza uma transação existente"""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   UPDATE transacoes
                   SET mes               = ?,
                       tipo              = ?,
                       item              = ?,
                       valor             = ?,
                       categoria         = ?,
                       status            = ?,
                       observacao        = ?,
                       data_prevista     = ?,
                       recorrente        = ?,
                       parcelado         = ?,
                       numero_parcela    = ?,
                       total_parcelas    = ?,
                       tipo_recorrencia  = ?,
                       meses_recorrencia = ?,
                       grupo_recorrencia = ?,
                       comprovante       = ?
                   WHERE id = ?
                   ''', (
                       payload.get('mes'), payload.get('tipo'), payload.get('item'),
                       payload.get('valor'), payload.get('categoria'), payload.get('status'),
                       payload.get('observacao'), payload.get('data_prevista'),
                       payload.get('recorrente', False), payload.get('parcelado', False),
                       payload.get('numero_parcela'), payload.get('total_parcelas'),
                       payload.get('tipo_recorrencia'), payload.get('meses_recorrencia'),
                       payload.get('grupo_recorrencia'), payload.get('comprovante'),
                       id_transacao
                   ))

    conn.commit()
    conn.close()
    return True


# Inicializar banco ao importar
init_database()