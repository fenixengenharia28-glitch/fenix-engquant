import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

if "lista_materiais_civil" not in st.session_state: st.session_state.lista_materiais_civil = []
if "lista_materiais_eletricos" not in st.session_state: st.session_state.lista_materiais_eletricos = []
if "comodos" not in st.session_state: st.session_state.comodos = []
if "funcionarios" not in st.session_state:
    st.session_state.funcionarios = [
        {"Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA/RE": "MG20231045"},
        {"Nome": "Marcos Souza", "Função": "Eletricista Instalador", "CREA/RE": "RE-9942"}
    ]

with st.sidebar:
    st.markdown(
        """
        <div style="background-color:#1E3A8A; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <h2 style="color:#FFFFFF; margin:0; font-family:sans-serif; letter-spacing: 2px;">⚡ FÊNIX</h2>
            <p style="color:#0D9488; margin:0; font-size:11px; font-weight:bold; letter-spacing: 1px;">ENGENHARIA & SISTEMAS</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.write("### 👥 Cadastro de Funcionários")
    with st.form("form_func", clear_on_submit=True):
        f_nome = st.text_input("Nome do Colaborador:")
        f_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista"])
        f_reg = st.text_input("Registro (CREA / RE):")
        if st.form_submit_button("Cadastrar Funcionário"):
            if f_nome and f_reg:
                st.session_state.funcionarios.append({"Nome": f_nome, "Função": f_func, "CREA/RE": f_reg})
                st.success("Funcionário Cadastrado!")
                st.rerun()
    st.write("---")
    st.dataframe(pd.DataFrame(st.session_state.funcionarios), use_container_width=True)
st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP Corporativo: Memorial Integrado de Engenharia, QDC e Alvenaria")
st.markdown("---")

if "df_circuitos" not in st.session_state:
    st.session_state.df_circuitos = pd.DataFrame([
        {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO - Quarto 1, Corredor, Quarto 2", "POT_W": 1180, "TIPO": "Monofásico", "DISJ": "16A", "CURVA": "B", "COND": "1.5 mm²", "FASE": "R", "TENSÃO": 127},
        {"CIRC": "2", "DESCRIÇÃO": "ILUMINAÇÃO - Sala, Cozinha, Banheiro", "POT_W": 640, "TIPO": "Monofásico", "DISJ": "16A", "CURVA": "B", "COND": "1.5 mm²", "FASE": "S", "TENSÃO": 127},
        {"CIRC": "3", "DESCRIÇÃO": "TUG - Quarto 1, Quarto 2", "POT_W": 480, "TIPO": "Monofásico", "DISJ": "20A", "CURVA": "C", "COND": "2.5 mm²", "FASE": "R", "TENSÃO": 127},
        {"CIRC": "4", "DESCRIÇÃO": "TUG - Cozinha e Área de Serviço", "POT_W": 1760, "TIPO": "Monofásico", "DISJ": "32A", "CURVA": "C", "COND": "4.0 mm²", "FASE": "S", "TENSÃO": 127},
        {"CIRC": "5", "DESCRIÇÃO": "TUE - Chuveiro Master", "POT_W": 7800, "TIPO": "Bifásico", "DISJ": "40A", "CURVA": "B", "COND": "6.0 mm²", "FASE": "RS", "TENSÃO": 220}
    ])

CONCESSIONARIAS = {
    "CEMIG (Minas Gerais)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1"},
    "ENEL (São Paulo)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001"},
    "ENEL (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001"},
    "CPFL (Paulista)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13"},
    "LIGHT (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT"}
}
def recalcular_materiais_brutos_eletricos(area_ref, tipo_ent, dj_pad, circuitos_list):
    if not circuitos_list:
        st.session_state.lista_materiais_eletricos = []
        return
    materiais = [
        {"Etapa": "Infra Elétrica", "Material": "Eletroduto PVC Flexível Corrugado 3/4 (Rolo 50m)", "Quantidade": max(1, math.ceil(area_ref * 1.8 / 50.0)), "Unidade": "rl"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir Plástica 4x2", "Quantidade": max(4, math.ceil(area_ref * 0.45)), "Unidade": "un"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir Plástica 4x4", "Quantidade": max(2, math.ceil(area_ref * 0.15)), "Unidade": "un"}
    ]
    polos_circuitos = 0
    contagem_dj = {}
    for c in circuitos_list:
        tipo_c = c.get("TIPO", "Monofásico")
        disj_c = c.get("DISJ", "20A")
        polos = 2 if "Bifásico" in str(tipo_c) else 1
        polos_circuitos += polos
        chave_dj = f"Disjuntor DIN {tipo_c} {disj_c}"
        contagem_dj[chave_dj] = contagem_dj.get(chave_dj, 0) + 1
    for dj_nome, qtd in contagem_dj.items():
        materiais.append({"Etapa": "Dispositivos QDC", "Material": dj_nome, "Quantidade": qtd, "Unidade": "un"})
    
    n_fases = 1 if tipo_ent == "Monofásico" else (2 if tipo_ent == "Bifásico" else 3)
    espaco_din = polos_circuitos + n_fases + (2 if n_fases == 1 else 4) + n_fases
    reserva = 2 if polos_circuitos <= 6 else (3 if polos_circuitos <= 12 else 4)
    total_modulos = espaco_din + reserva
    padrao_qdc = 12 if total_modulos <= 12 else (18 if total_modulos <= 18 else (24 if total_modulos <= 24 else (36 if total_modulos <= 36 else 48)))
    
    materiais.append({"Etapa": "Dispositivos QDC", "Material": f"Quadro de Distribuição (QDC) Embutir {padrao_qdc} Módulos DIN Completo (NBR 5410)", "Quantidade": 1, "Unidade": "un"})
    st.session_state.lista_materiais_eletricos = materiais

tab_civil, tab_eletrica, tab_pdf = st.tabs(["🧱 1. Quantitativo Civil", "⚡ 2. Quadro de Cargas (QDC)", "📥 3. Fechamento & Relatório PDF"])
def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list)
    altura_d = max(140, (n_circ * 30) + 50)
    d = Drawing(720, altura_d)
    d.add(Line(20, altura_d - 30, 100, altura_d - 30, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 22, f"Entrada: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(100, altura_d - 30, 115, altura_d - 40, strokeColor=colors.black, strokeWidth=2))
    d.add(String(100, altura_d - 22, f"Geral {dj_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Line(140, altura_d - 30, 140, 15, strokeColor=colors.black, strokeWidth=2))
    d.add(Line(115, altura_d - 30, 140, altura_d - 30, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 55) - (idx * 30)
        d.add(Circle(140, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(140, y, 190, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(190, y, 205, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(185, y + 5, f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(205, y, 240, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(212, y + 5, str(c.get('COND','2.5 mm²')), fontSize=7, fillColor=colors.HexColor('#2563EB')))
        d.add(String(250, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO','Circuito Custom'))[:35]} - {c.get('FASE','R')} ({c.get('POT_W',1000)}W)", fontSize=7.5, fontName='Helvetica'))
    return d

def gerar_desenho_multifilar(circuitos_list):
    n_circ = len(circuitos_list)
    altura_d = max(180, (n_circ * 35) + 60)
    d = Drawing(720, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 220, 250, 280, 310
    d.add(Line(x_fase1, altura_d - 20, x_fase1, 15, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(x_fase2, altura_d - 20, x_fase2, 15, strokeColor=colors.HexColor('#9333EA'), strokeWidth=1.5))
    d.add(Line(x_neutro, altura_d - 20, x_neutro, 15, strokeColor=colors.blue, strokeWidth=1.5))
    d.add(Line(x_terra, altura_d - 20, x_terra, 15, strokeColor=colors.HexColor('#16A34A'), strokeWidth=1.2))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 50) - (idx * 35)
        if idx % 2 == 0:
            d.add(Rect(30, y - 10, 130, 24, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1))
            d.add(String(35, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:16]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(Line(160, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
        else:
            d.add(Rect(360, y - 10, 130, 24, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(365, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:16]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(Line(360, y, x_neutro, y, strokeColor=colors.blue, strokeWidth=0.8))
    return d
with tab_civil:
    st.write("### 🧱 Configuração do Método de Levantamento Estrutural")
    metodo_calculo = st.radio("Escolha a metodologia de cubagem civil:", ["Cálculo por Metro Quadrado (Global)", "Prancha Customizada Cômodo por Cômodo"], horizontal=True)
    st.markdown("---")
    
    if metodo_calculo == "Cálculo por Metro Quadrado (Global)":
        c_civ1, c_civ2, c_civ3 = st.columns(3)
        with c_civ1:
            area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0, step=5.0)
            perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0)
        with c_civ2:
            pe_direito = st.number_input("Altura do Pé-Direito (m):", min_value=1.5, value=2.8, step=0.1)
            qtd_sapatas = st.number_input("Quantidade de Sapatas Isoladas:", min_value=0, value=12, step=1)
        with c_civ3:
            tipo_tijolo = st.selectbox("Tipo de Alvenaria:", ["Tijolo Cerâmico Baiano", "Bloco de Concreto"])
            espessura_contrapiso = st.number_input("Espessura do Contrapiso (cm):", min_value=3.0, value=5.0, step=0.5)

        if st.button("📊 Processar Cubagem Global"):
            st.session_state.lista_materiais_civil = [
                {"Etapa": "Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": round(qtd_sapatas * 0.4, 2), "Unidade": "m³"},
                {"Etapa": "Alvenaria", "Material": "Tijolos/Blocos de Vedação", "Quantidade": math.ceil(perimetro_paredes * pe_direito * 25), "Unidade": "un"},
                {"Etapa": "Acabamento Civil", "Material": "Piso Porcelanato Retificado Comercial", "Quantidade": round(area_obra * 1.1, 1), "Unidade": "m²"}
            ]
            st.rerun()
    else:
        st.write("#### 🏠 Lançamento de Ambientes da Prancha Customizada")
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1: nome_c = st.text_input("Nome do Cômodo:", placeholder="Ex: Quarto Master")
        with cc2: comp_c = st.number_input("Comprimento (m):", min_value=0.5, value=4.0, step=0.5)
        with cc3: larg_c = st.number_input("Largura (m):", min_value=0.5, value=3.5, step=0.5)
        with cc4: port_c = st.number_input("Janelas/Portas no Cômodo:", min_value=1, value=2, step=1)
        
        if st.button("➕ Encaixar Cômodo na Prancha"):
            if nome_c:
                st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c, "Esquadrias": port_c})
                st.rerun()
                
        if st.session_state.comodos:
            st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)
            if st.button("📊 Processar Prancha de Ambientes"):
                area_total = sum(c["Comprimento"] * c["Largura"] for c in st.session_state.comodos)
                st.session_state.lista_materiais_civil = [
                    {"Etapa": "Estrutura e Piso (Prancha)", "Material": "Concreto Fck=20MPa (Contrapiso)", "Quantidade": round(area_total * 0.05, 2), "Unidade": "m³"},
                    {"Etapa": "Acabamento (Prancha)", "Material": "Revestimento Cerâmico de Piso", "Quantidade": round(area_total * 1.1, 1), "Unidade": "m²"}
                ]
                area_obra = area_total
                st.rerun()
                
    if st.session_state.lista_materiais_civil:
        st.dataframe(pd.DataFrame(st.session_state.lista_materiais_civil), use_container_width=True)
with tab_eletrica:
    st.write("### 🎛️ Mapeamento e Configuração de Circuitos Ilimitados")
    concessionaria_sel = st.selectbox("🔌 Concessionária Distribuidora:", list(CONCESSIONARIAS.keys()), key="sb_concessionaria_el")
    dados_c = CONCESSIONARIAS[concessionaria_sel]
    
    st.write("💡 *Dica: Clique no '+' no rodapé da tabela para adicionar novos circuitos de forma ilimitada.*")
    st.session_state.df_circuitos = st.data_editor(st.session_state.df_circuitos, num_rows="dynamic", use_container_width=True)
    circuitos_validos = st.session_state.df_circuitos.to_dict(orient="records")

try: area_obra_ref = area_obra
except: area_obra_ref = 70.0

pot_total = 0
for c in circuitos_validos:
    p_w = c.get("POT_W", 0)
    if str(p_w).isdigit(): pot_total += int(p_w)

tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
detalhe_caixa = "Caixa Tipo 'F'"

recalcular_materials = recalcular_materiais_brutos_eletricos(area_obra_ref, tipo_entrada, dj_padrao, circuitos_validos)
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
    
    func_txt = " | ".join([f"{f['Função']}: {f['Nome']} ({f['CREA/RE']})" for f in st.session_state.funcionarios])
    elementos.append(Paragraph(f"<b>Responsáveis Técnicos:</b> {func_txt}", estilo_celula_esq))
    
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro</b>", estilo_celula), Paragraph("<b>Especificação</b>", estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento", estilo_celula), Paragraph(tipo_entrada, estilo_celula_esq)],
        [Paragraph("Cabo do Ramal", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[240.0, 500.0])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)

    circuitos_validos = st.session_state.df_circuitos.to_dict(orient="records")
    if circuitos_validos:
        elementos.append(PageBreak())
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas e Distribuição por Fase", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO", "POT ILUM", "POT ESP", "POT (W)", "POT (VA)", "DEM (%)", "CORR (A)", "DISJ", "COND", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        
        tot_r, tot_s = 0, 0
        for idx, c in enumerate(circuitos_validos):
            p_w_val = int(c.get("POT_W", 0)) if str(c.get("POT_W", 0)).isdigit() else 0
            fase_c = str(c.get("FASE", "R"))
            r_val = p_w_val if fase_c == "R" else (p_w_val//2 if "RS" in fase_c else 0)
            s_val = p_w_val if fase_c == "S" else (p_w_val//2 if "RS" in fase_c else 0)
            tot_r += r_val
            tot_s += s_val
            dados_qdc_pdf.append([
                Paragraph(str(c.get("CIRC", idx+1)), estilo_celula), Paragraph(str(c.get("DESCRIÇÃO","")), estilo_celula_esq),
                Paragraph(str(p_w_val) if "ILUM" in str(c.get("DESCRIÇÃO","")).upper() else "0", estilo_celula),
                Paragraph(str(p_w_val) if "TUE" in str(c.get("DESCRIÇÃO","")).upper() else "0", estilo_celula),
                Paragraph(str(p_w_val), estilo_celula), Paragraph(str(p_w_val), estilo_celula),
                Paragraph("80%", estilo_celula), Paragraph("10A", estilo_celula),
                Paragraph(f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", estilo_celula), Paragraph(str(c.get("COND","2.5")), estilo_celula),
                Paragraph(fase_c, estilo_celula), Paragraph(f"{c.get('TENSÃO',127)}V", estilo_celula),
                Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)
            ])
            
        texto_centralizado_modelo = f"<b>Potência Instalada Total: {pot_total} W | {tot_r}VA | {tot_s}VA</b>"
        dados_qdc_pdf.append([Paragraph(texto_centralizado_modelo, estilo_celula)] + [""] * 13)
        
        t_qdc = Table(dados_qdc_pdf, colWidths=[32.0, 180.0, 42.0, 42.0, 42.0, 42.0, 42.0, 42.0, 40.0, 45.0, 35.0, 42.0, 58.0, 58.0])
        t_qdc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
            ('SPAN', (0,-1), (-1,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 2.5),
            ('ALIGN', (0,-1), (-1,-1), 'CENTER')
        ]))
        elementos.append(t_qdc)
    if st.session_state.lista_materiais_civil:
        elementos.append(PageBreak())
        elementos.append(Paragraph(f"2. Memorial Quantitativo da Alvenaria Estrutural ({metodo_calculo})", estilo_sub))
        dados_civil = [[Paragraph("<b>Etapa Civil</b>", estilo_celula), Paragraph("<b>Material Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
        for mat in st.session_state.lista_materiais_civil:
            dados_civil.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
        t_civ = Table(dados_civil, colWidths=[120.0, 400.0, 140.0, 80.0])
        t_civ.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_civ)

    if circuitos_validos:
        elementos.append(PageBreak())
        elementos.append(Paragraph("3. Diagrama Unifilar e Distribuição de Barramentos", estilo_sub))
        elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, circuitos_validos))
        elementos.append(PageBreak())
        elementos.append(Paragraph("4. Esquema Técnico Multifilar de Bornes", estilo_sub))
        elementos.append(gerar_desenho_multifilar(circuitos_validos))

    elementos.append(PageBreak())
    elementos.append(Paragraph("5. Diretrizes Técnicas Regulamentares", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴🟡 PRETO / VERMELHO / AMARELO: Condutores de Fase | ⚪⚪ BRANCO / CINZA: Condutores de Retorno (Iluminação).", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados nesta tampa de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente. Se ele não desarmar e desligar a energia da casa, substitua-o imediatamente (risco de choque).", estilo_aviso_corpo),
        Paragraph("• <b>Inspeção do DPS:</b> Verifique o indicador visual do protetor de surto regularmente. Janela verde indica funcionamento normal; janela vermelha exige substituição imediata do módulo.", estilo_aviso_corpo),
        Paragraph("• <b>Conexões Seguras:</b> Toda manutenção ou adição de circuito deve utilizar terminais elétricos apropriados (tipo ilhós/tubular). Emendas simples dentro do QDC são proibidas.", estilo_aviso_corpo),
        Paragraph("• <b>Profissionalismo:</b> Qualquer alteração na rede elétrica residencial deve ser feita exclusivamente por um eletricista qualificado.", estilo_aviso_corpo)
    ]
    t_av = Table([[caviso]], colWidths=[740.0])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#D97706')), ('PADDING', (0,0), (-1,-1), 10)]))
    elementos.append(t_av)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Consolidado (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia.pdf", mime="application/pdf", key="btn_pdf_real")
