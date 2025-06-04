GNU nano 5.4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            start_capture.py                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      import subprocess
import re
import os
import RPi.GPIO as GPIO
import time
from grove_rgb_lcd import *
from datetime import datetime
from scapy.all import PcapReader, PcapWriter, UDP

# === CONFIGURATION ===
source_macs = {
    "d8:3a:dd:b1:82:f4",
    "d8:3a:dd:b7:36:66",
    "d8:3a:dd:af:ef:99",
    "d8:3a:dd:d1:ff:11",
    "d8:3a:dd:93:cc:8e",
    "d8:3a:dd:93:e9:88",
    "d8:3a:dd:fc:f7:a7",
    "d8:3a:dd:fc:f6:d3",
    "2c:cf:67:22:85:6e",
}

packet_quota = 500
total_written = 0
current_position = (0, 0)
writer = None
measurement_started = False
running = True

# === GPIO Keypad Configuration ===
ROW_PINS = [20, 5, 19, 26]
COL_PINS = [13, 12, 16]
GPIO.setmode(GPIO.BCM)
for col in COL_PINS:
    GPIO.setup(col, GPIO.OUT)
    GPIO.output(col, GPIO.LOW)
for row in ROW_PINS:
    GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === KEY SCAN ===
def get_key():
    while True:
        for col_index, col_pin in enumerate(COL_PINS):
            GPIO.output(col_pin, GPIO.LOW)
            for other_col in COL_PINS:
                if other_col != col_pin:
                    GPIO.output(other_col, GPIO.HIGH)
            for row_index, row_pin in enumerate(ROW_PINS):
                if GPIO.input(row_pin) == GPIO.LOW:
                    time.sleep(0.02)
                    while GPIO.input(row_pin) == GPIO.LOW:
                        time.sleep(0.01)
                    for c in COL_PINS:
                        GPIO.output(c, GPIO.LOW)
                    key_map = [
                        ['1','2','3'],
                        ['4','5','6'],
                        ['7','8','9'],
                        ['*','0','#']
                    ]
                    return key_map[row_index][col_index]
        time.sleep(0.01)

def _read_number(label, max_digits, min_val, max_val):
    num_str = ""
    setText(f"{label}: _\n" + " " * 16)
    while True:
        key = get_key()
        if key.isdigit():
            if len(num_str) < max_digits:
                num_str += key
                setText(f"{label}: {num_str}_\n" + " " * 16)
            else:
                setText(f"  Max {max_digits} digits!\n Try again")
                time.sleep(1)
                num_str = ""
                setText(f"{label}: _\n" + " " * 16)
        elif key == '*':
            if num_str == "":
                setText("  No input!  \n Enter number")
                time.sleep(1)
                num_str = ""
                setText(f"{label}: _\n" + " " * 16)
                continue
            value = int(num_str)
            if value < min_val or value > max_val:
                setText(f"Out of range!\n({min_val}-{max_val})")
                time.sleep(1)
                num_str = ""
                setText(f"{label}: _\n" + " " * 16)
                continue
            else:
                return value
        elif key == '#':
            setText(" Entry cancelled.\nReturning..")
            time.sleep(1)
            return None
        else:
            continue

def set_position():
    global current_position
    x = _read_number("X", 4, 0, 9999)
    if x is None: return
    y = _read_number("Y", 4, 0, 9999)
    if y is None: return
    current_position = (x, y)
    setText(f"X:{x}, Y:{y}\nReady to start")
    time.sleep(2)
    setText("Press # and \n choose start")

def update_quota():
    global packet_quota
    new_quota = _read_number("New Quota", 4, 1, 9999)
    if new_quota is not None:
        packet_quota = new_quota
        setText(f"Quota updated\n to {packet_quota}")
        time.sleep(2)

def start_measurement():
    global writer, measurement_started, output_file, total_written
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    x, y = current_position

    #base folder="~/measurements_CSI/measurements_canal40_bw20_HT_5GHz_wifi/museum"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_HT_5GHz_wifi/lab"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_HT_5GHz_wifi/grenoble"

    #base folder="~/measurements_CSI/measurements_canal40_bw20_VHT_5GHz_wifi/museum"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_VHT_5GHz_wifi/lab"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_VHT_5GHz_wifi/grenoble"

    #base folder="~/measurements_CSI/measurements_canal40_bw20_nmcli_code_AP_5GHz_wifi/museum"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_nmcli_code_AP_5GHz_wifi/lab"
    #base folder="~/measurements_CSI/measurements_canal40_bw20_nmcli_code_AP_5GHz_wifi/grenoble"

    #base folder="~/measurements_CSI/measurements_canal40_bw80_VHT_5GHz_wifi/museum"
    base folder="~/measurements_CSI/measurements_canal40_bw80_VHT_5GHz_wifi/lab"
    #base folder="~/measurements_CSI/measurements_canal40_bw80_VHT_5GHz_wifi/grenoble"


    # Create the dated folder if it doesn't exist
    os.makedirs(date_folder, exist_ok=True)

    output_file = os.path.join(date_folder, f"CSI_pos_{x}_{y}_Date_{timestamp_str}.pcap")
    writer = PcapWriter(output_file, append=False, sync=True)
    total_written = 0
    measurement_started = True
    setText("Measurement\n  started")
    time.sleep(2)


