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

WARMUP_TIME=5
def run_flow(q, key, size):
    q.add_job(key, Job(1, {
        "tx_rate": 10000,
        "duration": 24 * 60 * 60 * 1000,
        "warmup": WARMUP_TIME,
        "num_flows": 1,
        "size_min": size, "size_max": size,
        "life_min": 60*1000, "life_max": 24*60*60*1000,
        "port_min": 80, "port_max": 80,
        "latency": False,
        "src_mac": "68:05:ca:00:00:ab",
        "dst_mac": "68:05:ca:00:00:01",
        "online": True}))

def stop_and_measure(q, key):
    q.results_event.clear()
    q.add_job(key, Job(0, {"stop": True, "print": True}))
    q.results_event.wait()
    measure = q.results
    return measure

def restart_pktgen(handle, port, nic, count):
    if handle:
        handle.kill()
        handle.wait()
    print "Booting"
    OUT_FILE = "/tmp/pktgen.out"
    f = open(OUT_FILE, 'w')
    args = ["stdbuf", \
            "-o0", \
            "-e0", \
            "bin/pktgen", \
            "-c", "0xff00"]
    for n in xrange(count):
        args.append("-w")
        args.append("%s.%d"%(nic, n))
    args.append("--")
    args.append(str(port))
    handle = subprocess.Popen(args, \
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
    start_ovs = "/opt/e2d2/scripts/start-ovs-container-size.sh 8 30 %d"
    start_container = \
    '/opt/e2d2/container/run-container.sh start fancy %d 8 6'
            # 
    stop_container = "/opt/e2d2/container/run-container.sh stop fancy"
    o, e = exec_command_and_wait(conn, stop_container)
    kill_all = "/opt/e2d2/scripts/kill-all.sh"
    o, e = exec_command_and_wait(conn, kill_all)
    kill_all = "/opt/e2d2/scripts/kill-all.sh"
    o, e = exec_command_and_wait(conn, kill_all)
    sizes = [60, 128, 256, 512, 768, 1024, 1200, 1500]
    n_restarts = 0
    try:
        for n_port in xrange(1, 5):
            for size in sizes:
                try:
                    success = False
                    while not success:
                        success = True
                        handle = restart_pktgen(handle, pgen_port, "81:00", \
                                n_port)
                        print "Starting OVS"
                        o, e = exec_command_and_wait(conn, start_ovs%(n_port))
                        print "Out ", '\n\t'.join(o)
                        print "Err ", '\n\t'.join(e)
                        print "Starting container"
                        run_container = start_container%(0) + ' "' + \
                            ' '.join(map(lambda c: 'ovs:%d'%c, \
                                    range(n_port))) + '"'
                        o,e = exec_command_and_wait(conn, run_container)
                        print "Out ", '\n\t'.join(o)
                        print "Err ", '\n\t'.join(e)
                        run_flow(q, key, size)
                        print "Measuring"
                        lines = 0
                        time.sleep(measure_time + WARMUP_TIME)
                        # output_data(handle)
                        print "Stopping"
                        m = stop_and_measure(q, key)
                        print "Stopped measurement"
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
                        if tx_mpps_mean < 0.5:
                            n_restarts += 1
                            if n_restarts < 2:
                                success = False
                                print "Restarting", tx_mpps_mean
                                continue
                            else:
                                print "WARN WARN WARN Should restart but not going to"
                        print size, n_port, rx_mpps_mean, tx_mpps_mean
                        print >>out, size, n_port, rx_mpps_mean, tx_mpps_mean
                        n_restarts = 0
                        out.flush()
                except:
                    print "Caught exception"
                    o, e = exec_command_and_wait(conn, stop_container)
                    print "Out ", '\n\t'.join(o)
                    print "Err ", '\n\t'.join(e)
                    raise
    finally:
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
    # code.interact(local=dict(globals(), **locals()))
    # q.stop()
    try:
        measure_delay(q, "127.0.0.1", 5000, "c3", open(sys.argv[1], "w"))
    finally:
        q.stop()


if __name__ == '__main__':
    main()
