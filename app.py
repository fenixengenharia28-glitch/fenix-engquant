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

# --- ENGINE DO BANCO DE DADOS PERSISTENTE LOCAL COM TODAS AS TABELAS CRUD ---
def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, quantidade REAL, unidade TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS equipe_tecnica (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, registro TEXT, responsavel INTEGER)")
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

def atualizar_material_db(id_material, fase, etapa, material, quantidade, unidade):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE materiais_catalogo SET fase=?, etapa=?, material=?, quantidade=?, unidade=? WHERE id=?", (fase, etapa, material, quantidade, unidade, id_material))
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

def atualizar_membro_equipe(id_membro, nome, funcao, registro, responsavel):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE equipe_tecnica SET nome=?, funcao=?, registro=?, responsavel=? WHERE id=?", (nome, funcao, registro, int(responsavel), id_membro))
    conn.commit()
    conn.close()
if "db_sync_completo" not in st.session_state:
    st.session_state.lista_materials_civil = []
    st.session_state.lista_materials_eletricos = []
    st.session_state.lista_materials_hidraulicos = []
    st.session_state.lista_materials_gas = []
    st.session_state.lista_materials_dados = []
    st.session_state.lista_materials_seguranca = []
    st.session_state.lista_materials_solar = []
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
    st.session_state.comodos = carregar_dados_permanentes("comodos", [])
    st.session_state.seguranca_insumos = carregar_dados_permanentes("seguranca", {"cameras": 4, "sensores": 3, "cabo_m": 100})
    st.session_state.db_sync_completo = True
def dimensionar_circuito_nbr5410_mda(potencia, tensao, comprimento, tipo_carga, fca=0.70, fct=1.0):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.80
    potencia_va = potencia / fp
    ib = potencia / (tensao * fp)
    ib_corrigida = ib / (fca * fct)
    
    bitola_inicial = 1.5 if "Iluminação" in tipo_carga else 2.5
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    
    bitola_final = bitola_inicial
    iz_cabo = 17.5 if "Iluminação" in tipo_carga else 24.0
    
    for b, cap in zip(bitolas_comerciais, capacidades_corrente):
        if b >= bitola_inicial and cap >= ib_corrigida:
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
        
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= (iz_cabo * fca * fct):
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
            
    return {
        "BITOLA": bitola_final, "DISJUNTORES": disjuntor_final, "CURVA": "B" if "Iluminação" in tipo_carga else "C",
        "IB": round(ib, 2), "IB_CORR": round(ib_corrigida, 2), "VA": round(potencia_va, 2), "FP": fp,
        "DV": round((2 * rho * comprimento * ib * 100) / (tensao * bitola_final), 2)
    }
