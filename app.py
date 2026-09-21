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

if "lista_circuitos_calc" not in st.session_state: st.session_state.lista_circuitos_calc = []
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
st.subheader("ERP Corporativo: Dimensionamento de Condutores, QDC e Alvenaria")
st.markdown("---")

CONCESSIONARIAS = {
    "CEMIG (Minas Gerais)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1"},
    "ENEL (São Paulo)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001"},
    "ENEL (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001"},
    "CPFL (Paulista)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13"},
    "LIGHT (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT"}
}
def calcular_bitola_e_disjuntor(potencia, tensao, comprimento, tipo_carga):
    # 1. Corrente de Projeto (Ib)
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.8
    ib = potencia / (tensao * fp)
    
    # 2. Bitola Mínima Obrigatória por Norma e Capacidade de Corrente (PVC em Eletroduto)
    if tipo_carga == "Iluminação":
        bitola_inicial = 1.5
        corrente_max_cabo = 17.5
    else:
        bitola_inicial = 2.5
        corrente_max_cabo = 24.0
        
    # Ajuste de bitola por capacidade térmica de corrente (Tabela 36 - NBR 5410)
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    
    bitola_final = bitola_inicial
    iz_cabo = corrente_max_cabo
    
    for b, cap in zip(bitolas_comerciais, capacidades_corrente):
        if b >= bitola_inicial and cap >= ib:
            bitola_final = b
            iz_cabo = cap
            break

    # 3. Verificação por Queda de Tensão Admissível (Limite de 2% para circuitos terminais)
    # Queda de tensão aproximada em condutores de cobre (Fórmula simplificada: dV% = (2 * rho * L * Ib * 100) / (V * S))
    rho = 1 / 58.0  # Resistividade do cobre
    while True:
        dv_perc = (2 * rho * comprimento * ib * 100) / (tensao * bitola_final)
        if dv_perc <= 2.0 or bitola_final >= 16.0:
            break
        # Se ultrapassar 2%, sobe para a próxima bitola comercial
        idx = bitolas_comerciais.index(bitola_final)
        if idx < len(bitolas_comerciais) - 1:
            bitola_final = bitolas_comerciais[idx + 1]
            iz_cabo = capacidades_corrente[idx + 1]
        else:
            break

    # 4. Dimensionamento do Disjuntor (Critério: Ib <= In <= Iz)
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= iz_cabo:
            disjuntor_final = dj
            break
        elif dj >= ib: # Margem de segurança caso o cabo esteja muito próximo do limite
            disjuntor_final = dj
            break
            
    curva = "B" if tipo_carga == "Iluminação" else "C"
    return bitola_final, disjuntor_final, curva, round(ib, 2)
