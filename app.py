import streamlit as st
import pandas as pd
import math
import sqlite3
import json
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# --- ENGINE DO BANCO DE DADOS PERSISTENTE LOCAL ---
def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    conn.commit()
    conn.close()

init_db()
def salvar_dados_permanentes(chave, valor):
    try:
        conn = sqlite3.connect("fenix_database.db")
        cursor = conn.cursor()
        json_dados = json.dumps(valor)
        cursor.execute("INSERT OR REPLACE INTO configuracoes (id, dados) VALUES (?, ?)", (chave, json_dados))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao salvar dados estruturais: {e}")

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

def atualizar_lote_materiais_fase(fase, lista_materiais):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiais_catalogo WHERE fase = ?", (fase,))
    for m in lista_materials:
        cursor.execute("INSERT INTO materiais_catalogo (fase, etapa, material, quantidade, unidade) VALUES (?, ?, ?, ?, ?)", 
                       (fase, m.get("Etapa", "Geral"), m.get("Material", ""), float(m.get("Quantidade", 0.0)), m.get("Unidade", "un")))
    conn.commit()
    conn.close()
# Sincroniza a memória de interface com os registros fixados no banco SQLite
if "db_sync_completo" not in st.session_state:
    raw_db = listar_materials_catalogo()
    st.session_state.lista_materials_civil = [{"Etapa": r[2], "Material": r[3], "Quantidade": r[4], "Unidade": r[5]} for r in raw_db if r[1] == "Civil"]
    st.session_state.lista_materials_eletricos = carregar_dados_permanentes("materials_eletricos", [])
    st.session_state.lista_materials_hidraulicos = [{"Etapa": r[2], "Material": r[3], "Quantidade": r[4], "Unidade": r[5]} for r in raw_db if r[1] == "Hidráulica"]
    st.session_state.lista_materials_gas = [{"Etapa": r[2], "Material": r[3], "Quantidade": r[4], "Unidade": r[5]} for r in raw_db if r[1] == "Gás Encanado"]
    st.session_state.lista_materials_dados = [{"Etapa": r[2], "Material": r[3], "Quantidade": r[4], "Unidade": r[5]} for r in raw_db if r[1] == "Internet/Dados"]
    st.session_state.lista_materials_seguranca = [{"Etapa": r[2], "Material": r[3], "Quantidade": r[4], "Unidade": r[5]} for r in raw_db if r[1] == "Segurança"]
    
    st.session_state.funcionarios = carregar_dados_permanentes("funcionarios", [
        {"id": 1, "Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA_RE": "MG20231045", "Responsavel": True}
    ])
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
    st.session_state.comodos = carregar_dados_permanentes("comodos", [])
    st.session_state.seguranca_insumos = carregar_dados_permanentes("seguranca", {"cameras": 4, "sensores": 3, "cabo_m": 100})
    st.session_state.db_sync_completo = True
