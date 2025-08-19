# Offline Voice-Activated POS System

## Project Architecture

The Offline Voice-Activated POS System is built with a modular, component-based architecture to enable fully offline operation. The core of the system is a central main.py loop that orchestrates interactions between the following key components:

Speech-to-Text (STT) (stt.py and main.py): This component is responsible for converting spoken commands into text. It leverages the whisper.cpp command-line interface for high-performance, local transcription. A recording function captures audio from the microphone, which is then processed by whisper.cpp.

Retrieval-Augmented Generation (RAG) (rag.py): This component manages the product inventory. It uses a pre-built index of product information, allowing it to perform fast semantic searches to find the most relevant product based on a user's spoken query. This ensures accurate item matching without needing a large, online database.

Large Language Model (LLM) (llm.py): A small, offline-compatible LLM (e.g., gemma3:1b) is used to generate conversational and human-friendly responses. It takes the output of the POS logic (e.g., "Added 2 apples") and formats it into a natural-sounding confirmation message or a receipt.

Point-of-Sale (POS) Logic (pos_logic.py): This module contains the core business logic. It includes the Cart class to manage items, quantities, and totals. It also contains parsing functions (parse_multi_items) to extract the quantity and item name from the transcribed text.

The system's flow is as follows:

The user speaks a command.

The record_until_enter function captures the audio and saves it to a WAV file.

The whisper.cpp CLI is executed to transcribe the audio file into text.

The handle_command function takes the transcribed text and uses a rule-based approach (cmd_type) to determine if the command is "add", "remove", or "checkout".

If the command is "add" or "remove", the parse_multi_items function extracts the quantity and item from the text.

The InventoryRAG component searches for the best match for the spoken item.

The Cart object is updated, and the inventory JSON file is modified to reflect the changes.

A prompt is sent to the OfflineLLM to generate a confirmation message, which is then printed to the console.

## Setup Instructions

Clone the Repository:
git clone https://github.com/Mohamedarsath26/pos_rag.git
cd pos_rag

Install Python Dependencies:
This project requires several Python packages. You can install them using pip:
pip install rich sounddevice numpy

### 🔹 Gemma Model Setup (with Ollama)

1. Download Ollama

Install it on your system (Windows, macOS, or Linux).

2. Set Ollama path in Environment Variables

On Windows: Add Ollama installation path (usually C:\Users\<your-username>\AppData\Local\Programs\Ollama) to your PATH in Environment Variables.

On Linux/macOS: Ollama installs under /usr/local/bin by default, so usually no change is needed.

3. Pull Gemma model

ollama pull gemma3:1b

This will download the Gemma model from Ollama’s registry.

4. Run Gemma

ollama run gemma3:1b

✅ You now have Gemma running locally with Ollama.

### 🔹 Whisper.cpp Setup (Speech-to-Text)

1. Clone the repository

git clone https://github.com/ggerganov/whisper.cpp.git

2. Enter the directory

cd whisper.cpp

3. Build Whisper.cpp

On Linux/macOS:
make

On Windows: Open Developer Command Prompt for MSVC and run:
make

(You may need CMake + Visual Studio Build Tools.)

4. Download the model

Whisper.cpp provides a script to download pre-trained models:
sh ./models/download-ggml-model.sh large-v3-turbo

⚠️ Correct name is large-v3-turbo (not large_v3_turbo).

Other available models: tiny, base, small, medium, large-v3, etc.

**Project Structure:** Ensure your file paths match the ones in
        > the main.py file, or update the paths accordingly:\
        > D:\\offline_pos_rag\\\
        > ├── app/\
        > │ ├── data/\
        > │ │ └── inventory.json\
        > │ ├── llm.py\
        > │ ├── pos_logic.py\
        > │ ├── rag.py\
        > │ └── stt.py\
        > ├── whisper.cpp/\
        > │ └── build/\
        > │ └── bin/\
        > │ └── Release/\
        > │ └── whisper-cli.exe\
        > └── main.py

## How to Run

Start your local LLM server. For example, using Ollama: ollama run gemma:1b

Navigate to the project directory in your terminal.

Run the main application:
python main.py

### Usage Example

Here is an example of a typical session using the WAV file input option:

(D:\offline_pos_rag\venv) D:\offline_pos_rag>python main.py
🔄 Initializing models, please wait...

=== POS System ===
1. Simulate (type commands manually)
2. WAV file input
3. Microphone input
4. Exit
Enter choice (1-4): 2
Enter WAV file path: D:\offline_pos_rag\add\audio.wav
⏳ Transcribing...
📝 Transcription:


[00:00:00.000 --> 00:00:02.500]    Add one apple.

Okay, I’ve added one apple. The cart now contains: {'APL001': 1}. 

Is there anything else I can help you with regarding this cart?

=== POS System ===
1. Simulate (type commands manually)
2. WAV file input
3. Microphone input
4. Exit
Enter choice (1-4): 2
Enter WAV file path: 2
File not found: 2

=== POS System ===
1. Simulate (type commands manually)
2. WAV file input
3. Microphone input
4. Exit
Enter choice (1-4): 2
Enter WAV file path: D:\offline_pos_rag\add\audio_2.wav
⏳ Transcribing...
📝 Transcription:


[00:00:00.000 --> 00:00:04.240]    Add one banana and one coffee.

Okay, I've added one banana. The cart now contains: {'APL001': 1, 'BAN001': 1}.
Okay, I've added one coffee.

The cart now contains: {'APL001': 1, 'BAN001': 1, 'COF001': 1}

Is there anything else I can help with?

=== POS System ===
1. Simulate (type commands manually)
2. WAV file input
3. Microphone input
4. Exit
Enter choice (1-4): 2
Enter WAV file path: D:\offline_pos_rag\remove\audio.wav
⏳ Transcribing...
📝 Transcription:


[00:00:00.000 --> 00:00:04.240]    Remove one coffee.

Okay, I've removed one coffee.

Now the data is: {'APL001': 1, 'BAN001': 1}

=== POS System ===
1. Simulate (type commands manually)
2. WAV file input
3. Microphone input
4. Exit
Enter choice (1-4): 2
Enter WAV file path: D:\offline_pos_rag\checkout\audio.wav
⏳ Transcribing...
📝 Transcription:


[00:00:00.000 --> 00:00:03.480]    Check out.

Okay, here's a short receipt-style summary:

**Receipt Summary:**

* **Items:** APL001 - 1, BAN001 - 1
* **Total:** $66.40

---

Let me know if you’d like me to do anything else!

