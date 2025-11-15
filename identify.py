import cv2
import easyocr
import os
import time
from mqtt_pub import publish_mqtt

MQTT_TOPIC = "/led_control"
MQTT_MESSAGE = "green_on" 

IMAGE_PATH = 'bien_so_xe.jpg'
OUTPUT_IMAGE_PATH = 'ket_qua_bien_so.jpg'
OUTPUT_TEXT_PATH = 'bien_so_xe.txt'
WHITELIST_FILE = 'check_bien.txt'

def check_plates_in_whitelist(detected_clean_plates, whitelist_path):
    if not detected_clean_plates:
        return None
    try:
        with open(whitelist_path, 'r', encoding='utf-8') as f:
            allowed_plates = {line.strip().upper() for line in f if line.strip()}
        
        if not allowed_plates:
            print(f"Cảnh báo: File whitelist '{whitelist_path}' bị rỗng.")
            return None
            
        print(f"\nĐã tải {len(allowed_plates)} biển số hợp lệ từ {whitelist_path}.")

        for plate in detected_clean_plates:
            if plate in allowed_plates:
                print(f"Biển số '{plate}' có trong file {whitelist_path}.")
                return plate
        
        print("Không có biển số nào phát hiện được trùng với file whitelist.")
        return None
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file whitelist '{whitelist_path}'.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file whitelist: {e}")
        return None

def recognize_license_plate(img_path, out_img_path, out_txt_path, whitelist_path):
    print("Đang khởi tạo EasyOCR Reader với CPU...")
    try:
        reader = easyocr.Reader(['en'], gpu=True) 
    except Exception as e:
        print(f"Lỗi khởi tạo EasyOCR: {e}")
        return

    img = cv2.imread(img_path)
    if img is None:
        print(f"Lỗi: Không thể đọc file ảnh tại '{img_path}'.")
        return
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print("Bắt đầu nhận diện văn bản...")
    results = reader.readtext(gray_img, detail=1)
    
    img_display = img.copy()
    found_clean_plates = []
    plates_to_draw = []

    for (bbox, text, prob) in results:
        if prob < 0.45:
            continue
        clean_text = text.upper().replace('.', '').replace('-', '').replace(' ', '')
        if (len(clean_text) >= 6 and len(clean_text) <= 10) and \
           any(c.isdigit() for c in clean_text) and \
           any(c.isalpha() for c in clean_text):
            
            plate_text_raw = text.upper()
            found_clean_plates.append(clean_text)
            plates_to_draw.append((bbox, plate_text_raw))
            print(f"Phát hiện biển số  '{plate_text_raw}'")

    for (bbox, text) in plates_to_draw:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left_pt = (int(top_left[0]), int(top_left[1]))
        bottom_right_pt = (int(bottom_right[0]), int(bottom_right[1]))
        cv2.rectangle(img_display, top_left_pt, bottom_right_pt, (0, 255, 0), 2)
        cv2.putText(img_display, text, (top_left_pt[0], top_left_pt[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    matched_plate = check_plates_in_whitelist(found_clean_plates, whitelist_path)
    
    if matched_plate:
        print(f"Hợp lệ: '{matched_plate}'. Đang gửi MQTT...")
        publish_mqtt(MQTT_TOPIC, MQTT_MESSAGE)
    else:
        if found_clean_plates:
            print("Đã phát hiện biển số, nhưng không có trong file whitelist.")
        else:
            print("Không phát hiện biển số nào.")

    if found_clean_plates:
        try:
            with open(out_txt_path, 'w', encoding='utf-8') as f:
                for plate in found_clean_plates:
                    f.write(f"{plate}\n")
            print(f"\nLưu file TXT log thành công: {out_txt_path}")
        except Exception as e:
            print(f"Lỗi khi lưu file TXT log: {e}")
    else:
        open(out_txt_path, 'w').close() 

    try:
        cv2.imwrite(out_img_path, img_display)
        print(f"Đã lưu vào file: {out_img_path}")
    except Exception as e:
        print(f"Lỗi khi lưu ảnh: {e}")

if __name__ == "__main__":
    recognize_license_plate(IMAGE_PATH, OUTPUT_IMAGE_PATH, OUTPUT_TEXT_PATH, WHITELIST_FILE)