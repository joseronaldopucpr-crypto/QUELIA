from services.local_service import carregar_transacoes
import pandas as pd
from datetime import datetime

df = carregar_transacoes()
df['data_prevista'] = pd.to_datetime(df['data_prevista'])

hoje = datetime.now()
limite = hoje - pd.DateOffset(months=6)

despesas_6m = df[(df['tipo'] == 'despesa') & (df['data_prevista'] >= limite)]
total = despesas_6m['valor'].sum()
media = total / 6 if total > 0 else 0

print(f'Período: {limite.strftime("%Y-%m-%d")} até {hoje.strftime("%Y-%m-%d")}')
print(f'Total despesas: R$ {total:.2f}')
print(f'Média mensal: R$ {media:.2f}')
print(f'Reserva mínima (3 meses): R$ {media * 3:.2f}')
print(f'Reserva ideal (6 meses): R$ {media * 6:.2f}')