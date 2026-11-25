import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import re
from openai import OpenAI

class ChatBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chatbot Agent - Secure Mode")
        self.root.geometry("700x850")

        # Dark Theme Colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#333333"
        self.text_bg = "#252526"
        self.root.configure(bg=self.bg_color)

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("TButton", background=self.accent_color, foreground=self.fg_color)

        config_frame = ttk.Frame(self.root)
        config_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(config_frame, width=40)
        self.api_key_entry.grid(row=0, column=1, padx=5)

        ttk.Label(config_frame, text="Base URL:").grid(row=1, column=0, sticky="w")
        self.base_url_entry = ttk.Entry(config_frame, width=40)
        self.base_url_entry.insert(0, "http://localhost:11434/v1")
        self.base_url_entry.grid(row=1, column=1, padx=5)

        ttk.Label(config_frame, text="Model:").grid(row=2, column=0, sticky="w")
        self.model_entry = ttk.Entry(config_frame, width=40)
        self.model_entry.insert(0, "llama3")
        self.model_entry.grid(row=2, column=1, padx=5)

        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=self.text_bg, fg=self.fg_color,
            insertbackground="white", font=("Consolas", 11)
        )
        self.chat_display.pack(pady=10, padx=10, fill="both", expand=True)
        self.chat_display.config(state=tk.DISABLED)

        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, fill="x")

        self.user_input = ttk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self.send_message())

        send_btn = ttk.Button(input_frame, text="Invia", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)

    def append_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def request_permission(self, command):
        return messagebox.askyesno("Permesso Richiesto", f"L'IA vuole eseguire:\n\n{command}\n\nConcedi permesso?")

    def execute_system_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def send_message(self):
        user_text = self.user_input.get()
        if not user_text: return
        self.append_chat("Tu", user_text)
        self.user_input.delete(0, tk.END)

        try:
            client = OpenAI(api_key=self.api_key_entry.get(), base_url=self.base_url_entry.get())

            system_prompt = (
                "You are a Secure Windows PC AI Agent. "
                "Suggest actions using [CMD]command[/CMD]. "
                "If the user rejects a command, you will receive 'Action Rejected'. "
                "If rejected, apologize and suggest an alternative. Do not bypass permissions."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]

            response = client.chat.completions.create(model=self.model_entry.get(), messages=messages)
            ai_response = response.choices[0].message.content

            if "[CMD]" in ai_response and "[/CMD]" in ai_response:
                commands = re.findall(r"\[CMD\](.*?)\[/CMD\]", ai_response, re.DOTALL)

                for cmd in commands:
                    cmd = cmd.strip()
                    if self.request_permission(cmd):
                        self.append_chat("Agente", f"Eseguendo: {cmd}...")
                        result = self.execute_system_command(cmd)
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "system", "content": f"Command output: {result}"})
                    else:
                        self.append_chat("Sistema", f"Azione respinta: {cmd}")
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "system", "content": "Action Rejected: The user denied permission."})

                final_response = client.chat.completions.create(model=self.model_entry.get(), messages=messages)
                self.append_chat("AI", final_response.choices[0].message.content)
            else:
                self.append_chat("AI", ai_response)

        except Exception as e:
            messagebox.showerror("Errore", f"Errore: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatBotApp(root)
    root.mainloop()
