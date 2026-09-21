import streamlit as st
import pandas as pd
import math

# 1. Configuração inicial da página (Obrigatório ser o primeiro comando)
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

st.title("🏗️ Fênix EngCalculus Pro")
st.subheader("Dimensionador Autônomo de Engenharia Elétrica Residencial")
st.markdown("---")

# 2. Banco de dados de concessionárias brasileiras e seus limites normativos
CONCESSIONARIAS = {
    "CEMIG (Minas Gerais)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 15000, "nome": "CEMIG"},
    "ENEL (São Paulo)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "nome": "ENEL_SP"},
    "ENEL (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "nome": "ENEL_RJ"},
    "CPFL (Paulista/Piratininga)": {"fase": 127, "linha": 220, "limite_mono": 12000, "limite_bi": 25000, "nome": "CPFL"},
    "LIGHT (Rio de Janeiro)": {"fase": 127, "linha": 220, "limite_mono": 8000, "limite_bi": 15000, "nome": "LIGHT"},
    "COPEL (Paraná)": {"fase": 127, "linha": 220, "limite_mono": 10000, "limite_bi": 24000, "nome": "COPEL"},
    "CELESC (Santa Catarina)": {"fase": 220, "linha": 380, "limite_mono": 15000, "limite_bi": 25000, "nome": "CELESC"},
    "NEOENERGIA (Coelba/Celpe/Cosern/Elektro/DF)": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "nome": "NEOENERGIA"},
    "EQUATORIAL (Maranhão/Pará/Piauí/Alagoas)": {"fase": 220, "linha": 380, "limite_mono": 10000, "limite_bi": 15000, "nome": "EQUATORIAL"}
}

# 3. Painel de entrada de dados do projeto
col_input1, col_input2 = st.columns(2)

with col_input1:
    concessionaria_sel = st.selectbox(
        "🔌 Escolha a Concessionária de Energia da Obra:",
        list(CONCESSIONARIAS.keys()),
        key="sb_concessionaria"
    )
    dados_c = CONCESSIONARIAS[concessionaria_sel]

with col_input2:
    area_imovel = st.number_input(
        "🏡 Área Construída Total da Casa (m²):",
        min_value=10.0,
        value=70.0,
        step=5.0,
        key="ni_area_casa"
    )

# 4. Questionário simplificado de cargas especiais (TUEs)
st.write("### 🎛️ Selecione os Equipamentos de Alta Potência da Casa:")
c_tue1, c_tue2, c_tue3 = st.columns(3)

with c_tue1:
    qtd_chuveiro = st.number_input("Chuveiros Elétricos (7500W):", min_value=0, value=1, step=1, key="tue_chuveiro")
with c_tue2:
    qtd_ar = st.number_input("Aparelhos de Ar Condicionado (2000W):", min_value=0, value=1, step=1, key="tue_ar")
with c_tue3:
    tem_microondas = st.checkbox("Forno Micro-ondas / Forno Elétrico (2500W)", value=True, key="tue_forno")

# --- ALGORITMO DE ENGENHARIA AUTOMÁTICO (Cálculos Internos) ---
# Cálculo de Carga Mínima Estimada por m² (NBR 5410)
potencia_iluminacao = 1500 if area_imovel <= 60 else 1500 + (math.ceil((area_imovel - 60)/15) * 500)
potencia_tug = 3000 if area_imovel <= 60 else 3000 + (math.ceil((area_imovel - 60)/20) * 600)
potencia_tue = (qtd_chuveiro * 7500) + (qtd_ar * 2000) + (2500 if tem_microondas else 0)

potencia_instalada_total = potencia_iluminacao + potencia_tug + potencia_tue

# Fator de Demanda aplicado à carga total residencial
fator_demanda = 0.52 if potencia_instalada_total > 10000 else 0.65
potencia_demandada = potencia_instalada_total * fator_demanda

# Determinação da tensão de atendimento principal da casa
tensao_geral = dados_c["linha"] if potencia_demandada > dados_c["limite_mono"] else dados_c["fase"]
corrente_demanda_geral = potencia_demandada / tensao_geral

# --- GERADOR AUTOMÁTICO DO QUADRO DE CIRCUITOS E QUANTITATIVOS ---
lista_circuitos = []

# Circuito 1: Iluminação Geral
lista_circuitos.append({
    "Nº": "📌 Circuito 01", "Descrição": "Iluminação Geral da Residência",
    "Potência (W)": potencia_iluminacao, "Tensão (V)": dados_c["fase"],
    "Bitola do Cabo": "1.5 mm²", "Disjuntor Recomendado": "10 A", "Tipo": "Distribuição"
})

