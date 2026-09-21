import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP de Engenharia: Quantitativos Detalhados Civil e Elétrico")
st.markdown("---")

AVISO_NBR = (
    "ADVERTÊNCIA: ADICIONAR OU MODIFICAR COMPONENTES DOS CIRCUITOS ELÉTRICOS PODE GERAR RISCO DE SOBRECARGA OU "
    "CHOQUE SE NÃO EXECUTADO POR PROFISSIONAL QUALIFICADO. MANTENHA AS PORTAS DO QUADRO SEMPRE FECHADAS. "
    "VERIFIQUE O FUNCIONAMENTO DO DISPOSITIVO DR MENSALMENTE APERTANDO O BOTÃO DE TESTE (T)."
)

CONCESSIONARIAS = {
    "CEMIG (Minas Gerais)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000},
    "ENEL (São Paulo)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000},
    "ENEL (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000},
    "CPFL (Paulista)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000},
    "LIGHT (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000},
    "COPEL (Paraná)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000},
    "CELESC (Santa Catarina)": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000},
    "NEOENERGIA": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000},
    "EQUATORIAL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000}
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

tab_civil, tab_eletrica, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quantitativo Elétrico", "📥 3. Fechamento & Relatório PDF"])
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
    col_el1, col_el2 = st.columns(2)
    with col_el1:
        concessionaria_sel = st.selectbox("🔌 Concessionária:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria_el")
        dados_c = CONCESSIONARIAS[concessionaria_sel]
    with col_el2:
        st.write("### 🏡 Opção 1: Kit Casa Completa")
        if st.button("Gerar Kit Casa Completa", key="btn_kit_casa_el"):
            st.session_state.lista_circuitos = [
                {"Circuito": "C1", "Descrição": "Torneira Elétrica", "Carga (W)": 5000, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "32 A", "Tipo": "Bifásico"},
                {"Circuito": "C2", "Descrição": "Iluminação Geral", "Carga (W)": 1500, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"},
                {"Circuito": "C3", "Descrição": "Tomadas Gerais (TUGs)", "Carga (W)": 3500, "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "20 A", "Tipo": "Monofásico"},
                {"Circuito": "C4", "Descrição": "Chuveiro Elétrico", "Carga (W)": 7500, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "40 A", "Tipo": "Bifásico"}
            ]
            st.rerun()

    st.markdown("---")
    st.write("### 🛠️ Opção 2: Lançar Circuito Individual")
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        txt_desc = st.text_input("Descrição:", placeholder="Ex: Chuveiro", key="ti_desc_manual")
    with col_a2:
        num_carga = st.number_input("Carga (W):", min_value=100, value=2200, step=100, key="ni_carga_manual")
    with col_a3:
        sel_tipo = st.selectbox("Ligação:", ["Monofásico", "Bifásico"], key="sb_tipo_manual")
    with col_a4:
        st.write(" ")
        if st.button("➕ Inserir Circuito", key="btn_add_manual"):
            if txt_desc:
                c_num = len(st.session_state.lista_circuitos) + 1
                v_tensao = dados_c["linha"] if sel_tipo == "Bifásico" else dados_c["fase"]
                cabo_calc, dj_calc = ("6.0 mm²", "40 A") if num_carga >= 6000 else (("4.0 mm²", "25 A") if num_carga >= 3500 else ("2.5 mm²", "20 A"))
                if "Iluminação" in txt_desc or num_carga <= 1000: cabo_calc, dj_calc = "1.5 mm²", "10 A"
                st.session_state.lista_circuitos.append({"Circuito": f"C{c_num}", "Descrição": txt_desc, "Carga (W)": num_carga, "Tensão (V)": v_tensao, "Cabo": cabo_calc, "Disjuntor": dj_calc, "Tipo": sel_tipo})
                st.success("Circuito lançado!")
                st.rerun()

pot_total = sum(c["Carga (W)"] for c in st.session_state.lista_circuitos)
tipo_entrada = "Monofásico" if pot_total <= dados_c["limite_mono"] else ("Bifásico" if pot_total <= dados_c["limite_bi"] else "Trifásico")
cabo_padrao = "10.0 mm²" if tipo_entrada == "Monofásico" else ("16.0 mm²" if tipo_entrada == "Bifásico" else "25.0 mm²")
dj_padrao = "40 A" if tipo_entrada == "Monofásico" else ("63 A" if tipo_entrada == "Bifásico" else "80 A")
recalcular_materials = recalcular_materiais_brutos_eletricos(area_obra, tipo_entrada, dj_padrao)

if st.session_state.lista_circuitos:
    st.write("#### 📋 Circuitos e Materiais Elétricos")
    st.dataframe(pd.DataFrame(st.session_state.lista_circuitos), use_container_width=True)
    st.dataframe(pd.DataFrame(st.session_state.lista_materiais_eletricos), use_container_width=True)

def generar_desenho_unifilar():
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(160, (n_circ * 35) + 60)
    d = Drawing(540, altura_d)
    d.add(Line(20, altura_d - 40, 100, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 30, f"{cabo_padrao}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(100, altura_d - 40, 115, altura_d - 50, strokeColor=colors.black, strokeWidth=2))
    d.add(String(100, altura_d - 30, f"{dj_padrao}", fontSize=9, fontName='Helvetica-Bold'))
    d.add(Line(140, altura_d - 40, 140, 20, strokeColor=colors.black, strokeWidth=2))
    d.add(Line(115, altura_d - 40, 140, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(st.session_state.lista_circuitos):
        y = (altura_d - 70) - (idx * 35)
        d.add(Circle(140, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(140, y, 200, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(200, y, 215, y - 10, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(195, y + 6, c["Disjuntor"], fontSize=8, fontName='Helvetica-Bold'))
        d.add(Line(215, y, 260, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(255, y + 4, 260, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(255, y - 4, 260, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(225, y + 6, c["Cabo"], fontSize=7, fillColor=colors.HexColor('#2563EB')))
        d.add(String(270, y - 3, f"{c['Circuito']}: {c['Descrição']} ({c['Carga (W)']}W)", fontSize=8, fontName='Helvetica'))
    return d

def generar_desenho_multifilar():
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(200, (n_circ * 45) + 80)
    d = Drawing(540, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 160, 190, 220, 250
    d.add(String(x_fase1, altura_d - 20, "Fase R", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.red))
    d.add(String(x_fase2, altura_d - 20, "Fase S", textAnchor='middle', fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#9333EA')))
    d.add(String(x_neutro, altura_d - 20, "N", textAnchor='middle', fontSize=9, fontName='Helvetica-Bold', fillColor=colors.blue))
    d.add(String(x_terra, altura_d - 20, "T", textAnchor='middle', fontSize=9, fontName='Helvetica-Bold', fillColor=colors.HexColor('#16A34A')))
    d.add(Line(x_fase1, altura_d - 25, x_fase1, 20, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(x_fase2, altura_d - 25, x_fase2, 20, strokeColor=colors.HexColor('#9333EA'), strokeWidth=1.5))
    d.add(Line(x_neutro, altura_d - 25, x_neutro, 20, strokeColor=colors.blue, strokeWidth=1.5))
    d.add(Line(x_terra, altura_d - 25, x_terra, 20, strokeColor=colors.HexColor('#16A34A'), strokeWidth=1.2))
    for idx, c in enumerate(st.session_state.lista_circuitos):
        y = (altura_d - 65) - (idx * 45)
        if idx % 2 == 0:
            d.add(Rect(20, y - 12, 90, 28, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1))
            d.add(String(25, y + 2, c["Circuito"], fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#1E3A8A')))
            d.add(String(25, y - 8, c["Disjuntor"], fontSize=7, fontName='Helvetica'))
            d.add(String(105, y - 8, f"{c['Carga (W)']}W", textAnchor='end', fontSize=7, fillColor=colors.grey))
            d.add(Line(110, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
            d.add(Circle(x_fase1, y, 2.5, fillColor=colors.black, strokeColor=colors.black))
            if c["Tipo"] == "Bifásico":
                d.add(Line(110, y - 6, x_fase2, y - 6, strokeColor=colors.black, strokeWidth=1))
                d.add(Circle(x_fase2, y - 6, 2.5, fillColor=colors.black, strokeColor=colors.black))
        else:
            d.add(Rect(300, y - 12, 90, 28, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(305, y + 2, c["Circuito"], fontSize=8, fontName='Helvetica-Bold', fillColor=colors.HexColor('#0D9488')))
            d.add(String(305, y - 8, c["Disjuntor"], fontSize=7, fontName='Helvetica'))
            d.add(String(385, y - 8, f"{c['Carga (W)']}W", textAnchor='end', fontSize=7, fillColor=colors.grey))
            d.add(Line(290, y, x_fase2, y, strokeColor=colors.black, strokeWidth=1))
            d.add(Circle(x_fase2, y, 2.5, fillColor=colors.black, strokeColor=colors.black))
            if c["Tipo"] == "Monofásico":
                d.add(Line(290, y - 6, x_neutro, y - 6, strokeColor=colors.blue, strokeWidth=0.8))
                d.add(Circle(x_neutro, y - 6, 2, fillColor=colors.blue, strokeColor=colors.blue))
    return d
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=estilos['Heading1'], fontSize=15, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    estilo_sub = ParagraphStyle('S', parent=estilos['Heading2'], fontSize=11, textColor=colors.HexColor('#0D9488'), spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_corpo = ParagraphStyle('C', parent=estilos['BodyText'], fontSize=8.5, spaceAfter=3)
    estilo_aviso_tit = ParagraphStyle('AT', parent=estilos['BodyText'], fontSize=9, textColor=colors.HexColor('#991B1B'), fontName='Helvetica-Bold')
    estilo_aviso_corpo = ParagraphStyle('AC', parent=estilos['BodyText'], fontSize=8)
    
    elementos = [Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INTEGRADO</b>", estilo_titulo), Spacer(1, 6)]
    
    if st.session_state.lista_materiais_civil:
        elementos.append(Paragraph("1. Lote de Materiais da Construção Civil", estilo_sub))
        dados = [["Etapa", "Material Otimizado", "Qtd", "Un"]]
        for m in st.session_state.lista_materiais_civil: dados.append([m["Etapa"], m["Material"], str(m["Quantidade"]), m["Unidade"]])
        t = Table(dados, colWidths=[110, 290, 80, 60])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        elementos.append(t)
        
    if st.session_state.lista_materiais_eletricos:
        elementos.append(Paragraph("2. Lote de Materiais e Componentes Elétricos", estilo_sub))
        dados_el = [["Etapa", "Componente Detalhado", "Qtd", "Un"]]
        for m in st.session_state.lista_materiais_eletricos: dados_el.append([m["Etapa"], m["Material"], str(m["Quantidade"]), m["Unidade"]])
        t_el = Table(dados_el, colWidths=[110, 290, 80, 60])
        t_el.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        elementos.append(t_el)

    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("3. Esquemas Técnicos e Diagramação Elétrica (QDC)", estilo_sub))
        elementos.append(gerar_desenho_unifilar())
        elementos.append(Spacer(1, 10))
        elementos.append(gerar_desenho_multifilar())

    elementos.append(Paragraph("4. Painel de Segurança e Advertências Obrigatórias", estilo_sub))
    caviso = [Paragraph("<b>⚠️ RISCO DE CHOQUE ELÉTRICO</b>", estilo_aviso_tit), Paragraph("• <b>NBR 5410:</b> Modificações sem profissional geram risco.", estilo_aviso_corpo), Paragraph("• <b>NR-10:</b> Intervenções por pessoal não autorizado são proibidas.", estilo_aviso_corpo)]
    t_av = Table([[caviso]], colWidths=[540])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#EF4444')), ('PADDING', (0,0), (-1,-1), 8)]))
    elementos.append(t_av)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão de Documentos Separados")
    if st.session_state.lista_materiais_civil or st.session_state.lista_materiais_eletricos:
        st.download_button(label="📥 Baixar PDF Comercial Consolidado", data=gerar_pdf_completo_obra(), file_name="quantitativos_completos_fenix.pdf", mime="application/pdf", key="btn_pdf_real")
        if st.button("🗑️ Resetar Todo o Sistema", key="btn_clear_total"):
            st.session_state.lista_circuitos = []
            st.session_state.lista_materiais_civil = []
            st.session_state.lista_materiais_eletricos = []
            st.rerun()
    else:
        st.info("Efetue os levantamentos nas abas para liberar o PDF.")
