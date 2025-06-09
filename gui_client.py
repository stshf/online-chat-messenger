import queue
import tkinter as tk
from tkinter import ttk, scrolledtext

from client import ChatClient, process_udp_message


class ChatUI:
    """Simple Tkinter based GUI for :class:`ChatClient`."""

    def __init__(self) -> None:
        self.client = ChatClient()
        self.root = tk.Tk()
        self.root.title("Chat Client")
        self.msg_queue: queue.Queue[bytes] = queue.Queue()
        self._connected = False
        self._build_widgets()

    def _build_widgets(self) -> None:
        connect = ttk.Frame(self.root, padding=10)
        connect.pack(fill=tk.X)

        ttk.Label(connect, text="Username:").pack(side=tk.LEFT)
        self.username = ttk.Entry(connect, width=15)
        self.username.pack(side=tk.LEFT, padx=5)

        ttk.Label(connect, text="Room:").pack(side=tk.LEFT)
        self.room = ttk.Entry(connect, width=15)
        self.room.pack(side=tk.LEFT, padx=5)

        ttk.Button(connect, text="Connect", command=self.connect).pack(side=tk.LEFT)

        self.text = scrolledtext.ScrolledText(self.root, state="disabled", width=60, height=20)
        self.text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        entry = ttk.Frame(self.root, padding=10)
        entry.pack(fill=tk.X)

        self.message = ttk.Entry(entry)
        self.message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(entry, text="Send", command=self.send).pack(side=tk.LEFT, padx=5)

    def connect(self) -> None:
        try:
            self.client.handshake(self.username.get(), self.room.get())
            self.client.start_udp(lambda data: self.msg_queue.put(data))
            self._connected = True
            self.root.after(100, self._process_messages)
        except Exception as exc:  # pragma: no cover - best effort logging
            self._append(f"Connection error: {exc}\n")

    def _process_messages(self) -> None:
        while not self.msg_queue.empty():
            data = self.msg_queue.get_nowait()
            _, _, msg = process_udp_message(data)
            self._append(msg.decode() + "\n")
        if self._connected:
            self.root.after(100, self._process_messages)

    def send(self) -> None:
        if not self._connected:
            self._append("Not connected.\n")
            return
        msg = self.message.get()
        if not msg:
            return
        try:
            self.client.send_message(msg)
            self.message.delete(0, tk.END)
        except Exception as exc:  # pragma: no cover - best effort logging
            self._append(f"Send error: {exc}\n")

    def _append(self, text: str) -> None:
        self.text.configure(state="normal")
        self.text.insert(tk.END, text)
        self.text.see(tk.END)
        self.text.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ChatUI().run()
