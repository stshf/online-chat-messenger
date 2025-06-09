import streamlit as st
import threading
import queue
from client import ChatClient, process_udp_message


st.set_page_config(page_title="Chat Messenger")


def init_state() -> None:
    """Initialize required session state variables."""

    if "client" not in st.session_state:
        st.session_state["client"] = ChatClient()
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "listening" not in st.session_state:
        st.session_state["listening"] = False


init_state()

MESSAGE_QUEUE: queue.Queue[bytes] = queue.Queue()


def listener(client: ChatClient, stop_event: threading.Event) -> None:
    """Background thread to receive UDP packets."""

    while not stop_event.is_set():
        try:
            data, _ = client.udp_sock.recvfrom(4096)
        except Exception:
            break
        MESSAGE_QUEUE.put(data)
        # Trigger a UI refresh so new messages appear
        st.experimental_rerun()


def process_incoming() -> None:
    """Flush queued UDP messages into session state."""

    while not MESSAGE_QUEUE.empty():
        data = MESSAGE_QUEUE.get()
        room, _, msg = process_udp_message(data)
        st.session_state["messages"].append(
            f"{room.decode()} - {msg.decode()}"
        )

def connect():
    username = st.session_state.username
    roomname = st.session_state.roomname
    try:
        client = st.session_state["client"]
        client.handshake(username, roomname)
        # Start UDP without the default background listener so Streamlit can
        # manage incoming messages itself.
        client.start_udp(start_listener=False)
        st.session_state["listening"] = True
        stop_event = threading.Event()
        st.session_state["listener_stop_event"] = stop_event
        threading.Thread(target=listener, args=(client, stop_event), daemon=True).start()
    except Exception as e:
        st.error(str(e))
    process_incoming()

def send():
    message = st.session_state.message
    if message:
        try:
            st.session_state["client"].send_message(message)
            st.session_state.message = ""
        except Exception as e:
            st.error(str(e))

# Process any incoming messages from the background listener
process_incoming()

st.title("Simple Chat")

# Add a bit of simple styling so the chat looks nicer
st.markdown(
    """
    <style>
        .chat-box {
            display: flex;
            flex-direction: column;
            height: 400px;
            overflow-y: auto;
            padding: 1rem;
            border: 1px solid #CCC;
            border-radius: 4px;
            background-color: #F8F8F8;
        }
        .chat-msg {
            padding: 0.25rem 0.5rem;
            margin-bottom: 0.25rem;
            border-radius: 4px;
            background-color: #FFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            width: fit-content;
            max-width: 80%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state["listening"]:
    st.text_input("Username", key="username")
    st.text_input("Room", key="roomname")
    st.button("Connect", on_click=connect)
else:
    with st.container():
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state["messages"]:
            st.markdown(f'<div class="chat-msg">{m}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.text_input("Message", key="message", on_change=send)