def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(240, (n_circ * 30) + 130)
    d = Drawing(720, altura_d)
    d.add(Line(20, altura_d - 40, 90, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 32, f"Rede BT Ramal: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Rect(90, altura_d - 52, 45, 24, fillColor=colors.HexColor('#EFF6FF'), strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(95, altura_d - 44, "DJ Geral", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(95, altura_d - 51, f"{dj_pad}", fontSize=6.5, fontName='Helvetica'))
    d.add(Line(135, altura_d - 40, 160, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Rect(160, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(166, altura_d - 44, "DPS", fontSize=7, fontName='Helvetica-Bold'))
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
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:20]} - {c.get('COMODO','Geral')}", fontSize=7.5))
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
with st.sidebar:
    st.markdown("<h2 style='color:#FFFFFF; background-color:#1E3A8A; padding:10px; border-radius:5px; text-align:center;'>⚙️ CENTRAL FÊNIX</h2>", unsafe_allow_html=True)
    
    st.write("### 👤 Gestão de Clientes")
    lista_cli = listar_clientes_db()
    if lista_cli:
        df_cli_view = pd.DataFrame(lista_cli, columns=["ID", "Nome", "Endereço", "Cidade/UF"])
        st.dataframe(df_cli_view, use_container_width=True, hide_index=True)
        id_cli_del = st.number_input("ID do Cliente para Remover:", min_value=1, step=1, key="del_cli_id")
        if st.button("❌ Excluir Cliente", use_container_width=True):
            excluir_cliente_db(id_cli_del)
            st.success("Cliente removido!")
            st.rerun()
            
    with st.expander("➕ Adicionar Novo Cliente"):
        c_nome = st.text_input("Nome do Cliente:")
        c_end = st.text_input("Endereço:")
        c_cid = st.text_input("Cidade/UF:")
        if st.button("💾 Gravar Cliente"):
            if c_nome and c_end:
                inserir_cliente_db(c_nome, c_end, c_cid)
                st.success("Cliente Salvo!")
                st.rerun()

    st.markdown("---")
    
    st.write("### 📦 Cadastro de Materiais")
    with st.form("form_catalogo_mat", clear_on_submit=True):
        mat_fase = st.selectbox("Segmento Alvo:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança", "Energia Solar"])
        mat_etapa = st.text_input("Etapa de Aplicação (Ex: Infra, Fechamento):")
        mat_nome = st.text_input("Descrição do Insumo Técnico:")
        mat_qtd = st.number_input("Quantidade:", value=1.0, min_value=0.1)
        mat_uni = st.selectbox("Unidade:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
        if st.form_submit_button("💾 Gravar no Catálogo"):
            if mat_nome and mat_etapa:
                inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_qtd, mat_uni)
                st.success("Material adicionado ao catálogo!")
                st.rerun()

    st.markdown("---")
    st.write("### 👥 Equipe e Responsáveis")
    lista_eq = listar_equipe_tecnica()
    if lista_eq:
        df_eq_view = pd.DataFrame(lista_eq, columns=["ID", "Nome", "Função", "Registro", "Responsável"])
        st.dataframe(df_eq_view, use_container_width=True, hide_index=True)
        
        id_eq_op = st.number_input("ID do Membro para Ação:", min_value=1, step=1, key="op_eq_id")
        if st.button("❌ Remover Membro", use_container_width=True):
            excluir_membro_equipe(id_eq_op)
            st.success("Membro removido!")
            st.rerun()
                
    with st.expander("➕ Cadastrar Membro na Equipe"):
        eq_nome = st.text_input("Nome Completo:")
        eq_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista"])
        eq_reg = st.text_input("Registro Profissional:")
        eq_resp = st.checkbox("Marcar como Responsável Técnico?")
        if st.button("💾 Gravar Membro"):
            if eq_nome and eq_reg:
                inserir_membro_equipe(eq_nome, eq_func, eq_reg, eq_resp)
                st.success("Membro alocado!")
                st.rerun()
CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
    "ENEL CE (CE) - NT-002": {"fase": 220, "linha": 380, "limite_mono": 12000, "limite_bi": 25000, "norma": "NT-002 ENEL", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Tipo Mono", "caixa_bi": "Caixa Tipo Bi", "caixa_tri": "Caixa Tipo Tri"},
    "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"}
}

