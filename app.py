import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("Desenho Gráfico de Diagramas Unifilar/Multifilar & Emissão de Documentação NBR 5410")
st.markdown("---")

# Banco de dados das concessionárias brasileiras
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

# Painel de entrada de dados
col_input1, col_input2 = st.columns(2)
with col_input1:
    concessionaria_sel = st.selectbox("🔌 Selecione a Concessionária de Energia:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria")
    dados_c = CONCESSIONARIAS[concessionaria_sel]
with col_input2:
    area_imovel = st.number_input("🏡 Área Construída Total (m²):", min_value=10.0, value=70.0, step=5.0, key="ni_area_casa")

st.write("### 🎛️ Cargas Especiais (TUEs):")
c_tue1, c_tue2, c_tue3 = st.columns(3)
with c_tue1:
    qtd_chuveiro = st.number_input("Chuveiros Elétricos (7500W):", min_value=0, value=1, step=1, key="tue_chuveiro")
with c_tue2:
    qtd_ar = st.number_input("Aparelhos de Ar Condicionado (2000W):", min_value=0, value=1, step=1, key="tue_ar")
with c_tue3:
    tem_forno = st.checkbox("Forno Elétrico / Micro-ondas (2500W)", value=True, key="tue_forno")

# --- PROCESSAMENTO DOS CÁLCULOS NBR 5410 ---
pot_ilum = 1500 if area_imovel <= 60 else 1500 + (math.ceil((area_imovel - 60)/15) * 500)
pot_tug = 3000 if area_imovel <= 60 else 3000 + (math.ceil((area_imovel - 60)/20) * 600)
pot_tue = (qtd_chuveiro * 7500) + (qtd_ar * 2000) + (2500 if tem_forno else 0)
pot_total = pot_ilum + pot_tug + pot_tue

