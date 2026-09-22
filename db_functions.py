import sqlite3
import json

def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    # Criação das tabelas estruturais permanentes do sistema
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS equipe_tecnica (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, registro TEXT, responsavel INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS comodos_obra (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, comprimento REAL, largura REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_calculados (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT, modo_calculo TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS circuitos_calculados (id TEXT PRIMARY KEY, descricao TEXT, comodo TEXT, pot_w INTEGER, pot_va REAL, fp REAL, tipo TEXT, disj TEXT, curva TEXT, cond TEXT, fase_linha TEXT, tensao INTEGER, ib REAL, ib_corr REAL, comp INTEGER, dv REAL)")
    
    # Verifica se o catálogo técnico está limpo para realizar o abastecimento em massa
    cursor.execute("SELECT COUNT(*) FROM materiais_catalogo")
    if cursor.fetchone()[0] == 0:
        insumos_mestre = [
            # 🧱 DISCIPLINA: CIVIL (Base de cálculo: m² de Área Construída)
            ("Civil", "01. Infraestrutura", "Aço CA-50 ø 10.0mm (Barra de 12m)", 0.35, "barra"),
            ("Civil", "01. Infraestrutura", "Arame Recozido Fio 18 BWG para Amarrações", 0.05, "kg"),
            ("Civil", "01. Infraestrutura", "Forma de Tábua de Pinus 30cm x 3m", 0.12, "un"),
            ("Civil", "02. Superestrutura", "Bloco de Concreto Estrutural 14x19x39cm", 12.5, "un"),
            ("Civil", "02. Superestrutura", "Areia Média Lavada Comercial", 0.08, "m³"),
            ("Civil", "02. Superestrutura", "Argamassa AC-III Cinza Interno/Externo", 0.45, "sc"),
            ("Civil", "03. Acabamentos", "Revestimento Cerâmico PEI-4 Retificado", 1.10, "m²"),
            ("Civil", "03. Acabamentos", "Tinta Acrílica Premium Fosco Premium (Lata 18L)", 0.03, "jg"),

            # 🚰 DISCIPLINA: HIDRÁULICA (Base de cálculo: Metro Linear de Perímetro)
            ("Hidráulica", "01. Água Fria", "Tubo PVC Soldável Azul 25mm (Barra de 6m)", 0.18, "barra"),
            ("Hidráulica", "01. Água Fria", "Joelho 90 Graus PVC Soldável c/ Bucha de Latão 25mm x 1/2", 0.35, "un"),
            ("Hidráulica", "01. Água Fria", "Te 90 Graus Soldável PVC Integral 25mm", 0.15, "un"),
            ("Hidráulica", "01. Água Fria", "Fita Veda Rosca Premium de Alta Densidade 18mm x 25m", 0.05, "rl"),
            ("Hidráulica", "02. Esgoto Sanitário", "Tubo PVC Esgoto Série Normal 100mm (Barra de 6m)", 0.08, "barra"),
            ("Hidráulica", "02. Esgoto Sanitário", "Tubo PVC Esgoto Série Normal 40mm (Barra de 6m)", 0.12, "barra"),
            ("Hidráulica", "02. Esgoto Sanitário", "Caixa Sifonada PVC Quadrada Grelha Abre/Fecha 150x150x50mm", 0.05, "un"),
            ("Hidráulica", "02. Esgoto Sanitário", "Adesivo Plástico Técnico para PVC (Bisnaga 175g)", 0.04, "un"),

            # 🔥 DISCIPLINA: GÁS ENCANADO (Base de cálculo: Multiplicação por Cômodo Mapeado)
            ("Gás Encanado", "01. Tubulação de Carga", "Tubo Multicamadas de Gás PEX-AL-PEX 16mm", 2.80, "m"),
            ("Gás Encanado", "01. Tubulação de Carga", "Conector Fêmea Tipo Crimpagem PEX 16mm x 1/2 NPT", 0.50, "un"),
            ("Gás Encanado", "02. Segurança e Controle", "Válvula de Esfera para Gás Monobloco Angular 90° 1/2", 0.25, "un"),
            ("Gás Encanado", "02. Segurança e Controle", "Abrigo Pré-Moldado de Policarbonato para Medidor Gás G L P", 0.15, "un"),
            ("Gás Encanado", "02. Segurança e Controle", "Tubo Flexível Metálico Inox Malha Trançada 1/2 com 1m", 0.25, "un"),

            # 🌐 DISCIPLINA: INTERNET/DADOS (Base de cálculo: Multiplicação por Cômodo Mapeado)
            ("Internet/Dados", "01. Infraestrutura Seca", "Eletroduto Corrugado de Alta Resistência PEAD Amarelo 3/4", 4.50, "m"),
            ("Internet/Dados", "01. Infraestrutura Seca", "Caixa de Passagem Embutir Termoplástica 4x2", 1.20, "un"),
            ("Internet/Dados", "02. Cabeamento Estruturado", "Cabo de Rede Par Trançado UTP Cat6 Puro Cobre Homologado Anatel", 18.5, "m"),
            ("Internet/Dados", "02. Cabeamento Estruturado", "Conector RJ45 Fêmea Modular Keystone Cat6 para Tomada", 1.00, "un"),
            ("Internet/Dados", "03. Ativos", "Roteador Wireless Mesh Gigabit Dual Band AC1200", 0.25, "un"),

            # 🛡️ DISCIPLINA: SEGURANÇA ELETRÔNICA (Base de cálculo: Multiplicação por Cômodo Mapeado)
            ("Segurança", "01. CFTV", "Câmera Bullet IP Intelbras Full HD 1080p Lente 2.8mm POE", 0.50, "un"),
            ("Segurança", "01. CFTV", "Cabo Coaxial Flexível RF 4mm + Bipolar 80% Malha Cobre (Bobina)", 8.00, "m"),
            ("Segurança", "01. CFTV", "Balun de Vídeo Passivo HD 400 Metros contra Surtos", 1.00, "un"),
            ("Segurança", "02. Perímetro e Alarme", "Sensor de Presença Infravermelho Passivo Interno Digital", 0.35, "un"),
            ("Segurança", "02. Perímetro e Alarme", "Central de Alarme Monitorável Cloud Wi-Fi/GPRS com Teclado", 0.15, "un"),

            # ☀️ DISCIPLINA: ENERGIA SOLAR FOTOVOLTAICA (Base de cálculo: Fator Fixo por Kit Instalado)
            ("Energia Solar", "01. Módulos", "Painel Solar Fotovoltaico Monocristalino Jinko 550W", 6.00, "un"),
            ("Energia Solar", "02. Inversão", "Inversor String Growatt 3kW On-Grid 220V com Wi-Fi Integrado", 1.00, "un"),
            ("Energia Solar", "03. Proteção DC", "String Box Solar 2 Strings 1000V DC com DPS e Fusíveis", 1.00, "un"),
            ("Energia Solar", "04. Estrutural", "Perfil de Alumínio Anodizado Linha Solar para Fixação de Trilhos", 18.0, "m"),
            ("Energia Solar", "04. Estrutural", "Cabo Elétrico Solar Fotovoltaico Flexível Solflex 6.0mm² Preto", 30.0, "m"),
            ("Energia Solar", "04. Estrutural", "Cabo Elétrico Solar Fotovoltaico Flexível Solflex 6.0mm² Vermelho", 30.0, "m"),
            ("Energia Solar", "04. Estrutural", "Conector Técnico Rápido para Painel Fotovoltaico MC4 Macho/Fêmea", 6.00, "jg")
        ]
        cursor.executemany("INSERT INTO materiais_catalogo (fase, etapa, material, quantidade, unidade) VALUES (?, ?, ?, ?, ?)", insumos_mestre)
    
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
        if row: return json.loads(row[0])
    except Exception:
        return valor_padrao
    return valor_padrao

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
    return [{
        "CIRC": r[0], "DESCRIÇÃO": r[1], "COMODO": r[2], "POT_W": r[3], "POT_VA": r[4], "FP": r[5],
        "TIPO": r[6], "DISJ": r[7], "CURVA": r[8], "COND": r[9], "FASE": r[10], "TENSÃO": r[11],
        "IB": r[12], "IB_CORR": r[13], "COMP": r[14], "DV": r[15]
    } for r in rows]

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
def salvar_materiais_calculados_fase(fase, lista_materiais, modo_calculo):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiais_calculados WHERE fase = ? AND modo_calculo = ?", (fase, modo_calculo))
    for m in lista_materiais:
        cursor.execute("""
            INSERT INTO materiais_calculados (fase, etapa, material, quantidade, unidade, modo_calculo) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fase, m["Etapa"], m["Material"], m["Quantidade"], m["Unidade"], modo_calculo))
    conn.commit()
    conn.close()

def listar_materiais_calculados_fase(fase, modo_calculo):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT etapa, material, quantidade, unidade FROM materiais_calculados WHERE fase = ? AND modo_calculo = ?", (fase, modo_calculo))
    rows = cursor.fetchall()
    conn.close()
    return [{"Etapa": r[0], "Material": r[1], "Quantidade": r[2], "Unidade": r[3]} for r in rows]

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
