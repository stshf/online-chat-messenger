"""Simple chat client implementation."""

from __future__ import annotations

import socket
import threading
from typing import Callable, Tuple


TCP_SERVER_ADDRESS = "0.0.0.0"
TCP_SERVER_PORT = 9000
UDP_SERVER_ADDRESS = "0.0.0.0"
UDP_SERVER_PORT = 9001

SPACE = "     "


def process_udp_message(data: bytes) -> Tuple[bytes, bytes, bytes]:
    """Extract room name, token and message from a UDP packet."""

    room_name_size = data[0]
    token_size = data[1]
    room_name = data[2 : 2 + room_name_size]
    token = data[2 + room_name_size : 2 + room_name_size + token_size]
    message = data[2 + room_name_size + token_size : 4096]
    return room_name, token, message


def display_recv_message(data: bytes) -> None:
    """Pretty print received UDP packet."""

    room_name, token, message = process_udp_message(data)
    print(f"\n{SPACE}room_name: {room_name.decode()}")
    print(f"{SPACE}token: {token.decode()}")
    print(f"{SPACE}message: {message.decode()}")


def recv_messages(sock: socket.socket, handler: Callable[[bytes], None]) -> None:
    """Receive UDP packets and handle them using a callback."""

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if not data:
                break
            handler(data)
        except ConnectionResetError:
            print("Server disconnected")
            break
        except Exception as exc:  # pragma: no cover - best effort logging
            print(f"Error receiving message: {exc}")
            break


def recv_and_display_message(sock: socket.socket) -> None:
    """Wrapper to display received UDP packets."""

    recv_messages(sock, display_recv_message)

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
def build_tcp_packet(operation: int, state: int, room_name: str, operation_payload: str) -> bytes:
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

def build_error_packet(error_message: str) -> bytes:
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
def build_udp_packet(room_name: str, token: str, message: str) -> bytes:
    packet = bytearray(4096)
    packet[0] = len(room_name)
    packet[1] = len(token)
    packet[2: 2+len(room_name)] = room_name.encode()
    packet[2+len(room_name): 2+len(room_name)+len(token)] = token.encode()
    packet[2+len(room_name)+len(token): 2+len(room_name)+len(token)+len(message)] = message.encode()
    return packet


class ChatClient:
    """Encapsulates client side logic for the messenger."""

    def __init__(
        self,
        tcp_addr: Tuple[str, int] = (TCP_SERVER_ADDRESS, TCP_SERVER_PORT),
        udp_addr: Tuple[str, int] = (UDP_SERVER_ADDRESS, UDP_SERVER_PORT),
    ) -> None:
        self.tcp_addr = tcp_addr
        self.udp_addr = udp_addr
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock: socket.socket | None = None
        self.username = ""
        self.roomname = ""
        self.token = ""

    def handshake(self, username: str, roomname: str) -> None:
        """Perform TCP handshake and store the received token."""

        self.username = username
        self.roomname = roomname

        self.tcp_sock.connect(self.tcp_addr)
        self.tcp_sock.sendall(build_tcp_packet(0, 0, roomname, username))

        response = self.tcp_sock.recv(4096)
        if response[0] == 0 and response[1] == 1:
            raise RuntimeError(f"Failed: {response[32:].decode()}")

        response = self.tcp_sock.recv(4096)
        roomname_size = response[0]
        operation_payload_size = int.from_bytes(response[3:32], byteorder="big")
        self.token = response[32 + roomname_size : 32 + roomname_size + operation_payload_size].decode()

    def start_udp(
        self, message_handler: Callable[[bytes], None] | None = None
    ) -> None:
        """Start UDP socket and receiving thread.

        Parameters
        ----------
        message_handler:
            Optional callback executed for every received UDP packet.
            If omitted, messages are printed to stdout.
        """

        try:
            udp_port = int(self.token)
        except ValueError as exc:  # pragma: no cover
            raise RuntimeError("Invalid token format") from exc

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("", udp_port))

        handler = message_handler if message_handler else display_recv_message
        thread = threading.Thread(
            target=recv_messages,
            args=(self.udp_sock, handler),
            daemon=True,
        )
        thread.start()

    def send_message(self, message: str) -> None:
        if not self.udp_sock:
            raise RuntimeError("UDP socket not started")
        payload = build_udp_packet(self.roomname, self.token, message)
        self.udp_sock.sendto(payload, self.udp_addr)

    def close(self) -> None:
        if self.udp_sock:
            self.udp_sock.close()
        self.tcp_sock.close()


def main() -> None:
    client = ChatClient()

    username = input("Enter your username: ")
    if len(username) > 255:
        raise ValueError("Username length exceeds 255 bytes")

    roomname = input("Enter the room name: ")
    if len(roomname) > 255:
        raise ValueError("Room name exceeds maximum size of 255 bytes")

    client.handshake(username, roomname)
    print(f"Unique token: {client.token}")
    client.start_udp()

    try:
        while True:
            message = input("Enter your message: ")
            if len(message) > 4096 - len(username):
                print("Message Length exceeds 4096 bytes")
                continue
            client.send_message(message)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        client.close()


if __name__ == "__main__":
    main()
