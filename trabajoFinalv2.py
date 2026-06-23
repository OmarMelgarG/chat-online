from flask import Flask
from flask_socketio import SocketIO, send
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import threading
import requests
import asyncio
import os



# TELEGRAM


tokenTelegram = os.getenv('TOKEN_TELEGRAM')
chatID = os.getenv('CHAT_ID')
gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_model = os.getenv('GEMINI_MODEL', 'text-bison-001')

#PALABRAS CLAVE DE ACTIVACION
palabrasClave={
    "ayuda":"/ayuda",
    "emergencia":"/ayuda",
    "urgente":"/ayuda",
    "comprar":"/comprar",
    "productos":"/producto",
    "reserva":"/reserva"
}




# APP


app = Flask(__name__)

socket = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)



# BOT TELEGRAM


botTelegram = ApplicationBuilder().token(
    tokenTelegram
).build()







# INTERFAZ HTML


@app.route("/")
def index():

    return """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chat de Estudio Inteligente</title>

<style>
:root {
    color-scheme: dark;
    --bg: #f4f7fb;
    --panel: #ffffff;
    --surface: #e5eaf4;
    --surface-dark: #d1d9e6;
    --text: #1b2330;
    --muted: #596277;
    --primary: #0f3d7c;
    --accent: #0066cc;
    --success: #0a6b4a;
    --danger: #c4303b;
    --border: rgba(27, 35, 48, 0.12);
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Inter, Arial, sans-serif;
    background: linear-gradient(180deg, #eef2f8 0%, #f7fbff 100%);
    color: var(--text);
}

.page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
}

.panel {
    width: min(1080px, 100%);
    background: var(--panel);
    border-radius: 24px;
    box-shadow: 0 36px 80px rgba(15, 61, 124, 0.08);
    overflow: hidden;
    border: 1px solid rgba(15, 61, 124, 0.08);
}

.header {
    background: #0f3d7c;
    color: white;
    padding: 30px 34px;
}

.header-title {
    margin: 0;
    font-size: 1.85rem;
    letter-spacing: -0.02em;
}

.header-subtitle {
    margin: 10px 0 0;
    color: rgba(255, 255, 255, 0.82);
    font-size: 1rem;
    max-width: 620px;
    line-height: 1.6;
}

.body-grid {
    display: grid;
    grid-template-columns: 1fr;
}

.chat-panel {
    padding: 28px;
}

.status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 22px;
}

.status-card {
    width: 100%;
    border-radius: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 18px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.status-card strong {
    color: var(--primary);
}

.chat-window {
    border-radius: 24px;
    background: var(--surface);
    min-height: 460px;
    max-height: 620px;
    overflow: hidden;
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
}

.chat-history {
    padding: 24px;
    overflow-y: auto;
    gap: 14px;
    display: flex;
    flex-direction: column;
    flex: 1;
}

.message {
    display: inline-flex;
    max-width: 80%;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.6;
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid transparent;
}

.message.user {
    background: #ffffff;
    color: var(--text);
    align-self: flex-end;
    border-color: rgba(15, 61, 124, 0.08);
}

.message.telegram {
    background: #eef2ff;
    color: var(--text);
    border-color: rgba(0, 102, 204, 0.16);
    align-self: flex-start;
}

.message.tutor {
    background: #0f3d7c;
    color: white;
    border-color: rgba(255, 255, 255, 0.18);
    align-self: flex-start;
}

.message.system {
    background: #f5f7fb;
    color: var(--muted);
    border-radius: 14px;
    align-self: center;
    font-size: 0.95rem;
}

.message .badge {
    display: inline-flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 10px;
    font-size: 0.82rem;
    opacity: 0.88;
}

.message .badge span {
    display: inline-flex;
}

.input-area {
    padding: 20px 24px 24px;
    background: #f6f8fb;
    border-top: 1px solid var(--border);
}

.input-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
}

.input-row input {
    width: 100%;
    border: 1px solid rgba(15, 61, 124, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    font-size: 1rem;
    background: white;
    color: var(--text);
}

.input-row button {
    border: none;
    border-radius: 16px;
    background: var(--accent);
    color: white;
    padding: 0 26px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease;
}

.input-row button:hover {
    background: #004ea1;
    transform: translateY(-1px);
}

.note {
    margin-top: 16px;
    color: var(--muted);
    font-size: 0.92rem;
}

@media (max-width: 720px) {
    .panel { border-radius: 18px; }
    .chat-window { min-height: 520px; }
}
</style>

</head>

<body>

<div class="page">
    <section class="panel">
        <header class="header">
            <h1 class="header-title">Chat de Estudio Inteligente</h1>
            <p class="header-subtitle">Asistente de estudio profesional para la web y Telegram. Usa <strong>/tutor</strong> para pedir explicaciones académicas formales al tutor.</p>
        </header>

        <div class="body-grid">
            <div class="chat-panel">
                <div class="status-bar">
                    <div class="status-card">
                        <div>
                            <strong>Modo Tutor:</strong> disponible para consultas académicas.
                        </div>
                        <div id="statusText">Escribe /tutor seguido de tu pregunta.</div>
                    </div>
                </div>

                <div class="chat-window">
                    <div id="chat" class="chat-history"></div>
                </div>

                <div class="input-area">
                    <div class="input-row">
                        <input type="text" id="nombre" placeholder="Tu nombre" autocomplete="off" />
                        <button id="btn-entrar" onclick="guardarNombre()">Entrar</button>
                    </div>
                    <div class="input-row" style="margin-top: 12px;">
                        <input type="text" id="mensaje" placeholder="Escribe un mensaje o /tutor explica ..." autocomplete="off" />
                        <button onclick="enviar()">Enviar</button>
                    </div>
                    <p class="note">El tutor de IA responde aquí y también envía la misma explicación al chat de Telegram.</p>
                </div>
            </div>
        </div>
    </section>
</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>

var socket = io();
var nombre = "";

function guardarNombre() {
    let input = document.getElementById("nombre");

    if (input.value.trim() == "") {
        alert("Ingrese nombre");
        return;
    }

    nombre = input.value.trim();
    input.disabled = true;
    document.getElementById("btn-entrar").disabled = true;
    agregarSistema(nombre + " se unió al chat");
}

function enviar() {
    let input = document.getElementById("mensaje");
    let mensaje = input.value.trim();

    if (nombre == "") {
        alert("Ingrese nombre");
        return;
    }

    if (mensaje == "") {
        return;
    }

    if (mensaje.toLowerCase().startsWith('/tutor')) {
        socket.emit('tutor_query', mensaje);
        showTutorStatus('El tutor de IA está analizando tu consulta...');
        agregarChat('Tu consulta se está enviando al tutor de IA...', 'system');
    } else {
        socket.send(nombre + ': ' + mensaje);
    }

    input.value = "";
}

socket.on('message', function(msg) {
    agregarChat(msg, 'user');
});

socket.on('telegram_message', function(msg) {
    agregarChat('📲 ' + msg, 'telegram');
});

socket.on('emergencia', function(msg) {
    agregarChat('🚨 ' + msg, 'telegram');
});

socket.on('tutor_status', function(msg) {
    showTutorStatus(msg);
});

socket.on('tutor_response', function(msg) {
    hideTutorStatus();
    agregarChat('🤖 Tutor IA: ' + msg, 'tutor');
});

function agregarChat(msg, tipo) {
    var chat = document.getElementById('chat');
    var div = document.createElement('div');
    div.className = 'message ' + (tipo || 'user');

    if (tipo === 'tutor') {
        div.innerHTML = '<div class="badge">🤖 <strong>Tutor IA</strong></div>' + msg;
    } else if (tipo === 'telegram') {
        div.innerHTML = '<div class="badge">📲 <strong>Telegram</strong></div>' + msg;
    } else if (tipo === 'system') {
        div.className = 'message system';
        div.innerHTML = msg;
    } else {
        div.innerHTML = msg;
    }

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function agregarSistema(msg) {
    agregarChat('<strong>Sistema:</strong> ' + msg, 'system');
}

function showTutorStatus(text) {
    var status = document.getElementById('statusText');
    status.textContent = text;
}

function hideTutorStatus() {
    showTutorStatus('El tutor está listo para tu próxima consulta.');
}

</script>

</body>
</html>
"""



