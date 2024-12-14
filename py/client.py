import socket
import sys
import json
import os

# Create a socket
def createSocket():
    return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# connect to the server
def connectToServer(sock, server_address):
    print('Connecting to {}'.format(server_address))
    try:
        sock.connect(server_address)
    except socket.error as msg:
        print(msg)
        sys.exit(1)

def load_json(file_path):
    with open(file_path) as json_file:
        text = json.load(json_file)
        return json.dumps(text)


def sendJsonToServer(sock, json_message):
    print('Sending {}'.format(json_message))
    sock.sendall(json_message.encode())

def receiveJsonFromServer(sock):
    # It's time to receive
    sock.settimeout(2)
    responce = b''
    try:
        # Look for the response
        while True:
            # Receive data from the server 
            data = sock.recv(32)
            data_str = data.decode('utf-8')

            # If data is received, responce will be updated
            if data:
                responce += data
            else:
                break
        return responce
    # if the server does not respond within 2 seconds, a TimeoutError will be raised
    except(TimeoutError):
        print('Timeout error')

def displayResponseJson(response):
    responce_json = response.decode('utf-8')
    responce_dict = json.loads(responce_json)
    print('Received {}'.format(responce_dict))

def main():

    # get test json file path list
    test_json_files = os.listdir('test')
    print('test json files: {}'.format(test_json_files))
    
    for file in test_json_files:
        print('test_json_file: {}'.format(file))

    sock = createSocket()

    server_address = ('tmp/socket_file')
    connectToServer(sock, server_address)

    try:
        # load json message
        json_message = load_json('test/subtruct.json')
        # Send data
        sendJsonToServer(sock, json_message)

        # Receive data
        response = receiveJsonFromServer(sock)

        # Display the response
        displayResponseJson(response)

    # Close the socket
    finally:
        print('Closing socket')
        sock.close()

if __name__ == '__main__':
    main()