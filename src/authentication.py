import csv
import urllib.parse

def login(username, password):
    
    with open('data/users.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                return True
    return False
    
def handle_login(connection_socket, body):
    
    parsed_data = urllib.parse.parse_qs(body)
    
    # Convert lists to single values (since parse_qs returns lists of values)
    parsed_data = {key: value[0] for key, value in parsed_data.items()}
    
    # Extract username and password
    username = parsed_data.get('username')
    password = parsed_data.get('password')
    print(f"Login attempt with username: {username} and password: {password}")
    
    # Here, you can validate the credentials
    if login(username, password):
        response = """HTTP/1.1 302 Found\r\nLocation: /pages/welcome.html\r\n\r\n"""
    else:
        response = """HTTP/1.1 401 Unauthorized\r\nContent-Type: text/html\r\n\r\nWrong username or password"""
    
    connection_socket.send(response.encode())    