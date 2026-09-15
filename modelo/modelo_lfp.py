"""
Modelo semiempírico de envejecimiento de una batería LFP de coche eléctrico
según la estrategia de carga diaria (a qué porcentaje se carga, con qué frecuencia,
cuándo se calibra al 100 %), el uso (km/día), el cargador y el clima.

Química LFP (celda Sony/Murata US26650FTC1, 3 Ah):
  Naumann, Schimpe, Keil, Hesse, Jossen (2018), J. Energy Storage 17, 153-169 (reposo):
    Q_cal = k_ref · exp(−Ea/R·(1/T − 1/298,15)) · k_SOC · sqrt(t[s])
    k_ref = 1,2571e-5 s^-0,5 ; Ea = 17.126 J/mol ; k_SOC = 2,8575·(SOC−0,5)^3 + 0,60225
  Naumann, Spingler, Jossen (2020), J. Power Sources 451, 227666 (uso):
    Q_cyc[%] = k_C · k_DOD · sqrt(FEC) ; k_C = 0,0630·C + 0,0971 ; k_DOD = 4,0253·(DOD−0,6)^3 + 1,0923
  Parámetros verificados en SimSES (TUM). Mismo modelo que en el vídeo «¿Cargar al 80 % o al 100 %?».

Variante «penalización alta» (sensibilidad): por encima del 70 % de carga, k_SOC crece linealmente
hasta 2,2 veces el valor del 50 % en el 100 %, que es el orden de la relación medida por Keil 2016
(≈2–2,5 entre ≥80 % y ≤70 %) y descrita por Yang 2025 (90–100 % «sustancialmente más rápido»).

Acumulación con estrés variable: método del «tiempo virtual», paso horario.
"""
import json
import math
import numpy as np

R = 8.314
K_REF = 1.2571e-5
EA = 17126.0


def k_soc_naumann(soc):
    return 2.8575 * (soc - 0.5) ** 3 + 0.60225


def k_soc(soc, variante="naumann"):
    k = k_soc_naumann(soc)
    if variante == "alta":
        k50 = k_soc_naumann(0.5)
        if soc > 0.7:
            k70 = k_soc_naumann(0.7)
            k = k70 + (soc - 0.7) / 0.3 * (2.2 * k50 - k70)
    return k


def k_cal(soc, T_C, variante="naumann"):
    T = T_C + 273.15
    return K_REF * math.exp(-EA / R * (1.0 / T - 1.0 / 298.15)) * k_soc(soc, variante)  # por s^0,5


def k_cyc(c_rate, dod):
    return (0.0630 * c_rate + 0.0971) * (4.0253 * (dod - 0.6) ** 3 + 1.0923) / 100.0  # fracción por sqrt(FEC)


# ---------- Temperaturas medias mensuales (AEMET, valores normales 1981-2010; Murcia 1984-2010) ----------
CLIMAS = {
    "A Coruña": [10.8, 11.1, 12.4, 13.0, 15.0, 17.4, 19.0, 19.6, 18.6, 16.1, 13.3, 11.5],
    "Santander": [9.7, 9.8, 11.3, 12.4, 15.1, 17.8, 19.8, 20.3, 18.6, 16.1, 12.5, 10.5],
    "Oviedo": [8.3, 8.7, 10.5, 11.3, 13.9, 16.7, 18.7, 19.1, 17.6, 14.6, 10.9, 8.9],
    "Bilbao": [9.3, 9.7, 11.5, 12.6, 15.7, 18.4, 20.4, 20.9, 19.2, 16.4, 12.4, 9.9],
    "León": [3.2, 4.7, 7.6, 9.0, 12.6, 17.1, 19.8, 19.6, 16.5, 11.7, 7.0, 4.2],
    "Valladolid": [4.2, 5.9, 9.0, 10.7, 14.5, 19.3, 22.3, 22.1, 18.5, 13.2, 7.9, 5.0],
    "Madrid": [6.3, 7.9, 11.2, 12.9, 16.7, 22.2, 25.6, 25.1, 20.9, 15.1, 9.9, 6.9],
    "Zaragoza": [6.6, 8.2, 11.6, 13.8, 18.0, 22.6, 25.3, 25.0, 21.2, 16.2, 10.6, 7.0],
    "Barcelona": [9.2, 9.9, 11.8, 13.7, 16.9, 20.9, 23.9, 24.4, 21.7, 17.8, 13.0, 10.0],
    "Valencia": [11.8, 12.5, 14.4, 16.2, 19.0, 22.9, 25.6, 26.1, 23.5, 19.7, 15.3, 12.6],
    "Palma": [9.5, 9.8, 11.3, 13.6, 17.5, 21.7, 24.8, 25.1, 22.2, 18.5, 13.7, 10.8],
    "Murcia": [10.6, 12.2, 14.3, 16.5, 20.0, 24.2, 27.2, 27.6, 24.2, 19.8, 14.6, 11.5],
    "Málaga": [12.1, 12.9, 14.7, 16.3, 19.3, 23.0, 25.5, 26.0, 23.5, 19.5, 15.7, 13.2],
    "Sevilla": [10.9, 12.5, 15.6, 17.3, 20.7, 25.1, 28.2, 27.9, 25.0, 20.2, 15.1, 11.9],
    "Tenerife": [18.2, 18.3, 19.0, 19.7, 21.0, 22.9, 25.0, 25.5, 24.9, 23.4, 21.3, 19.4],
    "25 °C constante": [25.0] * 12,
}
DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def temperatura_horaria(clima, offset=0.0):
    temps = CLIMAS[clima]
    return np.concatenate([np.full(24 * d, t + offset) for t, d in zip(temps, DIAS_MES)])  # 8760


