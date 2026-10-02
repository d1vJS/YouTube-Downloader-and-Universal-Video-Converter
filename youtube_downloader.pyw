import os
import queue
import shutil
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, filedialog, messagebox

import yt_dlp
from yt_dlp.utils import sanitize_filename

AUDIO_QUALITIES = ["128 kbps", "192 kbps", "256 kbps", "320 kbps"] # made by divJS
VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p"] # telegram: @divJS

# How many videos to download at the same time when downloading a playlist.
# 2-4 is recommended; setting it too high may trigger YouTube rate limiting / 429 errors.
PARALLEL_DOWNLOADS = 3

# Number of automatic retry rounds for videos that failed to download
# (403 errors are usually temporary / caused by rate limiting)
RETRY_ROUNDS = 2


def esc(path):
    """'%' is special in yt-dlp output templates, so escape it inside paths."""
    return path.replace("%", "%%")


class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader (MP3 / MP4)")
        self.geometry("560x300")
        self.resizable(False, False)

        # Get the folder the program runs from and set a "Download" folder next to it as the target
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_dir = os.path.join(base_dir, "Download")
        os.makedirs(default_dir, exist_ok=True)

        self.folder = tk.StringVar(value=default_dir)
        self.fmt = tk.StringVar(value="mp3")              # mp3 / mp4
        self.quality = tk.StringVar(value="320 kbps")     # mp3 -> kbps, mp4 -> resolution
        self.mode = tk.StringVar(value="single")          # single / playlist
        self.status = tk.StringVar(value="Paste a link and press Download.")

        # --- Download state (worker threads write, the main thread reads via a timer) ---
        self.lock = threading.Lock()
        self.ui_queue = queue.Queue()
        self.prog = {"percent": 0.0, "text": self.status.get()}
        self._shown_pct = -1.0
        self._shown_text = self.prog["text"]
        self.item_pct = {}
        self.total_items = 1
        self.done_count = 0
        self.note = ""
        self.playlist_run = False

        pad = {"padx": 12, "pady": 6}

        # Link row
        ttk.Label(self, text="YouTube link:").grid(row=0, column=0, sticky="w", **pad)
        self.link_entry = ttk.Entry(self, width=48)
        self.link_entry.grid(row=0, column=1, **pad)
        ttk.Button(self, text="Paste", command=self.paste).grid(row=0, column=2, **pad)

        # Folder row
        ttk.Label(self, text="Save folder:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.folder, width=48).grid(row=1, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.choose_folder).grid(row=1, column=2, **pad)

        # Format row (MP3 / MP4)
        ttk.Label(self, text="Format:").grid(row=2, column=0, sticky="w", **pad)
        fmt_frame = ttk.Frame(self)
        fmt_frame.grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(
            fmt_frame, text="MP3 (audio)", value="mp3", variable=self.fmt,
            command=self.on_format_change,
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            fmt_frame, text="MP4 (video)", value="mp4", variable=self.fmt,
            command=self.on_format_change,
        ).pack(side="left")

        # Quality row (label is fixed, options change with the format)
        ttk.Label(self, text="Quality:").grid(row=3, column=0, sticky="w", **pad)
        self.quality_box = ttk.Combobox(
            self, textvariable=self.quality, values=AUDIO_QUALITIES,
            state="readonly", width=12,
        )
        self.quality_box.grid(row=3, column=1, sticky="w", **pad)

        # Mode row
        ttk.Label(self, text="Mode:").grid(row=4, column=0, sticky="w", **pad)
        mode_frame = ttk.Frame(self)
        mode_frame.grid(row=4, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(
            mode_frame, text="Single", value="single", variable=self.mode
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            mode_frame, text="Playlist (download all)", value="playlist", variable=self.mode
        ).pack(side="left")

        # Download button
        self.download_btn = ttk.Button(self, text="Download (MP3)", command=self.start)
        self.download_btn.grid(row=5, column=0, columnspan=3, pady=8)

        # Progress bar and status text
        self.bar = ttk.Progressbar(self, length=520, maximum=100)
        self.bar.grid(row=6, column=0, columnspan=3, padx=12, pady=4)
        ttk.Label(self, textvariable=self.status, wraplength=520).grid(
            row=7, column=0, columnspan=3, padx=12, pady=2
        )

        self.link_entry.focus()
        self.bind("<Return>", lambda e: self.start())

        if not shutil.which("ffmpeg"):
            messagebox.showwarning(
                "ffmpeg not found",
                "ffmpeg is required for MP3 conversion and for merging MP4 video + audio.\n\n"
                "Please install ffmpeg on your system."
            )

        # UI updates: done by a timer on the main thread instead of the worker threads
        self.after(100, self.poll)

    # ---------- UI Functions ----------

    def on_format_change(self):
        """Selecting MP3 shows kbps options, selecting MP4 shows resolution options."""
        if self.fmt.get() == "mp3":
            self.quality_box.config(values=AUDIO_QUALITIES)
            self.quality.set("320 kbps")
            self.download_btn.config(text="Download (MP3)")
        else:
            self.quality_box.config(values=VIDEO_QUALITIES)
            self.quality.set("1080p")
            self.download_btn.config(text="Download (MP4)")

    def paste(self):
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            return
        self.link_entry.delete(0, tk.END)
        self.link_entry.insert(0, text)

    def choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder.get())
        if selected:
            self.folder.set(selected)

    def poll(self):
        """Every 100 ms: run pending jobs, update the bar and text only if they changed."""
        while True:
            try:
                fn = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            fn()

        pct, text = self.prog["percent"], self.prog["text"]
        if pct != self._shown_pct:
            self.bar.config(value=pct)
            self._shown_pct = pct
        if text != self._shown_text:
            self.status.set(text)
            self._shown_text = text

        self.after(100, self.poll)

    def quality_value(self):
        """'320 kbps' -> '320', '1080p' -> '1080'"""
        return "".join(ch for ch in self.quality.get() if ch.isdigit())

    # ---------- State helpers (thread-safe) ----------

    def set_text(self, text):
        with self.lock:
            if not self.playlist_run:
                self.prog["text"] = text

    def playlist_text(self):
        """Must be called while holding the lock."""
        text = f"Playlist: {self.done_count}/{self.total_items} completed"
        if self.note:
            text += f"  |  {self.note}"
        return text

    def set_item_pct(self, idx, pct, single_text=None):
        with self.lock:
            # Keep the bar from going backwards (whatever the video/audio order)
            self.item_pct[idx] = max(self.item_pct.get(idx, 0.0), pct)
            overall = sum(self.item_pct.values()) / self.total_items
            self.prog["percent"] = overall
            if self.playlist_run:
                self.prog["text"] = self.playlist_text()
            elif single_text:
                self.prog["text"] = single_text

    # ---------- Download Logic ----------

    def start(self):
        link = self.link_entry.get().strip()
        if not link:
            messagebox.showinfo("No Link", "Please paste a YouTube link first.")
            return
        self.download_btn.config(state="disabled")
        with self.lock:
            self.item_pct = {}
            self.total_items = 1
            self.done_count = 0
            self.note = ""
            self.playlist_run = False
            self.prog["percent"] = 0.0
            self.prog["text"] = "Checking link..."
        threading.Thread(
            target=self.download,
            args=(link, self.mode.get(), self.fmt.get(), self.quality_value()),
            daemon=True,
        ).start()

    def make_progress_hook(self, idx, fmt):
        last = [0.0]

        def hook(d):
            info = d.get("info_dict") or {}
            audio_only = info.get("vcodec") == "none"

            if d["status"] == "downloading":
                # The hook is called very often; skip anything more frequent than 100 ms
                now = time.monotonic()
                if now - last[0] < 0.1:
                    return
                last[0] = now

                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if not total:
                    return
                frac = d["downloaded_bytes"] / total

                # For a single file the bar moves from 0 -> 100 in one go
                if fmt == "mp4":
                    if audio_only:
                        pct, label = 85 + frac * 13, "Audio"
                    else:
                        pct, label = frac * 85, "Video"
                else:
                    pct, label = frac * 95, "Downloading"
                self.set_item_pct(idx, pct, f"{label}: %{frac * 100:.0f}")

            elif d["status"] == "finished":
                if fmt == "mp3":
                    self.set_item_pct(idx, 95)
                elif audio_only:
                    self.set_item_pct(idx, 98)
                else:
                    self.set_item_pct(idx, 85)

        return hook

    def postprocess_hook(self, d):
        if d["status"] != "started":
            return
        name = d.get("postprocessor")
        if name == "ExtractAudio":
            self.set_text("Converting to MP3...")
        elif name == "Merger":
            self.set_text("Merging video and audio...")

    def build_format_options(self, fmt, quality):
        """Returns the yt-dlp format/postprocessor settings for the selected format."""
        if fmt == "mp3":
            return {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": quality,
                    },
                    {"key": "FFmpegMetadata"},  # MP3 files are small, so write tags (title etc.)
                ],
            }

        # MP4: best video not exceeding the selected height + best audio.
        # Note: FFmpegMetadata is left out on purpose; it rewrote the large video file
        # from the start and made the process take longer.
        h = quality
        return {
            "format": (
                f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                f"/best[height<={h}][ext=mp4]"
                f"/bestvideo[height<={h}]+bestaudio"
                f"/best[height<={h}]"
            ),
            "merge_output_format": "mp4",
        }

    def make_options(self, template, fmt, quality, idx, fallback=False):
        options = {
            "outtmpl": template,
            "noplaylist": True,       # Each download is a single video (we expand playlists ourselves)
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "no_color": True,

            # --- SPEED / RESILIENCE SETTINGS ---
            "concurrent_fragment_downloads": 8,
            "http_chunk_size": 10485760,
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 20,
            "extractor_args": {"youtube": ["player_client=android,web"]},
            # -----------------------------------

            "progress_hooks": [self.make_progress_hook(idx, fmt)],
            "postprocessor_hooks": [self.postprocess_hook],
        }
        if fallback:
            # Fallback attempt: yt-dlp's default YouTube settings + a single connection
            options.pop("extractor_args")
            options["concurrent_fragment_downloads"] = 1
        options.update(self.build_format_options(fmt, quality))
        return options

    def download_item(self, url, template, fmt, quality, idx, fallback=False):
        """Downloads a single video. Returns None on success, or the error text on failure."""
        try:
            with yt_dlp.YoutubeDL(
                self.make_options(template, fmt, quality, idx, fallback)
            ) as ydl:
                ydl.download([url])
            with self.lock:
                self.done_count += 1
            self.set_item_pct(idx, 100)
            return None
        except Exception as e:
            self.set_item_pct(idx, 100)
            return str(e)

    def get_playlist(self, link):
        """Returns (title, [(index, url), ...]) if it's a playlist, otherwise None."""
        try:
            with yt_dlp.YoutubeDL(
                {"quiet": True, "extract_flat": True, "skip_download": True}
            ) as ydl:
                info = ydl.extract_info(link, download=False)
            if not info or info.get("_type") != "playlist":
                return None

            entries = []
            for i, e in enumerate(info.get("entries") or [], start=1):
                if not e:
                    continue
                url = e.get("url") or e.get("webpage_url")
                if (not url or not url.startswith("http")) and e.get("id"):
                    url = f"https://www.youtube.com/watch?v={e['id']}"
                if url:
                    entries.append((i, url))
            if entries:
                return info.get("title") or "Playlist", entries
        except Exception:
            pass
        return None

    def download(self, link, mode, fmt, quality):
        folder = self.folder.get()
        kind = "songs" if fmt == "mp3" else "videos"
        try:
            playlist = None
            if mode == "playlist":
                self.set_text("Analyzing playlist...")
                playlist = self.get_playlist(link)

            if playlist:
                title, entries = playlist
                total = len(entries)
                with self.lock:
                    self.playlist_run = True
                    self.total_items = total
                    self.prog["text"] = self.playlist_text()

                raw_base = os.path.join(folder, sanitize_filename(title))
                base = esc(raw_base)
                items = [
                    (idx, url, os.path.join(base, f"{idx:02d} - %(title)s.%(ext)s"))
                    for idx, url in entries
                ]

                def run_pass(batch, workers, fallback):
                    """Downloads the videos in batch; returns the failed ones as [(item, error)]."""
                    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(batch)))) as pool:
                        futures = [
                            pool.submit(self.download_item, url, tpl, fmt, quality, idx, fallback)
                            for idx, url, tpl in batch
                        ]
                        results = [f.result() for f in futures]
                    return [(it, err) for it, err in zip(batch, results) if err]

                failed = run_pass(items, PARALLEL_DOWNLOADS, False)

                # Automatically retry the ones that failed:
                # Round 1: same settings but one at a time (against rate limiting)
                # Round 2: with yt-dlp's default YouTube settings
                for round_no in range(1, RETRY_ROUNDS + 1):
                    if not failed:
                        break
                    with self.lock:
                        self.note = f"Retrying {len(failed)} video(s) ({round_no}/{RETRY_ROUNDS})"
                        self.prog["text"] = self.playlist_text()
                    time.sleep(3)
                    failed = run_pass([it for it, _ in failed], 1, fallback=(round_no >= 2))

                with self.lock:
                    self.note = ""
                done = self.done_count
                if done == 0 and failed:
                    raise RuntimeError(failed[0][1])

                msg = f"Done! {done}/{total} {kind} downloaded."
                if failed:
                    try:
                        os.makedirs(raw_base, exist_ok=True)
                        with open(os.path.join(raw_base, "failed.txt"), "w",
                                  encoding="utf-8") as fh:
                            for (idx, url, _), err in failed:
                                fh.write(f"{idx:02d} | {url} | {err.splitlines()[0] if err else ''}\n")
                    except OSError:
                        pass
                    msg += f" ({len(failed)} failed, details: failed.txt)"
            else:
                self.set_text("Starting download...")
                template = os.path.join(esc(folder), "%(title)s.%(ext)s")
                err = self.download_item(link, template, fmt, quality, 0)
                if err:
                    raise RuntimeError(err)
                msg = "Done! File saved."

            def finish():
                with self.lock:
                    self.prog["text"] = msg
                    self.prog["percent"] = 100.0
                self.link_entry.delete(0, tk.END)

            self.ui_queue.put(finish)

        except Exception as e:
            error = str(e)

            def fail():
                with self.lock:
                    self.prog["text"] = "An error occurred."
                messagebox.showerror("Error", error)

            self.ui_queue.put(fail)
        finally:
            self.ui_queue.put(lambda: self.download_btn.config(state="normal"))


if __name__ == "__main__":
    YouTubeDownloader().mainloop()
