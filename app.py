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
        # CORREÇÃO DEFINITIVA DO TYPEERROR: Extrai estritamente o índice [0] da tupla retornada
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        return valor_padrao
    return valor_padrao
# Inicialização garantida de todas as variáveis para evitar KeyError e AttributeError
if "lista_materiais_civil" not in st.session_state: st.session_state.lista_materiais_civil = []
if "lista_materiais_eletricos" not in st.session_state: st.session_state.lista_materiais_eletricos = []

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
        f_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista", "Técnico em Segurança Eletrônica"])
        f_reg = st.text_input("Registro (CREA / RE):")
        f_resp = st.checkbox("Definir como Responsável pelo Projeto?")
        if st.form_submit_button("Cadastrar Funcionário"):
            if f_nome and f_reg:
                base_ids = [f["id"] for f in st.session_state.funcionarios] if st.session_state.funcionarios else
                novo_id = max(base_ids) + 1 if base_ids else 1
                st.session_state.funcionarios.append({"id": novo_id, "Nome": f_nome, "Função": f_func, "CREA_RE": f_reg, "Responsavel": f_resp})
                salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                st.success("Funcionário Cadastrado!")
                st.rerun()
    st.write("📋 **Lista de Colaboradores:**")
    if st.session_state.funcionarios:
        for idx, f in enumerate(list(st.session_state.funcionarios)):
            c_label = "⭐ RESPONSÁVEL" if f["Responsavel"] else "Colaborador"
            col_f1, col_f2 = st.columns()
            with col_f1: st.write(f"**{f['Nome']}** ({f['Função']}) - {c_label}")
            with col_f2:
                if st.button("❌", key=f"del_f_{f['id']}_{idx}"):
                    st.session_state.funcionarios.pop(idx)
                    salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                    st.rerun()
    else:
        st.info("Nenhum funcionário cadastrado.")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP Corporativo Base SQLite: Memorial de Engenharia, Dimensionamento CAD e Segurança")
st.markdown("---")

st.write("### 👤 Cadastro e Homologação do Cliente")
col_cl1, col_cl2, col_cl3 = st.columns(3)
with col_cl1: cliente_nome = st.text_input("Nome Completo do Cliente:", value=carregar_dados_permanentes("cli_nome", "Condomínio Residencial Bella Vista"))
with col_cl2: cliente_endereco = st.text_input("Endereço da Obra:", value=carregar_dados_permanentes("cli_end", "Av. das Palmeiras, nº 450 - Lote 12"))
with col_cl3: cliente_cidade = st.text_input("Cidade / UF:", value=carregar_dados_permanentes("cli_cid", "Belo Horizonte / MG"))

salvar_dados_permanentes("cli_nome", cliente_nome)
salvar_dados_permanentes("cli_end", cliente_endereco)
salvar_dados_permanentes("cli_cid", cliente_cidade)
CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1"},
    "ENEL SP (SP) - CNC-OM-BR-24": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001"},
    "ENEL RJ (RJ) - CNC-OM-BR-24": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001"},
    "ENEL CE (CE) - NT-001": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT"},
    "CPFL Paulista (SP) - GED-13": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13"},
    "EDP SP (SP) - DIT-24": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "DIT-24"},
    "COPEL (PR) - NTC 901100": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100"},
    "CELESC (SC) - N-321.0001": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001"},
    "EQUATORIAL MA/PA/PI/AL - NT-01": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ"},
    "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN"},
    "AMAZONAS ENERGIA (AM)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-AM-01"},
    "RORAIMA ENERGIA (RR)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-RR-01"}
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
    disjuntores_comerciais =
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= iz_cabo:
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
    return bitola_final, disjuntor_final, "B" if tipo_carga == "Iluminação" else "C", round(ib, 2)

