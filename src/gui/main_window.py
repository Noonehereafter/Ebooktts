import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, Menu
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

        self.title("Ứng dụng TTS (Edge TTS) - v1.3")
        self.geometry("950x800")

        # Apply Theme
        style = ttk.Style()
        style.theme_use('clam')

        # Backend Init
        self.tts = TTSManager()
        self.player = AudioPlayer()
        self.temp_file = os.path.join(tempfile.gettempdir(), "tts_preview.mp3")
        self.voices_data = []

        # Config Init
        self.config = ConfigManager.load_config()

        # State management
        self.current_chapters = []
        self.current_subtitle_segments = []
        self.is_epub_loaded = False
        self.is_subtitle_loaded = False

        # Configure grid weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.create_menu()
        self.create_widgets()
        self.bind_shortcuts()

        # Load voices
        self.status_var.set("Đang tải giọng đọc...")
        threading.Thread(target=self.load_voices, daemon=True).start()

        # Clean exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tệp (File)", menu=file_menu)

        file_menu.add_command(label="Mở File...", command=self.load_file_action)

        # Recent Files
        self.recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Mở Gần Đây", menu=self.recent_menu)
        self.update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.on_closing)

        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Chỉnh sửa", menu=edit_menu)
        edit_menu.add_command(label="Làm sạch văn bản", command=self.clean_text_action)

    def update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        recents = self.config.get("recent_files", [])
        if not recents:
            self.recent_menu.add_command(label="(Trống)", state="disabled")
        else:
            for filepath in recents:
                self.recent_menu.add_command(
                    label=os.path.basename(filepath),
                    command=lambda p=filepath: self.load_file_direct(p)
                )

    def create_widgets(self):
        # --- Top Frame: File Loading and Chapter Split ---
        top_frame = ttk.Frame(self, padding=10)
        top_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(top_frame, text="Nhập văn bản hoặc tải file:").pack(side="left")
        self.btn_load = ttk.Button(top_frame, text="Chọn File", command=self.load_file_action)
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
        # Bind text change to duration estimate
        self.text_area.bind('<<Modified>>', self.on_text_changed)

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(self, text="Tùy chọn", padding=10)
        settings_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Row 0
        ttk.Label(settings_frame, text="Giọng đọc:").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_voice = ttk.Combobox(settings_frame, state="readonly", width=50)
        self.combo_voice.grid(row=0, column=1, padx=5, sticky="w", columnspan=2)

        # Row 1
        ttk.Label(settings_frame, text="Tốc độ:").grid(row=1, column=0, padx=5, sticky="w")
        self.scale_rate = ttk.Scale(settings_frame, from_=0.5, to=2.0, value=self.config.get("rate", 1.0), command=self.update_rate_label)
        self.scale_rate.grid(row=1, column=1, padx=5, sticky="ew")
        self.lbl_rate_val = ttk.Label(settings_frame, text=f"{self.config.get('rate', 1.0)}x")
        self.lbl_rate_val.grid(row=1, column=2, padx=5, sticky="w")

        # Row 2
        ttk.Label(settings_frame, text="Âm lượng:").grid(row=2, column=0, padx=5, sticky="w")
        self.scale_volume = ttk.Scale(settings_frame, from_=0, to=100, value=self.config.get("volume", 100), command=self.update_volume_label)
        self.scale_volume.grid(row=2, column=1, padx=5, sticky="ew")
        self.lbl_volume_val = ttk.Label(settings_frame, text=f"{int(self.config.get('volume', 100))}%")
        self.lbl_volume_val.grid(row=2, column=2, padx=5, sticky="w")

        # Row 3 - Pitch
        ttk.Label(settings_frame, text="Cao độ (Hz):").grid(row=3, column=0, padx=5, sticky="w")
        self.scale_pitch = ttk.Scale(settings_frame, from_=-50, to=50, value=self.config.get("pitch", 0), command=self.update_pitch_label)
        self.scale_pitch.grid(row=3, column=1, padx=5, sticky="ew")
        self.lbl_pitch_val = ttk.Label(settings_frame, text=f"{int(self.config.get('pitch', 0))}Hz")
        self.lbl_pitch_val.grid(row=3, column=2, padx=5, sticky="w")

        settings_frame.columnconfigure(1, weight=1)

        # --- Bottom Frame: Controls and Progress ---
        control_frame = ttk.Frame(self, padding=10)
        control_frame.grid(row=3, column=0, sticky="ew")

        # Info Label (Duration)
        self.lbl_info = ttk.Label(control_frame, text="Ước tính: 0s")
        self.lbl_info.pack(side="top", anchor="w", pady=2)

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
        self.update_estimated_duration()

    def update_volume_label(self, val):
        self.lbl_volume_val.config(text=f"{int(float(val))}%")

    def update_pitch_label(self, val):
        self.lbl_pitch_val.config(text=f"{int(float(val))}Hz")

    def on_text_changed(self, event=None):
        self.text_area.edit_modified(False)
        self.update_estimated_duration()

    def update_estimated_duration(self):
        if self.is_subtitle_loaded:
             # Duration is fixed by subtitle
             if self.current_subtitle_segments:
                 duration = self.current_subtitle_segments[-1]['end'] / 1000
                 self.lbl_info.config(text=f"Thời lượng Subtitle: {int(duration // 60)}m {int(duration % 60)}s")
             return

        text = self.text_area.get("1.0", tk.END)
        word_count = len(text.split())
        rate = float(self.scale_rate.get())

        # Approx: 150 words per minute at 1.0x
        # Duration (min) = (Words / 150) / Rate
        if word_count > 0:
            minutes = (word_count / 150) / rate
            seconds = int(minutes * 60)
            self.lbl_info.config(text=f"Ước tính: {seconds // 60}m {seconds % 60}s ({word_count} từ)")
        else:
            self.lbl_info.config(text="Ước tính: 0s")

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

        for i, v in enumerate(voices):
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
            if target_voice_shortname:
                for idx, val in enumerate(voice_values):
                    if val.startswith(target_voice_shortname):
                        self.combo_voice.current(idx)
                        break

        self.status_var.set("Sẵn sàng")

    def load_file_action(self):
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", "*.txt *.epub *.srt *.vtt *.ass *.ssa"),
                ("Text Files", "*.txt"),
                ("Epub Files", "*.epub"),
                ("Subtitle Files", "*.srt *.vtt *.ass *.ssa"),
                ("All Files", "*.*")
            ]
        )
        if filepath:
            self.load_file_direct(filepath)

    def load_file_direct(self, filepath):
        self.current_filepath = filepath
        # Update config recent files
        self.config = ConfigManager.add_recent_file(self.config, filepath)
        ConfigManager.save_config(self.config)
        self.update_recent_menu()

        self.reload_file_content()

    def clean_text_action(self):
        text = self.text_area.get("1.0", tk.END)
        # Basic cleaning: replace multiple newlines with one, multiple spaces with one
        cleaned = " ".join(text.split())
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", cleaned)
        self.status_var.set("Đã làm sạch văn bản.")

    def reload_file_content(self):
        if not hasattr(self, 'current_filepath') or not self.current_filepath:
            return

        split_chapters = self.var_split_chapters.get()
        ext = os.path.splitext(self.current_filepath)[1].lower()
        self.is_epub_loaded = (ext == '.epub')
        self.is_subtitle_loaded = (ext in ['.srt', '.vtt', '.ass', '.ssa'])

        self.current_chapters = []
        self.current_subtitle_segments = []

        if self.is_epub_loaded and split_chapters:
             self.frame_chapters.grid(row=0, column=0, sticky="s", pady=(40,0))
        else:
             self.frame_chapters.grid_forget()

        try:
            content = read_file(self.current_filepath, split_chapters=(split_chapters and self.is_epub_loaded))

            self.text_area.delete("1.0", tk.END)

            if self.is_subtitle_loaded:
                self.current_subtitle_segments = content
                display_text = "\n".join([f"[{s['start']}->{s['end']}] {s['text']}" for s in content])
                self.text_area.insert("1.0", display_text)
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
                self.status_var.set(f"Đã tải Subtitle: {os.path.basename(self.current_filepath)} ({len(content)} lines)")

            elif isinstance(content, list):
                self.current_chapters = content
                chapter_titles = [c['title'] for c in content]
                self.combo_chapters['values'] = chapter_titles
                if chapter_titles:
                    self.combo_chapters.current(0)
                    self.on_chapter_selected(None)
                self.frame_chapters.grid(row=1, column=0, sticky="n", pady=5)
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(40, 5))
                self.status_var.set(f"Đã tải Ebook: {os.path.basename(self.current_filepath)}")
            else:
                self.text_area.insert("1.0", content)
                self.frame_chapters.grid_forget()
                self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
                self.status_var.set(f"Đã tải: {os.path.basename(self.current_filepath)}")

            self.update_estimated_duration()

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
            self.update_estimated_duration()

    def get_settings(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text and not self.is_subtitle_loaded:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập nội dung.")
            return None

        voice_str = self.combo_voice.get()
        if not voice_str:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn giọng đọc.")
            return None

        voice = voice_str.split(" ")[0]

        rate = float(self.scale_rate.get())
        volume = int(float(self.scale_volume.get()))
        pitch = int(float(self.scale_pitch.get()))

        return text, voice, rate, volume, pitch

    def play_action(self):
        if self.is_subtitle_loaded:
            messagebox.showinfo("Thông báo", "Chế độ Subtitle hiện chỉ hỗ trợ Lưu File MP3 (để đồng bộ thời gian).")
            return

        settings = self.get_settings()
        if not settings:
            return

        text, voice, rate, volume, pitch = settings

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang tạo âm thanh (Play)...")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)

        threading.Thread(target=self.run_tts_play, args=(text, voice, rate, volume, pitch), daemon=True).start()

    def run_tts_play(self, text, voice, rate, volume, pitch):
        try:
            try:
                self.player.stop()
            except:
                pass

            asyncio.run(self.tts.save_audio(text, voice, rate, volume, self.temp_file, pitch))
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
        if self.is_subtitle_loaded and self.current_subtitle_segments:
            self.save_subtitle_audio_action()
            return

        if self.var_split_chapters.get() and self.current_chapters:
             self.save_chapters_action()
             return

        settings = self.get_settings()
        if not settings:
            return

        text, voice, rate, volume, pitch = settings

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

        threading.Thread(target=self.run_tts_save, args=(text, voice, rate, volume, filepath, pitch), daemon=True).start()

    def save_subtitle_audio_action(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Files", "*.mp3")],
            title="Lưu Audio Đồng Bộ Subtitle"
        )
        if not filepath:
            return

        settings = self.get_settings()
        if not settings: return
        _, voice, rate, volume, pitch = settings

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang tạo audio từ subtitle...")
        self.progress.config(mode="determinate", maximum=len(self.current_subtitle_segments), value=0)

        threading.Thread(
            target=self.run_tts_subtitle,
            args=(self.current_subtitle_segments, voice, rate, volume, filepath, pitch),
            daemon=True
        ).start()

    def run_tts_subtitle(self, segments, voice, rate, volume, filepath, pitch):
        def progress_cb(current, total):
            self.after(0, lambda: self.progress.config(value=current))
            self.after(0, lambda: self.status_var.set(f"Đang xử lý dòng {current}/{total}"))

        try:
            asyncio.run(self.tts.generate_audio_with_silence(segments, voice, rate, volume, filepath, progress_cb, pitch))
            self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu file audio đồng bộ tại:\n{filepath}"))
        except Exception as e:
             self.after(0, lambda: messagebox.showerror("Lỗi Subtitle TTS", str(e)))
        finally:
            self.after(0, self.reset_ui_state)
            self.after(0, lambda: self.status_var.set("Sẵn sàng"))

    def save_chapters_action(self):
        directory = filedialog.askdirectory(title="Chọn thư mục để lưu các chương")
        if not directory:
            return

        settings = self.get_settings()
        if not settings: return
        _, voice, rate, volume, pitch = settings

        self.btn_play.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.status_var.set("Đang lưu hàng loạt...")
        self.progress.config(mode="determinate", maximum=len(self.current_chapters), value=0)

        threading.Thread(
            target=self.run_tts_save_batch,
            args=(self.current_chapters, voice, rate, volume, directory, pitch),
            daemon=True
        ).start()

    def run_tts_save_batch(self, chapters, voice, rate, volume, directory, pitch):
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

                asyncio.run(self.tts.save_audio(text, voice, rate, volume, filepath, pitch))

            self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu {total} file tại:\n{directory}"))
        except Exception as e:
             self.after(0, lambda: messagebox.showerror("Lỗi Batch Save", str(e)))
        finally:
            self.after(0, self.reset_ui_state)
            self.after(0, lambda: self.status_var.set("Sẵn sàng"))

    def run_tts_save(self, text, voice, rate, volume, filepath, pitch):
        try:
            asyncio.run(self.tts.save_audio(text, voice, rate, volume, filepath, pitch))
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
        voice_str = self.combo_voice.get()
        if voice_str:
            self.config["voice"] = voice_str.split(" ")[0]

        self.config["rate"] = self.scale_rate.get()
        self.config["volume"] = self.scale_volume.get()
        self.config["pitch"] = self.scale_pitch.get()

        ConfigManager.save_config(self.config)
        self.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
