#!/bin/bash
set -o errexit
run_count=3
for ((iter=0; iter<10; iter++)); do
	echo BESS $iter
	python controller/pktgen-bess-ctr-size.py \
		../results/size/bess-container-${iter}-${run_count}
	python controller/pktgen-bess-isol-ctr-size.py \
		../results/size/bess-isol-container-${iter}-${run_count}
	python controller/pktgen-bess-vm-size.py \
		../results/size/bess-vm-${iter}-${run_count}
	echo OVS $iter
	python controller/pktgen-ovs-ctr-size.py \
		../results/size/ovs-container-${iter}-${run_count}
	python controller/pktgen-ovs-vm-size.py \
		../results/size/ovs-vm-${iter}-${run_count}
	echo ZCSI $iter
	python controller/pktgen-zcsi-size.py \
		../results/size/zcsi-${iter}-${run_count}
done
