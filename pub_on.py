from paho.mqtt import client as mqtt
import asyncio

#broker = "localhost"
broker = "192.168.18.129"
data_test = "blue_on"

client = mqtt.Client(client_id="1236", clean_session=True)
client.connect(broker, 1883)
    
async def main():
    client.publish("/led_control", data_test)
    await asyncio.sleep(4)

asyncio.run(main())
client.disconnect()