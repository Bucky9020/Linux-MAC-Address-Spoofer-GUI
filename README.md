Markdown
# Linux-MAC-Address-Spoofer-GUI
A simple Tkinter-based tool that allows you to change your MAC address manually or automatically on Linux, Kali, or Parrot OS. This tool is built for educational and privacy purposes — to help users test network spoofing and anonymity setups safely.

---

## 📸 Screenshot
<img width="1920" height="1080" alt="Screenshot at 2025-10-26 10-52-22" src="https://github.com/user-attachments/assets/dd626ab2-2dbb-45ec-aaae-f49b2b9c62c4" />

---

## 🚀 Features
* GUI built with Tkinter (Dark Mode)
* List all available network interfaces
* Change MAC manually or auto-change every few minutes
* Logs every action with timestamp
* Fully compatible with Linux, Kali, and Parrot

## 📋 Requirements
Before running the tool, make sure these dependencies are installed:
```bash
sudo apt update
sudo apt install python3 python3-tk net-tools macchanger
```
Installation
Clone the repository and navigate to the project folder:
git clone [https://github.com/Bucky9020/Linux-MAC-Address-Spoofer-GUI.git](https://github.com/Bucky9020/Linux-MAC-Address-Spoofer-GUI.git)
cd Linux-MAC-Address-Spoofer-GUI

▶️ Run the Tool
```
sudo python3 mac_spoofer_linux.py
⚠️ Note: sudo is required because changing MAC addresses needs root privileges.
```
⚙️ Example of Usage

Select your network interface from the list (e.g., eth0, wlan0).

Enter a new MAC manually or start auto-change mode.

Watch the logs update in real time!

💻 Tested On

Kali Linux 2024.x

Parrot OS 6.x

Ubuntu 22.04 LTS

Disclaimer
This tool is for educational and ethical testing purposes only. Do not use it on networks you don’t own or have permission to test. The author takes no responsibility for misuse.

Credits
Developed by A Bucky — Red Team Researcher & Developer
Inspired by the Windows version of the MAC Spoofer.

License
This project is licensed under the
