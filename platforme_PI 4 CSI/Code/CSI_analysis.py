import numpy as np
import struct
from collections import defaultdict, Counter
from scapy.all import PcapReader
from scapy.layers.inet import UDP
import matplotlib.pyplot as plt

def read_pcap_summary(pcap_path, mac_filters=None):
    total_packets = 0
    mac_counter = defaultdict(int)

    with PcapReader(pcap_path) as reader:
        for pkt in reader:
            total_packets += 1
            if pkt.haslayer(UDP):
                payload = bytes(pkt[UDP].payload)
                if len(payload) >= 10:
                    src_mac = ':'.join(f'{b:02x}' for b in payload[4:10])
                    if mac_filters is None or src_mac in mac_filters:
                        mac_counter[src_mac] += 1

    print(f"\U0001F4E6 Total packets in file: {total_packets}")
    if mac_filters:
        for mac in mac_filters:
            print(f"\U0001F50D Packets from {mac}: {mac_counter[mac]}")
    return total_packets, mac_counter

def filter_packets_by_csi_length(pcap_path, expected_len):
    valid_packets = []
    corrupted_indices = []

    with PcapReader(pcap_path) as reader:
        for idx, pkt in enumerate(reader):
            if not pkt.haslayer(UDP):
                continue
            payload = bytes(pkt[UDP].payload)
            if len(payload) < 18 or payload[0:2] != b'\x11\x11':
                continue
            try:
                rssi = struct.unpack("b", payload[2:3])[0]  # Extract signed RSSI
                src_mac = ':'.join(f'{b:02x}' for b in payload[4:10])
                csi_bytes = payload[18:]
                iq_pairs = struct.unpack('<' + 'hh' * (len(csi_bytes) // 4), csi_bytes)
                csi_values = [complex(iq_pairs[i], iq_pairs[i + 1]) for i in range(0, len(iq_pairs), 2)]
                if len(csi_values) == expected_len:
                    valid_packets.append({
                        "mac": src_mac,
                        "rssi": rssi,
                        "csi": csi_values
                    })
                else:
                    corrupted_indices.append((idx, len(csi_values)))
            except Exception as e:
                corrupted_indices.append((idx, str(e)))

    print(f"✅ Valid CSI packets: {len(valid_packets)}")
    print("❌ Corrupted packets (index, length/error):", corrupted_indices)
    return valid_packets, corrupted_indices

def plot_rssi_over_time(valid_packets, mac_addresses=None):
    if mac_addresses:
        filtered_packets = [pkt for pkt in valid_packets if pkt["mac"] in mac_addresses]
    else:
        filtered_packets = valid_packets

    if not filtered_packets:
        print("❌ No matching packets for RSSI plotting.")
        return

    mac_groups = defaultdict(list)
    for i, pkt in enumerate(filtered_packets):
        mac_groups[pkt["mac"]].append((i, pkt["rssi"]))

    plt.figure(figsize=(10, 5))
    for mac, values in mac_groups.items():
        indices, rssis = zip(*values)
        plt.plot(indices, rssis, label=f"{mac}")

    plt.title("RSSI Over Packet Index")
    plt.xlabel("Packet Index")
    plt.ylabel("RSSI (dBm)")
    plt.grid(True)
    plt.legend()
    plt.show()

def remove_redundant_subcarriers(valid_packets):
    csi_by_index = defaultdict(list)
    for pkt in valid_packets:
        for idx, val in enumerate(pkt["csi"]):
            csi_by_index[idx].append(val)

    redundant_indices = []
    for idx, values in csi_by_index.items():
        freq_counter = Counter(values)
        most_common_val, freq = freq_counter.most_common(1)[0]
        if freq > 10:
            print(f"\U0001F7A1 Subcarrier {idx} is redundant ({freq} times): Value = {most_common_val}")
            redundant_indices.append(idx)

    cleaned_packets = []
    for pkt in valid_packets:
        filtered = [val for i, val in enumerate(pkt["csi"]) if i not in redundant_indices]
        cleaned_packets.append({"mac": pkt["mac"], "csi": filtered})

    return cleaned_packets, redundant_indices

def detect_and_remove_spike_subcarriers(cleaned_packets, amplitude_threshold=3000):
    print("\n\U0001F6A8 Detecting amplitude spikes and removing affected subcarriers...")
    spike_indices = set()

    for pkt_idx, pkt in enumerate(cleaned_packets):
        amplitudes = np.abs(pkt["csi"])
        for sub_idx, amp in enumerate(amplitudes):
            if amp > amplitude_threshold:
                print(f"⚠️ Spike detected: Packet #{pkt_idx}, Subcarrier #{sub_idx}, Amplitude = {amp:.2f}")
                spike_indices.add(sub_idx)

    if not spike_indices:
        print("✅ No spikes detected above threshold.")
        return cleaned_packets, []

    cleaned_packets_no_spikes = []
    for pkt in cleaned_packets:
        filtered = [val for i, val in enumerate(pkt["csi"]) if i not in spike_indices]
        cleaned_packets_no_spikes.append({"mac": pkt["mac"], "csi": filtered})

    print(f"\n🧹 Removed subcarrier indices across all packets: {sorted(spike_indices)}")
    return cleaned_packets_no_spikes, sorted(spike_indices)

def plot_csi_analysis(cleaned_packets, packet_indices=None, mac_addresses=None):
    if mac_addresses:
        filtered_packets = [pkt for pkt in cleaned_packets if pkt["mac"] in mac_addresses]
    else:
        filtered_packets = cleaned_packets

    if packet_indices is None or (isinstance(packet_indices, list) and len(packet_indices) == 0):
        indices = range(len(filtered_packets))
    elif isinstance(packet_indices, int):
        indices = [packet_indices]
    else:
        indices = packet_indices

    if not filtered_packets:
        print("❌ No packets matched the given MAC filter.")
        return

    plt.figure(figsize=(10, 4)); plt.title("Amplitude Spectrum (Frequency Domain)-FILE 2"); plt.xlabel("Subcarrier Index"); plt.ylabel("Amplitude"); plt.grid(True)
    plt.figure(figsize=(10, 4)); plt.title("Phase Spectrum (Frequency Domain)-FILE 2"); plt.xlabel("Subcarrier Index"); plt.ylabel("Phase (rad)"); plt.grid(True)
    plt.figure(figsize=(10, 4)); plt.title("Time Domain Magnitude (IFFT)- FILE 2"); plt.xlabel("Sample Index"); plt.ylabel("Magnitude"); plt.grid(True)
    plt.figure(figsize=(10, 4)); plt.title("Time Domain Phase (IFFT)- FILE 2"); plt.xlabel("Sample Index"); plt.ylabel("Phase (rad)"); plt.grid(True)

    for idx in indices:
        pkt = filtered_packets[idx]
        csi = np.array(pkt["csi"])
        amplitudes = np.abs(csi)
        phases = np.angle(csi)
        time_domain = np.fft.ifft(csi)
        time_mag = np.abs(time_domain)
        time_phase = np.angle(time_domain)

        plt.figure(1); plt.plot(amplitudes, label=f"Packet {idx} ({pkt['mac']})")
        plt.figure(2); plt.plot(phases, label=f"Packet {idx} ({pkt['mac']})")
        plt.figure(3); plt.plot(time_mag, label=f"Packet {idx} ({pkt['mac']})")
        plt.figure(4); plt.plot(time_phase, label=f"Packet {idx} ({pkt['mac']})")

    for i in range(1, 5):
        plt.figure(i)
        plt.legend()

    plt.show()

def main_pipeline(pcap_path, bandwidth_mhz, mac_filters=None, packet_indices_to_plot='all', mac_addresses_to_plot=None):
    print("\U0001F680 Starting CSI Analysis Pipeline")
    print("Step 1: Reading PCAP Summary...")
    total_packets, mac_counts = read_pcap_summary(pcap_path, mac_filters)

    expected_csi_len = int(3.2 * bandwidth_mhz)
    print(f"\nStep 2: Filtering packets with expected CSI length = {expected_csi_len}...")
    valid_packets, corrupted_info = filter_packets_by_csi_length(pcap_path, expected_csi_len)

    print("\nStep 3: Removing redundant subcarriers...")
    cleaned_packets, redundant_indices = remove_redundant_subcarriers(valid_packets)

    print("\nStep 4: Detecting and removing spike subcarriers...")
    cleaned_packets_no_spikes, spike_indices = detect_and_remove_spike_subcarriers(cleaned_packets, amplitude_threshold=3000)

    print("\nStep 5: Plotting CSI Analysis...")
    plot_csi_analysis(cleaned_packets_no_spikes, packet_indices=packet_indices_to_plot, mac_addresses=mac_addresses_to_plot)

    print("\nStep 6: Plotting RSSI over time...")
    plot_rssi_over_time(valid_packets, mac_addresses_to_plot)

    return {
        "total_packets": total_packets,
        "mac_packet_counts": mac_counts,
        "valid_packets": valid_packets,
        "corrupted_packets": corrupted_info,
        "cleaned_packets": cleaned_packets,
        "redundant_indices": redundant_indices,
        "spike_indices": spike_indices
    }

if __name__ == "__main__":
    pcap_path = "TEST_analysis_one_position/CSI_pos_99_99_Date_2025-05-15_14-09-16.pcap"
    bandwidth_mhz = 20

    mac_filters = [
        "d8:3a:dd:93:e9:88",
        "d8:3a:dd:93:cc:8e",
        "d8:3a:dd:d1:ff:11",
        "d8:3a:dd:af:ef:99",
        "d8:3a:dd:b7:36:66",
        "d8:3a:dd:b1:82:f4"
    ]

    packet_indices_to_plot = [9,10,11,12,13,14,15,16]
    mac_addresses_to_plot = ["d8:3a:dd:b1:82:f4"]

    results = main_pipeline(
        pcap_path=pcap_path,
        bandwidth_mhz=bandwidth_mhz,
        mac_filters=mac_filters,
        packet_indices_to_plot=packet_indices_to_plot,
        mac_addresses_to_plot=mac_addresses_to_plot
    )
