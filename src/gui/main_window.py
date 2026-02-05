import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import asyncio
import os
import tempfile
import sys
import webbrowser

# Ensure src is in path if running directly (though main.py will handle this)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.tts_manager import TTSManager
from src.core.audio_player import AudioPlayer
from src.utils.file_handler import read_file
from src.utils.config_manager import ConfigManager

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Ứng dụng TTS (Edge TTS) - v1.1")
        self.geometry("950x750")

        # Apply Theme
        style = ttk.Style()
        style.theme_use('clam') # Modern looking theme

        # Backend Init
        self.tts = TTSManager()
        self.player = AudioPlayer()
        self.temp_file = os.path.join(tempfile.gettempdir(), "tts_preview.mp3")
        self.voices_data = []

        # Config Init
        self.config = ConfigManager.load_config()

        # Chapter management
        self.current_chapters = []
        self.is_epub_loaded = False

        # Configure grid weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.create_widgets()
        self.bind_shortcuts()

        # Load voices
        self.status_var.set("Đang tải giọng đọc...")
        threading.Thread(target=self.load_voices, daemon=True).start()

        # Clean exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- Top Frame: File Loading and Chapter Split ---
        top_frame = ttk.Frame(self, padding=10)
        top_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(top_frame, text="Nhập văn bản hoặc tải file:").pack(side="left")
        self.btn_load = ttk.Button(top_frame, text="Chọn File (.txt, .epub)", command=self.load_file_action)
        self.btn_load.pack(side="right")

        self.var_split_chapters = tk.BooleanVar()
        self.chk_split = ttk.Checkbutton(
            top_frame,
            text="Tách chương (EPUB)",
            variable=self.var_split_chapters,
            command=self.on_split_toggle
        )
        self.chk_split.pack(side="right", padx=10)

        # --- Chapter Selection (Hidden by default) ---
        self.frame_chapters = ttk.Frame(self, padding=5)
        self.frame_chapters.grid(row=0, column=0, sticky="s")
        self.frame_chapters.grid_forget()

        ttk.Label(self.frame_chapters, text="Chọn chương:").pack(side="left")
        self.combo_chapters = ttk.Combobox(self.frame_chapters, state="readonly", width=50)
        self.combo_chapters.pack(side="left", padx=5)
        self.combo_chapters.bind("<<ComboboxSelected>>", self.on_chapter_selected)

        # --- Middle Frame: Text Area ---
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Arial", 12))
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(self, text="Tùy chọn", padding=10)
        settings_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Voice Selection
        ttk.Label(settings_frame, text="Giọng đọc:").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_voice = ttk.Combobox(settings_frame, state="readonly", width=50)
        self.combo_voice.grid(row=0, column=1, padx=5, sticky="w")

        # Rate Slider
        ttk.Label(settings_frame, text="Tốc độ:").grid(row=1, column=0, padx=5, sticky="w")
        self.scale_rate = ttk.Scale(settings_frame, from_=0.5, to=2.0, value=self.config.get("rate", 1.0), command=self.update_rate_label)
        self.scale_rate.grid(row=1, column=1, padx=5, sticky="ew")
        self.lbl_rate_val = ttk.Label(settings_frame, text=f"{self.config.get('rate', 1.0)}x")
        self.lbl_rate_val.grid(row=1, column=2, padx=5, sticky="w")

        # Volume Slider
        ttk.Label(settings_frame, text="Âm lượng:").grid(row=2, column=0, padx=5, sticky="w")
        self.scale_volume = ttk.Scale(settings_frame, from_=0, to=100, value=self.config.get("volume", 100), command=self.update_volume_label)
        self.scale_volume.grid(row=2, column=1, padx=5, sticky="ew")
        self.lbl_volume_val = ttk.Label(settings_frame, text=f"{int(self.config.get('volume', 100))}%")
        self.lbl_volume_val.grid(row=2, column=2, padx=5, sticky="w")

        settings_frame.columnconfigure(1, weight=1)

        # --- Bottom Frame: Controls and Progress ---
        control_frame = ttk.Frame(self, padding=10)
        control_frame.grid(row=3, column=0, sticky="ew")

        # Progress Bar
        self.progress = ttk.Progressbar(control_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side="bottom", fill="x", pady=5)

        # Buttons
        self.btn_play = ttk.Button(control_frame, text="Phát (F5)", command=self.play_action)
        self.btn_play.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(control_frame, text="Dừng (F6)", command=self.stop_action)
        self.btn_stop.pack(side="left", padx=5)

        self.btn_save = ttk.Button(control_frame, text="Lưu MP3 (Ctrl+S)", command=self.save_action)
        self.btn_save.pack(side="right", padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=4, column=0, sticky="ew")

    def bind_shortcuts(self):
        self.bind("<F5>", lambda event: self.play_action())
        self.bind("<F6>", lambda event: self.stop_action())
        self.bind("<Control-s>", lambda event: self.save_action())

    def update_rate_label(self, val):
        self.lbl_rate_val.config(text=f"{float(val):.1f}x")

    def update_volume_label(self, val):
        self.lbl_volume_val.config(text=f"{int(float(val))}%")

    def load_voices(self):
        try:
            voices = asyncio.run(self.tts.get_voices())
            self.after(0, self.update_voice_list, voices)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi", f"Không tải được giọng đọc: {e}"))

    def update_voice_list(self, voices):
        self.voices_data = voices
        voice_values = []
        target_voice_shortname = self.config.get("voice", "")
        target_index = 0

        for i, v in enumerate(voices):
            name = v.get('ShortName', 'Unknown')
            locale = v.get('Locale', 'Unknown')
            gender = v.get('Gender', '')
            display = f"{name} ({gender}, {locale})"
            voice_values.append(display)

            # Check if this matches saved preference
            if target_voice_shortname and name == target_voice_shortname:
                # We can't set index easily after sorting unless we track it differently.
                # So we will just look it up after sort.
                pass

        # Custom Sort
        def sort_key(s):
            if "vi-VN" in s: return (0, s)
            if "en-US" in s: return (1, s)
            return (2, s)

        voice_values.sort(key=sort_key)
        self.combo_voice['values'] = voice_values

        # Try to restore selection
        if voice_values:
            self.combo_voice.current(0) # Default
            if target_voice_shortname:
                for idx, val in enumerate(voice_values):
                    if val.startswith(target_voice_shortname):
                        self.combo_voice.current(idx)
                        break

        self.status_var.set("Sẵn sàng")

    def load_file_action(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text/Epub Files", "*.txt *.epub"), ("All Files", "*.*")]
        )
        if filepath:
            self.current_filepath = filepath
            self.reload_file_content()

    def reload_file_content(self):
        if not hasattr(self, 'current_filepath') or not self.current_filepath:
            return

        split_chapters = self.var_split_chapters.get()
        is_epub = self.current_filepath.lower().endswith('.epub')
        self.is_epub_loaded = is_epub

        if is_epub and split_chapters:
             self.frame_chapters.grid(row=0, column=0, sticky="s", pady=(40,0))
        else:
             self.frame_chapters.grid_forget()

        try:
            content = read_file(self.current_filepath, split_chapters=(split_chapters and is_epub))

            self.text_area.delete("1.0", tk.END)

            if isinstance(content, list):
                self.current_chapters = content
                chapter_titles = [c['title'] for c in content]
                self.combo_chapters['values'] = chapter_titles
                if chapter_titles:
                    self.combo_chapters.current(0)
                    self.on_chapter_selected(None)
                self.frame_chapters.grid(row=1, column=0, sticky="n", pady=5)
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(40, 5))
            else:
                self.current_chapters = []
                self.text_area.insert("1.0", content)
                self.frame_chapters.grid_forget()
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

            self.status_var.set(f"Đã tải: {os.path.basename(self.current_filepath)}")

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_split_toggle(self):
        if hasattr(self, 'current_filepath'):
             self.reload_file_content()

    def on_chapter_selected(self, event):
        idx = self.combo_chapters.current()
        if idx >= 0 and idx < len(self.current_chapters):
            chapter = self.current_chapters[idx]
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", chapter['content'])

    def get_settings(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập nội dung.")
            return None

        voice_str = self.combo_voice.get()
        if not voice_str:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn giọng đọc.")
            return None

        voice = voice_str.split(" ")[0]

        rate = float(self.scale_rate.get())
        volume = int(float(self.scale_volume.get()))

        return text, voice, rate, volume

    def play_action(self):
        settings = self.get_settings()
        if not settings:
            return

        text, voice, rate, volume = settings

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang tạo âm thanh (Play)...")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)

        threading.Thread(target=self.run_tts_play, args=(text, voice, rate, volume), daemon=True).start()

    def run_tts_play(self, text, voice, rate, volume):
        try:
            try:
                self.player.stop()
            except:
                pass

            asyncio.run(self.tts.save_audio(text, voice, rate, volume, self.temp_file))
            self.after(0, self.start_playback)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi TTS", str(e)))
            self.after(0, self.reset_ui_state)

    def start_playback(self):
        try:
            self.player.load(self.temp_file)
            self.player.play()
            self.status_var.set("Đang phát...")
            self.reset_ui_state()
        except Exception as e:
            messagebox.showerror("Lỗi Player", str(e))
            self.reset_ui_state()

    def stop_action(self):
        self.player.stop()
        self.status_var.set("Đã dừng.")
        self.progress.stop()
        self.progress.config(mode="determinate", value=0)

    def save_action(self):
        if self.var_split_chapters.get() and self.current_chapters:
             self.save_chapters_action()
             return

        settings = self.get_settings()
        if not settings:
            return

        text, voice, rate, volume = settings

        filepath = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Files", "*.mp3")]
        )
        if not filepath:
            return

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang lưu file...")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)

        threading.Thread(target=self.run_tts_save, args=(text, voice, rate, volume, filepath), daemon=True).start()

    def save_chapters_action(self):
        directory = filedialog.askdirectory(title="Chọn thư mục để lưu các chương")
        if not directory:
            return

        voice_str = self.combo_voice.get()
        if not voice_str: return
        voice = voice_str.split(" ")[0]
        rate = float(self.scale_rate.get())
        volume = int(float(self.scale_volume.get()))

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang lưu hàng loạt...")
        self.progress.config(mode="determinate", maximum=len(self.current_chapters), value=0)

        threading.Thread(
            target=self.run_tts_save_batch,
            args=(self.current_chapters, voice, rate, volume, directory),
            daemon=True
        ).start()

    def run_tts_save_batch(self, chapters, voice, rate, volume, directory):
        try:
            total = len(chapters)
            for i, chapter in enumerate(chapters):
                title = chapter['title']
                text = chapter['content']
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
                filename = f"{i+1:02d}_{safe_title}.mp3"
                filepath = os.path.join(directory, filename)

                self.after(0, lambda idx=i: self.status_var.set(f"Đang lưu ({idx+1}/{total}): {filename}"))
                self.after(0, lambda idx=i: self.progress.config(value=idx+1))

                asyncio.run(self.tts.save_audio(text, voice, rate, volume, filepath))

            self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu {total} file tại:\n{directory}"))
        except Exception as e:
             self.after(0, lambda: messagebox.showerror("Lỗi Batch Save", str(e)))
        finally:
            self.after(0, self.reset_ui_state)
            self.after(0, lambda: self.status_var.set("Sẵn sàng"))

    def run_tts_save(self, text, voice, rate, volume, filepath):
        try:
            asyncio.run(self.tts.save_audio(text, voice, rate, volume, filepath))
            self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu file tại:\n{filepath}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi Lưu File", str(e)))
        finally:
            self.after(0, self.reset_ui_state)
            self.after(0, lambda: self.status_var.set("Sẵn sàng"))

    def reset_ui_state(self):
        self.btn_play.config(state="normal")
        self.btn_save.config(state="normal")
        self.progress.stop()
        self.progress.config(value=0)

    def on_closing(self):
        # Save config
        voice_str = self.combo_voice.get()
        if voice_str:
            self.config["voice"] = voice_str.split(" ")[0]

        self.config["rate"] = self.scale_rate.get()
        self.config["volume"] = self.scale_volume.get()

        ConfigManager.save_config(self.config)
        self.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
