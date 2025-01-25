import serial
from PIL import Image, ImageDraw, ImageFont
import qrcode

# 프린터 설정
printer_port = "/dev/ttyACM0"  # 라즈베리파이에서 프린터가 연결된 포트
baud_rate = 19200  # 프린터의 통신 속도
printer = serial.Serial(printer_port, baudrate=baud_rate, timeout=1)

# 1. 초기화 명령어
printer.write(b'\x1b\x40')  # ESC @ (초기화)

# 2. 영수증 텍스트와 이미지 생성
# QR 코드 생성
participation_qr_data = "https://3dowon.com"
participation_qr = qrcode.QRCode(box_size=6, border=2)
participation_qr.add_data(participation_qr_data)
participation_qr.make(fit=True)
participation_qr_img = participation_qr.make_image(fill="black", back_color="white").convert("1")

# 영수증 이미지 생성
width, height = 580, 800
receipt_img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(receipt_img)

# 폰트 설정
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 라즈베리파이 폰트 경로
font_small = ImageFont.truetype(font_path, 26)
font_large = ImageFont.truetype(font_path, 30)

# 제목 텍스트
title_text = "=== 3DOWON SOLO EXHIBITION ==="
title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
title_width = title_bbox[2] - title_bbox[0]
x = (width - title_width) // 2
y = 0
draw.text((x, y), title_text, fill="black", font=font_large)

# 전시 정보
info_text = [
    "[장 소] CICA 미술관 3-A 전시실",
    "[날 짜] 2025.03.26 - 2025.03.30",
    "[시 간] 10:30 - 17:30",
    "======================",
    "몇 동 몇 호",
    "Which unit number is your house?",
    "======================",
    "*참여 가이드",
    "1. Wi-Fi에 연결해주세요.",
    "2. QR 코드를 스캔하여 작품의 세계에 참여하세요.",
    "",
    "*Wi-Fi 정보",
    "SSID: 아무개의 방_WiFi",
    "P.W: 1234abcd",
    "",
    "*참여 QR 코드",
]
y_offset = 55
for line in info_text:
    draw.text((10, y_offset), line, fill="black", font=font_small)
    y_offset += 30

# 참여 QR 코드 삽입
qr_x = (width - participation_qr_img.size[0]) // 2
receipt_img.paste(participation_qr_img, (qr_x, y_offset))
y_offset += participation_qr_img.size[1] + 20

# 마지막 문구 추가
final_text = "@3dowon"
final_text_bbox = draw.textbbox((0, 0), final_text, font=font_small)
final_text_width = final_text_bbox[2] - final_text_bbox[0]
final_x = (width - final_text_width) // 2
draw.text((final_x, y_offset), final_text, fill="black", font=font_small)

# 4. 영수증 이미지를 BMP로 저장
receipt_img = receipt_img.convert("1")
receipt_img.save("receipt.bmp")

# 5. BMP 이미지 데이터를 ESC/POS 명령어로 프린터로 전송
qr_image = Image.open("receipt.bmp").convert("1")
width, height = qr_image.size
bytes_per_row = (width + 7) // 8
image_data = bytearray()

for y in range(height):
    row = bytearray()
    for x in range(0, width, 8):
        byte = 0
        for bit in range(8):
            if x + bit < width and qr_image.getpixel((x + bit, y)) == 0:  # 검은색 픽셀
                byte |= 1 << (7 - bit)
        row.append(byte)
    image_data.extend(row)

printer.write(b'\x1d\x76\x30\x00')  # 이미지 출력 명령
printer.write(bytes([bytes_per_row % 256, bytes_per_row // 256]))  # 너비
printer.write(bytes([height % 256, height // 256]))  # 높이
printer.write(image_data)

# 6. 용지 자르기 명령 추가
printer.write(b'\x1d\x56\x42\x00')  # 용지 자르기 명령

# 7. 프린터 종료
printer.close()
