def dimensionar_circuito_nbr5410_mda(potencia, tensao, comprimento, tipo_carga, fca=0.70, fct=1.0):
    fp = 1.0 if (tipo_carga in ["Iluminação", "TUE - Chuveiro"]) else 0.80
    # ... todas as suas contas de bitola e disjuntores ...
    return { "BITOLA": bitola_final, "DISJUNTORES": disjuntor_final, ... }
