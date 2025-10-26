#!/usr/bin/env python3
# mac_spoofer_linux.py
# Linux MAC Address Spoofer GUI (Kali / Parrot / Debian / Ubuntu compatible)
# Author: (yours)
# Requires: python3, tkinter (python3-tk). Optional: macchanger (recommended).

import os
import re
import subprocess
import threading
import time
import random
import shutil
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

APP_TITLE = "Linux MAC Address Spoofer (Kali/Parrot Friendly)"

def is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False

def run_cmd(cmd, capture=True):
    """Run command list or string. Return (returncode, stdout, stderr)."""
    try:
        if isinstance(cmd, str):
            proc = subprocess.run(cmd, shell=True, capture_output=capture, text=True, check=False)
        else:
            proc = subprocess.run(cmd, capture_output=capture, text=True, check=False)
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except Exception as e:
        return 255, "", str(e)

def list_interfaces():
    """Return list of (ifname, mac) using `ip -o link` parsing."""
    code, out, err = run_cmd(["ip", "-o", "link", "show"])
    if code != 0:
        return []
    lines = out.splitlines()
    ifs = []
    for line in lines:
        # format: "1: lo: <LOOPBACK,...> mtu ... link/loopback 00:00:00:00:00:00 ..."
        m = re.match(r'^\d+:\s+([^:]+):.*link/\S+\s+([0-9a-fA-F:]{17})', line)
        if m:
            name = m.group(1)
            mac = m.group(2)
            if name != "lo":
                ifs.append((name, mac))
    return ifs

def normalize_mac(mac_str):
    """Return 12 hex uppercase or None if invalid."""
    cleaned = re.sub(r'[^0-9A-Fa-f]', '', mac_str).upper()
    if len(cleaned) != 12 or not re.fullmatch(r'[0-9A-F]{12}', cleaned):
        return None
    return cleaned

def format_mac12(mac12):
    return ':'.join(mac12[i:i+2] for i in range(0,12,2))

def random_locally_administered_mac():
    # first octet must have the local-admin bit set (02,06,0A,...). Use 02 for simplicity.
    return "{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}".format(
        0x02,
        random.randint(0,255),
        random.randint(0,255),
        random.randint(0,255),
        random.randint(0,255),
        random.randint(0,255),
    )

class MacSpooferApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("820x540")
        self.use_macchanger = shutil.which("macchanger") is not None
        self.is_root = is_root()
        self.stop_event = threading.Event()
        self.auto_thread = None

        # UI
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except:
            pass

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        top = ttk.LabelFrame(main, text="1) Select Interface", padding=8)
        top.pack(fill=tk.X, pady=6)
        self.iface_combo = ttk.Combobox(top, state='readonly', width=60)
        self.iface_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(top, text="Refresh", command=self.load_ifaces).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Show Current MAC", command=self.show_current_mac).pack(side=tk.LEFT, padx=5)

        manual = ttk.LabelFrame(main, text="2) Manual Change", padding=8)
        manual.pack(fill=tk.X, pady=6)
        ttk.Label(manual, text="New MAC:").pack(side=tk.LEFT, padx=5)
        self.mac_entry = ttk.Entry(manual, width=40)
        self.mac_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(manual, text="Apply Now", command=self.manual_change).pack(side=tk.LEFT, padx=5)
        ttk.Button(manual, text="Random (local-admin)", command=self.fill_random).pack(side=tk.LEFT, padx=5)

        auto = ttk.LabelFrame(main, text="3) Automatic Change", padding=8)
        auto.pack(fill=tk.X, pady=6)
        ttk.Label(auto, text="Every (minutes):").pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(auto, width=10)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        self.auto_start_btn = ttk.Button(auto, text="Start Auto", command=self.start_auto)
        self.auto_start_btn.pack(side=tk.LEFT, padx=5)
        self.auto_stop_btn = ttk.Button(auto, text="Stop Auto", command=self.stop_auto, state=tk.DISABLED)
        self.auto_stop_btn.pack(side=tk.LEFT, padx=5)

        options = ttk.LabelFrame(main, text="Options", padding=8)
        options.pack(fill=tk.X, pady=6)
        self.use_macchanger_var = tk.BooleanVar(value=self.use_macchanger)
        self.chk_macchanger = ttk.Checkbutton(options, text=f"Use macchanger (found: {self.use_macchanger})", variable=self.use_macchanger_var)
        self.chk_macchanger.pack(side=tk.LEFT, padx=5)
        self.dryrun_var = tk.BooleanVar(value=not self.is_root)
        self.chk_dryrun = ttk.Checkbutton(options, text="Dry run / Mock mode (don't change system) - useful if not root", variable=self.dryrun_var)
        self.chk_dryrun.pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main, text="Logs", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=6)
        self.logbox = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=14)
        self.logbox.pack(fill=tk.BOTH, expand=True)

        # initial load
        self.load_ifaces()
        self.log(f"macchanger available: {self.use_macchanger}. Running as root: {self.is_root}. If not root, enable Dry run to avoid errors.")

    # UI helpers
    def log(self, message):
        ts = time.strftime("%H:%M:%S")
        self.logbox.insert(tk.END, f"[{ts}] {message}\n")
        self.logbox.see(tk.END)
        self.root.update_idletasks()

    def load_ifaces(self):
        self.log("Loading interfaces...")
        ifs = list_interfaces()
        if not ifs:
            self.log("No interfaces found or `ip` command failed.")
            self.iface_combo['values'] = []
            return
        display = [f"{name}    [{mac}]" for name, mac in ifs]
        names = [name for name, mac in ifs]
        self.iface_map = {f"{name}    [{mac}]": name for name, mac in ifs}
        self.iface_combo['values'] = display
        if display:
            self.iface_combo.current(0)
            self.log(f"Found {len(display)} interfaces.")
        else:
            self.log("No usable interfaces found.")

    def get_selected_iface(self):
        txt = self.iface_combo.get()
        if not txt:
            return None
        # mapping
        try:
            return self.iface_map.get(txt, txt.split()[0])
        except Exception:
            return txt.split()[0]

    def show_current_mac(self):
        iface = self.get_selected_iface()
        if not iface:
            self.log("Select an interface first.")
            return
        code, out, err = run_cmd(["ip", "-o", "link", "show", iface])
        if code != 0:
            self.log(f"Failed to read interface {iface}: {err or out}")
            return
        m = re.search(r'link/\S+\s+([0-9a-fA-F:]{17})', out)
        if m:
            self.log(f"{iface} current MAC: {m.group(1)}")
        else:
            self.log(f"Could not parse MAC for {iface}. Output: {out}")

    def fill_random(self):
        mac12 = random_locally_administered_mac()
        self.mac_entry.delete(0, tk.END)
        self.mac_entry.insert(0, format_mac12(mac12))

    # Core actions
    def manual_change(self):
        iface = self.get_selected_iface()
        if not iface:
            self.log("Select an interface first.")
            return
        mac_raw = self.mac_entry.get().strip()
        norm = normalize_mac(mac_raw)
        if not norm:
            self.log("Invalid MAC format. Use 12 hex digits, or aa:bb:cc:dd:ee:ff.")
            return
        # run in thread
        threading.Thread(target=self._apply_mac, args=(iface, norm), daemon=True).start()

    def _apply_mac(self, iface, mac12):
        mac_colon = format_mac12(mac12)
        dryrun = self.dryrun_var.get()
        use_mc = self.use_macchanger_var.get() and shutil.which("macchanger") is not None

        self.log(f"Applying MAC {mac_colon} to {iface} (dryrun={dryrun}, use_macchanger={use_mc})")

        if dryrun:
            self.log("(Dry run) Would: bring {iface} down -> set MAC -> bring up -> verify")
            return

        # try macchanger path first if requested
        if use_mc:
            code, out, err = run_cmd(["macchanger", "-m", mac_colon, iface])
            if code == 0:
                self.log(f"macchanger succeeded: {out}")
                # verify
                time.sleep(1)
                self.show_current_mac()
                return
            else:
                self.log(f"macchanger failed (trying ip): {err or out}")

        # fallback to ip commands
        # bring down
        code, out, err = run_cmd(["ip", "link", "set", iface, "down"])
        if code != 0:
            self.log(f"Failed to bring down {iface}: {err or out}")
            return
        # set mac
        code, out, err = run_cmd(["ip", "link", "set", "dev", iface, "address", mac_colon])
        if code != 0:
            self.log(f"Failed to set MAC on {iface}: {err or out}")
            # try to bring up anyway
            run_cmd(["ip", "link", "set", iface, "up"])
            return
        # bring up
        code, out, err = run_cmd(["ip", "link", "set", iface, "up"])
        if code != 0:
            self.log(f"Failed to bring up {iface}: {err or out}")
            return
        # small delay then verify
        time.sleep(1)
        self.show_current_mac()
        self.log(f"MAC {mac_colon} applied to {iface}.")

    # Auto-change worker
    def auto_worker(self, iface, interval_seconds):
        self.log("Auto-change worker started.")
        while not self.stop_event.is_set():
            mac12 = random_locally_administered_mac()
            self.log(f"Auto: changing {iface} -> {format_mac12(mac12)}")
            self._apply_mac(iface, mac12)
            # wait with stop check
            waited = 0
            while waited < interval_seconds:
                if self.stop_event.wait(1.0):
                    break
                waited += 1
        self.log("Auto-change worker stopped.")
        self.root.after(0, lambda: (self.auto_start_btn.config(state=tk.NORMAL), self.auto_stop_btn.config(state=tk.DISABLED)))

    def start_auto(self):
        iface = self.get_selected_iface()
        if not iface:
            self.log("Select an interface first.")
            return
        im = self.interval_entry.get().strip()
        try:
            minutes = int(im)
            if minutes <= 0:
                raise ValueError
        except Exception:
            self.log("Invalid interval. Enter positive integer minutes.")
            return
        interval_seconds = minutes * 60
        self.stop_event.clear()
        self.auto_start_btn.config(state=tk.DISABLED)
        self.auto_stop_btn.config(state=tk.NORMAL)
        self.auto_thread = threading.Thread(target=self.auto_worker, args=(iface, interval_seconds), daemon=True)
        self.auto_thread.start()

    def stop_auto(self):
        self.stop_event.set()
        self.log("Stop signal sent to auto worker.")
        self.auto_start_btn.config(state=tk.NORMAL)
        self.auto_stop_btn.config(state=tk.DISABLED)

def main():
    # check tkinter availability
    try:
        root = tk.Tk()
    except Exception as e:
        print("Tkinter not available or cannot start GUI:", e)
        sys.exit(1)

    app = MacSpooferApp(root)
    # show warning if not root and dryrun not enabled
    if not is_root():
        app.log("Warning: Not running as root. Tool will default to dry-run. (Enable Dry run or run with sudo to actually change MAC.)")
        messagebox.showwarning(APP_TITLE, "Not running as root. Tool will default to Dry run. Run with sudo to change MACs.")
    root.mainloop()

if __name__ == "__main__":
    main()
