import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Scanner PRO v2", layout="wide", initial_sidebar_state="expanded")
arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

# Estilo personalizado para mejorar la visibilidad
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stSuccess { background-color: #052e16; color: #4ade80; border: 1px solid #22c55e; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "api" not in st.session_state:
    st.session_state.api = None
if "conectado" not in st.session_state:
    st.session_state.conectado = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Acceso IQ Option")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("🚀 Iniciar Scanner", use_container_width=True):
        with st.spinner("Conectando con el servidor..."):
            API = IQ_Option(email, password)
            check, reason = API.connect()
            if check:
                st.session_state.api = API
                st.session_state.conectado = True
                st.success("¡Conexión Exitosa!")
            else:
                st.error(f"Error: {reason}")

# --- LÓGICA DE TRADING ---
def get_candles_safe(api, par):
    """Obtiene velas manejando fallos de conexión"""
    try:
        # Intenta primero mercado real, luego OTC
        velas = api.get_candles(par, 60, 50, time.time())
        if not velas:
            velas = api.get_candles(par + "-OTC", 60, 50, time.time())
        return velas
    except:
        return None

def analizar_señal(velas):
    """Calcula indicadores y genera señales"""
    df = pd.DataFrame(velas)
    closes = df['close']
    highs = df['max']
    lows = df['min']
    
    # Indicadores
    ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]
    max_20 = highs.tail(20).max()
    min_20 = lows.tail(20).min()
    f618 = max_20 - ((max_20 - min_20) * 0.618)
    precio_actual = closes.iloc[-1]
    
    # RSI rápido
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    
    # Lógica de entrada
    if abs(precio_actual - f618) < (precio_actual * 0.0001): # Margen dinámico
        if precio_actual > ema20 and rsi < 45:
            return "COMPRA (CALL) 🚀"
        elif precio_actual < ema20 and rsi > 55:
            return "VENTA (PUT) 🔻"
    return None

# --- CUERPO PRINCIPAL ---
st.title("🎯 Dashboard de Señales Fibonacci + RSI")

if st.session_state.conectado:
    pares = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY", "GBPJPY"]
    placeholder = st.empty()
    
    while True:
        if not st.session_state.api.check_connect():
            st.session_state.api.connect()

        ahora = datetime.now(arg_tz)
        prox_entrada = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)
        
        with placeholder.container():
            col1, col2 = st.columns([1, 3])
            col1.metric("Hora Local (Junín)", ahora.strftime("%H:%M:%S"))
            col2.info(f"Siguiente vela operativa: {prox_entrada.strftime('%H:%M:%S')}")
            
            st.divider()
            
            # Grid de señales
            grid = st.columns(3)
            idx = 0
            
            for par in pares:
                velas = get_candles_safe(st.session_state.api, par)
                if velas:
                    resultado = analizar_señal(velas)
                    if resultado:
                        with grid[idx % 3]:
                            st.success(f"**{par}**\n\n{resultado}\n\nEntrada: {prox_entrada.strftime('%H:%M')}")
                        idx += 1
            
            if idx == 0:
                st.write("🔎 Monitoreando mercados... Sin señales confirmadas.")
        
        time.sleep(2) # Actualización más rápida para scalping
else:
    st.warning("👈 Por favor, ingresa tus credenciales en el panel lateral para comenzar.")
