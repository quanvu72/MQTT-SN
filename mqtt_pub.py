# File: mqtt_pub.py
import paho.mqtt.client as mqtt
import time

# --- Cấu hình MQTT (Theo yêu cầu) ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# ĐỊNH NGHĨA HÀM PHẢI NHƯ THẾ NÀY:
def publish_mqtt(topic, message, broker=MQTT_BROKER, port=MQTT_PORT):
    """
    Kết nối đến MQTT broker, gửi một tin nhắn và ngắt kết nối.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        print(f"\nĐang kết nối đến MQTT Broker {broker}:{port}...")
        client.connect(broker, port, 60)
        
        client.loop_start()
        
        print(f"Đang gửi tin nhắn: Topic='{topic}', Message='{message}'")
        result = client.publish(topic, message)
        
        result.wait_for_publish(timeout=5)
        
        if result.is_published():
            print("Gửi tin nhắn MQTT thành công.")
        else:
            print("Gửi tin nhắn MQTT thất bại.")

        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"Lỗi kết nối hoặc gửi MQTT: {e}")
        if client.is_connected():
            client.disconnect()
        client.loop_stop()