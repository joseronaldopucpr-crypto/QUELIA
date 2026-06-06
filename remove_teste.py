from services.local_service import get_connection

conn = get_connection()
cursor = conn.cursor()

# Ver quantas tem antes
cursor.execute("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Teste de remoção'")
antes = cursor.fetchone()[0]
print(f"Transações com 'Teste de remoção' antes: {antes}")

# Remover
cursor.execute("DELETE FROM transacoes WHERE categoria = 'Teste de remoção'")
conn.commit()
print(f"✅ Removidas {cursor.rowcount} transações")

# Verificar depois
cursor.execute("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Teste de remoção'")
depois = cursor.fetchone()[0]
print(f"Transações com 'Teste de remoção' depois: {depois}")

conn.close()