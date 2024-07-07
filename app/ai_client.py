import time
from app.client import ChatClient
import select
import sys
from openai import OpenAI

def retry(retry_count=5, initial_delay=20):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = initial_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retries < retry_count:
                        retries += 1
                        print(f'Waiting: {current_delay} seconds')
                        time.sleep(current_delay)
                        current_delay = min(current_delay * 2, 60)  # exponential backoff
                    else:
                        print(f'Maximum attempts made. Error: {e}')
                        raise
        return wrapper
    return decorator


class AIClient(ChatClient):
    def __init__(self, username, mode, interval, api_key, host='localhost', port=8080, test_mode=False):
        super().__init__(username, host, port, test_mode)

        if mode != 'lines' and mode != 'time':
            raise f'Unallowed mode was entered: {mode}, supporing only lines or time'
        
        self.mode = mode
        self.interval = interval
        self.message_count = 0
        self.last_response_time = time.time()
        self.conversation_history = []
        self.received_messages = [] if test_mode else None
        self.api_key = api_key
        self.openai_client = OpenAI(
            # This is the default and can be omitted
            api_key=api_key,
        )

    def handle_receive(self):
        message = self.receive_message()
        if message:
            if self.test_mode:
                self.received_messages.append(message)
            
            print(message)
            self.message_count += 1
            self.conversation_history.append(message)

            if self.mode == 'lines' and self.message_count % self.interval == 0:
                self.generate_response()
    
    def handle_input(self):
        pass

    def listen_for_events(self):
        while self.listening:
            try:
                if self.mode == 'time' and time.time() - self.last_response_time >= self.interval:
                    self.generate_unrelated_message()
                
                    self.last_response_time = time.time()

                read_sockets, _, _ = select.select([self.client_socket], [], [], 0.1)
                for notified_socket in read_sockets:
                    if notified_socket == self.client_socket:
                        self.handle_receive()

            except Exception as e:
                print(f"Error in select: {str(e)}")
                sys.exit()

    def generate_response(self):
        if self.test_mode:
            self.send_message("related message by lines")
        else:
            system_prompt = f'''
                    You are in a chat room. The following is a conversation. Respond to it:,
                    recent message:
                        {"\n".join(self.conversation_history[-self.interval:])}
            '''

            model_response = self.call_open_ai_api(
                system_prompt=system_prompt,
                user_prompt="Generate a relevent response to the chat",
                temperature=0
            )

            if model_response != None:
                return self.send_message(model_response)
            
    def generate_unrelated_message(self):
        if self.test_mode:
            self.send_message("related message by time")
        else:
            model_response = self.call_open_ai_api(
                system_prompt="You are in a chat room.",
                user_prompt="Generate a random, interesting message for the chat room, that you have never sent before",
                temperature=0.9
            )

            if model_response != None:
                return self.send_message(model_response)
            

    @retry(retry_count=5, initial_delay=20)
    def call_open_ai_api(self, system_prompt, user_prompt, model="gpt-3.5-turbo", temperature=0):
        try:
            chat_completion_response = self.openai_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=temperature
            )

            if chat_completion_response.choices:
                return chat_completion_response.choices[0].message.content.strip()
            return None
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            raise  # Re-raise the exception to trigger the retry


if __name__ == "__main__":
    username = input("Enter AI bot name: ")
    mode = input("Enter mode (lines/time): ")
    while mode != "lines" and mode != "time":
        print("only two modes are supported: lines or time")
        mode = input("Enter mode (lines/time): ")
    interval = int(input("Enter interval: "))
    api_key = input("Enter your OpenAI API key: ") 
    
    ai_client = AIClient(username, mode, interval, api_key)
    ai_client.start()