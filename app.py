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
    cursor.execute("CREATE TABLE IF NOT EXISTS equipe_tecnica (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, registro TEXT, responsavel INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS comodos_obra (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, comprimento REAL, largura REAL)")
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
        if row and row[0]: return json.loads(row[0])
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

if "db_sync_completo" not in st.session_state:
    st.session_state.lista_materials_civil = []
    st.session_state.lista_materials_hidraulicos = []
    st.session_state.lista_materials_gas = []
    st.session_state.lista_materials_dados = []
    st.session_state.lista_materials_seguranca = []
    st.session_state.lista_materials_solar = []
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
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
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]
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
    d.add(String(20, altura_d - 32, f"Ramal BT: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
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
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:20]}", fontSize=7.5))
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
            st.st.rerun()
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
    st.write("### 📦 Catálogo de Materiais")
    with st.expander("➕ Cadastrar Insumo Técnico"):
        with st.form("form_catalogo_mat", clear_on_submit=True):
            mat_fase = st.selectbox("Segmento:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança", "Energia Solar"])
            mat_etapa = st.text_input("Etapa de Aplicação:")
            mat_nome = st.text_input("Descrição do Material:")
            mat_qtd = st.number_input("Fator de Multiplicação:", value=1.0, min_value=0.1)
            mat_uni = st.selectbox("Unidade:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
            if st.form_submit_button("💾 Salvar Material"):
                if mat_nome and mat_etapa:
                    inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_qtd, mat_uni)
                    st.success("Adicionado!")
                    st.rerun()
    st.markdown("---")
    st.write("### 👥 Equipe e Engenheiros")
    lista_eq = listar_equipe_tecnica()
    if lista_eq:
        df_eq_view = pd.DataFrame(lista_eq, columns=["ID", "Nome", "Função", "Registro", "Responsável"])
        st.dataframe(df_eq_view, use_container_width=True, hide_index=True)
        id_eq_op = st.number_input("ID do Membro para Ação:", min_value=1, step=1, key="op_eq_id")
        if st.button("❌ Remover Membro", use_container_width=True):
            excluir_membro_equipe(id_eq_op)
            st.success("Removido!")
            st.rerun()
    with st.expander("➕ Cadastrar Membro na Equipe"):
        eq_nome = st.text_input("Nome Completo:")
        eq_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista"])
        eq_reg = st.text_input("Registro Profissional:")
        eq_resp = st.checkbox("Marcar como RT?")
        if st.button("💾 Gravar Membro"):
            if eq_nome and eq_reg:
                inserir_membro_equipe(eq_nome, eq_func, eq_reg, eq_resp)
                st.success("Membro alocado!")
                st.rerun()

CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
    "ENEL CE (CE) - NT-002": {"fase": 220, "linha": 380, "limite_mono": 12000, "limite_bi": 25000, "norma": "NT-002 ENEL", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
    "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Tipo Mono", "caixa_bi": "Caixa Tipo Bi", "caixa_tri": "Caixa Tipo Tri"},
    "CELESC (SC) - N-321": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
    "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"}
}

st.write("## 🏗️ Fênix EngCalculus Pro")
concessionaria_sel = st.selectbox("Escolha a Concessionária de Energia Alvo do Brasil:", list(CONCESSIONARIAS.keys()))
dados_c = CONCESSIONARIAS[concessionaria_sel]

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_solar, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica (Modelo MDA)", "🚰 Hidráulica", "🔥 Gás", "🌐 Internet", "🛡️ Segurança", "☀️ Energia Solar", "📂 Catálogo de Insumos", "📥 Emissão PDF"])

with tab_civil:
    st.write("### 🧱 Planta de Cômodos (Inserir / Alterar / Remover)")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        with st.form("form_comodo_civil"):
            c_nome = st.text_input("Nome do Ambiente (Ex: Cozinha):")
            c_comp = st.number_input("Comprimento Linear (m):", value=4.0, min_value=0.1)
            c_larg = st.number_input("Largura Linear (m):", value=3.0, min_value=0.1)
            if st.form_submit_button("➕ Salvar Ambiente"):
                if c_nome:
                    inserir_comodo_db(c_nome, c_comp, c_larg)
                    st.success("Cômodo gravado!")
                    st.rerun()
    with col_v2:
        lista_comodos_fisicos = listar_comodos_db()
        if lista_comodos_fisicos:
            df_com_f = pd.DataFrame(lista_comodos_fisicos, columns=["ID", "Cômodo", "Comprimento (m)", "Largura (m)"])
            st.dataframe(df_com_f, use_container_width=True, hide_index=True)
            id_com_op = st.number_input("ID do Cômodo para Ação:", min_value=1, step=1, key="op_com_id")
            c_alt_chk = st.checkbox("Ativar Alteração de Dados?")
            if c_alt_chk:
                alt_c_nome = st.text_input("Novo Nome Ambiente:")
                alt_c_comp = st.number_input("Novo Comprimento:", value=4.0)
                alt_c_larg = st.number_input("Nova Largura:", value=3.0)
                if st.button("📝 Confirmar Alteração Cômodo"):
                    atualizar_comodo_db(id_com_op, alt_c_nome, alt_c_comp, alt_c_larg)
                    st.success("Dados updated!")
                    st.rerun()
            if st.button("❌ Remover Cômodo Selecionado"):
                excluir_comodo_db(id_com_op)
                st.success("Removido da planta!")
                st.rerun()
    st.markdown("---")
    modo_civil = st.radio("Seletor do Modo de Escopo Civil:", ["Cálculo Global por Área (m²)", "Levantamento por Cômodos Cadastrados"], horizontal=True)
    if modo_civil == "Cálculo Global por Área (m²)":
        area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0)
        perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0)
        if st.button("📊 Processar Cubagem Global de Insumos Civis"):
            st.session_state.lista_materials_civil = [
                {"Etapa": "01. Locação", "Material": "Tábua de Pinus 30cm x 3m", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
                {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": 4.8, "Unidade": "m³"},
                {"Etapa": "03. Estrutura", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"}
            ]
            st.rerun()
    else:
        if lista_comodos_fisicos:
            area_acumulada = sum(float(row_c[2]) * float(row_c[3]) for row_c in lista_comodos_fisicos)
            perimetro_acumulado = sum((float(row_c[2]) * 2) + (float(row_c[3]) * 2) for row_c in lista_comodos_fisicos)
            num_comodos = len(lista_comodos_fisicos)
            st.metric("Área Computada dos Ambientes", f"{round(area_acumulada, 2)} m²")
            if st.button("📊 Processar Insumos por Prancha de Cômodos"):
                st.session_state.lista_materials_civil = []
                st.session_state.lista_circuitos_calc = []
                st.session_state.lista_materials_hidraulicos = []
                st.session_state.lista_materials_gas = []
                st.session_state.lista_materials_dados = []
                st.session_state.lista_materials_seguranca = []
                st.session_state.lista_materials_solar = []
                itens_catalogo = listar_materiais_catalogo()
                for item in itens_catalogo:
                    fase_cat, etapa_cat, nome_cat, fat_cat, uni_cat = item[1], item[2], item[3], float(item[4]), item[5]
                    if fase_cat == "Civil":
                        st.session_state.lista_materials_civil.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(area_acumulada * fat_cat)), "Unidade": uni_cat})
                    elif fase_cat == "Hidráulica":
