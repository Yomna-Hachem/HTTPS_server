from Frame import Frame
from HPACK.myHpack import HPACK
from authentication import handle_login
from urllib.parse import parse_qs
from request import Request
from hpack import Encoder
from hpack import Decoder
from http2_methods import handle_get
encoder = Encoder()
decoder = Decoder()

#SETTINGS
HTTP2_SETTINGS = {
0x1: "SETTINGS_HEADER_TABLE_SIZE",
0x2: "SETTINGS_ENABLE_PUSH",
0x3: "SETTINGS_MAX_CONCURRENT_STREAMS",
0x4: "SETTINGS_INITIAL_WINDOW_SIZE",
0x5: "SETTINGS_MAX_FRAME_SIZE",
0x6: "SETTINGS_MAX_HEADER_LIST_SIZE"
}

def handle_frame(connection_socket, frame):
    
    if frame.frame_type == 0x0:  # DATA
        print(f"Processing DATA frame: {frame.payload}")
        
    elif frame.frame_type == 0x1:  # HEADERS
        print("Processing HEADERS frame")
        try:
            header_block = extract_header_block(frame.payload, frame.flags)
            decoded_headers = decoder.decode(header_block)
            print(f"Decoded headers: {decoded_headers}")
            
            if not decoded_headers:
                print("No headers found, skipping request processing.")
                return  # Skip processing if headers are empty
            method = None
            path = None
            body = None
            for key, value in decoded_headers:
                if key == ":method" and method is None:
                    method = value
                elif key == ":path" and path is None:
                    path = value
                
            if method == "GET":
                handle_get(connection_socket, path, frame.stream_id)
            
            # Create the Request object only if method and path are set
            if method and path:
                request = Request(method, path, body)
                print(f"Method: {request.method}, Path: {request.path}, Body: {request.body}")
            else:
                print("Incomplete headers: method or path is missing.")
        
        except Exception as e:
            print(f"Error decoding headers: {e}")
        
        
    elif frame.frame_type == 0x4:  # SETTINGS
        print("Processing SETTINGS frame")
        sendAcknowledgement(connection_socket)
    elif frame.frame_type == 0x5:  # PING
        print("Processing PING frame")
        send_pong(connection_socket, frame.payload)
    elif frame.frame_type == 0x6:  # GOAWAY
        print("Processing GOAWAY frame")
        print(f"GOAWAY: Stream ID {frame.stream_id}, payload: {frame.payload}")
    else:
        print(f"Unknown frame type: {frame.frame_type}")

def extract_header_block(payload, flags):

    index = 0

    # Check for PADDED flag (bit 0x08)
    if flags & 0x08:  # PADDED
        pad_length = payload[index]
        index += 1
    else:
        pad_length = 0

    # Check for PRIORITY flag (bit 0x20)
    if flags & 0x20:  # PRIORITY
        index += 5  # Skip the priority fields (5 bytes)

    # Extract the HPACK-encoded header block
    header_block = payload[index:-pad_length if pad_length > 0 else None]

    return header_block

def decode_settings_frame(self, payload):
    """Decode a settings frame payload into a dictionary."""
    if len(payload) % 6 != 0:
        raise ValueError("Settings frame payload length must be a multiple of 6")
    
    settings = {}
    for i in range(0, len(payload), 6):
        identifier = int.from_bytes(payload[i:i+2], byteorder='big')
        value = int.from_bytes(payload[i+2:i+6], byteorder='big')
        
        if identifier in HTTP2_SETTINGS:
            settings[HTTP2_SETTINGS[identifier]] = value
        else:
            # Handle unknown settings gracefully
            settings[f"UNKNOWN_{identifier}"] = value
    return settings

def handle_settings(self, settings):
    """Validate and apply HTTP/2 settings."""
    for key, value in settings.items():
        if key == "SETTINGS_HEADER_TABLE_SIZE":
            if value < 4096:  # Example minimum value
                raise ValueError("Header table size too small")
            self.header_table_size = value
        
        elif key == "SETTINGS_ENABLE_PUSH":
            if value not in (0, 1):
                raise ValueError("SETTINGS_ENABLE_PUSH must be 0 or 1")
            self.enable_push = bool(value)
        
        elif key == "SETTINGS_INITIAL_WINDOW_SIZE":
            if value > 2**31 - 1:
                raise ValueError("Initial window size exceeds maximum value")
            self.initial_window_size = value
        
        elif key == "SETTINGS_MAX_FRAME_SIZE":
            if value < 16384 or value > 16777215:
                raise ValueError("Max frame size out of range")
            self.max_frame_size = value
        
        elif key == "SETTINGS_MAX_HEADER_LIST_SIZE":
            self.max_header_list_size = value
        
        else:
            # Handle unknown settings
            print(f"Unknown setting {key} with value {value}")


def send_settings_ack(self, connection):
    """Send an acknowledgment for the settings frame."""
    frame = self.create_settings_frame(flags=0x1)  # ACK flag set
    connection.send(frame)

def create_settings_frame(self, settings=None, flags=0x0):
    """Create a SETTINGS frame."""
    payload = b""
    if settings:
        for key, value in settings.items():
            identifier = next(k for k, v in HTTP2_SETTINGS.items() if v == key)
            payload += identifier.to_bytes(2, byteorder='big')
            payload += value.to_bytes(4, byteorder='big')
    frame = self.create_frame(frame_type=0x4, flags=flags, payload=payload)
    return frame    


def sendAcknowledgement(connection_socket):
    settings_ack = b'\x00\x00\x00'
    settings_ack += b'\x04'  # Type: SETTINGS
    settings_ack += b'\x01'  # Flags: ACK
    settings_ack += b'\x00\x00\x00\x00'  # Stream ID: 0
    print("Sending settings acknowledgement")
    connection_socket.sendall(settings_ack)

def send_pong(connection_socket, payload):
    pong_frame = (
        b'\x00\x00\x08' +  # Length: 8 bytes
        b'\x06' +  # Type: PING
        b'\x01' +  # Flags: ACK
        b'\x00\x00\x00\x00' +  # Stream ID: 0
        payload  # Same payload as the PING
    )
    print("Sending PONG frame")
    connection_socket.sendall(pong_frame)