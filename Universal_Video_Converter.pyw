import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk

def klasor_sec(entry_widget): 
    klasor = filedialog.askdirectory()
    if klasor:
        entry_widget.delete(0, tk.END) # made by divJS
        entry_widget.insert(0, klasor) # telegram: @divJS

def log_yaz(mesaj):
    txt_log.config(state=tk.NORMAL)
    txt_log.insert(tk.END, mesaj + "\n")
    txt_log.see(tk.END)
    txt_log.config(state=tk.DISABLED)

def donustur_thread():
    btn_basla.config(state=tk.DISABLED)
    girdi_klasoru = ent_girdi.get()
    cikti_klasoru = ent_cikti.get()
    secilen_cozunurluk = combo_coz.get()
    
    if not girdi_klasoru or not cikti_klasoru:
        messagebox.showwarning("Warning", "Please select the input and output folders!")
        btn_basla.config(state=tk.NORMAL)
        return

    if os.path.normcase(os.path.abspath(girdi_klasoru)) == os.path.normcase(os.path.abspath(cikti_klasoru)):
        messagebox.showwarning(
            "Same Folder",
            "The input and output folders are the same!\n\n"
            "The converted videos would overwrite your original files. "
            "Please select a different output folder."
        )
        btn_basla.config(state=tk.NORMAL)
        return

    if not os.path.exists(cikti_klasoru):
        os.makedirs(cikti_klasoru)

    videolar = [f for f in os.listdir(girdi_klasoru) if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.av1'))]
    
    if not videolar:
        log_yaz("No suitable videos found in the selected folder.")
        btn_basla.config(state=tk.NORMAL)
        return

    toplam = len(videolar)
    log_yaz(f"Found {toplam} videos in total. Starting multi-core processing...\n")
    
    progress["maximum"] = toplam
    progress["value"] = 0

    for indeks, dosya in enumerate(videolar, 1):
        girdi_yolu = os.path.join(girdi_klasoru, dosya)
        dosya_adi = os.path.splitext(dosya)[0]
        cikti_yolu = os.path.join(cikti_klasoru, f"{dosya_adi}.mp4")
        
        lbl_durum.config(text=f"Processing: {indeks} / {toplam}")
        log_yaz(f"[{indeks}/{toplam}] Converting: {dosya}")
        
        komut = [
            "ffmpeg", "-y",
            "-i", girdi_yolu, 
            "-c:v", "libx264",          # Universal encoder that works on every computer
            "-preset", "superfast",     # Convert at maximum speed without straining the CPU
            "-profile:v", "main",       # Standard profile for car screens
            "-level", "4.0",            # Support for older devices
            "-crf", "23",               # Balance of picture quality
            "-pix_fmt", "yuv420p",      # Universal color format
            "-c:a", "aac", 
            "-b:a", "192k",
            "-threads", "0"             # Uses ALL CPU cores of the person running the code
        ]
        
        if secilen_cozunurluk == "1080p":
            komut.extend(["-vf", "scale=-2:1080"])
        elif secilen_cozunurluk == "720p":
            komut.extend(["-vf", "scale=-2:720"])
        elif secilen_cozunurluk == "480p (Old Screens)":
            komut.extend(["-vf", "scale=-2:480"])
            
        komut.append(cikti_yolu)
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo, check=True)
            log_yaz(f"Success: {dosya}\n")
        except subprocess.CalledProcessError:
            log_yaz(f"ERROR: This file may be corrupted, skipping. ({dosya})\n")
        except Exception as e:
            log_yaz(f"Unexpected error ({dosya}): {str(e)}\n")
            
        progress["value"] = indeks
        pencere.update_idletasks()

    log_yaz("=== ALL TASKS FINISHED ===")
    lbl_durum.config(text="Done, you can transfer the files to your USB drive.")
    btn_basla.config(state=tk.NORMAL)

def baslat():
    threading.Thread(target=donustur_thread, daemon=True).start()

pencere = tk.Tk()
pencere.title("Universal Video Converter")
pencere.geometry("650x580")
pencere.configure(padx=20, pady=20)

style = ttk.Style()
style.theme_use("clam")

ttk.Label(pencere, text="Folder of Videos to Convert:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
frame_girdi = ttk.Frame(pencere)
frame_girdi.pack(fill=tk.X, pady=(0, 10))
ent_girdi = ttk.Entry(frame_girdi, font=("Arial", 10))
ent_girdi.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
ttk.Button(frame_girdi, text="Select Folder", command=lambda: klasor_sec(ent_girdi)).pack(side=tk.RIGHT)

ttk.Label(pencere, text="Folder to Save the New Videos:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
frame_cikti = ttk.Frame(pencere)
frame_cikti.pack(fill=tk.X, pady=(0, 15))
ent_cikti = ttk.Entry(frame_cikti, font=("Arial", 10))
ent_cikti.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
ttk.Button(frame_cikti, text="Select Folder", command=lambda: klasor_sec(ent_cikti)).pack(side=tk.RIGHT)

frame_ayar = ttk.Frame(pencere)
frame_ayar.pack(fill=tk.X, pady=(0, 15))
ttk.Label(frame_ayar, text="Car Screen Resolution:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
combo_coz = ttk.Combobox(frame_ayar, values=["Original (Don't Change)", "1080p", "720p", "480p (Old Screens)"], state="readonly", width=25)
combo_coz.current(0)
combo_coz.pack(side=tk.LEFT, padx=(10, 0))

btn_basla = tk.Button(pencere, text="Start Conversion", font=("Arial", 11, "bold"), bg="#107C41", fg="white", command=baslat, relief=tk.FLAT)
btn_basla.pack(fill=tk.X, pady=(0, 15), ipady=5)

frame_durum = ttk.Frame(pencere)
frame_durum.pack(fill=tk.X, pady=(0, 5))
lbl_durum = ttk.Label(frame_durum, text="Waiting...", font=("Arial", 9, "italic"))
lbl_durum.pack(side=tk.LEFT)

progress = ttk.Progressbar(pencere, orient=tk.HORIZONTAL, mode='determinate')
progress.pack(fill=tk.X, pady=(0, 15))

ttk.Label(pencere, text="Details:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
txt_log = scrolledtext.ScrolledText(pencere, height=10, font=("Consolas", 9), state=tk.DISABLED, bg="#F3F3F3")
txt_log.pack(fill=tk.BOTH, expand=True)

log_yaz("System ready. This program is set to a universal mode compatible with all computers.")
pencere.mainloop()
