import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Scanner PRO v2 - MultiPar", layout="wide")
arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

# Estilo para mejorar la interfaz oscura
st.markdown("""
    <style>
    .stSuccess { background-color: #052e16; color: #4ade80; border: 1px solid #22c55e; }
    .stWarning { background-color: #2e2a05; color: #facc15; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "api" not in st.session_state:
    st.session_state.api = None
if "conectado" not in st.session_state:
    st.session_state.conectado = False

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.header("🔑 Acceso IQ Option")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("🚀 Iniciar Scanner", use_container_width=True):
        with st.spinner("Conectando..."):
            API = IQ_Option(email, password)
            check, reason = API.connect()
            if check:
                st.session_state.api = API
                st.session_state.conectado = True
                st.success("¡Conexión Exitosa!")
            else:
                st.error(f"Error: {reason}")

# --- FUNCIONES TÉCNICAS ---
def obtener_activo_abierto(api, par):
    """Detecta si el par está en mercado real o debe usar OTC"""
    try:
        # Verificamos disponibilidad en mercado digital/turbo
        all_asset = api.get_all_profit()
        if par in all_asset.get('turbo', {}):
            return par
        else:
            return par + "-OTC"
    except:
        return par + "-OTC"

def calcular_indicadores(velas):
    """Calcula Fibo 0.618, RSI y EMA20"""
    df = pd.DataFrame(velas)
    closes = df['close']
    
    # EMA 20
    ema = closes.ewm(span=20, adjust=False).mean().iloc[-1]
    
    # Fibonacci 0.618 de las últimas 20 velas
    max_h = df['max'].tail(20).max()
    min_l = df['min'].tail(20).min()
    f618 = max_h - ((max_h - min_l) * 0.618)
    
    # RSI 14
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    
    return closes.iloc[-1], f618, rsi, ema

# --- DASHBOARD PRINCIPAL ---
st.title("🎯 Dashboard de Señales Fibonacci + RSI (10 Pares)")

if st.session_state.conectado:
    # Lista de 10 pares solicitados
    lista_pares = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "GBPCHF"
    ]
    
    placeholder = st.empty()
    
    while True:
        # Verificar conexión
        if not st.session_state.api.check_connect():
            st.session_state.api.connect()

        ahora = datetime.now(arg_tz)
        prox_v = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)
        
        with placeholder.container():
            # Encabezado con hora de Junín
            c1, c2 = st.columns(2)
            c1.metric("🕒 Hora (Junín)", ahora.strftime("%H:%M:%S"))
            c2.info(f"⌛ Próxima Vela: {prox_v.strftime('%H:%M:%S')}")
            
            st.divider()
            
            # Grid de 2 columnas para los 10 pares
            cols = st.columns(2)
            
            for i, par_base in enumerate(lista_pares):
                with cols[i % 2]:
                    # 1. Detectar si es mercado Real u OTC
                    activo = obtener_activo_abierto(st.session_state.api, par_base)
                    
                    # 2. Pedir velas (60 seg, 50 velas)
                    velas = st.session_state.api.get_candles(activo, 60, 50, time.time())
                    
                    if velas:
                        precio, f618, rsi, ema = calcular_indicadores(velas)
                        
                        # 3. Lógica de Señal
                        señal = None
                        # Margen de 0.0003 para Fibo
                        if abs(precio - f618) < 0.0003:
                            if precio > ema and rsi < 45:
                                señal = "COMPRA (CALL) 🚀"
                            elif precio < ema and rsi > 55:
                                señal = "VENTA (PUT) 🔻"
                        
                        # 4. Mostrar en pantalla
                        if señal:
                            st.success(f"**{activo}** | {señal}\n\nEntrada: {prox_v.strftime('%H:%M')}")
                        else:
                            st.write(f"🔎 {activo}: Buscando entrada... (P: {round(precio,5)} | F618: {round(f618,5)})")
                    else:
                        st.warning(f"⚠️ {activo}: Sin datos.")

        time.sleep(5) # Pausa para no saturar la API
else:
    st.info("👈 Ingresá tus credenciales y dale a 'Iniciar Scanner' para arrancar.")
