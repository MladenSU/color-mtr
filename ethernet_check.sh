#!/bin/bash

console_device="/dev/tty1"
INTERFACE="eth0"
command_to_execute="sudo python3 /root/color-mtr/cmtr-rpi.py -n -i 2 -c 10 google.com -o LSAW -r"
initial_run=true

function write_to_tty {
    echo -e "\n" >>$console_device
    writevt "$console_device" "$1"
}

while true; do
    if ip link show "$INTERFACE" | grep -q "state UP"; then
        if [ "$initial_run" = true ]; then
            initial_run=false
            write_to_tty "Ethernet cable is connected."
            sleep 5
            script -q -c "$command_to_execute" -f "$console_device"
        fi
        while ip link show "$INTERFACE" | grep -q "state UP"; do
            sleep 5
        done
        write_to_tty "Ethernet cable is disconnected." && echo -e "\n" >>$console_device
        initial_run=true
    fi
done
