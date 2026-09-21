import streamlit as st
import pandas as pd

# Configuração da página - DEVE ser o primeiro comando Streamlit
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# 1. CRIAÇÃO DOS DATASET DE REFERÊNCIA NATIVOS E CORRIGIDOS
df_cabos = pd.DataFrame({
    "Seção Nominal (mm²)": [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0],
    "Aplicação Mínima": ["Iluminação", "Tomadas Gerais (TUG)", "Circuitos Pesados", "Ar/Chuveiro", "Alimentação QDC", "Entrada Padrão", "Entrada Tri", "Entrada Industrial"],
    "Capacidade Corrente B1 (A)": [17.5, 24.0, 32.0, 41.0, 57.0, 76.0, 101.0, 125.0]
})

df_agrupamento = pd.DataFrame({
    "Nº de Circuitos no Tubo":,
    "Fator de Redução (Fg)": [1.00, 0.80, 0.70, 0.65, 0.60]
})

df_servicos = pd.DataFrame({
    "Etapa da Obra": ["01. Preliminares", "01. Preliminares", "02. Infraestrutura", "02. Infraestrutura", "03. Alvenaria", "03. Alvenaria", "04. Acabamento", "04. Acabamento"],
    "Serviço / Insumo": ["Limpeza Mecanizada de Terreno", "Locação de Obra (Gabarito)", "Escavação Manual de Sapatas", "Concreto Usinado Fck=30MPa", "Alvenaria em Blocos ICF (iForms)", "Alvenaria Tijolo Baiano 8 Furos", "Instalação de Porcelanato", "Pintura Látex PVA (Duas Mãos)"],
    "Unidade": ["m²", "m²", "m³", "m³", "m²", "m²", "m²", "m²"],
    "Rendimento Estimado / Consumo": ["1.00 m²/m²", "1.00 m²/m²", "1.30 h/m³", "1.05 m³/m³", "1.00 m²/m²", "23.00 un/m²", "1.05 m²/m²", "0.25 L/m²"]
})

# Inicialização segura das variáveis de sessão
if "circuitos" not in st.session_state:
    st.session_state.circuitos = []
if "servicos_lancados" not in st.session_state:
    st.session_state.servicos_lancados = []

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("Plataforma ERP Integrada de Engenharia: Construção Civil & Instalações Elétricas")

# Criação das abas de interface
aba1, aba2, aba3, aba4 = st.tabs([
    "🧱 1. Serviços e Construção Civil", 
    "⚡ 2. Mapeamento & Dimensionamento Elétrico", 
    "📊 3. Central de Tabelas Técnicas",
    "📋 4. Quadro Geral e Fechamento"
])

