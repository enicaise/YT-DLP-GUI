import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import os
import json
import threading
import requests
import sys
from io import BytesIO
from PIL import Image, ImageTk, ImageDraw

# -------------------------------
# Translations for bilingual UI
# -------------------------------
translations = {
    "en": {
        "window_title": "YT-dlp Interface",
        "language": "Language:",
        "video_url": "Video URL:",
        "fetch_options": "Fetch Options",
        "download_folder": "Download Folder:",
        "browse": "Browse",
        "file_type": "File Type:",
        "extract_audio": "Extract Audio Only",
        "audio_format": "Audio Format:",
        "safe_windows": "Safe for Windows",
        "quality": "Quality:",
        "subtitles": "Subtitles:",
        "download": "Download",
        "error": "Error",
        "url_empty_error": "The URL cannot be empty.",
        "download_empty_error": "Please select a download folder.",
        "options_fetching": "Fetching options...\n",
        "options_updated": "Options updated.\n",
        "no_quality_options": "No quality options found.\n",
        "no_subtitles": "No subtitles available.\n",
        "exec_cmd": "\nExecuting command: ",
        "download_complete": "\nDownload complete.\n",
        "config_load_error": "Error loading config: ",
        "config_save_error": "Error saving config: ",
        "fetch_options_error": "Error fetching options: "
    },
    "fr": {
        "window_title": "Interface YT‑dlp",
        "language": "Langue:",
        "video_url": "URL de la vidéo :",
        "fetch_options": "Récupérer options",
        "download_folder": "Dossier de téléchargement :",
        "browse": "Parcourir",
        "file_type": "Type de fichier :",
        "extract_audio": "Extraire uniquement l'audio",
        "audio_format": "Format audio :",
        "safe_windows": "Sûr pour Windows",
        "quality": "Qualité :",
        "subtitles": "Sous-titres :",
        "download": "Télécharger",
        "error": "Erreur",
        "url_empty_error": "L'URL ne peut pas être vide.",
        "download_empty_error": "Veuillez sélectionner un dossier de téléchargement.",
        "options_fetching": "Récupération des options...\n",
        "options_updated": "Options mises à jour.\n",
        "no_quality_options": "Aucune option de qualité trouvée.\n",
        "no_subtitles": "Aucun sous-titre disponible.\n",
        "exec_cmd": "\nExécution de la commande : ",
        "download_complete": "\nTéléchargement terminé.\n",
        "config_load_error": "Erreur lors du chargement de la config : ",
        "config_save_error": "Erreur lors de la sauvegarde de la config : ",
        "fetch_options_error": "Erreur lors de la récupération des options : "
    }
}

def get_lang_code():
    return "fr" if language_var.get() == "Français" else "en"

def t(key):
    lang = get_lang_code()
    return translations.get(lang, translations["en"]).get(key, key)

# ----------------------------------------
# Utility: Add a rounded border to an image
# ----------------------------------------
def add_rounded_border(im, radius=5, border=2, border_color="#000000"):
    im = im.convert("RGBA")
    w, h = im.size
    new_w, new_h = w + 2 * border, h + 2 * border
    background = Image.new("RGBA", (new_w, new_h), border_color)
    mask_bg = Image.new("L", (new_w, new_h), 0)
    draw_bg = ImageDraw.Draw(mask_bg)
    draw_bg.rounded_rectangle((0, 0, new_w, new_h), radius=radius+border, fill=255)
    background.putalpha(mask_bg)
    mask_im = Image.new("L", (w, h), 0)
    draw_im = ImageDraw.Draw(mask_im)
    draw_im.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    im.putalpha(mask_im)
    background.paste(im, (border, border), im)
    return background

# ---------------------------------
# Configuration: Load and save config
# ---------------------------------
def get_app_path():
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        return os.path.dirname(os.path.abspath(__file__))

