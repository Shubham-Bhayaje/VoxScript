# VoxScript

## UI Preview
<p align="center">
<img src="https://github.com/Shubham-Bhayaje/VoxScript/blob/main/Main_Ui.png" width="100%">
</p>

## Overview
This project is a voice-controlled assistant with a GUI interface built using Tkinter. It integrates OpenAI's API to process voice commands, generate responses, and execute Python code based on user input. The assistant can listen to speech, process input using AI, generate Python scripts, and execute them in real-time.

## Features
- **Voice Recognition**: Uses Google Speech Recognition to capture and process voice input.
- **AI-Powered Responses**: Integrates OpenAI API to generate responses and code.
- **Code Execution**: Automatically generates and executes Python scripts based on user commands.
- **Graphical User Interface (GUI)**: Built using Tkinter with multiple tabs for input, response, code, and execution output.
- **Progress Indicators**: Uses progress bars to show processing status.
- **Text-to-Speech (TTS)**: Reads out AI-generated responses.
- **Error Handling**: Includes robust error handling mechanisms to provide user-friendly feedback.
- **Command History**: Stores previous commands and responses for easy reference.

## Prerequisites
### Software & Libraries
Ensure you have the following installed:
- Python 3.x
- Required Python libraries:
  ```sh
  pip install openai tkinter speechrecognition pyttsx3 dotenv
  ```
- OpenAI API Key (Set it as an environment variable `OPENAI_API_KEY`).

## Installation
1. Clone the repository or copy the project files.
2. Install the required dependencies using the command:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in an `.env` file:
   ```sh
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run the program:
   ```sh
   python voice_assistant.py
   ```

## Directory Structure
```
VoiceAssistant/
│── voice_assistant.py  # Main application file
│── requirements.txt    # Dependencies
│── .env                # API key storage
│── assets/
│   ├── mic_icon.ico    # Application icon
│── scripts/
    ├── generated_script.py  # AI-generated Python scripts
│── logs/
    ├── error_logs.txt  # Logs for error tracking
```

## Usage
- Click the **"Start Listening"** button to activate voice recognition.
- Speak your command; the assistant will process it and generate an AI response.
- If the response contains Python code, it will be displayed and executed automatically.
- The execution output will be shown in the "Execution Output" tab.
- Use the **"Read Response"** button to listen to the AI's response.
- Click **"Clear All"** to reset the interface.
- Review the **Command History** tab for previous interactions.
- Check **logs/error_logs.txt** for troubleshooting issues.

## Troubleshooting
- If the assistant fails to recognize speech, check your microphone settings.
- If you get an `API Key Missing` error, ensure the `.env` file contains the correct OpenAI API key.
- For execution errors, check the error message in the "Execution Output" tab.
- Review `logs/error_logs.txt` for error details and debugging.

## License
This project is open-source and available under the MIT License.

## Author
Your Name - Shubham Bhayaje

