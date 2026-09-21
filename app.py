import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página (Primeiro comando obrigatório)
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("Geração Autônoma de Engenharia Elétrica & Emissão de Documentação NBR 5410")
st.markdown("---")

# Banco de dados das concessionárias
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

# Painel de entrada
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
pot_demandada = pot_total * (0.52 if pot_total > 10000 else 0.65)

# Padrão de Entrada
if pot_total <= dados_c["limite_mono"]:
    tipo_entrada, cabo_padrao, dj_padrao, esquema_fase = "Monofásico", "10.0 mm²", "40 A", "[F + N + T]"
elif pot_total <= dados_c["limite_bi"]:
    tipo_entrada, cabo_padrao, dj_padrao, esquema_fase = "Bifásico", "16.0 mm²", "63 A", "[F1 + F2 + N + T]"
else:
    tipo_entrada, cabo_padrao, dj_padrao, esquema_fase = "Trifásico", "25.0 mm²", "80 A", "[F1 + F2 + F3 + N + T]"

# Geração automática da Tabela de Circuitos
lista_circuitos = []
lista_circuitos.append({"Circuito": "C1", "Descrição": "Iluminação Geral", "Carga (W)": pot_ilum, "Tensão (V)": dados_c["fase"], "Cabo": "1.5 mm²", "Disjuntor": "10 A", "Tipo": "Monofásico"})

n_tugs = 2 if area_imovel > 80 else 1
for i in range(n_tugs):
    lista_circuitos.append({"Circuito": f"C{2+i}", "Descrição": f"Tomadas Gerais (TUGs) - Setor {i+1}", "Carga (W)": round(pot_tug/n_tugs), "Tensão (V)": dados_c["fase"], "Cabo": "2.5 mm²", "Disjuntor": "20 A", "Tipo": "Monofásico"})

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

# Texto do Aviso Padrão NBR 5410 (Item 6.1.5.1)
AVISO_NBR = (
    "ADVERTÊNCIA: ADICIONAR OU MODIFICAR COMPONENTES DOS CIRCUITOS ELÉTRICOS PODE GERAR RISCO DE SOBRECARGA OU "
    "CHOQUE SE NÃO EXECUTADO POR PROFISSIONAL QUALIFICADO. MANTENHA AS PORTAS DO QUADRO SEMPRE FECHADAS. "
    "VERIFIQUE O FUNCIONAMENTO DO DISPOSITIVO DR MENSALMENTE APERTANDO O BOTÃO DE TESTE (T)."
)

# --- INTERFACE GRÁFICA DO APP ---
st.markdown("---")
t1, t2, t3 = st.tabs(["📊 Quadro de Cargas", "📐 Diagramas Unifilar / Multifilar", "🛡️ Padrão e Segurança"])

with t1:
    st.write("### Relação de Circuitos Dimensionados")
    st.dataframe(df_circuitos, use_container_width=True)

with t2:
    st.write("### 📜 Esquemas Representativos para Etiqueta do QDC")
    
    st.write("**Diagrama Unifilar (Estrutura do Barramento Principal)**")
    unifilar_texto = f"📦 ENTRADA PADRÃO ({tipo_entrada}) ➔ DISJUNTOR GERAL {dj_padrao} ➔ IDR GERAL 63A/30mA ➔ BARRAMENTO FASE ➔ DISJUNTORES DOS CIRCUITOS"
    st.code(unifilar_texto)
    
    st.write("**Diagrama Multifilar de Distribuição dos Bornes**")
    multifilar_linhas = [f"⚡ Linha de Entrada Alimentação: {esquema_fase} - Cabos: {cabo_padrao}"]
    for c in lista_circuitos:
        multifilar_linhas.append(f"  └─► [{c['Circuito']}] - {c['Descrição']} ➔ Disjuntor {c['Disjuntor']} ➔ Saída: Cabo {c['Cabo']}")
    st.code("\n".join(multifilar_linhas))