def recalcular_materiais_brutos_eletricos(area_ref, tipo_ent, dj_pad, circuitos_list):
    if not circuitos_list:
        st.session_state.lista_materiais_eletricos = []
        return
    materiais = [
        {"Etapa": "Infra Elétrica", "Material": "Eletroduto PVC Flexível Corrugado 3/4 (Rolo 50m)", "Quantidade": max(1, math.ceil(area_ref * 1.8 / 50.0)), "Unidade": "rl"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir Plástica 4x2", "Quantidade": max(4, math.ceil(area_ref * 0.45)), "Unidade": "un"},
        {"Etapa": "Infra Elétrica", "Material": "Caixa de Passagem Embutir Plástica 4x4", "Quantidade": max(2, math.ceil(area_ref * 0.15)), "Unidade": "un"}
    ]
    polos_circuitos = sum(2 if "Bifásico" in c["TIPO"] else 1 for c in circuitos_list)
    n_fases = 1 if tipo_ent == "Monofásico" else (2 if tipo_ent == "Bifásico" else 3)
    total_modulos = polos_circuitos + n_fases + (2 if n_fases == 1 else 4) + n_fases + 3
    padrao_qdc = 12 if total_modulos <= 12 else (18 if total_modulos <= 18 else (24 if total_modulos <= 24 else (36 if total_modulos <= 36 else 48)))
    
    materiais.append({"Etapa": "Dispositivos QDC", "Material": f"Quadro de Distribuição (QDC) Embutir {padrao_qdc} Módulos DIN Completo (NBR 5410)", "Quantidade": 1, "Unidade": "un"})
    st.session_state.lista_materiais_eletricos = materiais
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
    st.write("### 🎛️ Modos de Cálculo do Sistema de Cabeamento e Proteção")
    modo_eletrico = st.radio("Escolha o modo de lançamento elétrico:", ["Fazer o cálculo da casa toda (Planta Modelo Otimizada)", "Lançar circuitos separados (Cálculo Individual Automático)"], horizontal=True)
    concessionaria_sel = st.selectbox("🔌 Concessionária Distribuidora de Energia:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]
    st.markdown("---")
    
    if modo_eletrico == "Fazer o cálculo da casa toda (Planta Modelo Otimizada)":
        st.write("#### 🏠 Cubagem Computacional da Prancha de Cargas Completa")
        st.write("O sistema aplicará a NBR 5410 para dimensionar automaticamente todos os condutores por capacidade de condução de corrente e queda de tensão.")
        if st.button("🚀 Processar e Dimensionar Casa Toda"):
            planta_modelo = [
                {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO - Quartos e Corredor", "POT_W": 1180, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 15},
                {"CIRC": "2", "DESCRIÇÃO": "ILUMINAÇÃO - Cozinha e Sala", "POT_W": 640, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 12},
                {"CIRC": "3", "DESCRIÇÃO": "TUG - Dormitórios", "POT_W": 600, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 18},
                {"CIRC": "4", "DESCRIÇÃO": "TUG - Sala e Varanda", "POT_W": 1300, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 14},
                {"CIRC": "5", "DESCRIÇÃO": "TUG - Cozinha (Tomadas Potentes)", "POT_W": 2200, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 10},
                {"CIRC": "6", "DESCRIÇÃO": "TUE - Chuveiro Banheiro Social", "POT_W": 5500, "TIPO": "Monofásico", "TENSÃO": dados_c["fase"], "COMP": 22},
                {"CIRC": "7", "DESCRIÇÃO": "TUE - Chuveiro Master Suíte", "POT_W": 7800, "TIPO": "Bifásico", "TENSÃO": dados_c["linha"], "COMP": 25}
            ]
            st.session_state.lista_circuitos_calc = []
            for item in planta_modelo:
                bitola, disj, curva, ib_c = calcular_bitola_e_disjuntor(item["POT_W"], item["TENSÃO"], item["COMP"], item["DESCRIÇÃO"])
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": item["CIRC"], "DESCRIÇÃO": item["DESCRIÇÃO"], "POT_W": item["POT_W"], "TIPO": item["TIPO"],
                    "DISJ": f"{disj}A", "CURVA": curva, "COND": f"{bitola} mm²", "FASE": "RS" if item["TIPO"]=="Bifásico" else "R",
                    "TENSÃO": item["TENSÃO"], "IB": ib_c, "COMP": item["COMP"]
                })
            st.success("Planta modelo calculada com sucesso!")
            st.rerun()
    else:
        st.write("#### 🛠️ Lançamento de Circuito Individualizado com Bitola e Disjuntor Automáticos")
        col_an1, col_an2, col_an3, col_an4 = st.columns(4)
        with col_an1:
            desc_c = st.text_input("Descrição do Circuito Terminal:", placeholder="Ex: Ar Condicionado Suíte")
            tipo_carga_sel = st.selectbox("Tipo de Carga:", ["Iluminação", "TUG - Tomada Uso Geral", "TUE - Tomada Especial"])
        with col_an2:
            pot_w_c = st.number_input("Potência Total Adensada (W):", min_value=100, value=2200, step=100)
        with cc_v := col_an3:
            tipo_ligacao = st.selectbox("Tipo de Ligação Elétrica:", ["Monofásico (127V/220V)", "Bifásico (220V/380V)"])
            v_utilizada = dados_c["linha"] if "Bifásico" in tipo_ligacao else dados_c["fase"]
        with col_an4:
            comprimento_m = st.number_input("Distância do QDC até a Carga (m):", min_value=1, value=15, step=1)
            
        if st.button("➕ Calcular e Encaixar no Barramento"):
            if desc_c:
                c_num_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
                tipo_txt = "Bifásico" if "Bifásico" in tipo_ligacao else "Monofásico"
                fase_atrib_txt = "RS" if tipo_txt == "Bifásico" else "R"
                
                # Chamada do Motor Normativo NBR 5410
                bitola, disj, curva, ib_c = calcular_bitola_e_disjuntor(pot_w_c, v_utilizada, comprimento_m, tipo_carga_sel)
                
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": c_num_idx, "DESCRIÇÃO": desc_c, "POT_W": pot_w_c, "TIPO": tipo_txt,
                    "DISJ": f"{disj}A", "CURVA": curva, "COND": f"{bitola} mm²", "FASE": fase_atrib_txt,
                    "TENSÃO": v_utilizada, "IB": ib_c, "COMP": comprimento_m
                })
                st.success(f"Circuito C{c_num_idx} Calculado: Cabo {bitola}mm² | Disjuntor {disj}A!")
                st.rerun()

    if st.session_state.lista_circuitos_calc:
        st.write("#### 📊 Quadro de Circuitos Dimensionados por Norma")
        st.dataframe(pd.DataFrame(st.session_state.lista_circuitos_calc), use_container_width=True)
