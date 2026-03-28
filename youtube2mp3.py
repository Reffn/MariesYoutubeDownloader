"""
Maries YouTube-zu-MP3 Downloader
Ordner waehlen, Links einfuegen, fertig.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import subprocess
import sys
import zipfile
import urllib.request
import shutil

FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def get_app_dir():
    """Ordner in dem die .exe oder das .py liegt."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_ytdlp_cmd():
    """Findet yt-dlp: erst neben der .exe, dann im PATH."""
    local = os.path.join(get_app_dir(), "yt-dlp.exe")
    if os.path.isfile(local):
        return local
    return "yt-dlp"


def has_ffmpeg():
    """Prueft ob ffmpeg vorhanden ist (lokal oder im PATH)."""
    local = os.path.join(get_app_dir(), "ffmpeg.exe")
    if os.path.isfile(local):
        return True
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_dir():
    """Findet ffmpeg-Ordner fuer --ffmpeg-location."""
    local = os.path.join(get_app_dir(), "ffmpeg.exe")
    if os.path.isfile(local):
        return get_app_dir()
    return None


def download_ffmpeg(progress_callback=None):
    """Laedt ffmpeg herunter und extrahiert ffmpeg.exe neben die App."""
    app_dir = get_app_dir()
    zip_path = os.path.join(app_dir, "_ffmpeg_temp.zip")

    try:
        # Download mit Fortschritt
        def reporthook(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                pct = min(100, int(block_num * block_size * 100 / total_size))
                progress_callback(f"Lade ffmpeg herunter... {pct}%")

        if progress_callback:
            progress_callback("Lade ffmpeg herunter... 0%")

        urllib.request.urlretrieve(FFMPEG_ZIP_URL, zip_path, reporthook)

        # ffmpeg.exe aus dem ZIP extrahieren
        if progress_callback:
            progress_callback("Entpacke ffmpeg...")

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith("bin/ffmpeg.exe"):
                    with zf.open(name) as src, open(os.path.join(app_dir, "ffmpeg.exe"), "wb") as dst:
                        dst.write(src.read())
                    break

        return True
    except Exception:
        return False
    finally:
        if os.path.isfile(zip_path):
            os.remove(zip_path)

# -- Farben --
BG_TOP = "#667eea"
BG_BOT = "#f093fb"
CARD_BG = "#1a1a2e"
CARD_BG_LIGHT = "#16213e"
ACCENT = "#e94eff"
ACCENT2 = "#667eea"
TEXT = "#ffffff"
TEXT_DIM = "#8888aa"
SUCCESS = "#00e676"
BTN_BG = "#e94eff"
BTN_HOVER = "#ff6fff"
BTN_DISABLED = "#555577"


class GradientFrame(tk.Canvas):
    """Canvas mit vertikalem Farbverlauf als Hintergrund."""

    def __init__(self, parent, color1, color2, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self._c1 = color1
        self._c2 = color2
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("gradient")
        w = self.winfo_width()
        h = self.winfo_height()
        r1, g1, b1 = self._hex(self._c1)
        r2, g2, b2 = self._hex(self._c2)
        steps = max(h, 1)
        for i in range(steps):
            f = i / steps
            r = int(r1 + (r2 - r1) * f)
            g = int(g1 + (g2 - g1) * f)
            b = int(b1 + (b2 - b1) * f)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.create_line(0, i, w, i, fill=color, tags="gradient")
        self.tag_lower("gradient")

    @staticmethod
    def _hex(color):
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


class ProgressBar(tk.Canvas):
    """Eigener huebscher Fortschrittsbalken."""

    def __init__(self, parent, width=500, height=22, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=CARD_BG, highlightthickness=0, **kwargs)
        self._bar_w = width
        self._bar_h = height
        self._value = 0
        self._max = 1
        self._draw()

    def set(self, value, maximum):
        self._value = value
        self._max = max(maximum, 1)
        self._draw()

    def _draw(self):
        self.delete("all")
        # Hintergrund-Track
        self._round_rect(2, 2, self._bar_w - 2, self._bar_h - 2, 10, fill="#2a2a4a", outline="")
        # Gefuellter Bereich
        frac = self._value / self._max
        if frac > 0:
            fill_w = max(20, int((self._bar_w - 4) * frac))
            self._round_rect(2, 2, fill_w + 2, self._bar_h - 2, 10, fill=ACCENT, outline="")
            # Glanz-Effekt
            self._round_rect(2, 2, fill_w + 2, self._bar_h // 2, 10, fill="#ff8fff", outline="",
                             stipple="gray50")

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90,
                        style="pieslice", **kwargs)
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90,
                        style="pieslice", **kwargs)
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90,
                        style="pieslice", **kwargs)
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90,
                        style="pieslice", **kwargs)
        self.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Maries MP3 Downloader")
        self.root.geometry("620x620")
        self.root.resizable(False, False)
        self.is_downloading = False
        self.download_dir = ""

        # Gradient-Hintergrund
        self.bg = GradientFrame(root, BG_TOP, BG_BOT)
        self.bg.pack(fill="both", expand=True)

        # Hauptkarte (zentriert, abgerundet simuliert)
        card_outer = tk.Frame(self.bg, bg=CARD_BG, padx=3, pady=3)
        card_outer.place(relx=0.5, rely=0.5, anchor="center", width=560, height=570)

        card = tk.Frame(card_outer, bg=CARD_BG, padx=25, pady=15)
        card.pack(fill="both", expand=True)

        # --- Titel ---
        tk.Label(card, text="\u266b Maries MP3 Downloader \u266b",
                 font=("Segoe UI", 22, "bold"), bg=CARD_BG, fg=ACCENT).pack(pady=(10, 0))
        tk.Label(card, text="YouTube \u2192 MP3 \u2192 Player. Easy!",
                 font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_DIM).pack(pady=(2, 18))

        # --- Schritt 1: Ordner waehlen ---
        step1 = tk.Frame(card, bg=CARD_BG)
        step1.pack(fill="x")
        tk.Label(step1, text="\u2460  Wo sollen die Songs hin?",
                 font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT).pack(anchor="w")

        self.dir_btn = tk.Button(step1, text="\U0001F4C2  Ordner waehlen...",
                                 font=("Segoe UI", 11), bg=ACCENT2, fg="white",
                                 activebackground=BTN_HOVER, activeforeground="white",
                                 relief="flat", cursor="hand2", padx=16, pady=7,
                                 command=self._choose_dir)
        self.dir_btn.pack(fill="x", pady=(6, 0))

        self.dir_label = tk.Label(step1, text="Noch kein Ordner gewaehlt",
                                  font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DIM, anchor="w")
        self.dir_label.pack(fill="x", pady=(4, 0))

        # --- Schritt 2: Links ---
        step2 = tk.Frame(card, bg=CARD_BG)
        step2.pack(fill="x", pady=(16, 0))

        step2_header = tk.Frame(step2, bg=CARD_BG)
        step2_header.pack(fill="x")
        tk.Label(step2_header, text="\u2461  Deine YouTube-Links hier rein!",
                 font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT).pack(side="left")
        self.counter_label = tk.Label(step2_header, text="",
                                      font=("Segoe UI", 10), bg=CARD_BG, fg=ACCENT)
        self.counter_label.pack(side="right")

        text_frame = tk.Frame(step2, bg=CARD_BG_LIGHT, padx=2, pady=2)
        text_frame.pack(fill="x", pady=(6, 0))

        self.links_text = tk.Text(text_frame, height=9, font=("Consolas", 10),
                                  bg=CARD_BG_LIGHT, fg="#ddddff", insertbackground=ACCENT,
                                  relief="flat", bd=8, wrap="word",
                                  selectbackground=ACCENT, selectforeground="white")
        self.links_text.pack(fill="x")

        # Placeholder
        self._placeholder_on = True
        self.links_text.insert("1.0", "Einfach Links hier reinkopieren...\n(ein Link pro Zeile)")
        self.links_text.config(fg=TEXT_DIM)
        self.links_text.bind("<FocusIn>", self._clear_placeholder)
        self.links_text.bind("<FocusOut>", self._show_placeholder)
        self.links_text.bind("<KeyRelease>", self._update_counter)

        # --- Schritt 3: Download ---
        step3 = tk.Frame(card, bg=CARD_BG)
        step3.pack(fill="x", pady=(18, 0))
        tk.Label(step3, text="\u2462  Und los!",
                 font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT).pack(anchor="w")

        self.download_btn = tk.Button(
            step3, text="\u25B6  Alle Songs herunterladen",
            font=("Segoe UI", 14, "bold"),
            bg=BTN_BG, fg="white", activebackground=BTN_HOVER, activeforeground="white",
            relief="flat", cursor="hand2", padx=20, pady=12,
            command=self._start_download
        )
        self.download_btn.pack(fill="x", pady=(8, 0))

        # Hover-Effekte
        self._add_hover(self.download_btn, BTN_BG, BTN_HOVER)
        self._add_hover(self.dir_btn, ACCENT2, "#7b93ff")

        # --- Fortschritt ---
        progress_frame = tk.Frame(card, bg=CARD_BG)
        progress_frame.pack(fill="x", pady=(14, 0))

        self.progress = ProgressBar(progress_frame, width=500, height=20)
        self.progress.pack()

        self.status_var = tk.StringVar(value="")
        tk.Label(progress_frame, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_DIM).pack(pady=(6, 0))

    # -- Hover-Effekt --
    def _add_hover(self, btn, normal, hover):
        btn.bind("<Enter>", lambda e: btn.config(bg=hover) if btn["state"] != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=normal) if btn["state"] != "disabled" else None)

    # -- Placeholder --
    def _clear_placeholder(self, event=None):
        if self._placeholder_on:
            self.links_text.delete("1.0", "end")
            self.links_text.config(fg="#ddddff")
            self._placeholder_on = False

    def _show_placeholder(self, event=None):
        content = self.links_text.get("1.0", "end").strip()
        if not content:
            self._placeholder_on = True
            self.links_text.insert("1.0", "Einfach Links hier reinkopieren...\n(ein Link pro Zeile)")
            self.links_text.config(fg=TEXT_DIM)

    def _update_counter(self, event=None):
        if self._placeholder_on:
            self.counter_label.config(text="")
            return
        links = self._get_links()
        n = len(links)
        if n == 0:
            self.counter_label.config(text="")
        elif n == 1:
            self.counter_label.config(text="1 Song")
        else:
            self.counter_label.config(text=f"{n} Songs")

    def _choose_dir(self):
        path = filedialog.askdirectory(title="Ordner auf dem MP3-Player waehlen")
        if path:
            self.download_dir = path
            # Pfad kuerzen wenn zu lang
            display = path if len(path) < 55 else "..." + path[-52:]
            self.dir_label.config(text=f"\u2714 {display}", fg=SUCCESS)

    def _get_links(self):
        if self._placeholder_on:
            return []
        raw = self.links_text.get("1.0", "end").strip()
        links = [line.strip() for line in raw.splitlines() if line.strip()]
        return links

    def _start_download(self):
        if self.is_downloading:
            return
        if not self.download_dir:
            messagebox.showwarning("Kein Ordner", "Bitte zuerst den Ordner waehlen! (Schritt 1)")
            return
        links = self._get_links()
        if not links:
            messagebox.showwarning("Keine Links", "Bitte mindestens einen YouTube-Link einfuegen! (Schritt 2)")
            return

        self.is_downloading = True
        self.download_btn.config(state="disabled", bg=BTN_DISABLED, text="\u23F3  Lade herunter...")
        self.progress.set(0, len(links))

        thread = threading.Thread(target=self._download_all, args=(links,), daemon=True)
        thread.start()

    def _download_all(self, links):
        total = len(links)
        ok = 0
        errors = []

        for i, url in enumerate(links, 1):
            self.root.after(0, self._update_status,
                            f"\u266b  Lade Song {i} von {total}...")

            try:
                output_template = os.path.join(self.download_dir, "%(title)s.%(ext)s")
                cmd = [
                    get_ytdlp_cmd(),
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--audio-quality", "0",
                    "--no-playlist",
                    "--output", output_template,
                    url,
                ]
                ffmpeg_dir = get_ffmpeg_dir()
                if ffmpeg_dir:
                    cmd.insert(1, "--ffmpeg-location")
                    cmd.insert(2, ffmpeg_dir)
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    encoding="utf-8", errors="replace"
                )
                if result.returncode == 0:
                    ok += 1
                else:
                    errors.append(f"#{i}: {url}")
            except Exception:
                errors.append(f"#{i}: {url}")

            self.root.after(0, self.progress.set, i, total)

        self.root.after(0, self._on_done, ok, total, errors)

    def _update_status(self, msg):
        self.status_var.set(msg)

    def _on_done(self, ok, total, errors):
        self.is_downloading = False
        self.download_btn.config(state="normal", bg=BTN_BG,
                                 text="\u25B6  Alle Songs herunterladen")
        self._add_hover(self.download_btn, BTN_BG, BTN_HOVER)

        if errors:
            self.status_var.set(f"\u26A0  {ok}/{total} erfolgreich")
            err_list = "\n".join(errors)
            messagebox.showwarning("Teilweise Fehler",
                                   f"{ok}/{total} erfolgreich.\n\nFehlgeschlagen:\n{err_list}")
        else:
            self.status_var.set(f"\u2714  Alle {total} Songs geladen!")
            messagebox.showinfo("Fertig!",
                                f"Alle {total} Songs als MP3 gespeichert!\n\n{self.download_dir}")
            self.links_text.delete("1.0", "end")
            self._placeholder_on = False
            self._show_placeholder()
            self._update_counter()
            self.progress.set(0, 1)


