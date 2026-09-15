"""Escenarios del vídeo «Estrategia óptima de carga LFP» — genera resultados.json y una tabla legible."""
import json
import sys
sys.path.insert(0, ".")
import numpy as np
import modelo_lfp as m

KM_ANO = 70 * 365  # 25.550 km/año
ESCALA_FLOTA = 0.7  # factor de escala a flotas (Carla/AVILOO 2026: Model 3 LFP 93,3 % a >100.000 km)


def resumen(r, escala=1.0):
    tot = np.array(r["total"]) * escala
    rr = dict(r)
    rr["total"] = tot.tolist()
    rr["cal"] = (np.array(r["cal"]) * escala).tolist()
    rr["cyc"] = (np.array(r["cyc"]) * escala).tolist()
    a80 = m.anos_hasta(rr, 0.20)
    a70 = m.anos_hasta(rr, 0.30)
    return {
        "loss10": float(tot[9]), "cal10": float(rr["cal"][9]), "cyc10": float(rr["cyc"][9]),
        "loss15": float(tot[14]), "loss5": float(tot[4]),
        "a80": a80, "a70": a70, "km80": a80 * KM_ANO, "km70": a70 * KM_ANO,
        "soc_medio": r["soc_medio"], "h_sem_95": r["h_sem_95"], "h_sem_80": r["h_sem_80"],
        "soc_min": r["soc_min"], "dod": r["dod"], "fec_ano": r["fec_ano"], "c_eff": r["c_eff"],
        "curva": tot.tolist(), "curva_cal": rr["cal"], "curva_cyc": rr["cyc"], "soc_semana": r["soc_semana"],
    }


def fila(nombre, s):
    print(f"{nombre:52s} 10a {s['loss10']*100:5.1f} (rep {s['cal10']*100:4.1f} + uso {s['cyc10']*100:3.1f})  15a {s['loss15']*100:5.1f}  "
          f"80%: {s['a80']:5.1f} a  70%: {s['a70']:5.1f} a  SOC medio {s['soc_medio']*100:4.0f}  h≥95 {s['h_sem_95']:4.0f}  h≥80 {s['h_sem_80']:4.0f}  DOD {s['dod']*100:3.0f}  mín {s['soc_min']*100:3.0f}")


out = {"meta": {"km_ano": KM_ANO, "escala_flota": ESCALA_FLOTA}}

# ---------------- Caso principal: Model 3 LFP 60 kWh útiles, 0,14 kWh/km, 70 km/día, 7,4 kW, Madrid ----------------
BASE = dict(kwh=60, consumo_kwh_km=0.14, km_semana=[70] * 7, potencia_kw=7.4, clima="Madrid", anos=15)
regimenes = {
    "A_100_enchufar": dict(objetivo=1.0),
    "A2_100_programada": dict(objetivo=1.0, programada=True),
    "A3_90_enchufar": dict(objetivo=0.9),
    "B_80": dict(objetivo=0.8),
    "B2_80_cal_semanal": dict(objetivo=0.8, dia_calibracion=5, cada_k_semanas=1),
    "B3_80_cal_mensual": dict(objetivo=0.8, dia_calibracion=5, cada_k_semanas=4),
    "B4_70": dict(objetivo=0.7),
    "B5_60": dict(objetivo=0.6),
    "C_50": dict(objetivo=0.5),
    "C2_50_cal_semanal": dict(objetivo=0.5, dia_calibracion=5, cada_k_semanas=1),
    "C3_50_cal_quincenal": dict(objetivo=0.5, dia_calibracion=5, cada_k_semanas=2),
    "C4_50_cal_mensual": dict(objetivo=0.5, dia_calibracion=5, cada_k_semanas=4),
    "D_70_cada_2_dias": dict(objetivo=0.7, cada_n_dias=2),
    "D2_85_cada_3_dias": dict(objetivo=0.85, cada_n_dias=3),
    "D3_100_cada_5_dias": dict(objetivo=1.0, cada_n_dias=5),
    "E_50_cal_semanal_dia_largo": dict(objetivo=0.5, dia_calibracion=5, cada_k_semanas=1, km_semana=[55, 55, 55, 55, 55, 55, 160]),
    "E2_50_cal_mensual_dia_largo": dict(objetivo=0.5, dia_calibracion=5, cada_k_semanas=4, km_semana=[55, 55, 55, 55, 55, 55, 160]),
    "A4_100_enchufar_dia_largo": dict(objetivo=1.0, km_semana=[55, 55, 55, 55, 55, 55, 160]),
    "A5_100_programada_dia_largo": dict(objetivo=1.0, programada=True, km_semana=[55, 55, 55, 55, 55, 55, 160]),
    "B6_80_dia_largo": dict(objetivo=0.8, km_semana=[55, 55, 55, 55, 55, 55, 160]),
}
print("=== MODEL 3 LFP 60 kWh · 70 km/día · Madrid · 7,4 kW · celda (sin escala) ===")
out["m3"] = {}
for k, p in regimenes.items():
    params = dict(BASE); params.update(p)
    r = m.simular(**params)
    out["m3"][k] = resumen(r)
    fila(k, out["m3"][k])

