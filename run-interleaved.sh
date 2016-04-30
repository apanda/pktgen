#!/bin/bash
set -o errexit
run_count=3
for ((iter=0; iter<10; iter++)); do
if (($iter > 0)); then
	echo BESS $iter
	python controller/pktgen-bess-ctr-size.py \
		../results/size/bess-container-${iter}-${run_count}
	python controller/pktgen-bess-isol-ctr-size.py \
		../results/size/bess-isol-container-${iter}-${run_count}
	python controller/pktgen-bess-vm-size.py \
		../results/size/bess-vm-${iter}-${run_count}
	python controller/pktgen-delay-bess-vm.py \
		../results/delay/bess-vm-$iter-${run_count}
	python controller/pktgen-delay-bess-isol-container.py \
				../results/delay/bess-isol-container-${iter}-${run_count}
	python controller/pktgen-delay-bess-container.py \
				../results/delay/bess-container-${iter}-${run_count}
	echo OVS $iter
	python controller/pktgen-ovs-ctr-size.py \
		../results/size/ovs-container-${iter}-${run_count}
	python controller/pktgen-ovs-vm-size.py \
		../results/size/ovs-vm-${iter}-${run_count}
	python controller/pktgen-delay-ovs-vm.py \
		../results/delay/ovs-vm-${iter}-${run_count}
	python controller/pktgen-delay-ovs-container.py \
			../results/delay/ovs-container-${iter}-${run_count}

	echo ZCSI $iter
	python controller/pktgen-zcsi-size.py \
		../results/size/zcsi-${iter}-${run_count}
fi
	echo ZCSI $iter
	python controller/pktgen-delay-zcsi.py \
		../results/delay/zcsi-${iter}-${run_count}
done
