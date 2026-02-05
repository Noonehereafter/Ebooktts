import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import asyncio
import os
import tempfile
import sys

# Ensure src is in path if running directly (though main.py will handle this)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.tts_manager import TTSManager
from src.core.audio_player import AudioPlayer
from src.utils.file_handler import read_file

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Ứng dụng TTS (Edge TTS)")
        self.geometry("900x700")

        # Backend Init
        self.tts = TTSManager()
        self.player = AudioPlayer()
        self.temp_file = os.path.join(tempfile.gettempdir(), "tts_preview.mp3")
        self.voices_data = []

        # Chapter management
        self.current_chapters = [] # List of {'title': str, 'content': str}
        self.is_epub_loaded = False

        # Configure grid weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.create_widgets()

        # Load voices
        self.status_var.set("Đang tải giọng đọc...")
        threading.Thread(target=self.load_voices, daemon=True).start()

    def create_widgets(self):
        # Top Frame: File Loading and Chapter Split
        top_frame = ttk.Frame(self, padding=10)
        top_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(top_frame, text="Nhập văn bản hoặc tải file:").pack(side="left")
        self.btn_load = ttk.Button(top_frame, text="Chọn File (.txt, .epub)", command=self.load_file_action)
        self.btn_load.pack(side="right")

        # Checkbox for Split Chapters
        self.var_split_chapters = tk.BooleanVar()
        self.chk_split = ttk.Checkbutton(
            top_frame,
            text="Tách chương (EPUB)",
            variable=self.var_split_chapters,
            command=self.on_split_toggle
        )
        self.chk_split.pack(side="right", padx=10)

        # Chapter Selection (Hidden by default)
        self.frame_chapters = ttk.Frame(self, padding=5)
        self.frame_chapters.grid(row=0, column=0, sticky="s") # Put it below top frame logic if needed, but let's re-arrange slightly or just insert row
        # Actually better to put it below the top frame.
        self.frame_chapters.grid_forget() # Hide initially

        ttk.Label(self.frame_chapters, text="Chọn chương:").pack(side="left")
        self.combo_chapters = ttk.Combobox(self.frame_chapters, state="readonly", width=50)
        self.combo_chapters.pack(side="left", padx=5)
        self.combo_chapters.bind("<<ComboboxSelected>>", self.on_chapter_selected)


        # Middle Frame: Text Area
        # Update row index because we might want chapter frame in between
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Arial", 12))
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Settings Frame
        settings_frame = ttk.LabelFrame(self, text="Tùy chọn", padding=10)
        settings_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Voice Selection
        ttk.Label(settings_frame, text="Giọng đọc:").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_voice = ttk.Combobox(settings_frame, state="readonly", width=50)
        self.combo_voice.grid(row=0, column=1, padx=5, sticky="w")

        # Rate Slider
        ttk.Label(settings_frame, text="Tốc độ:").grid(row=1, column=0, padx=5, sticky="w")
        self.scale_rate = ttk.Scale(settings_frame, from_=0.5, to=2.0, value=1.0, command=self.update_rate_label)
        self.scale_rate.grid(row=1, column=1, padx=5, sticky="ew")
        self.lbl_rate_val = ttk.Label(settings_frame, text="1.0x")
        self.lbl_rate_val.grid(row=1, column=2, padx=5, sticky="w")

        # Volume Slider
        ttk.Label(settings_frame, text="Âm lượng:").grid(row=2, column=0, padx=5, sticky="w")
        self.scale_volume = ttk.Scale(settings_frame, from_=0, to=100, value=100, command=self.update_volume_label)
        self.scale_volume.grid(row=2, column=1, padx=5, sticky="ew")
        self.lbl_volume_val = ttk.Label(settings_frame, text="100%")
        self.lbl_volume_val.grid(row=2, column=2, padx=5, sticky="w")

        settings_frame.columnconfigure(1, weight=1)

        # Bottom Frame: Controls
        control_frame = ttk.Frame(self, padding=10)
        control_frame.grid(row=3, column=0, sticky="ew")

        self.btn_play = ttk.Button(control_frame, text="Phát", command=self.play_action)
        self.btn_play.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(control_frame, text="Dừng", command=self.stop_action)
        self.btn_stop.pack(side="left", padx=5)

        self.btn_save = ttk.Button(control_frame, text="Lưu MP3", command=self.save_action)
        self.btn_save.pack(side="right", padx=5)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=4, column=0, sticky="ew")

    # ... Rest of methods will be updated in next step ...
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
        for v in voices:
            name = v.get('ShortName', 'Unknown')
            locale = v.get('Locale', 'Unknown')
            gender = v.get('Gender', '')
            display = f"{name} ({gender}, {locale})"
            voice_values.append(display)

        def sort_key(s):
            if "vi-VN" in s: return (0, s)
            if "en-US" in s: return (1, s)
            return (2, s)

        voice_values.sort(key=sort_key)

        self.combo_voice['values'] = voice_values
        if voice_values:
            self.combo_voice.current(0)
        self.status_var.set("Sẵn sàng")

    def load_file_action(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text/Epub Files", "*.txt *.epub"), ("All Files", "*.*")]
        )
        if filepath:
            self.current_filepath = filepath
            self.reload_file_content()

    def reload_file_content(self):
        """Reloads file content based on split setting."""
        if not hasattr(self, 'current_filepath') or not self.current_filepath:
            return

        split_chapters = self.var_split_chapters.get()
        is_epub = self.current_filepath.lower().endswith('.epub')
        self.is_epub_loaded = is_epub

        # Toggle UI visibility based on file type
        if is_epub and split_chapters:
             # Show chapter selection, insert it into grid
             # We put it at row 0 but sticky south, effectively making it a sub-toolbar
             # Or we can just pack it into top_frame? No, separate logic.
             # Let's adjust grid
             self.frame_chapters.grid(row=0, column=0, sticky="s", pady=(40,0)) # Offset to avoid overlap
             # Or better, shift everything down?
             # Let's just assume simple layout update for now.
             pass
        else:
             self.frame_chapters.grid_forget()

        try:
            content = read_file(self.current_filepath, split_chapters=(split_chapters and is_epub))

            self.text_area.delete("1.0", tk.END)

            if isinstance(content, list): # Chapters
                self.current_chapters = content
                chapter_titles = [c['title'] for c in content]
                self.combo_chapters['values'] = chapter_titles
                if chapter_titles:
                    self.combo_chapters.current(0)
                    self.on_chapter_selected(None) # Load first chapter
                self.frame_chapters.grid(row=1, column=0, sticky="n", pady=5) # Place above text area
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(40, 5)) # Push text area down
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

    def save_action(self):
        # Special handling for Split Mode
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

        threading.Thread(target=self.run_tts_save, args=(text, voice, rate, volume, filepath), daemon=True).start()

    def save_chapters_action(self):
        directory = filedialog.askdirectory(title="Chọn thư mục để lưu các chương")
        if not directory:
            return

        # Settings
        voice_str = self.combo_voice.get()
        if not voice_str: return
        voice = voice_str.split(" ")[0]
        rate = float(self.scale_rate.get())
        volume = int(float(self.scale_volume.get()))

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang lưu hàng loạt...")

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

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
