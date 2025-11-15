from paho.mqtt import client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connect success")
        client.subscribe(TOPIC)   
    else:
        print("Error:", rc)

def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload.decode()}") 

client = mqtt.Client(client_id="sub-test")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)

client.loop_forever()
