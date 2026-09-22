import sqlite3
import json

def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    # Tabelas base de cadastro administrativo e geométrico
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS equipe_tecnica (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, registro TEXT, responsavel INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS comodos_obra (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, comprimento REAL, largura REAL)")
    
    # Tabelas de persistência permanente para os insumos calculados e prancha elétrica
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_calculados (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS circuitos_calculados (id TEXT PRIMARY KEY, descricao TEXT, comodo TEXT, pot_w INTEGER, pot_va REAL, fp REAL, tipo TEXT, disj TEXT, curva TEXT, cond TEXT, fase_linha TEXT, tensao INTEGER, ib REAL, ib_corr REAL, comp INTEGER, dv REAL)")
    conn.commit()
    conn.close()

# --- FUNÇÕES DE CONFIGURAÇÃO GERAL ---
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

# --- PERSISTÊNCIA PERMANENTE DE CIRCUITOS (ABA ELÉTRICA) ---
def inserir_circuito_permanente(c_dict):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO circuitos_calculados 
        (id, descricao, comodo, pot_w, pot_va, fp, tipo, disj, curva, cond, fase_linha, tensao, ib, ib_corr, comp, dv)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        c_dict["CIRC"], c_dict["DESCRIÇÃO"], c_dict["COMODO"], c_dict["POT_W"], c_dict["POT_VA"], c_dict["FP"],
        c_dict["TIPO"], c_dict["DISJ"], c_dict["CURVA"], c_dict["COND"], c_dict["FASE"], c_dict["TENSÃO"],
        c_dict["IB"], c_dict["IB_CORR"], c_dict["COMP"], c_dict["DV"]
    ))
    conn.commit()
    conn.close()

def listar_circuitos_permanentes():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, descricao, comodo, pot_w, pot_va, fp, tipo, disj, curva, cond, fase_linha, tensao, ib, ib_corr, comp, dv FROM circuitos_calculados")
    rows = cursor.fetchall()
    conn.close()
    lista = []
    for r in rows:
        lista.append({
            "CIRC": r[0], "DESCRIÇÃO": r[1], "COMODO": r[2], "POT_W": r[3], "POT_VA": r[4], "FP": r[5],
            "TIPO": r[6], "DISJ": r[7], "CURVA": r[8], "COND": r[9], "FASE": r[10], "TENSÃO": r[11],
            "IB": r[12], "IB_CORR": r[13], "COMP": r[14], "DV": r[15]
        })
    return lista

def excluir_circuito_permanente(id_circuito):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM circuitos_calculados WHERE id = ?", (id_circuito,))
    conn.commit()
    conn.close()

def limpar_todos_circuitos_permanentes():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM circuitos_calculados")
    conn.commit()
    conn.close()

# --- PERSISTÊNCIA PERMANENTE DE MATERIAIS DE OBRA (TODAS AS DISCIPLINAS) ---
def salvar_materiais_calculados_fase(fase, lista_materiais):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiais_calculados WHERE fase = ?", (fase,))
    
    # CORRIGIDO: Vinculação de variável corrigida de lista_materials para lista_materiais
    for m in lista_materiais:
        cursor.execute("""
            INSERT INTO materiais_calculados (fase, etapa, material, quantidade, unidade) 
            VALUES (?, ?, ?, ?, ?)
        """, (fase, m["Etapa"], m["Material"], m["Quantidade"], m["Unidade"]))
    conn.commit()
    conn.close()

def listar_materiais_calculados_fase(fase):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT etapa, material, quantidade, unidade FROM materiais_calculados WHERE fase = ?", (fase,))
    rows = cursor.fetchall()
    conn.close()
    return [{"Etapa": r[0], "Material": r[1], "Quantidade": r[2], "Unidade": r[3]} for r in rows]

# --- CRUD DE CADASTROS ADMINISTRATIVOS ---
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