# ----------------------------------------------------
# ABA 1: SERVIÇOS E CONSTRUÇÃO CIVIL
# ----------------------------------------------------
with aba1:
    st.header("🧱 Levantamento de Escopo e Serviços Civis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        etapas_disponiveis = list(df_servicos["Etapa da Obra"].unique())
        etapa_sel = st.selectbox("Selecione a Etapa:", etapas_disponiveis, key="sb_etapa_civil")
        
        servicos_filtrados = df_servicos[df_servicos["Etapa da Obra"] == etapa_sel]["Serviço / Insumo"].tolist()
        servico_sel = st.selectbox("Selecione o Serviço Correspondente:", servicos_filtrados, key="sb_serv_civil")
        
    with col2:
        qtd_solicitada = st.number_input("Insira a Quantidade da Carga/Área:", min_value=0.0, value=10.0, step=1.0, key="ni_qtd_civil")
        unidade_lista = df_servicos[df_servicos["Serviço / Insumo"] == servico_sel]["Unidade"].values
        unidade_padrao = str(unidade_lista[0]) if len(unidade_lista) > 0 else "un"
        st.info(f"Unidade Métrica: {unidade_padrao}")
        
    with col3:
        preco_unitario = st.number_input("Preço Unitário Praticado (R$):", min_value=0.0, value=50.0, step=5.0, key="ni_preco_civil")
        
    total_servico = qtd_solicitada * preco_unitario
    
    if st.button("Lançar Serviço Civil", key="btn_lancar_civil_ok"):
        st.session_state.servicos_lancados.append({
            "Módulo": "Construção Civil",
            "Serviço/Item": f"[{etapa_sel}] {servico_sel}",
            "Quantidade": qtd_solicitada,
            "Unidade": unidade_padrao,
            "Preço Unitário (R$)": preco_unitario,
            "Total (R$)": total_servico,
            "Cabo (mm²)": "-",
            "Corrente (A)": 0.0
        })
        st.success("Item civil computado com sucesso!")
        st.rerun()

# ----------------------------------------------------
# ABA 2: MAPEAMENTO E DIMENSIONAMENTO ELÉTRICO
# ----------------------------------------------------
with aba2:
    st.header("⚡ Inteligência Elétrica NBR 5410")
    
    col1_el, col2_el, col3_el = st.columns(3)
    with col1_el:
        id_circuito = st.text_input("Nome do Circuito:", placeholder="Ex: Chuveiro Master, TUGs Sala", key="ti_nome_circ")
        tipo_carga = st.selectbox("Classificação da Carga:", ["Iluminação", "Tomadas Gerais (TUG)", "Circuitos Pesados / TUE"], key="sb_tipo_carga")
        
    with col2_el:
        potencia_watts = st.number_input("Potência Estimada (W):", min_value=0, value=2200, step=100, key="ni_pot_el")
        tensao_volts = st.selectbox("Tensão Nominal (V):", [127, 220, 380], key="sb_tensao_el")
        
    with col3_el:
        n_agrupados = st.slider("Quantidade de Circuitos no mesmo Eletroduto:", 1, 5, 2, key="sl_agrupamento")
        
    # Processamento matemático do dimensionamento elétrico
    f_reducao_lista = df_agrupamento[df_agrupamento["Nº de Circuitos no Tubo"] == n_agrupados]["Fator de Redução (Fg)"].values
    f_reducao = float(f_reducao_lista[0]) if len(f_reducao_lista) > 0 else 1.0
    
    corrente_projeto = potencia_watts / tensao_volts if tensao_volts > 0 else 0
    corrente_corrigida = corrente_projeto / f_reducao if f_reducao > 0 else corrente_projeto
    
    secao_min = 1.5 if tipo_carga == "Iluminação" else 2.5
    secao_calculada = secao_min
    
    for _, linha in df_cabos.iterrows():
        if linha["Seção Nominal (mm²)"] >= secao_min and linha["Capacidade Corrente B1 (A)"] >= corrente_corrigida:
            secao_calculada = linha["Seção Nominal (mm²)"]
            break

    st.info(f"📊 Análise: Corrente Ib: {corrente_projeto:.2f}A | Corrente Corrigida: {corrente_corrigida:.2f}A | Cabo sugerido: {secao_calculada} mm²")
    
    if st.button("Salvar e Dimensionar Circuito", key="btn_lancar_eletrico_ok"):
        if id_circuito:
            st.session_state.circuitos.append({
                "Módulo": "Elétrica",
                "Serviço/Item": f"Circuito: {id_circuito} ({tipo_carga}) - {potencia_watts}W",
                "Quantidade": 1.0,
                "Unidade": "un",
                "Preço Unitário (R$)": round(corrente_projeto * 12.0, 2),
                "Total (R$)": round(corrente_projeto * 12.0, 2),
                "Cabo (mm²)": str(secao_calculada),
                "Corrente (A)": round(corrente_projeto, 2)
            })
            st.success(f"Circuito {id_circuito} integrado ao barramento!")
            st.rerun()
        else:
            st.error("Por favor, digite o nome do circuito antes de salvar.")

# ----------------------------------------------------
# ABA 3: CENTRAL DE TABELAS TÉCNICAS
# ----------------------------------------------------
with aba3:
    st.header("📋 Tabelas Normativas do Sistema")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Capacidade de Condução de Cabos (Cobre/PVC - Método B1)")
        st.dataframe(df_cabos, use_container_width=True)
    with c2:
        st.subheader("Fatores de Agrupamento de Circuitos")
        st.dataframe(df_agrupamento, use_container_width=True)
        
    st.subheader("Dicionário de Insumos da Construção Civil")
    st.dataframe(df_servicos, use_container_width=True)

# ----------------------------------------------------
# ABA 4: QUADRO GERAL E FECHAMENTO
# ----------------------------------------------------
with aba4:
    st.header("📊 Fechamento do Orçamento e Engenharia")
    todos_itens = st.session_state.servicos_lancados + st.session_state.circuitos
    
    if todos_itens:
        df_final = pd.DataFrame(todos_itens)
        colunas_exibicao = ["Módulo", "Serviço/Item", "Quantidade", "Unidade", "Preço Unitário (R$)", "Total (R$)", "Cabo (mm²)", "Corrente (A)"]
        st.dataframe(df_final[colunas_exibicao], use_container_width=True)
        
        custo_total_geral = df_final["Total (R$)"].sum()
        st.metric(label="Valor Orçado Total (Fênix Engenharia)", value=f"R$ {custo_total_geral:,.2f}")
        
        csv_buffer = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Relatório Técnico Consolidado", data=csv_buffer, file_name="orcamento_fenix_pro.csv", mime="text/csv", key="btn_download_csv_ok")
        
        if st.button("Zerar Sistema", key="btn_zerar_tudo_ok"):
            st.session_state.circuitos = []
            st.session_state.servicos_lancados = []
            st.rerun()
    else:
        st.info("Nenhum lançamento efetuado nesta sessão de projeto.")
