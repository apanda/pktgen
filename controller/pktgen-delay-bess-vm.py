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
    measure_time = 15 + WARMUP_TIME# seconds
    start_container = "/opt/e2d2/scripts/start-bess-vm.sh start %d | tee /tmp/start"
    stop_container = "/opt/e2d2/scripts/start-bess-vm.sh stop"
    stop_container_hard = "/opt/e2d2/scripts/start-bess-vm.sh hardkill"
    print "Killing container"
    o, e = exec_command_and_wait(conn, stop_container)
    print "Killed container"
    print "Killing all"
    kill_all = "/opt/e2d2/scripts/kill-all.sh"
    o, e = exec_command_and_wait(conn, kill_all)
    print "Killed all"
    for delay in xrange(0, 2000, 50):
        try:
            success = False
            while not success:
                print "Starting pgen"
                success = True
                handle = restart_pktgen(handle, pgen_port, "81:00", 2)
                print "Starting VM"
                o,e = exec_command_noblock(conn, start_container%(delay))
                while True:
                    l = o.readline()
                    print l
                    if l.strip() == "Successfully started":
                        break
                    if l.strip() == "Fail Fail Fail":
                        print "Detected failure"
                        success = False
                        break
                if not success:
                    print "Stopping"
                    o,e = exec_command_noblock(conn, stop_container)
                    o,e = exec_command_noblock(conn, stop_container_hard)
                    print "Restarting"
                    continue
                print "VM started"
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
