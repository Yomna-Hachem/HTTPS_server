from Frame import Frame
from HPACK.myHpack import HPACK
from hpack import Encoder
from hpack import Decoder
from frame_handler import handle_frame, sendAcknowledgement

encoder = Encoder()
decoder = Decoder()

        
def handle_http2_requests(connection_socket):
    try:
        while True:  # Keep the connection open to process multiple frames
            raw_data = connection_socket.recv(1024)
            print("raw data: " + str(raw_data))
            print()
            if not raw_data:  # Client closed the connection
                print("Client closed the connection")
                break

            #print("raw data: " + str(raw_data))
            frames = process_multiple_frames(raw_data)

            for frame in frames:
                print(frame)
                handle_frame(connection_socket, frame)

            # Respond to SETTINGS frame and send initial page only once
            if not hasattr(handle_http2_requests, "settings_ack_sent"):
                sendAcknowledgement(connection_socket)
                handle_http2_requests.settings_ack_sent = True  # Mark as sent
    except Exception as e:
        print(f"Error handling HTTP/2 requests: {e}")
    finally:
        connection_socket.close()

def process_multiple_frames(raw_data):
    frames = []
    while raw_data:
        try:
            frame = Frame(raw_data)
            frame.parse()  # Parse the current frame
            frames.append(frame)  # Add the frame to the list

            # Slice the raw_data to remove the processed frame
            raw_data = raw_data[9 + frame.length:]  # 9 bytes for the header + frame length
        except ValueError as e:
            print(f"Error processing frame: {e}")
            break
    return frames







