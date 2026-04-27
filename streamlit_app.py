import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
from iqoptionapi.stable_api import IQ_Option

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Scanner Institucional IQ", layout="wide")

arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

st.title("🏦 Scanner Institucional IQ Option (Sin Parpadeo)")

# ---------------- SESSION ----------------
if "api" not in st.session_state:
    st.session_state.api = None

if "conectado" not in st.session_state:
    st.session_state.conectado = False

if "running" not in st.session_state:
    st.session_state.running = False

if "signals" not in st.session_state:
    st.session_state.signals = {}

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

    if st.session_state.conectado:
        if st.button("▶ Iniciar Scanner"):
            st.session_state.running = True

        if st.button("⏹ Detener"):
            st.session_state.running = False

# ---------------- UI ----------------
pares = ["EURUSD", "GBPUSD", "EURJPY", "AUDUSD"]

cols = st.columns(4)

interfaces = []

for i, par in enumerate(pares):
    with cols[i]:
        st.subheader(f"📊 {par}")
        interfaces.append({
            "par": par,
            "msg": st.empty(),
            "fibo": st.empty(),
            "reloj": st.empty()
        })

# ---------------- FUNCIONES ----------------
def obtener_par_activo(API, par):
    try:
        abiertos = API.get_all_open_time()
        if abiertos["forex"][par]["open"]:
            return par
        else:
            return par + "-OTC"
    except:
        return par + "-OTC"

# ---------------- LOOP PRINCIPAL ----------------
if st.session_state.conectado and st.session_state.running:

    API = st.session_state.api

    while st.session_state.running:

        ahora = datetime.now(arg_tz)

        minutos_restantes = 5 - (ahora.minute % 5)
        prox_v = (ahora + timedelta(minutes=minutos_restantes)).replace(second=0, microsecond=0)

        for ui in interfaces:

            try:
                par = ui["par"]
                activo = obtener_par_activo(API, par)

                velas = API.get_candles(activo, 60, 50, time.time())

                if not velas:
                    continue

                closes = [v['close'] for v in velas]
                highs = [v['max'] for v in velas]
                lows = [v['min'] for v in velas]

                precio = closes[-1]

                # EMA
                ema20 = sum(closes[-20:]) / 20

                # FIBO
                max_h = max(highs[-20:])
                min_l = min(lows[-20:])
                f618 = max_h - ((max_h - min_l) * 0.618)

                # VELA
                vela = velas[-1]
                alcista = vela['close'] > vela['open']
                bajista = vela['close'] < vela['open']

                # VOLATILIDAD
                rango = max_h - min_l
                volatilidad_ok = rango > 0.0005

                señal = None

                if abs(precio - f618) < 0.0001 and volatilidad_ok:
                    if precio > ema20 and alcista:
                        señal = "CALL 🚀"
                    elif precio < ema20 and bajista:
                        señal = "PUT 🔻"

                # --------- GUARDAR SEÑAL ---------
                if señal:
                    st.session_state.signals[par] = {
                        "señal": señal,
                        "precio": precio,
                        "hora": ahora.strftime('%H:%M:%S'),
                        "entrada": prox_v.strftime('%H:%M'),
                        "activo": activo
                    }

                data = st.session_state.signals.get(par)

                # --------- MOSTRAR ---------
                if data:
                    ui["msg"].write(f"Modo: **{data['activo']}**")

                    ui["fibo"].metric(
                        "SEÑAL ACTIVA",
                        f"{data['precio']:.5f}",
                        data["señal"]
                    )

                    ui["reloj"].success(
                        f"{data['señal']} | {data['hora']} | Entrada {data['entrada']}"
                    )
                else:
                    ui["msg"].write(f"Modo: **{activo}**")

                    ui["fibo"].metric(
                        "Sin señal",
                        f"{precio:.5f}",
                        f"F618: {f618:.5f}",
                        delta_color="off"
                    )

                    ui["reloj"].info(
                        f"{ahora.strftime('%H:%M:%S')} | Próx {prox_v.strftime('%H:%M')}"
                    )

            except Exception as e:
                ui["msg"].error(str(e))

        time.sleep(2)
