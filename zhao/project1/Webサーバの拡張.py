import socket
import threading
import os
from datetime import datetime
import mimetypes

SERVER_PORT = 8888
# 设置基本目录，访问 /file.html 时将读取 C:\MyWebServer\file.html
BASE_DIR = r"C:\MyWebServer"

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', SERVER_PORT))
    server_sock.listen(5)
    print(f"Open http://localhost:{SERVER_PORT}/ with your browser!")
    while True:
        client_sock, address = server_sock.accept()
        print(f"Connection from {address} has been established!")
        threading.Thread(target=handle_client, args=(client_sock,)).start()

def handle_client(client_sock: socket.socket):
    with client_sock:
        # 使用文本模式读取请求（请求头均为UTF-8文本）
        f_r = client_sock.makefile("r", encoding="utf-8")
        request_lines = []
        while True:
            line = f_r.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            print("Received:", line)
            request_lines.append(line)
            if line == "":
                break
        if not request_lines:
            print("No header received")
            return

        req_line = request_lines[0]
        parts = req_line.split(" ")
        if len(parts) != 3:
            print("Wrong request format:", parts)
            return
        method, path, http_version = parts
        print(f"Method={method}, Path={path}, HTTP_Version={http_version}")

        if method == "GET":
            handle_get(client_sock, path)
        else:
            response = "HTTP/1.0 501 Not Implemented\r\n\r\n"
            client_sock.sendall(response.encode("utf-8"))

def handle_get(client_sock: socket.socket, path: str):
    # 默认首页
    if path == "/" or path == "/index.html":
        html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Sample</title></head>
<body>This server is implemented in Python!</body>
</html>"""
        response = "HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n" + html
        client_sock.sendall(response.encode("utf-8"))

    # 返回当前服务器日期（date.html）
    elif path == "/date.html":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Server Date</title></head>
<body>Current server date and time: {now}</body>
</html>"""
        response = "HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n" + html
        client_sock.sendall(response.encode("utf-8"))

    # 当作文件请求处理
    else:
        # 去掉路径前导的斜杠，并组合到基本目录下
        file_name = path.lstrip("/")
        file_path = os.path.join(BASE_DIR, file_name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
            try:
                # 如果是文本类型文件，以UTF-8文本方式读取并发送
                if mime_type.startswith("text/"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    header = f"HTTP/1.0 200 OK\r\nContent-Type: {mime_type}; charset=UTF-8\r\n\r\n"
                    response = header + file_content
                    client_sock.sendall(response.encode("utf-8"))
                else:
                    # 二进制文件直接读取后发送（先发送HTTP头，再发送二进制内容）
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    header = f"HTTP/1.0 200 OK\r\nContent-Type: {mime_type}\r\n\r\n"
                    client_sock.sendall(header.encode("utf-8") + file_content)
            except Exception as e:
                error_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Error</title></head>
<body>Error reading file: {str(e)}</body>
</html>"""
                response = f"HTTP/1.0 500 Internal Server Error\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n" + error_html
                client_sock.sendall(response.encode("utf-8"))
        else:
            # 文件不存在，返回404页面
            html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>404 Not Found</title></head>
<body>{path} is not found</body>
</html>"""
            response = f"HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n" + html
            client_sock.sendall(response.encode("utf-8"))

if __name__ == "__main__":
    main()
