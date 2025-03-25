import socket

# 수신할 포트 설정 (예: 8888)
UDP_IP = "0.0.0.0"  # 모든 인터페이스에서 수신
UDP_PORT = 8888

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP {UDP_IP}:{UDP_PORT}")

while True:
    data, addr = sock.recvfrom(1024)  # 최대 1024바이트 수신
    print(f"Received from {addr}: {data.decode()}")
