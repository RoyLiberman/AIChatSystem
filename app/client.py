import socket
import struct
import threading
import sys
import select
import os

class ChatClient:
    def __init__(self, username, host='localhost', port=8080, test_mode=False):
        self.username = str(username)
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.test_mode = test_mode
        self.listening = False
        self.listen_thread = None
        self.received_messages = [] if test_mode else None

    def send_message(self, message):
        message = str(message).encode('utf-8')
        message_header = struct.pack('!I', len(message))
        self.client_socket.send(message_header + message)

    def receive_message(self):
        try:
            message_header = self.client_socket.recv(4)
            if not len(message_header):
                return None  # Connection closed by the server
            message_length = struct.unpack('!I', message_header)[0]
            return self.client_socket.recv(message_length).decode('utf-8')
        except IOError:
            return None
        except Exception as e:
            print(f"Error receiving message: {str(e)}")
            return None
    
    def handle_receive(self):
        message = self.receive_message()
        if message:
            if self.test_mode:
                self.received_messages.append(message)
            
            print(message)
            
    def handle_input(self):
        line = sys.stdin.readline().strip()
        if line:
            self.send_message(line)

    def listen_for_events(self):
        while self.listening:
            try:
                read_sockets, _, _ = select.select([self.client_socket, sys.stdin], [], [], 0.1)
                for notified_socket in read_sockets:
                    if notified_socket == self.client_socket:
                        self.handle_receive()
                    elif notified_socket == sys.stdin and not self.test_mode:
                        self.handle_input()
            except Exception as e:
                print(f"Error in select: {str(e)}")
                sys.exit()

    def start(self):
        self.client_socket.connect((self.host, self.port))
        self.client_socket.setblocking(False)
        self.listening = True
        self.send_message(self.username)
        self.listen_thread = threading.Thread(target=self.listen_for_events)
        self.listen_thread.start()
    
    def close(self):
        self.listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=1)
            self.send_message("__DISCONNECT__")  # Send disconnect message
        self.client_socket.close()

if __name__ == "__main__":
    username = input("Enter your Username: ")
    print("Waiting for your message write it and press enter to send")
    client = ChatClient(username)
    client.start()