def load_config():
    try:
        config_path = os.path.join(get_app_path(), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                download_path_var.set(config.get("download_path", ""))
                file_type_var.set(config.get("file_type", "mp4"))
                extract_audio_var.set(config.get("extract_audio", False))
                audio_format_var.set(config.get("audio_format", "mp3"))
                safe_windows_var.set(config.get("safe_windows", False))
                lang_code = config.get("language", "en")
                language_var.set("Français" if lang_code == "fr" else "English")
    except Exception as e:
        safe_append_text(t("config_load_error") + str(e) + "\n")

def save_config():
    try:
        config = {
            "download_path": download_path_var.get(),
            "file_type": file_type_var.get(),
            "extract_audio": extract_audio_var.get(),
            "audio_format": audio_format_var.get(),
            "safe_windows": safe_windows_var.get(),
            "language": get_lang_code()
        }
        config_path = os.path.join(get_app_path(), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        safe_append_text(t("config_save_error") + str(e) + "\n")

def on_closing():
    save_config()
    root.destroy()

# ---------------------------
# Update UI texts per language
# ---------------------------
def update_ui_language(*args):
    lang = get_lang_code()
    root.title(translations[lang]["window_title"])
    label_language.config(text=t("language"))
    label_video_url.config(text=t("video_url"))
    button_fetch_options.config(text=t("fetch_options"))
    label_download_folder.config(text=t("download_folder"))
    button_browse.config(text=t("browse"))
    label_file_type.config(text=t("file_type"))
    label_extract_audio.config(text=t("extract_audio"))
    label_safe_windows.config(text=t("safe_windows"))
    label_audio_format.config(text=t("audio_format"))
    label_quality.config(text=t("quality"))
    label_subtitles.config(text=t("subtitles"))
    button_download.config(text=t("download"))

# ----------------------
# Logging helper function
# ----------------------
def safe_append_text(msg):
    text_area.after(0, lambda: (text_area.insert(tk.END, msg), text_area.see(tk.END)))

# --------------------------
# Action functions (Fetch, Download, etc.)
# --------------------------
quality_options_mapping = {}  # Global mapping for available formats
thumbnail_photo = None        # Global reference for thumbnail image

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path_var.set(folder)

def fetch_options():
    url = url_var.get().strip()
    if not url:
        messagebox.showerror(t("error"), t("url_empty_error"))
        return
    text_area.delete("1.0", tk.END)
    safe_append_text(t("options_fetching"))
    
    def worker():
        global quality_options_mapping, thumbnail_photo
        try:
            # Setup startupinfo and creationflags to hide console window
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                startupinfo = None
                creationflags = 0

            result = subprocess.run(["yt-dlp", "-J", url],
                                    capture_output=True, text=True, check=True,
                                    startupinfo=startupinfo,
                                    creationflags=creationflags)
            data = json.loads(result.stdout)
            # --- Thumbnail ---
            thumbnail_url = data.get("thumbnail")
            if thumbnail_url:
                try:
                    response = requests.get(thumbnail_url)
                    response.raise_for_status()
                    img_data = response.content
                    image = Image.open(BytesIO(img_data))
                    max_size = (200, 200)
                    try:
                        resample_filter = Image.Resampling.LANCZOS
                    except AttributeError:
                        resample_filter = Image.ANTIALIAS
                    image.thumbnail(max_size, resample_filter)
                    image = add_rounded_border(image, radius=5, border=2, border_color="#000000")
                    thumbnail_photo = ImageTk.PhotoImage(image)
                    thumbnail_label.after(0, lambda: thumbnail_label.config(image=thumbnail_photo))
                except Exception as e:
                    safe_append_text("Error fetching thumbnail: " + str(e) + "\n")
            else:
                safe_append_text("No thumbnail found.\n")
            # --- Video formats ---
            formats = data.get("formats", [])
            quality_options = []
            quality_options_mapping.clear()
            for fmt in formats:
                fmt_id = fmt.get("format_id", "")
                ext = fmt.get("ext", "")
                note = fmt.get("format_note", "")
                acodec = fmt.get("acodec", "none")
                acodec_info = "video only" if acodec == "none" else acodec
                label = f"{fmt_id} - {ext} - {note} - audio: {acodec_info}"
                quality_options.append(label)
                quality_options_mapping[label] = fmt
            quality_options = list(dict.fromkeys(quality_options))
            if quality_options:
                quality_var.set(quality_options[0])
                quality_menu["menu"].delete(0, "end")
                for opt in quality_options:
                    quality_menu["menu"].add_command(label=opt, command=lambda value=opt: quality_var.set(value))
                safe_append_text(t("options_updated"))
            else:
                safe_append_text(t("no_quality_options"))
            # --- Subtitles ---
            subs = data.get("subtitles", {})
            subtitle_options = list(subs.keys())
            if subtitle_options:
                subtitle_var.set(subtitle_options[0])
                subtitle_menu["menu"].delete(0, "end")
                for opt in subtitle_options:
                    subtitle_menu["menu"].add_command(label=opt, command=lambda value=opt: subtitle_var.set(value))
                safe_append_text(t("options_updated"))
            else:
                safe_append_text(t("no_subtitles"))
        except subprocess.CalledProcessError as e:
            safe_append_text(t("fetch_options_error") + e.stderr + "\n")
        except json.JSONDecodeError:
            safe_append_text("JSON decode error.\n")
        except Exception as ex:
            safe_append_text("Exception: " + str(ex) + "\n")
    
    threading.Thread(target=worker, daemon=True).start()

def start_download():
    url = url_var.get().strip()
    download_path = download_path_var.get().strip()
    quality_option = quality_var.get().strip()
    subtitle_option = subtitle_var.get().strip()
    if not url:
        messagebox.showerror(t("error"), t("url_empty_error"))
        return
    if not download_path:
        messagebox.showerror(t("error"), t("download_empty_error"))
        return
    output_template = os.path.join(download_path, "%(title)s.%(ext)s")
    cmd = ["yt-dlp", url, "-o", output_template]
    if extract_audio_var.get():
        cmd += ["--extract-audio", "--audio-format", audio_format_var.get()]
    else:
        if file_type_var.get() == "mp3":
            cmd += ["--extract-audio", "--audio-format", "mp3"]
        else:
            if quality_option != "Choisir" and " - " in quality_option and quality_option in quality_options_mapping:
                fmt_info = quality_options_mapping[quality_option]
                fmt_id = fmt_info.get("format_id", "")
                if file_type_var.get() == "mp4":
                    if safe_windows_var.get():
                        # If safe for Windows is checked, re-encode to MP4
                        if fmt_info.get("acodec", "none") == "none":
                            combined_format = f"{fmt_id}+bestaudio"
                            cmd += ["-f", combined_format, "--recode-video", "mp4"]
                        else:
                            cmd += ["-f", fmt_id, "--recode-video", "mp4"]
                    else:
                        if fmt_info.get("acodec", "none") == "none":
                            combined_format = f"{fmt_id}+bestaudio"
                            cmd += ["-f", combined_format, "--merge-output-format", "mp4"]
                        else:
                            cmd += ["-f", fmt_id]
                else:
                    cmd += ["-f", fmt_id]
    if subtitle_option and subtitle_option.lower() != "choisir":
        cmd += ["--write-subs", "--sub-lang", subtitle_option]
    safe_append_text(t("exec_cmd") + " ".join(cmd) + "\n\n")
    
    def run_download():
        try:
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                startupinfo = None
                creationflags = 0
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1,
                                       startupinfo=startupinfo,
                                       creationflags=creationflags)
            for line in process.stdout:
                safe_append_text(line)
            process.stdout.close()
            process.wait()
            safe_append_text(t("download_complete"))
        except Exception as ex:
            safe_append_text("Exception: " + str(ex) + "\n")
    
    threading.Thread(target=run_download, daemon=True).start()

def toggle_audio_format():
    if extract_audio_var.get():
        audio_format_menu.config(state='normal')
    else:
        audio_format_menu.config(state='disabled')

# ---------------------------
# Main Window & Layout Setup
# ---------------------------
root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.geometry("1000x800")

# Configuration variables
language_var = tk.StringVar(value="English")
url_var = tk.StringVar()
download_path_var = tk.StringVar()
file_type_var = tk.StringVar(value="mp4")
quality_var = tk.StringVar(value="Choisir")
subtitle_var = tk.StringVar(value="Choisir")
extract_audio_var = tk.BooleanVar(value=False)
audio_format_var = tk.StringVar(value="mp3")
safe_windows_var = tk.BooleanVar(value=False)
audio_formats = ["mp3", "aac", "flac", "wav", "m4a"]

# --- Row 0: Language selection (spanning columns 0-1) ---
language_frame = tk.Frame(root)
language_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
label_language = tk.Label(language_frame, text="")
label_language.pack(side=tk.LEFT)
language_menu = tk.OptionMenu(language_frame, language_var, "English", "Français", command=lambda _: update_ui_language())
language_menu.config(width=10)
language_menu.pack(side=tk.LEFT, padx=5)

# --- Row 1: Video URL ---
label_video_url = tk.Label(root, text="")
label_video_url.grid(row=1, column=0, padx=10, pady=5, sticky="w")
url_frame = tk.Frame(root)
url_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
entry_url = tk.Entry(url_frame, textvariable=url_var, width=50)
entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True)
button_fetch_options = tk.Button(url_frame, text="", command=fetch_options)
button_fetch_options.pack(side=tk.LEFT, padx=5)