# Circuito 2 e 3: Divisão automática de Tomadas Gerais (TUGs)
n_circuitos_tug = 2 if area_imovel > 80 else 1
for i in range(n_circuitos_tug):
    lista_circuitos.append({
        "Nº": f"📌 Circuito 0{2+i}", "Descrição": f"Tomadas de Uso Geral (TUGs) - Setor {i+1}",
        "Potência (W)": round(potencia_tug / n_circuitos_tug, 0), "Tensão (V)": dados_c["fase"],
        "Bitola do Cabo": "2.5 mm²", "Disjuntor Recomendado": "20 A", "Tipo": "Distribuição"
    })

# Circuitos Especiais Dinâmicos (TUEs)
contador_c = 2 + n_circuitos_tug
if qtd_chuveiro > 0:
    for i in range(qtd_chuveiro):
        contador_c += 1
        lista_circuitos.append({
            "Nº": f"📌 Circuito 0{contador_c}", "Descrição": f"Chuveiro Elétrico da Suíte / Banheiro {i+1}",
            "Potência (W)": 7500, "Tensão (V)": dados_c["linha"],
            "Bitola do Cabo": "6.0 mm²", "Disjuntor Recomendado": "40 A", "Tipo": "Exclusivo"
        })
if qtd_ar > 0:
    for i in range(qtd_ar):
        contador_c += 1
        lista_circuitos.append({
            "Nº": f"📌 Circuito 0{contador_c}", "Descrição": f"Ar Condicionado Dormitório/Sala {i+1}",
            "Potência (W)": 2000, "Tensão (V)": dados_c["fase"],
            "Bitola do Cabo": "2.5 mm²", "Disjuntor Recomendado": "16 A", "Tipo": "Exclusivo"
        })
if tem_microondas:
    contador_c += 1
    lista_circuitos.append({
        "Nº": f"📌 Circuito 0{contador_c}", "Descrição": "Cozinha - Circuito do Forno / Micro-ondas",
        "Potência (W)": 2500, "Tensão (V)": dados_c["fase"],
        "Bitola do Cabo": "4.0 mm²", "Disjuntor Recomendado": "25 A", "Tipo": "Exclusivo"
    })

# --- DETERMINAÇÃO DO PADRÃO DE ENTRADA CONFORME AGÊNCIA REGULADORA ---
if potencia_instalada_total <= dados_c["limite_mono"]:
    tipo_entrada = "Monofásico"
    cabo_padrao = "10.0 mm²"
    disjuntor_padrao = "40 A ou 50 A"
elif potencia_instalada_total <= dados_c["limite_bi"]:
    tipo_entrada = "Bifásico"
    cabo_padrao = "16.0 mm²"
    disjuntor_padrao = "63 A"
else:
    tipo_entrada = "Trifásico"
    cabo_padrao = "25.0 mm²"
    disjuntor_padrao = "80 A"

# --- INTERFACE DE EXIBIÇÃO DE RESULTADOS NA TELA ---
st.markdown("---")
st.header("📋 Memorial de Cálculo e Dimensionamento Gerado")

tab1, tab2, tab3 = st.tabs(["🎛️ Quadro de Circuitos (QDC)", "🛡️ Sistema de Segurança Elétrica", "🏢 Padrão da Concessionária"])

with tab1:
    st.subheader("Quadro de Distribuição de Circuitos Otimizado")
    df_qdc = pd.DataFrame(lista_circuitos)
    st.dataframe(df_qdc, use_container_width=True)

with tab2:
    st.subheader("Dispositivos de Proteção e Segurança Contra Choque e Surtos (NBR 5410)")
    
    c_sec1, c_sec2, c_sec3 = st.columns(3)
    with c_sec1:
        st.metric("Dispositivo IDR Geral", "Disjuntor DR 63A - 30mA", help="Proteção contra choques elétricos.")
    with c_sec2:
        st.metric("Módulos DPS Tipo II", "Classe II - 45kA / 275V", help="Proteção contra surtos e quedas de raios.")
    with c_sec3:
        st.metric("Sistema de Aterramento Mínimo", "Malha com 3 Hastes de Cobre de 2,40m")

with tab3:
    st.subheader(f"Especificações para Homologação na {concessionaria_sel}")
    
    c_pad1, c_pad2, c_pad3 = st.columns(3)
    with c_pad1:
        st.metric("Tipo de Ligação", tipo_entrada)
    with c_pad2:
        st.metric("Cabo do Ramal de Entrada", cabo_padrao)
    with c_pad3:
        st.metric("Disjuntor Geral da Caixa", disjuntor_padrao)

st.markdown("---")
# Botão para baixar tudo direto para o Excel/Planilhas
csv_buffer = df_qdc.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Exportar Dados de Dimensionamento (CSV)",
    data=csv_buffer,
    file_name="dimensionamento_eletrico_automatico.csv",
    mime="text/csv",
    key="btn_download_final_ok"
)
