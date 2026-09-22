import streamlit as st
import pandas as pd
import math
import sqlite3
import json
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle

# Configuração primária obrigatória do Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# --- ENGINE DO BANCO DE DADOS PERSISTENTE LOCAL ---
def init_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (id TEXT PRIMARY KEY, dados TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, endereco TEXT, cidade_uf TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS materiais_catalogo (id INTEGER PRIMARY KEY AUTOINCREMENT, fase TEXT, etapa TEXT, material TEXT, unidade TEXT)")
    conn.commit()
    conn.close()

init_db()
def salvar_dados_permanentes(chave, valor):
    try:
        conn = sqlite3.connect("fenix_database.db")
        cursor = conn.cursor()
        json_dados = json.dumps(valor)
        cursor.execute("INSERT OR REPLACE INTO configuracoes (id, dados) VALUES (?, ?)", (chave, json_dados))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def carregar_dados_permanentes(chave, valor_padrao):
    try:
        conn = sqlite3.connect("fenix_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT dados FROM configuracoes WHERE id = ?", (chave,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        return valor_padrao
    return valor_padrao

def inserir_cliente_db(nome, endereco, city_uf):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nome, endereco, cidade_uf) VALUES (?, ?, ?)", (nome, endereco, city_uf))
    conn.commit()
    conn.close()

def listar_clientes_db():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, endereco, cidade_uf FROM clientes")
    rows = cursor.fetchall()
    conn.close()
    return rows

def inserir_material_catalogo(fase, etapa, material, unidade):
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO materiais_catalogo (fase, etapa, material, unidade) VALUES (?, ?, ?, ?)", (fase, etapa, material, unidade))
    conn.commit()
    conn.close()

def listar_materiais_catalogo():
    conn = sqlite3.connect("fenix_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, fase, etapa, material, unidade FROM materiais_catalogo")
    rows = cursor.fetchall()
    conn.close()
    return rows
if "lista_materials_civil" not in st.session_state: st.session_state.lista_materials_civil = []
if "lista_materials_eletricos" not in st.session_state: st.session_state.lista_materials_eletricos = []
if "lista_materials_hidraulicos" not in st.session_state: st.session_state.lista_materials_hidraulicos = []
if "lista_materials_gas" not in st.session_state: st.session_state.lista_materials_gas = []
if "lista_materials_dados" not in st.session_state: st.session_state.lista_materials_dados = []
if "lista_materials_seguranca" not in st.session_state: st.session_state.lista_materials_seguranca = []

if "db_sync" not in st.session_state:
    st.session_state.funcionarios = carregar_dados_permanentes("funcionarios", [
        {"id": 1, "Nome": "Eng. Carlos Silva", "Função": "Responsável Técnico", "CREA_RE": "MG20231045", "Responsavel": True},
        {"id": 2, "Nome": "Marcos Souza", "Função": "Eletricista Instalador", "CREA_RE": "RE-9942", "Responsavel": False}
    ])
    st.session_state.lista_circuitos_calc = carregar_dados_permanentes("circuitos", [])
    st.session_state.comodos = carregar_dados_permanentes("comodos", [])
    st.session_state.seguranca_insumos = carregar_dados_permanentes("seguranca", {"cameras": 4, "sensores": 3, "cabo_m": 100})
    st.session_state.db_sync = True
def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
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
        d.add(String(250, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:25]} - {c.get('COMODO','Geral')}", fontSize=7.5, fontName='Helvetica'))
    return d

def gerar_desenho_multifilar(circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
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
            d.add(String(35, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:12]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(Line(160, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
        else:
            d.add(Rect(360, y - 10, 130, 24, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(365, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:12]}", fontSize=7, fontName='Helvetica-Bold'))
            d.add(Line(360, y, x_neutro, y, strokeColor=colors.blue, strokeWidth=0.8))
    return d
with st.sidebar:
    st.markdown(
        """
        <div style="background-color:#1E3A8A; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <h2 style="color:#FFFFFF; margin:0; font-family:sans-serif; letter-spacing: 2px;">⚡ FÊNIX</h2>
            <p style="color:#0D9488; margin:0; font-size:11px; font-weight:bold; letter-spacing: 1px;">ENGENHARIA & SISTEMAS</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.write("### 👥 Gestão de Equipe Técnica")
    with st.form("form_func", clear_on_submit=True):
        f_nome = st.text_input("Nome do Colaborador:")
        f_func = st.selectbox("Função:", ["Responsável Técnico", "Eletricista Instalador", "Mestre de Obras", "Projetista", "Encanador", "Técnico"])
        f_reg = st.text_input("Registro (CREA / RE):")
        f_resp = st.checkbox("Definir como Responsável?")
        if st.form_submit_button("Cadastrar Funcionário"):
            if f_nome and f_reg:
                ids_existentes = [f["id"] for f in st.session_state.funcionarios]
                novo_id = max(ids_existentes) + 1 if ids_existentes else 1
                st.session_state.funcionarios.append({"id": novo_id, "Nome": f_nome, "Função": f_func, "CREA_RE": f_reg, "Responsavel": f_resp})
                salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                st.success("Funcionário Cadastrado!")
                st.rerun()

    if st.session_state.funcionarios:
        for idx, f in enumerate(list(st.session_state.funcionarios)):
            col_f1, col_f2 = st.columns(2)
            with col_f1: st.write(f"**{f['Nome']}** ({f['Função']})")
            with col_f2:
                if st.button("❌", key=f"del_f_{f['id']}_{idx}"):
                    st.session_state.funcionarios.pop(idx)
                    salvar_dados_permanentes("funcionarios", st.session_state.funcionarios)
                    st.rerun()

    st.markdown("---")
    st.write("### 📦 Cadastro Geral de Materiais")
    with st.form("form_catalogo_mat", clear_on_submit=True):
        mat_fase = st.selectbox("Pertence a qual Fase/Segmento?", ["Civil", "Elétrica", "Hidráulica", "Gás Encanado", "Internet/Dados", "Segurança"])
        mat_etapa = st.text_input("Etapa do Serviço (Ex: Infraestrutura, Fechamento, Acabamento):")
        mat_nome = st.text_input("Nome Técnico do Material:")
        mat_uni = st.selectbox("Unidade:", ["un", "m", "m²", "m³", "sc", "barra", "rl", "jg"])
        if st.form_submit_button("💾 Cadastrar Insumo no Catálogo"):
            if mat_nome and mat_etapa:
                inserir_material_catalogo(mat_fase, mat_etapa, mat_nome, mat_uni)
                st.success(f"Material salvo no catálogo da fase {mat_fase}!")
                st.rerun()
st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("ERP Corporativo Base SQLite: Memorial Dinâmico de Instalações Relacionais")
st.markdown("---")

st.write("### 👤 Central de Clientes (Gravar e Selecionar)")
lista_clientes = listar_clientes_db()
opcoes_clientes = ["-- Cadastrar Novo Cliente --"] + [f"ID {c[0]} - {c[1]}" for c in lista_clientes]

col_c1, col_c2 = st.columns(2)
with col_c1:
    cliente_selecionado = st.selectbox("📂 Escolher Cliente Salvo:", opcoes_clientes)

if cliente_selecionado != "-- Cadastrar Novo Cliente --":
    id_cli = int(cliente_selecionado.split(" - ")[0].replace("ID ", ""))
    dados_cli_atual = [c for c in lista_clientes if c[0] == id_cli][0]
    val_nome, val_end, val_cid = dados_cli_atual[1], dados_cli_atual[2], dados_cli_atual[3]
else:
    val_nome, val_end, val_cid = "", "", ""

with col_c2:
    with st.form("form_cliente"):
        cliente_nome = st.text_input("Nome Completo do Cliente:", value=val_nome)
        cliente_endereco = st.text_input("Endereço da Obra:", value=val_end)
        cliente_cidade = st.text_input("Cidade / UF:", value=val_cid)
        if st.form_submit_button("💾 Gravar e Salvar Cliente"):
            if cliente_nome and cliente_endereco:
                inserir_cliente_db(cliente_nome, cliente_endereco, cliente_cidade)
                st.success("Cliente gravado com sucesso no banco SQLite!")
                st.rerun()

CONCESSIONARIAS = {
    "CEMIG (MG) - ND-5.1": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "norma": "ND-5.1", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "ENEL SP (SP) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "ENEL RJ (RJ) - CNC-OM": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "CNC-OM-BR-24-001", "caixa_mono": "Caixa Tipo A", "caixa_bi": "Caixa Tipo B", "caixa_tri": "Caixa Tipo C"},
    "CPFL Paulista (SP)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "norma": "GED-13", "caixa_mono": "Caixa Tipo II", "caixa_bi": "Caixa Tipo III", "caixa_tri": "Caixa Tipo IV"},
    "LIGHT (RJ) - Recon-BT": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "norma": "Recon-BT", "caixa_mono": "Caixa Tipo L", "caixa_bi": "Caixa Tipo M", "caixa_tri": "Caixa Tipo N"},
    "COPEL (PR) - NTC 901": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "norma": "NTC 901100", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "CELESC (SC) - N-321": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "norma": "N-321.0001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "EQUATORIAL MA/PA/PI/AL": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "NT-01.EQ", "caixa_mono": "Caixa Tipo E", "caixa_bi": "Caixa Tipo F", "caixa_tri": "Caixa Tipo H"},
    "NEOENERGIA BA/PE/RN/DF": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "norma": "DIS-NOR-001", "caixa_mono": "Caixa Monofásica", "caixa_bi": "Caixa Bifásica", "caixa_tri": "Caixa Trifásica"},
    "ENERGISA MT/MS/TO/RO/AC": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 22000, "norma": "NT-03.EN", "caixa_mono": "Caixa Padrão E", "caixa_bi": "Caixa Padrão F", "caixa_tri": "Caixa Padrão H"}
}

def dimensionar_circuito_nbr5410(potencia, tensao, comprimento, tipo_carga):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.8
    ib = potencia / (tensao * fp)
    bitola_inicial = 1.5 if "Iluminação" in tipo_carga else 2.5
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    bitola_final = bitola_inicial
    iz_cabo = 17.5 if "Iluminação" in tipo_carga else 24.0
    for b, cap in zip(bitolas_comerciais, capacidades_corrente):
        if b >= bitola_inicial and cap >= ib:
            bitola_final = b
            iz_cabo = cap
            break
    rho = 1 / 58.0
    while True:
        dv_perc = (2 * rho * comprimento * ib * 100) / (tensao * bitola_final)
        if dv_perc <= 2.0 or bitola_final >= 16.0: break
        idx = bitolas_comerciais.index(bitola_final)
        if idx < len(bitolas_comerciais) - 1:
            bitola_final = bitolas_comerciais[idx + 1]
            iz_cabo = capacidades_corrente[idx + 1]
        else: break
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= iz_cabo:
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
    return bitola_final, disjuntor_final, "B" if "Iluminação" in tipo_carga else "C", round(ib, 2)

tab_civil, tab_eletrica, tab_hidraulica, tab_gas, tab_dados, tab_seguranca, tab_catalogo, tab_pdf = st.tabs(["🧱 Civil", "⚡ Elétrica", "🚰 Hidráulica", "🔥 Gás Encanado", "🌐 Internet/Dados", "🛡️ Segurança", "📂 Ver Catálogo", "📥 Relatório PDF"])
with tab_civil:
    st.write("### 🧱 Configuração do Método de Levantamento Estrutural e Prancha de Cômodos")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: nome_c = st.text_input("Nome do Cômodo (Ex: Cozinha, Suíte 1):")
    with cc2: comp_c = st.number_input("Comprimento do Cômodo (m):", value=4.0, min_value=0.5)
    with cc3: larg_c = st.number_input("Largura do Cômodo (m):", value=3.5, min_value=0.5)
    if st.button("➕ Encaixar Cômodo na Prancha de Ambientes"):
        if nome_c:
            st.session_state.comodos.append({"Cômodo": nome_c, "Comprimento": comp_c, "Largura": larg_c})
            salvar_dados_permanentes("comodos", st.session_state.comodos)
            st.success(f"Ambiente '{nome_c}' cadastrado com sucesso!")
            st.rerun()

    if st.session_state.comodos:
        st.write("📋 **Prancha de Ambientes Cadastrados:**")
        st.dataframe(pd.DataFrame(st.session_state.comodos), use_container_width=True)
        if st.button("🗑️ Limpar Todos os Cômodos"):
            st.session_state.comodos = []
            salvar_dados_permanentes("comodos", [])
            st.rerun()

    st.markdown("---")
    area_obra = st.number_input("Área Construída Total da Obra para Cálculo Lote (m²):", min_value=10.0, value=70.0, step=5.0)
    perimetro_paredes = st.number_input("Perímetro Total das Paredes (m):", min_value=0.0, value=45.0, step=1.0)
    if st.button("📊 Processar Cubagem Global de Insumos Civis"):
        st.session_state.lista_materials_civil = [
            {"Etapa": "01. Locação da Obra", "Material": "Tábua de Pinus 30cm x 3m", "Quantidade": float(math.ceil(perimetro_paredes * 0.4)), "Unidade": "un"},
            {"Etapa": "02. Infraestrutura", "Material": "Concreto Usinado Fck=30MPa", "Quantidade": 4.8, "Unidade": "m³"},
            {"Etapa": "03. Estrutura e Piso", "Material": "Cimento CP II-Z-32 (Saco de 50kg)", "Quantidade": float(math.ceil(area_obra * 1.1)), "Unidade": "sc"},
            {"Etapa": "04. Alvenaria", "Material": "Tijolo Cerâmico Baiano 8 Furos", "Quantidade": float(math.ceil(perimetro_paredes * 2.8 * 25 * 1.1)), "Unidade": "un"},
            {"Etapa": "05. Acabamentos", "Material": "Piso Porcelanato Retificado Comercial", "Quantidade": float(round(area_obra * 1.1, 1)), "Unidade": "m²"}
        ]
        st.rerun()

    if st.session_state.lista_materials_civil:
        edited_civil = st.data_editor(pd.DataFrame(st.session_state.lista_materials_civil), num_rows="dynamic", use_container_width=True, key="editor_civil")
        if st.button("💾 Salvar Alterações da Fase Civil"):
            st.session_state.lista_materials_civil = edited_civil.to_dict(orient="records")
            st.success("Fase civil atualizada!")
            st.rerun()

with tab_eletrica:
    st.write("### ⚡ Dimensionamento Elétrico NBR 5410 com Lançamento Separável por Cômodo")
    concessionaria_sel = st.selectbox("🔌 Escolha a Distribuidora de Energia Elétrica:", list(CONCESSIONARIAS.keys()))
    dados_c = CONCESSIONARIAS[concessionaria_sel]

    lista_comodos_opcoes = [c["Cômodo"] for c in st.session_state.comodos] if st.session_state.comodos else []
    
    if not lista_comodos_opcoes:
        st.warning("⚠️ Atenção: Cadastre pelo menos um cômodo na aba '🧱 Civil' para poder lançar os circuitos elétricos vinculados.")
    else:
        with st.form("form_novo_circuito_separado"):
            st.write("#### ➕ Lançar Circuito Individual Customizado")
            manual_nome = st.text_input("Nome do Circuito (Ex: Tomadas Cozinha, Ar Suíte):", value="Tomadas Uso Geral")
            c_comodo = st.selectbox("A qual Cômodo pertence este circuito?", lista_comodos_opcoes)
            c_desc = st.selectbox("Tipo de Carga / Serviço:", ["Iluminação", "TUG - Tomadas Uso Geral", "TUE - Tomadas Uso Especial (Chuveiro/Ar)"])
            
            # Condicional dinâmica para quantidade de tomadas
            if "Tomadas" in c_desc or "TUG" in c_desc or "TUE" in c_desc:
                qtd_tomadas = st.number_input("Quantas tomadas serão ligadas neste circuito?", min_value=1, value=4, step=1)
                manual_pot = qtd_tomadas * 600 if "Geral" in c_desc else 4400
            else:
                qtd_tomadas = 0
                manual_pot = st.number_input("Potência Total da Iluminação (W):", value=1200, step=100)
                
            manual_comp = st.number_input("Metragem Linear de Cabo até o QDC (m):", value=15, min_value=1)
            tipo_rede = st.selectbox("Tipo de Fornecimento do Circuito:", ["Monofásico", "Bifásico"])
            
            if st.form_submit_button("🔌 Processar Cálculo Automático e Inserir"):
                c_idx = str(len(st.session_state.lista_circuitos_calc) + 1)
                tensao_c = dados_c["linha"] if tipo_rede == "Bifásico" else dados_c["fase"]
                b, dj, crv, ib_c = dimensionar_circuito_nbr5410(manual_pot, tensao_c, manual_comp, c_desc)
                
                desc_final = f"{manual_nome} ({qtd_tomadas}t)" if qtd_tomadas > 0 else manual_nome
                st.session_state.lista_circuitos_calc.append({
                    "CIRC": c_idx, "DESCRIÇÃO": desc_final, "COMODO": c_comodo, "POT_W": int(manual_pot), "TIPO": tipo_rede,
                    "DISJ": f"{dj}A", "CURVA": crv, "COND": f"{b} mm²", "FASE": "RS" if tipo_rede == "Bifásico" else "R",
                    "TENSÃO": int(tensao_c), "IB": float(ib_c), "COMP": int(manual_comp)
                })
                salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
                st.success(f"Circuito {manual_nome} alocado com sucesso!")
                st.rerun()

    if st.session_state.lista_circuitos_calc:
        st.write("#### 📋 Quadro de Distribuição de Cargas (QDC) Relacional:")
        edited_eletrica = st.data_editor(pd.DataFrame(st.session_state.lista_circuitos_calc), num_rows="dynamic", use_container_width=True, key="editor_eletrica")
        if st.button("💾 Salvar Alterações da Fase Elétrica"):
            st.session_state.lista_circuitos_calc = edited_eletrica.to_dict(orient="records")
            salvar_dados_permanentes("circuitos", st.session_state.lista_circuitos_calc)
            st.success("QDC atualizado!")
            st.rerun()
with tab_hidraulica:
    st.write("### 🚰 Redes Hidráulicas e Esgoto Sanitário")
    n_banheiros = st.number_input("Quantidade de Banheiros/Lavabos Totais:", min_value=1, value=2)
    m_tubo_agua = st.number_input("Tubulação Água Fria 25mm (m):", min_value=6, value=30)
    m_tubo_esgoto = st.number_input("Tubulação Esgoto 100mm (m):", min_value=6, value=24)
    if st.button("📊 Processar Hidráulica Automática"):
        st.session_state.lista_materials_hidraulicos = [
            {"Etapa": "01. Reservatório", "Material": "Caixa d'Água Polietileno 1000L", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "02. Água Fria", "Material": "Tubo PVC Soldável Marrom 25mm (6m)", "Quantidade": float(math.ceil(m_tubo_agua / 6.0)), "Unidade": "barra"},
            {"Etapa": "03. Esgoto", "Material": "Tubo Esgoto PVC Branco 100mm (6m)", "Quantidade": float(math.ceil(m_tubo_esgoto / 6.0)), "Unidade": "barra"}
        ]
        st.rerun()
    if st.session_state.lista_materials_hidraulicos:
        edited_hidr = st.data_editor(pd.DataFrame(st.session_state.lista_materials_hidraulicos), num_rows="dynamic", use_container_width=True, key="editor_hidr")
        if st.button("💾 Salvar Alterações Hidráulicas"):
            st.session_state.lista_materials_hidraulicos = edited_hidr.to_dict(orient="records")
            st.rerun()

with tab_gas:
    st.write("### 🔥 Dimensionamento e Insumos de Redes de Gás Encanado")
    pontos_gas = st.number_input("Quantidade de Aparelhos a Gás (Fogão/Aquecedor):", min_value=1, value=2)
    m_cobre = st.number_input("Metragem de Rede de Cobre Hidrolítico Sem Costura (m):", min_value=2, value=12)
    if st.button("📊 Processar Gás Automático"):
        st.session_state.lista_materials_gas = [
            {"Etapa": "01. Tubulação", "Material": "Tubo de Cobre Sem Costura 15mm", "Quantidade": float(math.ceil(m_cobre)), "Unidade": "m"},
            {"Etapa": "02. Regulagem", "Material": "Regulador de Pressão Gás GLP 7kg/h", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "03. Válvulas", "Material": "Válvula de Esfera Latão para Gás 1/2", "Quantidade": float(pontos_gas), "Unidade": "un"}
        ]
        st.rerun()
    if st.session_state.lista_materials_gas:
        edited_gas = st.data_editor(pd.DataFrame(st.session_state.lista_materials_gas), num_rows="dynamic", use_container_width=True, key="editor_gas")
        if st.button("💾 Salvar Alterações de Gás"):
            st.session_state.lista_materials_gas = edited_gas.to_dict(orient="records")
            st.rerun()

with tab_dados:
    st.write("### 🌐 Infraestrutura de Redes de Dados e Internet")
    m_cat6 = st.number_input("Metragem Estimada de Cabo LAN UTP Cat6 Puro Cobre (m):", min_value=20, value=150)
    if st.button("📊 Processar Telecom e Internet"):
        st.session_state.lista_materials_dados = [
            {"Etapa": "01. Cabeamento", "Material": "Cabo de Rede UTP Cat6 Puro Cobre", "Quantidade": float(m_cat6), "Unidade": "m"},
            {"Etapa": "02. Ativos", "Material": "Switch Gerenciável Gigabit PoE 16 Portas", "Quantidade": 1.0, "Unidade": "un"},
            {"Etapa": "03. Terminais", "Material": "Rack Padrão De Parede 19 Polegadas 6U", "Quantidade": 1.0, "Unidade": "un"}
        ]
        st.rerun()
    if st.session_state.lista_materials_dados:
        edited_dados = st.data_editor(pd.DataFrame(st.session_state.lista_materials_dados), num_rows="dynamic", use_container_width=True, key="editor_dados")
        if st.button("💾 Salvar Alterações de Internet"):
            st.session_state.lista_materials_dados = edited_dados.to_dict(orient="records")
            st.rerun()

with tab_seguranca:
    st.write("### 🛡️ Engenharia de Sistemas de Segurança e Monitoramento CFTV")
    n_cameras = st.number_input("Quantidade de Câmeras IP IP67:", min_value=0, value=st.session_state.seguranca_insumos["cameras"], step=1)
    n_sensores = st.number_input("Quantidade de Sensores de Presença IVP:", min_value=0, value=st.session_state.seguranca_insumos["sensores"], step=1)
    m_cabo_rede = st.number_input("Metragem de Cabo UTP Cat6 (m):", min_value=10, value=st.session_state.seguranca_insumos["cabo_m"], step=10)
    if st.button("📊 Processar Segurança Eletrônica"):
        st.session_state.lista_materials_seguranca = [
            {"Etapa": "Segurança Eletrônica", "Material": "Câmera CFTV IP Bullet 2MP Full HD IP67", "Quantidade": float(n_cameras), "Unidade": "un"},
            {"Etapa": "Segurança Eletrônica", "Material": "Gravador Digital de Vídeo NVR 8 Canais", "Quantidade": 1.0 if n_cameras <= 8 else 2.0, "Unidade": "un"},
            {"Etapa": "Segurança Eletrônica", "Material": "Sensor Infravermelho Passivo (IVP)", "Quantidade": float(n_sensores), "Unidade": "un"}
        ]
        st.session_state.seguranca_insumos = {"cameras": n_cameras, "sensores": n_sensores, "cabo_m": m_cabo_rede}
        salvar_dados_permanentes("seguranca", st.session_state.seguranca_insumos)
        st.rerun()
    if st.session_state.lista_materials_seguranca:
        edited_seg = st.data_editor(pd.DataFrame(st.session_state.lista_materials_seguranca), num_rows="dynamic", use_container_width=True, key="editor_seg")
        if st.button("💾 Salvar Alterações de Segurança"):
            st.session_state.lista_materials_seguranca = edited_seg.to_dict(orient="records")
            st.rerun()

with tab_catalogo:
    st.write("### 📂 Catálogo Geral de Materiais Cadastrados no Banco de Dados")
    dados_catalogo = listar_materiais_catalogo()
    if dados_catalogo:
        df_cat = pd.DataFrame(dados_catalogo, columns=["ID", "Fase/Segmento", "Etapa de Serviço", "Insumo Técnico", "Unidade"])
        st.dataframe(df_cat, use_container_width=True)
    else:
        st.info("Nenhum material cadastrado de forma personalizada ainda. Use o formulário da barra lateral.")
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
    dados_cliente_tabela = [[Paragraph(f"<b>CLIENTE:</b> {cliente_nome}", estilo_celula_esq), Paragraph(f"<b>OBRA:</b> {cliente_endereco}", estilo_celula_esq), Paragraph(f"<b>LOCALIDADE:</b> {cliente_cidade}", estilo_celula_esq)]]
    t_cli = Table(dados_cliente_tabela, colWidths=[240.0, 260.0, 240.0])
    t_cli.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 4)]))
    elementos.append(t_cli)
    
    responsaveis_projeto = [f"{f['Função']}: {f['Nome']} ({f['CREA_RE']})" for f in st.session_state.funcionarios if f["Responsavel"]]
    elementos.append(Paragraph(f"<b>Responsáveis Técnicos:</b> {' | '.join(responsaveis_projeto)}", estilo_celula_esq))

    # Lógica de enquadramento técnico automática da concessionária para o PDF
    try: area_ref_val = area_obra
    except: area_ref_val = 70.0
    
    pot_total_sistema = sum(int(c["POT_W"]) for c in st.session_state.lista_circuitos_calc) if st.session_state.lista_circuitos_calc else 5000
    if pot_total_sistema <= dados_c["limite_mono"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Monofásico", "10.0 mm²", "40 A", dados_c["caixa_mono"]
    elif pot_total_sistema <= dados_c["limite_bi"]: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Bifásico", "16.0 mm²", "63 A", dados_c["caixa_bi"]
    else: tipo_entrada, cabo_padrao, dj_padrao, detalhe_caixa = "Trifásico", "25.0 mm²", "80 A", dados_c["caixa_tri"]

    elementos.append(Paragraph(f"<b>Padrão de Entrada Homologado ({concessionaria_sel})</b>", estilo_sub))
    dados_padrao_pdf = [
        [Paragraph("<b>Parâmetro Normativo</b>", estilo_celula), Paragraph("<b>Especificação Técnica Regulamentar</b>", estilo_celula_esq)],
        [Paragraph("Norma Técnica da Concessionária", estilo_celula), Paragraph(dados_c["norma"], estilo_celula_esq)],
        [Paragraph("Tipo de Fornecimento / Padrão de Entrada", estilo_celula), Paragraph(f"{tipo_entrada} - ({detalhe_caixa})", estilo_celula_esq)],
        [Paragraph("Cabo do Ramal Geral (Cobre)", estilo_celula), Paragraph(cabo_padrao, estilo_celula_esq)],
        [Paragraph("Disjuntor Geral da Caixa", estilo_celula), Paragraph(dj_padrao, estilo_celula_esq)]
    ]
    t_pad = Table(dados_padrao_pdf, colWidths=[240.0, 500.0])
    t_pad.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D9488')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
    elementos.append(t_pad)

    if st.session_state.lista_circuitos_calc:
        elementos.append(PageBreak())
        elementos.append(Paragraph("1. Mapeamento Geral de Cargas com Vínculo Relacional de Cômodos", estilo_sub))
        cabecalhos_modelo = ["CIRC", "DESCRIÇÃO DO CIRCUITO TERMINAL", "CÔMODO ALOCADO", "POT (W)", "DIST (M)", "CORRENTE (A)", "DISJ", "BITOLA", "FASE", "TENSÃO", "FAS R", "FAS S"]
        dados_qdc_pdf = [[Paragraph(f"<b>{h}</b>", estilo_celula) for h in cabecalhos_modelo]]
        tot_r, tot_s = 0, 0
        for c in st.session_state.lista_circuitos_calc:
            p_w_val = int(c["POT_W"])
            r_val = p_w_val if c["FASE"] == "R" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            s_val = p_w_val if c["FASE"] == "S" else (p_w_val//2 if "RS" in c["FASE"] else 0)
            tot_r += r_val; tot_s += s_val
            dados_qdc_pdf.append([Paragraph(str(c["CIRC"]), estilo_celula), Paragraph(str(c["DESCRIÇÃO"]), estilo_celula_esq), Paragraph(str(c.get("COMODO","Geral")), estilo_celula), Paragraph(str(p_w_val), estilo_celula), Paragraph(f"{c['COMP']}m", estilo_celula), Paragraph(f"{c['IB']}A", estilo_celula), Paragraph(f"{c['CURVA']}{c['DISJ']}", estilo_celula), Paragraph(str(c["COND"]), estilo_celula), Paragraph(c["FASE"], estilo_celula), Paragraph(f"{c['TENSÃO']}V", estilo_celula), Paragraph(f"{r_val}VA", estilo_celula), Paragraph(f"{s_val}VA", estilo_celula)])
        dados_qdc_pdf.append([Paragraph(f"<b>Potência Instalada Total: {pot_total_sistema} W | R: {tot_r}VA | S: {tot_s}VA</b>", estilo_celula)] + [""] * 11)
        t_qdc = Table(dados_qdc_pdf, colWidths=[30.0, 160.0, 80.0, 45.0, 45.0, 55.0, 40.0, 50.0, 35.0, 40.0, 50.0, 50.0])
        t_qdc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')), ('SPAN', (0,-1), (-1,-1)), ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')), ('PADDING', (0,0), (-1,-1), 3), ('ALIGN', (0,-1), (-1,-1), 'CENTER')]))
        elementos.append(t_qdc)

    listas_gerais_obra = [
        ("2. Memorial Quantitativo da Alvenaria e Cubagem Civil", st.session_state.lista_materials_civil, '#475569'),
        ("3. Lote Hidráulico e Redes de Esgoto Sanitário", st.session_state.lista_materials_hidraulicos, '#1E40AF'),
        ("4. Infraestrutura e Tubulações de Gás Encanado (GLP/GN)", st.session_state.lista_materials_gas, '#B45309'),
        ("5. Cabeamento Estruturado e Rede de Internet/Dados", st.session_state.lista_materials_dados, '#6D28D9'),
        ("6. Lote de Ativos e Segurança Eletrônica Monitorável", st.session_state.lista_materials_seguranca, '#0F172A')
    ]
    for tit, lista, cor_hex in listas_gerais_obra:
        if lista:
            elementos.append(PageBreak())
            elementos.append(Paragraph(tit, estilo_sub))
            tbl_d = [[Paragraph("<b>Etapa</b>", estilo_celula), Paragraph("<b>Insumo Otimizado</b>", estilo_celula_esq), Paragraph("<b>Quantidade</b>", estilo_celula), Paragraph("<b>Unidade</b>", estilo_celula)]]
            for mat in lista: tbl_d.append([Paragraph(mat["Etapa"], estilo_celula), Paragraph(mat["Material"], estilo_celula_esq), Paragraph(str(mat["Quantidade"]), estilo_celula), Paragraph(mat["Unidade"], estilo_celula)])
            t_m = Table(tbl_d, colWidths=[130.0, 390.0, 140.0, 80.0])
            t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor(cor_hex)), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('PADDING', (0,0), (-1,-1), 3)]))
            elementos.append(t_m)

    elementos.append(PageBreak())
    elementos.append(Paragraph("7. Diagrama Unifilar e Distribuição de Barramentos", estilo_sub))
    elementos.append(gerar_desenho_unifilar(cabo_padrao, dj_padrao, st.session_state.lista_circuitos_calc))
    elementos.append(PageBreak())
    elementos.append(Paragraph("8. Esquema Técnico Multifilar de Bornes por Fase", estilo_sub))
    elementos.append(gerar_desenho_multifilar(st.session_state.lista_circuitos_calc))

    elementos.append(PageBreak())
    elementos.append(Paragraph("9. Diretrizes Técnicas e Normativas de Campo", estilo_sub))
    caviso = [
        Paragraph("<b>📝 DIRETRIZES DE CAMPO - REGRAS DE EXECUÇÃO NBR 5410 & NR-10</b>", estilo_aviso_tit),
        Spacer(1, 4),
        Paragraph("• <b>Padrão de Cores dos Condutores:</b> É obrigatório respeitar estritamente a padronização de cores desta instalação: 🟢 VERDE: Condutor de Proteção (Terra) | 🔵 AZUL: Condutor Neutro | ⚫🔴🟡 PRETO / VERMELHO / AMARELO: Condutores de Fase | ⚪⚪ BRANCO / CINZA: Condutores de Retorno.", estilo_aviso_corpo),
        Paragraph("• <b>Identificação de Circuitos:</b> É obrigatório manter todos os disjuntores devidamente identificados nesta tampa de acordo com a fiação correspondente.", estilo_aviso_corpo),
        Paragraph("• <b>Teste Mensal do DR:</b> Pressione o botão 'T' (Teste) do interruptor diferencial residual mensalmente. Se ele não desarmar e desligar a energia da casa, substitua-o imediatamente.", estilo_aviso_corpo),
        Paragraph("• <b>Inspeção do DPS:</b> Verifique o indicador visual do protetor de surto regularmente. Janela verde indica funcionamento normal; janela vermelha exige substituição imediata.", estilo_aviso_corpo),
        Paragraph("• <b>Seção vs. Disjuntor:</b> Nunca aumente a amperagem de um disjuntor sem recalcular a fiação. O disjuntor protege o fio; alterar o valor sem critério técnico causa incêndio.", estilo_aviso_corpo)
    ]
    t_av = Table([[caviso]], colWidths=[740.0])
    t_av.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFBEB')), ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#D97706')), ('PADDING', (0,0), (-1,-1), 10)]))
    elementos.append(t_av)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

with tab_pdf:
    st.write("### 🖨️ Central de Emissão")
    st.download_button(label="📥 Baixar Memorial Técnico Consolidado da Obra Completa (PDF)", data=gerar_pdf_completo_obra(), file_name="memorial_de_engenharia_unificado.pdf", mime="application/pdf", key="btn_pdf_real")
