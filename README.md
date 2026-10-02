# 🎬 YouTube Downloader & Universal Video Converter

Two small, easy-to-install GUI tools made for Windows:

* **YouTube Downloader** – Downloads music (MP3) or video (MP4) from a YouTube link. Supports single videos or entire playlists.
* **Universal Video Converter** – Converts videos on your computer to play smoothly on any device (car screens, old TVs, USB-powered multimedia systems, etc.).
* **setup.bat** – A helper file that installs everything required (Python, yt-dlp, ffmpeg) with a single click.

No command-line knowledge required; they all work with simple double-click windows.

---

## 📦 Files

| File | What does it do? |
| --- | --- |
| `setup.bat` | Automatically installs Python, yt-dlp, and ffmpeg |
| `youtube_downloader.pyw` | MP3 / MP4 downloader for YouTube |
| `Universal_Video_Converter.pyw` | Batch video conversion program |

> Thanks to the `.pyw` extension, no black console window appears when launching the programs, only the application window is shown.

---

## ⚙️ Installation

1. Download this repo via **Code → Download ZIP** and extract it to a folder.
2. Double-click the **`setup.bat`** file.
3. The script sequentially checks / installs the following:
* **Python** (if missing, Python 3.12 is installed via `winget`)
* **yt-dlp** (installed or updated via `pip`)
* **ffmpeg** (if missing, installed via `winget`)


4. If Python was installed for the first time, close the window and **run `setup.bat` one more time** (required for Python to be added to PATH).
5. Once the installation is complete, close any open programs and reopen them. You are good to go!

**Requirements:** Windows 10/11 and an internet connection. The installation uses `winget`; if your computer doesn't have winget, you must install Python manually from [python.org](https://www.python.org/downloads/) (making sure to check the **"Add python.exe to PATH"** box during installation) and install ffmpeg manually.

---

## 🎵 YouTube Downloader

Open by double-clicking the `youtube_downloader.pyw` file.

### Features

* Download as **MP3 (audio)** or **MP4 (video)**
* **Audio quality:** 128 / 192 / 256 / 320 kbps
* **Video quality:** 360p / 480p / 720p / 1080p / 1440p / 2160p
* **Single video** or **playlist (download all)** mode
* Fast downloading for playlists with **multiple simultaneous downloads** (default 3)
* **Automatic retry** for failed videos; those that still fail are logged in the `failed.txt` file
* Progress bar and status text
* One-click link pasting from the clipboard ("Paste" button)
* Playlists are saved in their own folders, numbered sequentially (e.g., `01 - Song Name.mp3`)

### How to use?

1. Paste the YouTube link.
2. Select the destination folder (default: an auto-created `Download` folder next to the program).
3. Select the format (MP3 / MP4) and quality.
4. Select whether it's a single video or a playlist.
5. Click the **Download** button (or press Enter).

### Settings

You can change the values at the top of the file if you wish:

```python
PARALLEL_DOWNLOADS = 3   # How many videos to download simultaneously in a playlist (2-4 recommended)
RETRY_ROUNDS = 2         # Number of automatic retries for failed videos

```

> A very high number of parallel downloads may cause you to hit YouTube's rate limits (Error 429).

---

## 🔄 Universal Video Converter

Open by double-clicking the `Universal_Video_Converter.pyw` file.

### What does it do?

Some car multimedia screens, old televisions, or devices that play from USBs don't support every video format. This program converts all videos in a folder **to MP4 (H.264 + AAC) using the most compatible settings**; ensuring they play smoothly on almost any device.

### Features

* **Batch** converts all videos in a folder
* Supported input formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.av1`
* Output is always **MP4** (H.264 video, AAC 192k audio, widely compatible `yuv420p` color format)
* Resolution options: **Original (no change)**, **1080p**, **720p**, **480p (for older screens)**
* Utilizes all CPU cores, runs with a fast preset
* Operation log and progress bar
* Skips corrupted files if encountered and continues with the rest
* Gives a warning if the input and output folders are the same **to prevent overwriting original files**

### How to use?

1. Select the **folder containing the videos to be converted**.
2. Select the **folder where the new videos will be saved** (must be different from the input folder).
3. Select the appropriate resolution for the target device's screen.
4. Click the **Start Conversion** button.
5. Once finished, copy the files from the output folder to your USB drive and play them on your device.

> Note: Only videos within the selected folder are processed; subfolders are ignored.

---

## ❓ Common Issues

**"ffmpeg not found" warning appears.**
ffmpeg might not be installed, or it might have just been added to the PATH. After running `setup.bat`, close the program and reopen it; if it still appears, restart your computer.

**The program doesn't open at all.**
Python might not be installed, or `.pyw` files are not associated with Python. Run `setup.bat`; if you installed Python manually, make sure you checked the PATH option.

**Downloading gives an error (403 / 429).**
YouTube might have imposed a temporary limit. Wait a bit and try again, or run `setup.bat` to update yt-dlp (Since YouTube changes frequently, keeping yt-dlp up-to-date is important).

---

## ⚠️ Legal Disclaimer

These tools are for **personal use** only. It is solely the user's responsibility to comply with the copyright of the downloaded content and the YouTube Terms of Service. Do not download or distribute copyrighted content without permission.

---

## 🙏 Open Source Projects Used

* [yt-dlp](https://github.com/yt-dlp/yt-dlp) – YouTube download engine
* [FFmpeg](https://ffmpeg.org/) – Audio/video conversion

---

## 👤 Creator

Made by **divJS** – Telegram: [@divJS](https://www.google.com/search?q=https://t.me/divJS)

You can use the **Issues** section for bug reports or suggestions.
