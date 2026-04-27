import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
from iqoptionapi.stable_api import IQ_Option

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Scanner PRO", layout="wide")

arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

st.title("🎯 Scanner PRO - Señales Activas")

# ---------------- SESSION ----------------
if "api" not in st.session_state:
    st.session_state.api = None

if "conectado" not in st.session_state:
    st.session_state.conectado = False

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Configuración")

    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Conectar"):
        API = IQ_Option(email, password)
        check, reason = API.connect()

        if check:
            st.session_state.api = API
            st.session_state.conectado = True
            st.success("✅ Conectado")
        else:
            st.error(f"❌ {reason}")

# ---------------- PARES ----------------
pares = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD",
    "EURJPY","GBPJPY","EURGBP","AUDJPY","GBPCHF"
]

# ---------------- FUNCIONES ----------------
def get_par(API, par):
    try:
        abiertos = API.get_all_open_time()
        if abiertos["forex"][par]["open"]:
            return par
        else:
            return par + "-OTC"
    except:
        return par + "-OTC"

def calcular_rsi(closes, period=14):
    gains, losses = [], []

    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period if sum(losses[-period:]) != 0 else 1

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ---------------- SCANNER ----------------
if st.session_state.conectado:

    API = st.session_state.api

    placeholder = st.empty()

    while True:

        try:
            # 🔄 reconexión automática
            if not API.check_connect():
                API.connect()

            señales = []

            ahora = datetime.now(arg_tz)
            prox_v = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)

            for par in pares:

                try:
                    activo = get_par(API, par)
                    velas = API.get_candles(activo, 60, 50, time.time())

                    if not velas:
                        continue

                    closes = [v['close'] for v in velas]
                    highs = [v['max'] for v in velas]
                    lows = [v['min'] for v in velas]

                    precio = closes[-1]

                    # EMA
                    ema = sum(closes[-20:]) / 20

                    # FIBO (más flexible)
                    max_h = max(highs[-20:])
                    min_l = min(lows[-20:])
                    f618 = max_h - ((max_h - min_l) * 0.618)

                    # RSI
                    rsi = calcular_rsi(closes)

                    señal = None

                    # 🎯 CONDICIONES MÁS REALISTAS
                    if abs(precio - f618) < 0.0003:

                        if precio > ema and rsi < 45:
                            señal = "CALL 🚀"

                        elif precio < ema and rsi > 55:
                            señal = "PUT 🔻"

                    if señal:
                        señales.append(
                            f"{activo} | {señal} | Precio: {round(precio,5)} | Entrada: {prox_v.strftime('%H:%M')}"
                        )

                except:
                    continue

            # ---------------- UI ----------------
            with placeholder.container():

                st.subheader("📡 Señales Detectadas")

                if señales:
                    for s in señales:
                        st.success(s)
                else:
                    st.warning("Sin señales por el momento...")

            time.sleep(5)

        except Exception as e:
            st.error(f"Error conexión: {str(e)}")
            time.sleep(5)
