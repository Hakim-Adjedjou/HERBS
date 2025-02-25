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
