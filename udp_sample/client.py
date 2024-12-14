import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '0.0.0.0'
server_port = 9001

address = ''
port = 9050
message = b'Message from client'

# empty string means 0.0.0.0
sock.bind((address, port))

try:
    print('sending {!r}'.format(message))
    # send message to server
    sent = sock.sendto(message, (server_address, server_port))
    print('Send {} bytes to server'.format(sent))

    # receive response from server
    print('waiting to receive')
    data, server = sock.recvfrom(4096)
    print('received {!r}'.format(data))
finally:
    print('closing socket')
    sock.close()