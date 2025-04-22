import subprocess
import re
from scapy.all import PcapReader, PcapWriter, UDP

# === CONFIGURATION ===
source_macs = {
    "d8:3a:dd:b1:82:f4",
    "d8:3a:dd:af:ef:99",
    "d8:3a:dd:d1:ff:11",
    # Add more MACs if needed
}

packet_quota = 400  # Total packets to collect (from all MACs combined)
output_file = "filtered_output.pcap"
base_capture_name = "measurement-bw20-canal40-position2_3"
capture_index = 1
total_written = 0


# === UTILITIES ===
def run(command, capture_output=False):
    print(f"[>] Running: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE if capture_output else None,
                            stderr=subprocess.PIPE if capture_output else None, text=True)
    return result.stdout.strip() if capture_output else None


# === ONE-TIME SETUP ===
def setup_monitor_interface():
    print("\n🔧 Initial CSI setup (one-time)...")

    # 1. Run MCP and extract Base64 key (used directly)
    print("[1] Running mcp to get CSI key...")
    csi_key = run("mcp -C 1 -N 1 -c 40/80", capture_output=True).strip()
    if not csi_key or len(csi_key) < 10:
        raise ValueError("❌ Invalid or missing key from MCP.")

    print(f"🔑 Using CSI Key as-is: {csi_key}")

    # 2. Restart wlan0
    print("[2] Restarting wlan0...")
    run("sudo ifconfig wlan0 down")
    run("sudo ifconfig wlan0 up")

    # 3. Send key using nexutil
    print("[3] Injecting CSI key using nexutil...")
    run(f"sudo nexutil -Iwlan0 -s500 -b -l34 -v{csi_key}")

    # 4. Set up monitor interface (assumes phy0)
    print("[4] Creating monitor interface on phy0...")
    run("sudo iw phy phy0 interface add mon0 type monitor")
    run("sudo ifconfig mon0 up")
    run("sudo ip link set mon0 up")


# === CAPTURE LOOP ===
def capture_new_pcap():
    global capture_index
    filename = f"{base_capture_name}_{capture_index}.pcap"
    print(f"\n📡 Capturing packets to: {filename}")
    subprocess.run([
        "sudo", "tcpdump", "-i", "wlan0", "dst", "port", "5500",
        "-vv", "-w", filename, "-c", "1000"
    ])
    capture_index += 1
    return filename

def filter_pcap(pcap_path, writer):
    global total_written
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
                print(f"✔ Match #{total_written}: MAC = {csi_src_mac}, Size = {len(bytes(packet))} bytes")
                if total_written >= packet_quota:
                    return match_count
    return match_count


# === EXECUTION ===
if __name__ == "__main__":
    setup_monitor_interface()

    writer = PcapWriter(output_file, append=False, sync=True)
    try:
        while total_written < packet_quota:
            pcap_path = capture_new_pcap()
            matched_now = filter_pcap(pcap_path, writer)
            print(f"🧮 Matched {matched_now} packets from this file. Total so far: {total_written}/{packet_quota}")
    finally:
        writer.close()
        print(f"\n✅ DONE: {total_written} packets saved in {output_file}")