# ---------- Perfil semanal de estado de carga (simulación horaria explícita) ----------
def simular_semana(kwh, consumo_kwh_km, km_semana, objetivo, potencia_kw, eficiencia=0.9,
                   h_salida=8, h_regreso=18, h_enchufe=19, programada=False, cada_n_dias=1,
                   dia_calibracion=None, objetivo_calibracion=1.0, reserva_min=0.05,
                   semanas=4, cada_k_semanas=1):
    """Simulación horaria explícita de `semanas` semanas; devuelve el SOC horario de la última.
    Cada hora: primero se aplica el consumo (a h_salida y h_regreso), después la carga en curso.
    La carga «al enchufar» empieza a h_enchufe; la «programada» empieza a la hora que haga falta
    para terminar a h_salida del día siguiente (calculada con el SOC de ese momento)."""
    p_bat = potencia_kw * eficiencia / kwh
    semanas = max(semanas, 3 * cada_k_semanas)  # estado estacionario y al menos un ciclo completo de calibración
    n = 24 * 7 * semanas
    n_ult = 168 * cada_k_semanas  # ventana devuelta: un ciclo completo de calibración
    soc = np.zeros(n)
    s = objetivo
    # estado de la carga en curso: (objetivo, hora de inicio absoluta) o None
    carga = None
    fec = 0.0  # ciclos completos equivalentes (descarga) en la última semana
    dods = []
    for t in range(n):
        d = (t // 24) % 7
        w = (t // 168)
        h = t % 24
        uso = km_semana[d] * consumo_kwh_km / kwh
        if h == h_salida:
            s = max(s - uso * 0.55, reserva_min)
            if t >= n - n_ult:
                fec += uso * 0.55
        if h == h_regreso:
            s = max(s - uso * 0.45, reserva_min)
            if t >= n - n_ult:
                fec += uso * 0.45
        # decidir carga al llegar la hora de enchufar
        if h == h_enchufe:
            dia_carga = (d % cada_n_dias == 0)
            obj = objetivo
            prog = programada
            if dia_calibracion is not None and d == dia_calibracion and (w % cada_k_semanas == cada_k_semanas - 1):
                dia_carga, obj, prog = True, objetivo_calibracion, True
            if dia_carga and obj > s + 1e-9:
                horas = (obj - s) / p_bat
                if prog:
                    fin = t + (24 - h_enchufe) + h_salida  # hora absoluta de salida de mañana
                    ini = max(t, fin - horas)
                else:
                    ini = t
                carga = (obj, ini)
                if t >= n - n_ult:
                    dods.append(obj - s)
        # carga en curso
        if carga is not None:
            obj, ini = carga
            if t + 1 > ini:
                paso = p_bat * min(1.0, t + 1 - ini)
                s = min(obj, s + paso)
                if s >= obj - 1e-9:
                    carga = None
        soc[t] = s
    return soc[-n_ult:], fec, dods


def simular(kwh, consumo_kwh_km, km_semana, objetivo, potencia_kw, clima, anos=15,
            programada=False, cada_n_dias=1, dia_calibracion=None, objetivo_calibracion=1.0,
            eficiencia=0.9, offset_T=0.0, variante="naumann", dias_100_ano=0,
            cargas_rapidas_mes=0.0, fec_carga_rapida=0.6, c_rapida=1.5, c_lenta=0.15,
            reserva_min=0.05, h_enchufe=19, h_salida=8, h_regreso=18, cada_k_semanas=1):
    """Simula `anos` años. Devuelve pérdidas (fracción) año a año: total, reposo (cal), uso (cyc),
    y estadísticas del perfil (SOC medio, horas/semana ≥ 95 %, DOD, FEC/año)."""
    soc_sem, fec_sem, dods = simular_semana(kwh, consumo_kwh_km, km_semana, objetivo, potencia_kw,
                                            eficiencia, h_salida, h_regreso, h_enchufe, programada,
                                            cada_n_dias, dia_calibracion, objetivo_calibracion, reserva_min,
                                            cada_k_semanas=cada_k_semanas)
    n_ult = len(soc_sem)
    T_h = temperatura_horaria(clima, offset_T)
    n_h = len(T_h)
    soc_h = np.tile(soc_sem, int(math.ceil(n_h / n_ult)))[:n_h]
    if dias_100_ano > 0:
        paso = int(365 // dias_100_ano)
        for k in range(dias_100_ano):
            d0 = k * paso
            soc_h[d0 * 24:(d0 + 1) * 24] = 1.0
    fec_ano = fec_sem * 365.0 / (7.0 * cada_k_semanas)
    fec_rapida_ano = cargas_rapidas_mes * 12 * fec_carga_rapida
    # DOD representativo: media de los tramos de carga de la semana (ponderada por su tamaño)
    dod = float(np.average(dods, weights=dods)) if dods else max(km_semana) * consumo_kwh_km / kwh
    # C-rate efectiva ponderada por energía
    fec_tot_ano = fec_ano + fec_rapida_ano
    c_eff = (fec_ano * c_lenta + fec_rapida_ano * c_rapida) / fec_tot_ano if fec_tot_ano > 0 else c_lenta
    kc = k_cyc(c_eff, dod)
    res = {"anos": [], "total": [], "cal": [], "cyc": []}
    Q_cal = 0.0
    ks = np.array([k_cal(float(s_), float(T_), variante) for s_, T_ in zip(soc_h, T_h)])
    for a in range(1, anos + 1):
        for h in range(n_h):
            k = ks[h]
            t_v = (Q_cal / k) ** 2 if Q_cal > 0 else 0.0
            Q_cal = k * math.sqrt(t_v + 3600.0)
        Q_cyc = kc * math.sqrt(fec_tot_ano * a)
        res["anos"].append(a)
        res["cal"].append(Q_cal)
        res["cyc"].append(Q_cyc)
        res["total"].append(Q_cal + Q_cyc)
    res["soc_medio"] = float(np.mean(soc_h))
    res["h_sem_95"] = float(np.sum(soc_sem >= 0.95)) / cada_k_semanas
    res["h_sem_80"] = float(np.sum(soc_sem >= 0.80)) / cada_k_semanas
    res["soc_min"] = float(np.min(soc_sem))
    res["dod"] = dod
    res["fec_ano"] = fec_ano
    res["fec_rapida_ano"] = fec_rapida_ano
    res["c_eff"] = c_eff
    res["soc_semana"] = soc_sem.tolist()
    return res


def anos_hasta(res, umbral):
    t = np.array(res["total"])
    a = np.array(res["anos"], dtype=float)
    if t[-1] < umbral:
        return float(a[-1] * (umbral / t[-1]) ** 2)  # extrapolación ~ sqrt(t)
    i = int(np.argmax(t >= umbral))
    if i == 0:
        return float(a[0] * umbral / t[0])
    return float(a[i - 1] + (umbral - t[i - 1]) / (t[i] - t[i - 1]))


if __name__ == "__main__":
    # Prueba rápida
    r = simular(60, 0.14, [70] * 7, 0.5, 7.4, "Madrid", anos=10, dia_calibracion=5)
    print("SOC medio", round(r["soc_medio"], 3), "h≥95", r["h_sem_95"], "FEC/año", round(r["fec_ano"], 1),
          "DOD", round(r["dod"], 3), "pérdida 10 a", round(r["total"][-1] * 100, 2), "cal", round(r["cal"][-1] * 100, 2), "cyc", round(r["cyc"][-1] * 100, 2))
