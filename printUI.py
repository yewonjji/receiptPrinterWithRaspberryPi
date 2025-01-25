import serial
from PIL import Image, ImageDraw, ImageFont
import qrcode
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import tkinter as tk
from threading import Thread

# Tkinter 초기화
root = tk.Tk()
root.title("RFID 상태")
root.geometry("800x400")

# 상태 메시지 라벨
status_label = tk.Label(root, text="태그를 인식해주세요", font=("NanumGothic", 24))
status_label.pack(expand=True)

# 상태 메시지 업데이트 함수
def update_status(message):
    status_label.config(text=message)
    root.update_idletasks()

# RFID 리더기 초기화
reader = SimpleMFRC522()

# 프린터 설정
printer_port = "/dev/ttyACM0"  # 라즈베리파이에서 프린터가 연결된 포트
baud_rate = 19200  # 프린터의 통신 속도
printer = serial.Serial(printer_port, baudrate=baud_rate, timeout=1)

# RFID ID와 URL 매핑
rfid_url_mapping = {
    123456789: "https://example.com/user1",
    987654321: "https://example.com/user2",
    111122223: "https://example.com/user3",
}

# 한글 폰트 경로 (Nanum Gothic 폰트 설치 필요)
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# RFID 스캔 및 영수증 출력 함수
def rfid_reader():
    try:
        while True:
            update_status("태그를 인식해주세요")
            print("RFID 스캔 대기 중...")
            # RFID 카드 ID 읽기
            id = reader.read()[0]
            update_status("인식 중입니다")
            print(f"RFID ID 읽음: {id}")

            # URL 매핑
            participation_qr_data = rfid_url_mapping.get(id, "https://example.com/default")
            print(f"생성된 URL: {participation_qr_data}")

            # 프린터 초기화 및 영수증 생성
            printer.write(b'\x1b\x40')  # ESC @ (초기화)
            participation_qr = qrcode.QRCode(box_size=6, border=2)
            participation_qr.add_data(participation_qr_data)
            participation_qr.make(fit=True)
            participation_qr_img = participation_qr.make_image(fill="black", back_color="white").convert("1")

            width, height = 580, 800
            receipt_img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(receipt_img)
            font_small = ImageFont.truetype(font_path, 26)
            font_large = ImageFont.truetype(font_path, 30)

            title_text = "=== 3DOWON SOLO EXHIBITION ==="
            title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            x = (width - title_width) // 2
            y = 0
            draw.text((x, y), title_text, fill="black", font=font_large)

            # QR 코드와 정보 추가
            info_text = [
                f"[RFID ID]: {id}",
                f"[URL]: {participation_qr_data}",
                "======================",
                "*참여 QR 코드",
            ]
            y_offset = 55
            for line in info_text:
                draw.text((10, y_offset), line, fill="black", font=font_small)
                y_offset += 30
            qr_x = (width - participation_qr_img.size[0]) // 2
            receipt_img.paste(participation_qr_img, (qr_x, y_offset))
            receipt_img = receipt_img.convert("1")
            receipt_img.save("receipt.bmp")

            # BMP 이미지 프린터로 전송
            qr_image = Image.open("receipt.bmp").convert("1")
            width, height = qr_image.size
            bytes_per_row = (width + 7) // 8
            image_data = bytearray()
            for y in range(height):
                row = bytearray()
                for x in range(0, width, 8):
                    byte = 0
                    for bit in range(8):
                        if x + bit < width and qr_image.getpixel((x + bit, y)) == 0:
                            byte |= 1 << (7 - bit)
                    row.append(byte)
                image_data.extend(row)
            printer.write(b'\x1d\x76\x30\x00')
            printer.write(bytes([bytes_per_row % 256, bytes_per_row // 256]))
            printer.write(bytes([height % 256, height // 256]))
            printer.write(image_data)
            printer.write(b'\x1d\x56\x42\x00')

            update_status("인식 완료!")
            print("영수증 출력 완료")
            time.sleep(2)  # 2초 대기
    finally:
        GPIO.cleanup()
        printer.close()
        print("프로그램 종료")

# RFID 스캔을 별도의 스레드로 실행
rfid_thread = Thread(target=rfid_reader, daemon=True)
rfid_thread.start()

# Tkinter 메인 루프 실행
root.mainloop()