tab_civil, tab_eletrica, tab_seguranca, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quadro de Cargas (QDC)", "🛡️ 3. Sistemas de Segurança", "📥 4. Fechamento & Relatório PDF"])
with tab_civil:
    st.write("### 🧱 Configuração do Método de Levantamento Estrutural")
    metodo_calculo = st.radio("Escolha a metodologia de cubagem civil:", ["Cálculo por Metro Quadrado (Global)", "Prancha Customizada Cômodo por Cômodo"], horizontal=True)
    st.markdown("---")
    
    if metodo_calculo == "Cálculo por Metro Quadrado (Global)":
        area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0, step=5.0)
        perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0)
        qtd_sapatas = st.number_input("Quantidade de Sapatas Isoladas:", min_value=0, value=12, step=1)
        if st.button("📊 Processar Cubagem Global Completa"):
            st.session_state.lista_materiais_civil = [
                {"Etapa": "01. Locação e Infra", "Material": "Madeira de Pinus para Gabarito / Sarrafo (Barra 3m)", "Quantidade": math.ceil(perimetro_paredes * 0.5), "Unidade": "un"},
                {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa (Fundações)", "Quantidade": round(qtd_sapatas * 0.4, 2), "Unidade": "m³"},
                {"Etapa": "02. Infraestrutura", "Material": "Aço CA-50 Cortado e Dobrado (Sapatas)", "Quantidade": round(qtd_sapatas * 25.0, 1), "Unidade": "kg"},
                {"Etapa": "03. Estrutura e Piso", "Material": "Cimento CP II-E-32 (Saco 50kg)", "Quantidade": math.ceil(area_obra * 1.1), "Unidade": "sc"},
                {"Etapa": "04. Alvenaria", "Material": "Tijolos Cerâmicos de Vedação Baiano", "Quantidade": math.ceil(perimetro_paredes * 2.8 * 25), "Unidade": "un"},
                {"Etapa": "05. Fechamento", "Material": "Porta de Madeira Completa com Batente Interna (0,80x2,10m)", "Quantidade": max(2, math.ceil(area_obra * 0.05)), "Unidade": "un"},
                {"Etapa": "06. Acabamento", "Material": "Piso Porcelanato Retificado Comercial", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"}
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
                st.session_state.lista_materiais_civil = [
                    {"Etapa": "01. Estrutura e Piso (Prancha)", "Material": "Cimento CP II (Saco 50kg) - Obra", "Quantidade": math.ceil(area_total * 1.1), "Unidade": "sc"},
                    {"Etapa": "02. Alvenaria (Prancha)", "Material": "Tijolos Cerâmicos de Vedação", "Quantidade": math.ceil(perimetro_total * 2.8 * 25), "Unidade": "un"},
                    {"Etapa": "03. Acabamento (Prancha)", "Material": "Revestimento Cerâmico de Piso", "Quantidade": round(area_total * 1.1, 1), "Unidade": "m²"}
                ]
                st.rerun()
    if st.session_state.lista_materiais_civil:
        st.dataframe(pd.DataFrame(st.session_state.lista_materiais_civil), use_container_width=True)
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
def def_recalcular_materiais_brutos_eletricos(area_ref, tipo_ent, dj_pad, circuitos_list):
    materiais = [
        {"Etapa": "Infra Elétrica", "Material": "Eletroduto PVC Flexível Corrugado 3/4 (Rolo 50m)", "Quantidade": max(1, math.ceil(area_ref * 1.8 / 50.0)), "Unidade": "rl"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir Plástica 4x2", "Quantidade": max(4, math.ceil(area_ref * 0.45)), "Unidade": "un"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível Antichama 1.5 mm² (Rolo 100m)", "Quantidade": max(1, math.ceil(area_ref * 1.5 / 100.0)), "Unidade": "rl"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível Antichama 2.5 mm² (Rolo 100m)", "Quantidade": max(1, math.ceil(area_ref * 2.8 / 100.0)), "Unidade": "rl"}
    ]
    st.session_state.lista_materiais_eletricos = materiais

try: area_obra_ref = area_obra
except: area_obra_ref = 70.0

pot_total_sistema = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc)
if pot_total_sistema <= dados_c["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
    detalhe_caixa = "Caixa Tipo 'E' ou 'A'"
elif pot_total_sistema <= dados_c["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
    detalhe_caixa = "Caixa Tipo 'F' ou 'B'"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"
    detalhe_caixa = "Caixa Tipo 'H' ou 'C'"

def_recalcular_materials = def_recalcular_materiais_brutos_eletricos(area_obra_ref, tipo_entrada, dj_padrao, st.session_state.lista_circuitos_calc)

with tab_seguranca:
    st.write("### 🛡️ Engenharia de Sistemas de Segurança e Monitoramento CFTV")
    n_cameras = st.number_input("Quantidade de Câmeras Infravermelho IP IP67:", min_value=0, value=st.session_state.seguranca_insumos["cameras"], step=1)
    n_sensores = st.number_input("Quantidade de Sensores de Presença IVP Animais:", min_value=0, value=st.session_state.seguranca_insumos["sensores"], step=1)
    m_cabo_rede = st.number_input("Metragem de Cabo de Rede UTP Cat6 (m):", min_value=10, value=st.session_state.seguranca_insumos["cabo_m"], step=10)
        
    if st.button("📊 Processar e Sincronizar Sistemas de Segurança"):
        st.session_state.seguranca_insumos = {"cameras": n_cameras, "sensores": n_sensores, "cabo_m": m_cabo_rede}
        salvar_dados_permanentes("seguranca", st.session_state.seguranca_insumos)
        st.success("Ativos de segurança calculados!")
        st.rerun()

    seg_data = [
        {"Componente Técnico": "Câmera CFTV IP Bullet 2MP Full HD IP67", "Quantidade": n_cameras, "Unidade": "un"},
        {"Componente Técnico": "Gravador Digital de Vídeo NVR 8 Canais Ultra HD", "Quantidade": 1 if n_cameras <= 8 else 2, "Unidade": "un"},
        {"Componente Técnico": "Sensor Infravermelho Passivo (IVP) com Suporte", "Quantidade": n_sensores, "Unidade": "un"},
        {"Componente Técnico": "Cabo de Rede Blindado UTP Cat6 Puro Cobre", "Quantidade": m_cabo_rede, "Unidade": "m"},
        {"Componente Técnico": "HD Seagate SkyHawk 2TB (Gravação Industrial 24/7)", "Quantidade": 1, "Unidade": "un"},
        {"Componente Técnico": "Central de Alarme Monitorável Cloud com Teclado", "Quantidade": 1, "Unidade": "un"}
    ]
    st.dataframe(pd.DataFrame(seg_data), use_container_width=True)
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
    
    dados_cliente_tabela = [
        [Paragraph(f"<b>CLIENTE:</b> {cliente_nome}", estilo_celula_esq), Paragraph(f"<b>OBRA:</b> {cliente_endereco}", estilo_celula_esq), Paragraph(f"<b>LOCALIDADE:</b> {cliente_cidade}", estilo_celula_esq)]
    ]
    t_cli = Table(dados_cliente_tabela, colWidths=[240.0, 260.0, 240.0])
    t_cli.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 4)]))
    elementos.append(t_cli)
    elementos.append(Spacer(1, 6))
    
    responsaveis_projeto = [f"{f['Função']}: {f['Nome']} ({f['CREA_RE']})" for f in st.session_state.funcionarios if f["Responsavel"]]
    func_txt = " | ".join(responsaveis_projeto) if responsaveis_projeto else "Nenhum assinado"
    elementos.append(Paragraph(f"<b>Responsáveis Técnicos pelo Projeto:</b> {func_txt}", estilo_celula_esq))

    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado - Regulamentação Técnica ({concessionaria_sel})</b>", estilo_sub))
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro Normativo</b>", estilo_celula), Paragraph("<b>Especificação Conforme Norma Técnica Vigente</b>", estilo_celula_esq)],
        [Paragraph("Norma Técnica Base da Concessionária", estilo_celula), Paragraph(dados_c["norma"], estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento / Entrada", estilo_celula), Paragraph(tipo_entrada, estilo_celula_esq)],
        [Paragraph("Cabo do Ramal Geral (Cobre)", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral da Caixa", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)],
        [Paragraph("Modelo de Caixa Sugerido", estilo_celula), Paragraph(detalhe_caixa, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[240.0, 500.0])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)
    if st.session_state.lista_circuitos_calc:
        elementos.append(PageBreak())
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas e Distribuição por Fase", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO TERMINAL", "POT (W)", "POT (VA)", "DIST (M)", "CORRENTE (A)", "DISJ", "BITOLA", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        
        tot_r, tot_s, pot_total_calc = 0, 0, 0
        for c in st.session_state.lista_circuitos_calc:
            p_w_val = int(c["POT_W"])
            pot_total_calc += p_w_val
            fase_c = str(c["FASE"])
            r_val = p_w_val if fase_c == "R" else (p_w_val//2 if "RS" in fase_c else 0)
            s_val = p_w_val if fase_c == "S" else (p_w_val//2 if "RS" in fase_c else 0)
            tot_r += r_val
            tot_s += s_val
            dados_qdc_pdf.append([
                Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq),
                Paragraph(str(p_w_val), estilo_celula), Paragraph(str(p_w_val), estilo_celula),
                Paragraph(f"{c['COMP']}m", estilo_celula), Paragraph(f"{c['IB']}A", estilo_celula),
                Paragraph(f"{c['CURVA']}{c['DISJ']}", estilo_celula), Paragraph(str(c["COND"]), estilo_celula),
                Paragraph(fase_c, estilo_celula), Paragraph(f"{c['TENSÃO']}V", estilo_celula),
                Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)
            ])
            
        texto_centralizado_modelo = f"<b>Potência Instalada Total: {pot_total_calc} W | R: {tot_r}VA | S: {tot_s}VA</b>"
        dados_qdc_pdf.append([Paragraph(texto_centralizado_modelo, estilo_celula)] + [""] * 11)
        
        t_qdc = Table(dados_qdc_pdf, colWidths=[35.0, 200.0, 50.0, 50.0, 50.0, 65.0, 45.0, 55.0, 40.0, 45.0, 53.0, 53.0])
        t_qdc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
            ('SPAN', (0,-1), (-1,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 3),
            ('ALIGN', (0,-1), (-1,-1), 'CENTER')
        ]))
        elementos.append(t_qdc)

    if st.session_state.lista_materiais_civil:
        elementos.append(PageBreak())
        elementos.append(Paragraph("2. Memorial Quantitativo da Alvenaria Estrutural e Cubagem Civil do Zero", estilo_sub))
        dados_civil = [[Paragraph("<b>Etapa Civil</b>", estilo_celula), Paragraph("<b>Material Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
        for mat in st.session_state.lista_materiais_civil:
            dados_civil.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
        t_civ = Table(dados_civil, colWidths=[120.0, 400.0, 140.0, 80.0])
        t_civ.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_civ)

    if st.session_state.lista_materiais_eletricos:
        elementos.append(PageBreak())
        elementos.append(Paragraph("3. Lote de Componentes Elétricos Brutos e Infraestrutura Terminais", estilo_sub))
        dados_el_pdf = [[Paragraph("<b>Etapa Elétrica</b>", estilo_celula), Paragraph("<b>Componente Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", strokeColor:=colors.black)]]
        for mat_e in st.session_state.lista_materiais_eletricos:
            dados_el_pdf.append([Paragraph(mat_e["Etapa"], estilo_celula), Paragraph(mat_e["Material"], estilo_celula_esq), Paragraph(str(mat_e["Quantidade"]), estilo_celula), Paragraph(mat_e["Unidade"], estilo_celula)])
        t_el = Table(dados_el_pdf, colWidths=[120.0, 400.0, 140.0, 80.0])
        t_el.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_el)

    elementos.append(PageBreak())
    elementos.append(Paragraph("4. Lote de Ativos e Segurança Eletrônica Monitorável", estilo_sub))
    dados_seg_pdf = [[Paragraph("<b>Sistema</b>", estilo_celula), Paragraph("<b>Componente</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
    for row_s in seg_data:
        dados_seg_pdf.append([Paragraph("Segurança Eletrônica", estilo_celula), Paragraph(row_s["Componente Técnico"], estilo_celula_esq), Paragraph(str(row_s["Quantidade"]), estilo_celula), Paragraph(row_s["Unidade"], estilo_celula)])
    t_seg = Table(dados_seg_pdf, colWidths=[120.0, 400.0, 140.0, 80.0])
    t_seg.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_seg)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Consolidado Completo (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_completo.pdf", mime="application/pdf", key="btn_pdf_real")
