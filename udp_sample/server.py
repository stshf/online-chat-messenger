import socket

# USE AF_INET for IPv4 and SOCK_DGRAM for UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '0.0.0.0'
server_port = 9001
print('starting up on {} port {}'.format(server_address, server_port))

# socket.bind takes a tuple of (address, port)
sock.bind((server_address, server_port))

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)

    print('received {} bytes from {}'.format(len(data), address))
    print(data)

    if data:
        sent = sock.sendto(data, address)
        print('sent {} bytes back to {}'.format(sent, address))