if pot_total <= dados_c["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Monofásico", "10.0 mm²", "40 A"
elif pot_total <= dados_c["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
else:
    tipo_entrada, cabo_padrao, dj_padrao = "Trifásico", "25.0 mm²", "80 A"

# Geração automática da árvore de circuitos
lista_circuitos = []
lista_circuitos.append({"Circuito": "C1", "Descrição": "Iluminação Geral", "Carga (W)": pot_ilum, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"})

n_tugs = 2 if area_imovel > 80 else 1
for i in range(n_tugs):
    lista_circuitos.append({"Circuito": f"C{2+i}", "Descrição": f"Tomadas Gerais (TUGs) {i+1}", "Carga (W)": round(pot_tug/n_tugs), "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "20 A", "Tipo": "Monofásico"})

cont = 1 + n_tugs
if qtd_chuveiro > 0:
    for i in range(qtd_chuveiro):
        cont += 1
        lista_circuitos.append({"Circuito": f"C{cont}", "Descrição": f"Chuveiro Elétrico {i+1}", "Carga (W)": 7500, "Tensão (V)": dados_c["linha"], "Cabo": "6.0 mm²", "Disjuntor": "40 A", "Tipo": "Bifásico"})
if qtd_ar > 0:
    for i in range(qtd_ar):
        cont += 1
        lista_circuitos.append({"Circuito": f"C{cont}", "Descrição": f"Ar Condicionado {i+1}", "Carga (W)": 2000, "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "16 A", "Tipo": "Monofásico"})
if tem_forno:
    cont += 1
    lista_circuitos.append({"Circuito": f"C{cont}", "Descrição": "Forno / Micro-ondas", "Carga (W)": 2500, "Tensão (V)": dados_c["fase"], "Cabo": "4.0 mm²", "Disjuntor": "25 A", "Tipo": "Monofásico"})

df_circuitos = pd.DataFrame(lista_circuitos)

AVISO_NBR = (
    "ADVERTÊNCIA: ADICIONAR OU MODIFICAR COMPONENTES DOS CIRCUITOS ELÉTRICOS PODE GERAR RISCO DE SOBRECARGA OU "
    "CHOQUE SE NÃO EXECUTADO POR PROFISSIONAL QUALIFICADO. MANTENHA AS PORTAS DO QUADRO SEMPRE FECHADAS. "
    "VERIFIQUE O FUNCIONAMENTO DO DISPOSITIVO DR MENSALMENTE APERTANDO O BOTÃO DE TESTE (T)."
)
# --- FUNÇÃO DO MOTOR GRÁFICO (DESENHO DOS DIAGRAMAS VETORIAIS) ---
def desenhar_unifilar_grafico():
    d = Drawing(540, 140)
    d.add(Rect(10, 10, 520, 120, fillColor=colors.HexColor('#F8FAFC'), strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))
    
    d.add(Rect(30, 45, 70, 50, fillColor=colors.HexColor('#1E3A8A'), strokeColor=None))
    d.add(String(65, 75, "DJ GERAL", textAnchor='middle', fillColor=colors.white, fontSize=8, fontName='Helvetica-Bold'))
    d.add(String(65, 55, dj_padrao, textAnchor='middle', fillColor=colors.white, fontSize=9, fontName='Helvetica-Bold'))
    
    d.add(Rect(120, 45, 70, 50, fillColor=colors.HexColor('#0D9488'), strokeColor=None))
    d.add(String(155, 75, "IDR GERAL", textAnchor='middle', fillColor=colors.white, fontSize=8, fontName='Helvetica-Bold'))
    d.add(String(155, 55, "63A / 30mA", textAnchor='middle', fillColor=colors.white, fontSize=8, fontName='Helvetica-Bold'))
    
    d.add(Rect(210, 45, 50, 50, fillColor=colors.HexColor('#EA580C'), strokeColor=None))
    d.add(String(235, 75, "DPS", textAnchor='middle', fillColor=colors.white, fontSize=8, fontName='Helvetica-Bold'))
    d.add(String(235, 55, "45 kA", textAnchor='middle', fillColor=colors.white, fontSize=8, fontName='Helvetica-Bold'))

    d.add(Line(100, 70, 120, 70, strokeColor=colors.HexColor('#475569'), strokeWidth=2))
    d.add(Line(190, 70, 210, 70, strokeColor=colors.HexColor('#475569'), strokeWidth=2))
    d.add(Line(260, 70, 290, 70, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=3))
    
    d.add(Rect(290, 35, 220, 70, fillColor=colors.HexColor('#EFF6FF'), strokeColor=colors.HexColor('#3B82F6'), strokeWidth=1))
    d.add(String(400, 75, "BARRAMENTO DE SAÍDA", textAnchor='middle', fillColor=colors.HexColor('#1E3A8A'), fontSize=9, fontName='Helvetica-Bold'))
    d.add(String(400, 50, f"Distribuição para {len(lista_circuitos)} Circuitos", textAnchor='middle', fillColor=colors.HexColor('#475569'), fontSize=8))
    
    return d

def desenhar_multifilar_grafico():
    largura_modulo = 55
    espacamento = 10
    total_circuitos = len(lista_circuitos)
    largura_total = (total_circuitos * (largura_modulo + espacamento)) + 20
    
    d = Drawing(max(540, largura_total), 150)
    d.add(Rect(5, 5, max(530, largura_total - 10), 140, fillColor=colors.HexColor('#F1F5F9'), strokeColor=colors.HexColor('#CBD5E1')))
    
    for idx, c in enumerate(lista_circuitos):
        x = 15 + idx * (largura_modulo + espacamento)
        
        d.add(Rect(x, 30, largura_modulo, 90, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1.5))
        d.add(Rect(x, 95, largura_modulo, 25, fillColor=colors.HexColor('#1E3A8A'), strokeColor=None))
        d.add(String(x + (largura_modulo/2), 103, c["Circuito"], textAnchor='middle', fillColor=colors.white, fontSize=10, fontName='Helvetica-Bold'))
        
        d.add(String(x + (largura_modulo/2), 75, c["Disjuntor"], textAnchor='middle', fillColor=colors.HexColor('#0F172A'), fontSize=9, fontName='Helvetica-Bold'))
        d.add(String(x + (largura_modulo/2), 55, c["Cabo"], textAnchor='middle', fillColor=colors.HexColor('#2563EB'), fontSize=8, fontName='Helvetica-Bold'))
        d.add(String(x + (largura_modulo/2), 40, f"{c['Carga (W)']}W", textAnchor='middle', fillColor=colors.HexColor('#64748B'), fontSize=7))
        
        d.add(Line(x + (largura_modulo/2), 120, x + (largura_modulo/2), 130, strokeColor=colors.red, strokeWidth=1.5))
        d.add(Line(x + (largura_modulo/2), 30, x + (largura_modulo/2), 15, strokeColor=colors.black, strokeWidth=1.5))

    return d
# --- GERADOR CONSOLIDADO DE DOCUMENTAÇÃO PDF ---
def gerar_pdf_projeto_completo():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=16, textColor=colors.HexColor('#1E3A8A'), spaceAfter=10)
    estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], fontSize=11, textColor=colors.HexColor('#0D9488'), spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
    estilo_corpo = ParagraphStyle('Corpo', parent=estilos['BodyText'], fontSize=9, spaceAfter=4)
    estilo_aviso = ParagraphStyle('Aviso', parent=estilos['BodyText'], fontSize=9, textColor=colors.HexColor('#B91C1C'), fontName='Helvetica-Bold', alignment=4)

    elementos = []
    
    elementos.append(Paragraph("<b>FÊNIX ENGENHARIA - ETIQUETA E DIAGRAMAS DO QDC</b>", estilo_titulo))
    elementos.append(Paragraph(f"<b>Especificações Técnicas:</b> {tipo_entrada} | {cabo_padrao} | Concessionária: {concessionaria_sel}", estilo_corpo))
    elementos.append(Spacer(1, 8))
    
    elementos.append(Paragraph("1. Tabela de Identificação de Circuitos (Para colar na porta do QDC)", estilo_sub))
    dados_tabela = [["Circ", "Descrição do Circuito", "Potência", "Tensão", "Cabo", "Disjuntor"]]
    for c in lista_circuitos:
        dados_tabela.append([c["Circuito"], c["Descrição"], f"{c['Carga (W)']}W", f"{c['Tensão (V)']}V", c["Cabo"], c["Disjuntor"]])
    
    # 70 + 230 + 60 + 60 + 60 + 60 = 540 (Largura exata da folha Letter)
    t = Table(dados_tabela, colWidths=[70, 230, 60, 60, 60, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'), 
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 12))
    
    elementos.append(Paragraph("2. Diagrama Unifilar Geral do Quadro de Distribuição", estilo_sub))
    elementos.append(desenhar_unifilar_grafico())
    elementos.append(Spacer(1, 12))
    
    elementos.append(Paragraph("3. Esquema Multifilar de Distribuição e Bornes (Disjuntores DIN)", estilo_sub))
    elementos.append(desenhar_multifilar_grafico())
    elementos.append(Spacer(1, 12))
    
    elementos.append(Paragraph("4. Advertência de Segurança Compulsória (Item 6.1.5.1)", estilo_sub))
    
    dados_aviso = [[Paragraph(f"<b>⚠️ {AVISO_NBR}</b>", estilo_aviso)]]
    t_aviso = Table(dados_aviso, colWidths=[540])
    t_aviso.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('BORDER', (0,0), (-1,-1), 1.5, colors.HexColor('#EF4444')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elementos.append(t_aviso)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- VISUALIZAÇÃO INTERATIVA NO STREAMLIT ---
st.markdown("---")
tab_dados, tab_visual = st.tabs(["📊 Tabela de Dados", "📐 Visualização Prévia dos Diagramas"])

with tab_dados:
    st.dataframe(df_circuitos, use_container_width=True)

with tab_visual:
    st.write("#### Prévia do Diagrama Unifilar Barras (Representação em Tela)")
    st.info(f"📦 ENTRADA PADRÃO ➔ DISJUNTOR GERAL {dj_padrao} ➔ IDR GERAL 63A/30mA ➔ BARRAMENTO FASE")
    
    st.write("#### Lista Sequencial do Trilho DIN (Multifilar Prancha)")
    linhas_preview = []
    for c in lista_circuitos:
        linhas_preview.append(f"| {c['Circuito']} | {c['Descrição']} | Dj: {c['Disjuntor']} | Cabo: {c['Cabo']} |")
    st.code("\n".join(linhas_preview))

# Emissão do PDF Real
st.markdown("---")
arquivo_pdf = gerar_pdf_projeto_completo()
st.download_button(
    label="📥 Baixar Diagramas Técnicos e Placa do QDC (PDF Pronto para Imprimir)",
    data=arquivo_pdf,
    file_name="diagramas_qdc_fenix_pro.pdf",
    mime="application/pdf",
    key="btn_pdf_qdc_grafico"
)
