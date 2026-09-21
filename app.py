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
st.subheader("Gerador Autônomo de Diagramas Unifilares e Multifilares Dinâmicos")
st.markdown("---")

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

# Inicialização da memória técnica do circuito
if "lista_circuitos" not in st.session_state:
    st.session_state.lista_circuitos = []

# Painel Superior de Controle
col_c1, col_c2 = st.columns(2)
with col_c1:
    concessionaria_sel = st.selectbox("🔌 Selecione a Concessionária de Energia:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria")
    dados_c = CONCESSIONARIAS[concessionaria_sel]
with col_c2:
    st.write("### 🛠️ Ações Globais de Escopo")
    if st.button("🏡 Injetar Kit Casa Completa (Autônomo)", key="btn_kit_casa"):
        st.session_state.lista_circuitos = [
            {"Circuito": "C1", "Descrição": "Torneira Elétrica (Cozinha)", "Carga (W)": 5000, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "32 A", "Tipo": "Bifásico"},
            {"Circuito": "C2", "Descrição": "Iluminação Cozinha e Copa", "Carga (W)": 800, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"},
            {"Circuito": "C3", "Descrição": "Iluminação Sala e Quartos", "Carga (W)": 1200, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"},
            {"Circuito": "C4", "Descrição": "Tomadas Cozinha e Área Serviço", "Carga (W)": 4400, "Tensão (V)": dados_c["fase"], "Cabo": "4.0 mm²", "Disjuntor": "25 A", "Tipo": "Monofásico"},
            {"Circuito": "C5", "Descrição": "Tomadas de Uso Geral (TUGs)", "Carga (W)": 2200, "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "20 A", "Tipo": "Monofásico"},
            {"Circuito": "C6", "Descrição": "Chuveiro Elétrico", "Carga (W)": 7500, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "40 A", "Tipo": "Bifásico"},
            {"Circuito": "C7", "Descrição": "Ar Condicionado", "Carga (W)": 2000, "Tensão (V)": dados_c["linha"], "Cabo": "2.5 mm²", "Disjuntor": "16 A", "Tipo": "Bifásico"}
        ]
        st.success("Kit residencial estruturado!")
        st.rerun()

st.markdown("---")
st.write("### ➕ Adicionar Circuitos Individualmente (Lançamento Customizado)")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
with col_a1:
    txt_desc = st.text_input("Descrição do Circuito:", placeholder="Ex: Chuveiro Suíte", key="ti_desc_manual")
with col_a2:
    num_carga = st.number_input("Carga (W):", min_value=100, value=2200, step=100, key="ni_carga_manual")
with col_a3:
    sel_tipo = st.selectbox("Tipo de Ligação:", ["Monofásico", "Bifásico"], key="sb_tipo_manual")
with col_a4:
    st.write(" ")
    if st.button("⚡ Inserir Circuito", key="btn_add_manual"):
        if txt_desc:
            c_num = len(st.session_state.lista_circuitos) + 1
            v_tensao = dados_c["linha"] if sel_tipo == "Bifásico" else dados_c["fase"]
            
            if num_carga >= 5000:
                cabo_calc, dj_calc = "6.0 mm²", "32 A" if num_carga < 7000 else "40 A"
            elif num_carga >= 3500:
                cabo_calc, dj_calc = "4.0 mm²", "25 A"
            else:
                cabo_calc, dj_calc = "2.5 mm²", "20 A"
            if "Iluminação" in txt_desc or num_carga <= 1000:
                cabo_calc, dj_calc = "1.5 mm²", "10 A"

            st.session_state.lista_circuitos.append({
                "Circuito": f"C{c_num}", "Descrição": txt_desc, "Carga (W)": num_carga,
                "Tensão (V)": v_tensao, "Cabo": cabo_calc, "Disjuntor": dj_calc, "Tipo": sel_tipo
            })
            st.success(f"Circuito C{c_num} indexado!")
            st.rerun()
# --- CÁLCULO GERAL DO PADRÃO DE ATENDIMENTO DA PLANILHA ---
pot_total = sum(c["Carga (W)"] for c in st.session_state.lista_circuitos)
if pot_total <= dados_c["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
elif pot_total <= dados_c["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"

# --- ALGORITMOS DOS MOTORES GRÁFICOS NORMATIVOS ---
def gerar_desenho_unifilar():
    n_circ = len(st.session_state.lista_circuitos)
    altura_d = max(160, (n_circ * 35) + 40)
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
    
    d.add(String(x_fase1, altura_d - 20, "R", textAnchor='middle', fontSize=9, fontName='Helvetica-Bold', fillColor=colors.red))
    d.add(String(x_fase2, altura_d - 20, "S", textAnchor='middle', fontSize=9, fontName='Helvetica-Bold', fillColor=colors.HexColor('#9333EA')))
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
            d.add(String(25, y + 2, c["Circuito"], fontSize=9, fontName='Helvetica-Bold', fillColor=colors.HexColor('#1E3A8A')))
            d.add(String(25, y - 8, c["Disjuntor"], fontSize=7, fontName='Helvetica'))
            d.add(String(105, y - 8, f"{c['Carga (W)']}W", textAnchor='end', fontSize=7, fillColor=colors.grey))
            
            d.add(Line(110, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
            d.add(Circle(x_fase1, y, 2.5, fillColor=colors.black, strokeColor=colors.black))
            
            if c["Tipo"] == "Bifásico":
                d.add(Line(110, y - 6, x_fase2, y - 6, strokeColor=colors.black, strokeWidth=1))
                d.add(Circle(x_fase2, y - 6, 2.5, fillColor=colors.black, strokeColor=colors.black))
        else:
            d.add(Rect(300, y - 12, 90, 28, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(305, y + 2, c["Circuito"], fontSize=9, fontName='Helvetica-Bold', fillColor=colors.HexColor('#0D9488')))
            d.add(String(305, y - 8, c["Disjuntor"], fontSize=7, fontName='Helvetica'))
            d.add(String(385, y - 8, f"{c['Carga (W)']}W", textAnchor='end', fontSize=7, fillColor=colors.grey))
            
            d.add(Line(290, y, x_fase2, y, strokeColor=colors.black, strokeWidth=1))
            d.add(Circle(x_fase2, y, 2.5, fillColor=colors.black, strokeColor=colors.black))
            
            if c["Tipo"] == "Monofásico":
                d.add(Line(290, y - 6, x_neutro, y - 6, strokeColor=colors.blue, strokeWidth=0.8))
                d.add(Circle(x_neutro, y - 6, 2, fillColor=colors.blue, strokeColor=colors.blue))

    return d
# --- ENGINE CONSOLIDADA DA DOCUMENTAÇÃO EM PDF ---
def gerar_pdf_etiqueta_qdc():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=15, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], fontSize=11, textColor=colors.HexColor('#0D9488'), spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
    estilo_corpo = ParagraphStyle('Corpo', parent=estilos['BodyText'], fontSize=8.5, spaceAfter=3)
    estilo_aviso = ParagraphStyle('Aviso', parent=estilos['BodyText'], fontSize=8.5, textColor=colors.HexColor('#B91C1C'), fontName='Helvetica-Bold', alignment=4)

    elementos = []
    
    elementos.append(Paragraph("<b>FÊNIX ENGENHARIA - PRANCHA DE MONTAGEM E SINALIZAÇÃO DO QDC</b>", estilo_titulo))
    elementos.append(Paragraph(f"<b>Configuração Geral:</b> Sistema {tipo_entrada} | Distribuidor Geral: {dj_padrao} | Base: {concessionaria_sel}", estilo_corpo))
    elementos.append(Spacer(1, 6))
    
    elementos.append(Paragraph("1. Tabela Descritiva das Cargas e Circuitos (Porta Interna)", estilo_sub))
    dados_tabela = [["Circ", "Descrição do Campo", "Potência", "Tensão", "Condutor", "Disjuntor"]]
    for c in st.session_state.lista_circuitos:
        dados_tabela.append([c["Circuito"], c["Descrição"], f"{c['Carga (W)']}W", f"{c['Tensão (V)']}V", c["Cabo"], c["Disjuntor"]])
    
    t = Table(dados_tabela, colWidths=[40, 220, 70, 70, 70, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('FONTSIZE', (0,0), (-1,-1), 8.5)
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("2. Diagrama Unifilar do Quadro Geral", estilo_sub))
    elementos.append(gerar_desenho_unifilar())
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("3. Diagrama Multifilar Completo de Distribuição de Barramentos", estilo_sub))
    elementos.append(gerar_desenho_multifilar())
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("4. Sinalização Compulsória de Segurança (NBR 5410)", estilo_sub))
    AVISO_TEXTO = [[Paragraph(f"<b>⚠️ {AVISO_NBR}</b>", estilo_aviso)]]
    t_aviso = Table(AVISO_TEXTO, colWidths=[540])
    t_aviso.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('BORDER', (0,0), (-1,-1), 1.5, colors.HexColor('#EF4444')),
        ('PADDING', (0,0), (-1,-1), 8)
    ]))
    elementos.append(t_aviso)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- PAINEL DE CONTROLE E EXIBIÇÃO NO BROWSER ---
if st.session_state.lista_circuitos:
    tab_painel, tab_acoes = st.tabs(["📊 Visualização dos Circuitos Ativos", "📥 Emissão de Documentos Técnicos"])
    
    with tab_painel:
        st.write(f"**Total de Circuitos Mapeados:** {len(st.session_state.lista_circuitos)}")
        st.dataframe(pd.DataFrame(st.session_state.lista_circuitos), use_container_width=True)
        if st.button("🗑️ Resetar Configurações / Limpar Quadro", key="btn_clear_quadro"):
            st.session_state.lista_circuitos = []
            st.rerun()
            
    with tab_acoes:
        st.write("### Clique no link abaixo para fazer o download da folha de montagem oficial:")
        arquivo_pdf = gerar_pdf_etiqueta_qdc()
        st.download_button(
            label="📥 Baixar Prancha com Diagramas e Adesivo do QDC (PDF)",
            data=arquivo_pdf,
            file_name="prancha_diagramas_qdc_fenix.pdf",
            mime="application/pdf",
            key="btn_download_pdf_final_oficial"
        )
else:
    st.info("Nenhum circuito elétrico configurado. Use o botão 'Gerar Kit Casa Completa' ou adicione itens manualmente acima.")
