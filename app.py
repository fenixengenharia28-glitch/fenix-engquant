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

# --- ENGINE DO BANCO DE DADOS PERSISTENTE LOCAL (CORREÇÃO DE ESTRUTURA OPERACIONAL) ---
def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    # Remove as versões antigas conflitantes e incompatíveis da tabela
    cursor.execute("DROP TABLE IF EXISTS materiais_catalogo")
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
        cursor.execute("INSERT OR REPLACE INTO configuracoes (id, dados) VALUES (?, ?)", (chave, json.dumps(valor)))
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
        if row and row: return json.loads(row[0])
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

if "db_sync_completo" not in st.session_state:
    st.session_state.lista_materials_civil = []
    st.session_state.lista_materials_eletricos = []
    st.session_state.lista_materials_hidraulicos = []
    st.session_state.lista_materials_gas = []
    st.session_state.lista_materials_dados = []
    st.session_state.lista_materials_seguranca = []
    st.session_state.lista_materials_solar = []
    st.session_state.funcionarios = carregar_dados_permanentes("funcionarios", [{"id": 1, "Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA_RE": "MG20231045", "Responsavel": True}])
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
    st.session_state.comodos = carregar_dados_permanentes("comodos", [])
    st.session_state.seguranca_insumos = carregar_dados_permanentes("seguranca", {"cameras": 4, "sensores": 3, "cabo_m": 100})
    st.session_state.db_sync_completo = True
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
    d.add(Line(250, altura_d - 40, 280, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 40, 280, 20, strokeColor=colors.black, strokeWidth=2))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 80) - (idx * 30)
        d.add(Circle(280, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(280, y, 320, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(320, y, 335, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(315, y + 5, f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(335, y, 365, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(340, y + 4, str(c.get('COND','2.5 mm²')), fontSize=6.5, fillColor=colors.HexColor('#2563EB'), fontName='Helvetica-Bold'))
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:22]} - {c.get('COMODO','Geral')}", fontSize=7.5))
    return d
def gerar_desenho_multifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(260, (n_circ * 35) + 140)
    d = Drawing(720, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 220, 250, 280, 310
    d.add(Rect(180, altura_d - 45, 160, 35, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(185, altura_d - 22, "SISTEMA DE ENTRADA GERAL", fontSize=7, fontName='Helvetica-Bold'))
    d.add(Line(200, altura_d - 45, x_fase1, altura_d - 65, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(240, altura_d - 45, x_fase2, altura_d - 65, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 45, x_neutro, altura_d - 65, strokeColor=colors.blue, strokeWidth=1.5))
    d.add(Line(x_fase1, altura_d - 65, x_fase1, 20, strokeColor=colors.red, strokeWidth=1.8))
    d.add(Line(x_fase2, altura_d - 65, x_fase2, 20, strokeColor=colors.black, strokeWidth=1.8))
    d.add(Line(x_neutro, altura_d - 65, x_neutro, 20, strokeColor=colors.blue, strokeWidth=1.8))
    d.add(Line(x_terra, altura_d - 20, x_terra, 20, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 100) - (idx * 35)
        if idx % 2 == 0:
            d.add(Rect(20, y - 10, 140, 24, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1))
            d.add(String(25, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:15]}", fontSize=6.5, fontName='Helvetica-Bold'))
            d.add(Circle(x_fase1, y, 2, fillColor=colors.red, strokeColor=colors.red))
            d.add(Line(160, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
        else:
            d.add(Rect(350, y - 10, 140, 24, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(355, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:15]}", fontSize=6.5, fontName='Helvetica-Bold'))
            d.add(Circle(x_neutro, y, 2, fillColor=colors.blue, strokeColor=colors.blue))
            d.add(Line(350, y, x_neutro, y, strokeColor=colors.blue, strokeWidth=0.8))
    return d
col_c1, col_c2 = st.columns(2)
with col_c1:
    st.write("### 👤 Central de Clientes (Gravar e Selecionar)")
    lista_clientes = listar_clientes_db()
    opcoes_clientes = ["-- Cadastrar Novo Cliente --"] + [f"ID {c[0]} - {c[1]}" for c in lista_clientes]
    cliente_selecionado = st.selectbox("📂 Escolher Cliente Salvo:", opcoes_clientes)
    cliente_nome = st.text_input("Nome Completo do Cliente:", value="Condomínio Residencial Bella Vista")
    cliente_endereco = st.text_input("Endereço da Obra:", value="Av. das Palmeiras, nº 450")
    cliente_cidade = st.text_input("Cidade / UF:", value="Belo Horizonte / MG")
    if st.button("💾 Gravar Novo Cliente"):
        if cliente_nome and cliente_endereco:
            inserir_cliente_db(cliente_nome, cliente_endereco, cliente_cidade)
            st.success("Cliente gravado!")
            st.rerun()

CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"}
}
with col_c2:
    st.write("### 🔌 Distribuição e Concessionária")
    concessionaria_sel = st.selectbox("Distribuidora Alvo:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_solar, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica", "🚰 Hidráulica", "🔥 Gás", "🌐 Internet", "🛡️ Segurança", "☀️ Energia Solar", "📂 Catálogo", "📥 PDF"])
with tab_civil:
    st.write("### 🧱 Cadastro de Cômodos")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: nome_c = st.text_input("Nome do Cômodo:")
    with cc2: comp_c = st.number_input("Comprimento (m):", value=4.0)
    with cc3: larg_c = st.number_input("Largura (m):", value=3.5)
    if st.button("➕ Cadastrar Cômodo"):
        st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
        salvar_dados_permanentes("comodos", st.session_state.comodos)
        st.rerun()
    if st.session_state.comodos: st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)

with tab_eletrica:
    st.write("### ⚡ Escopo e Lançamento Elétrico NBR 5410")
    modo_eletrico = st.radio("Método de Lançamento:", ["Lote Automático (Casa Toda)", "Lançar Circuito Customizado Separado"], horizontal=True)
    lista_comodos_opcoes = [c["Cômodo"] for c in st.session_state.comodos] if st.session_state.comodos else ["Geral"]
    
    if modo_eletrico == "Lote Automático (Casa Toda)":
        if st.button("🚀 Dimensionar Casa Toda"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO", "COMODO": "Geral", "POT_W": 1200, "TIPO": "Monofásico", "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "TOMADAS TUG", "COMODO": "Geral", "POT_W": 2400, "TIPO": "Monofásico", "COMP": 12}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(item["POT_W"], dados_c["fase"], item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({"CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "COMODO": item["COMODO"], "POT_W": int(item["POT_W"]), "TIPO": item["TIPO"], "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "R", "TENSÃO": int(dados_c["fase"]), "IB": float(ib_c), "COMP": int(item["COMP"])})
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.rerun()
    else:
        with st.form("form_c_sep"):
            m_name = st.text_input("Nome do Circuito:", value="Tomadas Suíte")
            m_com = st.selectbox("Cômodo Alvo:", lista_comodos_opcoes)
            m_pot = st.number_input("Potência Ativa (W):", value=2200)
            m_met = st.number_input("Metragem Linear até o QDC (m):", value=15)
            if st.form_submit_button("🔌 Calcular e Adicionar Circuito"):
                c_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(m_pot, dados_c["fase"], m_met, "TUG")
                st.session_state.lista_circuitos_calc.append({"CIRC": c_idx, "DESCRIÇÃO": m_name, "COMODO": m_com, "POT_W": int(m_pot), "TIPO": "Monofásico", "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "R", "TENSÃO": int(dados_c["fase"]), "IB": float(ib_c), "COMP": int(m_met)})
                salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                st.rerun()
    if st.session_state.lista_circuitos_calc: st.dataframe(pd.DataFrame(st.session_state.lista_circuitos_calc), use_container_width=True)
with tab_hidraulica:
    st.write("### 🚰 Rede Hidráulica")
    m_agua = st.number_input("Metragem Tubo PVC 25mm (m):", value=30)
    if st.button("Calcular Hidráulica"):
        st.session_state.lista_materials_hidraulicos = [{"Etapa": "01. Água Fria", "Material": "Tubo PVC Marrom 25mm", "Quantidade": float(math.ceil(m_agua/6)), "Unidade": "barra"}]

with tab_gas:
    st.write("### 🔥 Rede de Gás")
    m_gas = st.number_input("Metragem Tubo Cobre 15mm (m):", value=12)
    if st.button("Calcular Gás"):
        st.session_state.lista_materials_gas = [{"Etapa": "01. Tubulação", "Material": "Tubo de Cobre 15mm Classe A", "Quantidade": float(m_gas), "Unidade": "m"}]

with tab_dados:
    st.write("### 🌐 Redes de Internet")
    m_lan = st.number_input("Metragem Cabo LAN Cat6 (m):", value=100)
    if st.button("Calcular Internet"):
        st.session_state.lista_materials_dados = [{"Etapa": "01. Cabeamento", "Material": "Cabo LAN UTP Cat6", "Quantidade": float(m_lan), "Unidade": "m"}]

with tab_seguranca:
    st.write("### 🛡️ Segurança Eletrônica")
    m_cam = st.number_input("Quantidade Câmeras IP IP67:", value=4)
    if st.button("Calcular Segurança"):
        st.session_state.lista_materials_seguranca = [{"Etapa": "01. CFTV", "Material": "Câmeras IP HD Bullet", "Quantidade": float(m_cam), "Unidade": "un"}]

with tab_solar:
    st.write("### ☀️ Dimensionamento Fotovoltaico (NBR 16690)")
    pot_solar_kwp = st.number_input("Potência Total Demandada do Sistema (kWp):", min_value=1.0, value=5.5, step=0.5)
    tipo_telhado = st.selectbox("Tipo de Telhado:", ["Telha Cerâmica", "Telha Metálica", "Laje", "Solo"])
    if st.button("📊 Processar Engenharia Solar"):
        num_paineis = math.ceil((pot_solar_kwp * 1000) / 550)
        st.session_state.lista_materials_solar = [
            {"Etapa": "01. Geração", "Material": "Painel Solar Monocristalino 550Wp Plus", "Quantidade": float(num_paineis), "Unidade": "un"},
            {"Etapa": "02. Inversão", "Material": f"Inversor Solar On-Grid String {math.ceil(pot_solar_kwp)}kW", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "03. Proteção CC", "Material": "String Box CC 1000V Proteções Completas", "Quantidade": 1.0, "Unidade": "un"}
        ]
        st.success("Módulo fotovoltaico processado!")
        st.rerun()
    if st.session_state.lista_materials_solar: st.dataframe(pd.DataFrame(st.session_state.lista_materials_solar), use_container_width=True)

with tab_catalogo:
    st.write("### 📦 Cadastrar Insumo Personalizado")
    with st.form("form_cat_dir"):
        c_fase = st.selectbox("Segmento Alvo do Produto:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança", "Energia Solar"])
        c_etapa = st.text_input("Etapa de Aplicação (Ex: Infraestrutura, Acabamento):")
        c_mat = st.text_input("Descrição do Material Técnico:")
        c_qtd = st.number_input("Quantidade:", value=1.0, min_value=0.1)
        c_uni = st.selectbox("Unidade:", ["un", "m", "barra", "rl", "jg", "sc"])
        if st.form_submit_button("Salvar no SQLite"):
            inserir_material_catalogo(c_fase, c_etapa, c_mat, c_qtd, c_uni)
            st.success("Salvo com sucesso!")
            st.rerun()
            
    st.markdown("---")
    # CORREÇÃO DEFINITIVA DO OPERATIONALERROR: Lê a tabela limpa e sincronizada no SQLite
    cat_df = listar_materiais_catalogo()
    if cat_df:
        st.dataframe(pd.DataFrame(cat_df, columns=["ID", "Segmento", "Etapa", "Material", "Quantidade", "Unidade"]), use_container_width=True)
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=9.5, textColor=colors.HexColor('#0D9488'), spaceBefore=6, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_celula = ParagraphStyle('Cel', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelEsq', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=0)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO DE QUANTITATIVOS</b>", estilo_titulo), Spacer(1, 4)]
    
    dados_cliente_tabela = [[Paragraph(f"<b>CLIENTE:</b> {cliente_nome}", estilo_celula_esq), Paragraph(f"<b>OBRA:</b> {cliente_endereco}", estilo_celula_esq), Paragraph(f"<b>LOCALIDADE:</b> {cliente_cidade}", estilo_celula_esq)]]
    t_cli = Table(dados_cliente_tabela, colWidths=[240.0, 260.0, 240.0])
    t_cli.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 4)]))
    elementos.append(t_cli)
    
    pot_total_sistema = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc) if st.session_state.lista_circuitos_calc else 5000
    if pot_total_sistema <= dados_c["limite_mono"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Monofásico", "10.0 mm²", "40 A", dados_c["caixa_mono"]
    elif pot_total_sistema <= dados_c["limite_bi"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Bifásico", "16.0 mm²", "63 A", dados_c["caixa_bi"]
    else: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Trifásico", "25.0 mm²", "80 A", dados_c["caixa_tri"]

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
        for c in st.session_state.lista_circuitos_calc:
            p_w_val = int(c["POT_W"])
            r_val = p_w_val if c["FASE"] == "R" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            s_val = p_w_val if c["FASE"] == "S" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            dados_qdc_pdf.append([Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq), Paragraph(str(c.get("COMODO","Geral")), estilo_celula), Paragraph(str(p_w_val), estilo_celula), Paragraph(f"{c['COMP']}m", estilo_celula), Paragraph(f"{c['IB']}A", estilo_celula), Paragraph(f"{c['CURVA']}{c['DISJ']}", estilo_celula), Paragraph(str(c["COND"]), estilo_celula), Paragraph(c["FASE"], estilo_celula), Paragraph(f"{c['TENSÃO']}V", estilo_celula), Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)])
        t_qdc = Table(dados_qdc_pdf, colWidths=[30.0, 160.0, 80.0, 45.0, 45.0, 55.0, 40.0, 50.0, 35.0, 40.0, 50.0, 50.0])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_qdc)

    listas_gerais_obra = [
        ("2. Lote Hidráulico e Redes de Esgoto", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("3. Infraestrutura de Gás Encanado", st.session_state.lista_materials_gas, '#B45309'),
        ("4. Cabeamento de Internet e Telecom", st.session_state.lista_materials_dados, '#6D28D9'),
        ("5. Ativos de Segurança Eletrônica Monitorável", st.session_state.lista_materials_seguranca, '#0F172A'),
        ("6. Engenharia Solar Fotovoltaica (NBR 16690)", st.session_state.lista_materials_solar, '#F59E0B')
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
    st.download_button(label="📥 Baixar Memorial Técnico Unificado (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_unificado.pdf", mime="application/pdf", key="btn_pdf_real")
