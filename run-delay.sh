#!/bin/bash
run_count=3
for ((iter=0; iter<10; iter++)); do
	echo Bess $iter
	python controller/pktgen-delay-bess-vm.py \
		../results/delay/bess-vm-$iter-${run_count}
	python controller/pktgen-delay-bess-isol-container.py \
				../results/delay/bess-isol-container-${iter}-${run_count}
	python controller/pktgen-delay-bess-container.py \
				../results/delay/bess-container-${iter}-${run_count}
	
	echo OVS $iter
	python controller/pktgen-delay-ovs-vm.py \
		../results/delay/ovs-vm-${iter}-${run_count}
	python controller/pktgen-delay-ovs-container.py \
			../results/delay/ovs-container-${iter}-${run_count}

	echo ZCSI $iter
	python controller/pktgen-delay-zcsi.py \ 
		../results/delay/zcsi-${iter}-${run_count}
done
