"""DualSense (PS5) -> tablette pour osu! (Windows)

Pavé tactile = position absolue du curseur.
L1 / Croix / L2 = touche Z    R1 / Rond / R2 = touche X
Clic du pavé = clic gauche    Options = activer / désactiver
"""
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

import hid  # paquet pip "hidapi"

user32 = ctypes.windll.user32
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _U)]


def _send(inp):
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def mouse_move(nx, ny):
    i = INPUT(type=0)
    i.u.mi = MOUSEINPUT(int(nx * 65535), int(ny * 65535), 0, 0x0001 | 0x8000, 0, 0)  # MOVE | ABSOLUTE
    _send(i)


def mouse_button(down):
    i = INPUT(type=0)
    i.u.mi = MOUSEINPUT(0, 0, 0, 0x0002 if down else 0x0004, 0, 0)
    _send(i)


def key(scan, down):
    i = INPUT(type=1)
    i.u.ki = KEYBDINPUT(0, scan, 0x0008 | (0 if down else 0x0002), 0, 0)  # SCANCODE (| KEYUP)
    _send(i)


SCAN_Z, SCAN_X = 0x2C, 0x2D
IDS = [(0x054C, 0x0CE6), (0x054C, 0x0DF2)]  # DualSense, DualSense Edge


class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.enabled = True
        self.area = 0.6      # part du pavé utilisée (0.3 à 1.0)
        self.status = "Recherche de la manette..."

    def find(self):
        for vid, pid in IDS:
            for d in hid.enumerate(vid, pid):
                try:
                    dev = hid.device()
                    dev.open_path(d["path"])
                    try:
                        dev.get_feature_report(0x05, 41)  # active le mode complet en Bluetooth
                    except Exception:
                        pass
                    return dev
                except Exception:
                    continue
        return None

    def release_all(self):
        key(SCAN_Z, False)
        key(SCAN_X, False)
        if self.click:
            mouse_button(False)
        self.zd = self.xd = self.click = False

    def run(self):
        self.zd = self.xd = self.click = False
        prev_opt = False
        while self.running:
            dev = self.find()
            if not dev:
                self.status = "Manette introuvable. Branche-la (ferme DS4Windows / Steam)."
                time.sleep(1)
                continue
            self.status = "Manette connectée."
            try:
                while self.running:
                    d = dev.read(128, 50)
                    if not d:
                        continue
                    if len(d) >= 64 and d[0] == 0x01:
                        o = 1
                    elif len(d) >= 70 and d[0] == 0x31:
                        o = 2
                    else:
                        continue
                    l2, r2 = d[o + 4], d[o + 5]
                    b0, b1, b2 = d[o + 7], d[o + 8], d[o + 9]
                    opt = bool(b1 & 0x20)
                    if opt and not prev_opt:
                        self.enabled = not self.enabled
                        if not self.enabled:
                            self.release_all()
                    prev_opt = opt
                    if not self.enabled:
                        self.status = "Désactivé (Options pour réactiver)."
                        continue
                    self.status = "Actif : pose un doigt sur le pavé."
                    z = bool((b0 & 0x20) or (b1 & 0x01) or (b1 & 0x04) or l2 > 100)   # Croix / L1 / L2
                    x = bool((b0 & 0x40) or (b1 & 0x02) or (b1 & 0x08) or r2 > 100)   # Rond / R1 / R2
                    c = bool(b2 & 0x02)                                              # clic du pavé
                    if z != self.zd:
                        key(SCAN_Z, z); self.zd = z
                    if x != self.xd:
                        key(SCAN_X, x); self.xd = x
                    if c != self.click:
                        mouse_button(c); self.click = c
                    t = o + 32
                    if not (d[t] & 0x80):
                        px = (d[t + 1] | ((d[t + 2] & 0x0F) << 8)) / 1919
                        py = ((d[t + 2] >> 4) | (d[t + 3] << 4)) / 1079
                        s = self.area
                        nx = min(1, max(0, (px - 0.5) / s + 0.5))
                        ny = min(1, max(0, (py - 0.5) / s + 0.5))
                        mouse_move(nx, ny)
            except Exception:
                self.status = "Connexion perdue, nouvelle tentative..."
                self.release_all()
                try:
                    dev.close()
                except Exception:
                    pass
                time.sleep(1)
        self.release_all()


def main():
    w = Worker()
    w.start()
    root = tk.Tk()
    root.title("DualSense pour osu!")
    root.geometry("360x230")
    f = ttk.Frame(root, padding=14)
    f.pack(fill="both", expand=True)
    st = ttk.Label(f, text=w.status, wraplength=330)
    st.pack(anchor="w")
    ttk.Label(f, text="Zone du pavé utilisée (petite = curseur plus rapide)").pack(anchor="w", pady=(14, 0))
    val = ttk.Label(f, text="60 %")

    def on_area(v):
        w.area = float(v) / 100
        val.config(text="%d %%" % float(v))

    sc = ttk.Scale(f, from_=30, to=100, value=60, command=on_area)
    sc.pack(fill="x")
    val.pack(anchor="e")
    ttk.Label(f, text="L1/Croix = Z   R1/Rond = X   Clic pavé = clic gauche\nOptions = activer / désactiver",
              justify="left").pack(anchor="w", pady=(10, 0))

    def tick():
        st.config(text=w.status)
        root.after(200, tick)

    def close():
        w.running = False
        time.sleep(0.15)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