@socket.on("message")
def recibirMensaje(mensaje):

    print("WEB:", mensaje)

    # Solo chat web
    send(
        mensaje,
        broadcast=True
    )
    comandosDeteccion(mensaje)


@socket.on('tutor_query')
def recibirTutorQuery(texto):

    print('TUTOR QUERY:', texto)
    pregunta = texto[len('/tutor'):].strip()

    if not pregunta:
        socket.emit('tutor_status', 'Escribe /tutor seguido de tu consulta.')
        return

    socket.emit('tutor_status', 'El tutor de IA está procesando tu consulta...')
    respuesta = consultar_tutor_ia(pregunta)
    socket.emit('tutor_response', respuesta)
    socket.emit('tutor_status', 'El tutor está listo para tu próxima consulta.')

    enviarTelegram(
        f"📘 Tutor IA\nPregunta: {pregunta}\nRespuesta: {respuesta}"
    )


#Paso Extra. COnectar los comandos de activacion
def comandosDeteccion(mensaje):
    texto=mensaje.lower()

    for palabra, comando in palabrasClave.items():
        if palabra in texto:
            notificacion=f"""
            REPORTE MENSAJE CHAT WEB

            Comando:
            {comando}

            Palabra Detectada:
            {mensaje}

            Estado:
            En revision...
        """
            socket.emit(
                "ayuda",
                notificacion
            )
            threading.Thread(
                target=enviarTelegram,
                args=(notificacion,),
                daemon=True
            ).start()
            print("Notificacion Enviada...")
            break




