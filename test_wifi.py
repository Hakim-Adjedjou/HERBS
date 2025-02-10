import subprocess
import re
import time

def scan_wifi():
    # Ensure wlan0 interface is up
    subprocess.run(["sudo", "ifconfig", "wlan0", "up"])

    # Regex to extract SSID and RSSI (signal level)
    ssid_regex = re.compile(r'ESSID:"(.*?)"')
    rssi_regex = re.compile(r'Signal level=(-?\d+) dBm')

    previous_time = time.time()  # Store the initial time

    while True:
        try:
            # Run iwlist scan command to fetch Wi-Fi networks
            result = subprocess.check_output(["sudo", "iwlist", "wlan0", "scan"], encoding="utf-8")
        except subprocess.CalledProcessError as e:
            print(f"Error during Wi-Fi scan: {e}")
            return []

        # Find all SSIDs and RSSI values
        ssids = ssid_regex.findall(result)
        rssi_values = rssi_regex.findall(result)

        # Only look for the latest RSSI value of "eduroam"
        rssi_of_eduroam = None
        for ssid, rssi in zip(ssids, rssi_values):
            if ssid == "eduroam":
                rssi_of_eduroam = int(rssi)
                break

        if rssi_of_eduroam is not None:
            # Calculate the time difference
            current_time = time.time()  # Get the current time for this measurement
            elapsed_time = current_time - previous_time  # Calculate the time difference
            elapsed_time_rounded = round(elapsed_time, 2)  # Round to two decimal places

            # Print the result with the elapsed time and RSSI of "eduroam"
            print(f"SSID: eduroam, RSSI: {rssi_of_eduroam} dBm, Time since last scan: {elapsed_time_rounded} seconds")

            previous_time = current_time  # Update the previous time to the current time

       

if __name__ == "__main__":
    scan_wifi()


