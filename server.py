import socket
import threading
import time
import signal
import sys
import hashlib
# {'roomname': {'token': last_active_time}}
# if room owner : token = client port number
# if joiner : token = hash(room_name) % 65535
chatrooms = {}
# Store owner information: {'roomname': owner_token}
room_owners = {}

# Global socket variables for cleanup
sock_tcp = None
sock = None

def cleanup_resources():
    """Clean up all resources before server shutdown"""
    print("\nCleaning up resources...")
    
    # Close TCP socket
    if sock_tcp:
        try:
            sock_tcp.close()
            print("TCP socket closed")
        except Exception as e:
            print(f"Error closing TCP socket: {e}")
    
    # Close UDP socket
    if sock:
        try:
            sock.close()
            print("UDP socket closed")
        except Exception as e:
            print(f"Error closing UDP socket: {e}")
    
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle Ctrl+C signal"""
    print("\nShutting down server...")
    cleanup_resources()

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def process_message(data):
    # data = usernamelen(1byte) + username + message + filler(0x00) = 4096bytes
    username_length = data[0]
    username = data[1:username_length + 1]
    message = data[username_length + 1:4096]
    return username, message

def display_message(data):
    # display message to user
    username, message = process_message(data)
    print(f'username: {username.decode()}')
    print(f'message: {message.decode()}')

def recv_client_message():
    # receive message from client
    # data = usernamelen(1byte) + username + message + filler(0x00) = 4096bytes
    data, address = sock.recvfrom(4096)
    return data, address

def send_message_to_clients(data, sender_token, room_name):
    if not is_valid_chatroom(room_name):
        return False
    
    current_time = time.time()
    inactive_tokens = []
    
    for token, last_active in list(chatrooms[room_name].items()):
        if token != sender_token:
            try:
                # Here we need to map token back to actual UDP address for sending
                # This might need to be handled differently depending on your requirements
                target_port = int(token)
                sock.sendto(data, ('0.0.0.0', target_port))
                print(f'Sent message to client with token {token}')
            except Exception as e:
                print(f'Error sending message to client with token {token}: {e}')
                inactive_tokens.append(token)
    
    for token in inactive_tokens:
        leave_chatroom(room_name, token)
    
    return True

def handle_client(data, address):
    try:
        # Display received message
        display_message(data)
        # Update last active time for the client
        chatrooms[room_name][address] = time.time()
        # Broadcast message to other clients
        send_message_to_clients(data, address, room_name)
    except Exception as e:
        print(f'Error handling client {address}: {e}')
        if address in chatrooms[room_name]:
            del chatrooms[room_name][address]

def cleanup_clients():
    while True:
        print('Cleaning up inactive clients...')
        current_time = time.time()
        inactive_threshold = 180

        for room_name, clients in list(chatrooms.items()):
            inactive_clients = []
            for client, last_active in list(clients.items()):
                if current_time - last_active > inactive_threshold:
                    inactive_clients.append(client)
            
            for client in inactive_clients:
                leave_chatroom(room_name, client)

        time.sleep(60)

def is_valid_chatroom(room_name):
    """Check if chatroom exists and owner is still active"""
    if room_name not in chatrooms or room_name not in room_owners:
        return False
    owner_token = room_owners[room_name]
    return owner_token in chatrooms[room_name]

def validate_client_token(room_name, token):
    """Check if client has valid token for the room"""
    if not is_valid_chatroom(room_name):
        return False
    # Token should match a valid token in the chatroom
    return token in chatrooms[room_name]

def create_chatroom(room_name, owner_address):
    if room_name not in chatrooms:
        chatrooms[room_name] = {}
        # Generate owner's token from their port number
        owner_token = str(owner_address[1])
        room_owners[room_name] = owner_token
        # Add owner to chatroom with their token
        chatrooms[room_name][owner_token] = time.time()
        print(f'Chatroom {room_name} created with owner token {owner_token}')
    else:
        print(f'Chatroom {room_name} already exists')

def join_chatroom(room_name, client_address, token):
    if not is_valid_chatroom(room_name):
        print(f'Chatroom {room_name} is not valid')
        return False
    # Add client to chatroom with their token
    chatrooms[room_name][token] = time.time()
    print(f'Client with token {token} joined chatroom {room_name}')
    return True

def leave_chatroom(room_name, token):
    if room_name in chatrooms and token in chatrooms[room_name]:
        del chatrooms[room_name][token]
        print(f'Client with token {token} left chatroom {room_name}')
        
        # If owner leaves, delete the chatroom
        if token == room_owners.get(room_name):
            del chatrooms[room_name]
            del room_owners[room_name]
            print(f'Room {room_name} deleted as owner left')
        # If room becomes empty, delete it
        elif not chatrooms[room_name]:
            del chatrooms[room_name]
            del room_owners[room_name]
            print(f'Room {room_name} deleted as it became empty')
    else:
        print(f'Client with token {token} not in chatroom {room_name}')

def process_udp_packet(data):
    """Process UDP packet with new format"""
    # Header
    room_name_size = data[0]
    token_size = data[1]
    
    # Body
    room_name = data[2:2 + room_name_size]
    token = data[2 + room_name_size:2 + room_name_size + token_size]
    message = data[2 + room_name_size + token_size:4096]
    print(f'room_name: {room_name.decode()}, token: {token.decode()}, message: {message.decode()}')
    
    return room_name.decode(), token.decode(), message.decode()

def build_udp_packet(room_name, token, message):
    print(f'room_name: {room_name}, token: {token}, message: {message}')
    packet = bytearray(4096)
    packet[0] = len(room_name)
    packet[1] = len(token)
    packet[2: 2+len(room_name)] = room_name.encode()
    packet[2+len(room_name): 2+len(room_name)+len(token)] = token.encode()
    packet[2+len(room_name)+len(token): 2+len(room_name)+len(token)+len(message)] = message.encode()
    return packet

def handle_udp_message(data, address):
    try:
        room_name, token, message = process_udp_packet(data)
        print(f'room_name: {room_name}, token: {token}, message: {message}')
        print(f'chatrooms: {chatrooms[room_name]}')
        for stored_token in chatrooms[room_name]:
            print(f'stored token: {stored_token}')
            
        if not validate_client_token(room_name, token):
            error_packet = build_error_packet("Invalid room or token")
            sock.sendto(error_packet, address)
            return
        
        # Update client activity using their token
        chatrooms[room_name][token] = time.time()
        
        # Broadcast message to other clients
        send_message = build_udp_packet(room_name, token, message)
        if not send_message_to_clients(send_message, token, room_name):
            error_packet = build_error_packet("Room is no longer valid")
            sock.sendto(error_packet, address)
            
    except Exception as e:
        print(f'Error handling UDP message: {e}')
        error_packet = build_error_packet(str(e))
        sock.sendto(error_packet, address)

"""
# TCP for chatroom management
## tcp packet format:
Header | RoomNameSize(1byte) + Operation(1byte) + State(1byte) + OperationPayloadSize(29byte)
Body | RoomName(RoomNameSize) + OperationPayload(29byte)

