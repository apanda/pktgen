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

import job_pb2
import status_pb2

def connect_test_machine(machine='c3'):
    conn = paramiko.SSHClient()
    conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    conn.connect(hostname=machine) # This assumes we don't need a key to ssh.
    return conn

def exec_command_and_wait(conn, cmd):
    i, o, e = conn.exec_command(cmd)
    o = list(o)
    e = list(e)
    return (o, e)

def add_server(q, server, port):
    key = "%s_%d"%(server, port)
    q.add_node(Node(key, server, port))
    return key

def run_flow(q, key):
    q.results_event.clear()
    q.add_job(key, Job(1, {
        "tx_rate": 10000,
        "duration": 24 * 60 * 60 * 1000,
        "warmup": 5,
        "num_flows": 1,
        "size_min": 64, "size_max": 64,
        "life_min": 60*1000, "life_max": 24*60*60*1000,
        "port_min": 80, "port_max": 80,
        "latency": False,
        "src_mac": "68:05:ca:00:00:ab",
        "dst_mac": "68:05:ca:00:00:01",
        "online": True}))

def stop_and_measure(q, key):
    q.add_job(key, Job(0, {"print": True, "stop": True}))
    print "Beginning to wait" 
    q.results_event.wait(10) # If we have not heard back in 10 seconds, just
                             # restart
    print "Done waiting"
    measure = q.results
    return measure

def restart_pktgen(handle, port, nic):
    if handle:
        handle.kill()
        handle.wait()
    print "Booting"
    OUT_FILE = "/tmp/pktgen.out"
    f = open(OUT_FILE, 'w')
    handle = subprocess.Popen(["stdbuf", \
                               "-o0", \
                               "-e0", \
                               "bin/pktgen", \
                               "-c", "0x1f0", \
                               "-w", str(nic+".0"), \
                               "-w", str(nic+".1"), \
                               "-w", str(nic+".2"), \
                               "-w", str(nic+".3"), \
                               "--", str(port)], \
                               stdout=f, \
                               stderr=f)
    with open(OUT_FILE, 'r') as f2:
        while True:
            l = f2.readline()
            if l.startswith("Init core"):
                return handle

def output_data(handle):
    while True:
        try:
            l = read(handle.stdout.fileno(), 1024)
            print l
        except OSError:
            break
    while True:
        try:
            l = read(handle.stderr.fileno(), 1024)
            print l
        except OSError:
            break
def measure_delay(q, pgen_server, pgen_port, server, out):
    handle = None
    conn = connect_test_machine(server)
    key = add_server(q, pgen_server, pgen_port)
    measure_time = 20 # seconds
    start_bess = "/opt/e2d2/scripts/start-bess-container-isol.sh"
    start_container = \
    '/opt/e2d2/container/run-container.sh start fancy %d 8 6 "bess:rte_ring0 bess:rte_ring1 bess:rte_ring2 bess:rte_ring3"'
    stop_container = "/opt/e2d2/container/run-container.sh stop fancy"
    o, e = exec_command_and_wait(conn, stop_container)
    for delay in xrange(0, 5000, 50):
        try:
            success = False
            while not success:
                success = True
                handle = restart_pktgen(handle, pgen_port, "81:00")
                print "Starting BESS"
                o, e = exec_command_and_wait(conn, start_bess)
                print "Out ", '\n\t'.join(o)
                print "Err ", '\n\t'.join(e)
                print "Starting container"
                o,e = exec_command_and_wait(conn, start_container%(delay))
                print "Out ", '\n\t'.join(o)
                print "Err ", '\n\t'.join(e)
                run_flow(q, key)
                print "Measuring"
                time.sleep(measure_time)
                # output_data(handle)
                print "Stopping"
                m = stop_and_measure(q, key)
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
            raise
 
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
