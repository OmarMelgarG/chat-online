from flask import Flask
from flask_socketio import SocketIO, send
import os

# Crear la app
app = Flask(__name__)
socket = SocketIO(app, cors_allowed_origins="*")

# Ruta principal
@app.route("/")
def index():
    return """  
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat en tiempo real</title>
    </head>
    <body>

    <h2>Chat en tiempo real</h2>

    <input type="text" id="nombre" placeholder="Ingrese su nombre">
    <button onclick="guardarNombre()">Entrar</button>

    <br><br>

    <div id="chat" style="border:1px solid #000; height:200px; overflow-y:scroll; padding:10px;"></div>

    <br>

    <input type="text" id="mensaje" placeholder="Ingrese el mensaje">
    <button onclick="enviar()">Enviar</button>

    <!-- Librería Socket.IO -->
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>

    <script>
        var socket = io();
        var nombre = "";

        function guardarNombre(){
            nombre = document.getElementById("nombre").value;
        }

        function enviar(){
            var mensajeInput = document.getElementById("mensaje");
            var mensaje = mensajeInput.value;

            if(nombre === "" || mensaje === ""){
                alert("Debe ingresar nombre y mensaje");
                return;
            }

            socket.send(nombre + ": " + mensaje);

            // Limpiar input
            mensajeInput.value = "";
        }

        socket.on("message", function(mensaje){
            var chat = document.getElementById("chat");
            chat.innerHTML += "<p>" + mensaje + "</p>";
            chat.scrollTop = chat.scrollHeight; // auto scroll
        });
    </script>

    </body>
    </html>
    """

# Evento de mensaje
@socket.on("message")
def conexionMensaje(mensaje):
    send(mensaje, broadcast=True)

# Ejecutar servidor
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    socket.run(app, host="0.0.0.0", port=puerto)