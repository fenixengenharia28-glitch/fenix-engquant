import streamlit as st
import pandas as pd

# Configuração da página (Primeiro comando obrigatório)
st.set_page_config(page_title="Fênix EngCalculus Pro - Elétrica", layout="wide", page_icon="⚡")

# Inicialização segura da memória do orçamento (Salvamento automático)
if "servicos_eletricos" not in st.session_state:
    st.session_state.servicos_eletricos = []

st.title("⚡ Fênix EngCalculus Pro")
st.subheader("Levantamento Quantitativo de Serviços Elétricos")

# Painel de Entrada de Dados
st.header("🛠️ Lançamento de Serviços")

col1, col2, col3 = st.columns(3)

with col1:
    categoria = st.selectbox(
        "Categoria do Serviço:",
        [
            "Infraestrutura (Eletrodutos, Caixas, Perfilados)",
            "Condutores (Passagem de Cabos e Fios)",
            "Dispositivos (Tomadas, Interruptores, Disjuntores)",
            "Montagem de Painéis (QDC, Barramentos, DPS/IDR)",
            "Luminotécnica (Luminárias, Spots, Fitas LED)"
        ],
        key="sb_categoria"
    )
    
    descricao = st.text_input(
        "Descrição Detalhada do Serviço:", 
        placeholder="Ex: Passagem de cabo flexível 2,5mm²",
        key="ti_descricao"
    )

with col2:
    quantidade = st.number_input(
        "Quantidade Métrica:", 
        min_value=0.0, 
        value=1.0, 
        step=1.0,
        key="ni_quantidade"
    )
    
    unidade = st.selectbox(
        "Unidade de Medida:",
        ["m (Metro)", "un (Unidade)", "ponto", "cj (Conjunto)", "h (Hora)"],
        key="sb_unidade"
    )

with col3:
    preco_unitario = st.number_input(
        "Preço Unitário (R$):", 
        min_value=0.0, 
        value=0.0, 
        step=5.0,
        key="ni_preco"
    )

# Cálculo em tempo real do item atual
total_item = quantidade * preco_unitario

# Botão para adicionar o serviço à lista
if st.button("➕ Adicionar Serviço ao Orçamento", key="btn_adicionar"):
    if descricao.strip() == "":
        st.error("❌ Por favor, digite uma descrição para o serviço.")
    elif total_item <= 0:
        st.error("❌ O preço unitário ou a quantidade deve ser maior que zero.")
    else:
        # Salva o serviço na memória do aplicativo
        st.session_state.servicos_eletricos.append({
            "Categoria": categoria,
            "Descrição": descricao,
            "Quantidade": quantidade,
            "Unidade": unidade.split(" ")[0],  # Pega apenas a sigla (ex: 'm' ou 'un')
            "Preço Unitário (R$)": preco_unitario,
            "Total (R$)": total_item
        })
        st.success(f"✔️ '{descricao}' adicionado com sucesso!")
        st.rerun()

# ----------------------------------------------------
# VISUALIZAÇÃO DO ORÇAMENTO E QUADRO GERAL
# ----------------------------------------------------
st.markdown("---")
st.header("📊 Quadro Quantitativo Consolidado")

if st.session_state.servicos_eletricos:
    # Transforma a lista de serviços salvos em uma tabela (DataFrame)
    df_orcamento = pd.DataFrame(st.session_state.servicos_eletricos)
    
    # Exibe a tabela na tela de forma interativa
    st.dataframe(df_orcamento, use_container_width=True)
    
    # Cálculos de fechamento
    valor_total_eletrica = df_orcamento["Total (R$)"].sum()
    
    col_tot1, col_tot2 = st.columns(2)
    with col_tot1:
        st.metric(label="Valor Total dos Serviços Elétricos", value=f"R$ {valor_total_eletrica:,.2f}")
    
    with col_tot2:
        # Botão para exportar os dados para Excel/CSV
        csv_buffer = df_orcamento.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Planilha de Quantitativos (CSV)",
            data=csv_buffer,
            file_name="quantitativo_eletrico_fenix.csv",
            mime="text/csv",
            key="btn_download"
        )
    
    # Botão para limpar a tabela e começar outro projeto
    if st.button("🗑️ Zerar Quantitativos", key="btn_zerar"):
        st.session_state.servicos_eletricos = []
        st.rerun()
else:
    st.info("Nenhum serviço elétrico foi lançado ainda. Utilize o painel acima para começar.")
