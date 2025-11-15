import speech_recognition as sr
import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "/led_control"

def publish_mqtt(broker, port, topic, message):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        client.connect(broker, port, 60)
        client.loop_start()
        time.sleep(1) 

        result = client.publish(topic, message)
        result.wait_for_publish(timeout=5)
        
        if result.is_published():
            print(f"-> Đã gửi lệnh: {message}")
        else:
            print("-> Gửi thất bại.")

        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"Lỗi MQTT: {e}")
        if client.is_connected():
            client.disconnect()

r = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    print("Đang hiệu chỉnh tiếng ồn nền... Vui lòng giữ im lặng.")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Đã sẵn sàng! Hãy nói lệnh (hoặc nói 'dừng lại' để thoát).")

while True:
    with mic as source:
        print("\nĐang lắng nghe...")
        try:
            audio = r.listen(source, timeout=None, phrase_time_limit=5)
            
            print("Đang nhận diện...")
            text = r.recognize_google(audio, language="vi-VN")
            print(f"Bạn nói: {text}")
            
            command = text.lower()
            
            if "dừng lại" in command or "thoát" in command:
                print("Đang thoát chương trình...")
                break

            elif ("bật" in command or "mở" in command) and ("đèn" in command or "led" in command) and ("xanh" in command):
                print("=> Phát hiện lệnh BẬT.")
                publish_mqtt(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, "green_on")

            elif ("tắt" in command) and ("đèn" in command or "led" in command) and ("xanh" in command):
                print("=> Phát hiện lệnh TẮT.")
                publish_mqtt(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, "green_off")

            else:
                print("Không tìm thấy lệnh phù hợp.")

        except sr.WaitTimeoutError:
            pass 
        except sr.UnknownValueError:
            print("Không nghe rõ, vui lòng nói lại.")
        except sr.RequestError:
            print("Lỗi kết nối Google API. Kiểm tra internet.")
        except Exception as e:
            print(f"Lỗi hệ thống: {e}")
            break