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
    st.session_state.funcionarios = carregar_dados_permanentes("funcionarios", [
        {"id": 1, "Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA_RE": "MG20231045", "Responsavel": True},
        {"id": 2, "Nome": "Marcos Souza", "Função": "Eletricista Instalador", "CREA_RE": "RE-9942", "Responsavel": False}
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
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:22]} - {c.get('COMODO','Geral')}", fontSize=7.5))
    return d
def gerar_desenho_multifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(260, (n_circ * 35) + 140)
    d = Drawing(720, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 220, 250, 280, 310
    
    d.add(Rect(180, altura_d - 45, 160, 35, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(185, altura_d - 22, "SISTEMA DE ENTRADA GERAL", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(185, altura_d - 32, f"DISJ. GERAL: {dj_pad} | CABO: {cabo_pad}", fontSize=6.5))
    d.add(String(185, altura_d - 42, "PROTEÇÃO ADICIONAL: DPS + IDR", fontSize=5.5, fillColor=colors.red))
    
    d.add(Line(200, altura_d - 45, x_fase1, altura_d - 65, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(240, altura_d - 45, x_fase2, altura_d - 65, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 45, x_neutro, altura_d - 65, strokeColor=colors.blue, strokeWidth=1.5))
    
    d.add(Line(x_fase1, altura_d - 65, x_fase1, 20, strokeColor=colors.red, strokeWidth=1.8))
    d.add(Line(x_fase2, altura_d - 65, x_fase2, 20, strokeColor=colors.black, strokeWidth=1.8))
    d.add(Line(x_neutro, altura_d - 65, x_neutro, 20, strokeColor=colors.blue, strokeWidth=1.8))
    d.add(Line(x_terra, altura_d - 20, x_terra, 20, strokeColor=colors.black, strokeWidth=1.5))
    
    d.add(String(x_fase1 - 5, altura_d - 62, "R", fontSize=7, fontName='Helvetica-Bold', fillColor=colors.red))
    d.add(String(x_fase2 - 5, altura_d - 62, "S", fontSize=7, fontName='Helvetica-Bold', fillColor=colors.black))
    d.add(String(x_neutro - 5, altura_d - 62, "N", fontSize=7, fontName='Helvetica-Bold', fillColor=colors.blue))
    d.add(String(x_terra - 5, altura_d - 15, "T", fontSize=7, fontName='Helvetica-Bold'))
    
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
with st.sidebar:
    st.markdown(
        """
        <div style="background-color:#1E3A8A; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <h2 style="color:#FFFFFF; margin:0; font-family:sans-serif; letter-spacing: 2px;">⚡ FÊNIX</h2>
            <p style="color:#0D9488; margin:0; font-size:11px; font-weight:bold; letter-spacing: 1px;">ENGENHARIA & SISTEMAS</p>
        </div>
        """, unsafe_allow_html=True
    )
    # RESTAURAÇÃO: Cadastro de Responsáveis Técnicos e Funcionários na lateral
    st.write("### 👥 Gestão de Responsáveis")
    with st.form("form_func", clear_on_submit=True):
        f_nome = st.text_input("Nome do Colaborador:")
        f_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista", "Encanador", "Técnico"])
        f_reg = st.text_input("Registro (CREA / RE):")
        f_resp = st.checkbox("Definir como Responsável?")
        if st.form_submit_button("Cadastrar Funcionário"):
            if f_nome and f_reg:
                ids_existentes = [f["id"] for f in st.session_state.funcionarios]
                novo_id = max(ids_existentes) + 1 if ids_existentes else 1
                st.session_state.funcionarios.append({"id": novo_id, "Nome": f_nome, "Função": f_func, "CREA_RE": f_reg, "Responsavel": f_resp})
                salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                st.success("Responsável Cadastrado!")
                st.rerun()

    if st.session_state.funcionarios:
        for idx, f in enumerate(list(st.session_state.funcionarios)):
            col_f1, col_f2 = st.columns([4, 1])
            with col_f1: st.caption(f"**{f['Nome']}** ({f['Função']})")
            with col_f2:
                if st.button("❌", key=f"del_f_{f['id']}_{idx}"):
                    st.session_state.funcionarios.pop(idx)
                    salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                    st.rerun()

    st.markdown("---")
    # RESTAURAÇÃO: Cadastro rápido de novos materiais na lateral
    st.write("### 📦 Cadastro Rápido de Materiais")
    with st.form("form_catalogo_mat", clear_on_submit=True):
        mat_fase = st.selectbox("Segmento Alvo:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança", "Energia Solar"])
        mat_etapa = st.text_input("Etapa de Aplicação:")
        mat_nome = st.text_input("Descrição Técnica do Material:")
        mat_qtd = st.number_input("Quantidade Inicial:", value=1.0, min_value=0.1)
        mat_uni = st.selectbox("Unidade:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
        if st.form_submit_button("💾 Salvar no Catálogo"):
            if mat_nome and mat_etapa:
                inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_qtd, mat_uni)
                st.success("Salvo!")
                st.rerun()
# RESTAURAÇÃO: Painel de Clientes e Dicionário de TODAS as Concessionárias do Brasil
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

# RESTAURAÇÃO COMPLETA DE TODAS AS CONCESSIONÁRIAS DE ENERGIA DO BRASIL
CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
    "ENEL RJ (RJ) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "CPFL Paulista (SP) - GED-13": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13", "caixa_mono": "Caixa Tipo II", "caixa_bi": "Caixa Tipo III", "caixa_tri": "Caixa Tipo IV"},
    "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Tipo Mono", "caixa_bi": "Caixa Tipo Bi", "caixa_tri": "Caixa Tipo Tri"},
    "CELESC (SC) - N-321": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"},
    "CEAL (AL) / CEPISA (PI)": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-EQ-01", "caixa_mono": "Caixa Tipo Padrão", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"}
}
with col_c2:
    st.write("### 🔌 Distribuição Regulamentar")
    concessionaria_sel = st.selectbox("Distribuidora Regulamentar do Brasil:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_solar, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica", "🚰 Hidráulica", "🔥 Gás", "🌐 Internet", "🛡️ Segurança", "☀️ Energia Solar", "📂 Catálogo", "📥 PDF"])
