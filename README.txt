# Chat Application

This chat application consists of a server, client, and AI client. It allows multiple clients to connect and communicate, with an optional AI participant.

## Setup

1. Clone the repository:
    git clone <repository-url>
    cd <repository-directory>

2. Create a virtual environment:
    python3 -m venv venv

3. Activate the virtual environment:
- On Unix or MacOS:
  ```
  source venv/bin/activate
  ```
- On Windows:
  ```
  venv\Scripts\activate
  ```

4. Install the required dependencies:
    pip install -r requirements.txt

## Running the Application

All commands should be run from the root directory of the project.

### Start the Server

python3 app/server.py

The server will start and listen for incoming connections.

### Start a Client

Follow the prompts to enter your username and connect to the chat.

### Start an AI Client

python3 app/ai_client.py

You will be prompted to enter:
- Mode: Choose either 'lines' or 'time'
  - 'lines': AI responds after a specified number of chat messages
  - 'time': AI responds at regular time intervals
- Interval: 
  - For 'lines' mode: number of messages before AI responds
  - For 'time' mode: number of seconds between AI responses
- OpenAI API Key: Your personal API key for OpenAI

Example:
Enter mode (lines/time): lines
Enter interval: 5
Enter your OpenAI API key: sk-...


## Running Tests

To run the test suite:
python3 tests.py


Ensure you're in the virtual environment when running the tests.

## Notes

- Make sure the server is running before starting any clients.
- Keep your OpenAI API key confidential and do not share it publicly.
- The AI client requires an active internet connection to communicate with the OpenAI API.