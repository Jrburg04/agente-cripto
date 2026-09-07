import urllib.request
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

# --- CONFIGURACIÓN ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1546424832298717236/aV6u2kss3TsMRiMT_-udFK1f0iBosNd1JBe0sGGa04jBokrGJSrIXo3M45qlmoD8Shp3"

HORA_INICIO = 7   # 07:00 AM
HORA_FIN = 14     # 02:00 PM

SYMBOL = "BTCUSDT"
CAPITAL_SIMULADO = 1000.0
POSICION_ABIERTA = False
PRECIO_COMPRA = 0.0
CANTIDAD_BTC = 0.0

# Servidor Web liviano para requerimiento de Render Web Service
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Agente Cripto Operando OK")

def iniciar_servidor_web():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def enviar_discord(mensaje):
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=data, 
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("📩 Alerta enviada a Discord.")
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")

def dentro_de_horario():
    hora_actual = datetime.now().hour
    return HORA_INICIO <= hora_actual < HORA_FIN

def obtener_velas(symbol="BTCUSDT", interval="1h", limit=30):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.urlopen(url)
    datos = json.loads(req.read().decode())
    return [float(vela[4]) for vela in datos]

def calcular_media_movil(precios, periodo):
    if len(precios) < periodo:
        return 0
    return sum(precios[-periodo:]) / periodo

def ejecutar_agente():
    global CAPITAL_SIMULADO, POSICION_ABIERTA, PRECIO_COMPRA, CANTIDAD_BTC
    
    hora_str = datetime.now().strftime("%H:%M:%S")
    
    if not dentro_de_horario():
        print(f"[{hora_str}] 😴 Fuera de ventana ({HORA_INICIO}:00 a {HORA_FIN}:00 hrs). Pausa...")
        return

    try:
        precios = obtener_velas()
        precio_actual = precios[-1]
        
        ma_corta = calcular_media_movil(precios, 5)
        ma_larga = calcular_media_movil(precios, 20)
        
        print(f"[{hora_str}] 🟢 MERCADO ABIERTO | BTC: ${precio_actual:,.2f}")
        
        if ma_corta > ma_larga and not POSICION_ABIERTA:
            POSICION_ABIERTA = True
            PRECIO_COMPRA = precio_actual
            CANTIDAD_BTC = CAPITAL_SIMULADO / precio_actual
            
            msg = f"🟢 **[AGENTE - COMPRA]**\n**Par:** {SYMBOL}\n**Precio Entrada:** ${PRECIO_COMPRA:,.2f} USDT"
            enviar_discord(msg)
            
        elif ma_corta < ma_larga and POSICION_ABIERTA:
            CAPITAL_SIMULADO = CANTIDAD_BTC * precio_actual
            ganancia = CAPITAL_SIMULADO - 1000.0
            POSICION_ABIERTA = False
            
            msg = f"🔴 **[AGENTE - VENTA]**\n**Par:** {SYMBOL}\n**Precio Salida:** ${precio_actual:,.2f} USDT\n**Saldo:** ${CAPITAL_SIMULADO:,.2f} USDT (P/L: ${ganancia:,.2f})"
            enviar_discord(msg)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def bucle_agente():
    enviar_discord("🤖 **Agente Cripto Iniciado en la Nube (Render Free).**")
    while True:
        ejecutar_agente()
        time.sleep(15)

if __name__ == "__main__":
    t = threading.Thread(target=iniciar_servidor_web)
    t.daemon = True
    t.start()
    
    bucle_agente()

