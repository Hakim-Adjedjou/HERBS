import os
import subprocess
import time

def configure_ap():
    # Write hostapd configuration dynamically
    with open("/etc/hostapd/hostapd.conf", "w") as f:
        f.write("""
interface=wlan0
driver=nl80211
ssid=PythonAP
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=pythonpassword
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
""")
    print("hostapd.conf configured.")

    # Set static IP
    with open("/etc/dhcpcd.conf", "a") as f:
        f.write("""
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
""")
    print("Static IP set for wlan0.")

    # Stop conflicting services
    os.system("sudo systemctl stop wpa_supplicant")

    # Restart necessary services
    os.system("sudo systemctl restart dhcpcd")
    print("Waiting for dhcpcd to apply IP address...")
    time.sleep(5)  # Allow time for dhcpcd to configure the interface

    # Start hostapd manually to mimic working behavior
    print("Starting hostapd...")
    subprocess.run("sudo hostapd /etc/hostapd/hostapd.conf", shell=True)

configure_ap()
