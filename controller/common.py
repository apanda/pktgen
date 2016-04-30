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

WARMUP_TIME = 2
DURATION = 15
MIN_SIZE = 64
def run_flow_dynamic(q, key, size=MIN_SIZE, \
        duration = DURATION, warmup = WARMUP_TIME):
    q.results_event.clear()
    q.add_job(key, Request(0, [Job({
        "tx_rate": -1,
        "duration": duration * 1000,
        "warmup": warmup * 1000,
        "num_flows": 100,
        "size_min": size, "size_max": size,
        "life_min": 1000, "life_max": 5000,
        "port_min": 20, "port_max": 65535,
        "latency": False,
        "src_mac": "68:05:ca:00:00:ab",
        "dst_mac": "68:05:ca:00:00:01",
        "online": True})]))
    sleep(warmup + duration + 0.15)

def measure(q, key):
    sleep(0.2)
    measure = q.results

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

