from services.local_service import get_connection

conn = get_connection()
cursor = conn.cursor()

# Criar tabela metas se não existir
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
print("✅ Tabela metas criada/verificada com sucesso!")

# Verificar se existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metas'")
resultado = cursor.fetchone()
if resultado:
    print("✅ Tabela metas existe!")
else:
    print("❌ Tabela metas NÃO existe!")

conn.close()