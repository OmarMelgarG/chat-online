import socketio # Librería moderna para hablar con el servidor web
import threading

# Configuración
sio = socketio.Client()
server_ip = "http://192.168.172.254:5000" # Importante el http://

nombre = input("Ingrese su nombre para el chat: ")

@sio.event
def connect():
    print("✅ Conectado al servidor de chat.")
    sio.send(f"{nombre} se ha unido desde la terminal")

@sio.event
def message(data):
    # No imprimir si el mensaje es nuestro para no duplicar
    if not data.startswith(f"{nombre}:"):
        print(f"\n{data}")
        print(f"{nombre}: ", end="", flush=True)

@sio.event
def disconnect():
    print("❌ Desconectado del servidor.")

def enviar_mensajes():
    while True:
        msg = input(f"{nombre}: ")
        if msg.lower() == 'salir':
            sio.disconnect()
            break
        sio.send(f"{nombre}: {msg}")

if __name__ == '__main__':
    try:
        sio.connect(server_ip)
        # Hilo para que la entrada de texto no bloquee la recepción de mensajes
        hilo = threading.Thread(target=enviar_mensajes)
        hilo.start()
    except:
        print("No se pudo conectar al servidor. ¿Está chatOnline.py encendido?")