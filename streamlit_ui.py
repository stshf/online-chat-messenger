import streamlit as st
import threading
from client import ChatClient, process_udp_message


st.set_page_config(page_title="Chat Messenger")

if "client" not in st.session_state:
    st.session_state.client = ChatClient()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "listening" not in st.session_state:
    st.session_state.listening = False

def listener():
    client = st.session_state.client
    while st.session_state.listening:
        try:
            data, _ = client.udp_sock.recvfrom(4096)
            room, token, msg = process_udp_message(data)
            st.session_state.messages.append(
                f"{room.decode()} - {msg.decode()}"
            )
            st.experimental_rerun()
        except Exception:
            break

def connect():
    username = st.session_state.username
    roomname = st.session_state.roomname
    try:
        client = st.session_state.client
        client.handshake(username, roomname)
        # Start UDP without the default background listener so Streamlit can
        # manage incoming messages itself.
        client.start_udp(start_listener=False)
        st.session_state.listening = True
        threading.Thread(target=listener, daemon=True).start()
    except Exception as e:
        st.error(str(e))

def send():
    message = st.session_state.message
    if message:
        try:
            st.session_state.client.send_message(message)
            st.session_state.message = ""
        except Exception as e:
            st.error(str(e))

st.title("Simple Chat")

if not st.session_state.listening:
    st.text_input("Username", key="username")
    st.text_input("Room", key="roomname")
    st.button("Connect", on_click=connect)
else:
    for m in st.session_state.messages:
        st.write(m)
    st.text_input("Message", key="message", on_change=send)
