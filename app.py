import streamlit as st
# Importando seus próprios módulos separados
from database.fenix_db import init_db, listar_clientes_db
from engines.calculus import dimensionar_circuito_nbr5410_mda
from engines.report_gen import gerar_pdf_completo_obra

# Configuração da página
st.set_page_config(page_title="Fênix EngCalculus Pro", layout="wide", page_icon="⚡")

# Inicializa o banco
init_db()

def main():
    st.write("## 🏗️ Fênix EngCalculus Pro")
    # ... aqui você monta suas abas chamando as funções dos outros arquivos ...

if __name__ == "__main__":
    main()
