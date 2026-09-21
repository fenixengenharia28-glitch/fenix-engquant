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
st.subheader("Plataforma Autônoma: Separação de Quantitativos Civil & Elétrico")
st.markdown("---")

# Definição Global do Aviso Obrigatório NBR 5410
AVISO_NBR = (
    "ADVERTÊNCIA: ADICIONAR OU MODIFICAR COMPONENTES DOS CIRCUITOS ELÉTRICOS PODE GERAR RISCO DE SOBRECARGA OU "
    "CHOQUE SE NÃO EXECUTADO POR PROFISSIONAL QUALIFICADO. MANTENHA AS PORTAS DO QUADRO SEMPRE FECHADAS. "
    "VERIFIQUE O FUNCIONAMENTO DO DISPOSITIVO DR MENSALMENTE APERTANDO O BOTÃO DE TESTE (T)."
)

# Banco de dados de concessionárias brasileiras
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

# Inicialização das memórias técnicas da sessão
if "lista_circuitos" not in st.session_state:
    st.session_state.lista_circuitos = []
if "lista_materiais_civil" not in st.session_state:
    st.session_state.lista_materiais_civil = []
if "lista_materiais_eletricos" not in st.session_state:
    st.session_state.lista_materiais_eletricos = []

# Abas Principais do Sistema Integrado com Foco em Separação
tab_civil, tab_eletrica, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quantitativo Elétrico", "📥 3. Fechamento & Relatório PDF"])

# ABA 1: LEVANTAMENTO DA CONSTRUÇÃO CIVIL
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
        tipo_tijolo = st.selectbox("Tipo de Alvenaria:", ["Tijolo Baiano (8 furos - 9x19x19)", "Bloco de Concreto (14x19x39)"], key="sb_tijolo_civil")
        espessura_contrapiso = st.number_input("Espessura do Contrapiso (cm):", min_value=3.0, value=5.0, step=0.5, key="ni_contrapiso_civil")

    if st.button("📊 Processar Engenharia Civil", key="btn_calcular_civil"):
        st.session_state.lista_materiais_civil = []
        
        # Infraestrutura
        vol_concreto_sapatas = qtd_sapatas * 0.4
        peso_aco_sapatas = qtd_sapatas * 25.0
        st.session_state.lista_materiais_civil.append({"Etapa": "Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": round(vol_concreto_sapatas, 2), "Unidade": "m³"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Infraestrutura", "Material": "Aço CA-50 Cortado e Dobrado", "Quantidade": round(peso_aco_sapatas, 1), "Unidade": "kg"})
        
        # Estrutura e Piso
        vol_concreto_piso = area_obra * (espessura_contrapiso / 100.0)
        st.session_state.lista_materiais_civil.append({"Etapa": "Estrutura e Piso", "Material": "Concreto para Contrapiso Fck=20MPa", "Quantidade": round(vol_concreto_piso, 2), "Unidade": "m³"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Estrutura e Piso", "Material": "Tela Eletrosoldada Q-92 para Piso", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"})
        
        # Alvenaria
        area_parede_total = perimetro_paredes * pe_direito
        consumo_tijolo = 25 if "Tijolo" in tipo_tijolo else 12.5
        tijolo_nome = "Tijolo Cerâmico Baiano 8 Furos" if "Tijolo" in tipo_tijolo else "Bloco de Concreto Estrutural"
        
        total_tijolos = math.ceil(area_parede_total * consumo_tijolo * 1.1)
        st.session_state.lista_materiais_civil.append({"Etapa": "Alvenaria", "Material": tijolo_nome, "Quantidade": total_tijolos, "Unidade": "un"})
        
        # Acabamentos
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Piso Porcelanato Retificado", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Argamassa Colante AC-III (20kg)", "Quantidade": math.ceil(area_obra * 1.15 * 5.0 / 20.0), "Unidade": "sc"})
        st.session_state.lista_materiais_civil.append({"Etapa": "Acabamento", "Material": "Tinta Látex Acrílica (18L)", "Quantidade": math.ceil((area_parede_total * 2) * 0.25 / 18.0), "Unidade": "lt"})
        
        st.success("Levantamento civil gerado e separado!")
        st.rerun()

    if st.session_state.lista_materiais_civil:
        st.dataframe(pd.DataFrame(st.session_state.lista_materiais_civil), use_container_width=True)
