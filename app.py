import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Importação dos módulos locais soltos na mesma pasta raiz
from db_functions import *
from calculus_engine import *
# Configuração primária obrigatória da janela do navegador
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

def gerar_pdf_completo_obra():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elementos = []
    
    estilos = getSampleStyleSheet()
    estilo_sub = ParagraphStyle('SubTitulo', parent=estilos['Heading2'], fontSize=14, textColor=colors.HexColor('#1E3A8A'), spaceAfter=10)
    estilo_celula = ParagraphStyle('Celula', parent=estilos['Normal'], fontSize=9, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelulaEsq', parent=estilos['Normal'], fontSize=9, alignment=0)
    estilo_aviso_tit = ParagraphStyle('AvisoTit', parent=estilos['Normal'], fontSize=10, textColor=colors.HexColor('#D97706'))
    estilo_aviso_corpo = ParagraphStyle('AvisoCorpo', parent=estilos['Normal'], fontSize=8.5)
    
    cabo_padrao = "16 mm²"
    dj_padrao = "Disjuntor Geral 50A"

    listas_gerais_obra = [
        ("2. Memorial da Fase Civil", st.session_state.lista_materials_civil, '#475569'),
        ("3. Lote Hidráulico e Redes de Esgoto", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("4. Tubulações de Gás Encanado", st.session_state.lista_materials_gas, '#B45309'),
        ("5. Rede de Internet e Dados", st.session_state.lista_materials_dados, '#6D28D9'),
        ("6. Ativos de Segurança Eletrônica", st.session_state.lista_materials_seguranca, '#0F172A'),
        ("7. Engenharia Solar Fotovoltaica (NBR 16690)", st.session_state.lista_materials_solar, '#F59E0B')
    ]
    
    for tit, lista, col_hex in listas_gerais_obra:
        if lista:
            elementos.append(PageBreak())
            elementos.append(Paragraph(tit, estilo_sub))
            tbl_d = [[Paragraph("<b>Etapa</b>", estilo_celula), Paragraph("<b>Insumo Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
            for mat in lista: 
                tbl_d.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
            t_m = Table(tbl_d, colWidths=[130.0, 400.0, 140.0, 80.0])
            t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor(col_hex)), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
            elementos.append(t_m)

    elementos.append(PageBreak())
    elementos.append(Paragraph("8. Diagrama Unifilar - Entrada Geral, Barramentos e Dispositivos de Proteção", estilo_sub))
    elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))
    
    elementos.append(PageBreak())
    elementos.append(Paragraph("9. Esquema Técnico Multifilar - Proteções de Cabeceira e Distribuição por Fase", estilo_sub))
    elementos.append(gerar_desenho_multifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))

    elementos.append(PageBreak())
    elementos.append(Paragraph("10. Observações Técnicas Normativas (Fixar na Tampa Interna do QDC)", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO OBRIGATÓRIAS - NBR 5410 & NR-10</b>", estilo_aviso_tit), Spacer(1, 2),
        Paragraph("• <b>Código Regulamentar de Cores:</b> Condutor Neutro deve ser 🔵 AZUL CLARO. Condutor de Proteção deve ser 🟢 VERDE. Condutores de Fase devem ser ⚫ PRETO ou 🔴 VERMELHO.", estilo_aviso_corpo),
        Paragraph("• <b>Dispositivos de Proteção Ativos:</b> É proibido anular o IDR de 30mA e os Supressores de Surto (DPS) de 45kA classe II.", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> Todas as chaves disjuntoras devem receber etiquetas correspondentes à prancha MDA sob risco de interdição técnica.", estilo_aviso_corpo),
        Paragraph("• <b>Torque e Reaperto Técnico:</b> Realizar inspeção semestral de torque nos bornes de conexão dos disjuntores para evitar pontos quentes e perdas por efeito Joule.", estilo_aviso_corpo)
    ]
    t_av = Table([[caviso]], colWidths=[710.0])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#D97706')), ('PADDING', (0,0), (-1,-1), 8)]))
    elementos.append(t_av)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer
def renderizar_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='color:#FFFFFF; background-color:#1E3A8A; padding:10px; border-radius:5px; text-align:center;'>⚙️ CENTRAL FÊNIX</h2>", unsafe_allow_html=True)
        st.write("### 👤 Gestão de Clientes")
        lista_cli = listar_clientes_db()
        if lista_cli:
            df_cli_view = pd.DataFrame(lista_cli, columns=["ID", "Nome", "Endereço", "Cidade/UF"])
            st.dataframe(df_cli_view, use_container_width=True, hide_index=True)
            id_cli_del = st.number_input("ID do Cliente para Remover:", min_value=1, step=1, key="del_cli_id")
            if st.button("❌ Excluir Cliente", use_container_width=True):
                excluir_cliente_db(id_cli_del)
                st.success("Cliente removido!")
                st.rerun()
                
        with st.expander("➕ Adicionar Novo Cliente"):
            c_nome = st.text_input("Nome do Cliente:")
            c_end = st.text_input("Endereço:")
            c_cid = st.text_input("Cidade/UF:")
            if st.button("💾 Gravar Cliente"):
                if c_nome and c_end:
                    inserir_cliente_db(c_nome, c_end, c_cid)
                    st.success("Cliente Salvo!")
                    st.rerun()

        st.markdown("---")
        st.write("### 📦 Catálogo de Materiais")
        with st.expander("➕ Cadastrar Insumo Técnico"):
            with st.form("form_catalogo_mat", clear_on_submit=True):
                mat_fase = st.selectbox("Segmento:", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança", "Energia Solar"])
                mat_etapa = st.text_input("Etapa de Aplicação:")
                mat_nome = st.text_input("Descrição do Material:")
                mat_qtd = st.number_input("Fator de Multiplicação:", value=1.0, min_value=0.1)
                mat_uni = st.selectbox("Unidade:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
                if st.form_submit_button("💾 Salvar Material"):
                    if mat_nome and mat_etapa:
                        inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_qtd, mat_uni)
                        st.success("Adicionado!")
                        st.rerun()

        st.markdown("---")
        st.write("### 👥 Equipe e Engenheiros")
        lista_eq = listar_equipe_tecnica()
        if lista_eq:
            df_eq_view = pd.DataFrame(lista_eq, columns=["ID", "Nome", "Função", "Registro", "Responsável"])
            st.dataframe(df_eq_view, use_container_width=True, hide_index=True)
            id_eq_op = st.number_input("ID do Membro para Ação:", min_value=1, step=1, key="op_eq_id")
            if st.button("❌ Remover Membro", use_container_width=True):
                excluir_membro_equipe(id_eq_op)
                st.success("Removido!")
                st.rerun()
                    
        with st.expander("➕ Cadastrar Membro na Equipe"):
            eq_nome = st.text_input("Nome Completo:")
            eq_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista"])
            eq_reg = st.text_input("Registro Profissional:")
            eq_resp = st.checkbox("Marcar como RT?")
            if st.button("💾 Gravar Membro"):
                if eq_nome and eq_reg:
                    inserir_membro_equipe(eq_nome, eq_func, eq_reg, eq_resp)
                    st.success("Membro alocado!")
                    st.rerun()
def main():
    concessionarias_locais = {
        "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
        "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
        "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
        "ENEL CE (CE) - NT-002": {"fase": 220, "linha": 380, "limite_mono": 12000, "limite_bi": 25000, "norma": "NT-002 ENEL", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
        "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Tipo Mono", "caixa_bi": "Caixa Tipo Bi", "caixa_tri": "Caixa Tipo Tri"},
        "CELESC (SC) - N-321": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
        "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
        "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Tipo Tri"},
        "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"}
    }

    if "db_sync_completo" not in st.session_state:
        st.session_state.lista_materials_civil = []
        st.session_state.lista_materials_hidraulicos = []
        st.session_state.lista_materials_gas = []
        st.session_state.lista_materials_dados = []
        st.session_state.lista_materials_seguranca = []
        st.session_state.lista_materials_solar = []
        st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
        st.session_state.modo_eletrica_anterior = "Casa Toda"
        st.session_state.db_sync_completo = True

    renderizar_sidebar()

    concessionaria_sel = st.selectbox("Escolha a Concessionária de Energia Alvo do Brasil:", list(concessionarias_locais.keys()))
    dados_c = concessionarias_locais[concessionaria_sel]

    global_tabs = st.tabs(["🧱 Civil", "⚡ Elétrica (Modelo MDA)", "🚰 Hidráulica", "🔥 Gás", "🌐 Internet", "🛡️ Segurança", "☀️ Energia Solar", "📂 Catálogo de Insumos", "📥 Emissão PDF"])
    
    st.session_state["active_tabs_fenix"] = global_tabs
    # Recupera a referência das abas criadas no bloco anterior
    tab_civil = st.session_state["active_tabs_fenix"][0]

    with tab_civil:
        st.write("### 🧱 Planta de Cômodos (Inserir / Alterar / Remover)")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            with st.form("form_comodo_civil"):
                c_nome = st.text_input("Nome do Ambiente (Ex: Cozinha):")
                c_comp = st.number_input("Comprimento Linear (m):", value=4.0, min_value=0.1)
                c_larg = st.number_input("Largura Linear (m):", value=3.0, min_value=0.1)
                if st.form_submit_button("➕ Salvar Ambiente"):
                    if c_nome:
                        inserir_comodo_db(c_nome, c_comp, c_larg)
                        st.success("Cômodo gravado!")
                        st.rerun()
        with col_v2:
            lista_comodos_fisicos = listar_comodos_db()
            if lista_comodos_fisicos:
                df_com_f = pd.DataFrame(lista_comodos_fisicos, columns=["ID", "Cômodo", "Comprimento (m)", "Largura (m)"])
                st.dataframe(df_com_f, use_container_width=True, hide_index=True)
                id_com_op = st.number_input("ID do Cômodo para Ação:", min_value=1, step=1, key="op_com_id")
                c_alt_chk = st.checkbox("Ativar Alteração de Dados?")
                if c_alt_chk:
                    alt_c_nome = st.text_input("Novo Nome Ambiente:")
                    alt_c_comp = st.number_input("Novo Comprimento:", value=4.0)
                    alt_c_larg = st.number_input("Nova Largura:", value=3.0)
                    if st.button("📝 Confirmar Alteração Cômodo"):
                        atualizar_comodo_db(id_com_op, alt_c_nome, alt_c_comp, alt_c_larg)
                        st.success("Dados atualizados!")
                        st.rerun()
                if st.button("❌ Remover Cômodo Selecionado"):
                    excluir_comodo_db(id_com_op)
                    st.success("Removido da planta!")
                    st.rerun()
                    
        st.markdown("---")
        modo_civil = st.radio("Seletor do Modo de Escopo Civil:", ["Cálculo Global por Área (m²)", "Levantamento por Cômodos Cadastrados"], horizontal=True)
        if modo_civil == "Cálculo Global por Área (m²)":
            area_obra = st.number_input("Área Construída Total (m²):", min_value=10.0, value=70.0)
            perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0)
            if st.button("📊 Processar Cubagem Global de Insumos Civis"):
                st.session_state.lista_materials_civil = [
                    {"Etapa": "01. Locação", "Material": "Tábua de Pinus 30cm x 3m", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
                    {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": 4.8, "Unidade": "m³"},
                    {"Etapa": "03. Estrutura", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"}
                ]
                st.rerun()
        else:
            if lista_comodos_fisicos:
                area_acumulada = sum(float(row_c[2]) * float(row_c[3]) for row_c in lista_comodos_fisicos)
                perimetro_acumulado = sum((float(row_c[2]) * 2) + (float(row_c[3]) * 2) for row_c in lista_comodos_fisicos)
                num_comodos = len(lista_comodos_fisicos)
                st.metric("Área Computada dos Ambientes", f"{round(area_acumulada, 2)} m²")
                if st.button("📊 Processar Insumos por Prancha de Cômodos"):
                    st.session_state.lista_materials_civil = []
                    st.session_state.lista_circuitos_calc = []
                    st.session_state.lista_materials_hidraulicos = []
                    st.session_state.lista_materials_gas = []
                    st.session_state.lista_materials_dados = []
                    st.session_state.lista_materials_seguranca = []
                    st.session_state.lista_materials_solar = []
                    itens_catalogo = listar_materiais_catalogo()
                    for item in itens_catalogo:
                        fase_cat, etapa_cat, nome_cat, fat_cat, uni_cat = item[1], item[2], item[3], float(item[4]), item[5]
                        if fase_cat == "Civil":
                            st.session_state.lista_materials_civil.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(area_acumulada * fat_cat)), "Unidade": uni_cat})
                        elif fase_cat == "Hidráulica":
                            st.session_state.lista_materials_hidraulicos.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(perimetro_acumulado * fat_cat)), "Unidade": uni_cat})
                        elif fase_cat == "Gás Encanado":
                            st.session_state.lista_materials_gas.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(num_comodos * fat_cat)), "Unidade": uni_cat})
                        elif fase_cat == "Internet/Dados":
                            st.session_state.lista_materials_dados.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(num_comodos * fat_cat)), "Unidade": uni_cat})
                        elif fase_cat == "Segurança":
                            st.session_state.lista_materials_seguranca.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(num_comodos * fat_cat)), "Unidade": uni_cat})
                        elif fase_cat == "Energia Solar":
                            st.session_state.lista_materials_solar.append({"Etapa": etapa_cat, "Material": nome_cat, "Quantidade": float(math.ceil(fat_cat)), "Unidade": uni_cat})
                    planta_modelo = [
                        {"CIRC": "1", "DESCRIÇÃO": "ILUMINAÇÃO", "COMODO": "Geral", "POT_W": int(math.ceil(area_acumulada * 15))},
                        {"CIRC": "2", "DESCRIÇÃO": "TOMADAS TUG", "COMODO": "Geral", "POT_W": int(math.ceil(num_comodos * 600))}
                    ]
                    for item_el in planta_modelo:
                        res = dimensionar_circuito_nbr5410_mda(item_el["POT_W"], dados_c["fase"], 15, item_el["DESCRIÇÃO"])
                        st.session_state.lista_circuitos_calc.append({
                            "CIRC": item_el["CIRC"], "DESCRIÇÃO": item_el["DESCRIÇÃO"], "COMODO": item_el["COMODO"], "POT_W": int(item_el["POT_W"]), "POT_VA": res["VA"], "FP": res["FP"],
                            "TIPO": "Monofásico", "DISJ": f"{res['DISJUNTORES']}A", "CURVA": res["CURVA"], "COND": f"{res['BITOLA']} mm²",
                            "FASE": "R", "TENSÃO": int(dados_c["fase"]), "IB": res["IB"], "IB_CORR": res["IB_CORR"], "COMP": 15, "DV": res["DV"]
                        })
                    salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                    st.rerun()
        if st.session_state.lista_materials_civil: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_civil), use_container_width=True, hide_index=True)
    # Recupera as referências das demais abas mapeadas no Bloco 4
    tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_solar, tab_catalogo, tab_pdf = st.session_state["active_tabs_fenix"]

    with tab_eletrica:
        st.write("### ⚡ Escopo e Gestão de Circuitos")
        modo_eletrica = st.radio("Selecione a Abrangência do Cálculo:", ["Casa Toda", "Apenas 1 Circuito / Circuitos Customizados"], horizontal=True, key="switch_modo_ele")
        
        # Monitora a mudança de modo. Ao entrar em circuito customizado, limpa a prancha anterior
        if modo_eletrica != st.session_state.modo_eletrica_anterior:
            st.session_state.modo_eletrica_anterior = modo_eletrica
            if modo_eletrica == "Apenas 1 Circuito / Circuitos Customizados":
                st.session_state.lista_circuitos_calc = []
                salvar_dados_permanentes("circuitos", [])
                st.rerun()

        if modo_eletrica == "Apenas 1 Circuito / Circuitos Customizados":
            st.markdown("#### ➕ Adicionar Circuito à Prancha")
            with st.form("form_add_circuito_individual", clear_on_submit=True):
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    c_num_in = st.text_input("Número/Identificação do Circuito (Ex: C1, C2):")
                    c_desc_in = st.selectbox("Tipo de Carga/Descrição:", ["Iluminação", "Tomadas TUG", "TUE - Chuveiro", "Ar Condicionado", "Micro-ondas", "TUG Cozinha"])
                with col_c2:
                    c_pot_in = st.number_input("Potência Total Instalada (Watts):", min_value=50, value=1200, step=50)
                    c_com_in = st.number_input("Comprimento Máximo do Circuito (m):", min_value=1, value=15, step=1)
                with col_c3:
                    c_amb_in = st.text_input("Ambiente Principal Ocupado:")
                
                if st.form_submit_button("💾 Adicionar Circuito"):
                    if c_num_in and c_desc_in:
                        res = dimensionar_circuito_nbr5410_mda(c_pot_in, dados_c["fase"], c_com_in, c_desc_in)
                        st.session_state.lista_circuitos_calc.append({
                            "CIRC": c_num_in, "DESCRIÇÃO": c_desc_in.upper(), "COMODO": c_amb_in if c_amb_in else "Geral",
                            "POT_W": int(c_pot_in), "POT_VA": res["VA"], "FP": res["FP"], "TIPO": "Monofásico",
                            "DISJ": f"{res['DISJUNTORES']}A", "CURVA": res["CURVA"], "COND": f"{res['BITOLA']} mm²",
                            "FASE": "R", "TENSÃO": int(dados_c["fase"]), "IB": res["IB"], "IB_CORR": res["IB_CORR"],
                            "COMP": c_com_in, "DV": res["DV"]
                        })
                        salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                        st.success(f"Circuito {c_num_in} adicionado!")
                        st.rerun()

            if st.session_state.lista_circuitos_calc:
                st.markdown("#### ❌ Remover Circuito Selecionado")
                col_rem_1, col_rem_2 = st.columns(2)
                with col_rem_1:
                    opcoes_circ = [circ["CIRC"] for circ in st.session_state.lista_circuitos_calc]
                    circ_para_remover = st.selectbox("Identificação para Excluir:", opcoes_circ)
                    if st.button("🗑️ Remover Circuito"):
                        st.session_state.lista_circuitos_calc = [c for c in st.session_state.lista_circuitos_calc if c["CIRC"] != circ_para_remover]
                        salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                        st.success("Circuito removido!")
                        st.rerun()

        if st.session_state.lista_circuitos_calc:
            st.markdown("#### 📋 Prancha MDA - Circuitos Ativos")
            st.dataframe(pd.DataFrame(st.session_state.lista_circuitos_calc), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum circuito programado ou calculado até o momento.")
    with tab_hidraulica:
        if st.session_state.lista_materials_hidraulicos: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_hidraulicos), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum material hidráulico processado até o momento.")

    with tab_gas:
        if st.session_state.lista_materials_gas: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_gas), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum material de gás encanado processado até o momento.")

    with tab_dados:
        if st.session_state.lista_materials_dados: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_dados), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum ativo de internet ou dados cadastrado até o momento.")

    with tab_seguranca:
        if st.session_state.lista_materials_seguranca: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_seguranca), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum material de segurança eletrônica listado até o momento.")

    with tab_solar:
        if st.session_state.lista_materials_solar: 
            st.dataframe(pd.DataFrame(st.session_state.lista_materials_solar), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum componente solar fotovoltaico gerado até o momento.")

    with tab_catalogo:
        cat_df = listar_materiais_catalogo()
        if cat_df: 
            st.dataframe(pd.DataFrame(cat_df, columns=["ID", "Segmento", "Etapa", "Material", "Fator Base", "Unidade"]), use_container_width=True, hide_index=True)
        else:
            st.info("O catálogo de insumos técnicos está vazio.")

    with tab_pdf:
        st.write("### 🖨️ Central de Emissão")
        if st.button("🔄 Preparar Relatório Técnico"):
            pdf_dados = gerar_pdf_completo_obra()
            st.download_button(
                label="📥 Baixar Memorial Técnico Unificado (PDF)", 
                data=pdf_dados, 
                file_name="memorial_de_engenharia_unificado.pdf", 
                mime="application/pdf", 
                key="btn_pdf_real"
            )

# Cláusula de inicialização segura do ecossistema Fênix
if __name__ == "__main__":
    init_db()  # Garante as tabelas estruturais locais prontas antes da interface
    main()
