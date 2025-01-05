import socket
import threading

from http1Server import handle_request

UPGRADE_REQUEST = False

def start_tcp_server(port, connection_handler):

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", port))
    server_socket.listen(5)

    print(f"server is running on port {port}...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection accepted from {addr}")
        
        client_thread = threading.Thread(target=connection_handler, args=(client_socket,))
        client_thread.start()
     
def request_handler(client_socket):
    request = client_socket.recv(1024)
    HTTP1_FLAG, HTTP2_FLAG =  check_version(request)
                
    
    if HTTP1_FLAG:
        print("This is an HTTP/1.x request.")
        handle_request(client_socket, request.decode())

    
    elif HTTP2_FLAG:
        print("This is an HTTP/2 request.")
    else:
        print("Unable to determine the protocol. This may be a different HTTP version or malformed request.")
    
    # Close the client connection
    client_socket.close()

def check_version(request):
    HTTP1_FLAG = False
    HTTP2_FLAG = False
    try:
        # Decode the request and split by lines
        lines = request.decode('utf-8').split("\r\n")
        
        # Check if the first line is in the format "METHOD /path HTTP/1.x"
        if len(lines) > 0:
            first_line = lines[0]
            print("first line: " + first_line)
            if 'HTTP/1.' in first_line:
                HTTP1_FLAG = True
                
    except Exception as e:
        print(f"Error checking HTTP/1.x: {e}")
        HTTP2_FLAG = True
    
    print("http1" + str(HTTP1_FLAG))
    print("http2" + str(HTTP2_FLAG))

    return HTTP1_FLAG, HTTP2_FLAG    
    



if __name__ == "__main__":
    SERVER_PORT = 80
    # Start the server with the request handler function
    start_tcp_server(SERVER_PORT, request_handler)
        