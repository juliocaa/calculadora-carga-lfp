// Modelo de envejecimiento LFP (Naumann 2018/2020) — versión JavaScript idéntica a modelo_lfp.py
// Se valida contra la versión Python con validar.js.
(function (root) {
  const R = 8.314, K_REF = 1.2571e-5, EA = 17126.0;
  const DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const CLIMAS = {
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
    "25 °C constante": [25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25],
  };

  function kSocNaumann(s) { return 2.8575 * Math.pow(s - 0.5, 3) + 0.60225; }
  function kSoc(s, variante) {
    let k = kSocNaumann(s);
    if (variante === "alta" && s > 0.7) {
      const k50 = kSocNaumann(0.5), k70 = kSocNaumann(0.7);
      k = k70 + (s - 0.7) / 0.3 * (2.2 * k50 - k70);
    }
    return k;
  }
  function kCal(s, TC, variante) {
    const T = TC + 273.15;
    return K_REF * Math.exp(-EA / R * (1 / T - 1 / 298.15)) * kSoc(s, variante);
  }
  function kCyc(c, dod) { return (0.0630 * c + 0.0971) * (4.0253 * Math.pow(dod - 0.6, 3) + 1.0923) / 100; }

  function temperaturaHoraria(clima, offset) {
    const temps = CLIMAS[clima];
    const out = new Float64Array(8760);
    let i = 0;
    for (let m = 0; m < 12; m++) for (let h = 0; h < 24 * DIAS_MES[m]; h++) out[i++] = temps[m] + (offset || 0);
    return out;
  }

  // Simulación horaria de la semana (idéntica a simular_semana)
  function simularSemana(p) {
    const kwh = p.kwh, cons = p.consumo_kwh_km, km = p.km_semana, objetivo = p.objetivo;
    const ef = p.eficiencia == null ? 0.9 : p.eficiencia;
    const hS = p.h_salida == null ? 8 : p.h_salida, hR = p.h_regreso == null ? 18 : p.h_regreso, hE = p.h_enchufe == null ? 19 : p.h_enchufe;
    const programada = !!p.programada, cadaN = p.cada_n_dias || 1;
    const diaCal = (p.dia_calibracion == null) ? null : p.dia_calibracion;
    const objCal = p.objetivo_calibracion == null ? 1.0 : p.objetivo_calibracion;
    const reserva = p.reserva_min == null ? 0.05 : p.reserva_min;
    const k = p.cada_k_semanas || 1;
    const semanas = Math.max(p.semanas || 4, 3 * k);
    const pBat = p.potencia_kw * ef / kwh;
    const n = 168 * semanas, nUlt = 168 * k;
    const soc = new Float64Array(n);
    let s = objetivo, carga = null, fec = 0;
    const dods = [];
    for (let t = 0; t < n; t++) {
      const d = Math.floor(t / 24) % 7, w = Math.floor(t / 168), h = t % 24;
      const uso = km[d] * cons / kwh;
      if (h === hS) { s = Math.max(s - uso * 0.55, reserva); if (t >= n - nUlt) fec += uso * 0.55; }
      if (h === hR) { s = Math.max(s - uso * 0.45, reserva); if (t >= n - nUlt) fec += uso * 0.45; }
      if (h === hE) {
        let diaCarga = (d % cadaN === 0), obj = objetivo, prog = programada;
        if (diaCal !== null && d === diaCal && (w % k === k - 1)) { diaCarga = true; obj = objCal; prog = true; }
        if (diaCarga && obj > s + 1e-9) {
          const horas = (obj - s) / pBat;
          let ini;
          if (prog) { const fin = t + (24 - hE) + hS; ini = Math.max(t, fin - horas); } else ini = t;
          carga = [obj, ini];
          if (t >= n - nUlt) dods.push(obj - s);
        }
      }
      if (carga !== null) {
        const obj = carga[0], ini = carga[1];
        if (t + 1 > ini) {
          const paso = pBat * Math.min(1, t + 1 - ini);
          s = Math.min(obj, s + paso);
          if (s >= obj - 1e-9) carga = null;
        }
      }
      soc[t] = s;
    }
    return { soc: soc.slice(n - nUlt), fec: fec, dods: dods };
  }

  function simular(p) {
    const anos = p.anos || 15;
    const sem = simularSemana(p);
    const socSem = sem.soc, nUlt = socSem.length;
    const k = p.cada_k_semanas || 1;
    const T = temperaturaHoraria(p.clima, p.offset_T || 0);
    const nH = 8760;
    const socH = new Float64Array(nH);
    for (let h = 0; h < nH; h++) socH[h] = socSem[h % nUlt];
    if (p.dias_100_ano > 0) {
      const paso = Math.floor(365 / p.dias_100_ano);
      for (let j = 0; j < p.dias_100_ano; j++) for (let h = j * paso * 24; h < (j * paso + 1) * 24; h++) socH[h] = 1.0;
    }
    const fecAno = sem.fec * 365 / (7 * k);
    const cargasMes = p.cargas_rapidas_mes || 0;
    const fecRap = p.fec_carga_rapida == null ? 0.6 : p.fec_carga_rapida;
    const cRap = p.c_rapida == null ? 1.5 : p.c_rapida, cLenta = p.c_lenta == null ? 0.15 : p.c_lenta;
    const fecRapAno = cargasMes * 12 * fecRap;
    let dod;
    if (sem.dods.length) { let sw = 0, sww = 0; for (const x of sem.dods) { sw += x * x; sww += x; } dod = sw / sww; }
    else dod = Math.max.apply(null, p.km_semana) * p.consumo_kwh_km / p.kwh;
    const fecTot = fecAno + fecRapAno;
    const cEff = fecTot > 0 ? (fecAno * cLenta + fecRapAno * cRap) / fecTot : cLenta;
    const kc = kCyc(cEff, dod);
    const ks = new Float64Array(nH);
    for (let h = 0; h < nH; h++) ks[h] = kCal(socH[h], T[h], p.variante || "naumann");
    const res = { anos: [], total: [], cal: [], cyc: [] };
    let Q = 0;
    for (let a = 1; a <= anos; a++) {
      for (let h = 0; h < nH; h++) {
        const kk = ks[h];
        const tv = Q > 0 ? (Q / kk) * (Q / kk) : 0;
        Q = kk * Math.sqrt(tv + 3600);
      }
      const Qc = kc * Math.sqrt(fecTot * a);
      res.anos.push(a); res.cal.push(Q); res.cyc.push(Qc); res.total.push(Q + Qc);
    }
    let sm = 0, h95 = 0, h80 = 0, smin = 1;
    for (let h = 0; h < nH; h++) sm += socH[h];
    for (let h = 0; h < nUlt; h++) { if (socSem[h] >= 0.95) h95++; if (socSem[h] >= 0.80) h80++; if (socSem[h] < smin) smin = socSem[h]; }
    res.soc_medio = sm / nH; res.h_sem_95 = h95 / k; res.h_sem_80 = h80 / k; res.soc_min = smin;
    res.dod = dod; res.fec_ano = fecAno; res.fec_rapida_ano = fecRapAno; res.c_eff = cEff;
    res.soc_semana = Array.from(socSem);
    return res;
  }

  function anosHasta(total, umbral) {
    const n = total.length;
    if (total[n - 1] < umbral) return n * Math.pow(umbral / total[n - 1], 2);
    let i = 0; while (i < n && total[i] < umbral) i++;
    if (i === 0) return umbral / total[0];
    return i + (umbral - total[i - 1]) / (total[i] - total[i - 1]);
  }

  const api = { CLIMAS, kSoc, kCal, kCyc, simularSemana, simular, anosHasta, EA, R };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ModeloLFP = api;
})(typeof window !== "undefined" ? window : globalThis);
