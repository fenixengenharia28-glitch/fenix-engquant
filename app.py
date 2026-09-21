import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP de Engenharia: Prancha com Quadro de Cargas Modelo e Esquema Multifilar")
st.markdown("---")

if "lista_circuitos" not in st.session_state:
    st.session_state.lista_circuitos = []
if "lista_materiais_civil" not in st.session_state:
    st.session_state.lista_materiais_civil = []
if "lista_materiais_eletricos" not in st.session_state:
    st.session_state.lista_materiais_eletricos = []
CONCESSIONARIAS = {
    "CEMIG (Minas Gerais)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1"},
    "ENEL (São Paulo)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001"},
    "ENEL (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001"},
    "CPFL (Paulista)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13"},
    "LIGHT (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT"},
    "COPEL (Paraná)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100"},
    "CELESC (Santa Catarina)": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001"},
    "NEOENERGIA (Coelba/Elektro/DF)": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001"},
    "EQUATORIAL (Maranhão/Pará)": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ"}
}
def recalcular_materiais_brutos_eletricos(area_ref, tipo_ent, dj_pad):
    if not st.session_state.lista_circuitos:
        st.session_state.lista_materiais_eletricos = []
        return
    materiais = [
        {"Etapa": "Infra Elétrica", "Material": "Eletroduto PVC 3/4 (Rolo 50m)", "Quantidade": max(1, math.ceil(area_ref * 1.8 / 50.0)), "Unidade": "rl"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir 4x2", "Quantidade": max(4, math.ceil(area_ref * 0.45)), "Unidade": "un"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir 4x4", "Quantidade": max(2, math.ceil(area_ref * 0.15)), "Unidade": "un"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 1.5 mm² (Rolo 100m)", "Quantidade": max(1, math.ceil(area_ref * 1.5 / 100.0)), "Unidade": "rl"},
        {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 2.5 mm² (Rolo 100m)", "Quantidade": max(1, math.ceil(area_ref * 2.8 / 100.0)), "Unidade": "rl"}
    ]
    contagem_dj = {}
    for c in st.session_state.lista_circuitos:
        chave_dj = f"Disjuntor DIN {c['Tipo']} {c['Disjuntor']}"
        contagem_dj[chave_dj] = contagem_dj.get(chave_dj, 0) + 1
    for dj_nome, qtd in contagem_dj.items():
        materiais.append({"Etapa": "Dispositivos QDC", "Material": dj_nome, "Quantidade": qtd, "Unidade": "un"})
    n_fases = 1 if tipo_ent == "Monofásico" else (2 if tipo_ent == "Bifásico" else 3)
    materiais.append({"Etapa": "Proteção QDC", "Material": "DPS Classe II 45kA", "Quantidade": n_fases, "Unidade": "un"})
    materiais.append({"Etapa": "Proteção QDC", "Material": f"IDR {'Bipolar' if n_fases==1 else 'Tetrapolar'} 63A", "Quantidade": 1, "Unidade": "un"})
    materiais.append({"Etapa": "Proteção QDC", "Material": f"Disjuntor Geral DIN {tipo_ent} {dj_pad}", "Quantidade": 1, "Unidade": "un"})
    
    total_tomadas = max(6, math.ceil(area_ref * 0.35))
    total_interruptores = max(3, math.ceil(area_ref * 0.12))
    materiais.append({"Etapa": "Acabamento Elétrico", "Material": "Tomada Simples 10A 4x2", "Quantidade": total_tomadas, "Unidade": "un"})
    materiais.append({"Etapa": "Acabamento Elétrico", "Material": "Interruptor Simples com Placa 4x2", "Quantidade": total_interruptores, "Unidade": "un"})
    
    if any(c["Cabo"] == "4.0 mm²" for c in st.session_state.lista_circuitos):
        materiais.append({"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 4.0 mm² (100m)", "Quantidade": 1, "Unidade": "rl"})
    if any(c["Cabo"] == "6.0 mm²" for c in st.session_state.lista_circuitos):
        materiais.append({"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 6.0 mm² (100m)", "Quantidade": 1, "Unidade": "rl"})
    st.session_state.lista_materiais_eletricos = materiais

tab_civil, tab_eletrica, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quadro de Cargas (QDC)", "📥 3. Fechamento & Relatório PDF"])
def gerar_desenho_unifilar(cabo_pad, dj_pad):
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(140, (n_circ * 30) + 50)
    d = Drawing(720, altura_d)
    d.add(Line(20, altura_d - 30, 100, altura_d - 30, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 22, f"Entrada: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(100, altura_d - 30, 115, altura_d - 40, strokeColor=colors.black, strokeWidth=2))
    d.add(String(100, altura_d - 22, f"Geral {dj_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(140, altura_d - 30, 140, 15, strokeColor=colors.black, strokeWidth=2))
    d.add(Line(115, altura_d - 30, 140, altura_d - 30, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(st.session_state.lista_circuitos):
        y = (altura_d - 55) - (idx * 30)
        d.add(Circle(140, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(140, y, 190, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(190, y, 205, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(185, y + 5, f"{c['Curva']}{c['Disjuntor']}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(205, y, 240, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(212, y + 5, c["Cabo"], fontSize=7, fillColor=colors.HexColor('#2563EB')))
        d.add(String(250, y - 2, f"C{c['Circuito']}: {c['Descrição'][:35]} - {c['Fase']} ({c['Carga']}W)", fontSize=7.5, fontName='Helvetica'))
    return d
def gerar_desenho_multifilar():
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(180, (n_circ * 35) + 60)
    d = Drawing(720, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 220, 250, 280, 310
    
    d.add(String(x_fase1, altura_d - 15, "R", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.red))
    d.add(String(x_fase2, altura_d - 15, "S", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#9333EA')))
    d.add(String(x_neutro, altura_d - 15, "N", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.blue))
    d.add(String(x_terra, altura_d - 15, "T", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#16A34A')))
    
    d.add(Line(x_fase1, altura_d - 20, x_fase1, 15, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(x_fase2, altura_d - 20, x_fase2, 15, strokeColor=colors.HexColor('#9333EA'), strokeWidth=1.5))
    d.add(Line(x_neutro, altura_d - 20, x_neutro, 15, strokeColor=colors.blue, strokeWidth=1.5))
    d.add(Line(x_terra, altura_d - 20, x_terra, 15, strokeColor=colors.HexColor('#16A34A'), strokeWidth=1.2))
    for idx, c in enumerate(st.session_state.lista_circuitos):
        y = (altura_d - 50) - (idx * 35)
        if idx % 2 == 0:
            d.add(Rect(30, y - 10, 130, 24, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1))
            d.add(String(35, y + 2, f"C{c['Circuito']}: {c['Descrição'][:16]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(String(35, y - 6, f"{c['Curva']}{c['Disjuntor']} - {c['Cabo']}", fontSize=6.5))
            d.add(Line(160, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
            d.add(Circle(x_fase1, y, 2, fillColor=colors.black, strokeColor=colors.black))
            if "S" in c["Fase"]:
                d.add(Line(160, y - 3, x_fase2, y - 3, strokeColor=colors.black, strokeWidth=1))
                d.add(Circle(x_fase2, y - 3, 2, fillColor=colors.black, strokeColor=colors.black))
        else:
            d.add(Rect(360, y - 10, 130, 24, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(365, y + 2, f"C{c['Circuito']}: {c['Descrição'][:16]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(String(365, y - 6, f"{c['Curva']}{c['Disjuntor']} - {c['Cabo']}", fontSize=6.5))
            d.add(Line(360, y, x_neutro, y, strokeColor=colors.blue, strokeWidth=0.8))
            d.add(Circle(x_neutro, y, 1.8, fillColor=colors.blue, strokeColor=colors.blue))
            d.add(Line(360, y - 3, x_terra, y - 3, strokeColor=colors.HexColor('#16A34A'), strokeWidth=0.8))
            d.add(Circle(x_terra, y - 3, 1.8, fillColor=colors.HexColor('#16A34A'), strokeColor=colors.HexColor('#16A34A')))
    return d
with tab_civil:
    st.write("### 📐 Parâmetros de Entrada da Construção Civil")
    c_civ1, c_civ2, c_civ3 = st.columns(3)
    with c_civ1:
        area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0, step=5.0, key="ni_area_civil_geral")
        perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0, key="ni_perimetro_civil")
    with c_civ2:
        pe_direito = st.number_input("Altura do Pé-Direito (m):", min_value=1.5, value=2.8, step=0.1, key="ni_pedireito_civil")
        qtd_sapatas = st.number_input("Quantidade de Sapatas Isoladas:", min_value=0, value=12, step=1, key="ni_sapatas_civil")
    with c_civ3:
        tipo_tijolo = st.selectbox("Tipo de Alvenaria:", ["Tijolo Cerâmico Baiano", "Bloco de Concreto"], key="sb_tijolo_civil")
        espessura_contrapiso = st.number_input("Espessura do Contrapiso (cm):", min_value=3.0, value=5.0, step=0.5, key="ni_contrapiso_civil")

    if st.button("📊 Processar Engenharia Civil", key="btn_calcular_civil"):
        st.session_state.lista_materiais_civil = []
        vol_sapatas = qtd_sapatas * 0.4
        peso_aco = qtd_sapatas * 25.0
        st.session_state.lista_materiais_civil.append({"Etapa": "Infraestrutura", "Material": "Concreto Fck=30MPa", "Quantidade": round(vol_sapatas, 2), "Unidade": "m³"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Infraestrutura", "Material": "Aço CA-50", "Quantidade": round(peso_aco, 1), "Unidade": "kg"})
        vol_piso = area_obra * (espessura_contrapiso / 100.0)
        st.session_state.lista_materiais_civil.append({"Etapa": "Estrutura e Piso", "Material": "Concreto Fck=20MPa", "Quantidade": round(vol_piso, 2), "Unidade": "m³"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Estrutura e Piso", "Material": "Tela Soldada Q-92", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"})
        area_parede = perimetro_paredes * pe_direito
        total_tijolos = math.ceil(area_parede * (25 if "Tijolo" in tipo_tijolo else 12.5) * 1.1)
        st.session_state.lista_materiais_civil.append({"Etapa": "Alvenaria", "Material": "Tijolos/Blocos de Vedação", "Quantidade": total_tijolos, "Unidade": "un"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Piso Porcelanato Retificado", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Argamassa AC-III (Saco 20kg)", "Quantidade": math.ceil(area_obra * 1.15 * 5.0 / 20.0), "Unidade": "sc"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Tinta Látex Acrílica Premium (18L)", "Quantidade": math.ceil((area_parede * 2) * 0.25 / 18.0), "Unidade": "lt"})
        st.success("Levantamento civil gerado!")
        st.rerun()

    if st.session_state.lista_materiais_civil:
        st.dataframe(pd.DataFrame(st.session_state.lista_materiais_civil), use_container_width=True)
with tab_eletrica:
    st.write("### 🎛️ Configuração do Quadro de Distribuição de Cargas (QDC)")
    col_el1, col_el2 = st.columns(2)
    with col_el1:
        concessionaria_sel = st.selectbox("🔌 Escolha a Concessionária de Energia:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria_el")
        dados_c = CONCESSIONARIAS[concessionaria_sel]
    with col_el2:
        st.write("### 🏡 Opção 1: Carregar Planta Completa conforme Anexo")
        if st.button("Gerar Quadro de Cargas Completo", key="btn_kit_casa_el"):
            st.session_state.lista_circuitos = [
                {"Circuito": "1", "Descrição": "ILUMINAÇÃO - Quarto 1, Corredor, Quarto 2, Área Externa", "Carga": 1180, "VA": 1180, "Ilum": "1180", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "0", "Demanda": "60,00%", "FP": "100,00%", "Ib (A)": 9.29, "Disjuntor": "16A", "Curva": "B", "Cabo": "1.5 mm²", "Fase": "R", "Tensão": 127, "R_val": "1180", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "2", "Descrição": "ILUMINAÇÃO - Sala, Cozinha, Banheiro, Área de Serviço", "Carga": 640, "VA": 640, "Ilum": "640", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "0", "Demanda": "60,00%", "FP": "100,00%", "Ib (A)": 5.04, "Disjuntor": "16A", "Curva": "B", "Cabo": "1.5 mm²", "Fase": "S", "Tensão": 127, "R_val": "0", "S_val": "640", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "3", "Descrição": "TUG - Quarto 1, Quarto 2", "Carga": 480, "VA": 600, "Ilum": "0", "Tug100": "6", "Tug600": "0", "Tug1000": "0", "PotEsp": "0", "Demanda": "60,00%", "FP": "80,00%", "Ib (A)": 4.72, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "R", "Tensão": 127, "R_val": "600", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "4", "Descrição": "TUG - Corredor, Área Externa", "Carga": 320, "VA": 400, "Ilum": "0", "Tug100": "4", "Tug600": "0", "Tug1000": "0", "PotEsp": "0", "Demanda": "60,00%", "FP": "80,00%", "Ib (A)": 3.15, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "S", "Tensão": 127, "R_val": "0", "S_val": "400", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "5", "Descrição": "TUG - Sala, Banheiro", "Carga": 1040, "VA": 1300, "Ilum": "0", "Tug100": "3", "Tug600": "0", "Tug1000": "1", "PotEsp": "0", "Demanda": "60,00%", "FP": "80,00%", "Ib (A)": 10.24, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "R", "Tensão": 127, "R_val": "1300", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "6", "Descrição": "TUG - Cozinha, Área de Serviço", "Carga": 1760, "VA": 2200, "Ilum": "0", "Tug100": "4", "Tug600": "3", "Tug1000": "0", "PotEsp": "0", "Demanda": "60,00%", "FP": "80,00%", "Ib (A)": 17.32, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "R_val": "0", "S_val": "2200", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "7", "Descrição": "TUE - Micro-Ondas", "Carga": 2450, "VA": 2450, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "2450", "Demanda": "80,00%", "FP": "80,00%", "Ib (A)": 19.29, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "R", "Tensão": 127, "R_val": "2450", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "8", "Descrição": "TUE - Fritadeira Elétrica de Mesa", "Carga": 2450, "VA": 2450, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "2450", "Demanda": "80,00%", "FP": "80,00%", "Ib (A)": 19.29, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "R_val": "0", "S_val": "2450", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "9", "Descrição": "TUE - Secador de Cabelo Suíte 1", "Carga": 2500, "VA": 2500, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "2500", "Demanda": "80,00%", "FP": "80,00%", "Ib (A)": 19.69, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "R", "Tensão": 127, "R_val": "2500", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "10", "Descrição": "TUE - Secador de Cabelo Social 2", "Carga": 2500, "VA": 2500, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "2500", "Demanda": "80,00%", "FP": "80,00%", "Ib (A)": 19.69, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "R_val": "0", "S_val": "2500", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "11", "Descrição": "TUE - Chuveiro Banheiro Social", "Carga": 7800, "VA": 7800, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "7800", "Demanda": "80,00%", "FP": "100,00%", "Ib (A)": 61.42, "Disjuntor": "40A", "Curva": "B", "Cabo": "6.0 mm²", "Fase": "R", "Tensão": 127, "R_val": "7800", "S_val": "0", "T_val": "0", "Tipo": "Monofásico"},
                {"Circuito": "12", "Descrição": "TUE - Chuveiro Master Suíte", "Carga": 7800, "VA": 7800, "Ilum": "0", "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": "7800", "Demanda": "80,00%", "FP": "100,00%", "Ib (A)": 35.45, "Disjuntor": "40A", "Curva": "B", "Cabo": "6.0 mm²", "Fase": "RS", "Tensão": 220, "R_val": "3900", "S_val": "3900", "T_val": "0", "Tipo": "Bifásico"}
            ]
            st.rerun()
    st.markdown("---")
    st.write("### 🛠️ Opção 2: Lançar Circuito Customizado no Quadro")
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        txt_desc = st.text_input("Descrição Local:", placeholder="Ex: TUG Cozinha", key="ti_desc_manual")
    with col_a2:
        num_carga = st.number_input("Carga do Aparelho (W):", min_value=100, value=2200, step=100, key="ni_carga_manual")
    with col_a3:
        sel_tipo = st.selectbox("Ligação da Carga:", ["Monofásico (127V)", "Bifásico (220V)"], key="sb_tipo_manual")
    with col_a4:
        st.write(" ")
        if st.button("➕ Encaixar no Barramento", key="btn_add_manual"):
            if txt_desc:
                c_num = str(len(st.session_state.lista_circuitos) + 1)
                v_tensao = 220 if "220V" in sel_tipo else 127
                fase_atrib = "RS" if v_tensao == 220 else ("R" if int(c_num)%2!=0 else "S")
                ib_calc = round(num_carga / v_tensao, 2)
                cabo_c = "6.0 mm²" if num_carga >= 6000 else ("4.0 mm²" if num_carga >= 3500 else "2.5 mm²")
                dj_c = "40A" if num_carga >= 6000 else ("32A" if num_carga >= 3500 else "20A")
                t_tipo_c = "Bifásico" if v_tensao == 220 else "Monofásico"
                r_f = str(num_carga) if fase_atrib == "R" else ("0" if fase_atrib == "S" else str(round(num_carga/2)))
                s_f = str(num_carga) if fase_atrib == "S" else ("0" if fase_atrib == "R" else str(round(num_carga/2)))
                if "Iluminação" in txt_desc: cabo_c, dj_c = "1.5 mm²", "16A"
                st.session_state.lista_circuitos.append({
                    "Circuito": c_num, "Descrição": txt_desc, "Carga": num_carga, "VA": num_carga, "Ilum": str(num_carga) if "ILUM" in txt_desc.upper() else "0",
                    "Tug100": "0", "Tug600": "0", "Tug1000": "0", "PotEsp": str(num_carga) if "TUE" in txt_desc.upper() else "0", "Demanda": "80,00%", "FP": "100,00%",
                    "Ib (A)": ib_calc, "Disjuntor": dj_c, "Curva": "C", "Cabo": cabo_c, "Fase": fase_atrib, "Tensão": v_tensao, "R_val": r_f, "S_val": s_f, "T_val": "0", "Tipo": t_tipo_c
                })
                st.success("Circuito adicionado!")
                st.rerun()
pot_total = sum(int(c["Carga"]) for c in st.session_state.lista_circuitos)
dados_c_global = CONCESSIONARIAS[concessionaria_sel]
if pot_total <= dados_c_global["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
    detalhe_caixa = "Caixa Tipo 'E' ou Tipo 'A'"
elif pot_total <= dados_c_global["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
    detalhe_caixa = "Caixa Tipo 'F' ou Tipo 'B'"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"
    detalhe_caixa = "Caixa Tipo 'H' ou Tipo 'C'"

recalcular_materials = recalcular_materiais_brutos_eletricos(area_obra, tipo_entrada, dj_padrao)

if st.session_state.lista_circuitos:
    st.write("#### 📋 Painel de Controle: Padrão Homologado")
    st.success(f"📋 **Enquadramento Técnico ({dados_c_global['norma']}):** Fornecimento **{tipo_entrada}** | Disjuntor Geral da Caixa: **{dj_padrao}** | Ramal de Entrada: **{cabo_padrao}**")
    st.dataframe(pd.DataFrame(st.session_state.lista_circuitos), use_container_width=True)
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceAfter=6)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=9.5, textColor=colors.HexColor('#0D9488'), spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_celula = ParagraphStyle('Cel', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelEsq', parent=estilos['BodyText'], fontSize=7, leading=8, alignment=0)
    estilo_aviso_tit = ParagraphStyle('AT', parent=estilos['BodyText'], fontSize=8.5, textColor=colors.HexColor('#B45309'), fontName='Helvetica-Bold', spaceAfter=3)
    estilo_aviso_corpo = ParagraphStyle('AC', parent=estilos['BodyText'], fontSize=7, leading=9.5)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO DE QUANTITATIVOS E HOMOLOGAÇÃO</b>", estilo_titulo), Spacer(1, 4)]
    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado - Regulamentação Técnica da {concessionaria_sel}</b>", estilo_sub))
    
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro do Padrão</b>", estilo_celula), Paragraph("<b>Specification Conforme Norma</b>", estilo_celula_esq)],
        [Paragraph("Norma Técnica Base", estilo_celula), Paragraph(dados_c_global["norma"], estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento", estilo_celula), Paragraph(tipo_entrada, estilo_celula_esq)],
        [Paragraph("Cabo do Ramal (Entrada)", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral da Caixa", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)],
        [Paragraph("Modelo de Caixa Sugerido", estilo_celula), Paragraph(detalhe_caixa, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[180, 360])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)
    elementos.append(Spacer(1, 8))

    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas e Distribuição por Fase", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO", "POT ILUM", "POT ESP", "POT (W)", "POT (VA)", "DEM (%)", "CORR (A)", "DISJ", "COND", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        for c in st.session_state.lista_circuitos:
            dados_qdc_pdf.append([
                Paragraph(c["Circuito"], estilo_celula), Paragraph(c["Descrição"], estilo_celula_esq),
                Paragraph(f"{c['Ilum']}VA", estilo_celula), Paragraph(f"{c['PotEsp']}VA", estilo_celula),
                Paragraph(f"{c['Carga']}W", estilo_celula), Paragraph(f"{c['VA']}VA", estilo_celula),
                Paragraph(c["Demanda"], estilo_celula), Paragraph(f"{c['Ib (A)']}A", estilo_celula),
                Paragraph(f"{c['Curva']}{c['Disjuntor']}", estilo_celula), Paragraph(c["Cabo"], estilo_celula),
                Paragraph(c["Fase"], estilo_celula), Paragraph(f"{c['Tensão']}V", estilo_celula),
                Paragraph(f"{c['R_val']}VA", estilo_celula), Paragraph(f"{c['S_val']}VA", estilo_celula)
            ])
        tot_r = sum(int(c['R_val']) for c in st.session_state.lista_circuitos)
        tot_s = sum(int(c['S_val']) for c in st.session_state.lista_circuitos)
        dados_qdc_pdf.append([Paragraph("<b>TOTAL</b>", estilo_celula), Paragraph(f"<b>Potência Total Instalada: {pot_total} W</b>", estilo_celula_esq), "", "", "", "", "", "", "", "", "", "", Paragraph(f"<b>{tot_r}VA</b>", estilo_celula), Paragraph(f"<b>{tot_s}VA</b>", estilo_celula)])
        t_qdc = Table(dados_qdc_pdf, colWidths=[30, 160, 45, 45, 45, 45, 40, 45, 40, 45, 35, 45, 50, 50])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('SPAN', (1,-1), (11,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 2)]))
        elementos.append(t_qdc)
        elementos.append(Spacer(1, 8))
    if st.session_state.lista_materiais_civil:
        elementos.append(Paragraph("2. Lote de Materiais da Construção Civil", estilo_sub))
        dados_civil = [[Paragraph("<b>Etapa Civil</b>", estilo_celula), Paragraph("<b>Material Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
        for mat in st.session_state.lista_materiais_civil:
            dados_civil.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
        t_civ = Table(dados_civil, colWidths=[110, 260, 90, 80])
        t_civ.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_civ)
        elementos.append(Spacer(1, 8))
        
    if st.session_state.lista_materiais_eletricos:
        elementos.append(Paragraph("3. Lote de Materiais e Componentes Elétricos Brutos", estilo_sub))
        dados_el = [[Paragraph("<b>Etapa Elétrica</b>", estilo_celula), Paragraph("<b>Componente Detalhado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
        for m in st.session_state.lista_materiais_eletricos:
            dados_el.append([Paragraph(m["Etapa"], estilo_celula), Paragraph(m["Material"], estilo_celula_esq), Paragraph(str(m["Quantidade"]), estilo_celula), Paragraph(m["Unidade"], estilo_celula)])
        t_el = Table(dados_el, colWidths=[110, 260, 90, 80])
        t_el.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_el)
        elementos.append(Spacer(1, 8))

    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("4. Desenho Técnico Unifilar do Quadro (QDC)", estilo_sub))
        elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao))
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph("5. Desenho Técnico Multifilar e Conexão de Bornes por Fase", estilo_sub))
        elementos.append(gerar_desenho_multifilar())
        elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("6. Observações Técnicas Normativas Obrigatórias (Porta do Quadro)", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴🟡 PRETO/VERMELHO/AMARELO: Condutores de Fase | ⚪⚪ BRANCO/CINZA: Condutores de Retorno (Iluminação).", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados nesta tampa de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente. Se ele não desarmar e desligar a energia da casa, substitua-o imediatamente (risco de choque).", estilo_aviso_corpo),
        Paragraph("• <b>Inspeção do DPS:</b> Verifique o indicador visual do protetor de surto regularmente. Janela verde indica funcionamento normal; janela vermelha exige substituição imediata do módulo.", estilo_aviso_corpo),
        Paragraph("• <b>Seção vs. Disjuntor:</b> Nunca aumente a amperagem de um disjuntor sem recalcular a fiação. O disjuntor protege o fio; alterar o valor sem critério técnico causa incêndio.", estilo_aviso_corpo),
        Paragraph("• <b>Conexões Seguras:</b> Toda manutenção ou adição de circuito deve utilizar terminais elétricos apropriados (tipo ilhós/tubular). Emendas simples dentro do QDC são proibidas.", estilo_aviso_corpo),
        Paragraph("• <b>Manutenção Preventiva:</b> A cada 12 meses, realize a manutenção com o quadro totalmente desligado, efetuando o reaperto de todos os parafusos (disjuntores e barramentos de neutro/terra).", estilo_aviso_corpo),
        Paragraph("• <b>Distribuição de Cargas:</b> Novas cargas (ar-condicionado, eletrodomésticos potentes) devem ser distribuídas entre as fases para evitar sobrecarga no cabo geral de entrada.", estilo_aviso_corpo),
        Paragraph("• <b>Área de Segurança:</b> Mantenha a frente deste quadro totalmente desobstruída. Nunca guarde vassouras, caixas ou objetos que dificultem o acesso rápido.", estilo_aviso_corpo),
        Paragraph("• <b>Profissionalismo:</b> Qualquer alteração na rede elétrica residencial deve ser feita exclusivamente por um eletricista qualificado.", estilo_aviso_corpo)
    ]
    t_av = Table([[caviso]], colWidths=[540])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#D97706')), ('PADDING', (0,0), (-1,-1), 5)]))
    elementos.append(t_av)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨 Imprimir Documento Integrado")
    if st.session_state.lista_materiais_civil or st.session_state.lista_materiais_eletricos:
        st.download_button(label="📥 Baixar Prancha Técnica com Quadro de Cargas & Multifilar (PDF)", data=gerar_pdf_completo_obra(), file_name="quadro_de_cargas_fenix.pdf", mime="application/pdf", key="btn_pdf_real")
        if st.button("🗑 Resetar Todo O Sistema", key="btn_clear_total"):
            st.session_state.lista_circuitos = []
            st.session_state.lista_materiais_civil = []
            st.session_state.lista_materiais_eletricos = []
            st.rerun()
    else:
        st.info("Efetue os levantamentos nas abas para liberar o PDF.")
