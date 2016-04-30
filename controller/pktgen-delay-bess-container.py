# -*- coding: utf-8 -*-

"""
pktgen_scheduler.py
---------
pktgen_scheduler talks with pktgen_servers, schedules
jobs and listens for statuses.
"""

import sys
import json
import code
import Queue
import struct
import socket
import logging
import argparse
import threading
import time
import math
from control import *
import paramiko
import subprocess
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
from common import *

import job_pb2
import status_pb2

def measure_delay(q, pgen_server, pgen_port, server, out):
    handle = None
    conn = connect_test_machine(server)
    key = add_server(q, pgen_server, pgen_port)
    count = 2
    measure_time = 20 # seconds
    start_bess = \
            "/opt/e2d2/scripts/start-bess-container.sh 4,5 %d %d"%(count, count)
    start_container = \
    '/opt/e2d2/container/run-container.sh start fancy %d 8 6 "' + \
           ' '.join(map(lambda c: "bess:rte_ring%d"%c, range(count))) + '"'
    stop_container = "/opt/e2d2/container/run-container.sh stop fancy"
    o, e = exec_command_and_wait(conn, stop_container)
    kill_all = "/opt/e2d2/scripts/kill-all.sh"
    o, e = exec_command_and_wait(conn, kill_all)
    for delay in xrange(0, 2000, 50):
        try:
            success = False
            while not success:
                success = True
                handle = restart_pktgen(handle, pgen_port, "81:00", count)
                print "Starting BESS"
                o, e = exec_command_and_wait(conn, start_bess)
                print "Out ", '\n\t'.join(o)
                print "Err ", '\n\t'.join(e)
                print "Starting container"
                o,e = exec_command_and_wait(conn, start_container%(delay))
                print "Out ", '\n\t'.join(o)
                print "Err ", '\n\t'.join(e)
                run_flow_dynamic(q, key)
                print "Stopping"
                m = measure_pkts(q, key)
                rx_mpps_mean = 0
                tx_mpps_mean = 0
                for v in m.itervalues():
                    for measure in v.itervalues():
                        if measure['rx_mpps_mean'] > 0.0: 
                            rx_mpps_mean += measure['rx_mpps_mean']
                            tx_mpps_mean += measure['tx_mpps_mean']
                o, e = exec_command_and_wait(conn, stop_container)
                print "Out ", '\n\t'.join(o)
                print "Err ", '\n\t'.join(e)
                if tx_mpps_mean < 1.0:
                    success = False
                    print "Restarting"
                else:
                    print delay, rx_mpps_mean, tx_mpps_mean
                    print >>out, delay, rx_mpps_mean, tx_mpps_mean
                    out.flush()
        except:
            print "Caught exception"
            o, e = exec_command_and_wait(conn, stop_container)
            print "Out ", '\n\t'.join(o)
            print "Err ", '\n\t'.join(e)
            if handle:
               handle.kill()
               handle.wait()
            raise
    if handle:
       handle.kill()
       handle.wait()
 
def main():
    q_ip = 'localhost'
    q_port = 1800
    q_nodes_file = q_jobs_file = None

    parser = argparse.ArgumentParser(
        description="pktgen_scheduler schedules jobs for pktgen_servers")

    q = Q(q_ip, q_port, q_nodes_file, q_jobs_file)
    q.start()
    try:
        measure_delay(q, "127.0.0.1", 5000, "c3", open(sys.argv[1], "w"))
    finally:
        q.stop()


if __name__ == '__main__':
    main()
