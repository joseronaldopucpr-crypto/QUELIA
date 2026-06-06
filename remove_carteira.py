from services.local_service import get_connection

conn = get_connection()
cursor = conn.cursor()

# Contar antes
cursor.execute("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Carteira'")
antes = cursor.fetchone()[0]
print(f"Transações com 'Carteira' antes: {antes}")

# Remover
cursor.execute("DELETE FROM transacoes WHERE categoria = 'Carteira'")
conn.commit()

print(f"✅ Removidas {cursor.rowcount} transações com categoria 'Carteira'")

# Verificar depois
cursor.execute("SELECT COUNT(*) FROM transacoes WHERE categoria = 'Carteira'")
depois = cursor.fetchone()[0]
print(f"Transações com 'Carteira' depois: {depois}")

conn.close()