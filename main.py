import json
from typing import List, Union, Optional, Dict, Any
from tabulate import tabulate
from halo import Halo
from datetime import datetime
import sys
import subprocess

from termcolor import colored

# Constants
DEFAULT_LOSS_WARN = 0.1
DEFAULT_LOSS_CRIT = 5
DEFAULT_LATENCY_WARN = 10
DEFAULT_LATENCY_CRIT = 100

# Spinner animation
spinner = Halo(text="Generating a report.", spinner="dots")

# Colors
cw = lambda x: colored(x, "white")
cy = lambda x: colored(x, "yellow")
cb = lambda x: colored(x, "blue")
cr = lambda x: colored(x, "red")
cg = lambda x: colored(x, "green")

# That will be dynamic in config
loss_threshold = {"warn": 0.1, "crit": 5}
latency_threshold = {"warn": 10, "crit": 100}


# Color loss packets if any over given threshold
def _mark_loss(loss_packet: Union[int, float], limits: Dict[str, Union[int, float]]):
    loss_packet = float(loss_packet)
    if loss_packet >= limits.get("crit", DEFAULT_LOSS_WARN):
        return cr(loss_packet)
    elif loss_packet >= limits.get("warn", DEFAULT_LOSS_CRIT):
        return cy(loss_packet)
    else:
        return cg(loss_packet)


# Color latency packets if any over given threshold
def _mark_latency(latency: Union[int, float], limits: Dict[str, Union[int, float]]):
    latency = float(latency)
    if latency >= limits.get("crit", DEFAULT_LATENCY_CRIT):
        return cr(latency)
    elif latency >= limits.get("warn", DEFAULT_LATENCY_WARN):
        return cy(latency)
    else:
        return cg(latency)


def _report(data):
    loss_headers = ["Loss%"]
    latency_headers = ["Last", "Avg", "Best", "Wrst", "StDev"]
    all_entries: List[Dict] = data.get("report").get("hubs")
    for a in range(len(all_entries)):
        for k, v in all_entries[a].items():
            if k in loss_headers:
                all_entries[a][k] = _mark_loss(v, loss_threshold)
            if k in latency_headers:
                all_entries[a][k] = _mark_latency(v, latency_threshold)

    headers: List[str] = [cb(x) for x in all_entries[0].keys()]
    data: List[List] = [list(x.values()) for x in all_entries]
    print(tabulate(data, headers=headers, numalign="right"))


def _start_info(data, start_time, end_time):
    result = [f"{cb('Start: ')} {cy(start_time)}",
              f"{cb('Source: ')} {cy(data.get('src', 'Unknown'))}",
              f"{cb('Destination: ')} {cy(data.get('dst', 'Unknown'))}",
              f"{cb('Count: ')} {cy(data.get('tests', 'Unknown'))}",
              f"{cb('End: ')} {cg(end_time)}"]
    print(tabulate([[]], headers=result))


def _verify_mtr() -> Union[str, None]:
    try:
        output = subprocess.check_output(['which', 'mtr'])
        return output.decode('utf-8').strip("\n")
    except subprocess.CalledProcessError:
        print(cr("[ERROR] mtr executable not found! Please install it."))
        sys.exit(1)


def _exec_mtr(*args) -> Union[dict, None]:
    mtr_path = _verify_mtr()
    args = list(*args)
    args.insert(0, "sudo")
    args.insert(1, mtr_path)
    args.append("-j") if "-j" not in args else args
    run_it = subprocess.run(args=args, capture_output=True)
    if run_it.returncode != 0:
        print(str(run_it.stderr.decode()))
        sys.exit(1)
    try:
        return json.loads(run_it.stdout.decode())
    except json.decoder.JSONDecodeError:
        print(run_it.stdout.decode())
        sys.exit(0)


def main(user_input: List[Any]):
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    spinner.start()
    data = _exec_mtr(user_input)
    spinner.stop()
    end_time = datetime.now().strftime('%H:%M:%S')
    _start_info(data.get("report").get("mtr"), start_time, end_time)
    _report(data)


if __name__ == '__main__':
    main(sys.argv[1:])
