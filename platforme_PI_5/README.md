# 📡 Indoor Localization Experiment Guide

This project contains configurations and materials for **waveform analysis, modulation techniques, and electromagnetic wave experiments** in the context of **indoor localization**.

---

## 🚀 Getting Started

### 1️⃣ **Replicate the Experiment Setup**
If you want to **replicate the exact same configuration**, follow these steps:
- Download the **pre-configured Raspberry Pi images** from `images/`:
  - 📥 **`pi4_image.img`** → for Raspberry Pi 4  
  - 📥 **`pi5_image.img`** → for Raspberry Pi 5  
- Flash the image to an SD card using **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**.
- Modify the **network configuration** (IP addresses, DHCP settings) as needed.

---

## 📖 **Step-by-Step Configuration Guide**
This guide walks you through setting up each component manually.

### 🔹 **2.1 Connecting a Raspberry Pi to Your Network**
> 🌐 *Enterprise, School WiFi Setup (WPA2-Enterprise, Static IP, etc.)*
```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

