import socket
import ssl
import h2.connection
import h2.events

# Server Configuration
HOST = '127.0.0.1'
PORT = 8080

# Create an SSL context that doesn't verify certificates
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
context.set_alpn_protocols(['h2', 'http/1.1'])

# Create a connection
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
secure_socket = context.wrap_socket(client_socket, server_hostname=HOST)

# Connect to the server
secure_socket.connect((HOST, PORT))

# Initialize the H2 connection
connection = h2.connection.H2Connection()
connection.initiate_connection()

# Send the HTTP/2 request
stream_id = connection.get_next_available_stream_id()
headers = [
    (':method', 'GET'),
    (':scheme', 'https'),
    (':authority', f'{HOST}:{PORT}'),
    (':path', '/')
]

# Send the headers
secure_socket.send(connection.data_to_send())

# Send the HTTP/2 frame with the request headers
connection.send_headers(stream_id, headers)

# Receive the response
data = secure_socket.recv(1024)

# Process the response
while data:
    events = connection.receive_data(data)
    for event in events:
        if isinstance(event, h2.events.Response):
            print(f"Response Headers: {event.headers}")
        elif isinstance(event, h2.events.Data):
            print(f"Response Data: {event.data.decode()}")
    data = secure_socket.recv(1024)

# Close the connection
secure_socket.close()
