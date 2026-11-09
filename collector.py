import time
import psutil
import pandas as pd
import os
import sys

LOG_FILE = "traffic_logs.csv"
INTERVAL = 1.0

def collect_telemetry(duration_seconds=60, is_attack_label=0):
    mode_str = "ATAQUE (MITRE)" if is_attack_label == 1 else "NORMAL (BASELINE)"
    print(f"-> Coletando {duration_seconds}s de telemetria [{mode_str}]...")
    records = []
    
    last_net = psutil.net_io_counters()
    
    for sec in range(1, duration_seconds + 1):
        time.sleep(INTERVAL)
        current_net = psutil.net_io_counters()
        
        bytes_sent = current_net.bytes_sent - last_net.bytes_sent
        bytes_recv = current_net.bytes_recv - last_net.bytes_recv
        packets_sent = current_net.packets_sent - last_net.packets_sent
        packets_recv = current_net.packets_recv - last_net.packets_recv
        
        total_packets = packets_sent + packets_recv
        total_bytes = bytes_sent + bytes_recv
        
        packet_size = (total_bytes / total_packets) if total_packets > 0 else 0.0
        packet_freq = float(total_packets) / INTERVAL
        cpu_usage = psutil.cpu_percent()
        mem_usage = psutil.virtual_memory().percent
        conn_count = len(psutil.net_connections(kind='inet'))
        
        records.append({
            'packet_size': packet_size,
            'packet_freq': packet_freq,
            'cpu_usage': cpu_usage,
            'mem_usage': mem_usage,
            'conn_count': conn_count,
            'is_attack': is_attack_label
        })
        last_net = current_net
        if sec % 10 == 0 or sec == duration_seconds:
            print(f"   [{sec}/{duration_seconds}s] capturado...")

    df_new = pd.DataFrame(records)
    
    if os.path.exists(LOG_FILE):
        df_new.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        df_new.to_csv(LOG_FILE, index=False)
        
    print(f"-> Gravado com sucesso em '{LOG_FILE}'.")

if __name__ == "__main__":
    label = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    collect_telemetry(duration_seconds=duration, is_attack_label=label)