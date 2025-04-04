import socket
import threading
import time

# clients = {'address': time.time()}
clients = {}

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
    current_time = time.time()
    inactive_clients = []
    for client, last_active in list(clients.items()):
        if client != sender_address:
            try:
                sock.sendto(data, client)
                print(f'Sent message to {client}')
            except Exception as e:
                print(f'Error sending message to {client}: {e}')
                inactive_clients.append(client)
    
    for client in inactive_clients:
        if client in clients:
            del clients[client]
            print(f'Client {client} removed due to send error')
        
def handle_client(data, address):
    try:
        # Display received message
        display_message(data)
        # Update last active time for the client
        clients[address] = time.time()
        # Broadcast message to other clients
        send_message_to_clients(data, address)
    except Exception as e:
        print(f'Error handling client {address}: {e}')
        if address in clients:
            clients.remove(address)

def cleanup_clients():
    while True:
        # Remove clients that have not sent a message in the last 500 seconds
        print('Cleaning up inactive clients...')
        current_time = time.time()
        inactive_threshold = 180

        inactive_clients = []
        for client, last_active in list(clients.items()):
            if current_time - last_active > inactive_threshold:
                inactive_clients.append(client)
        
        for client in inactive_clients:
            if client in clients:
                del clients[client]
                print(f'Client {client} removed due to inactivity')

        time.sleep(60)

if __name__ == '__main__':
    # USE AF_INET for IPv4 and SOCK_DGRAM for UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = '0.0.0.0'
    server_port = 9001
    print(f'starting up on {server_address} port {server_port}')

    # Bind socket to address and port
    sock.bind((server_address, server_port))
    print('\nwaiting to receive message')

    # Start thread to clean up inactive clients
    cleanup_thread = threading.Thread(target=cleanup_clients, daemon=True)
    cleanup_thread.start()

    while True:
        try:
            # Receive message from client
            data, address = sock.recvfrom(4096)
            # Register new client if not already connected or update activity time
            clients[address] = time.time()
            if address not in clients:
                print(f'Client {address} connected')
            
            # Handle client message in a new thread
            thread = threading.Thread(target=handle_client, args=(data, address))
            thread.start()
        except Exception as e:
            print(f'Server error: {e}')