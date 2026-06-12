from flask import Flask
from flask_socketio import SocketIO, send
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes
)

import threading
import requests
import eventlet
import os



# CONFIGURACION TELEGRAM


tokenTelegram = os.getenv("TOKEN_TELEGRAM")
chatID = os.getenv("CHAT_ID")


eventlet.monkey_patch()


# CREAR APP


app = Flask(__name__)


# CONFIGURAR SOCKETIO


socket = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)


# CREAR BOT TELEGRAM


botTelegram = ApplicationBuilder().token(
    tokenTelegram
).build()


# PAGINA PRINCIPAL


@app.route("/")
def index():

    return """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Chat Tiempo Real</title>

<style>

body{
    font-family:Arial;
    background:#f2f2f2;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
    margin:0;
}

.chat-container{
    width:95%;
    max-width:450px;
    background:white;
    border-radius:10px;
    overflow:hidden;
    box-shadow:0 0 10px rgba(0,0,0,0.2);
}

.chat-header{
    background:#007bff;
    color:white;
    padding:15px;
    text-align:center;
    font-size:20px;
    font-weight:bold;
}

#chat{
    height:400px;
    overflow-y:auto;
    padding:10px;
    background:#fafafa;
}

.mensaje{
    background:#e4e6eb;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
    word-wrap:break-word;
}

.controls{
    padding:10px;
    border-top:1px solid #ddd;
}

.input-group{
    display:flex;
    gap:10px;
    margin-bottom:10px;
}

input{
    flex:1;
    padding:10px;
    border:1px solid #ccc;
    border-radius:5px;
}

button{
    padding:10px 15px;
    border:none;
    background:#007bff;
    color:white;
    border-radius:5px;
    cursor:pointer;
}

button:hover{
    background:#0056b3;
}

#btn-entrar{
    background:#28a745;
}

#btn-entrar:hover{
    background:#1e7e34;
}

</style>

</head>

<body>

<div class="chat-container">

    <div class="chat-header">
        Chat Tiempo Real
    </div>

    <div id="chat"></div>

    <div class="controls">

        <div class="input-group">

            <input
                type="text"
                id="nombre"
                placeholder="Tu nombre"
            >

            <button
                id="btn-entrar"
                onclick="guardarNombre()"
            >
                Entrar
            </button>

        </div>

        <div class="input-group">

            <input
                type="text"
                id="mensaje"
                placeholder="Escribe un mensaje"
            >

            <button onclick="enviar()">
                Enviar
            </button>

        </div>

    </div>

</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<script>

var socket = io();

var nombre = "";


// GUARDAR NOMBRE


function guardarNombre(){

    let input = document.getElementById("nombre");

    if(input.value.trim() == ""){

        alert("Ingrese su nombre");

        return;
    }

    nombre = input.value;

    input.disabled = true;

    document.getElementById(
        "btn-entrar"
    ).disabled = true;

    agregarMensaje(
        "Sistema",
        nombre + " se unió al chat"
    );
}


// ENVIAR MENSAJE


function enviar(){

    let mensajeInput =
        document.getElementById("mensaje");

    let mensaje = mensajeInput.value;

    if(nombre == ""){

        alert("Debe ingresar su nombre");

        return;
    }

    if(mensaje.trim() == ""){

        return;
    }

    socket.send(
        nombre + ": " + mensaje
    );

    mensajeInput.value = "";
}


// MENSAJES NORMALES


socket.on("message", function(msg){

    agregarChat(msg);
});

// =====================================
// MENSAJES DESDE TELEGRAM
// =====================================

socket.on("telegram_message", function(msg){

    agregarChat("Telegram: " + msg);
});

// =====================================
// AGREGAR MENSAJES
// =====================================

function agregarChat(msg){

    let chat = document.getElementById("chat");

    let div = document.createElement("div");

    div.className = "mensaje";

    if(msg.includes(":")){

        let partes = msg.split(":");

        div.innerHTML =
            "<strong>" +
            partes[0] +
            ":</strong> " +
            partes.slice(1).join(":");

    }else{

        div.innerText = msg;
    }

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}

// =====================================
// MENSAJE LOCAL
// =====================================

function agregarMensaje(usuario, texto){

    let chat = document.getElementById("chat");

    let div = document.createElement("div");

    div.className = "mensaje";

    div.innerHTML =
        "<strong>" +
        usuario +
        ":</strong> " +
        texto;

    chat.appendChild(div);
}

</script>

</body>
</html>
"""

# MENSAJES DESDE WEB


@socket.on("message")
def recibirMensaje(mensaje):

    print("Mensaje WEB:", mensaje)

    # Mostrar a todos los clientes WEB
    send(mensaje, broadcast=True)

    # Enviar a Telegram
    threading.Thread(
        target=enviarTelegram,
        args=(mensaje,)
    ).start()


# ENVIAR A TELEGRAM


def enviarTelegram(mensaje):

    url = (
        f"https://api.telegram.org/bot"
        f"{tokenTelegram}/sendMessage"
    )

    data = {
        "chat_id": chatID,
        "text": f"{mensaje}"
    }

    try:

        requests.post(url, data=data)

    except Exception as e:

        print("Error Telegram:", e)


# RECIBIR DESDE TELEGRAM


async def recibirTelegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    usuario = update.message.from_user.first_name

    mensaje = update.message.text

    texto = f"{usuario}: {mensaje}"

    print("Telegram:", texto)

    # SOLO enviar a WEB
    socket.emit(
        "telegram_message",
        texto
    )


# INICIAR BOT


def iniciarBot():

    botTelegram.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            recibirTelegram
        )
    )

    print("BOT TELEGRAM ACTIVO")

    botTelegram.run_polling()


# MAIN


if __name__ == "__main__":

    hiloBot = threading.Thread(
        target=iniciarBot
    )

    hiloBot.start()

    print("Servidor iniciado")

    socket.run(
        app,
        host="0.0.0.0",
        port=5000
    )