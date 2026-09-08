import urllib.request
import json
import time
from datetime import datetime
import threading
import os
from flask import Flask

# --- CONFIGURACIÓN ---
# Si sigue dando error 401, genera un Webhook nuevo en Discord y pégalo aquí
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1546424832298717236/aV6u2kss3TsMRiMT_-udFK1f0iBosNd1JBe0sGGa04jBokrGJSrIXo3M45qlmoD8Shp3"

CAPITAL_SIMULADO = 1000.0
POSICION_ABIERTA = False
PRECIO_COMPRA = 0.0
CANTIDAD_BTC = 0.0
HISTORIAL_PRECIOS = []

app = Flask(__name__)

@app.route('/')
def home():
    return "Agente Cripto Operando OK - 24/7", 200

def enviar_discord(mensaje):
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=data, 
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"📩 Alerta enviada a Discord ({response.getcode()}).")
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")

def obtener_precio_btc():
    # Proveedor alternativo sin restricciones HTTP 451
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        datos = json.loads(response.read().decode())
    return float(datos['bitcoin']['usd'])

def calcular_media_movil(periodo):
    if len(HISTORIAL_PRECIOS) < periodo:
        return 0
    return sum(HISTORIAL_PRECIOS[-periodo:]) / periodo

def ejecutar_agente(contador_ciclos):
    global CAPITAL_SIMULADO, POSICION_ABIERTA, PRECIO_COMPRA, CANTIDAD_BTC, HISTORIAL_PRECIOS
    
    hora_str = datetime.now().strftime("%H:%M:%S")

    try:
        precio_actual = obtener_precio_btc()
        HISTORIAL_PRECIOS.append(precio_actual)
        if len(HISTORIAL_PRECIOS) > 50:
            HISTORIAL_PRECIOS.pop(0)

        ma_corta = calcular_media_movil(5)
        ma_larga = calcular_media_movil(20)
        
        print(f"[{hora_str}] 🟢 MONITOREO 24/7 | BTC: ${precio_actual:,.2f} | MA5: ${ma_corta:,.2f} | MA20: ${ma_larga:,.2f}")
        
        if contador_ciclos % 120 == 0:
            msg_reporte = f"📊 **[REPORTE ACTIVO 24/7]**\n**BTC/USDT:** ${precio_actual:,.2f}\n**Estado:** {'En Posición' if POSICION_ABIERTA else 'Sin Posición'}"
            enviar_discord(msg_reporte)

        if ma_corta > 0 and ma_larga > 0:
            if ma_corta > ma_larga and not POSICION_ABIERTA:
                POSICION_ABIERTA = True
                PRECIO_COMPRA = precio_actual
                CANTIDAD_BTC = CAPITAL_SIMULADO / precio_actual
                
                msg = f"🟢 **[AGENTE - COMPRA]**\n**Par:** BTCUSDT\n**Precio Entrada:** ${PRECIO_COMPRA:,.2f} USDT"
                enviar_discord(msg)
                
            elif ma_corta < ma_larga and POSICION_ABIERTA:
                CAPITAL_SIMULADO = CANTIDAD_BTC * precio_actual
                ganancia = CAPITAL_SIMULADO - 1000.0
                POSICION_ABIERTA = False
                
                msg = f"🔴 **[AGENTE - VENTA]**\n**Par:** BTCUSDT\n**Precio Salida:** ${precio_actual:,.2f} USDT\n**Saldo:** ${CAPITAL_SIMULADO:,.2f} USDT (P/L: ${ganancia:,.2f})"
                enviar_discord(msg)
            
    except Exception as e:
        print(f"❌ Error en bucle: {e}")

def bucle_agente():
    time.sleep(5)
    enviar_discord("🤖 **Agente Cripto Operativo 24/7 en Render.**")
    contador = 0
    while True:
        ejecutar_agente(contador)
        contador += 1
        time.sleep(15)

# Iniciar hilo secundario
t = threading.Thread(target=bucle_agente)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
