from HPACK.myHpack import HPACK
import os
from authentication import handle_login
import json
from urllib.parse import parse_qs
from request import Request
from hpack import Encoder
from hpack import Decoder

encoder = Encoder()
decoder = Decoder()

def handle_get(connection_socket, requested_file, stream_id):
    print(f"Handling GET request for {requested_file}")     
         
    # Default to "index.html" if root is requested
    if requested_file == "/":
        requested_file = "/pages/index.html"
        
    file_extension = os.path.splitext(requested_file)[1].lower()
    print("file extention: " + str(file_extension))
    directory = str()
    if file_extension in ['.html', '.htm']:
        directory = "/pages"  
    elif file_extension in ['.jpg', '.jpeg']:
        directory = "/images"  
    elif file_extension == '.txt':
        directory = "/texts"  

    # Construct the full file path based on the directory
    file_path = "." + directory + requested_file    

    # Construct the full file path
    file_path = "." + requested_file  # Assuming the server runs in the directory containing index.html
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        if file_extension in ['.jpg', '.jpeg']:
            with open(file_path, "rb") as file:
                file_content = file.read()
            response_header = {
                ":status", "200",  # Status: 200 OK
                "content-type", "image/jpeg",
            }
        else:
            with open(file_path, "r") as file:
                file_content = file.read()
            response_header = {
                ":status": "200",
                "content-type": "text/html",
                "content-length": "1024",
            }
    else:
        response_header = {    
                ":status", "404",  # Status: 404 Not Found
                "content-type", "text/plain",  # Content-Type: text/plain}
        }
        
        
    print("Response header before encoding:")
    for key, value in response_header.items():
        print(f"{key}: {value}")
    encoded_header = encoder.encode(response_header)
    print("respons header after encoding: " + str(encoded_header))
    
    # Calculate the length of the encoded header and convert it to 3 bytes
    header_length = len(encoded_header) 

    header_frame = (     
        header_length.to_bytes(3, byteorder='big') +  # Length 
        b'\x01' +       # Type: HEADERS
        b'\x04' +       # Flags: END_HEADERS
        stream_id.to_bytes(4, byteorder='big') +  # Stream ID 
        encoded_header  # Headers
    )

    # Data frame
    data_payload = file_content.encode('utf-8') 
    data_frame = (
        len(data_payload).to_bytes(3, byteorder='big') + # Length
        b'\x00' +       # Type: DATA
        b'\x00' +       # Flags: END_STREAM
        stream_id.to_bytes(4, byteorder='big') +  # Stream ID (from received frame)
        data_payload  # Data
    )

    connection_socket.send(header_frame + data_frame)
  

DATA_FILE = "data/post_data.json"  # File to save POST data

def handle_post(connection_socket, body):
    print("Handling POST request")
    response = ""
    try:
        # Parse the body assuming URL-encoded form data
        parsed_body = parse_qs(body)

        if 'username' in body and 'password' in body:
            # Delegate to handle_login for authentication
            handle_login(connection_socket, body)
            return

        # Handle other POST-related logic
        if parsed_body:
            with open(DATA_FILE, "w") as file:
                json.dump(parsed_body, file)

            response_body = "POST request received and saved. Data:\n"
            for key, value in parsed_body.items():
                response_body += f"{key}: {', '.join(value)}\n"

            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n\r\n{response_body}"
            )
        else:
            raise ValueError("No valid data in POST request body.")

    except Exception as e:
        print(f"Error processing POST request: {e}")
        response = """HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid Form Submission"""

    finally:
        connection_socket.send(response.encode())

def handle_delete(connection_socket, requested_file):
    print(f"Handling DELETE request for {requested_file}")

    # Strip leading slashes and clean the resource name
    resource_name = requested_file.replace("/delete_resource/", "")

    # Define the base path where resources are stored
    base_path = "D:/project/project/images/"

    # Create the full path to the resource
    full_path = os.path.join(base_path, resource_name)
    full_path = full_path.replace("\\", "/") 
    # Check if the resource exists
    if os.path.exists(full_path):
        try:
            # Delete the resource (file) from the server
            os.remove(full_path)
            # Send a success response
            response = f"""HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nResource {resource_name} deleted successfully."""
        except Exception as e:
            # In case of an error while deleting the resource
            print(f"Error deleting resource {resource_name}: {e}")
            response = f"""HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nFailed to delete resource {resource_name}."""
    else:
        # Resource not found
        response = f"""HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nResource {resource_name} not found."""

    # Send the response back to the client
    connection_socket.send(response.encode())