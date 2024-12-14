import socket
import threading
import os
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pymongo import MongoClient
from urllib.parse import parse_qs

# ------------------- CONFIG -------------------
HTTP_PORT = 3000
SOCKET_PORT = 5000
MONGO_URI = "mongodb+srv://mongodbuser:theBestPasswordInWorld123@cluster0.mlqna.mongodb.net/test?retryWrites=true&w=majority"
DB_NAME = "messages_db"
COLLECTION_NAME = "messages"
STATIC_DIR = "static"

# ------------------- MONGO INIT -------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ------------------- SOCKET SERVER -------------------
def socket_server():
    """Socket server to handle form data and save to MongoDB."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", SOCKET_PORT))
    server_socket.listen(5)
    print(f"[SOCKET SERVER] Listening on port {SOCKET_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[SOCKET SERVER] Connection from {addr}")
        data = client_socket.recv(1024)
        if data:
            try:
                # Decode and parse the received data
                received_json = data.decode("utf-8")
                message_data = json.loads(received_json)
                message_data["date"] = str(datetime.now())

                # Save to MongoDB
                collection.insert_one(message_data)
                print(f"[SOCKET SERVER] Data saved: {message_data}")
            except Exception as e:
                print(f"[SOCKET SERVER] Error: {e}")
        client_socket.close()

# ------------------- HTTP SERVER -------------------
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/" or self.path == "/index.html":
            self.serve_file("index.html")
        elif self.path == "/message.html":
            self.serve_file("message.html")
        elif self.path.endswith(".css"):
            self.serve_file("style.css")
        elif self.path.endswith(".png"):
            self.serve_file("logo.png")
        else:
            self.send_error(404, f"File Not Found: {self.path}")
            self.serve_file("error.html")
    
    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])  # Get the size of data
            post_data = self.rfile.read(content_length)  # Read the POST body

        # Parse the form data
            parsed_data = parse_qs(post_data.decode("utf-8"))

        # Get the username and message from parsed data
            username = parsed_data.get("username", ["Anonymous"])[0]
            message = parsed_data.get("message", [""])[0]

        # Prepare the message for the socket server
            socket_data = json.dumps({"username": username, "message": message})

        # Send the data to the socket server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(('localhost', SOCKET_PORT))
                sock.sendall(socket_data.encode('utf-8'))

        # Log the message to the console (or further process it)
            print(f"[HTTP SERVER] Sent to socket: username={username}, message={message}")

        # Send a success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "success", "message": "Message received"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")
            self.serve_file("error.html")


    def serve_file(self, file_path, status_code=200):
        """Serve an HTML file."""
        try:
            with open(file_path, "rb") as file:
                self.send_response(status_code)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, f"File Not Found: {file_path}")

    def serve_static_file(self, file_path):
        """Serve static files (CSS, images, etc.)."""
        try:
            if file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_path.endswith(".js"):
                content_type = "application/javascript"
            else:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as file:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, f"Static File Not Found: {file_path}")


# ------------------- MAIN FUNCTION -------------------
def main():
    # Start the socket server in a thread
    threading.Thread(target=socket_server, daemon=True).start()

    # Start the HTTP server
    print(f"[HTTP SERVER] Serving on port {HTTP_PORT}")
    httpd = HTTPServer(("0.0.0.0", HTTP_PORT), SimpleHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    main()