with tab_civil:
    st.write("### 🧱 Configuração Estrutural e Prancha de Cômodos")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: nome_c = st.text_input("Nome do Cômodo:")
    with cc2: comp_c = st.number_input("Comprimento (m):", value=4.0)
    with cc3: larg_c = st.number_input("Largura (m):", value=3.5)
    if st.button("➕ Cadastrar Cômodo na Planta"):
        st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
        salvar_dados_permanentes("comodos", st.session_state.comodos)
        st.rerun()
    if st.session_state.comodos: st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)

    st.markdown("---")
    area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0)
    perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0)
    if st.button("📊 Processar Cubagem Global de Insumos Civis"):
        st.session_state.lista_materials_civil = [
            {"Etapa": "01. Locação da Obra", "Material": "Tábua de Pinus 30cm x 3m (Gabarito)", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
            {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa (Sapatas)", "Quantidade": 4.8, "Unidade": "m³"},
            {"Etapa": "03. Estrutura e Piso", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"},
            {"Etapa": "04. Alvenaria", "Material": "Tijolo Cerâmico Baiano 8 Furos", "Quantidade": float(math.ceil(perimetro_paredes * 2.8 * 25 * 1.1)), "Unidade": "un"},
            {"Etapa": "05. Acabamentos", "Material": "Piso Porcelanato Retificado Comercial", "Quantidade": float(round(area_obra * 1.1, 1)), "Unidade": "m²"}
        ]
        st.rerun()
    if st.session_state.lista_materials_civil: st.dataframe(pd.DataFrame(st.session_state.lista_materials_civil), use_container_width=True)

with tab_eletrica:
    st.write("### ⚡ Escopo e Lançamento Elétrico NBR 5410")
    modo_eletrico = st.radio("Método de Lançamento:", ["Lote Automático (Casa Toda)", "Lançar Circuito Customizado Separado"], horizontal=True)
    lista_comodos_opcoes = [c["Cômodo"] for c in st.session_state.comodos] if st.session_state.comodos else ["Geral"]
    
    if modo_eletrico == "Lote Automático (Casa Toda)":
        if st.button("🚀 Dimensionar Casa Toda"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO", "COMODO": "Geral", "POT_W": 1200, "TIPO": "Monofásico", "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "TOMADAS TUG", "COMODO": "Geral", "POT_W": 2400, "TIPO": "Monofásico", "COMP": 12},
                {"CIRC": "3", "DESCRIÇÃO": "TUE - Chuveiro Master", "COMODO": "Banheiro", "POT_W": 7500, "TIPO": "Bifásico", "COMP": 22}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                tensao_item = dados_c["linha"] if item["TIPO"] == "Bifásico" else dados_c["fase"]
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(item["POT_W"], tensao_item, item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({"CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "COMODO": item["COMODO"], "POT_W": int(item["POT_W"]), "TIPO": item["TIPO"], "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "RS" if item["TIPO"]=="Bifásico" else "R", "TENSÃO": int(tensao_item), "IB": float(ib_c), "COMP": int(item["COMP"])})
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.rerun()
    else:
        with st.form("form_c_sep"):
            m_name = st.text_input("Nome do Circuito:", value="Tomadas Cozinha")
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
    st.write("### 🚰 Rede Hidráulica e Esgoto Sanitário")
    m_agua = st.number_input("Metragem Tubo PVC Água Fria 25mm (m):", value=30)
    if st.button("Calcular Hidráulica"):
        st.session_state.lista_materials_hidraulicos = [
            {"Etapa": "01. Reservatório", "Material": "Caixa d'Água Polietileno 1000L Fortlev", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "02. Água Fria", "Material": "Tubo PVC Marrom 25mm (6m)", "Quantidade": float(math.ceil(m_agua/6)), "Unidade": "barra"}
        ]
        st.rerun()
    if st.session_state.lista_materials_hidraulicos: st.dataframe(pd.DataFrame(st.session_state.lista_materials_hidraulicos), use_container_width=True)

with tab_gas:
    st.write("### 🔥 Rede de Gás Encanado")
    m_gas = st.number_input("Metragem Tubo Cobre 15mm (m):", value=12)
    if st.button("Calcular Gás"):
        st.session_state.lista_materials_gas = [{"Etapa": "01. Tubulação", "Material": "Tubo de Cobre 15mm Classe A", "Quantidade": float(m_gas), "Unidade": "m"}]
        st.rerun()
    if st.session_state.lista_materials_gas: st.dataframe(pd.DataFrame(st.session_state.lista_materials_gas), use_container_width=True)

with tab_dados:
    st.write("### 🌐 Infraestrutura de Redes e Internet")
    m_lan = st.number_input("Metragem Cabo LAN Cat6 Puro Cobre (m):", value=100)
    if st.button("Calcular Internet"):
        st.session_state.lista_materials_dados = [{"Etapa": "01. Cabeamento", "Material": "Cabo LAN UTP Cat6 LSZH", "Quantidade": float(m_lan), "Unidade": "m"}]
        st.rerun()
    if st.session_state.lista_materials_dados: st.dataframe(pd.DataFrame(st.session_state.lista_materials_dados), use_container_width=True)

with tab_seguranca:
    st.write("### 🛡️ Sistemas de Segurança CFTV Monitorável")
    m_cam = st.number_input("Quantidade Câmeras IP IP67 Bullet:", value=4)
    if st.button("Calcular Segurança"):
        st.session_state.lista_materials_seguranca = [{"Etapa": "01. CFTV", "Material": "Câmeras IP HD Bullet 2MP", "Quantidade": float(m_cam), "Unidade": "un"}]
        st.rerun()
    if st.session_state.lista_materials_seguranca: st.dataframe(pd.DataFrame(st.session_state.lista_materials_seguranca), use_container_width=True)

with tab_solar:
    st.write("### ☀️ Dimensionamento Fotovoltaico (NBR 16690)")
    pot_solar_kwp = st.number_input("Potência do Sistema Fotovoltaico Demandada (kWp):", min_value=1.0, value=5.5)
    if st.button("📊 Processar Engenharia Solar"):
        num_paineis = math.ceil((pot_solar_kwp * 1000) / 550)
        st.session_state.lista_materials_solar = [
            {"Etapa": "01. Geração", "Material": "Painel Solar Monocristalino 550Wp Plus", "Quantidade": float(num_paineis), "Unidade": "un"},
            {"Etapa": "02. Inversão", "Material": f"Inversor Solar On-Grid String {math.ceil(pot_solar_kwp)}kW", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "03. Proteção", "Material": "String Box CC 1000V Proteções Completas", "Quantidade": 1.0, "Unidade": "un"}
        ]
        st.rerun()
    if st.session_state.lista_materials_solar: st.dataframe(pd.DataFrame(st.session_state.lista_materials_solar), use_container_width=True)

with tab_catalogo:
    st.write("### 📂 Visualização de Catálogo Customizado SQLite")
    cat_df = listar_materiais_catalogo()
    if cat_df: st.dataframe(pd.DataFrame(cat_df, columns=["ID", "Segmento", "Etapa", "Material", "Quantidade", "Unidade"]), use_container_width=True)
    else: st.info("Use a barra lateral esquerda para cadastrar novos produtos no catálogo.")
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=9.5, textColor=colors.HexColor('#0D9488'), spaceBefore=6, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_celula = ParagraphStyle('Cel', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelEsq', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=0)
    estilo_aviso_tit = ParagraphStyle('AT', parent=estilos['Heading3'], fontSize=11, textColor=colors.HexColor('#991B1B'), fontName='Helvetica-Bold', spaceAfter=4)
    estilo_aviso_corpo = ParagraphStyle('AC', parent=estilos['BodyText'], fontSize=10, leading=13, alignment=4, spaceAfter=3)
    
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
        ("2. Memorial Quantitativo da Fase Civil", st.session_state.lista_materials_civil, '#475569'),
        ("3. Lote Hidráulico e Redes de Esgoto Sanitário", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("4. Infraestrutura e Tubulações de Gás Encanado", st.session_state.lista_materials_gas, '#B45309'),
        ("5. Cabeamento Estruturado e Rede de Internet", st.session_state.lista_materials_dados, '#6D28D9'),
        ("6. Ativos de Segurança Eletrônica Monitorável", st.session_state.lista_materials_seguranca, '#0F172A'),
        ("7. Engenharia Solar Fotovoltaica (NBR 16690)", st.session_state.lista_materials_solar, '#F59E0B')
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
    elementos.append(Paragraph("8. Diagrama Unifilar - Entrada Geral, Barramentos e Dispositivos de Proteção (DJ / DR / DPS)", estilo_sub))
    elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))
    elementos.append(PageBreak())
    elementos.append(Paragraph("9. Esquema Técnico Multifilar - Proteções de Cabeceira e Distribuição por Fase", estilo_sub))
    elementos.append(gerar_desenho_multifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))

    # RESTAURAÇÃO: Notas Técnicas e Observações Importantes de Campo Completas NBR 5410 & NR-10
    elementos.append(PageBreak())
    elementos.append(Paragraph("10. Diretrizes Técnicas e Normativas de Campo", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Spacer(1, 4),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴 FASES: Condutores Ativos.", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente para garantir a integridade contra choques elétricos.", estilo_aviso_corpo),
        Paragraph("• <b>Inspeção do DPS:</b> Verifique o indicador visual do protetor de surto regularmente. Janela vermelha exige substituição imediata.", estilo_aviso_corpo),
        Paragraph("• <b>Seção vs. Disjuntor:</b> Nunca aumente a amperagem de um disjuntor sem recalcular a fiação para evitar riscos de incêndio por sobrecarga.", estilo_aviso_corpo)
    ]
    t_av = Table([[caviso]], colWidths=[740.0])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#D97706')), ('PADDING', (0,0), (-1,-1), 10)]))
    elementos.append(t_av)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Unificado (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_unificado.pdf", mime="application/pdf", key="btn_pdf_real")
