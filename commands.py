#!/usr/bin/env python3

import json
import subprocess

from datetime import datetime, timedelta

machines = [
    "mario",
    "cosmo",
    "dale",
    "may",
    "pintsize",
    ]

this_machine = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()

def run_on(machine, command):
    if machine == this_machine:
        commands = command
    else:
        commands = ["ssh", machine, *command]

    return subprocess.run(commands, capture_output=True, text=True)


def is_online(machine):
    command = ["ping", "-c", "1", "-W", "2", machine]
    ping_output = run_on(this_machine, command)
    if ping_output.returncode == 0:
        return True
    else:
        return False


def automation_status(machine):
    command = ["systemctl", "status", "nixos-upgrade.service"]
    output = run_on(machine, command)

    if output.stderr or not "Loaded: loaded" in output.stdout:
        return "not automated"

    if "Active: inactive" in output.stdout:
        return "automated"
    elif "Active: failed" in output.stdout:
        return "build failed"
    else:
        return "unknown"


def nixos_version(machine):
    command = ["nixos-version", "--json"]
    version_json = run_on(machine, command).stdout.strip()
    version_dict = json.loads(version_json)
    return version_dict["configurationRevision"][:8]

def remote_nixos_version(url, pat=None):
    if pat:
        command = ["curl", "-s", "--header", f"PRIVATE-TOKEN: {pat}", url]
    else:
        command = ["curl", "-s", url]
    repo_info = run_on(this_machine, command).stdout.strip()
    repo_info_json = json.loads(repo_info)
    return repo_info_json[0]["short_id"]


def generation(machine):
    command = ["ls", "-l", "/nix/var/nix/profiles/system"]
    system_folder = run_on(machine, command).stdout.strip()
    system_string = system_folder.split()[-1]
    if "No such file or directory" in system_string:
        return "unknown"
    generation_number = "".join(list(filter(str.isdigit, system_string)))
    return generation_number


def last_build(machine):
    command = ["ls", "-l", "--time-style=long-iso", "/nix/var/nix/profiles/system"]
    system_folder = run_on(machine, command).stdout.strip()
    build_date_string = " ".join(system_folder.split()[-5:-3])
    build_date = datetime.strptime(build_date_string, "%Y-%m-%d %H:%M")
    difference = datetime.today() - build_date
    difference_days = str(difference.days)
    difference_hours = str(difference.seconds//3600)
    if difference_days == "0":
        return difference_hours + "h"
    else:
        return difference_days + "d " + difference_hours + "h"