# --- Row 2: Download Folder ---
label_download_folder = tk.Label(root, text="")
label_download_folder.grid(row=2, column=0, padx=10, pady=5, sticky="w")
download_frame = tk.Frame(root)
download_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
entry_download = tk.Entry(download_frame, textvariable=download_path_var, width=50)
entry_download.pack(side=tk.LEFT, fill=tk.X, expand=True)
button_browse = tk.Button(download_frame, text="", command=browse_folder)
button_browse.pack(side=tk.LEFT, padx=5)

# --- Row 3: File Type ---
label_file_type = tk.Label(root, text="")
label_file_type.grid(row=3, column=0, padx=10, pady=5, sticky="w")
option_file_type = tk.OptionMenu(root, file_type_var, "mp3", "mp4", "mkv")
option_file_type.grid(row=3, column=1, padx=10, pady=5, sticky="w")

# --- Row 4: Extract Audio Only ---
label_extract_audio = tk.Label(root, text="")
label_extract_audio.grid(row=4, column=0, padx=10, pady=5, sticky="w")
checkbutton_extract_audio = tk.Checkbutton(root, text="", variable=extract_audio_var, command=toggle_audio_format)
checkbutton_extract_audio.grid(row=4, column=1, padx=10, pady=5, sticky="w")

# --- Row 5: Safe for Windows ---
label_safe_windows = tk.Label(root, text="")
label_safe_windows.grid(row=5, column=0, padx=10, pady=5, sticky="w")
checkbutton_safe_windows = tk.Checkbutton(root, text="", variable=safe_windows_var)
checkbutton_safe_windows.grid(row=5, column=1, padx=10, pady=5, sticky="w")