def stop_program():
    global running
    running = False
    setText("Program exiting\n  please wait")
    time.sleep(2)

def exit_menu():
    setText("1: Exit Only\n2: Shutdown")
    while True:
        key = get_key()
        if key == '1':
            stop_program()
            break
        elif key == '2':
            setText("Shutting down...\nPlease wait.")
            time.sleep(2)
            run("sudo shutdown now")
            break
        else:
            setText("Invalid choice\n1=Exit 2=Off")
            time.sleep(1)

def config_menu():
    setText("* Config Menu *\n")
    time.sleep(2)
    setText("1:Start 2:Quota\n3:POS  4:Exit")
    while True:
        choice = get_key()
        if choice == '1':
            start_measurement()
            break
        elif choice == '2':
            update_quota()
            break
        elif choice == '3':
            set_position()
            break
        elif choice == '4':
            exit_menu()
            break
        else:
            setText("Invalid choice\ntry again")
            time.sleep(1)
            setText("1:Start 2:Q 3:P 4:X")

def on_hash_pressed(channel):
    GPIO.remove_event_detect(26)
    time.sleep(0.05)
    key = get_key()
    if key == "#":
        config_menu()
    GPIO.add_event_detect(26, GPIO.FALLING, callback=on_hash_pressed, bouncetime=200)

# === UTILITIES ===
def run(command, capture_output=False):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE if capture_output else None,
                            stderr=subprocess.PIPE if capture_output else None, text=True)
    return result.stdout.strip() if capture_output else None

def setup_monitor_interface():
    csi_key = run("mcp -C 1 -N 1 -c 40/20", capture_output=True).strip()
    if not csi_key or len(csi_key) < 10:
        raise ValueError("❌ Invalid or missing key from MCP.")
    run("sudo ifconfig wlan0 down")
    run("sudo ifconfig wlan0 up")
    run(f"sudo nexutil -Iwlan0 -s500 -b -l34 -v{csi_key}")
    run("sudo iw phy phy0 interface add mon0 type monitor")
    run("sudo ifconfig mon0 up")
    run("sudo ip link set mon0 up")

def capture_new_pcap():
    temp_capture_file = "temp_capture.pcap"
    if os.path.exists(temp_capture_file):
        os.remove(temp_capture_file)
    subprocess.run([
        "sudo", "tcpdump", "-i", "wlan0", "dst", "port", "5500",
        "-vv", "-w", temp_capture_file, "-c", "600"
    ])
    return temp_capture_file

#======= no filter ==============
#def filter_pcap(pcap_path):
#    global total_written, writer
#    match_count = 0
#    with PcapReader(pcap_path) as reader:
#        for packet in reader:
#            if not packet.haslayer(UDP):
#                continue
#            payload = bytes(packet[UDP].payload)
#            if len(payload) < 10 or payload[0:2] != b'\x11\x11':
#                continue
#            writer.write(packet)
#            total_written += 1
#            match_count += 1
#            if total_written >= packet_quota:
#                return match_count
#    return match_count


#======== with filter
def filter_pcap(pcap_path):
    global total_written, writer
    match_count = 0
    with PcapReader(pcap_path) as reader:
        for packet in reader:
            if not packet.haslayer(UDP):
                continue
            payload = bytes(packet[UDP].payload)
            if len(payload) < 10 or payload[0:2] != b'\x11\x11':
                continue
            mac_bytes = payload[4:10]
            if len(mac_bytes) != 6:
                continue
            csi_src_mac = ':'.join(f'{b:02x}' for b in mac_bytes)
            if csi_src_mac.lower() in source_macs:
                writer.write(packet)
                total_written += 1
                match_count += 1
                if total_written >= packet_quota:
                    return match_count
    return match_count
# === MAIN LOOP ===
if __name__ == "__main__":
    setup_monitor_interface()
    setRGB(255, 255, 255)
    setText("Press # for\nconfiguration")
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    GPIO.add_event_detect(26, GPIO.FALLING, callback=on_hash_pressed, bouncetime=200)
    try:
        while running:
            if measurement_started and total_written < packet_quota:
                temp_path = capture_new_pcap()
                setText("filtering en \n cours ...")
                matched = filter_pcap(temp_path)
                setText(f"Packets:\n{matched}/{packet_quota}")
                time.sleep(2)
            elif measurement_started and total_written >= packet_quota:
                writer.close()
                measurement_started = False
                setText(" Measurement\nComplete!")
                time.sleep(3)
                setText("Press # for\n new position")
            else:
                time.sleep(1)
    finally:
        GPIO.cleanup()
        if writer:
            writer.close()
        setText("Program stopped\nBye!")








                                                                                                                                                                                                                       
