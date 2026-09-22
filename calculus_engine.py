from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.lib import colors

def dimensionar_circuito_nbr5410_mda(potencia, tensao, comprimento, tipo_carga, fca=0.70, fct=1.0):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.80
    potencia_va = potencia / fp
    ib = potencia / (tensao * fp)
    ib_corrigida = ib / (fca * fct)
    bitola_inicial = 1.5 if "Iluminação" in tipo_carga else 2.5
    bitolas_comerciais = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0]
    capacidades_corrente = [17.5, 24.0, 32.0, 41.0, 57.0, 76.0]
    bitola_final = bitola_inicial
    iz_cabo = 17.5 if "Iluminação" in tipo_carga else 24.0
    for b, cap in zip(bitolas_comerciais, capacidades_corrente):
        if b >= bitola_inicial and cap >= ib_corrigida:
            bitola_final = b
            iz_cabo = cap
            break
    rho = 1 / 58.0
    while True:
        dv_perc = (2 * rho * comprimento * ib * 100) / (tensao * bitola_final)
        if dv_perc <= 2.0 or bitola_final >= 16.0: 
            break
        idx = bitolas_comerciais.index(bitola_final)
        if idx < len(bitolas_comerciais) - 1:
            bitola_final = bitolas_comerciais[idx + 1]
            iz_cabo = capacidades_corrente[idx + 1]
        else: 
            break
    disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]
    disjuntor_final = 20
    for dj in disjuntores_comerciais:
        if dj >= ib and dj <= (iz_cabo * fca * fct):
            disjuntor_final = dj
            break
        elif dj >= ib:
            disjuntor_final = dj
            break
    return {
        "BITOLA": bitola_final, "DISJUNTORES": disjuntor_final, "CURVA": "B" if "Iluminação" in tipo_carga else "C",
        "IB": round(ib, 2), "IB_CORR": round(ib_corrigida, 2), "VA": round(potencia_va, 2), "FP": fp,
        "DV": round((2 * rho * comprimento * ib * 100) / (tensao * bitola_final), 2)
    }

def gerar_desenho_unifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(240, (n_circ * 30) + 130)
    d = Drawing(720, altura_d)
    d.add(Line(20, altura_d - 40, 90, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(20, altura_d - 32, f"Ramal BT: {cabo_pad}", fontSize=8, fontName='Helvetica-Bold'))
    d.add(Rect(90, altura_d - 52, 45, 24, fillColor=colors.HexColor('#EFF6FF'), strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(95, altura_d - 44, "DJ Geral", fontSize=7, fontName='Helvetica-Bold'))
    d.add(String(95, altura_d - 51, f"{dj_pad}", fontSize=6.5, fontName='Helvetica'))
    d.add(Line(135, altura_d - 40, 160, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Rect(160, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(166, altura_d - 44, "DPS", fontSize=7, fontName='Helvetica-Bold'))
    d.add(Line(195, altura_d - 40, 215, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Rect(215, altura_d - 52, 35, 24, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(222, altura_d - 44, "IDR", fontSize=7, fontName='Helvetica-Bold'))
    d.add(Line(250, altura_d - 40, 280, altura_d - 40, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 40, 280, 20, strokeColor=colors.black, strokeWidth=2))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 80) - (idx * 30)
        d.add(Circle(280, y, 2, fillColor=colors.black, strokeColor=colors.black))
        d.add(Line(280, y, 320, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(Line(320, y, 335, y - 8, strokeColor=colors.black, strokeWidth=1.5))
        d.add(String(315, y + 5, f"{c.get('CURVA','C')}{c.get('DISJ','20A')}", fontSize=7, fontName='Helvetica-Bold'))
        d.add(Line(335, y, 365, y, strokeColor=colors.black, strokeWidth=1.2))
        d.add(String(340, y + 4, str(c.get('COND','2.5 mm²')), fontSize=6.5, fillColor=colors.HexColor('#2563EB'), fontName='Helvetica-Bold'))
        d.add(String(375, y - 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:20]}", fontSize=7.5))
    return d

def gerar_desenho_multifilar(cabo_pad, dj_pad, circuitos_list):
    n_circ = len(circuitos_list) if circuitos_list else 1
    altura_d = max(260, (n_circ * 35) + 140)
    d = Drawing(720, altura_d)
    x_fase1, x_fase2, x_neutro, x_terra = 220, 250, 280, 310
    d.add(Rect(180, altura_d - 45, 160, 35, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.5))
    d.add(String(185, altura_d - 22, "SISTEMA DE ENTRADA GERAL", fontSize=7, fontName='Helvetica-Bold'))
    d.add(Line(200, altura_d - 45, x_fase1, altura_d - 65, strokeColor=colors.red, strokeWidth=1.5))
    d.add(Line(240, altura_d - 45, x_fase2, altura_d - 65, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(280, altura_d - 45, x_neutro, altura_d - 65, strokeColor=colors.blue, strokeWidth=1.5))
    d.add(Line(x_fase1, altura_d - 65, x_fase1, 20, strokeColor=colors.red, strokeWidth=1.8))
    d.add(Line(x_fase2, altura_d - 65, x_fase2, 20, strokeColor=colors.black, strokeWidth=1.8))
    d.add(Line(x_neutro, altura_d - 65, x_neutro, 20, strokeColor=colors.blue, strokeWidth=1.8))
    d.add(Line(x_terra, altura_d - 20, x_terra, 20, strokeColor=colors.black, strokeWidth=1.5))
    for idx, c in enumerate(circuitos_list):
        y = (altura_d - 100) - (idx * 35)
        if idx % 2 == 0:
            d.add(Rect(20, y - 10, 140, 24, fillColor=colors.white, strokeColor=colors.HexColor('#1E3A8A'), strokeWidth=1))
            d.add(String(25, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:15]}", fontSize=6.5, fontName='Helvetica-Bold'))
            d.add(Circle(x_fase1, y, 2, fillColor=colors.red, strokeColor=colors.red))
            d.add(Line(160, y, x_fase1, y, strokeColor=colors.black, strokeWidth=1))
        else:
            d.add(Rect(350, y - 10, 140, 24, fillColor=colors.white, strokeColor=colors.HexColor('#0D9488'), strokeWidth=1))
            d.add(String(355, y + 2, f"C{c.get('CIRC', idx+1)}: {str(c.get('DESCRIÇÃO',''))[:15]}", fontSize=6.5, fontName='Helvetica-Bold'))
            d.add(Circle(x_neutro, y, 2, fillColor=colors.blue, strokeColor=colors.blue))
            d.add(Line(350, y, x_neutro, y, strokeColor=colors.blue, strokeWidth=0.8))
    return d
