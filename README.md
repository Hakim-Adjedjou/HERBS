# HERBS

Setting raspberry PI 4 model B as AP :

# 1️⃣ Unblock Wi-Fi and Ensure It Stays Enabled
rfkill list all
sudo rfkill unblock wifi
sudo ip link set wlan0 up
nmcli radio wifi on
sudo systemctl restart NetworkManager

# 2️⃣ Ensure NetworkManager Manages wlan0
nmcli device show wlan0 | grep GENERAL.STATE
sudo nmcli dev set wlan0 managed yes
sudo systemctl restart NetworkManager
nmcli device status

# 3️⃣ Set Up AP Mode ( 2.4 GHZ)
nmcli connection delete "HERBS_AP"
nmcli connection add type wifi ifname wlan0 con-name "HERBS_AP" autoconnect yes ssid "HERBS_AP"
nmcli connection modify "HERBS_AP" 802-11-wireless.mode ap
nmcli connection modify "HERBS_AP" 802-11-wireless.band bg
nmcli connection modify "HERBS_AP" 802-11-wireless.channel 6
nmcli connection modify "HERBS_AP" ipv4.addresses 192.168.1.1/24
nmcli connection modify "HERBS_AP" ipv4.method manual
nmcli connection modify "HERBS_AP" ipv6.method ignore
nmcli connection up "HERBS_AP"

# 4️⃣ Scan for Wi-Fi Networks and Get RSSI
nmcli device wifi list
watch -n 2 nmcli device wifi list


if 5 GHz just change these : 
nmcli connection modify "RaspberryPiAP" 802-11-wireless.band a
nmcli connection modify "RaspberryPiAP" 802-11-wireless.channel 36


###################################################################### ANOTHER METHOD IF YOU WANT TO CHANGE THE BANDWIDTH ###########################################################


✅ 1. Install Required Packages

sudo apt update
sudo apt install hostapd dnsmasq

✅ 2. Stop Conflicting Services

sudo systemctl stop wpa_supplicant
sudo systemctl disable wpa_supplicant
sudo systemctl stop NetworkManager
sudo systemctl disable NetworkManager
sudo killall wpa_supplicant
sudo killall dhclient
sudo rfkill unblock wifi

✅ 3. Set the Regulatory Domain (e.g. France)

sudo iw reg set FR
To make it permanent:
echo 'REGDOMAIN=FR' | sudo tee /etc/default/crda

✅ 4. Create or Edit /etc/hostapd/hostapd.conf

sudo nano /etc/hostapd/hostapd.conf

Paste this:

interface=wlan0
driver=nl80211
ssid=HERBS_AP1
hw_mode=a
channel=36
ieee80211n=1
ht_capab=[HT40+]
wmm_enabled=1
auth_algs=1
ignore_broadcast_ssid=0
#noscan=1


✅ 5. Point hostapd to Config File

sudo nano /etc/default/hostapd

Set:

DAEMON_CONF="/etc/hostapd/hostapd.conf"

    
✅ 6. Configure DHCP Server (dnsmasq)

sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
Add:

interface=wlan0
dhcp-range=192.168.1.10,192.168.1.100,24h

✅ 7. Bring wlan0 into AP Mode

sudo ip link set wlan0 down
sudo iw dev wlan0 set type __ap
sudo ip link set wlan0 up

✅ 8. Enable and Start Services

sudo systemctl enable systemd-networkd
sudo systemctl start systemd-networkd
sudo nano /etc/systemd/network/wlan0.network

copy this : 
[Match]
Name=wlan0

[Network]
Address=192.168.1.1/24



sudo nano /etc/systemd/network/eth0.network

cpoy this : 
[Match]
Name=eth0

[Network]
Address=163.173.96.166/22
Gateway=163.173.96.2
DNS=163.173.128.6


sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

✅ 9. Reboot and Verify

sudo reboot
After reboot, check:

sudo systemctl status hostapd
iw dev wlan0 info

You should see:

AP mode

Channel: 36

Bandwidth: 40 MHz

SSID: HERBS_AP1 broadcasting


if you want 80 Mhz DO THIS in hotspad file : 

interface=wlan0
driver=nl80211
ssid=HERBS_AP1
hw_mode=a
channel=36
ieee80211n=1
ieee80211ac=1
vht_capab=[SHORT-GI-80]
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
ht_capab=[HT40+]
wmm_enabled=1
auth_algs=1