def ensure_ffmpeg(root):
    """Zeigt ein Setup-Fenster und laedt ffmpeg falls noetig."""
    if has_ffmpeg():
        return True

    setup = tk.Toplevel(root)
    setup.title("Ersteinrichtung")
    setup.geometry("420x160")
    setup.resizable(False, False)
    setup.configure(bg=CARD_BG)
    setup.grab_set()

    tk.Label(setup, text="\u2699  Ersteinrichtung",
             font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=ACCENT).pack(pady=(20, 5))
    status = tk.Label(setup, text="ffmpeg wird heruntergeladen...",
                      font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_DIM)
    status.pack(pady=5)

    success = [False]

    def do_download():
        def update(msg):
            root.after(0, lambda: status.config(text=msg))

        ok = download_ffmpeg(progress_callback=update)
        success[0] = ok
        root.after(0, setup.destroy)

    threading.Thread(target=do_download, daemon=True).start()
    root.wait_window(setup)
    return success[0]


def main():
    root = tk.Tk()
    root.withdraw()

    if not ensure_ffmpeg(root):
        messagebox.showerror("Fehler",
                             "ffmpeg konnte nicht heruntergeladen werden.\n"
                             "Bitte pruefe deine Internetverbindung und versuche es erneut.")
        root.destroy()
        return

    root.deiconify()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
