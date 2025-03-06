import subprocess
import time

def wifi_scan_5ghz():
    # **Configuration:** list the 6 target Wi-Fi SSIDs to scan for (case-sensitive)
    target_ssids = ["HERBS_AP1", "HERBS_AP2"]

    # Use the built-in Wi-Fi interface (wlan0 is default on Raspberry Pi)
    wifi_iface = "wlan0"

    # Prepare the iw scan command:
    # - "flush" ensures we don't use cached results&#8203;:contentReference[oaicite:16]{index=16}
    # - "freq ..." limits the scan to channels 36,40,44,48 (5180-5240 MHz)&#8203;:contentReference[oaicite:17]{index=17}
    # You can also add `ssid "<Name>"` filters here if desired to speed up scanning specific networks&#8203;:contentReference[oaicite:18]{index=18}.
    iw_command = ["sudo", "iw", "dev", wifi_iface, "scan", "flush", 
                  "freq", "5180", "5200", "5220", "5240"]

    try:
        # Execute the scan command and capture output
        result = subprocess.run(iw_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("Error running iw scan:", e)
        exit(1)

    output = result.stdout

    # Parse the iw output to extract SSID and signal for each BSS
    networks = {}  # dict to store results by SSID
    current_ssid = None
    current_signal = None

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue  # skip empty lines
        if line.startswith("BSS "):
            # New network entry begins; reset current tracking
            current_ssid = None
            current_signal = None
        elif line.startswith("SSID:"):
            # SSID line example: "SSID: MyNetwork"
            ssid_val = line.partition("SSID: ")[2]  # text after "SSID: "
            current_ssid = ssid_val
            # Store the network with a placeholder for signal (which might come before or after SSID in output)
            if current_ssid not in networks:
                networks[current_ssid] = None
            if current_signal is not None:
                # If we already saw signal before SSID (sometimes signal comes first in output), record it
                networks[current_ssid] = current_signal
        elif line.startswith("signal:"):
            # Signal line example: "signal: -67.00 dBm"
            # Split by spaces and take second token as the numeric value (strip 'dBm')
            parts = line.split()
            if len(parts) >= 2:
                try:
                    sig_val = float(parts[1])
                except ValueError:
                    sig_val = None
            else:
                sig_val = None
            current_signal = sig_val
            # If SSID was already seen for this network, update its signal
            if current_ssid:
                networks[current_ssid] = current_signal

    # Prepare the result vector of six values (in order of target_ssids)
    result_vector = []
    for ssid in target_ssids:
        if ssid in networks and networks[ssid] is not None:
            result_vector.append(networks[ssid])
        else:
            result_vector.append("KO")

    return result_vector  # e.g. [-55.0, -70.0, 'KO', ..., -80.0]

