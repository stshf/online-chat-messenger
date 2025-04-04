import socket
import threading


server_address = '0.0.0.0'
server_port = 9001

address = ''
port = 0 # auto assign port

SPACE = '     '

def process_message(data):
    # data = usernamelen(1byte) + username + message + filler(0x00) = 4096bytes
    username_length = data[0]
    username = data[1:username_length + 1]
    message = data[username_length + 1:4096]
    return username, message

def display_recv_message(data):
    # display message to user
    username, message = process_message(data)
    print(f'\n{SPACE}username: {username.decode()}')
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

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # empty string means 0.0.0.0
    sock.bind((address, port))

    # user input username
    username = input('Enter your username: ')
    username_length = len(username)
    if username_length > 255:
        print('Username Length exceeds 255 bytes')
        exit(1)


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

            # Prepare message: usernamelen(1byte) + username + message + filler(0x00) = 4096bytes
            send_message = bytes([username_length]) + username.encode() + message.encode() + b'\x00' * (4096 - username_length - message_length)
            # send message to server
            sock.sendto(send_message, (server_address, server_port))
            print('Send message to server')
    except KeyboardInterrupt:
        print('\nExiting...')
    finally:
        sock.close()