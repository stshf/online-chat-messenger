import socket
import threading

# TCP server address and port
tcp_server_address = '0.0.0.0'
tcp_server_port = 9000  # TCP port for chatroom management

# UDP server address and port
udp_server_address = '0.0.0.0'
udp_server_port = 9001  # UDP port for chat messages

address = ''
port = 0 # auto assign port

SPACE = '     '

def process_udp_message(data):
    room_name_size = data[0]
    token_size = data[1]
    room_name = data[2:2 + room_name_size]
    token = data[2 + room_name_size:2 + room_name_size + token_size]
    message = data[2 + room_name_size + token_size:4096]
    return room_name, token, message

def display_recv_message(data):
    # display message to user
    room_name, token, message = process_udp_message(data)
    print(f'\n{SPACE}room_name: {room_name.decode()}')
    print(f'{SPACE}token: {token.decode()}')
    print(f'{SPACE}message: {message.decode()}')

def recv_and_display_message():
    while True:
        try:
            data, server = sock.recvfrom(4096)
            if data == b'':
                break
            display_recv_message(data)
        except ConnectionResetError:
            print('Server disconnected')
            break
        except Exception as e:
            print(f'Error receiving message: {e}')
            break

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
    OperationPayload = username
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

        packet = bytearray(4096) 
        # Header(32bytes)
        packet[0] = len(room_name) # RoomNameSize(1byte)
        packet[1] = operation # Operation(1byte)
        packet[2] = state # State(1byte)
        packet[3:32] = len(operation_payload).to_bytes(29, byteorder='big') # OperationPayloadSize(29byte)
        # Body(RoomNameSize + OperationPayload)
        packet[32:32 + len(room_name)] = room_name.encode() # RoomName(RoomNameSize bytes, max 255byte)
        packet[32 + len(room_name):32 + len(room_name) + len(operation_payload)] = operation_payload.encode() # OperationPayload(max 2^29 - 1 bytes)

        return packet
    except Exception as e:
        return build_error_packet(str(e))

def build_error_packet(error_message):
    """Build a packet with operation=1 (error response) and state=1 (failed)"""
    packet = bytearray(4096)
    # Header(32bytes)
    packet[0] = 0  # RoomNameSize = 0 for error messages
    packet[1] = 1  # Operation = 1 (error response)
    packet[2] = 1  # State = 1 (failed)
    packet[3:32] = len(error_message.encode())  # OperationPayloadSize
    # Body (only OperationPayload)
    packet[32:32 + len(error_message.encode())] = error_message.encode()
    return packet

"""
# UDP for chat
- packet format:
    - header:
        - RoomNameSize(1byte)
        - TokenSize(1byte)
    - body:
        - RoomName(RoomNameSize)
        - Token(TokenSize)
        - Message(4096 - RoomNameSize - TokenSize)
"""
def build_udp_packet(room_name, token, message):
    packet = bytearray(4096)
    packet[0] = len(room_name)
    packet[1] = len(token)
    packet[2: 2+len(room_name)] = room_name.encode()
    packet[2+len(room_name): 2+len(room_name)+len(token)] = token.encode()
    packet[2+len(room_name)+len(token): 2+len(room_name)+len(token)+len(message)] = message.encode()
    return packet

if __name__ == '__main__':
    # tcp connection
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock_tcp.connect((tcp_server_address, tcp_server_port))
    except ConnectionRefusedError:
        print(f'Failed to connect to server at {tcp_server_address}:{tcp_server_port}')
        print('Please ensure the server is running and the port is correct')
        exit(1)

    # user input username
    username = input('Enter your username: ')
    username_length = len(username)
    if username_length > 255:
        print('Username Length exceeds 255 bytes')
        exit(1)

    # user input roomname
    roomname = input('Enter the room name: ')
    roomname_length = len(roomname)
    if roomname_length > 255:
        print('Room name exceeds maximum size of 255 bytes')
        exit(1) 

    # Operation:
    # 0: request to create chatroom or join chatroom (client send server roomname and username)
    # 1: server respond to request containing status code
    # 2: server respond to request containing unique token that is assigned client name 
    # 0: send request
    sock_tcp.sendall(build_tcp_packet(0, 0, roomname, username))
    # 1: receive response
    response = sock_tcp.recv(4096)
    if response[0] == 0 and response[1] == 1: # failed
        print(f'Failed : {response[32:].decode()}')
        exit(1)
    #2: receive unique token
    response = sock_tcp.recv(4096)
    # decode unique token
    roomname_size = response[0]
    operation = response[1]
    state = response[2]
    operation_payload_size = int.from_bytes(response[3:32], byteorder='big')
    room_name = response[32:32 + roomname_size]
    unique_token = response[32 + roomname_size:32 + roomname_size + operation_payload_size].decode() # e.g) b'27448'
    print(f'Unique token: {unique_token}')
    if operation == 2 and state == 1:
        print(f'Failed: {room_name.decode()}')
        exit(1)

    # udp connection use unique token as port
    try:
        udp_port = int(unique_token)  # Convert token to integer
    except ValueError:
        print('Error: Invalid token format')
        exit(1)
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # empty string means 0.0.0.0
    sock.bind((address, udp_port))

    # Start thread to receive messages from server
    thread = threading.Thread(target=recv_and_display_message, daemon=True)
    thread.start()

    try:
        while True:
            message = input('Enter your message: ')
            message_length = len(message)
            if message_length > 4096 - username_length:
                print('Message Length exceeds 4096 bytes')
                exit(1)


            print(f'roomname: {roomname}, unique_token: {unique_token}, message: {message}')
            send_message = build_udp_packet(roomname, unique_token, message)
            # send message to server
            sock.sendto(send_message, (udp_server_address, udp_server_port))
            print('Send message to server')
    except KeyboardInterrupt:
        print('\nExiting...')
    finally:
        sock.close()