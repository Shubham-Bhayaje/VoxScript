import os
import subprocess
import re
import speech_recognition as sr
import pyttsx3
from openai import OpenAI
import threading
import time
import keyboard
import json
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime
import flet as ft
from flet import (
    Page, Text, TextField, ElevatedButton, Column, Row, 
    Container, ProgressBar, Tabs, Tab, IconButton, 
    Icons, Colors, TextButton, AlertDialog, Switch,
    Dropdown, Slider, Checkbox, ScrollMode
)

load_dotenv()

def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    api_key = config.get("api_key")
            except Exception as e:
                print(f"Error loading config: {e}")
    return api_key

API_KEY = get_api_key()
if not API_KEY:
    raise ValueError("❌ Missing API Key! Set OPENAI_API_KEY as an environment variable or in config.json.")

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=API_KEY,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_PATH = os.path.join(BASE_DIR, "app.log")
HISTORY_PATH = os.path.join(BASE_DIR, "conversation_history.json")

os.makedirs(SCRIPTS_DIR, exist_ok=True)
recognizer = sr.Recognizer()

def setup_logging():
    """Set up comprehensive logging system"""
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"voxscript_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class VoiceAssistantApp:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "VoxScript Voice Assistant"
        self.page.theme_mode = "light"
        self.page.padding = 20
        self.page.scroll = ScrollMode.AUTO
        
        # Initialize state variables
        self.current_code = ""
        self.is_processing = False
        self.is_listening = False
        self.is_reading = False
        self.stop_listening_event = threading.Event()
        self.stop_reading_event = threading.Event()
        self.listen_thread = None
        self.read_thread = None
        self.current_script_path = None
        
        # Initialize settings with default values
        self.model_name = "gpt-4"
        self.temperature = 0.7
        self.max_tokens = 2000
        self.voice_enabled = True
        self.auto_save = True
        self.theme = "light"
        self.language = "en-US"

        # Load settings
        self.load_settings()
      
        # Initialize UI components
        self.setup_ui()

        # Load conversation history
        self.conversation_history = self.load_conversation_history()
        
    def load_settings(self):
        """Load settings with validation and defaults"""
        default_settings = {
            "model_name": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "voice_enabled": True,
            "auto_save": True,
            "theme": "light",
            "language": "en-US"
        }
        
        try:
            config_path = os.path.join(BASE_DIR, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    user_settings = json.load(f)
                    # Validate and merge settings
                    for key, value in default_settings.items():
                        if key in user_settings:
                            if key == "temperature" and not (0 <= user_settings[key] <= 1):
                                logger.warning(f"Invalid temperature value: {user_settings[key]}")
                                user_settings[key] = default_settings[key]
                            elif key == "max_tokens" and not (100 <= user_settings[key] <= 4000):
                                logger.warning(f"Invalid max_tokens value: {user_settings[key]}")
                                user_settings[key] = default_settings[key]
        else:
                            user_settings[key] = value
            else:
                user_settings = default_settings
                self.save_settings(user_settings)
                
            # Update instance variables
            self.model_name = user_settings["model_name"]
            self.temperature = user_settings["temperature"]
            self.max_tokens = user_settings["max_tokens"]
            self.voice_enabled = user_settings["voice_enabled"]
            self.auto_save = user_settings["auto_save"]
            self.theme = user_settings["theme"]
            self.language = user_settings["language"]
            
            logger.info("Settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)
            # Fallback to defaults
            self.model_name = default_settings["model_name"]
            self.temperature = default_settings["temperature"]
            self.max_tokens = default_settings["max_tokens"]
            self.voice_enabled = default_settings["voice_enabled"]
            self.auto_save = default_settings["auto_save"]
            self.theme = default_settings["theme"]
            self.language = default_settings["language"]
            
    def save_settings(self, settings):
        """Save settings with validation"""
        try:
            # Validate settings
            if not (0 <= settings["temperature"] <= 1):
                raise ValueError("Temperature must be between 0 and 1")
            if not (100 <= settings["max_tokens"] <= 4000):
                raise ValueError("Max tokens must be between 100 and 4000")
                
            config_path = os.path.join(BASE_DIR, "config.json")
            with open(config_path, "w") as f:
                json.dump(settings, f, indent=4)
                
            logger.info("Settings saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            self.update_status("Error saving settings", "error")
            return False
        
    def setup_ui(self):
        """Set up the Flet UI components"""
        # Header
        self.status_indicator = Container(
            width=20,
            height=20,
            border_radius=10,
            bgcolor=Colors.GREEN
        )
        
        self.status_text = Text("Ready", size=16)
        
        header = Row(
            controls=[
                Text("VoxScript Voice Assistant", size=24, weight="bold"),
                Row(
                    controls=[
                        self.status_indicator,
                        self.status_text
                    ],
                    alignment="end",
                    expand=True
                )
            ],
            alignment="spaceBetween"
        )
        
        # Microphone button
        self.mic_button = ElevatedButton(
            text="🎤 Start Listening",
            icon=Icons.MIC,
            on_click=self.toggle_listening,
            bgcolor=Colors.BLUE,
            color=Colors.WHITE
        )
        
        # Progress bar
        self.progress = ProgressBar(
            width=400,
            visible=False
        )
        
        # Tabs
        self.input_text = TextField(
            multiline=True,
            min_lines=5,
            max_lines=5,
            expand=True
        )
        
        self.response_text = TextField(
            multiline=True,
            min_lines=10,
            max_lines=10,
            expand=True
        )
        
        self.code_text = TextField(
            multiline=True,
            min_lines=15,
            max_lines=15,
            expand=True,
            read_only=True
        )
        
        self.output_text = TextField(
            multiline=True,
            min_lines=10,
            max_lines=10,
            expand=True,
            read_only=True
        )
        
        tabs = Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                Tab(
                    text="Input",
                    content=Container(
                        content=self.input_text,
                        padding=10
                    )
                ),
                Tab(
                    text="Response",
                    content=Container(
                        content=self.response_text,
                        padding=10
                    )
                ),
                Tab(
                    text="Code",
                    content=Container(
                        content=self.code_text,
                        padding=10
                    )
                ),
                Tab(
                    text="Output",
                    content=Container(
                        content=self.output_text,
                        padding=10
                    )
                )
            ],
            expand=True
        )
        
        # Action buttons
        action_buttons = Row(
            controls=[
                ElevatedButton(
                    text="Execute Code",
                    icon=Icons.PLAY_ARROW,
                    on_click=self.execute_current_code
                ),
                ElevatedButton(
                    text="Read Response",
                    icon=Icons.VOLUME_UP,
                    on_click=self.read_response
                ),
                ElevatedButton(
            text="Stop Reading",
                    icon=Icons.STOP,
                    on_click=self.stop_reading,
                    disabled=True
                ),
                ElevatedButton(
                    text="Clear All",
                    icon=Icons.CLEAR_ALL,
                    on_click=self.clear_all
                )
            ],
            alignment="center",
            spacing=10
        )
        
        # Main layout
        self.page.add(
            Column(
                controls=[
                    header,
                    self.mic_button,
                    self.progress,
                    tabs,
                    action_buttons
                ],
                spacing=20,
                expand=True
            )
        )
        
        # Setup menu
        self.setup_menu()
        
    def setup_menu(self):
        """Set up the application menu"""
        def open_settings(e):
            self.show_settings_dialog()
            
        def show_about(e):
            self.show_about_dialog()
            
        def show_instructions(e):
            self.show_instructions_dialog()
            
        self.page.appbar = ft.AppBar(
            title=Text("VoxScript"),
            center_title=False,
            bgcolor=Colors.BLUE,
            actions=[
                IconButton(Icons.SETTINGS, on_click=open_settings),
                IconButton(Icons.HELP, on_click=show_instructions),
                IconButton(Icons.INFO, on_click=show_about)
            ]
        )
        
    def update_status(self, message, level="info"):
        """Update status with visual feedback"""
        self.status_text.value = message
        
        if level == "error":
            self.status_indicator.bgcolor = Colors.RED
        elif level == "warning":
            self.status_indicator.bgcolor = Colors.AMBER
        elif level == "success":
            self.status_indicator.bgcolor = Colors.GREEN
        else:
            self.status_indicator.bgcolor = Colors.BLUE
            
        self.page.update()
        logger.info(f"Status update: {message} ({level})")
        
    def toggle_listening(self, e):
        """Toggle speech recognition on/off"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        """Start speech recognition"""
        if self.is_listening:  
            return
            
        self.is_listening = True
        self.stop_listening_event.clear()
        self.mic_button.text = "🛑 Stop Listening"
        self.mic_button.bgcolor = Colors.RED
        self.update_status("Listening... Speak now")
        
        self.listen_thread = threading.Thread(target=self.listen_for_voice)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False
        self.stop_listening_event.set()
        self.mic_button.text = "🎤 Start Listening"
        self.mic_button.bgcolor = Colors.BLUE
        self.update_status("Stopped listening")

    def listen_for_voice(self):
        """Enhanced voice recognition with better error handling and feedback"""
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.update_status("Adjusting for ambient noise...", "info")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Listening...")
                self.update_status("Listening...", "info")
                
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
                
                try:
                    logger.info("Processing speech...")
                    self.update_status("Processing speech...", "info")
                        text = recognizer.recognize_google(audio)
                    
                    if text.strip():
                        logger.info(f"Recognized: {text}")
                        self.update_status("Processing command...", "info")
                        self.process_input(text)
                    else:
                        logger.warning("No speech detected")
                        self.update_status("No speech detected", "warning")
                        
                    except sr.UnknownValueError:
                    logger.warning("Could not understand audio")
                    self.update_status("Could not understand audio", "warning")
                except sr.RequestError as e:
                    logger.error(f"Could not request results: {e}", exc_info=True)
                    self.update_status("Speech recognition service error", "error")
                        
        except Exception as e:
            logger.error(f"Error in voice recognition: {e}", exc_info=True)
            self.update_status("Error in voice recognition", "error")
        finally:
            self.stop_listening()

    def process_input(self, user_input):
        """Process user input and generate response"""
        if not user_input.strip():
            logger.warning("Empty input received")
            self.update_status("Please provide a command", "warning")
            return
            
        try:
            logger.info(f"Processing input: {user_input}")
            self.update_status("Processing command...", "info")
            
            # Update input text
            self.input_text.value = user_input
            
            # Start processing in a separate thread
            processing_thread = threading.Thread(
            target=self._process_input_thread, 
                args=(user_input,)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            self.update_status("Error processing command", "error")
            self.response_text.value = f"Error: {str(e)}"

    def _process_input_thread(self, user_input):
        """Thread for processing input and generating response"""
        try:
            self.update_status(f"Processing: {user_input[:50]}...", "info")
            logger.info(f"Processing user input: {user_input}")
            
            response = self.generate_response(user_input)
            self.response_text.value = response
            
            code = self.extract_code(response)
            if code:
                self.current_code = code
                self.code_text.value = code
                self.save_and_execute_code(code, user_input)
            else:
                self.update_status("No code found in response", "warning")
                self.read_response()
                
            self.update_history_display()
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "error")
            logger.error(f"Error in processing input: {str(e)}", exc_info=True)
            
        finally:
            self.progress.visible = False
            self.is_processing = False
            self.page.update()
            
    def show_settings_dialog(self):
        """Show settings dialog"""
        def save_settings(e):
            try:
                settings = {
                    "model_name": model_dropdown.value,
                    "temperature": float(temp_slider.value),
                    "max_tokens": int(tokens_field.value),
                    "voice_enabled": voice_switch.value,
                    "auto_save": auto_save_switch.value,
                    "theme": theme_dropdown.value,
                    "language": language_dropdown.value
                }
                
                if self.save_settings(settings):
                    self.model_name = settings["model_name"]
                    self.temperature = settings["temperature"]
                    self.max_tokens = settings["max_tokens"]
                    self.voice_enabled = settings["voice_enabled"]
                    self.auto_save = settings["auto_save"]
                    self.theme = settings["theme"]
                    self.language = settings["language"]
                    
                    # Apply theme changes
                    self.page.theme_mode = self.theme
                    settings_dialog.open = False
                    self.page.update()
                    
            except ValueError as e:
                self.page.show_snack_bar(
                    ft.SnackBar(content=Text(str(e)))
                )
                
        # Create settings controls
        model_dropdown = Dropdown(
            value=self.model_name,
            options=[
                ft.dropdown.Option("gpt-4"),
                ft.dropdown.Option("gpt-3.5-turbo")
            ]
        )
        
        temp_slider = Slider(
            value=self.temperature,
            min=0,
            max=1,
            divisions=10
        )
        
        tokens_field = TextField(
            value=str(self.max_tokens),
            keyboard_type="number"
        )
        
        voice_switch = Switch(value=self.voice_enabled)
        auto_save_switch = Switch(value=self.auto_save)
        
        theme_dropdown = Dropdown(
            value=self.theme,
            options=[
                ft.dropdown.Option("light"),
                ft.dropdown.Option("dark")
            ]
        )
        
        language_dropdown = Dropdown(
            value=self.language,
            options=[
                ft.dropdown.Option("en-US"),
                ft.dropdown.Option("en-GB"),
                ft.dropdown.Option("es-ES"),
                ft.dropdown.Option("fr-FR"),
                ft.dropdown.Option("de-DE")
            ]
        )
        
        settings_dialog = AlertDialog(
            title=Text("Settings"),
            content=Column(
                controls=[
                    Text("AI Model:"),
                    model_dropdown,
                    Text("Temperature:"),
                    temp_slider,
                    Text("Max Tokens:"),
                    tokens_field,
                    Row(
                        controls=[
                            Text("Voice Enabled:"),
                            voice_switch
                        ]
                    ),
                    Row(
                        controls=[
                            Text("Auto Save:"),
                            auto_save_switch
                        ]
                    ),
                    Text("Theme:"),
                    theme_dropdown,
                    Text("Language:"),
                    language_dropdown
                ],
                spacing=10
            ),
            actions=[
                TextButton("Save", on_click=save_settings),
                TextButton("Cancel", on_click=lambda e: setattr(settings_dialog, "open", False))
            ]
        )
        
        self.page.dialog = settings_dialog
        settings_dialog.open = True
        self.page.update()
        
    def show_about_dialog(self):
        """Show about dialog"""
        about_dialog = AlertDialog(
            title=Text("About VoxScript"),
            content=Column(
                controls=[
                    Text("VoxScript Voice Assistant"),
                    Text("Version 1.0"),
                    Text("© 2023")
                ],
                spacing=10
            ),
            actions=[
                TextButton("OK", on_click=lambda e: setattr(about_dialog, "open", False))
            ]
        )
        
        self.page.dialog = about_dialog
        about_dialog.open = True
        self.page.update()
        
    def show_instructions_dialog(self):
        """Show instructions dialog"""
        instructions = """
        VoxScript Voice Assistant Instructions:
        
        1. Click the microphone button to start speaking 
            or Click Ctrl+J
        2. Say your command (e.g., "Create a calculator app")
        3. The AI will generate Python code
        4. Review the code in the Generated Code tab
        5. Click Execute Code to run it
        6. View results in the Execution Output tab
        7. Use Read Response to hear the explanation
        
        Tips:
        - Be specific in your requests
        - The AI will attempt to fix errors automatically
        - You can edit code before executing
        - Save useful code snippets for later
        """
        
        instructions_dialog = AlertDialog(
            title=Text("Instructions"),
            content=Column(
                controls=[
                    Text(instructions)
                ],
                scroll=ScrollMode.AUTO
            ),
            actions=[
                TextButton("Close", on_click=lambda e: setattr(instructions_dialog, "open", False))
            ]
        )
        
        self.page.dialog = instructions_dialog
        instructions_dialog.open = True
        self.page.update()

    def execute_current_code(self, e):
        """Execute the currently displayed code"""
        if not self.current_code:
            self.update_status("No code to execute", "warning")
            return
            
        try:
            self.update_status("Executing code...", "info")
            self.progress.visible = True
            self.page.update()
            
            # Save code to temporary file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            script_name = f"script_{timestamp}.py"
            self.current_script_path = os.path.join(SCRIPTS_DIR, script_name)
            
            with open(self.current_script_path, 'w') as f:
                f.write(self.current_code)
                
            # Execute the code
            result = subprocess.run(
                ["python", self.current_script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stderr:
                error = result.stderr
                self.update_status(f"Error: {error[:100]}...", "error")
                self.output_text.value = f"ERROR:\n{error}"
                
                # Try to fix the error
                fixed_response = self.generate_response(
                    self.input_text.value,
                    f"Previous code failed with error:\n{error}\nPlease fix it."
                )
                fixed_code = self.extract_code(fixed_response)
                
                if fixed_code:
                    self.current_code = fixed_code
                    self.code_text.value = fixed_code
                    self.save_and_execute_code(fixed_code, self.input_text.value)
            else:
                output = result.stdout or "Code executed successfully with no output"
                self.output_text.value = output
                self.update_status("Execution complete", "success")
                
        except subprocess.TimeoutExpired:
            self.update_status("Execution timed out (30s)", "error")
            self.output_text.value = "ERROR: Execution timed out after 30 seconds"
        except Exception as e:
            self.update_status(f"Execution error: {str(e)}", "error")
            self.output_text.value = f"ERROR:\n{str(e)}"
        finally:
            self.progress.visible = False
            self.page.update()

    def save_and_execute_code(self, code, user_input, retry_count=0):
        """Save code to file and execute it"""
        if retry_count >= 3:
            self.update_status("Max retries reached", "error")
            return
            
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            script_name = f"script_{timestamp}.py"
            self.current_script_path = os.path.join(SCRIPTS_DIR, script_name)
            
            with open(self.current_script_path, 'w') as f:
                f.write(code)
                
            self.update_status(f"Executing {script_name}...", "info")
            
            result = subprocess.run(
                ["python", self.current_script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stderr:
                error = result.stderr
                self.update_status(f"Error: {error[:100]}...", "error")
                self.output_text.value = f"ERROR:\n{error}"
                
                # Try to fix the error
                fixed_response = self.generate_response(
                    user_input,
                    f"Previous code failed with error:\n{error}\nPlease fix it."
                )
                fixed_code = self.extract_code(fixed_response)
                
                if fixed_code:
                    self.current_code = fixed_code
                    self.code_text.value = fixed_code
                    self.save_and_execute_code(fixed_code, user_input, retry_count + 1)
            else:
                output = result.stdout or "Code executed successfully with no output"
                self.output_text.value = output
                self.update_status("Execution complete", "success")
                
        except subprocess.TimeoutExpired:
            self.update_status("Execution timed out (30s)", "error")
            self.output_text.value = "ERROR: Execution timed out after 30 seconds"
        except Exception as e:
            self.update_status(f"Execution error: {str(e)}", "error")
            self.output_text.value = f"ERROR:\n{str(e)}"

    def read_response(self, e=None):
        """Read the AI response aloud"""
        if self.is_reading:
            return
            
        response = self.response_text.value.strip()
        if not response:
            self.update_status("No response to read", "warning")
            return
            
        self.is_reading = True
        self.stop_reading_event.clear()
        
        # Enable stop reading button
        for button in self.page.controls[0].controls[-1].controls:
            if button.text == "Stop Reading":
                button.disabled = False
                break
                
        self.page.update()
        
        # Start reading thread
        self.read_thread = threading.Thread(
            target=self._read_text,
            args=(response,),
            daemon=True
        )
        self.read_thread.start()

        # Update status
        self.update_status("Reading response...", "info")
        
    def stop_reading(self, e):
        """Stop the text-to-speech reading"""
        if self.is_reading:
            self.stop_reading_event.set()
            self.update_status("Stopping speech...", "info")
            
            # Disable stop reading button
            for button in self.page.controls[0].controls[-1].controls:
                if button.text == "Stop Reading":
                    button.disabled = True
                    break
                    
            self.page.update()

    def _read_text(self, text):
        """Thread for text-to-speech reading"""
        try:
            engine = pyttsx3.init()
            clean_text = re.sub(r"```.*?```", "[code]", text, flags=re.DOTALL)
            
            for sentence in re.split(r'(?<=[.!?])\s+', clean_text):
                if self.stop_reading_event.is_set():
                    break
                    
                engine.say(sentence)
                engine.runAndWait()
                time.sleep(0.1)
                
            self.update_status("Finished reading", "success")
        except Exception as e:
            self.update_status(f"Reading error: {str(e)}", "error")
        finally:
            self.is_reading = False
            self.stop_reading_event.clear()
            
            # Disable stop reading button
            for button in self.page.controls[0].controls[-1].controls:
                if button.text == "Stop Reading":
                    button.disabled = True
                    break
                    
            self.page.update()
            
    def clear_all(self, e):
        """Clear all text fields"""
        self.input_text.value = ""
        self.response_text.value = ""
        self.code_text.value = ""
        self.output_text.value = ""
        self.current_code = ""
        self.current_script_path = None
        self.update_status("All cleared", "info")
        self.page.update()

    def load_conversation_history(self):
        """Load conversation history from file"""
            try:
            if os.path.exists(HISTORY_PATH):
                with open(HISTORY_PATH, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No conversation history found, starting new history")
                return []
            except Exception as e:
            logger.error(f"Error loading conversation history: {e}", exc_info=True)
        return []

    def save_conversation_history(self):
        """Save conversation history to file"""
        try:
            with open(HISTORY_PATH, 'w') as f:
                json.dump(self.conversation_history, f, indent=4)
            logger.info("Conversation history saved successfully")
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}", exc_info=True)

    def update_history_display(self):
        """Update the history display in the UI"""
        try:
            # Get the last conversation
            if self.conversation_history:
                last_user, last_ai = self.conversation_history[-1]
                
                # Update input and response fields
                self.input_text.value = last_user
                self.response_text.value = last_ai
                
                # Extract and update code if present
                code = self.extract_code(last_ai)
                if code:
                    self.current_code = code
                    self.code_text.value = code
                    
                logger.info("History display updated")
        except Exception as e:
            logger.error(f"Error updating history display: {e}", exc_info=True)
            
    def extract_code(self, response_text):
        """Extract Python code from response text"""
        try:
            match = re.search(r"```python\n(.*?)\n```", response_text, re.DOTALL)
            return match.group(1).strip() if match else None
            except Exception as e:
            logger.error(f"Error extracting code: {e}", exc_info=True)
            return None
            
    def generate_response(self, prompt, error_info=None):
        """Generate AI response using OpenAI API"""
        try:
            system_instruction = (
                "You are an AI assistant that generates and executes Python code. "
                "For app launches, use system commands like 'start whatsapp://' (Windows) "
                "or 'open -a WhatsApp' (macOS). Never use absolute file paths. "
                "If you encounter an error related to missing dependencies, install them first and then run the code again."
                "Current system is windows"
            )
            
            messages = [
                {
                    "role": "system", 
                    "content": system_instruction
                }
            ]
            
            # Add conversation history
            for user_msg, ai_resp in self.conversation_history[-3:]:
                messages.extend([
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": ai_resp}
                ])
                
            current_prompt = f"{prompt}\n\nError:\n{error_info}" if error_info else prompt
            messages.append({"role": "user", "content": current_prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            ai_response = response.choices[0].message.content
            self.conversation_history.append((prompt, ai_response))
            self.save_conversation_history()
            
            return ai_response
            
        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

def main(page: Page):
    app = VoiceAssistantApp(page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)