with t3:
    st.write("### Parâmetros de Homologação e Segurança")
    st.info(f"**Concessionária:** {concessionaria_sel} | **Tipo:** {tipo_entrada} | **Cabo Padrão:** {cabo_padrao}")
    st.warning(f"**Aviso Obrigatório NBR 5410:**\n{AVISO_NBR}")

# --- GERADOR AUTOMÁTICO DE PDF (ReportLab) ---
def gerar_pdf_projeto():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    
    # Customização de estilos
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=18, textColor=colors.HexColor('#1E3A8A'), spaceAfter=12)
    estilo_sub = ParagraphStyle('Sub', parent=estilos['Heading2'], fontSize=12, textColor=colors.HexColor('#0D9488'), spaceBefore=10, spaceAfter=6)
    estilo_corpo = ParagraphStyle('Corpo', parent=estilos['BodyText'], fontSize=9, spaceAfter=4)
    estilo_aviso = ParagraphStyle('Aviso', parent=estilos['BodyText'], fontSize=9, textColor=colors.HexColor('#B91C1C'), fontName='Helvetica-Bold')

    elementos = []
    
    # Cabeçalho
    elementos.append(Paragraph("<b>FÊNIX ENGENHARIA - MEMORIAL TÉCNICO ELÉTRICO</b>", estilo_titulo))
    elementos.append(Paragraph(f"<b>Homologação Base:</b> {concessionaria_sel} | <b>Área da Residência:</b> {area_imovel} m²", estilo_corpo))
    elementos.append(Spacer(1, 10))
    
    # Tabela de circuitos
    elementos.append(Paragraph("<b>1. Mapeamento de Carga e Quadro de Circuitos</b>", estilo_sub))
    dados_tabela = [["Circ", "Descrição", "Carga", "Tensão", "Cabo", "Disjuntor", "Tipo"]]
    for c in lista_circuitos:
        dados_tabela.append([c["Circuito"], c["Descrição"], f"{c['Carga (W)']}W", f"{c['Tensão (V)']}V", c["Cabo"], c["Disjuntor"], c["Tipo"]])
    
    t = Table(dados_tabela, colWidths=[40, 160, 50, 50, 60, 60, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 15))
    
    # Diagramas
    elementos.append(Paragraph("<b>2. Diagrama Unifilar do Quadro</b>", estilo_sub))
    elementos.append(Paragraph(unifilar_texto, estilo_corpo))
    elementos.append(Spacer(1, 10))
    
    elementos.append(Paragraph("<b>3. Diagrama Multifilar (Esquema de Bornes e Ligações)</b>", estilo_sub))
    for lin in multifilar_linhas:
        elementos.append(Paragraph(lin.replace(" ", "&nbsp;"), estilo_corpo))
    elementos.append(Spacer(1, 15))
    
    # Padrão de Entrada
    elementos.append(Paragraph("<b>4. Especificações do Padrão de Entrada Técnico</b>", estilo_sub))
    elementos.append(Paragraph(f"• <b>Tipo de Fornecimento:</b> {tipo_entrada}", estilo_corpo))
    elementos.append(Paragraph(f"• <b>Condutores do Padrão:</b> {cabo_padrao} | <b>Disjuntor Geral da Caixa:</b> {dj_padrao}", estilo_corpo))
    elementos.append(Paragraph("• <b>Dispositivos de Proteção Internos:</b> IDR Geral 63A - 30mA e DPS Classe II 45kA", estilo_corpo))
    elementos.append(Spacer(1, 15))
    
    # Aviso NBR
    elementos.append(Paragraph("<b>⚠️ ADVERTÊNCIA NORMATIVA (NBR 5410):</b>", estilo_sub))
    elementos.append(Paragraph(AVISO_NBR, estilo_aviso))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# Botão de download do PDF na interface
st.markdown("---")
pdf_file = gerar_pdf_projeto()
st.download_button(
    label="📥 Baixar Projeto Elétrico Completo e Diagramas (PDF)",
    data=pdf_file,
    file_name=f"projeto_eletrico_fenix_{concessionaria_sel.split(' ')[0].lower()}.pdf",
    mime="application/pdf",
    key="btn_download_pdf_real"
)
