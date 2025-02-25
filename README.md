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
nmcli connection delete "RaspberryPiAP"
nmcli connection add type wifi ifname wlan0 con-name "RaspberryPiAP" autoconnect yes ssid "RaspberryPiAP"
nmcli connection modify "RaspberryPiAP" 802-11-wireless.mode ap
nmcli connection modify "RaspberryPiAP" 802-11-wireless.band bg
nmcli connection modify "RaspberryPiAP" 802-11-wireless.channel 6
nmcli connection modify "RaspberryPiAP" ipv4.addresses 192.168.1.1/24
nmcli connection modify "RaspberryPiAP" ipv4.method manual
nmcli connection modify "RaspberryPiAP" ipv6.method ignore
nmcli connection up "RaspberryPiAP"

# 4️⃣ Scan for Wi-Fi Networks and Get RSSI
nmcli device wifi list
watch -n 2 nmcli device wifi list


if 5 GHz just change these : 
nmcli connection modify "RaspberryPiAP" 802-11-wireless.band a
nmcli connection modify "RaspberryPiAP" 802-11-wireless.channel 36
