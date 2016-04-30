import time
from control import *

import job_pb2
import status_pb2

def start_traffic(q, server_id, tx_mbps, dur_sec):
    try:
        dur_msec = int(dur_sec * 1000)
        q.add_job(server_id, Request(0, [Job({
            "tx_rate": tx_mbps,
            "duration": dur_msec,
            "warmup": 1 * 1000,
            "num_flows": 1,
            "size_min": 64,
            "size_max": 64,
            "life_min": dur_sec* 1000,
            "life_max": dur_sec * 1000,
            "port_min": 1024,
            "port_max": 2048,
            "latency": True,
             "src_mac": "68:05:ca:00:01",
             "dst_mac": "68:05:ca:00:02"})]))
        time.sleep(dur_sec + 2)
        print "Issuing print"
        q.results_event.clear()
        q.add_job(server_id, Request(0, [Job({"print": True, \
            "port": "00:00:00:00:00:00"})]))
    except:
        q.add_job(server_id, Request(0, [Job({"stop": True, "print": True, \
                "port": "00:00:00:00:00:00"})]))
    finally:
        print "Waiting for event"
        time.sleep(1)
        print "Done Waiting for event"
        m = q.results
        rx_mpps_mean = 0
        tx_mpps_mean = 0
        for v in m.itervalues():
            for measure in v.itervalues():
                if measure['rx_mpps_mean'] > 0.0: 
                    rx_mpps_mean += measure['rx_mpps_mean']
                    tx_mpps_mean += measure['tx_mpps_mean']
        print rx_mpps_mean, tx_mpps_mean

def main():
    q = Q("127.0.0.1", 1800, None, None)
    q.start()

    server_ip = "127.0.0.1"
    server_port = 5000
    server_id = "%s:%d" % (server_ip, server_port)
    q.add_node(Node(server_id, server_ip, server_port))
    print("Starting traffic. Press ctrl + c to stop")
    # Generate 1 10gbps flow of 64B packets for 10 seconds
    start_traffic(q, server_id, -1, 15)
    q.stop()

if __name__ == '__main__':
    main()
