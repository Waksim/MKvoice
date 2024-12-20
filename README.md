# Text-to-Speech (TTS) Telegram Bot

This Telegram bot receives text (from a user message, a file, or a URL), performs basic text analysis, and then synthesizes speech from the text using Microsoft Edge TTS.

## Features

- **Text Input:** Send a block of text to the bot, and it will:
  - Analyze the text (word count, estimated reading time, top words, reading level, and key phrases).
  - Convert the text to an audio file (MP3) and return it to you.

- **URL Input:** Send a URL to an article or webpage. The bot will:
  - Extract text from the page (statically or dynamically if needed).
  - Analyze the text and return an MP3 with synthesized speech.

- **File Input:** Send a text file. The bot will:
  - Read the file contents.
  - Perform text analysis and return the synthesized speech as an MP3 file.

## Requirements

- Python 3.9+ recommended
- Dependencies listed in `requirements.txt`

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Waksim/MKvoice.git
   cd MKvoice
    ```
   
2. **Clone the repository**:
   ```bash
   python -m venv venv
   source venv/bin/activate
    ```
   
3. **Install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install libxml2-dev libxslt-dev python3-dev build-essential  # Linux

   pip install --upgrade pip
   pip install -r requirements.txt
   playwright install chromium  # firefox, webkit, <all>
   playwright install-deps
   ```
   
4. **Set up environment variables: Create a `.env` file in the project root**:
   ```env
   TELEGRAM_BOT_TOKEN=7000000000:AAHHYqmzvlaRiZ0000HnFFpAsRgfo1GUooE
   LOG_FILE=bot.log
   AUDIO_FOLDER=audio
   ADMIN_ID=300202500  # telegram user id
   ```
   
5. **Run the Bot:**:
   ```bash
   python main.py
   ```
   
## Usage
- **`/start`**: Start interacting with the bot.
- **`/s`**: Show the last 50 user queries.
- **Send Text**: Receive an analysis and an audio file of the text.
- **Send URL**: Extract text from the webpage, analyze it, and receive an audio file.
- **Send File**: Upload a text file to receive its audio conversion.

## License
[MIT License](https://mit-license.org/)