# Con escala de flota
print("\n=== Idem con escala de flota ×0,7 ===")
out["m3_flota"] = {k: resumen(m.simular(**{**BASE, **p}), ESCALA_FLOTA) for k, p in regimenes.items()}
for k in ["A_100_enchufar", "A2_100_programada", "B_80", "C_50", "C2_50_cal_semanal", "C4_50_cal_mensual"]:
    fila(k, out["m3_flota"][k])

# ---------------- Sensibilidad «penalización alta» ----------------
print("\n=== Variante alta (Keil/Yang) ===")
out["m3_alta"] = {}
for k in ["A_100_enchufar", "A2_100_programada", "B_80", "C_50", "C2_50_cal_semanal", "C4_50_cal_mensual"]:
    params = dict(BASE); params.update(regimenes[k]); params["variante"] = "alta"
    out["m3_alta"][k] = resumen(m.simular(**params))
    fila(k + " [alta]", out["m3_alta"][k])

# ---------------- Climas ----------------
print("\n=== Climas (celda) ===")
out["climas"] = {}
for clima in ["A Coruña", "León", "Madrid", "Barcelona", "Sevilla", "Tenerife", "25 °C constante"]:
    out["climas"][clima] = {}
    for k in ["A_100_enchufar", "A2_100_programada", "B_80", "C_50", "C4_50_cal_mensual"]:
        params = dict(BASE); params.update(regimenes[k]); params["clima"] = clima
        out["climas"][clima][k] = resumen(m.simular(**params))
        fila(f"{clima} · {k}", out["climas"][clima][k])

# ---------------- Cargador de 3,7 kW y 2,3 kW (afecta solo al perfil horario) ----------------
print("\n=== Potencia del cargador ===")
out["cargador"] = {}
for P in [2.3, 3.7, 7.4, 11.0]:
    out["cargador"][str(P)] = {}
    for k in ["A_100_enchufar", "A2_100_programada", "C_50"]:
        params = dict(BASE); params.update(regimenes[k]); params["potencia_kw"] = P
        out["cargador"][str(P)][k] = resumen(m.simular(**params))
        fila(f"{P} kW · {k}", out["cargador"][str(P)][k])

# ---------------- Cargas rápidas puntuales y días al 100 % por viajes ----------------
print("\n=== Cargas rápidas puntuales (sobre C_50) y días enteros al 100 % ===")
out["rapidas"] = {}
for n in [0, 0.5, 1, 2, 4]:
    params = dict(BASE); params.update(regimenes["C_50"]); params["cargas_rapidas_mes"] = n
    out["rapidas"][str(n)] = resumen(m.simular(**params))
    fila(f"C_50 + {n} cargas rápidas/mes (0,6 FEC, 1,5C)", out["rapidas"][str(n)])