st.write("## 🏗️ Fênix EngCalculus Pro")
concessionaria_sel = st.selectbox("Escolha a Concessionária de Energia Alvo do Brasil:", list(CONCESSIONARIAS.keys()))
dados_c = CONCESSIONARIAS[concessionaria_sel]

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_solar, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica (Modelo MDA)", "🚰 Hidráulica", "🔥 Gás", "🌐 Internet", "🛡️ Segurança", "☀️ Energia Solar", "📂 Catálogo de Insumos", "📥 Emissão PDF"])
with tab_civil:
    st.write("### 🧱 Configuração de Ambientes")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: nome_c = st.text_input("Nome do Cômodo:")
    with cc2: comp_c = st.number_input("Comprimento (m):", value=4.0)
    with cc3: larg_c = st.number_input("Largura (m):", value=3.5)
    if st.button("➕ Cadastrar Cômodo na Planta"):
        if nome_c:
            st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
            salvar_dados_permanentes("comodos", st.session_state.comodos)
            st.rerun()
    if st.session_state.comodos: st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)

    st.markdown("---")
    area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0)
    perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0)
    if st.button("📊 Processar Cubagem Global de Insumos Civis"):
        st.session_state.lista_materials_civil = [
            {"Etapa": "01. Locação", "Material": "Tábua de Pinus 30cm x 3m", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
            {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": 4.8, "Unidade": "m³"},
            {"Etapa": "03. Estrutura", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"}
        ]
        st.rerun()
    if st.session_state.lista_materials_civil: st.dataframe(pd.DataFrame(st.session_state.lista_materials_civil), use_container_width=True)

with tab_eletrica:
    st.write("### ⚡ Escopo Relacional sob Critério Estruturado MDA (NBR 5410)")
    modo_eletrico = st.radio("Método de Lançamento:", ["Lote Automático (Casa Toda)", "Lançar Circuito Customizado Separado"], horizontal=True)
    lista_comodos_opcoes = [c["Cômodo"] for c in st.session_state.comodos] if st.session_state.comodos else ["Geral"]
    
    if modo_eletrico == "Lote Automático (Casa Toda)":
        if st.button("🚀 Processar Lote Completo Base MDA"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO", "COMODO": "Geral", "POT_W": 1200, "TIPO": "Monofásico", "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "TOMADAS TUG", "COMODO": "Geral", "POT_W": 2400, "TIPO": "Monofásico", "COMP": 12},
                {"CIRC": "3", "DESCRIÇÃO": "TUE - CHUVEIRO", "COMODO": "Banheiro", "POT_W": 7500, "TIPO": "Bifásico", "COMP": 22}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                v_tensao = dados_c["linha"] if item["TIPO"] == "Bifásico" else dados_c["fase"]
                res = dimensionar_circuito_nbr5410_mda(item["POT_W"], v_tensao, item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "COMODO": item["COMODO"], "POT_W": int(item["POT_W"]), "POT_VA": res["VA"], "FP": res["FP"],
                    "TIPO": item["TIPO"], "DISJ": f"{res['DISJUNTORES']}A", "CURVA": res["CURVA"], "COND": f"{res['BITOLA']} mm²",
                    "FASE": "RS" if item["TIPO"]=="Bifásico" else "R", "TENSÃO": int(v_tensao), "IB": res["IB"], "IB_CORR": res["IB_CORR"], "COMP": int(item["COMP"]), "DV": res["DV"]
                })
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.rerun()
    else:
        with st.form("form_c_sep"):
            m_name = st.text_input("Nome do Circuito:", value="Tomadas de Uso Geral")
            m_com = st.selectbox("Cômodo Alvo:", lista_comodos_opcoes)
            m_desc = st.selectbox("Tipo de Carga:", ["Iluminação", "TUG - Tomadas Uso Geral", "TUE - Chuveiro"])
            m_pot = st.number_input("Potência Ativa (W):", value=2200)
            m_met = st.number_input("Metragem Linear até o QDC (m):", value=15)
            tipo_rede = st.selectbox("Fornecimento:", ["Monofásico", "Bifásico"])
            if st.form_submit_button("🔌 Calcular e Adicionar Circuito"):
                c_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
                v_tensao = dados_c["linha"] if tipo_rede == "Bifásico" else dados_c["fase"]
                res = dimensionar_circuito_nbr5410_mda(m_pot, v_tensao, m_met, m_desc)
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": c_idx, "DESCRIÇÃO": m_name, "COMODO": m_com, "POT_W": int(m_pot), "POT_VA": res["VA"], "FP": res["FP"], "TIPO": tipo_rede,
                    "DISJ": f"{res['DISJUNTORES']}A", "CURVA": res["CURVA"], "COND": f"{res['BITOLA']} mm²", "FASE": "RS" if tipo_rede=="Bifásico" else "R",
                    "TENSÃO": int(v_tensao), "IB": res["IB"], "IB_CORR": res["IB_CORR"], "COMP": int(m_met), "DV": res["DV"]
                })
                salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                st.rerun()
    if st.session_state.lista_circuitos_calc: st.dataframe(pd.DataFrame(st.session_state.lista_circuitos_calc), use_container_width=True)

with tab_hidraulica:
    st.write("### 🚰 Rede Hidráulica")
    m_agua = st.number_input("Metragem Tubo PVC 25mm (m):", value=30)
    if st.button("Calcular Hidráulica"):
        st.session_state.lista_materials_hidraulicos = [{"Etapa": "01. Água Fria", "Material": "Tubo PVC Marrom 25mm", "Quantidade": float(math.ceil(m_agua/6)), "Unidade": "barra"}]
    if st.session_state.lista_materials_hidraulicos: st.dataframe(pd.DataFrame(st.session_state.lista_materials_hidraulicos), use_container_width=True)

with tab_gas:
    st.write("### 🔥 Rede de Gás")
    m_gas = st.number_input("Metragem Tubo Cobre 15mm (m):", value=12)
    if st.button("Calcular Gás"):
        st.session_state.lista_materials_gas = [{"Etapa": "01. Tubulação", "Material": "Tubo de Cobre 15mm Classe A", "Quantidade": float(m_gas), "Unidade": "m"}]
    if st.session_state.lista_materials_gas: st.dataframe(pd.DataFrame(st.session_state.lista_materials_gas), use_container_width=True)

