import socket
import sys
import json

# Create a IP socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Connect to the server
server_address = ('tmp/socket_file')
print('Connecting to {}'.format(server_address))
try:
    sock.connect(server_address)
except socket.error as msg:
    print(msg)
    sys.exit(1)

try:
    # Send data
    message = {
        "method": "subtract", 
        "params": [42, 23], 
        "param_types": ["int", "int"],
        "id": 1
    }
    json_message = json.dumps(message)
    print('Sending {}'.format(json_message))
    sock.sendall(json_message.encode())

    # It's time to receive
    sock.settimeout(2)
    responce = b''
    try:
        # Look for the response
        while True:
            # Receive data from the server 
            data = sock.recv(32)
            data_str = data.decode('utf-8')

            # If data is received, print it
            if data:
                responce += data
            else:
                print('No more data from {}'.format(server_address))
                break
        responce_json = responce.decode('utf-8')
        print('Received {}'.format(responce_json))
        responce_dict = json.loads(responce_json)
        print('Received {}'.format(responce_dict))
    # if the server does not respond within 2 seconds, a TimeoutError will be raised
    except(TimeoutError):
        print('Timeout error')
# Close the socket
finally:
    print('Closing socket')
    sock.close()
