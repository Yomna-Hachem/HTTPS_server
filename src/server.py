import socket
import threading
import ssl
from handler import handle_http2_requests

# Server Configuration
HOST = '127.0.0.1'
PORT = 8080

CERT_FILE = "/Users/yomna.hashem/Documents/Semester 7/Networks/Project/TRIAL 1/certificates/cert.cert"
KEY_FILE = "/Users/yomna.hashem/Documents/Semester 7/Networks/Project/TRIAL 1/certificates/key.key"

def start_server():
    try:
        # Create a socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the address
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Server started on {HOST}:{PORT}")

        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            context.set_alpn_protocols(["h2", "http/1.1"])
        
        except ssl.SSLError as e:
            print(f"SSL error: {e}")
            return

        while True:
            try:
                
                client_socket, client_address = server.accept()
                print(f"New connection from {client_address}")
                secure_socket = context.wrap_socket(client_socket, server_side=True)

                selected_protocol = secure_socket.selected_alpn_protocol()
                if selected_protocol == "h2":
                    print(f"Client {client_address} upgraded to HTTP/2")
                else:
                    print(f"Client {client_address} is using HTTP/1.1")
                    handle_http2_requests(client_socket, client_socket.recv(1024).decode)

                threading.Thread(target=request_handler, args=(secure_socket,), daemon=True).start()

            except Exception as e:
                print(f"Error accepting a connection: {e}")

    except Exception as e:
        print(f"Server failed to start: {e}")
    finally:
        print("Shutting down the server")
        server.close()
        
def request_handler(connection_socket):
    
    try:
        
        handle_http2_requests(connection_socket)
        
    except Exception as e:
        print(f"Error handling request: {e}")
        response = """HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\n500 Internal Server Error"""
        connection_socket.send(response.encode())    


    
if __name__ == "__main__":
    start_server()