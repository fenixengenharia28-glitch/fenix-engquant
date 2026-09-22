import sqlite3
import json

def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS equipe_tecnica (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, registro TEXT, responsavel INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS comodos_obra (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, comprimento REAL, largura REAL)")
    conn.commit()
    conn.close()

def salvar_dados_permanentes(chave, valor):
    try:
        conn = sqlite3.connect("fenix_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO configuracoes (id, dados) VALUES (?, ?)", (chave, json.dumps(valor)))
        conn.commit()
        conn.close()
    except Exception:
        pass

def carregar_dados_permanentes(chave, valor_padrao):
    try:
        conn = sqlite3.connect("fenix_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT dados FROM configuracoes WHERE id = ?", (chave,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]: 
            return json.loads(row[0])
    except Exception:
        return valor_padrao
    return valor_padrao

def inserir_cliente_db(nome, endereco, city_uf):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nome, endereco, cidade_uf) VALUES (?, ?, ?)", (nome, endereco, city_uf))
    conn.commit()
    conn.close()

def listar_clientes_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, endereco, cidade_uf FROM clientes")
    rows = cursor.fetchall()
    conn.close()
    return rows

def excluir_cliente_db(id_cliente):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    conn.commit()
    conn.close()

def inserir_material_catalogo(fase, etapa, material, quantidade, unidade):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO materiais_catalogo (fase, etapa, material, quantidade, unidade) VALUES (?, ?, ?, ?, ?)", (fase, etapa, material, quantidade, unidade))
    conn.commit()
    conn.close()

def listar_materiais_catalogo():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, fase, etapa, material, quantidade, unidade FROM materiais_catalogo")
    rows = cursor.fetchall()
    conn.close()
    return rows

def excluir_material_db(id_material):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiais_catalogo WHERE id = ?", (id_material,))
    conn.commit()
    conn.close()

def inserir_membro_equipe(nome, funcao, registro, responsavel):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO equipe_tecnica (nome, funcao, registro, responsavel) VALUES (?, ?, ?, ?)", (nome, funcao, registro, int(responsavel)))
    conn.commit()
    conn.close()

def listar_equipe_tecnica():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, funcao, registro, responsavel FROM equipe_tecnica")
    rows = cursor.fetchall()
    conn.close()
    return rows

def excluir_membro_equipe(id_membro):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipe_tecnica WHERE id = ?", (id_membro,))
    conn.commit()
    conn.close()

def inserir_comodo_db(nome, comprimento, largura):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comodos_obra (nome, comprimento, largura) VALUES (?, ?, ?)", (nome, comprimento, largura))
    conn.commit()
    conn.close()

def listar_comodos_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, comprimento, largura FROM comodos_obra")
    rows = cursor.fetchall()
    conn.close()
    return rows

def atualizar_comodo_db(id_comodo, nome, comprimento, largura):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE comodos_obra SET nome=?, comprimento=?, largura=? WHERE id=?", (nome, comprimento, largura, id_comodo))
    conn.commit()
    conn.close()

def excluir_comodo_db(id_comodo):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comodos_obra WHERE id = ?", (id_comodo,))
    conn.commit()
    conn.close()
