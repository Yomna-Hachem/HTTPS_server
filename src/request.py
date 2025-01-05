
class Request:
    def __init__(self, method=None, path=None, body=None):
        self.method = method
        self.path = path
        self.body = body
        
    def parse_HTTP1_request(self, connection_socket, raw_request):
        # Split the request into header and body
        header_body_split = raw_request.split("\r\n\r\n", 1)
        headers, self.body = (header_body_split[0], header_body_split[1] if len(header_body_split) > 1 else "")

        # First line: Request method, URL, and HTTP version
        request_line = headers.split("\r\n")[0]
        self.method, self.path, version = request_line.split(' ')

        # Parse headers
        headers_dict = {}
        for line in headers.split("\r\n")[1:]:  # Skip the request line
            if line.strip():
                key, value = line.split(": ", 1)
                headers_dict[key] = value

        # Extract content-length if present
        content_length = int(headers_dict.get("Content-Length", 0))
        
        # Handle incomplete body (if any)
        if len(body) < content_length:
            body += connection_socket.recv(content_length - len(body)).decode()    
        

                
            