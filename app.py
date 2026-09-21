import streamlit as st
import pandas as pd

# Configuração primária obrigatória
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# Inicialização limpa da memória local
if "dados_eletricos" not in st.session_state:
    st.session_state.dados_eletricos = []

st.title("⚡ Fênix EngCalculus Pro")
st.subheader("Painel de Levantamento Quantitativo Elétrico")

st.markdown("---")

# Formulário de entrada simples e direto
st.write("### 🛠️ Inserir Novo Item Elétrico")

c1, c2, c3 = st.columns(3)

with c1:
    categoria = st.selectbox(
        "Setor do Serviço:",
        ["Infraestrutura", "Condutores e Cabos", "Dispositivos e Tomadas", "Quadros e Segurança", "Iluminação"],
        key="setor_eletrico"
    )
    descricao = st.text_input("Descrição:", placeholder="Ex: Eletroduto corrugado 3/4", key="desc_eletrico")

with c2:
    quantidade = st.number_input("Quantidade:", min_value=1.0, value=1.0, step=1.0, key="qtd_eletrico")
    unidade = st.selectbox("Unidade:", ["m", "un", "ponto", "cj", "h"], key="uni_eletrico")

with c3:
    preco = st.number_input("Preço Unitário (R$):", min_value=0.0, value=0.0, step=1.0, key="pr_eletrico")

# Cálculo total do item lançado
total_item = quantidade * preco

# Botão de ação direta
if st.button("➕ Adicionar ao Quadro", key="btn_adicionar_item"):
    if not descricao:
        st.error("Por favor, preencha a descrição do item.")
    elif total_item <= 0:
        st.error("A quantidade e o preço devem ser maiores que zero.")
    else:
        # Armazena os dados brutos na sessão do Streamlit
        st.session_state.dados_eletricos.append({
            "Categoria": categoria,
            "Descrição": descricao,
            "Quantidade": quantidade,
            "Unidade": unidade,
            "Preço Unitário (R$)": preco,
            "Total (R$)": total_item
        })
        st.success("Item adicionado com sucesso!")
        st.preload = True
        st.rerun()

st.markdown("---")

# Exibição do Quadro de Resultados
st.write("### 📊 Relatório Quantitativo")

if st.session_state.dados_eletricos:
    # Conversão segura para tabela estruturada do Pandas
    df_quadro = pd.DataFrame(st.session_state.dados_eletricos)
    st.dataframe(df_quadro, use_container_width=True)
    
    # Exibição do valor total somado
    valor_final = df_quadro["Total (R$)"].sum()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.metric(label="Custo Total Acumulado", value=f"R$ {valor_final:,.2f}")
    
    with col_f2:
        # Geração do arquivo para baixar e abrir no Excel
        csv_data = df_quadro.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Planilha (CSV)",
            data=csv_data,
            file_name="quantitativo_fenix.csv",
            mime="text/csv",
            key="btn_csv_final"
        )
        
    if st.button("🗑️ Limpar Tudo", key="btn_limpar_tudo"):
        st.session_state.dados_eletricos = []
        st.rerun()
else:
    st.info("Nenhum item elétrico cadastrado no momento.")
