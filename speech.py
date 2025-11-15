import speech_recognition as sr
import time
from mqtt_pub import publish_mqtt 

MQTT_TOPIC = "/led_control"

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

            elif ("bật" in command or "mở" in command) and ("đèn" in command or "led" in command or "xanh" in command):
                print("=> Phát hiện lệnh BẬT.")
                publish_mqtt(MQTT_TOPIC, "green_on")

            elif ("tắt" in command) and ("đèn" in command or "led" in command or "xanh" in command):
                print("=> Phát hiện lệnh TẮT.")
                publish_mqtt(MQTT_TOPIC, "green_off")
            else:
                print("Không tìm thấy lệnh phù hợp.")

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            print("Không nghe rõ, vui lòng nói lại.")
        except sr.RequestError:
            print("Lỗi kết nối Google API.")
        except Exception as e:
            print(f"Lỗi hệ thống: {e}")
            break