# ----------------------------------------------------
# ABA 2: LEVANTAMENTO DAS INSTALAÇÕES ELÉTRICAS
# ----------------------------------------------------
with tab_eletrica:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        concessionaria_sel = st.selectbox("🔌 Selecione a Concessionária de Energia:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria_el")
        dados_c = CONCESSIONARIAS[concessionaria_sel]
    with col_c2:
        st.write("### 🛠️ Geração de Escopo")
        if st.button("🏡 Injetar Kit Casa Completa (Elétrica)", key="btn_kit_casa_el"):
            st.session_state.lista_circuitos = [
                {"Circuito": "Circuito 1", "Descrição": "Torneira Elétrica (Cozinha)", "Carga (W)": 5000, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "32 A", "Tipo": "Bifásico"},
                {"Circuito": "Circuito 2", "Descrição": "Iluminação Cozinha e Copa", "Carga (W)": 800, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"},
                {"Circuito": "Circuito 3", "Descrição": "Iluminação Sala e Quartos", "Carga (W)": 1200, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"},
                {"Circuito": "Circuito 4", "Descrição": "Tomadas Cozinha e Área Serviço", "Carga (W)": 4400, "Tensão (V)": dados_c["fase"], "Cabo": "4.0 mm²", "Disjuntor": "25 A", "Tipo": "Monofásico"},
                {"Circuito": "Circuito 5", "Descrição": "Tomadas de Uso Geral (TUGs)", "Carga (W)": 2200, "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "20 A", "Tipo": "Monofásico"},
                {"Circuito": "Circuito 6", "Descrição": "Chuveiro Elétrico", "Carga (W)": 7500, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "40 A", "Tipo": "Bifásico"},
                {"Circuito": "Circuito 7", "Descrição": "Ar Condicionado", "Carga (W)": 2000, "Tensão (V)": dados_c["linha"], "Cabo": "2.5 mm²", "Disjuntor": "16 A", "Tipo": "Bifásico"}
            ]
            
            # Geração automática da tabela paralela de MATERIAIS ELÉTRICOS BRUTOS
            st.session_state.lista_materiais_eletricos = [
                {"Etapa": "Infra Elétrica", "Material": "Eletroduto Corrugado PVC 3/4 (Rolo 50m)", "Quantidade": math.ceil(area_obra * 1.8 / 50.0), "Unidade": "rl"},
                {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir 4x2 PVC", "Quantidade": math.ceil(area_obra * 0.45), "Unidade": "un"},
                {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir 4x4 PVC", "Quantidade": math.ceil(area_obra * 0.15), "Unidade": "un"},
                {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 1.5 mm² (Rolo 100m) - Azul/Preto", "Quantidade": math.ceil(area_obra * 2.2 / 100.0), "Unidade": "rl"},
                {"Etapa": "Fiação Elétrica", "Material": "Cabo Flexível 2.5 mm² (Rolo 100m) - Vermelho/Azul/Verde", "Quantidade": math.ceil(area_obra * 3.5 / 100.0), "Unidade": "rl"},
                {"Etapa": "Dispositivos", "Material": "Quadro de Distribuição (QDC) para 12/16 Módulos DIN", "Quantidade": 1, "Unidade": "un"}
            ]
            st.success("Cálculo e quantitativos de materiais elétricos concluídos!")
            st.rerun()

    if st.session_state.lista_circuitos:
        st.write("#### 📋 Relação de Circuitos Ativos (QDC)")
        st.dataframe(pd.DataFrame(st.session_state.lista_circuitos), use_container_width=True)
        st.write("#### 📊 Lista Isolada de Materiais Elétricos Brutos Gerados")
        st.dataframe(pd.DataFrame(st.session_state.lista_materiais_eletricos), use_container_width=True)

# --- CÁLCULO GERAL DO PADRÃO DE ATENDIMENTO ---
pot_total = sum(c["Carga (W)"] for c in st.session_state.lista_circuitos)
dados_c_global = CONCESSIONARIAS[concessionaria_sel]
if pot_total <= dados_c_global["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
elif pot_total <= dados_c_global["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"

# --- ALGORITMOS DOS MOTORES GRÁFICOS ---
def gerar_desenho_unifilar():
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

def gerar_desenho_multifilar():
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
# --- ENGINE CONSOLIDADA DA DOCUMENTAÇÃO EM PDF SEPARADA ---
def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=15, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], fontSize=11, textColor=colors.HexColor('#0D9488'), spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_corpo = ParagraphStyle('Corpo', parent=estilos['BodyText'], fontSize=8.5, spaceAfter=3)
    estilo_aviso_tit = ParagraphStyle('AvisoTit', parent=estilos['BodyText'], fontSize=9, textColor=colors.HexColor('#991B1B'), fontName='Helvetica-Bold', spaceAfter=4)
    estilo_aviso_corpo = ParagraphStyle('AvisoCorpo', parent=estilos['BodyText'], fontSize=8, textColor=colors.HexColor('#1E293B'), spaceAfter=3)

    elementos = []
    
    elementos.append(Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL INDEPENDENTE DE QUANTITATIVOS</b>", estilo_titulo))
    elementos.append(Paragraph("Demonstrativo Separado por Categorias de Compra de Insumos", estilo_corpo))
    elementos.append(Spacer(1, 6))
    
    # SEÇÃO 1: APENAS CONSTRUÇÃO CIVIL NO PDF
    if st.session_state.lista_materiais_civil:
        elementos.append(Paragraph("1. Lote de Materiais da Construção Civil (Depósito Civil)", estilo_sub))
        dados_tabela_civil = [["Etapa Civil", "Insumo / Material Otimizado", "Quantidade", "Unidade"]]
        for mat in st.session_state.lista_materiais_civil:
            dados_tabela_civil.append([mat["Etapa"], mat["Material"], str(mat["Quantidade"]), mat["Unidade"]])
        
        t_civ = Table(dados_tabela_civil, colWidths=[100, 260, 90, 90])
        t_civ.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            ('PADDING', (0,0), (-1,-1), 4),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        elementos.append(t_civ)
        elementos.append(Spacer(1, 10))
        
    # SEÇÃO 2: APENAS INSTALAÇÃO ELÉTRICA NO PDF
    if st.session_state.lista_materiais_eletricos:
        elementos.append(Paragraph("2. Lote de Materiais e Componentes Elétricos (Distribuidora)", estilo_sub))
        dados_tabela_el_mat = [["Etapa Elétrica", "Componente / Insumo Hidro-Elétrico", "Quantidade", "Unidade"]]
        for emat in st.session_state.lista_materiais_eletricos:
            dados_tabela_el_mat.append([emat["Etapa"], emat["Material"], str(emat["Quantidade"]), emat["Unidade"]])
            
        t_el_mat = Table(dados_tabela_el_mat, colWidths=[100, 260, 90, 90])
        t_el_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            ('PADDING', (0,0), (-1,-1), 4),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        elementos.append(t_el_mat)
        elementos.append(Spacer(1, 10))

    # SEÇÃO 3: CIRCUITOS E PRANCHAS DO QDC
    if st.session_state.lista_circuitos:
        elementos.append(Paragraph("3. Esquemas Técnicos e Diagramação Elétrica (QDC)", estilo_sub))
        elementos.append(gerar_desenho_unifilar())
        elementos.append(Spacer(1, 10))
        elementos.append(gerar_desenho_multifilar())
        elementos.append(Spacer(1, 10))

    # Painel NBR 5410 & NR-10
    elementos.append(Paragraph("4. Painel de Segurança e Advertências Obrigatórias", estilo_sub))
    conteudo_aviso = [
        Paragraph("<b>⚠️ RISCO DE CHOQUE ELÉTRICO - PERIGO DE MORTE</b>", estilo_aviso_tit),
        Paragraph("• <b>Item 6.1.5.1 (NBR 5410):</b> Modificações sem profissional qualificado geram risco de curto e incêndio.", estilo_aviso_corpo),
        Paragraph("• <b>Proteção DR:</b> Teste mensalmente o botão (T) do IDR geral para garantir a proteção humana.", estilo_aviso_corpo),
        Paragraph("• <b>Item 4.5.3 (NR-10):</b> Intervenções por pessoal não autorizado são expressamente proibidas.", estilo_aviso_corpo)
    ]
    t_aviso = Table([[conteudo_aviso]], colWidths=[540])
    t_aviso.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('BORDER', (0,0), (-1,-1), 1.5, colors.HexColor('#EF4444')),
        ('PADDING', (0,0), (-1,-1), 8)
    ]))
    elementos.append(t_aviso)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- PAINEL DE CONTROLE FINAL NA TERCEIRA ABA ---
with tab_pdf:
    st.write("### 🖨️ Central de Emissão de Documentos Separados")
    if st.session_state.lista_materiais_civil or st.session_state.lista_materiais_eletricos:
        arquivo_pdf = gerar_pdf_completo_obra()
        st.download_button(
            label="📥 Baixar Prancha Separada Civil e Elétrica (PDF Comercial)",
            data=arquivo_pdf,
            file_name="quantitativos_separados_fenix.pdf",
            mime="application/pdf",
            key="btn_download_pdf_total_real"
        )
        if st.button("🗑️ Resetar Todo o Sistema", key="btn_clear_total"):
            st.session_state.lista_circuitos = []
            st.session_state.lista_materiais_civil = []
            st.session_state.lista_materiais_eletricos = []
            st.rerun()
    else:
        st.info("Efetue os levantamentos na Aba 1 (Civil) e Aba 2 (Elétrica) para liberar o PDF separado.")
