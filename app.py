import streamlit as st
import pandas as pd
import math
import sqlite3
import json
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# --- ENGINE DO BANCO DE DADOS PERSISTENTE LOCAL (SALVA PARA SEMPRE) ---
def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id TEXT PRIMARY KEY,
            dados TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            endereco TEXT,
            cidade_uf TEXT
        )
    """)
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
        st.error(f"Erro ao salvar dados: {e}")

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
if "lista_materials_civil" not in st.session_state: st.session_state.lista_materials_civil = []
if "lista_materials_eletricos" not in st.session_state: st.session_state.lista_materials_eletricos = []
if "lista_materials_hidraulicos" not in st.session_state: st.session_state.lista_materials_hidraulicos = []

if "db_sync" not in st.session_state:
    st.session_state.funcionarios = carregar_dados_permanentes("funcionarios", [
        {"id": 1, "Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA_RE": "MG20231045", "Responsavel": True},
        {"id": 2, "Nome": "Marcos Souza", "Função": "Eletricista Instalador", "CREA_RE": "RE-9942", "Responsavel": False}
    ])
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
    st.session_state.comodos = carregar_dados_permanentes("comodos", [])
    st.session_state.seguranca_insumos = carregar_dados_permanentes("seguranca", {"cameras": 4, "sensores": 3, "cabo_m": 100})
    st.session_state.db_sync = True
with st.sidebar:
    st.markdown(
        """
        <div style="background-color:#1E3A8A; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <h2 style="color:#FFFFFF; margin:0; font-family:sans-serif; letter-spacing: 2px;">⚡ FÊNIX</h2>
            <p style="color:#0D9488; margin:0; font-size:11px; font-weight:bold; letter-spacing: 1px;">ENGENHARIA & SISTEMAS</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.write("### 👥 Gestão de Equipe Técnica")
    with st.form("form_func", clear_on_submit=True):
        f_nome = st.text_input("Nome do Colaborador:")
        f_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista", "Encanador Hidráulico", "Técnico de Segurança"])
        f_reg = st.text_input("Registro (CREA / RE):")
        f_resp = st.checkbox("Definir como Responsável?")
        if st.form_submit_button("Cadastrar Funcionário"):
            if f_nome and f_reg:
                if st.session_state.funcionarios:
                    base_ids = [f["id"] for f in st.session_state.funcionarios]
                    novo_id = max(base_ids) + 1
                else:
                    novo_id = 1
                st.session_state.funcionarios.append({"id": novo_id, "Nome": f_nome, "Função": f_func, "CREA_RE": f_reg, "Responsavel": f_resp})
                salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                st.success("Funcionário Cadastrado!")
                st.rerun()

    st.write("📋 **Lista de Colaboradores:**")
    if st.session_state.funcionarios:
        for idx, f in enumerate(list(st.session_state.funcionarios)):
            c_label = "⭐ RESP" if f["Responsavel"] else "Colab"
            col_f1, col_f2 = st.columns([4, 1])
            with col_f1: st.write(f"**{f['Nome']}** ({f['Função']}) - {c_label}")
            with col_f2:
                if st.button("❌", key=f"del_f_{f['id']}_{idx}"):
                    st.session_state.funcionarios.pop(idx)
                    salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                    st.rerun()
st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP Corporativo Base SQLite: Memorial de Engenharia, Lote Otimizado e Segurança")
st.markdown("---")

st.write("### 👤 Central de Clientes (Gravar e Selecionar)")
lista_clientes = listar_clientes_db()
opcoes_clientes = ["-- Cadastrar Novo Cliente --"] + [f"ID {c[0]} - {c[1]}" for c in lista_clientes]

col_c1, col_c2 = st.columns(2)
with col_c1:
    cliente_selecionado = st.selectbox("📂 Escolher Cliente Salvo:", opcoes_clientes)

if cliente_selecionado != "-- Cadastrar Novo Cliente --":
    id_cli = int(cliente_selecionado.split(" - ")[0].replace("ID ", ""))
    dados_cli_atual = [c for c in lista_clientes if c[0] == id_cli][0]
    val_nome, val_end, val_cid = dados_cli_atual[1], dados_cli_atual[2], dados_cli_atual[3]
else:
    val_nome, val_end, val_cid = "", "", ""

with col_c2:
    with st.form("form_cliente"):
        cliente_nome = st.text_input("Nome Completo do Cliente:", value=val_nome)
        cliente_endereco = st.text_input("Endereço da Obra:", value=val_end)
        cliente_cidade = st.text_input("Cidade / UF:", value=val_cid)
        if st.form_submit_button("💾 Gravar e Salvar Cliente"):
            if cliente_nome and cliente_endereco:
                inserir_cliente_db(cliente_nome, cliente_endereco, cliente_cidade)
                st.success("Cliente gravado com sucesso no banco SQLite!")
                st.rerun()
CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "ENEL RJ (RJ) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "ENEL CE (CE) - NT-001": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica BT", "caixa_bi": "Caixa Bifásica BT", "caixa_tri": "Caixa Trifásica BT"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
    "CPFL Paulista (SP)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13", "caixa_mono": "Caixa Tipo II", "caixa_bi": "Caixa Tipo III", "caixa_tri": "Caixa Tipo IV"},
    "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "CELESC (SC) - N-321": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"}
}

def dimensionar_circuito_nbr5410(potencia, tensao, comprimento, tipo_carga):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.8
    ib = potencia / (tensao * fp)
    bitola_inicial = 1.5 if tipo_carga == "Iluminação" else 2.5
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    bitola_final = bitola_inicial
    iz_cabo = 17.5 if tipo_carga == "Iluminação" else 24.0
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
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= iz_cabo:
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
    return bitola_final, disjuntor_final, "B" if tipo_carga == "Iluminação" else "C", round(ib, 2)

tab_civil, tab_eletrica, tab_hidraulica, tab_seguranca, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quadro de Cargas (QDC)", "🚰 3. Hidráulica & Esgoto", "🛡️ 4. Sistemas de Segurança", "📥 5. Relatório PDF"])
with tab_civil:
    st.write("### 🧱 Configuração do Método de Levantamento Estrutural")
    metodo_calculo = st.radio("Escolha a metodologia de cubagem civil:", ["Cálculo por Metro Quadrado (Global)", "Prancha Customizada Cômodo por Cômodo"], horizontal=True)
    st.markdown("---")
    
    if metodo_calculo == "Cálculo por Metro Quadrado (Global)":
        area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0, step=5.0)
        perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0)
        qtd_sapatas = st.number_input("Quantidade de Sapatas Isoladas:", min_value=0, value=12, step=1)
        if st.button("📊 Processar Cubagem Global Completa"):
            st.session_state.lista_materials_civil = [
                {"Etapa": "01. Locação da Obra", "Material": "Tábua de Pinus 30cm x 3m (Gabarito de Alinhamento)", "Quantidade": math.ceil(perimetro_paredes * 0.4), "Unidade": "un"},
                {"Etapa": "01. Locação da Obra", "Material": "Piquete / Pontalete de Madeira 5x5cm", "Quantidade": 25, "Unidade": "un"},
                {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa para Sapatas/Blocos", "Quantidade": round(qtd_sapatas * 0.4, 2), "Unidade": "m³"},
                {"Etapa": "02. Infraestrutura", "Material": "Vergalhão de Aço CA-50 Cortado e Dobrado 10mm", "Quantidade": round(qtd_sapatas * 25.0, 1), "Unidade": "kg"},
                {"Etapa": "03. Estrutura e Piso", "Material": "Cimento CP II-Z-32 (Saco de 50kg) - Canteiro Geral", "Quantidade": math.ceil(area_obra * 1.1), "Unidade": "sc"},
                {"Etapa": "03. Estrutura e Piso", "Material": "Areia Média Lavada Grossa Comercial", "Quantidade": round(area_obra * 0.12, 1), "Unidade": "m³"},
                {"Etapa": "03. Estrutura e Piso", "Material": "Brita Graduada No 1 para Concretagem", "Quantidade": round(area_obra * 0.14, 1), "Unidade": "m³"},
                {"Etapa": "04. Alvenaria e Fechamento", "Material": "Tijolo Cerâmico Baiano 8 Furos (9x19x19cm)", "Quantidade": math.ceil(perimetro_paredes * 2.8 * 25 * 1.1), "Unidade": "un"},
                {"Etapa": "05. Acabamentos", "Material": "Argamassa Colante AC-III Interna/Externa (Saco 20kg)", "Quantidade": math.ceil(area_obra * 0.28), "Unidade": "sc"},
                {"Etapa": "05. Acabamentos", "Material": "Piso Porcelanato Retificado Comercial Retificado", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"}
            ]
            st.rerun()
    else:
        cc1, cc2, cc3 = st.columns(3)
        with cc1: nome_c = st.text_input("Nome do Cômodo:")
        with cc2: comp_c = st.number_input("Comprimento (m):", value=4.0)
        with cc3: larg_c = st.number_input("Largura (m):", value=3.5)
        if st.button("➕ Encaixar Cômodo na Prancha"):
            if nome_c:
                st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
                salvar_dados_permanentes("comodos", st.session_state.comodos)
                st.rerun()
        if st.session_state.comodos:
            st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)
            if st.button("📊 Processar Prancha de Ambientes"):
                area_total = sum(c["Comprimento"] * c["Largura"] for c in st.session_state.comodos)
                perimetro_total = sum(((c["Comprimento"] * 2) + (c["Largura"] * 2)) for c in st.session_state.comodos)
                st.session_state.lista_materials_civil = [
                    {"Etapa": "01. Estrutura (Prancha)", "Material": "Cimento CP II (Saco 50kg) - Obra", "Quantidade": math.ceil(area_total * 1.1), "Unidade": "sc"},
                    {"Etapa": "02. Alvenaria (Prancha)", "Material": "Tijolos Cerâmicos de Vedação", "Quantidade": math.ceil(perimetro_total * 2.8 * 25), "Unidade": "un"},
                    {"Etapa": "03. Acabamento (Prancha)", "Material": "Revestimento Cerâmico de Piso", "Quantidade": round(area_total * 1.1, 1), "Unidade": "m²"}
                ]
                st.rerun()
    if st.session_state.lista_materials_civil:
        st.dataframe(pd.DataFrame(st.session_state.lista_materials_civil), use_container_width=True)
with tab_eletrica:
    st.write("### 🎛️ Modos de Cálculo do Sistema de Cabeamento e Proteção")
    modo_eletrico = st.radio("Escolha o modo de lançamento elétrico:", ["Fazer o cálculo da casa toda (Planta Modelo Otimizada)", "Lançar circuitos separados (Cálculo Individual Automático)"], horizontal=True)
    concessionaria_sel = st.selectbox("🔌 Escolha a Distribuidora de Energia Elétrica:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]
    
    if modo_eletrico == "Fazer o cálculo da casa toda (Planta Modelo Otimizada)":
        if st.button("🚀 Processar e Dimensionar Casa Toda"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO - Área Geral", "POT_W": 1180, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "TUG - Tomadas Uso Geral", "POT_W": 2200, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 12},
                {"CIRC": "3", "DESCRIÇÃO": "TUE - Chuveiro Master Suíte", "POT_W": 7800, "TIPO": "Bifásico", "TENSÃO": dados_c["linha"], "COMP": 25}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                bitola, disj, curva, ib_c = dimensionar_circuito_nbr5410(item["POT_W"], item["TENSÃO"], item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "POT_W": item["POT_W"], "TIPO": item["TIPO"],
                    "DISJ": f"{disj}A", "CURVA": curva, "COND": f"{bitola} mm²", "FASE": "RS" if item["TIPO"]=="Bifásico" else "R",
                    "TENSÃO": item["TENSÃO"], "IB": ib_c, "COMP": item["COMP"]
                })
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.success("Planta completa dimensionada!")
            st.rerun()
    else:
        manual_pot = st.number_input("Potência Ativa do Circuito (W):", value=2200, step=100)
        manual_comp = st.number_input("Comprimento do Circuito (m):", value=15, step=1)
        if st.button("➕ Inserir Novo Circuito Calculado"):
            c_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
            b, dj, crv, ib_c = dimensionar_circuito_nbr5410(manual_pot, dados_c["fase"], manual_comp, "TUG")
            st.session_state.lista_circuitos_calc.append({
                "CIRC": c_idx, "DESCRIÇÃO": f"TUG - Circuito Customizado {c_idx}", "POT_W": manual_pot, "TIPO": "Monofásico",
                "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "R", "TENSÃO": dados_c["fase"], "IB": ib_c, "COMP": manual_comp
            })
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.rerun()

    if st.session_state.lista_circuitos_calc:
        st.dataframe(pd.DataFrame(st.session_state.lista_circuitos_calc), use_container_width=True)
# CORREÇÃO DEFINITIVA DO INDENTATIONERROR: Todo o bloco interno da aba hidráulica foi alinhado milimetricamente
with tab_hidraulica:
    st.write("### 🚰 Dimensionamento Automático de Redes Hidráulicas e Esgoto Sanitário")
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        n_banheiros = st.number_input("Quantidade de Banheiros/Lavabos:", min_value=1, value=2, step=1)
        res_litros = st.selectbox("Capacidade da Caixa d'Água (Litros):", [500, 1000, 1500, 2000])
    with col_h2:
        m_tubo_agua = st.number_input("Estimativa de Tubulação Água Fria 25mm (m):", min_value=6, value=30, step=6)
        m_tubo_esgoto = st.number_input("Estimativa de Tubulação Esgoto 100mm (m):", min_value=6, value=24, step=6)
        
    if st.button("📊 Processar Engenharia Hidráulica"):
        st.session_state.lista_materials_hidraulicos = [
            {"Etapa": "01. Reservatório", "Material": f"Caixa d'Água Polietileno {res_litros}L", "Quantidade": 1, "Unidade": "un"},
            {"Etapa": "01. Reservatório", "Material": "Kit Boia Click 3/4 com Registro Esfera", "Quantidade": 1, "Unidade": "jg"},
            {"Etapa": "02. Água Fria", "Material": "Tubo PVC Soldável Marrom 25mm (6m)", "Quantidade": math.ceil(m_tubo_agua / 6.0), "Unidade": "barra"},
            {"Etapa": "02. Água Fria", "Material": "Joelho 90 Graus PVC Soldável 25mm", "Quantidade": max(6, n_banheiros * 8), "Unidade": "un"},
            {"Etapa": "03. Esgoto Sanitário", "Material": "Tubo Esgoto PVC Branco 100mm (6m)", "Quantidade": math.ceil(m_tubo_esgoto / 6.0), "Unidade": "barra"},
            {"Etapa": "03. Esgoto Sanitário", "Material": "Caixa de Gordura em PVC com Cesta", "Quantidade": 1, "Unidade": "un"}
        ]
        st.success("Levantamento hidráulico processado!")
        st.rerun()
        
    if st.session_state.lista_materials_hidraulicos:
        st.dataframe(pd.DataFrame(st.session_state.lista_materials_hidraulicos), use_container_width=True)

def def_recalcular_materiais_brutos_eletricos(area_ref, tipo_ent, dj_pad, circuitos_list):
    materiais = [
        {"Etapa": "Infra Elétrica", "Material": "Eletroduto PVC Flexível Corrugado 3/4 (50m)", "Quantidade": max(1, math.ceil(area_ref * 1.8 / 50.0)), "Unidade": "rl"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Plástica 4x2", "Quantidade": max(4, math.ceil(area_ref * 0.45)), "Unidade": "un"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível Antichama 1.5 mm² (100m)", "Quantidade": max(1, math.ceil(area_ref * 1.5 / 100.0)), "Unidade": "rl"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível Antichama 2.5 mm² (100m)", "Quantidade": max(1, math.ceil(area_ref * 2.8 / 100.0)), "Unidade": "rl"}
    ]
    st.session_state.lista_materials_eletricos = materiais

try: area_obra_ref = area_obra
except: area_obra_ref = 70.0

pot_total_sistema = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc)
if pot_total_sistema <= dados_c["limite_mono"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Monofásico", "10.0 mm²", "40 A", dados_c["caixa_mono"]
elif pot_total_sistema <= dados_c["limite_bi"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Bifásico", "16.0 mm²", "63 A", dados_c["caixa_bi"]
else: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Trifásico", "25.0 mm²", "80 A", dados_c["caixa_tri"]

def_recalcular_materials = def_recalcular_materiais_brutos_eletricos(area_obra_ref, tipo_entrada, dj_padrao, st.session_state.lista_circuitos_calc)

with tab_seguranca:
    st.write("### 🛡️ Engenharia de Sistemas de Segurança e Monitoramento CFTV")
    n_cameras = st.number_input("Quantidade de Câmeras IP IP67:", min_value=0, value=st.session_state.seguranca_insumos["cameras"], step=1)
    n_sensores = st.number_input("Quantidade de Sensores de Presença IVP:", min_value=0, value=st.session_state.seguranca_insumos["sensores"], step=1)
    m_cabo_rede = st.number_input("Metragem de Cabo UTP Cat6 (m):", min_value=10, value=st.session_state.seguranca_insumos["cabo_m"], step=10)
    if st.button("📊 Processar Sistemas de Segurança"):
        st.session_state.seguranca_insumos = {"cameras": n_cameras, "sensores": n_sensores, "cabo_m": m_cabo_rede}
        salvar_dados_permanentes("seguranca", st.session_state.seguranca_insumos)
        st.success("Ativos de segurança calculados!")
        st.rerun()
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
    
    responsaveis_projeto = [f"{f['Função']}: {f['Nome']} ({f['CREA_RE']})" for f in st.session_state.funcionarios if f["Responsavel"]]
    elementos.append(Paragraph(f"<b>Responsáveis Técnicos:</b> {' | '.join(responsaveis_projeto)}", estilo_celula_esq))

    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado ({concessionaria_sel})</b>", estilo_sub))
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro Normativo</b>", estilo_celula), Paragraph("<b>Especificação Técnica Regulamentar</b>", estilo_celula_esq)],
        [Paragraph("Norma Técnica da Concessionária", estilo_celula), Paragraph(dados_c["norma"], estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento / Padrão de Entrada", estilo_celula), Paragraph(f"{tipo_entrada} - ({detalhe_caixa})", estilo_celula_esq)],
        [Paragraph("Cabo do Ramal Geral (Cobre)", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral da Caixa", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[240.0, 500.0])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)

    if st.session_state.lista_circuitos_calc:
        elementos.append(PageBreak())
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas e Distribuição por Fase", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO TERMINAL", "POT (W)", "POT (VA)", "DIST (M)", "CORRENTE (A)", "DISJ", "BITOLA", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        tot_r, tot_s = 0, 0
        for c in st.session_state.lista_circuitos_calc:
            p_w_val = int(c["POT_W"])
            r_val = p_w_val if c["FASE"] == "R" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            s_val = p_w_val if c["FASE"] == "S" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            tot_r += r_val; tot_s += s_val
            dados_qdc_pdf.append([Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq), Paragraph(str(p_w_val), estilo_celula), Paragraph(str(p_w_val), estilo_celula), Paragraph(f"{c['COMP']}m", estilo_celula), Paragraph(f"{c['IB']}A", estilo_celula), Paragraph(f"{c['CURVA']}{c['DISJ']}", estilo_celula), Paragraph(str(c["COND"]), estilo_celula), Paragraph(c["FASE"], estilo_celula), Paragraph(f"{c['TENSÃO']}V", estilo_celula), Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)])
        dados_qdc_pdf.append([Paragraph(f"<b>Potência Instalada Total: {pot_total_sistema} W | R: {tot_r}VA | S: {tot_s}VA</b>", estilo_celula)] + [""] * 11)
        t_qdc = Table(dados_qdc_pdf, colWidths=[35.0, 200.0, 50.0, 50.0, 50.0, 65.0, 45.0, 55.0, 40.0, 45.0, 53.0, 53.0])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('SPAN', (0,-1), (-1,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 3), ('ALIGN', (0,-1), (-1,-1), 'CENTER')]))
        elementos.append(t_qdc)

    for tit, lista in [("2. Memorial Quantitativo da Alvenaria e Cubagem Civil", st.session_state.lista_materials_civil), ("3. Componentes Elétricos Brutos e Infraestrutura", st.session_state.lista_materials_eletricos), ("4. Lote Hidráulico e Redes de Esgoto Sanitário", st.session_state.lista_materials_hidraulicos)]:
        if lista:
            elementos.append(PageBreak())
            elementos.append(Paragraph(tit, estilo_sub))
            tbl_d = [[Paragraph("<b>Etapa</b>", estilo_celula), Paragraph("<b>Insumo Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
            for mat in lista: tbl_d.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
            t_m = Table(tbl_d, colWidths=[130.0, 390.0, 140.0, 80.0])
            t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569' if "Civil" in tit else ('#0D9488' if "Elétricos" in tit else '#1E40AF'))), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
            elementos.append(t_m)

    elementos.append(PageBreak())
    elementos.append(Paragraph("5. Lote de Ativos e Segurança Eletrônica Monitorável", estilo_sub))
    dados_seg_pdf = [[Paragraph("<b>Sistema</b>", estilo_celula), Paragraph("<b>Componente Técnico</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
    seg_data_render = [
        {"Componente Técnico": "Câmera CFTV IP Bullet 2MP Full HD IP67", "Quantidade": st.session_state.seguranca_insumos["cameras"], "Unidade": "un"},
        {"Componente Técnico": "Gravador Digital de Vídeo NVR 8 Canais Ultra HD", "Quantidade": 1, "Unidade": "un"},
        {"Componente Técnico": "Sensor Infravermelho Passivo (IVP) com Suporte", "Quantidade": st.session_state.seguranca_insumos["sensores"], "Unidade": "un"},
        {"Componente Técnico": "Cabo de Rede Blindado UTP Cat6 Puro Cobre", "Quantidade": st.session_state.seguranca_insumos["cabo_m"], "Unidade": "m"}
    ]
    for row_s in seg_data_render: dados_seg_pdf.append([Paragraph("Segurança Eletrônica", estilo_celula), Paragraph(row_s["Componente Técnico"], estilo_celula_esq), Paragraph(str(row_s["Quantidade"]), estilo_celula), Paragraph(row_s["Unidade"], estilo_celula)])
    t_seg = Table(dados_seg_pdf, colWidths=[120.0, 400.0, 140.0, 80.0])
    t_seg.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_seg)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Consolidado da Obra Completa (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_unificado.pdf", mime="application/pdf", key="btn_pdf_real")