try: area_obra_ref = area_obra
except: area_obra_ref = 70.0

pot_total = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc)
tipo_entrada, cabo_padrao, dj_padrao = "Bifásico", "16.0 mm²", "63 A"
detalhe_caixa = "Caixa Tipo 'F'"

recalcular_materials = recalcular_materiais_brutos_eletricos(area_obra_ref, tipo_entrada, dj_padrao, st.session_state.lista_circuitos_calc)
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
        [Paragraph("<b>Parâmetro</b>", estilo_celula), Paragraph("<b>Especificação Técnica</b>", estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento", estilo_celula), Paragraph(tipo_entrada, estilo_celula_esq)],
        [Paragraph("Cabo do Ramal de Entrada", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
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
            
        # MUDANÇA DEMANDADA: Centralizar todas estas informações no meio conforme modelo anexo
        texto_centralizado_modelo = f"<b>Potência Instalada Total: {pot_total} W | {tot_r}VA | {tot_s}VA</b>"
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
        elementos.append(Paragraph(f"2. Memorial Quantitativo da Alvenaria Estrutural ({metodo_calculo})", estilo_sub))
        dados_civil = [[Paragraph("<b>Etapa Civil</b>", estilo_celula), Paragraph("<b>Material Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
        for mat in st.session_state.lista_materiais_civil:
            dados_civil.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
        t_civ = Table(dados_civil, colWidths=[120.0, 400.0, 140.0, 80.0])
        t_civ.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
        elementos.append(t_civ)

    elementos.append(PageBreak())
    elementos.append(Paragraph("3. Diretrizes Técnicas Regulamentares", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴🟡 PRETO / VERMELHO / AMARELO: Condutores de Fase | ⚪⚪ BRANCO / CINZA: Condutores de Retorno (Iluminação).", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados nesta tampa de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente. Se ele não desarmar e desligar a energia da casa, substitua-o imediatamente (risco de choque).", estilo_aviso_corpo),
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
    if st.session_state.lista_circuitos_calc:
        st.download_button(label="📥 Baixar Memorial Técnico Consolidado (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia.pdf", mime="application/pdf", key="btn_pdf_real")
        if st.button("🗑️ Resetar Todo O Sistema", key="btn_clear_total"):
            st.session_state.lista_circuitos_calc = []
            st.session_state.lista_materiais_civil = []
            st.session_state.comodos = []
            st.rerun()
    else:
        st.info("Efetue os levantamentos elétricos para liberar a emissão do PDF.")