with tab_dados:
    st.write("### 🌐 Redes de Internet")
    m_lan = st.number_input("Metragem Cabo LAN Cat6 (m):", value=100)
    if st.button("Calcular Internet"):
        st.session_state.lista_materials_dados = [{"Etapa": "01. Cabeamento", "Material": "Cabo LAN UTP Cat6", "Quantidade": float(m_lan), "Unidade": "m"}]
    if st.session_state.lista_materials_dados: st.dataframe(pd.DataFrame(st.session_state.lista_materials_dados), use_container_width=True)

with tab_seguranca:
    st.write("### 🛡️ Segurança Eletrônica")
    m_cam = st.number_input("Quantidade Câmeras IP IP67:", value=4)
    if st.button("Calcular Segurança"):
        st.session_state.lista_materials_seguranca = [{"Etapa": "01. CFTV", "Material": "Câmeras IP HD Bullet", "Quantidade": float(m_cam), "Unidade": "un"}]
    if st.session_state.lista_materials_seguranca: st.dataframe(pd.DataFrame(st.session_state.lista_materials_seguranca), use_container_width=True)

with tab_solar:
    st.write("### ☀️ Energia Solar Fotovoltaica (NBR 16690)")
    pot_solar_kwp = st.number_input("Potência Total Demandada do Sistema (kWp):", min_value=1.0, value=5.5)
    if st.button("📊 Processar Engenharia Solar"):
        num_paineis = math.ceil((pot_solar_kwp * 1000) / 550)
        st.session_state.lista_materials_solar = [
            {"Etapa": "01. Geração", "Material": "Painel Solar Monocristalino 550Wp Plus", "Quantidade": float(num_paineis), "Unidade": "un"},
            {"Etapa": "02. Inversão", "Material": f"Inversor Solar On-Grid String {math.ceil(pot_solar_kwp)}kW", "Quantidade": 1.0, "Unidade": "un"}
        ]
        st.rerun()
    if st.session_state.lista_materials_solar: st.dataframe(pd.DataFrame(st.session_state.lista_materials_solar), use_container_width=True)