# --- Row 6: Audio Format ---
label_audio_format = tk.Label(root, text="")
label_audio_format.grid(row=6, column=0, padx=10, pady=5, sticky="w")
audio_format_menu = tk.OptionMenu(root, audio_format_var, *audio_formats)
audio_format_menu.config(width=10, state='disabled')
audio_format_menu.grid(row=6, column=1, padx=10, pady=5, sticky="w")

# --- Row 7: Quality ---
label_quality = tk.Label(root, text="")
label_quality.grid(row=7, column=0, padx=10, pady=5, sticky="w")
quality_menu = tk.OptionMenu(root, quality_var, "Choisir")
quality_menu.config(width=40)
quality_menu.grid(row=7, column=1, padx=10, pady=5, sticky="w")

# --- Row 8: Subtitles ---
label_subtitles = tk.Label(root, text="")
label_subtitles.grid(row=8, column=0, padx=10, pady=5, sticky="w")
subtitle_menu = tk.OptionMenu(root, subtitle_var, "Choisir")
subtitle_menu.config(width=40)
subtitle_menu.grid(row=8, column=1, padx=10, pady=5, sticky="w")

# --- Row 9: Download button (centered across two columns) ---
button_download = tk.Button(root, text="", command=start_download, bg="#4CAF50", fg="white", width=20)
button_download.grid(row=9, column=0, columnspan=2, pady=20)

# --- Row 10: Log text area (spanning two columns) ---
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15)
text_area.grid(row=10, column=0, columnspan=2, padx=10, pady=5)

# --- Right Column (Column 3): Thumbnail ---
thumbnail_label = tk.Label(root)
thumbnail_label.grid(row=1, column=3, rowspan=5, padx=10, pady=5, sticky="ne")

# Load configuration and update UI texts now that all widgets exist
load_config()
update_ui_language()

root.mainloop()
