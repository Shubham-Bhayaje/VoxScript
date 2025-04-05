import os
import subprocess
import re
import tkinter as tk
import speech_recognition as sr
import pyttsx3
from tkinter import scrolledtext, Button, Frame, Label, ttk, messagebox, filedialog
from openai import OpenAI
import threading
import time
import keyboard
import json
from dotenv import load_dotenv


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

def log_message(message, level="INFO"):
    """Log messages to file with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as log_file:
        log_file.write(f"[{timestamp}] [{level}] {message}\n")

class VoiceAssistantGUI:
    def __init__(self, root):
        print("📦 Initializing VoiceAssistantGUI...")
        self.root = root
        self.root.title("VoxScript Voice Assistant")
        self.root.geometry("800x600")
        
   
        try:
            icon_path = os.path.join(BASE_DIR, "assets", "mic_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Couldn't load icon: {e}")

        self.current_code = ""
        self.is_processing = False
        self.is_listening = False
        self.is_reading = False
        self.stop_listening_event = threading.Event()
        self.stop_reading_event = threading.Event()
        self.listen_thread = None
        self.read_thread = None
        self.current_script_path = None
        self.model_name = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 2000

      
        self.setup_ui()

        keyboard.add_hotkey('ctrl+j', self.toggle_listening)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        
   
        self.conversation_history = self.load_conversation_history()
        self.load_settings()
        
        self.update_ui_state()

        

        self.root.bind('<Control-j>', lambda event: self.start_listening())
        self.root.bind('<Control-J>', lambda event: self.start_listening()) 
    
        print("✅ VoiceAssistantGUI initialized successfully")

    def on_close(self):
        """Clean up resources when closing"""
        keyboard.unhook_all_hotkeys() 
        self.root.destroy()

    def toggle_listening(self):
        """Toggle speech recognition on/off (called by button or Ctrl+J)"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
       
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)

    def setup_ui(self):
        """Set up all UI components"""
       
        self.main_frame = Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
       
        self.setup_menu()
        
       
        self.title_label = Label(self.main_frame, 
                               text="VoxScript Voice Assistant", 
                               font=("Arial", 18, "bold"), 
                               bg="#f0f0f0")
        self.title_label.pack(pady=10)
        
        self.status_label = Label(self.main_frame, 
                                text="Ready", 
                                font=("Arial", 10), 
                                bg="#f0f0f0")
        self.status_label.pack()
        
      
        self.mic_button = Button(
            self.main_frame,
            text="🎤 Start Listening",
            font=("Arial", 14),
            command=self.toggle_listening,
            bg="#4CAF50",
            fg="white",
            width=20
        )
        self.mic_button.pack(pady=10)
        
      
        self.progress = ttk.Progressbar(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='indeterminate'
        )
        
       
        self.setup_tabs()
        
       
        self.setup_action_buttons()
        
       
        self.status_bar = Label(
            self.root, 
            text="Ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_menu(self):
        """Set up the application menu bar"""
        menubar = tk.Menu(self.root)
        
       
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Save Code", command=self.save_code)
        file_menu.add_command(label="Load Code", command=self.load_code)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy Code", command=lambda: self.copy_to_clipboard(self.code_text))
        edit_menu.add_command(label="Copy Response", command=lambda: self.copy_to_clipboard(self.response_text))
        edit_menu.add_command(label="Copy Output", command=lambda: self.copy_to_clipboard(self.output_text))
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear History", command=self.clear_history)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
       
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

    def setup_tabs(self):
        """Set up the tabbed interface"""
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[10, 5])
        
        self.tab_control = ttk.Notebook(self.main_frame)
        
       
        self.input_tab = Frame(self.tab_control)
        self.tab_control.add(self.input_tab, text="Input")
        
        self.input_label = Label(
            self.input_tab, 
            text="Your Voice Input:", 
            font=("Arial", 12, "bold")
        )
        self.input_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.input_text = scrolledtext.ScrolledText(
            self.input_tab, 
            height=5, 
            font=("Arial", 11)
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
     
        self.response_tab = Frame(self.tab_control)
        self.tab_control.add(self.response_tab, text="AI Response")
        
        self.response_label = Label(
            self.response_tab, 
            text="AI Response:", 
            font=("Arial", 12, "bold")
        )
        self.response_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.response_text = scrolledtext.ScrolledText(
            self.response_tab, 
            height=10, 
            font=("Arial", 11)
        )
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
      
        self.code_tab = Frame(self.tab_control)
        self.tab_control.add(self.code_tab, text="Generated Code")
        
        self.code_label = Label(
            self.code_tab, 
            text="Generated Python Code:", 
            font=("Arial", 12, "bold")
        )
        self.code_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.code_text = scrolledtext.ScrolledText(
            self.code_tab, 
            height=15, 
            font=("Consolas", 11)
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.code_text.config(state=tk.DISABLED) 
        
    
        self.output_tab = Frame(self.tab_control)
        self.tab_control.add(self.output_tab, text="Execution Output")
        
        self.output_label = Label(
            self.output_tab, 
            text="Execution Result:", 
            font=("Arial", 12, "bold")
        )
        self.output_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.output_text = scrolledtext.ScrolledText(
            self.output_tab, 
            height=10, 
            font=("Arial", 11)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_action_buttons(self):
        """Set up action buttons"""
        button_frame = Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        self.execute_button = Button(
            button_frame,
            text="Execute Code",
            command=self.execute_current_code,
            bg="#2196F3",
            fg="white",
            width=15
        )
        self.execute_button.pack(side=tk.LEFT, padx=5)
        
        self.read_button = Button(
            button_frame,
            text="Read Response",
            command=self.read_response,
            bg="#FF9800",
            fg="white",
            width=15
        )
        self.read_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_read_button = Button(
            button_frame,
            text="Stop Reading",
            command=self.stop_reading,
            bg="#f44336",
            fg="white",
            width=15,
            state=tk.DISABLED
        )
        self.stop_read_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = Button(
            button_frame,
            text="Clear All",
            command=self.clear_all,
            bg="#9E9E9E",
            fg="white",
            width=15
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def update_ui_state(self):
        """Update UI elements based on current state"""
        state = tk.NORMAL if not self.is_processing else tk.DISABLED
        
        self.execute_button.config(state=state)
        self.read_button.config(state=state)
        self.clear_button.config(state=state)
        
        self.mic_button.config(
            state=tk.NORMAL if not self.is_processing else tk.DISABLED
        )
        
        self.stop_read_button.config(
            state=tk.NORMAL if self.is_reading else tk.DISABLED
        )

    def toggle_listening(self):
        """Toggle speech recognition on/off"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self, event=None):
        """Start speech recognition (can be triggered by Ctrl+J)"""
        if self.is_listening:  
            return
            
        self.is_listening = True
        self.stop_listening_event.clear()
        self.mic_button.config(text="🛑 Stop Listening", bg="#f44336")
        self.update_status("Listening... Speak now")
        
        self.listen_thread = threading.Thread(target=self.listen_for_voice)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False
        self.stop_listening_event.set()
        self.mic_button.config(text="🎤 Start Listening", bg="#4CAF50")
        self.update_status("Stopped listening")

    def listen_for_voice(self):
        """Listen for voice input and process it"""
        full_text = ""
        last_speech_time = time.time()
        silence_threshold = 2.0 
        
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                recognizer.pause_threshold = 0.8
                
                while self.is_listening and not self.stop_listening_event.is_set():
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        text = recognizer.recognize_google(audio)
                        last_speech_time = time.time()
                        
                        if text:
                            full_text = f"{full_text} {text}".strip()
                            self.root.after(0, lambda: self.input_text.delete(1.0, tk.END))
                            self.root.after(0, lambda: self.input_text.insert(tk.END, full_text))
                            self.update_status(f"Heard: {text}")
                            
                    except sr.WaitTimeoutError:
                        if full_text and (time.time() - last_speech_time > silence_threshold):
                            break
                    except sr.UnknownValueError:
                        self.update_status("Could not understand audio")
                    except Exception as e:
                        self.update_status(f"Recognition error: {str(e)}")
                        log_message(f"Recognition error: {str(e)}", "ERROR")
                        
                    if full_text and (time.time() - last_speech_time > silence_threshold):
                        break
                        
        except Exception as e:
            self.update_status(f"Error in speech recognition: {str(e)}")
            log_message(f"Error in speech recognition: {str(e)}", "ERROR")
        
        finally:
            if full_text:
                self.root.after(0, lambda: self.process_input(full_text))
            self.stop_listening()

    def process_input(self, user_input):
        """Process user input and generate AI response"""
        if not user_input or self.is_processing:
            return
            
        self.is_processing = True
        self.update_ui_state()
        self.progress.pack(pady=5)
        self.progress.start()
        
        threading.Thread(
            target=self._process_input_thread, 
            args=(user_input,),
            daemon=True
        ).start()

    def _process_input_thread(self, user_input):
        """Thread for processing input and generating response"""
        try:
            self.update_status(f"Processing: {user_input[:50]}...")
            log_message(f"Processing user input: {user_input}")
            
            response = self.generate_response(user_input)
            self.root.after(0, lambda: self.update_response_text(response))
            
            code = self.extract_code(response)
            if code:
                self.current_code = code
                self.root.after(0, lambda: self.update_code_text(code))
                self.root.after(0, lambda: self.save_and_execute_code(code, user_input))
            else:
                self.update_status("No code found in response")
                self.root.after(0, self.read_response)
                
            self.root.after(0, self.update_history_display)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            log_message(f"Error in processing input: {str(e)}", "ERROR")
            
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            self.is_processing = False
            self.root.after(0, self.update_ui_state)

    def generate_response(self, prompt, error_info=None):
        """Generate AI response using OpenAI API"""
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
        
      
        for user_msg, ai_resp in self.conversation_history[-3:]:
            messages.extend([
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": ai_resp}
            ])
            
        current_prompt = f"{prompt}\n\nError:\n{error_info}" if error_info else prompt
        messages.append({"role": "user", "content": current_prompt})
        
        try:
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
            log_message(error_msg, "ERROR")
            return error_msg

    def extract_code(self, response_text):
        """Extract Python code from response text"""
        match = re.search(r"```python\n(.*?)\n```", response_text, re.DOTALL)
        return match.group(1).strip() if match else None

    def save_and_execute_code(self, code, user_input, retry_count=0):
        """Save code to file and execute it"""
        if retry_count >= 3:
            self.update_status("Max retries reached")
            return
            
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            script_name = f"script_{timestamp}.py"
            self.current_script_path = os.path.join(SCRIPTS_DIR, script_name)
            
            with open(self.current_script_path, 'w') as f:
                f.write(code)
                
            self.update_status(f"Executing {script_name}...")
            
            result = subprocess.run(
                ["python", self.current_script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stderr:
                error = result.stderr
                self.update_status(f"Error: {error[:100]}...")
                self.update_output_text(f"ERROR:\n{error}")
                
              
                fixed_response = self.generate_response(
                    user_input,
                    f"Previous code failed with error:\n{error}\nPlease fix it."
                )
                fixed_code = self.extract_code(fixed_response)
                
                if fixed_code:
                    self.update_code_text(fixed_code)
                    self.current_code = fixed_code
                    self.save_and_execute_code(fixed_code, user_input, retry_count + 1)
            else:
                output = result.stdout or "Code executed successfully with no output"
                self.update_output_text(output)
                self.update_status("Execution complete")
                self.tab_control.select(3)  
                
        except subprocess.TimeoutExpired:
            self.update_status("Execution timed out (30s)")
            self.update_output_text("ERROR: Execution timed out after 30 seconds")
        except Exception as e:
            self.update_status(f"Execution error: {str(e)}")
            self.update_output_text(f"ERROR:\n{str(e)}")

    def execute_current_code(self):
        """Execute the currently displayed code"""
        current_code = self.code_text.get(1.0, tk.END).strip()
        if not current_code:
            self.update_status("No code to execute")
            return
            
        self.current_code = current_code
        self.save_and_execute_code(current_code, self.input_text.get(1.0, tk.END).strip())

    def read_response(self):
        """Read the AI response aloud"""
        if self.is_reading:
            return
            
        response = self.response_text.get(1.0, tk.END).strip()
        if not response:
            self.update_status("No response to read")
            return
            
        self.is_reading = True
        self.stop_reading_event.clear()
        self.update_ui_state()
        
        self.read_thread = threading.Thread(
            target=self._read_text,
            args=(response,),
            daemon=True
        )
        self.read_thread.start()

    def stop_reading(self):
        """Stop the text-to-speech reading"""
        if self.is_reading:
            self.stop_reading_event.set()
            self.update_status("Stopping speech...")

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
                
            self.update_status("Finished reading")
        except Exception as e:
            self.update_status(f"Reading error: {str(e)}")
        finally:
            self.is_reading = False
            self.stop_reading_event.clear()
            self.root.after(0, self.update_ui_state)

    def clear_all(self):
        """Clear all text fields"""
        self.input_text.delete(1.0, tk.END)
        self.response_text.delete(1.0, tk.END)
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete(1.0, tk.END)
        self.code_text.config(state=tk.DISABLED)
        self.output_text.delete(1.0, tk.END)
        self.current_code = ""
        self.current_script_path = None
        self.update_status("All cleared")

    def update_response_text(self, text):
        """Update the response text area"""
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, text)
        self.tab_control.select(1) 

    def update_code_text(self, text):
        """Update the code text area"""
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(tk.END, text)
        self.code_text.config(state=tk.DISABLED)
        self.tab_control.select(2)  

    def update_output_text(self, text):
        """Update the output text area"""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)

    def update_status(self, message):
        """Update status bar and label"""
        self.root.after(0, lambda: self.status_label.config(text=message))
        self.root.after(0, lambda: self.status_bar.config(text=message))
        print(f"Status: {message}")

    def load_conversation_history(self):
        """Load conversation history from file"""
        if os.path.exists(HISTORY_PATH):
            try:
                with open(HISTORY_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_message(f"Error loading history: {str(e)}", "ERROR")
        return []

    def save_conversation_history(self):
        """Save conversation history to file"""
        try:
            with open(HISTORY_PATH, 'w') as f:
                json.dump(self.conversation_history, f)
        except Exception as e:
            log_message(f"Error saving history: {str(e)}", "ERROR")

    def update_history_display(self):
        """Update the history list display"""
        pass  

    def load_settings(self):
        """Load application settings from config file"""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    self.model_name = config.get("model_name", self.model_name)
                    self.temperature = config.get("temperature", self.temperature)
                    self.max_tokens = config.get("max_tokens", self.max_tokens)
            except Exception as e:
                log_message(f"Error loading settings: {str(e)}", "ERROR")

    def save_settings(self, settings):
        """Save settings to config file"""
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            log_message(f"Error saving settings: {str(e)}", "ERROR")

    def open_settings(self):
        """Open settings dialog"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x300")
        
        
        tk.Label(settings_win, text="Model:").pack()
        model_var = tk.StringVar(value=self.model_name)
        model_menu = ttk.Combobox(
            settings_win, 
            textvariable=model_var,
            values=["gpt-4o"]
        )
        model_menu.pack()
        
        
        tk.Label(settings_win, text="Temperature:").pack()
        temp_var = tk.DoubleVar(value=self.temperature)
        tk.Scale(
            settings_win, 
            from_=0.0, 
            to=1.0, 
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=temp_var
        ).pack()
        
       
        tk.Label(settings_win, text="Max Tokens:").pack()
        tokens_var = tk.IntVar(value=self.max_tokens)
        tk.Entry(settings_win, textvariable=tokens_var).pack()
        
        
        tk.Button(
            settings_win,
            text="Save",
            command=lambda: self._save_settings_and_close(
                settings_win,
                model_var.get(),
                temp_var.get(),
                tokens_var.get()
            )
        ).pack(pady=10)

    def _save_settings_and_close(self, window, model, temp, tokens):
        """Save settings and close window"""
        self.model_name = model
        self.temperature = temp
        self.max_tokens = tokens
        
        self.save_settings({
            "model_name": model,
            "temperature": temp,
            "max_tokens": tokens
        })
        
        window.destroy()
        self.update_status("Settings saved")

    def new_session(self):
        """Start a new session"""
        if messagebox.askyesno("New Session", "Start a new session? Current work will be cleared."):
            self.clear_all()
            self.update_status("New session started")

    def save_code(self):
        """Save current code to file"""
        if not self.current_code:
            messagebox.showinfo("No Code", "There is no code to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialdir=SCRIPTS_DIR
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.current_code)
                self.update_status(f"Code saved to {file_path}")
                self.current_script_path = file_path
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def load_code(self):
        """Load code from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialdir=SCRIPTS_DIR
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                self.code_text.config(state=tk.NORMAL)
                self.code_text.delete(1.0, tk.END)
                self.code_text.insert(tk.END, code)
                self.code_text.config(state=tk.DISABLED)
                
                self.current_code = code
                self.current_script_path = file_path
                self.update_status(f"Loaded {os.path.basename(file_path)}")
                self.tab_control.select(2)  
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")

    def copy_to_clipboard(self, text_widget):
        """Copy text widget content to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text_widget.get(1.0, tk.END))
        self.update_status("Copied to clipboard")

    def clear_history(self):
        """Clear conversation history"""
        if messagebox.askyesno("Clear History", "Clear all conversation history?"):
            self.conversation_history = []
            self.save_conversation_history()
            self.update_status("History cleared")

    def show_about(self):
        """Show about dialog"""
        about_win = tk.Toplevel(self.root)
        about_win.title("About VoxScript")
        about_win.geometry("300x200")
        
        tk.Label(
            about_win, 
            text="VoxScript Voice Assistant\n\nVersion 1.0\n\n© 2023",
            font=("Arial", 12),
            pady=20
        ).pack()
        
        tk.Button(
            about_win,
            text="OK",
            command=about_win.destroy
        ).pack()

    def show_instructions(self):
        """Show instructions dialog"""
        instructions_win = tk.Toplevel(self.root)
        instructions_win.title("Instructions")
        instructions_win.geometry("500x400")
        
        text = scrolledtext.ScrolledText(instructions_win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
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
        
        text.insert(tk.END, instructions)
        text.config(state=tk.DISABLED)
        
        tk.Button(
            instructions_win,
            text="Close",
            command=instructions_win.destroy
        ).pack(pady=10)

def on_closing(root):
    """Handle window closing event"""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
    keyboard.add_hotkey('ctrl+j', lambda: app.toggle_listening())

if __name__ == "__main__":
    main()