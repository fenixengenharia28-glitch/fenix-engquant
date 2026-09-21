import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP de Engenharia: Homologação de Padrão por Concessionária & Tabelas NBR 5410")
st.markdown("---")

AVISO_NBR = (
    "ADVERTÊNCIA: ADICIONAR OU MODIFICAR COMPONENTES DOS CIRCUITOS ELÉTRICOS PODE GERAR RISCO DE SOBRECARGA OU "
    "CHOQUE SE NÃO EXECUTADO POR PROFISSIONAL QUALIFICADO. MANTENHA AS PORTAS DO QUADRO SEMPRE FECHADAS. "
    "VERIFIQUE O FUNCIONAMENTO DO DISPOSITIVO DR MENSALMENTE APERTANDO O BOTÃO DE TESTE (T)."
)

# Banco de dados com dados de limites de engenharia reais para Padrão de Entrada
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

if "lista_circuitos" not in st.session_state:
    st.session_state.lista_circuitos = []
if "lista_materiais_civil" not in st.session_state:
    st.session_state.lista_materiais_civil = []
if "lista_materiais_eletricos" not in st.session_state:
    st.session_state.lista_materiais_eletricos = []
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

def gerar_desenho_unifilar(cabo_pad, dj_pad):
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(160, (n_circ * 35) + 60)
    d = Drawing(720, altura_d)
    d.add(Line(20, altura_d - 40, 100, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 30, f"Entrada: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(100, altura_d - 40, 115, altura_d - 50, strokeColor=colors.black, strokeWidth=2))
    d.add(String(100, altura_d - 30, f"Geral {dj_pad}", fontSize=9, fontName='Helvetica-Bold'))
    d.add(Line(140, altura_d - 40, 140, 20, strokeColor=colors.black, strokeWidth=2))
    d.add(Line(115, altura_d - 40, 140, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(st.session_state.lista_circuitos):
        y = (altura_d - 70) - (idx * 35)
        d.add(Circle(140, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(140, y, 200, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(200, y, 215, y - 10, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(195, y + 6, f"{c['Curva']}{c['Disjuntor']}", fontSize=8, fontName='Helvetica-Bold'))
        d.add(Line(215, y, 260, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(225, y + 6, c["Cabo"], fontSize=7, fillColor=colors.HexColor('#2563EB')))
        d.add(String(270, y - 3, f"C{c['Circuito']}: {c['Descrição']} - {c['Fase']} ({c['Carga']}W)", fontSize=8, fontName='Helvetica'))
    return d

tab_civil, tab_eletrica, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quadro de Cargas (QDC)", "📥 3. Fechamento & Relatório PDF"])
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
        st.session_state.lista_materiais_civil.append({"Etapa": "Alvenaria", "Material": "Tijolos/Blocos", "Quantidade": total_tijolos, "Unidade": "un"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Piso Porcelanato Retificado", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Argamassa AC-III (20kg)", "Quantidade": math.ceil(area_obra * 1.15 * 5.0 / 20.0), "Unidade": "sc"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Tinta Látex Acrílica (18L)", "Quantidade": math.ceil((area_parede * 2) * 0.25 / 18.0), "Unidade": "lt"})
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
                {"Circuito": "1", "Descrição": "ILUMINAÇÃO - Quartos e Área Externa", "Carga": 1180, "VA": 1180, "Ib (A)": 9.29, "Disjuntor": "16A", "Curva": "B", "Cabo": "1.5 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "2", "Descrição": "ILUMINAÇÃO - Sala, Cozinha e Banheiro", "Carga": 640, "VA": 640, "Ib (A)": 5.04, "Disjuntor": "16A", "Curva": "B", "Cabo": "1.5 mm²", "Fase": "S", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "3", "Descrição": "TUG - Dormitórios", "Carga": 480, "VA": 600, "Ib (A)": 4.72, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "4", "Descrição": "TUG - Corredor e Área Externa", "Carga": 320, "VA": 400, "Ib (A)": 3.15, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "S", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "5", "Descrição": "TUG - Sala e Banheiro", "Carga": 1040, "VA": 1300, "Ib (A)": 10.24, "Disjuntor": "20A", "Curva": "C", "Cabo": "2.5 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "6", "Descrição": "TUG - Cozinha e Área de Serviço", "Carga": 1760, "VA": 2200, "Ib (A)": 17.32, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "7", "Descrição": "TUE - Micro-Ondas", "Carga": 2450, "VA": 2450, "Ib (A)": 19.29, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "8", "Descrição": "TUE - Fritadeira Elétrica", "Carga": 2450, "VA": 2450, "Ib (A)": 19.29, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "9", "Descrição": "TUE - Secador de Cabelo 1", "Carga": 2500, "VA": 2500, "Ib (A)": 19.69, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "10", "Descrição": "TUE - Secador de Cabelo 2", "Carga": 2500, "VA": 2500, "Ib (A)": 19.69, "Disjuntor": "32A", "Curva": "C", "Cabo": "4.0 mm²", "Fase": "S", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "11", "Descrição": "TUE - Chuveiro Monofásico", "Carga": 7800, "VA": 7800, "Ib (A)": 61.42, "Disjuntor": "40A", "Curva": "B", "Cabo": "6.0 mm²", "Fase": "R", "Tensão": 127, "Tipo": "Monofásico"},
                {"Circuito": "12", "Descrição": "TUE - Chuveiro Bifásico", "Carga": 7800, "VA": 7800, "Ib (A)": 35.45, "Disjuntor": "40A", "Curva": "B", "Cabo": "6.0 mm²", "Fase": "RS", "Tensão": 220, "Tipo": "Bifásico"}
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
                if "Iluminação" in txt_desc: cabo_c, dj_c = "1.5 mm²", "16A"
                st.session_state.lista_circuitos.append({
                    "Circuito": c_num, "Descrição": txt_desc, "Carga": num_carga, "VA": num_carga, 
                    "Ib (A)": ib_calc, "Disjuntor": dj_c, "Curva": "C", "Cabo": cabo_c, "Fase": fase_atrib, "Tensão": v_tensao, "Tipo": t_tipo_c
                })
                st.success("Circuito adicionado!")
                st.rerun()
# --- CÁLCULO GERAL E REGULAMENTAÇÃO TÉCNICA DO PADRÃO DE ENTRADA ---
pot_total = sum(c["Carga"] for c in st.session_state.lista_circuitos)
dados_c_global = CONCESSIONARIAS[concessionaria_sel]

# Aplicação das regras de engenharia de limites para fixar cabos e disjuntores da rua
if pot_total <= dados_c_global["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
    detalhe_caixa = "Caixa Tipo 'E' ou Tipo 'A' (De acordo com normas locais)"
elif pot_total <= dados_c_global["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
    detalhe_caixa = "Caixa Tipo 'F' ou Tipo 'B' (De acordo com normas locais)"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"
    detalhe_caixa = "Caixa Tipo 'H' ou Tipo 'C' (De acordo com normas locais)"

recalcular_materials = recalcular_materiais_brutos_eletricos(area_obra, tipo_entrada, dj_padrao)

if st.session_state.lista_circuitos:
    st.write("#### 📋 Painel de Controle: Padrão Homologado")
    st.success(f"📋 **Enquadramento Técnico ({dados_c_global['norma']}):** Fornecimento **{tipo_entrada}** | Disjuntor Geral da Caixa: **{dj_padrao}** | Ramal de Entrada: **{cabo_padrao}**")
    st.dataframe(pd.DataFrame(st.session_state.lista_circuitos), use_container_width=True)

def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=14, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=11, textColor=colors.HexColor('#0D9488'), spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_corpo = ParagraphStyle('C', parent=estilos['BodyText'], fontSize=8.5, spaceAfter=3)
    estilo_aviso_tit = ParagraphStyle('AT', parent=estilos['BodyText'], fontSize=9, textColor=colors.HexColor('#991B1B'), fontName='Helvetica-Bold')
    estilo_aviso_corpo = ParagraphStyle('AC', parent=estilos['BodyText'], fontSize=8)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO DE QUANTITATIVOS E HOMOLOGAÇÃO</b>", estilo_titulo), Spacer(1, 6)]
    
    # SEÇÃO DO PADRÃO DE ENTRADA DA CONCESSIONÁRIA NO PDF
    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado - Regulamentação Tecnica da {concessionaria_sel}</b>", estilo_sub))
    dados_padrao_pdf = [
        ["Parâmetro do Padrão", "Especificação Conforme Norma Técnica Vigente"],
        ["Norma Técnica Base", dados_c_global["norma"]],
        ["Tipo de Fornecimento", tipo_entrada],
        ["Cabo do Ramal (Entrada)", cabo_padrao],
        ["Disjuntor Geral da Caixa", dj_padrao],
        ["Modelo de Caixa Sugerido", detalhe_caixa]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=)
    t_pad.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4), ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))
    elementos.append(t_pad)
    elementos.append(Spacer(1, 10))

    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas e Dimensionamento do QDC (NBR 5410)", estilo_sub))
        cabecalhos_qdc = ["CIRC", "DESCRIÇÃO DO CIRCUITO", "POT (W)", "POT (VA)", "CORRENTE (A)", "DISJUNTOR", "CONDUTOR", "FASE", "TENSÃO (V)"]
        dados_qdc_pdf = [cabecalhos_qdc]
        for c in st.session_state.lista_circuitos:
            dados_qdc_pdf.append([c["Circuito"], c["Descrição"], f"{c['Carga']}W", f"{c['VA']}VA", f"{c['Ib (A)']}A", f"{c['Disjuntor']} {c['Curva']}", c["Cabo"], c["Fase"], f"{c['Tensão']}V"])
        dados_qdc_pdf.append(["TOTAL", f"Potência Instalada: {pot_total} W", "", "", "", "", "", "", ""])
        t_qdc = Table(dados_qdc_pdf, colWidths=)
        t_qdc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (1,1), (1,-2), 'LEFT'), ('SPAN', (1,-1), (-1,-1)),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 4), ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        elementos.append(t_qdc)
        elementos.append(Spacer(1, 10))

    if st.session_state.lista_materiais_civil:
        elementos.append(Paragraph("2. Lote de Materiais da Construção Civil", estilo_sub))
        dados_civil = [["Etapa Civil", "Material Otimizado", "Quantidade", "Unidade"]]
        for mat in st.session_state.lista_materiais_civil: dados_civil.append([mat["Etapa"], mat["Material"], str(mat["Quantidade"]), mat["Unidade"]])
        t_civ = Table(dados_civil, colWidths=)
        t_civ.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 4), ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        elementos.append(t_civ)
        elementos.append(Spacer(1, 10))
        
    if st.session_state.lista_materiais_eletricos:
        elementos.append(Paragraph("3. Lote de Materiais e Componentes Elétricos", estilo_sub))
        dados_el = [["Etapa Elétrica", "Componente Detalhado", "Quantidade", "Unidade"]]
        for m in st.session_state.lista_materiais_eletricos: dados_el.append([m["Etapa"], m["Material"], str(m["Quantidade"]), m["Unidade"]])
        t_el = Table(dados_el, colWidths=)
        t_el.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('FONTSIZE', (0,0), (-1,-1), 8), ('PADDING', (0,0), (-1,-1), 4)
        ]))
        elementos.append(t_el)
        elementos.append(Spacer(1, 10))

    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("4. Esquema Técnico Unifilar do QDC", estilo_sub))
        elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao))
        elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("5. Painel de Segurança e Advertências Obrigatórias", estilo_sub))
    caviso = [Paragraph("<b>⚠️ RISCO DE CHOQUE ELÉTRICO</b>", estilo_aviso_tit), Paragraph("• <b>NBR 5410:</b> Modificações sem profissional geram risco.", estilo_aviso_corpo), Paragraph("• <b>NR-10:</b> Intervenções por pessoal não autorizado são proibidas.", estilo_aviso_corpo)]
    t_av = Table([[caviso]], colWidths=)
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#EF4444')), ('PADDING', (0,0), (-1,-1), 8)]))
    elementos.append(t_av)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão de Documentos Separados")
    if st.session_state.lista_materiais_civil or st.session_state.lista_materiais_eletricos:
        st.download_button(label="📥 Baixar PDF Comercial Consolidado (Formato QDC)", data=gerar_pdf_completo_obra(), file_name="quantitativos_completos_fenix.pdf", mime="application/pdf", key="btn_pdf_real")
        if st.button("🗑️ Resetar Todo o Sistema", key="btn_clear_total"):
            st.session_state.lista_circuitos = []
            st.session_state.lista_materiais_civil = []
            st.session_state.lista_materiais_eletricos = []
            st.rerun()
    else:
        st.info("Efetue os levantamentos nas abas para liberar o PDF.")