Operation:
0: request to create chatroom or join chatroom (client send server roomname and username)
1: server respond to request containing status code
2: server respond to request containing unique token that is assigned client name 
that recognize client as the owner of the chatroom

State = status code:
0: Success
1: Failed

OperationPayload:
if operation == 0:
    RoomName = room name
    OperationPayload =  username
if operation == 1:
    RoomNameSize = 0
    State = status code
    OperationPayload = status message
if operation == 2:
    State = status code
    RoomName = room name
    OperationPayload = unique token
"""
def build_tcp_packet(operation, state, room_name, operation_payload):
    try:
        # Check size limits
        if len(room_name) > 255:
            return build_error_packet("Room name exceeds maximum size of 255 bytes")
        if len(operation_payload) > (2**29 - 1):
            return build_error_packet("Operation payload exceeds maximum size of 2^29 - 1 bytes")

        # Ensure inputs are bytes
        room_name_bytes = room_name.encode() if isinstance(room_name, str) else room_name
        operation_payload_bytes = operation_payload.encode() if isinstance(operation_payload, str) else operation_payload

        packet = bytearray(4096) 
        # Header(32bytes)
        packet[0] = len(room_name_bytes)  # RoomNameSize(1byte)
        packet[1] = operation  # Operation(1byte)
        packet[2] = state  # State(1byte)
        # Convert operation_payload_size to 29 bytes
        packet[3:32] = len(operation_payload_bytes).to_bytes(29, byteorder='big')
        # Body(RoomNameSize + OperationPayload)
        packet[32:32 + len(room_name_bytes)] = room_name_bytes  # RoomName(RoomNameSize bytes, max 255byte)
        packet[32 + len(room_name_bytes):32 + len(room_name_bytes) + len(operation_payload_bytes)] = operation_payload_bytes  # OperationPayload(max 2^29 - 1 bytes)

        return packet
    except Exception as e:
        return build_error_packet(str(e))

def build_error_packet(error_message):
    """Build a packet with operation=1 (error response) and state=1 (failed)"""
    # Ensure error_message is bytes
    error_message_bytes = error_message.encode() if isinstance(error_message, str) else error_message
    
    packet = bytearray(4096)
    # Header(32bytes)
    packet[0] = 0  # RoomNameSize = 0 for error messages
    packet[1] = 1  # Operation = 1 (error response)
    packet[2] = 1  # State = 1 (failed)
    # Convert error_message_size to 29 bytes
    packet[3:32] = len(error_message_bytes).to_bytes(29, byteorder='big')
    # Body (only OperationPayload)
    packet[32:32 + len(error_message_bytes)] = error_message_bytes
    return packet

"""
## Control flow
- start tcp connection
- client send roomname and username to server
- server send operation 1, status code 0 to client and success message
- create chatroom or join chatroom:
    - server check if roomname is in chatroom:
        - if roomname is not in chatroom, create chatroom
        - else if roomname is in chatroom, join chatroom
    - if create chatroom:
        - server create chatroom and assign unique token to client
        - if success:
            - server send operation 2, status code 0 to client and unique token
        - else if failed:
            - server send operation 1, status code 1 to client and error message
    - if join chatroom:
        - chatroom[roomname].append(client_address)
        - if success:
            - server send operation 2, status code 0 to client and unique token
        - else if failed:
            - server send operation 1, status code 1 to client and error message