out["dias100"] = {}
for d in [0, 6, 12, 26]:
    params = dict(BASE); params.update(regimenes["C_50"]); params["dias_100_ano"] = d
    out["dias100"][str(d)] = resumen(m.simular(**params))
    fila(f"C_50 + {d} días enteros al 100 %/año", out["dias100"][str(d)])

# ---------------- Kilometraje ----------------
print("\n=== Kilometraje (Madrid) ===")
out["km"] = {}
for kmd in [30, 50, 70, 100, 150]:
    out["km"][str(kmd)] = {}
    for k in ["A_100_enchufar", "A2_100_programada", "B_80", "C_50"]:
        params = dict(BASE); params.update(regimenes[k]); params["km_semana"] = [kmd] * 7
        # el objetivo del 50 % no cubre 150 km/día (35 %): subir al mínimo suficiente
        if k == "C_50":
            need = kmd * 0.14 / 60
            obj = max(0.5, np.ceil((need + 0.2) * 20) / 20)
            params["objetivo"] = float(obj)
        out["km"][str(kmd)][k] = resumen(m.simular(**params))
        out["km"][str(kmd)][k]["objetivo"] = params["objetivo"]
        fila(f"{kmd} km/día · {k} (obj {params['objetivo']:.2f})", out["km"][str(kmd)][k])

# ---------------- Batería pequeña: BYD Dolphin Surf 30 kWh (útil), 0,138 kWh/km ----------------
print("\n=== BYD DOLPHIN SURF 30 kWh · 70 km/día · Madrid · 7,4 kW ===")
SMALL = dict(kwh=30, consumo_kwh_km=0.138, km_semana=[70] * 7, potencia_kw=7.4, clima="Madrid", anos=15)
reg_small = {
    "A_100_enchufar": dict(objetivo=1.0),
    "A2_100_programada": dict(objetivo=1.0, programada=True),
    "B_80": dict(objetivo=0.8),
    "C_60": dict(objetivo=0.6),
    "C2_60_cal_semanal": dict(objetivo=0.6, dia_calibracion=5, cada_k_semanas=1),
    "C4_60_cal_mensual": dict(objetivo=0.6, dia_calibracion=5, cada_k_semanas=4),
    "C5_55": dict(objetivo=0.55),
    "C6_70": dict(objetivo=0.7),
    "D_100_cada_2_dias": dict(objetivo=1.0, cada_n_dias=2),
}
out["surf"] = {}
for k, p in reg_small.items():
    params = dict(SMALL); params.update(p)
    r = m.simular(**params)
    out["surf"][k] = resumen(r)
    fila(k, out["surf"][k])

# ---------------- Curvas k_SOC y Arrhenius para gráficos ----------------
socs = np.linspace(0, 1, 101)
out["_ksoc"] = {"soc": socs.tolist(),
                "naumann_rel50": [m.k_soc(float(s)) / m.k_soc(0.5) for s in socs],
                "alta_rel50": [m.k_soc(float(s), "alta") / m.k_soc(0.5) for s in socs]}
Ts = list(range(0, 46, 5))
out["_arrhenius"] = {"T": Ts, "LFP": [float(np.exp(-m.EA / m.R * (1 / (T + 273.15) - 1 / 298.15))) for T in Ts]}
out["_kdod"] = {"dod": [d / 100 for d in range(5, 101, 5)],
                "rel": [(4.0253 * (d / 100 - 0.6) ** 3 + 1.0923) / (4.0253 * (0.163 - 0.6) ** 3 + 1.0923) for d in range(5, 101, 5)]}

with open("resultados.json", "w") as f:
    json.dump(out, f, indent=1)
print("\nguardado resultados.json")