def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(220, (n_circ * 30) + 120)
    d = Drawing(720, altura_d)
    
    d.add(Line(20, altura_d - 40, 90, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 32, f"Rede BT Ramal: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    
    d.add(Rect(90, altura_d - 52, 45, 24, fillColor=colors.HexColor('#EFF6FF'), strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(95, altura_d - 44, "DJ Geral", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(95, altura_d - 51, f"{dj_pad}", fontSize=6.5, fontName='Helvetica'))
    d.add(Line(135, altura_d - 40, 160, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    
    d.add(Rect(160, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(166, altura_d - 44, "DPS", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(164, altura_d - 51, "45kA Cl.II", fontSize=5.5))
    d.add(Line(195, altura_d - 40, 215, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    
    d.add(Rect(215, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(222, altura_d - 44, "IDR", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(219, altura_d - 51, "30mA", fontSize=5.5))
    
    d.add(Line(250, altura_d - 40, 280, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 40, 280, 20, strokeColor=colors.black, strokeWidth=2))
    d.add(String(285, altura_d - 35, "Barramento QDC", fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#1E3A8A')))
    
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 80) - (idx * 30)
        d.add(Circle(280, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(280, y, 320, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(320, y, 335, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(315, y + 5, f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(335, y, 365, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(340, y + 4, str(c.get('COND','2.5 mm²')), fontSize=6.5, fillColor=colors.HexColor('#2563EB'), fontName='Helvetica-Bold'))
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:22]} - {c.get('COMODO','Geral')} ({c.get('POT_W',1000)}W)", fontSize=7.5, fontName='Helvetica'))
    return d
def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(220, (n_circ * 30) + 120)
    d = Drawing(720, altura_d)
    
    d.add(Line(20, altura_d - 40, 90, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 32, f"Rede BT Ramal: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    
    d.add(Rect(90, altura_d - 52, 45, 24, fillColor=colors.HexColor('#EFF6FF'), strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(95, altura_d - 44, "DJ Geral", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(95, altura_d - 51, f"{dj_pad}", fontSize=6.5, fontName='Helvetica'))
    d.add(Line(135, altura_d - 40, 160, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    
    d.add(Rect(160, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(166, altura_d - 44, "DPS", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(164, altura_d - 51, "45kA Cl.II", fontSize=5.5))
    d.add(Line(195, altura_d - 40, 215, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    
    d.add(Rect(215, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(222, altura_d - 44, "IDR", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(219, altura_d - 51, "30mA", fontSize=5.5))
    
    d.add(Line(250, altura_d - 40, 280, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 40, 280, 20, strokeColor=colors.black, strokeWidth=2))
    d.add(String(285, altura_d - 35, "Barramento QDC", fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#1E3A8A')))
    
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 80) - (idx * 30)
        d.add(Circle(280, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(280, y, 320, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(320, y, 335, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(315, y + 5, f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(335, y, 365, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(340, y + 4, str(c.get('COND','2.5 mm²')), fontSize=6.5, fillColor=colors.HexColor('#2563EB'), fontName='Helvetica-Bold'))
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:22]} - {c.get('COMODO','Geral')} ({c.get('POT_W',1000)}W)", fontSize=7.5, fontName='Helvetica'))
    return d
def dimensionar_circuito_nbr5410(potencia, tensao, comprimento, tipo_carga):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.8
    ib = potencia / (tensao * fp)
    bitola_inicial = 1.5 if "Iluminação" in tipo_carga else 2.5
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    bitola_final = bitola_inicial
    iz_cabo = 17.5 if "Iluminação" in tipo_carga else 24.0
    for b, cap in zip(bitolas_comerciais, capacidades_corrente):
        if b >= bitola_inicial and cap >= ib:
            bitola_final = b
            iz_cabo = cap
            break
    rho = 1 / 58.0
    while True:
        dv_perc = (2 * rho * comprimento * ib * 100) / (tensao * bitola_final)
        if dv_perc <= 2.0 or bitola_final >= 16.0: break
        idx = bitolas_comerciais.index(bitola_final)
        if idx < len(bitolas_comerciais) - 1:
            bitola_final = bitolas_comerciais[idx + 1]
            iz_cabo = capacidades_corrente[idx + 1]
        else: break
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= iz_cabo:
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
    return bitola_final, disjuntor_final, "B" if "Iluminação" in tipo_carga else "C", round(ib, 2)

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.write("### 👤 Central de Clientes (Gravar e Selecionar)")
    lista_clientes = listar_clientes_db()
    opcoes_clientes = ["-- Cadastrar Novo Cliente --"] + [f"ID {c[0]} - {c[1]}" for c in lista_clientes]
    cliente_selecionado = st.selectbox("📂 Escolher Cliente Salvo:", opcoes_clientes)
    if cliente_selecionado != "-- Cadastrar Novo Cliente --":
        id_cli = int(cliente_selecionado.split(" - ")[0].replace("ID ", ""))
        dados_cli_atual = [c for c in lista_clientes if c[0] == id_cli][0]
        cliente_nome = st.text_input("Nome Completo do Cliente:", value=dados_cli_atual[1])
        cliente_endereco = st.text_input("Endereço da Obra:", value=dados_cli_atual[2])
        cliente_cidade = st.text_input("Cidade / UF:", value=dados_cli_atual[3])
    else:
        cliente_nome = st.text_input("Nome Completo do Cliente:", value="Condomínio Residencial Bella Vista")
        cliente_endereco = st.text_input("Endereço da Obra:", value="Av. das Palmeiras, nº 450")
        cliente_cidade = st.text_input("Cidade / UF:", value="Belo Horizonte / MG")
        if st.button("💾 Gravar Novo Cliente"):
            if cliente_nome and cliente_endereco:
                inserir_cliente_db(cliente_nome, cliente_endereco, cliente_cidade)
                st.success("Cliente gravado com sucesso!")
                st.rerun()

CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"}
}
with col_c2:
    st.write("### 🔌 Escolha da Concessionária de Distribuição")
    concessionaria_sel = st.selectbox("🔌 Escolha a Distribuidora de Energia Elétrica:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica", "🚰 Hidráulica", "🔥 Gás Encanado", "🌐 Internet/Dados", "🛡️ Segurança", "📂 Ver Catálogo", "📥 Relatório PDF"])
with tab_civil:
    st.write("### 🧱 Configuração do Método de Levantamento Estrutural e Prancha de Cômodos")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: nome_c = st.text_input("Nome do Cômodo (Ex: Cozinha, Suíte 1):")
    with cc2: comp_c = st.number_input("Comprimento do Cômodo (m):", value=4.0, min_value=0.5)
    with cc3: larg_c = st.number_input("Largura do Cômodo (m):", value=3.5, min_value=0.5)
    if st.button("➕ Encaixar Cômodo na Prancha de Ambientes"):
        if nome_c:
            st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
            salvar_dados_permanentes("comodos", st.session_state.comodos)
            st.success(f"Ambiente '{nome_c}' cadastrado com sucesso!")
            st.rerun()

    if st.session_state.comodos:
        st.write("📋 **Prancha de Ambientes Cadastrados:**")
        st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)

    st.markdown("---")
    area_obra = st.number_input("Área Construída Total da Obra para Cálculo Lote (m²):", min_value=10.0, value=70.0, step=5.0)
    perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0)
    if st.button("📊 Processar Cubagem Global de Insumos Civis"):
        st.session_state.lista_materials_civil = [
            {"Etapa": "01. Locação da Obra", "Material": "Tábua de Pinus 30cm x 3m (Gabarito)", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
            {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa (Sapatas)", "Quantidade": 4.8, "Unidade": "m³"},
            {"Etapa": "03. Estrutura e Piso", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"},
            {"Etapa": "04. Alvenaria", "Material": "Tijolo Cerâmico Baiano 8 Furos", "Quantidade": float(math.ceil(perimetro_paredes * 2.8 * 25 * 1.1)), "Unidade": "un"},
            {"Etapa": "05. Acabamentos", "Material": "Piso Porcelanato Retificado Comercial", "Quantidade": float(round(area_obra * 1.1, 1)), "Unidade": "m²"}
        ]
        atualizar_lote_materiais_fase("Civil", st.session_state.lista_materials_civil)
        st.rerun()

    if st.session_state.lista_materials_civil:
        edited_civil = st.data_editor(pd.DataFrame(st.session_state.lista_materials_civil), num_rows="dynamic", use_container_width=True, key="editor_civil")
        if st.button("💾 Salvar Alterações da Fase Civil"):
            st.session_state.lista_materials_civil = edited_civil.to_dict(orient="records")
            atualizar_lote_materiais_fase("Civil", st.session_state.lista_materials_civil)
            st.success("Fase civil salva e sincronizada fisicamente no banco!")
            st.rerun()
with tab_eletrica:
    st.write("### ⚡ Dimensionamento Elétrico NBR 5410")
    modo_eletrico = st.radio("Escolha o Modo de Escopo Elétrico:", ["Lançar o cálculo dinâmico da casa toda (Planta Otimizada)", "Lançar circuitos separados (Cálculo Individual Avançado)"], horizontal=True)

    lista_comodos_opcoes = [c["Cômodo"] for c in st.session_state.comodos] if st.session_state.comodos else ["Geral"]

    if modo_eletrico == "Lançar o cálculo dinâmico da casa toda (Planta Otimizada)":
        if st.button("🚀 Processar e Dimensionar Casa Toda Automaticamente"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO - Área Geral", "COMODO": "Geral", "POT_W": 1200, "TIPO": "Monofásico", "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "TUG - Tomadas Uso Geral", "COMODO": "Geral", "POT_W": 2400, "TIPO": "Monofásico", "COMP": 12},
                {"CIRC": "3", "DESCRIÇÃO": "TUE - Chuveiro Master", "COMODO": "Banheiro", "POT_W": 7500, "TIPO": "Bifásico", "COMP": 22}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                tensao_item = dados_c["linha"] if item["TIPO"] == "Bifásico" else dados_c["fase"]
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(item["POT_W"], tensao_item, item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "COMODO": item["COMODO"], "POT_W": int(item["POT_W"]), "TIPO": item["TIPO"],
                    "DISJ": f"{dj}A", "CURVA": curva, "COND": f"{b} mm²", "FASE": "RS" if item["TIPO"]=="Bifásico" else "R",
                    "TENSÃO": int(tensao_item), "IB": float(ib_c), "COMP": int(item["COMP"])
                })
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.success("Planta completa dimensionada por lote!")
            st.rerun()
    else:
        with st.form("form_novo_circuito_separado"):
            st.write("#### ➕ Lançar Circuito Individual Customizado")
            manual_nome = st.text_input("Nome/Descrição do Circuito:", value="Tomadas de Uso Geral")
            c_comodo = st.selectbox("A qual Cômodo cadastrado pertence?", lista_comodos_opcoes)
            c_desc = st.selectbox("Tipo de Carga / Serviço:", ["Iluminação", "TUG - Tomadas Uso Geral", "TUE - Tomadas Uso Especial"])
            
            if "Tomadas" in c_desc or "TUG" in c_desc:
                qtd_tomadas = st.number_input("Quantas tomadas serão ligadas neste circuito?", min_value=1, value=4, step=1)
                manual_pot = qtd_tomadas * 600 if "Geral" in c_desc else 4400
            else:
                qtd_tomadas = 0
                manual_pot = st.number_input("Potência Total da Iluminação (W):", value=1200, step=100)
                
            manual_comp = st.number_input("Metragem Linear de Cabo até o QDC (m):", value=15, min_value=1)
            tipo_rede = st.selectbox("Tipo de Fornecimento do Circuito:", ["Monofásico", "Bifásico"])
            
            if st.form_submit_button("🔌 Processar Cálculo Automático e Inserir"):
                c_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
                tensao_c = dados_c["linha"] if tipo_rede == "Bifásico" else dados_c["fase"]
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(manual_pot, tensao_c, manual_comp, c_desc)
                
                desc_final = f"{manual_nome} ({qtd_tomadas}t)" if qtd_tomadas > 0 else manual_nome
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": c_idx, "DESCRIÇÃO": desc_final, "COMODO": c_comodo, "POT_W": int(manual_pot), "TIPO": tipo_rede,
                    "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "RS" if tipo_rede == "Bifásico" else "R",
                    "TENSÃO": int(tensao_c), "IB": float(ib_c), "COMP": int(manual_comp)
                })
                salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                st.success("Circuito adicionado e salvo permanentemente!")
                st.rerun()

    if st.session_state.lista_circuitos_calc:
        edited_eletrica = st.data_editor(pd.DataFrame(st.session_state.lista_circuitos_calc), num_rows="dynamic", use_container_width=True, key="editor_eletrica")
        if st.button("💾 Salvar Alterações da Fase Elétrica"):
            st.session_state.lista_circuitos_calc = edited_eletrica.to_dict(orient="records")
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.success("QDC atualizado com sucesso!")
            st.rerun()
with tab_hidraulica:
    st.write("### 🚰 Redes Hidráulicas e Esgoto")
    n_banheiros = st.number_input("Quantidade de Banheiros Totais:", min_value=1, value=2)
    m_tubo_agua = st.number_input("Tubulação Água Fria 25mm (m):", min_value=6, value=30)
    m_tubo_esgoto = st.number_input("Tubulação Esgoto 100mm (m):", min_value=6, value=24)
    if st.button("📊 Processar Hidráulica Automática"):
        st.session_state.lista_materials_hidraulicos = [
            {"Etapa": "01. Reservatório", "Material": "Caixa d'Água Polietileno 1000L", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "02. Água Fria", "Material": "Tubo PVC Soldável Marrom 25mm (6m)", "Quantidade": float(math.ceil(m_tubo_agua / 6.0)), "Unidade": "barra"},
            {"Etapa": "03. Esgoto", "Material": "Tubo Esgoto PVC Branco 100mm (6m)", "Quantidade": float(math.ceil(m_tubo_esgoto / 6.0)), "Unidade": "barra"}
        ]
        atualizar_lote_materiais_fase("Hidráulica", st.session_state.lista_materials_hidraulicos)
        st.rerun()
    if st.session_state.lista_materials_hidraulicos:
        edited_hidr = st.data_editor(pd.DataFrame(st.session_state.lista_materials_hidraulicos), num_rows="dynamic", use_container_width=True, key="editor_hidr")
        if st.button("💾 Salvar Alterações Hidráulicas"):
            st.session_state.lista_materials_hidraulicos = edited_hidr.to_dict(orient="records")
            atualizar_lote_materiais_fase("Hidráulica", st.session_state.lista_materials_hidraulicos)
            st.rerun()

with tab_gas:
    st.write("### 🔥 Redes de Gás Encanado")
    m_cobre = st.number_input("Metragem de Rede de Cobre (m):", min_value=2, value=12)
    if st.button("📊 Processar Gás Automático"):
        st.session_state.lista_materials_gas = [
            {"Etapa": "01. Tubulação", "Material": "Tubo de Cobre Sem Costura 15mm", "Quantidade": float(math.ceil(m_cobre)), "Unidade": "m"},
            {"Etapa": "02. Regulagem", "Material": "Regulador de Pressão Gás GLP 7kg/h", "Quantidade": 1.0, "Unidade": "un"}
        ]
        atualizar_lote_materiais_fase("Gás Encanado", st.session_state.lista_materials_gas)
        st.rerun()
    if st.session_state.lista_materials_gas:
        edited_gas = st.data_editor(pd.DataFrame(st.session_state.lista_materials_gas), num_rows="dynamic", use_container_width=True, key="editor_gas")
        if st.button("💾 Salvar Alterações de Gás"):
            st.session_state.lista_materials_gas = edited_gas.to_dict(orient="records")
            atualizar_lote_materiais_fase("Gás Encanado", st.session_state.lista_materials_gas)
            st.rerun()

with tab_dados:
    st.write("### 🌐 Redes de Dados e Internet")
    m_cat6 = st.number_input("Metragem de Cabo LAN Cat6 (m):", min_value=20, value=150)
    if st.button("📊 Processar Telecom"):
        st.session_state.lista_materials_dados = [
            {"Etapa": "01. Cabeamento", "Material": "Cabo de Rede UTP Cat6 Puro Cobre", "Quantidade": float(m_cat6), "Unidade": "m"}
        ]
        atualizar_lote_materiais_fase("Internet/Dados", st.session_state.lista_materials_dados)
        st.rerun()
    if st.session_state.lista_materials_dados:
        edited_dados = st.data_editor(pd.DataFrame(st.session_state.lista_materials_dados), num_rows="dynamic", use_container_width=True, key="editor_dados")
        if st.button("💾 Salvar Alterações de Internet"):
            st.session_state.lista_materials_dados = edited_dados.to_dict(orient="records")
            atualizar_lote_materiais_fase("Internet/Dados", st.session_state.lista_materials_dados)
            st.rerun()

with tab_seguranca:
    st.write("### 🛡️ Sistemas de Segurança CFTV")
    n_cameras = st.number_input("Quantidade de Câmeras IP:", min_value=0, value=4)
    if st.button("📊 Processar Segurança"):
        st.session_state.lista_materials_seguranca = [
            {"Etapa": "Segurança Eletrônica", "Material": "Câmera CFTV IP Bullet 2MP", "Quantidade": float(n_cameras), "Unidade": "un"}
        ]
        atualizar_lote_materiais_fase("Segurança", st.session_state.lista_materials_seguranca)
        st.rerun()
    if st.session_state.lista_materials_seguranca:
        edited_seg = st.data_editor(pd.DataFrame(st.session_state.lista_materials_seguranca), num_rows="dynamic", use_container_width=True, key="editor_seg")
        if st.button("💾 Salvar Alterações de Segurança"):
            st.session_state.lista_materials_seguranca = edited_seg.to_dict(orient="records")
            atualizar_lote_materiais_fase("Segurança", st.session_state.lista_materials_seguranca)
            st.rerun()

# DEMANDA ATENDIDA: Aba Ver Catálogo agora possui a opção de cadastro e gravação física imediata no SQLite
with tab_catalogo:
    st.write("### 📦 Cadastrar Novo Produto no Catálogo")
    with st.form("form_catalogo_direto", clear_on_submit=True):
        mat_fase = st.selectbox("Fase / Segmento do Material:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança"])
        mat_etapa = st.text_input("Etapa de Aplicação (Ex: Fundações, Infraestrutura):")
        mat_nome = st.text_input("Descrição do Material Técnico:")
        mat_qtd = st.number_input("Quantidade:", min_value=0.0, value=1.0, step=1.0)
        mat_uni = st.selectbox("Unidade de Medida:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
        if st.form_submit_button("💾 Salvar Insumo no Banco de Dados"):
            if mat_nome and mat_etapa:
                inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_qtd, mat_uni)
                st.success("Produto cadastrado com sucesso no banco de dados físico SQLite!")
                st.rerun()
                
    st.markdown("---")
    st.write("### 📂 Catálogo de Insumos Salvos")
    dados_catalogo = listar_materiais_catalogo()
    if dados_catalogo:
        df_cat = pd.DataFrame(dados_catalogo, columns=["ID", "Segmento", "Etapa", "Material", "Quantidade", "Unidade"])
        st.data_editor(df_cat, use_container_width=True, disabled=["ID"])
    else:
        st.info("Nenhum material cadastrado de forma personalizada ainda.")
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=9.5, textColor=colors.HexColor('#0D9488'), spaceBefore=6, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_celula = ParagraphStyle('Cel', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelEsq', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=0)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO DE QUANTITATIVOS</b>", estilo_titulo), Spacer(1, 4)]
    
    c_nome_txt = cliente_nome if 'cliente_nome' in locals() and cliente_nome else "Não Homologado"
    c_end_txt = cliente_endereco if 'cliente_endereco' in locals() and cliente_endereco else "Não Cadastrado"
    c_cid_txt = cliente_cidade if 'cliente_cidade' in locals() and cliente_cidade else "Geral"
    
    dados_cliente_tabela = [[Paragraph(f"<b>CLIENTE:</b> {c_nome_txt}", estilo_celula_esq), Paragraph(f"<b>OBRA:</b> {c_end_txt}", estilo_celula_esq), Paragraph(f"<b>LOCALIDADE:</b> {c_cid_txt}", estilo_celula_esq)]]
    t_cli = Table(dados_cliente_tabela, colWidths=[240.0, 260.0, 240.0])
    t_cli.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 4)]))
    elementos.append(t_cli)
    
    pot_total_sistema = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc) if st.session_state.lista_circuitos_calc else 5000
    if pot_total_sistema <= dados_c["limite_mono"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Monofásico", "10.0 mm²", "40 A", dados_c["caixa_mono"]
    elif pot_total_sistema <= dados_c["limite_bi"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Bifásico", "16.0 mm²", "63 A", dados_c["caixa_bi"]
    else: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Trifásico", "25.0 mm²", "80 A", dados_c["caixa_tri"]

    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado ({concessionaria_sel})</b>", estilo_sub))
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro Normativo</b>", estilo_celula), Paragraph("<b>Especificação Técnica Regulamentar</b>", estilo_celula_esq)],
        [Paragraph("Norma Técnica Base da Distribuidora", estilo_celula), Paragraph(dados_c["norma"], estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento / Entrada Regulamentar", estilo_celula), Paragraph(f"{tipo_entrada} - ({detalhe_caixa})", estilo_celula_esq)],
        [Paragraph("Cabo do Ramal Geral (Cobre)", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral de Proteção da Caixa", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[240.0, 500.0])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)

    if st.session_state.lista_circuitos_calc:
        elementos.append(PageBreak())
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas com Vínculo Relacional de Cômodos", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO TERMINAL", "CÔMODO ALOCADO", "POT (W)", "DIST (M)", "CORRENTE (A)", "DISJ", "BITOLA", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        tot_r, tot_s = 0, 0
        for c in st.session_state.lista_circuitos_calc:
            p_w_val = int(c["POT_W"])
            r_val = p_w_val if c["FASE"] == "R" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            s_val = p_w_val if c["FASE"] == "S" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            tot_r += r_val; tot_s += s_val
            dados_qdc_pdf.append([Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq), Paragraph(str(c.get("COMODO","Geral")), estilo_celula), Paragraph(str(p_w_val), estilo_celula), Paragraph(f"{c['COMP']}m", estilo_celula), Paragraph(f"{c['IB']}A", estilo_celula), Paragraph(f"{c['CURVA']}{c['DISJ']}", estilo_celula), Paragraph(str(c["COND"]), estilo_celula), Paragraph(c["FASE"], estilo_celula), Paragraph(f"{c['TENSÃO']}V", estilo_celula), Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)])
        dados_qdc_pdf.append([Paragraph(f"<b>Potência Instalada Total: {pot_total_sistema} W | R: {tot_r}VA | S: {tot_s}VA</b>", estilo_celula)] + [""] * 11)
        t_qdc = Table(dados_qdc_pdf, colWidths=[30.0, 160.0, 80.0, 45.0, 45.0, 55.0, 40.0, 50.0, 35.0, 40.0, 50.0, 50.0])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('SPAN', (0,-1), (-1,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 3), ('ALIGN', (0,-1), (-1,-1), 'CENTER')]))
        elementos.append(t_qdc)

    listas_gerais_obra = [
        ("2. Memorial Quantitativo da Alvenaria e Cubagem Civil", st.session_state.lista_materials_civil, '#475569'),
        ("3. Lote Hidráulico e Redes de Esgoto Sanitário", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("4. Infraestrutura e Tubulações de Gás Encanado (GLP/GN)", st.session_state.lista_materials_gas, '#B45309'),
        ("5. Cabeamento Estruturado e Rede de Internet/Dados", st.session_state.lista_materials_dados, '#6D28D9'),
        ("6. Lote de Ativos e Segurança Eletrônica Monitorável", st.session_state.lista_materials_seguranca, '#0F172A')
    ]
    for tit, lista, cor_hex in listas_gerais_obra:
        if lista:
            elementos.append(PageBreak())
            elementos.append(Paragraph(tit, estilo_sub))
            tbl_d = [[Paragraph("<b>Etapa</b>", estilo_celula), Paragraph("<b>Insumo Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
            for mat in lista: tbl_d.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
            t_m = Table(tbl_d, colWidths=[130.0, 390.0, 140.0, 80.0])
            t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor(cor_hex)), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
            elementos.append(t_m)

    elementos.append(PageBreak())
    elementos.append(Paragraph("7. Diagrama Unifilar - Entrada Geral, Barramentos e Dispositivos de Proteção (DJ / DR / DPS)", estilo_sub))
    elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))
    elementos.append(PageBreak())
    elementos.append(Paragraph("8. Esquema Técnico Multifilar - Proteções de Cabeceira e Distribuição por Fase", estilo_sub))
    elementos.append(gerar_desenho_multifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Consolidado da Obra Completa (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_unificado.pdf", mime="application/pdf", key="btn_pdf_real")
