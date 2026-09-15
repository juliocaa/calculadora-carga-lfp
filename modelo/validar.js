const M = require('./modelo.js');
const casos = [
  {kwh:60, consumo_kwh_km:0.14, km_semana:[70,70,70,70,70,70,70], objetivo:1.0, potencia_kw:7.4, clima:"Madrid", anos:15},
  {kwh:60, consumo_kwh_km:0.14, km_semana:[70,70,70,70,70,70,70], objetivo:1.0, potencia_kw:7.4, clima:"Madrid", anos:15, programada:true},
  {kwh:60, consumo_kwh_km:0.14, km_semana:[70,70,70,70,70,70,70], objetivo:0.5, potencia_kw:7.4, clima:"Madrid", anos:15, dia_calibracion:5, cada_k_semanas:1},
  {kwh:60, consumo_kwh_km:0.14, km_semana:[70,70,70,70,70,70,70], objetivo:0.5, potencia_kw:7.4, clima:"Sevilla", anos:15, dia_calibracion:5, cada_k_semanas:4, variante:"alta", cargas_rapidas_mes:2},
  {kwh:30, consumo_kwh_km:0.138, km_semana:[70,70,70,70,70,70,70], objetivo:0.6, potencia_kw:3.7, clima:"A Coruña", anos:15, cada_n_dias:2},
  {kwh:60, consumo_kwh_km:0.14, km_semana:[55,55,55,55,55,55,160], objetivo:0.5, potencia_kw:7.4, clima:"Madrid", anos:15, dia_calibracion:5, cada_k_semanas:1, dias_100_ano:12},
];
const out = casos.map(c => { const r = M.simular(c); return {loss10:r.total[9], cal10:r.cal[9], cyc10:r.cyc[9], loss15:r.total[14], soc_medio:r.soc_medio, dod:r.dod, fec:r.fec_ano, a80:M.anosHasta(r.total,0.2)}; });
console.log(JSON.stringify(out));
