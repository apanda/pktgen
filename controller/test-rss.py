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

def run_flow(q, key, size):
    q.add_job(key, Job(1, {
        "tx_rate": 10000,
        "duration": 24 * 60 * 60 * 1000,
        "warmup": 2,
        "num_flows": 1000,
        "size_min": size, "size_max": size,
        "life_min": 60*1000, "life_max": 24*60*60*1000,
        "port_min": 80, "port_max": 80,
        "latency": False,
        "src_mac": "68:05:ca:00:00:ab",
        "dst_mac": "68:05:ca:00:00:01",
        "online": True}))

def stop_and_measure(q, key):
    q.add_job(key, Job(0, {"print": True, "stop": True}))
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

 
def main():
    q_ip = 'localhost'
    q_port = 1800
    q_nodes_file = q_jobs_file = None

    parser = argparse.ArgumentParser(
        description="pktgen_scheduler schedules jobs for pktgen_servers")

    q = Q(q_ip, q_port, q_nodes_file, q_jobs_file)
    q.start()
    try:
        code.interact(local=dict(globals(), **locals()))
    finally:
        q.stop()


if __name__ == '__main__':
    main()