-close tcp connection
"""
def assign_token(room_name, client_address, is_owner):
    """ Assign a token to the client 
    Args:
        room_name: room name
        client_address: (ip, port) tuple
        is_owner: True if client is room owner
    Returns:
        token: string representation of port number
    """
    if is_owner:
        # For owner, use their port as token
        token = str(client_address[1])  # Convert port number to string
    else:
        # For joiners, use room name's hash as port
        token = str(hash(room_name) % 65535)  # Use modulo to ensure valid port range
    return token

def accept_tcp_connections():
    while True:
        conn, addr = sock_tcp.accept()
        print(f'Client {addr} connected')
        thread = threading.Thread(target=handle_tcp_connection, args=(conn, addr))
        thread.start()

def handle_tcp_connection(conn, addr):
    while True:
        data = conn.recv(4096)
        if not data:
            break

        try:
            # decode data
            room_name_size = data[0]
            operation = data[1]
            state = data[2]
            operation_payload_size = int.from_bytes(data[3:32], byteorder='big')
            
            # Extract room name and operation payload
            room_name = data[32:32 + room_name_size]
            operation_payload = data[32 + room_name_size:32 + room_name_size + operation_payload_size]
            
            # Convert to strings for processing
            room_name_str = room_name.decode()
            operation_payload_str = operation_payload.decode()
            
            print(f'Operation: {operation}, State: {state}, Room Name: {room_name_str}, Operation Payload: {operation_payload_str}')
            
            # Send initial success response
            conn.sendall(build_tcp_packet(1, 0, room_name_str, "Success"))
            
            # Handle operation
            if operation == 0:  # client request to create or join chatroom
                if room_name_str not in chatrooms:
                    # Create chatroom
                    create_chatroom(room_name_str, addr)
                    # Send token response
                    token = assign_token(room_name_str, addr, True)
                    print(f"Assigned token for owner: {token}")
                    conn.sendall(build_tcp_packet(2, 0, room_name_str, token))
                else:
                    # Join chatroom
                    token = assign_token(room_name_str, addr, False)
                    print(f"Assigned token for joiner: {token}")
                    if join_chatroom(room_name_str, addr, token):
                        # Send token response
                        conn.sendall(build_tcp_packet(2, 0, room_name_str, token))
                    else:
                        # Send error response
                        conn.sendall(build_error_packet("Failed to join chatroom"))
            else:
                conn.sendall(build_error_packet("Invalid operation"))
                
        except Exception as e:
            error_msg = f"Error handling client message: {str(e)}"
            print(error_msg)
            conn.sendall(build_error_packet(error_msg))
            break

"""
# UDP for chat
## 
- chatroom is valid if the owner is in the chatroom
  if the owner is not in the chatroom, a chatroom will be deleted
- client can join the chatroom if client has the unique token that is equal to client's address
- if client(joiner) delete the chatroom, token will be deleted
- packet format:
    - header:
        - RoomNameSize(1byte)
        - TokenSize(1byte)
    - body:
        - RoomName(RoomNameSize)
        - Token(TokenSize)
        - Message(4096 - RoomNameSize - TokenSize)
- control flow:
    - tcp connection is closed -> start udp connection
    - client send packet to server
    - server check if the chatroom is valid and the client has the valid token in the chatroom
    - if the chatroom is valid, server send packet to all clients in the chatroom
    - if the chatroom is not valid, server send error packet to client

"""

if __name__ == '__main__':
    try:
        # Create a TCP socket for the server that will make chatroom and accept clients
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Define tcp server address and port
        tcp_server_address = '0.0.0.0'
        tcp_server_port = 9000  # TCP port for chatroom management

        # Set socket options to allow reuse of address
        sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind socket to address and port
        sock_tcp.bind((tcp_server_address, tcp_server_port))
        sock_tcp.listen(5)
        print(f'Server listening on {tcp_server_address}:{tcp_server_port}')
        # Accept incoming connections subthread
        tcp_thread = threading.Thread(target=accept_tcp_connections, daemon=True)
        tcp_thread.start()

        # Create a UDP socket for chat messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Define UDP server address and port
        udp_server_address = '0.0.0.0'
        udp_server_port = 9001  # UDP port for chat messages

        # Set socket options to allow reuse of address
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind socket to address and port
        sock.bind((udp_server_address, udp_server_port))
        print(f'UDP server listening on {udp_server_address}:{udp_server_port}')

        # Start thread to clean up inactive clients
        cleanup_thread = threading.Thread(target=cleanup_clients, daemon=True)
        cleanup_thread.start()

        while True:
            try:
                # Receive message from client
                data, address = sock.recvfrom(4096)
                # Handle client message in a new thread
                thread = threading.Thread(target=handle_udp_message, args=(data, address))
                thread.start()
            except Exception as e:
                print(f'Server error: {e}')
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    finally:
        cleanup_resources()