# Calculadora de carga LFP — AutoIngenium

Herramienta del vídeo de AutoIngenium sobre la estrategia de carga que maximiza la vida de una batería de ferrofosfato de litio (LFP). Dices qué coche tienes, cuántos kilómetros haces al día, cómo cargas en casa y dónde vive el coche, y te devuelve:

- a qué porcentaje cargar cada noche y cómo hacerlo en tu coche (límite en el coche o duración de la carga si el coche no permite fijar un límite);
- cuándo hacer la carga al 100 % que pide el fabricante para calibrar el indicador, y cuánto cuesta hacerla cada semana o cada mes;
- qué hacer con los imprevistos (carga rápida puntual: minutos, kWh, euros y décimas de capacidad) y con los viajes largos (si tu cargador llega al 100 % en una noche);
- la capacidad estimada de la batería a los diez y a los quince años con tu estrategia frente a dejarla siempre al 100 % nada más enchufar y frente al límite del 80 %.

Todo el cálculo se hace en el navegador; no se envía ningún dato. Es una estimación con un modelo publicado, no una predicción para un coche concreto.

## Publicarla en GitHub Pages (cinco minutos)

1. Crea un repositorio público en GitHub (por ejemplo `calculadora-carga-lfp`).
2. Sube el contenido de esta carpeta tal cual (`index.html`, `README.md`, `LICENSE`, `.nojekyll` y la carpeta `modelo/`). Con la web de GitHub: «Add file → Upload files», arrastra los archivos y pulsa «Commit changes».
3. En el repositorio, «Settings → Pages → Build and deployment»: *Source* = «Deploy from a branch», *Branch* = `main`, carpeta `/ (root)`. Guarda.
4. Al cabo de uno o dos minutos la calculadora estará en `https://TU_USUARIO.github.io/calculadora-carga-lfp/`.
5. En `index.html` hay dos enlaces que conviene actualizar una vez publicado el vídeo: `id="linkVideo"` (URL del vídeo) e `id="linkRepo"` (URL de este repositorio).

También funciona abriendo `index.html` directamente en el navegador, sin servidor.

## Método

El modelo es el de una celda comercial LFP/grafito ensayada por el grupo de Andreas Jossen (Universidad Técnica de Múnich):

- **Reposo**: Naumann, Schimpe, Keil, Hesse, Jossen (2018), «Analysis and modeling of calendar aging of a commercial LiFePO4/graphite cell», *J. Energy Storage* 17, 153–169. Pérdida = k_ref · exp(−Ea/R·(1/T − 1/298,15 K)) · k_SOC · √t, con k_ref = 1,2571·10⁻⁵ s^−½, Ea = 17.126 J/mol y k_SOC = 2,8575·(SOC − 0,5)³ + 0,60225.
- **Uso**: Naumann, Spingler, Jossen (2020), «Analysis and modeling of cycle aging of a commercial LiFePO4/graphite cell», *J. Power Sources* 451, 227666. Pérdida [%] = (0,0630·C + 0,0971) · (4,0253·(DOD − 0,6)³ + 1,0923) · √FEC.
- Parámetros verificados en el simulador SimSES (TUM). La simulación recorre hora a hora una semana tipo (salida, regreso, hora de enchufar, carga al enchufar o programada para terminar al salir, carga de calibración cada k semanas) y la repite durante quince años con la temperatura media de cada mes de la ciudad elegida (AEMET, valores climatológicos normales 1981–2010) como temperatura de la batería. El estrés variable se acumula con el método del «tiempo virtual».
- **Escala**: la celda ensayada (Sony US26650, 2015) envejece en reposo más deprisa que las celdas prismáticas LFP actuales; por defecto el resultado se multiplica por 0,7, factor deducido de los Model 3 LFP con más de 100.000 km analizados en Suecia por Carla con la herramienta AVILOO (93,3 % de salud media; Electrek, 15-7-2026). Puede desactivarse en «Precios y método».
- **Penalización alta**: variante de sensibilidad en la que, por encima del 70 %, la velocidad de envejecimiento en reposo crece hasta 2,2 veces la del 50 % en el 100 %, del orden de lo medido por Keil et al. (2016, *J. Electrochem. Soc.* 163, A1872) y Yang et al. (2025, *Applied Sciences* 15, 12749).

Lo que el modelo no recoge: el daño adicional de ciclar dentro de la ventana 75–100 % (Zsoldos, Thompson, Black, Azam, Dahn, 2024, *J. Electrochem. Soc.* 171, 080527), el codo final de la curva de envejecimiento, la refrigeración activa del paquete y el depósito de litio metálico al cargar rápido en frío.

## Archivos

- `index.html`: la calculadora completa (HTML, CSS y JavaScript en un solo archivo; el modelo es `modelo/modelo.js` incrustado).
- `modelo/modelo_lfp.py`: el mismo modelo en Python (referencia). `modelo/escenarios.py` genera `resultados.json` con los escenarios del vídeo. `modelo/validar.js` comprueba que la versión JavaScript reproduce la de Python (diferencias < 10⁻¹²).
- Datos de los coches (capacidad útil, consumo real, potencia de carga rápida): EV Database y prensa especializada, septiembre de 2026; aproximados y editables en la propia calculadora.

## Licencia

MIT. Si reutilizas el modelo o la calculadora, cita las fuentes anteriores y el canal AutoIngenium.
