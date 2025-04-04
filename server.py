import socket
import threading

clients = []

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

def send_message_to_clients(data, sender_address):
    for client in clients:
        if client != sender_address:
            try:
                sock.sendto(data, client)
                print(f'Sent message to {client}')
            except Exception as e:
                print(f'Error sending message to {client}: {e}')
                clients.remove(client)
        
def handle_client(data, address):
    try:
        # Display received message
        display_message(data)
        # Broadcast message to other clients
        send_message_to_clients(data, address)
    except Exception as e:
        print(f'Error handling client {address}: {e}')
        if address in clients:
            clients.remove(address)

if __name__ == '__main__':
    # USE AF_INET for IPv4 and SOCK_DGRAM for UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = '0.0.0.0'
    server_port = 9001
    print(f'starting up on {server_address} port {server_port}')

    # Bind socket to address and port
    sock.bind((server_address, server_port))
    print('\nwaiting to receive message')

    while True:
        try:
            # Receive message from client
            data, address = sock.recvfrom(4096)
            # Register new client if not already connected
            if address not in clients:
                clients.append(address)
                print(f'Client {address} connected')
            
            # Handle client message in a new thread
            thread = threading.Thread(target=handle_client, args=(data, address))
            thread.start()
        except Exception as e:
            print(f'Server error: {e}')