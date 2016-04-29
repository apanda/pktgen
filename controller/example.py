import time
from control import *

import job_pb2
import status_pb2

def start_traffic(q, server_id, tx_mbps, dur_sec):
    try:
        dur_msec = int(dur_sec * 1000)
        q.add_job(server_id, Job(1, {
            "tx_rate": tx_mbps,
            "duration": dur_msec,
            "warmup": 10,
            "num_flows": 100,
            "size_min": 60,
            "size_max": 60,
            "life_min": 1000,
            "life_max": 4500,
            "port_min": 1024,
            "port_max": 2048,
            "latency": True}))
        time.sleep(600)
        print "Issuing stop"
        q.results_event.clear()
        q.add_job(server_id, Job(0, {"stop": True, "print": True}))
    except:
        q.add_job(server_id, Job(0, {"stop": True, "print": True}))
    finally:
        print "Waiting for event"
        q.results_event.wait(10)
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
    start_traffic(q, server_id, 14000, 640000)
    q.stop()

if __name__ == '__main__':
    main()
