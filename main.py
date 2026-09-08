import urllib.request
import json
import time
from datetime import datetime
import threading
import os
from flask import Flask

# --- CONFIGURACIÓN ---
# Reemplaza esta URL con la que acabas de copiar de Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1546967622430494731/WnGU3R9VKufDG7GjC5bZsxdoP35B7F4puoZ9BOc4xMU_tZ-I7XA_6QxFy9V_w9B-8P4S"

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
    if "TU_NUEVA_URL_AQUI" in DISCORD_WEBHOOK_URL:
        print("⚠️ Pendiente configurar nueva URL de Webhook de Discord.")
        return
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=data, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"📩 Alerta enviada a Discord (Código {response.getcode()}).")
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")

def obtener_precio_btc():
    # Intento 1: API pública de Coinbase (sin restricciones de limite estricto)
    try:
        url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            datos = json.loads(response.read().decode())
            return float(datos['data']['amount'])
    except Exception:
        pass

    # Intento 2: CoinGecko como respaldo
    url_cg = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    req_cg = urllib.request.Request(url_cg, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_cg) as response:
        datos_cg = json.loads(response.read().decode())
        return float(datos_cg['bitcoin']['usd'])

def calcular_media_movil(periodo):
    if len(HISTORIAL_PRECIOS) < periodo:
        return 0.0
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
        
        # Reporte cada 60 ciclos (cada 30 minutos con pausas de 30s)
        if contador_ciclos % 60 == 0:
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
        time.sleep(30)  # Pausa de 30s para respetar los limites de la API

# Iniciar hilo secundario
t = threading.Thread(target=bucle_agente)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
