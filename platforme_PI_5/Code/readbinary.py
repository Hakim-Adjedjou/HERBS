  GNU nano 5.4                                                                                                                                                                                                                                                          start_capture.py                                                                                                                                                                                                                                                                    
# === UTILITIES ===
def run(command, capture_output=False):
    #print(f"[>] Running: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE if capture_output else None,
                            stderr=subprocess.PIPE if capture_output else None, text=True)
    return result.stdout.strip() if capture_output else None

def setup_monitor_interface():
    #print("\n🔧 Initial CSI setup (one-time)...")
    csi_key = run("mcp -C 1 -N 1 -c 40/80", capture_output=True).strip()
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
        "-vv", "-w", temp_capture_file, "-c", "1000"
    ])
    return temp_capture_file

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
    GPIO.add_event_detect(26, GPIO.FALLING, callback=on_hash_pressed, bouncetime=200)
    try:
        while running:
            if measurement_started and total_written < packet_quota:
                temp_path = capture_new_pcap()
                setText("filtering en \n cours ...")
                matched=filter_pcap(temp_path)
                setText(f"measurement found\n    {matched}/{packet_quota}")
                time.sleep(2)
            elif measurement_started and total_written >= packet_quota:
                writer.close()
                measurement_started = False
                setText("✅ Measurement\nComplete!")
                time.sleep(3)
                setText("Press # for\n new position")
            else:
                time.sleep(1)
    finally:
        GPIO.cleanup()
        if writer:
            writer.close()
        setText("Program stopped\nBye!")




