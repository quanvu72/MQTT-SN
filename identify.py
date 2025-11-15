import cv2
import easyocr
import os
import paho.mqtt.client as mqtt
import time

# --- Cấu hình MQTT ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "/led_control"
MQTT_MESSAGE = "green_on"

# --- Cấu hình đường dẫn file ---
IMAGE_PATH = 'bien_so_xe.jpg'
OUTPUT_IMAGE_PATH = 'ket_qua_bien_so.jpg'
OUTPUT_TEXT_PATH = 'bien_so_xe.txt' # File log TẤT CẢ biển số phát hiện được
WHITELIST_FILE = 'check_bien.txt' # File để KIỂM TRA biển số hợp lệ

# --- Hàm để gửi tin nhắn MQTT ---
def publish_mqtt(broker, port, topic, message):
    """
    Kết nối đến MQTT broker, gửi một tin nhắn và ngắt kết nối.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        print(f"\nĐang kết nối đến MQTT Broker tại {broker}:{port}...")
        client.connect(broker, port, 60)
        client.loop_start()
        time.sleep(1) # Cho 1 giây để kết nối ổn định

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

# --- Hàm mới để kiểm tra biển số trong file ---
def check_plates_in_whitelist(detected_clean_plates, whitelist_path):
    """
    Đọc file whitelist và kiểm tra xem có biển số nào phát hiện được nằm trong file không.
    Trả về biển số đầu tiên trùng khớp, hoặc None nếu không có.
    """
    if not detected_clean_plates:
        return None # Không có biển số nào để kiểm tra

    try:
        with open(whitelist_path, 'r', encoding='utf-8') as f:
            # Đọc file, strip khoảng trắng/xuống dòng, chuyển sang UPPER
            allowed_plates = {line.strip().upper() for line in f if line.strip()}
        
        if not allowed_plates:
            print(f"Cảnh báo: File whitelist '{whitelist_path}' bị rỗng.")
            return None
            
        print(f"\nĐã tải {len(allowed_plates)} biển số hợp lệ từ {whitelist_path}.")

        # So sánh
        for plate in detected_clean_plates:
            if plate in allowed_plates:
                print(f"**TRÙNG KHỚP!** Biển số '{plate}' có trong file {whitelist_path}.")
                return plate # Trả về biển số hợp lệ đầu tiên tìm thấy
        
        print("Không có biển số nào phát hiện được trùng với file whitelist.")
        return None # Không tìm thấy trùng khớp

    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file whitelist '{whitelist_path}'. Vui lòng tạo file.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file whitelist: {e}")
        return None

# --- Hàm nhận diện biển số (Đã cập nhật logic) ---
def recognize_license_plate(img_path, out_img_path, out_txt_path, whitelist_path):
    """
    Phát hiện biển số, kiểm tra với whitelist, lưu file và gửi MQTT.
    """
    
    # 1. Khởi tạo EasyOCR
    print("Đang khởi tạo EasyOCR Reader với CPU...")
    try:
        reader = easyocr.Reader(['en'], gpu=False) # Đổi thành True nếu muốn dùng GPU
    except Exception as e:
        print(f"Lỗi khởi tạo EasyOCR: {e}")
        return

    # 2. Đọc ảnh
    img = cv2.imread(img_path)
    if img is None:
        print(f"Lỗi: Không thể đọc file ảnh tại '{img_path}'.")
        return
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Nhận diện
    print("Bắt đầu nhận diện văn bản...")
    results = reader.readtext(gray_img, detail=1)
    print(f"\n--- Đã phát hiện {len(results)} vùng văn bản ---")
    
    img_display = img.copy()
    
    # `found_clean_plates` sẽ lưu biển số đã được làm sạch (ví dụ: "51G12345")
    # `plates_to_draw` sẽ lưu [bbox, raw_text] để vẽ (ví dụ: "51G-123.45")
    found_clean_plates = []
    plates_to_draw = []

    # 4. Lọc kết quả
    for (bbox, text, prob) in results:
        if prob < 0.45:
            continue

        # Luôn làm sạch text để kiểm tra
        clean_text = text.upper().replace('.', '').replace('-', '').replace(' ', '')
        
        if (len(clean_text) >= 6 and len(clean_text) <= 10) and \
           any(c.isdigit() for c in clean_text) and \
           any(c.isalpha() for c in clean_text):
            
            plate_text_raw = text.upper() # Text gốc để vẽ
            
            found_clean_plates.append(clean_text) # Lưu text SẠCH để so sánh
            plates_to_draw.append((bbox, plate_text_raw)) # Lưu text GỐC để vẽ
            
            print(f"**Phát hiện biển số (chưa kiểm tra):** '{plate_text_raw}' -> (Sạch: '{clean_text}')")

    # 4.5. Vẽ TẤT CẢ các biển số phát hiện được (bất kể hợp lệ hay không)
    for (bbox, text) in plates_to_draw:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left_pt = (int(top_left[0]), int(top_left[1]))
        bottom_right_pt = (int(bottom_right[0]), int(bottom_right[1]))
        
        cv2.rectangle(img_display, top_left_pt, bottom_right_pt, (0, 255, 0), 2)
        cv2.putText(img_display, text, (top_left_pt[0], top_left_pt[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # --- 5. Kiểm tra Whitelist VÀ GỬI MQTT (ĐÃ THAY ĐỔI) ---
    
    # 5.1. Kiểm tra với file 'check_bien.txt'
    matched_plate = check_plates_in_whitelist(found_clean_plates, whitelist_path)
    
    if matched_plate:
        # Nếu có trùng khớp (matched_plate không phải là None)
        print(f"Phát hiện biển số hợp lệ: '{matched_plate}'. Đang gửi MQTT...")
        
        # --- GỌI HÀM GỬI MQTT ---
        publish_mqtt(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_MESSAGE)
    else:
        # (Không tìm thấy biển số HOẶC tìm thấy nhưng không có trong whitelist)
        if found_clean_plates:
            print("Đã phát hiện biển số, nhưng không có trong file whitelist.")
        else:
            print("Không phát hiện biển số nào.")

    # 5.2. Lưu file .txt (log tất cả biển số SẠCH đã phát hiện)
    if found_clean_plates:
        print(f"\nĐang lưu {len(found_clean_plates)} biển số đã phát hiện vào file log {out_txt_path}...")
        try:
            with open(out_txt_path, 'w', encoding='utf-8') as f:
                for plate in found_clean_plates:
                    f.write(f"{plate}\n")
            print(f"Lưu file TXT log thành công.")
        except Exception as e:
            print(f"Lỗi khi lưu file TXT log: {e}")
    else:
        # Tạo file txt rỗng nếu không tìm thấy gì
        open(out_txt_path, 'w').close() 

    # 5.3. Luôn lưu file ảnh (đã vẽ ở bước 4.5)
    try:
        cv2.imwrite(out_img_path, img_display)
        print(f"Đã lưu ảnh kết quả vào file: {out_img_path}")
    except Exception as e:
        print(f"Lỗi khi lưu file ảnh: {e}")

# --- Chạy chương trình ---
if __name__ == "__main__":
    recognize_license_plate(IMAGE_PATH, OUTPUT_IMAGE_PATH, OUTPUT_TEXT_PATH, WHITELIST_FILE)