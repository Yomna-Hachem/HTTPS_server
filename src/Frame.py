import struct

# Define the HTTP/2 preface
HTTP2_PREFACE = b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'

FRAME_TYPES = {
    0x0: "DATA",
    0x1: "HEADERS",
    0x2: "PRIORITY",
    0x3: "RST_STREAM",
    0x4: "SETTINGS",
    0x5: "PING",
    0x6: "GOAWAY",
    0x7: "WINDOW_UPDATE",
    0x8: "CONTINUATION"
}
class Frame:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.length = None
        self.frame_type = None
        self.flags = None
        self.stream_id = None
        self.payload = None

    def parse(self):
        """Parse the HTTP/2 frame, verify preface and remove it, then extract frame data."""
        # Check for the preface
        if self.raw_data.startswith(HTTP2_PREFACE):
            print("HTTP/2 preface found and verified.")
            # Remove the preface from the raw data
            self.raw_data = self.raw_data[len(HTTP2_PREFACE):]
        else:
            print("No valid HTTP/2 preface found.")

        # Ensure there is enough data left for a valid frame (at least 9 bytes)
        if len(self.raw_data) < 9:
            raise ValueError("Frame data is too short to be valid.")
        

        self.length = struct.unpack('>I', b'\x00' + self.raw_data[:3])[0]
        self.frame_type = self.raw_data[3]
        self.flags = self.raw_data[4]
        self.stream_id = struct.unpack('>I', self.raw_data[5:9])[0] & 0x7FFFFFFF  # Mask the high bit
        self.payload = self.raw_data[9:9 + self.length]

    def __repr__(self):
        return (f"Frame(length={self.length}, "
                f"type={self.frame_type}, "
                f"flags={self.flags}, "
                f"stream_id={self.stream_id}, "
                f"payload={self.payload})")


