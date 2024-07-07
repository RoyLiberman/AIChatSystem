# server.py
import socket
import select
import struct

class ChatServer:
    def __init__(self, host='localhost', port=8080):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        
        self.running = True
        self.sockets_list = [self.server_socket]
        self.clients = {}
        print(f"Chat server started on {host}:{port}")

    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(4)
            if not len(message_header):
                return False
            message_length = struct.unpack('!I', message_header)[0]
            return {"header": message_header, "data": client_socket.recv(message_length)}
        except:
            return False
    
    def remove_client(self, client_socket):
        self.sockets_list.remove(client_socket)
        del self.clients[client_socket]
        client_socket.close()

    def stop(self):
        self.running = False

    def broadcast(self, message, sender_socket):
        sender_username = self.clients[sender_socket]['data'].decode('utf-8')
        for client_socket in self.clients:
            if client_socket != sender_socket:
                try:
                    # Prepare the new message with the sender's username
                    full_message = f"{sender_username}: {message['data'].decode('utf-8')}"
                    full_message = full_message.encode('utf-8')
                    message_header = struct.pack('!I', len(full_message))
                    client_socket.send(message_header + full_message)
                except:
                    # If sending fails, assume the client has disconnected
                    print(f"Failed to send message to a client. Removing client.")
                    self.sockets_list.remove(client_socket)
                    del self.clients[client_socket]
                    
    def run(self):
        while self.running:
            try:
                read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
                
                for notified_socket in read_sockets:
                    if notified_socket == self.server_socket:
                        client_socket, client_address = self.server_socket.accept()
                        user = self.receive_message(client_socket)
                        if user is False:
                            continue
                        
                        self.sockets_list.append(client_socket)
                        self.clients[client_socket] = user
                        print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username:{user['data'].decode('utf-8')}")
                    else:
                        message = self.receive_message(notified_socket)
                        if message is False:
                            print(f"Closed connection from {self.clients[notified_socket]['data'].decode('utf-8')}")
                            self.remove_client(notified_socket)
                            continue

                        if message['data'].decode('utf-8') == "__DISCONNECT__":
                            print(f"Received disconnect message from {self.clients[notified_socket]['data'].decode('utf-8')}")
                            self.remove_client(notified_socket)
                            continue

                        user = self.clients[notified_socket]
                        print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")
                        self.broadcast(message, notified_socket)

                for notified_socket in exception_sockets:
                    self.sockets_list.remove(notified_socket)
                    del self.clients[notified_socket]
            except Exception as e:
                print(f"Server error: {str(e)}")
                break
        
        print("server stop")
        # Close all client sockets
        for client_socket in self.sockets_list[1:]:
            client_socket.close()
        self.server_socket.close()
        print("Server stopped")

if __name__ == "__main__":
    server = ChatServer()
    server.run()