# TELEGRAM SEND


def enviarTelegram(texto):

    url = (
        f"https://api.telegram.org/bot"
        f"{tokenTelegram}/sendMessage"
    )

    data = {
        "chat_id": chatID,
        "text": texto
    }

    try:
        requests.post(
            url,
            data=data,
            timeout=10
        )
    except Exception as e:
        print(
            "Telegram error:",
            e
        )


def _consultar_modelo_gemini(modelo, payload):
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta2/models/{modelo}:generateText"
        f"?key={gemini_api_key}"
    )
    response = requests.post(endpoint, json=payload, timeout=20)
    return response


def consultar_tutor_ia(pregunta):
    if not gemini_api_key:
        return "El tutor de IA no está disponible. Falta la variable GEMINI_API_KEY."

    prompt = (
        "Eres un Tutor Académico Formal y Profesional. "
        "Responde en español con claridad, precisión y un tono ejecutivo. "
        "Explica conceptos de manera estructurada, usa ejemplos cuando sean útiles y mantén la respuesta breve pero completa. "
        "Si la consulta es técnica, proporciona una explicación clara y ordenada. "
        f"Consulta: {pregunta}"
    )

    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.2,
        "maxOutputTokens": 420
    }

    modelos = [gemini_model, 'text-bison-001', 'chat-bison-001']
    modelo_probado = None
    response = None

    for modelo in modelos:
        try:
            response = _consultar_modelo_gemini(modelo, payload)
        except Exception as e:
            print(f"IA request exception for model {modelo}:", e)
            continue

        if response.status_code == 404:
            print(f"Modelo no encontrado: {modelo}")
            continue

        modelo_probado = modelo
        break

    if response is None:
        return "El tutor de IA no está disponible en este momento. Intenta de nuevo más tarde."

    if response.status_code != 200:
        print(f"IA request failed ({modelo_probado}): {response.status_code} {response.text}")
        return f"Error del tutor IA: {response.status_code} - {response.text}"

    data = response.json()

    if isinstance(data, dict):
        if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
            first = data['candidates'][0]
            if isinstance(first, dict):
                out = first.get('output') or first.get('content') or first.get('text')
                if isinstance(out, str):
                    return out
                if isinstance(out, dict):
                    return out.get('text', str(out))

        if 'output' in data:
            output = data['output']
            if isinstance(output, dict):
                content = output.get('content')
                if isinstance(content, list):
                    texts = [item.get('text', '') for item in content if isinstance(item, dict)]
                    if texts:
                        return ''.join(texts)
                return str(output)

        if 'candidates' in data and isinstance(data['candidates'][0], str):
            return data['candidates'][0]

    return "El tutor de IA no pudo generar una respuesta en este momento."


# TELEGRAM → WEB


async def recibirTelegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    usuario = (
        update.message
        .from_user
        .first_name
    )

    mensaje = update.message.text

    texto = (
        f"{usuario}: {mensaje}"
    )

    print(
        "TELEGRAM:",
        texto
    )

    socket.emit(
        "telegram_message",
        texto
    )


async def tutorTelegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    pregunta = ' '.join(context.args).strip()
    if not pregunta:
        await update.message.reply_text(
            "Usa /tutor seguido de tu consulta, por ejemplo: /tutor explica la fotosíntesis"
        )
        return

    await update.message.reply_text(
        "El tutor de IA está analizando tu consulta..."
    )

    respuesta = consultar_tutor_ia(pregunta)

    await update.message.reply_text(respuesta)
    socket.emit(
        "tutor_response",
        respuesta
    )
    enviarTelegram(
        f"📘 Tutor IA\nPregunta: {pregunta}\nRespuesta: {respuesta}"
    )


# BOT


def iniciarBot():

    asyncio.set_event_loop(
        asyncio.new_event_loop()
    )

    botTelegram.add_handler(
        CommandHandler(
            'tutor',
            tutorTelegram
        )
    )

    botTelegram.add_handler(
        MessageHandler(
            filters.TEXT
            &
            ~filters.COMMAND,
            recibirTelegram
        )
    )

    print(
        "BOT TELEGRAM ACTIVO"
    )

    botTelegram.run_polling()



# MAIN

if __name__ == "__main__":

    hiloBot = threading.Thread(
        target=iniciarBot,
        daemon=True
    )

    hiloBot.start()

    print(
        "Servidor iniciado"
    )

    puerto = int(os.getenv('PORT', 5000))
    socket.run(
        app,
        host="0.0.0.0",
        port=puerto,
        debug=False,
        allow_unsafe_werkzeug=True
    )