from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Paleta de Cores Corporativas Homologada para A4 Portrait
COR_PRIMARIA = colors.HexColor('#1E3A8A')
COR_SECUNDARIA = colors.HexColor('#475569')
COR_ALERTA = colors.HexColor('#D97706')
COR_FUNDO_AVISO = colors.HexColor('#FFFBEB')

def obter_estilos_pdf():
    estilos = getSampleStyleSheet()
    
    estilo_sub = ParagraphStyle('SubTitulo', parent=estilos['Heading2'], fontSize=14, textColor=COR_PRIMARIA, spaceAfter=10)
    estilo_celula = ParagraphStyle('Celula', parent=estilos['Normal'], fontSize=9, alignment=1)
    estilo_celula_esq = ParagraphStyle('CelulaEsq', parent=estilos['Normal'], fontSize=9, alignment=0)
    estilo_aviso_tit = ParagraphStyle('AvisoTit', parent=estilos['Normal'], fontSize=10, textColor=COR_ALERTA)
    estilo_aviso_corpo = ParagraphStyle('AvisoCorpo', parent=estilos['Normal'], fontSize=8.5)
    
    return estilo_sub, estilo_celula, estilo_celula_esq, estilo_aviso_tit, estilo_aviso_corpo

def banner_sidebar():
    return "<h2 style='color:#FFFFFF; background-color:#1E3A8A; padding:10px; border-radius:5px; text-align:center;'>⚙️ CENTRAL FÊNIX</h2>"
