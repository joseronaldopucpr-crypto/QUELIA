import uuid
from dateutil.relativedelta import relativedelta

# ==========================================
# RECORRÊNCIA
# ==========================================

def gerar_grupo_recorrencia():
    return str(uuid.uuid4())

def gerar_datas_recorrentes(data_inicial, quantidade_meses):
    datas = []
    for i in range(quantidade_meses):
        datas.append(data_inicial + relativedelta(months=i))
    return datas

# ==========================================
# MESES EM PORTUGUÊS
# ==========================================

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

def obter_nome_mes(data_ref):
    """Retorna o nome do mês em português"""
    return MESES_PT[data_ref.month]

# ==========================================
# FORMATAÇÃO MONETÁRIA
# ==========================================

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"