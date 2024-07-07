import unittest
import time
from app.server import ChatServer
from app.client import ChatClient
from app.ai_client import AIClient
import threading

class TestChatSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.server = ChatServer(port=12346)
        cls.server_thread = threading.Thread(target=cls.server.run)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        # Close the server
        cls.server.stop()
    
    def setUp(self):
        # Clear the test_clients list before each test
        self.test_clients = []
    

    def tearDown(self):
        # Close all clients created during the test
        for client in self.test_clients:
            client.close()
        self.test_clients.clear()


    def get_server_clients_usernames(self):
        return [username['data'].decode('utf-8') for _, username in self.server.clients.items()]
    

    def create_test_client(self, username, port=12346):
        test_client = ChatClient(username, port=port, test_mode=True)
        self.test_clients.append(test_client)
        return test_client
    
    def create_test_ai_client(self, username, port=12346, interval=2, mode='lines'):
        test_client = AIClient(username, mode=mode, interval=interval, api_key='', port=port, test_mode=True)
        self.test_clients.append(test_client)
        return test_client
    
    def close_test_client(self, client):
        client.close()
        self.test_clients.remove(client)

    def test_client_connection(self):
        client = self.create_test_client("TestUser")
        client.start()
        time.sleep(1)  # Give time for the client to connect
        self.assertIn(client.username, self.get_server_clients_usernames())
    
    def test_ai_client_connection(self):
        ai_client = self.create_test_ai_client("TestUser")
        ai_client.start()
        time.sleep(1)  # Give time for the client to connect
        self.assertIn(ai_client.username, self.get_server_clients_usernames())

    def test_none_client_username(self):
        client = self.create_test_client(None)
        client.start()
        self.assertIn(client.username, "None")
    
    def test_none_ai_client_username(self):
        client = self.create_test_ai_client(None)
        client.start()
        self.assertIn(client.username, "None")
    
    def test_client_no_start(self):
        client = self.create_test_client("NoStartUser")
        time.sleep(1)  # Give time for the client to connect
        self.assertNotIn(client.username, self.get_server_clients_usernames())

    def test_ai_client_no_start(self):
        client = self.create_test_ai_client("NoStartUser")
        time.sleep(1)  # Give time for the client to connect
        self.assertNotIn(client.username, self.get_server_clients_usernames())

    def test_message_broadcast(self):
        client1 = self.create_test_client("User1")
        client2 = self.create_test_client("User2")

        client1.start()
        time.sleep(1)  # Give time for the clients to connect

        client2.start()
        
        time.sleep(1)  # Give time for the clients to connect

        test_message = "Hello, everyone!"
        client1.send_message(test_message)
        time.sleep(1)  # Give time for the message to be sent and received

        received_message = client2.received_messages
        self.assertEqual(received_message[0], f"User1: {test_message}")
    

    def test_message_ai_broadcast(self):
        client1 = self.create_test_client("User1")
        client2 = self.create_test_client("User2")
        ai_client = self.create_test_ai_client("AI")

        client1.start()
        client2.start()
        ai_client.start()
        time.sleep(1)  # Give time for the clients to connect

        test_message = "Hello, everyone!"
        client1.send_message(test_message)
        time.sleep(1)  # Give time for the message to be sent and received

        received_message = client2.received_messages
        self.assertEqual(received_message[0], f"User1: {test_message}")
        ai_received_message = ai_client.received_messages
        self.assertEqual(ai_received_message[0], f"User1: {test_message}")

    def test_single_connect_disconnect(self):
        client = self.create_test_client("disconnect_user")
        client.start()
        time.sleep(0.5)  # Give time for the clients to connect

        self.assertIn("disconnect_user", self.get_server_clients_usernames())

        self.close_test_client(client)
        time.sleep(0.5)  # Give time for server to process disconnection

        self.assertNotIn(client.username, self.get_server_clients_usernames())

    def test_single_ai_connect_disconnect(self):
        client = self.create_test_ai_client("disconnect_user")
        client.start()
        time.sleep(0.5)  # Give time for the clients to connect

        self.assertIn("disconnect_user", self.get_server_clients_usernames())

        self.close_test_client(client)
        time.sleep(0.5)  # Give time for server to process disconnection

        self.assertNotIn(client.username, self.get_server_clients_usernames())

    def test_multiple_clients_login_and_disconnect(self):
        clients = [self.create_test_client(f"User{i}") for i in range(5)]
        for client in clients:
            client.start()
        time.sleep(1)

        server_clients = self.get_server_clients_usernames()
        for client in clients:
            self.assertIn(client.username, server_clients)

        for client in clients:
            self.close_test_client(client)

        time.sleep(1)

        server_clients = self.get_server_clients_usernames()
        for client in clients:
            self.assertNotIn(client.username, server_clients)
    
    def test_multiple_clients_with_ai_login_and_disconnect(self):
        clients = [self.create_test_client(f"User{i}") for i in range(5)]
        for client in clients:
            client.start()

        ai_client = self.create_test_ai_client("AI")
        ai_client.start()
        time.sleep(1)

        server_clients = self.get_server_clients_usernames()
        for client in clients:
            self.assertIn(client.username, server_clients)

        self.assertIn(ai_client.username, server_clients)

        for client in clients:
            self.close_test_client(client)

        self.close_test_client(ai_client)

        time.sleep(1)

        server_clients = self.get_server_clients_usernames()
        for client in clients:
            self.assertNotIn(client.username, server_clients)

        self.assertNotIn(ai_client.username, server_clients)

    def test_long_message(self):
        client1 = self.create_test_client("LongSender")
        client2 = self.create_test_client("LongReceiver")
        client1.start()
        client2.start()
        time.sleep(1)

        long_message = "A" * 10000
        client1.send_message(long_message)
        time.sleep(2)  # Give more time for long message

        received_messages = client2.received_messages
        self.assertEqual(f"LongSender: {long_message}", received_messages[0])

    def test_none_message(self):
        client = self.create_test_client("NoneUser")
        client2 = self.create_test_client("NoneUserReceive")
        client.start()
        client2.start()
        time.sleep(1)

        client.send_message(None)
        time.sleep(1)

        received_message = client2.received_messages

        self.assertIn(client.username, self.get_server_clients_usernames())  # Client should still be connected
        self.assertIn(str(None), received_message[0])  # message should be 'None'

    def test_concurrent_message_sending(self):
        clients = [self.create_test_client(f"User{i}") for i in range(5)]
        for client in clients:
            client.start()
        time.sleep(1)

        messages = [f"Message from User{i}" for i in range(5)]
        threads = []
        for i, client in enumerate(clients):
            thread = threading.Thread(target=client.send_message, args=(messages[i],))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        time.sleep(1)

        received_messages = {client: client.received_messages for client in clients}
        

        for i, client in enumerate(clients):
            for j, message in enumerate(messages):
                if i != j:  # Client should not receive its own message
                    expected_message = f"User{j}: {message}"
                    self.assertIn(expected_message, received_messages[client], 
                                f"User{i} did not receive message from User{j}")
                else:
                    self.assertNotIn(f"User{i}: {message}", received_messages[client], 
                                    f"User{i} received its own message")

        # Check that each client received exactly 4 messages (all but their own)
        for i, client in enumerate(clients):
            self.assertEqual(len(received_messages[client]), 4, 
                            f"User{i} did not receive the correct number of messages")

    
    def test_ai_client_time(self):
        client = self.create_test_client('user')
        ai_client = self.create_test_ai_client('AI', mode='time', interval=1)

        client.start()
        ai_client.start()
        time.sleep(0.5)
        client.send_message("user_message")
        time.sleep(1)
        client.send_message("user_message")
        time.sleep(2)
        client.send_message("user_message")        
        time.sleep(1)

        client_received_messages = client.received_messages
        self.assertEqual(len([cm for cm in client_received_messages if "AI" in cm]), 4)


    def test_ai_client_lines(self):
        client = self.create_test_client('user')
        ai_client = self.create_test_ai_client('AI', mode='lines', interval=2)

        client.start()
        ai_client.start()
        time.sleep(0.5)

        for _ in range(6):
            client.send_message("user_message")
        
        time.sleep(0.5)

        client_received_messages = client.received_messages
        self.assertEqual(len([cm for cm in client_received_messages if "AI" in cm]), 3)
        

    def test_end_to_end_chat_scenario(self):
        # Create clients
        alice = self.create_test_client("Alice")
        bob = self.create_test_client("Bob")
        charlie = self.create_test_client("Charlie")

        # Scenario 1: Alice connects, sends a message, and disconnects
        alice.start()
        time.sleep(0.5)
        alice.send_message("Hello, is anyone here?")
        time.sleep(0.5)
        self.close_test_client(alice)
        time.sleep(0.5)

        # Scenario 2: Bob and Charlie connect and send messages concurrently
        bob.start()
        charlie.start()
        time.sleep(0.5)

        def send_messages(client, messages):
            for msg in messages:
                client.send_message(msg)
                time.sleep(0.1)

        bob_messages = ["Hi, I'm Bob!", "How's everyone doing?"]
        charlie_messages = ["Hello, Charlie here!", "Nice to meet you all!"]

        bob_send_thread = threading.Thread(target=send_messages, args=(bob, bob_messages))
        charlie_send_thread = threading.Thread(target=send_messages, args=(charlie, charlie_messages))

        bob_send_thread.start()
        charlie_send_thread.start()

        bob_send_thread.join()
        charlie_send_thread.join()
        time.sleep(0.5)

        # Assertions
        self.assertNotIn("Alice: Hello, is anyone here?", bob.received_messages)
        self.assertNotIn("Alice: Hello, is anyone here?", charlie.received_messages)

        for msg in bob_messages:
            self.assertIn(f"Bob: {msg}", charlie.received_messages)
        for msg in charlie_messages:
            self.assertIn(f"Charlie: {msg}", bob.received_messages)

        # Scenario 3: Bob leaves, Charlie sends a message
        self.close_test_client(bob)
        time.sleep(0.5)

        # Scenario 4: Alice rejoins, both Alice and Charlie send messages concurrently
        alice = self.create_test_client("Alice")
        alice.start()
        time.sleep(0.5)

        charlie.send_message("Is anyone still here?")
        time.sleep(0.5)

        self.assertIn("Charlie: Is anyone still here?", alice.received_messages)


        alice_messages = ["I'm back!", "Did I miss anything?"]
        charlie_messages = ["Welcome back, Alice!", "Glad you're here again!"]

        alice_send_thread = threading.Thread(target=send_messages, args=(alice, alice_messages))
        charlie_send_thread = threading.Thread(target=send_messages, args=(charlie, charlie_messages))

        alice_send_thread.start()
        charlie_send_thread.start()

        alice_send_thread.join()
        charlie_send_thread.join()
        time.sleep(0.5)


        for msg in alice_messages:
            self.assertIn(f"Alice: {msg}", charlie.received_messages)
        for msg in charlie_messages:
            self.assertIn(f"Charlie: {msg}", alice.received_messages)

        # Check that Bob didn't receive messages after disconnecting
        self.assertNotIn("Charlie: Is anyone still here?", bob.received_messages)
        self.assertNotIn("Alice: I'm back!", bob.received_messages)

if __name__ == '__main__':
    unittest.main()