with tab_catalogo:
    st.write("### 📂 Visualização de Catálogo Geral Sincronizado SQLite")
    cat_df = listar_materiais_catalogo()
    if cat_df:
        df_cat = pd.DataFrame(cat_df, columns=["ID", "Segmento", "Etapa", "Material", "Quantidade", "Unidade"])
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
        
        id_mat_op = st.number_input("ID do Material para Modificação/Remoção:", min_value=1, step=1, key="op_mat_id")
        if st.button("❌ Remover Material do Catálogo", use_container_width=True):
            excluir_material_db(id_mat_op)
            st.success("Item removido do banco físico!")
            st.rerun()
    else:
        st.info("Catálogo vazio. Utilize a barra lateral esquerda para realizar o cadastro de insumos.")
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=9.5, textColor=colors.HexColor('#0D9488'), spaceBefore=6, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_celula = ParagraphStyle('Cel', parent=estilos['BodyText'], fontSize=6.5, leading=7, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelEsq', parent=estilos['BodyText'], fontSize=6.5, leading=7, alignment=0)
    estilo_aviso_tit = ParagraphStyle('AT', parent=estilos['Heading3'], fontSize=11, textColor=colors.HexColor('#991B1B'), fontName='Helvetica-Bold', spaceAfter=4)
    estilo_aviso_corpo = ParagraphStyle('AC', parent=estilos['BodyText'], fontSize=10, leading=13, alignment=4, spaceAfter=3)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO DE QUANTITATIVOS (MODELO MDA)</b>", estilo_titulo), Spacer(1, 4)]
    
    # --- PROVA DE NAMEERROR: Mapeamento seguro baseado na tabela persistente local ---
    lista_cli_local = listar_clientes_db()
    if lista_cli_local:
        c_nome_txt, c_end_txt, c_cid_txt = lista_cli_local[0][1], lista_cli_local[0][2], lista_cli_local[0][3]
    else:
        c_nome_txt, c_end_txt, c_cid_txt = "Condomínio Residencial Bella Vista", "Av. das Palmeiras, nº 450", "Belo Horizonte / MG"
        
    dados_cliente_tabela = [[Paragraph(f"<b>CLIENTE:</b> {c_nome_txt}", estilo_celula_esq), Paragraph(f"<b>OBRA:</b> {c_end_txt}", estilo_celula_esq), Paragraph(f"<b>LOCALIDADE:</b> {c_cid_txt}", estilo_celula_esq)]]
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
        elementos.append(Paragraph("1. Mapeamento de Cargas e Prancha Computacional Base MDA (NBR 5410)", estilo_sub))
        cabecalhos_mda = ["CIRC", "DESCRIÇÃO DA CARGA TERMINAL", "CÔMODO", "POT(W)", "FP", "POT(VA)", "IB(A)", "I'B(A)", "FCA/FCT", "BITOLA", "PROT", "QDV(%)", "BAR R", "BAR S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_mda]]
        for c in st.session_state.lista_circuitos_calc:
            p_va_val = c.get("POT_VA", c["POT_W"])
            r_val = p_va_val if c["FASE"] == "R" else (p_va_val//2 if "RS" in c["FASE"] else 0)
            s_val = p_va_val if c["FASE"] == "S" else (p_va_val//2 if "RS" in c["FASE"] else 0)
            dados_qdc_pdf.append([
                Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq), Paragraph(str(c.get("COMODO","Geral")), estilo_celula),
                Paragraph(str(c["POT_W"]), estilo_celula), Paragraph(str(c.get("FP", 1.0)), estilo_celula), Paragraph(str(p_va_val), estilo_celula),
                Paragraph(f"{c['IB']}A", estilo_celula), Paragraph(f"{c.get('IB_CORR', c['IB'])}A", estilo_celula), Paragraph("0.70/1.0", estilo_celula),
                Paragraph(str(c["COND"]), estilo_celula), Paragraph(f"{c.get('CURVA','C')}{c['DISJ']}", estilo_celula), Paragraph(f"{c.get('DV', 1.2)}%", estilo_celula),
                Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)
            ])
        t_qdc = Table(dados_qdc_pdf, colWidths=[25.0, 115.0, 65.0, 40.0, 30.0, 45.0, 40.0, 40.0, 45.0, 45.0, 40.0, 40.0, 55.0, 55.0])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_qdc)

    listas_gerais_obra = [
        ("2. Memorial Quantitativo da Fase Civil", st.session_state.lista_materials_civil, '#475569'),
        ("3. Lote Hidráulico e Redes de Esgoto", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("4. Infraestrutura de Gás Encanado", st.session_state.lista_materials_gas, '#B45309'),
        ("5. Cabeamento de Internet e Telecom", st.session_state.lista_materials_dados, '#6D28D9'),
        ("6. Ativos de Segurança Eletrônica Monitorável", st.session_state.lista_materials_seguranca, '#0F172A'),
        ("7. Engenharia Solar Fotovoltaica (NBR 16690)", st.session_state.lista_materials_solar, '#F59E0B')
    ]
    for tit, lista, col_hex in listas_gerais_obra:
        if lista:
            elementos.append(PageBreak())
            elementos.append(Paragraph(tit, estilo_sub))
            tbl_d = [[Paragraph("<b>Etapa</b>", estilo_celula), Paragraph("<b>Insumo Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
            for mat in lista: tbl_d.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
            t_m = Table(tbl_d, colWidths=[130.0, 390.0, 140.0, 80.0])
            t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor(col_hex)), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
            elementos.append(t_m)

    elementos.append(PageBreak())
    elementos.append(Paragraph("8. Diagrama Unifilar - Entrada Geral, Barramentos e Dispositivos de Proteção (DJ / DR / DPS)", estilo_sub))
    elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))
    elementos.append(PageBreak())
    elementos.append(Paragraph("9. Esquema Técnico Multifilar - Proteções de Cabeceira e Distribuição por Fase", estilo_sub))
    elementos.append(gerar_desenho_multifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))

    elementos.append(PageBreak())
    elementos.append(Paragraph("10. Diretrizes Técnicas e Normativas de Campo", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Spacer(1, 4),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴 FASES: Condutores Ativos.", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente para garantir a integridade contra choques elétricos.", estilo_aviso_corpo),
        Paragraph("• <b>Inspeção do DPS:</b> Verifique o indicador visual do protetor de surto regularmente. Janela vermelha exige substituição imediata.", estilo_aviso_corpo)
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
