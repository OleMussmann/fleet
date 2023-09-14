#!/usr/bin/env python3

import threading
import os
import time

import commands
import colors

from typing import TypedDict

try:
    MACHINE_LIST: list[str] = os.environ['FLEET_MACHINES'].split(" ")
    URL: str = os.environ['FLEET_REPO_URL']
    MAX_MACHINE_LENGTH: int = max([len(machine) for machine in MACHINE_LIST + ["machine"]])
    PAT_TOKEN: str | None
    try:
        # optional personal access token for your repository
        PAT_TOKEN = os.environ['FLEET_PAT_TOKEN']
    except KeyError:
        PAT_TOKEN = None
except KeyError as e:
    raise KeyError(f"Please set the environment variable {e}, see fleet --help")

MASK_STEP = 1
DIRECTION = "left"

OK_COLOR = "green"
WARNING_COLOR = "yellow"
ERROR_COLOR = "red"
SCRAMBLE_COLOR = "cyan"
STANDARD_COLOR = "standard"

COLOR_MACHINES = False
COLOR_VERSIONS = False
COLOR_BUILT = False

DELAY = 0.05

SPECS: dict[str, str] = {
    "is_online": "unset",
    "automation_status": "unset",
    "nixos_version": "unset",
    "nixos_version_match": "unset",
    "generation": "unset",
    "last_build": "unset",
    }

class TextSpecs(TypedDict):
    machine_mask: list[int]
    is_online_mask: list[int]
    automation_status_mask: list[int]
    nixos_version_mask: list[int]
    nixos_version_match_mask: list[int]
    generation_mask: list[int]
    last_build_mask: list[int]
    last_build_warning_mask: list[int]
TEXT_SPECS: TextSpecs = {
    "machine_mask": [0] * MAX_MACHINE_LENGTH,
    "is_online_mask": [0],
    "automation_status_mask": [0],
    "nixos_version_mask": [0] * 8,
    "nixos_version_match_mask": [0],
    "generation_mask": [0] * 5,
    "last_build_mask": [0] * 8,
    "last_build_warning_mask": [0],
    }

class VersionTextSpecs(TypedDict):
    version_mask: list[int]

VERSION_TEXT_SPECS: VersionTextSpecs = {
    "version_mask": [0, 0, 0, 0, 0, 0, 0, 0],
    }

MACHINE_SPECS: dict[str, dict[str, str]] = {}
for machine in MACHINE_LIST:
    MACHINE_SPECS[machine] = SPECS.copy()

MACHINE_TEXT_SPECS: dict[str, TextSpecs] = {}
for machine in MACHINE_LIST:
    MACHINE_TEXT_SPECS[machine] = TEXT_SPECS.copy()

REMOTE_VERSION = "unset"

DONE = False

def get_remote_version(url, pat):
    global REMOTE_VERSION
    try:
        REMOTE_VERSION = commands.remote_nixos_version(url, pat)
    except Exception as e:
        REMOTE_VERSION = "unknown"

def run_task(query, machine):
    global MACHINE_SPECS
    try:
        MACHINE_SPECS[machine][query.__name__] = query(machine)
    except:
        MACHINE_SPECS[machine][query.__name__] = "unknown"

def get_machine_specs(machine):
    global MACHINE_SPECS
    is_online = commands.is_online(machine)
    if not is_online:
        MACHINE_SPECS[machine]["is_online"] = "false"
        MACHINE_SPECS[machine]["automation_status"] = "none"
        MACHINE_SPECS[machine]["nixos_version"] = "none"
        MACHINE_SPECS[machine]["nixos_version_match"] = "none"
        MACHINE_SPECS[machine]["generation"] = "none"
        MACHINE_SPECS[machine]["last_build"] = "none"
        return

    MACHINE_SPECS[machine]["is_online"] = "true"
    queries = [
        commands.automation_status,
        commands.nixos_version,
        commands.generation,
        commands.last_build,
    ]
    tasks = []
    for query in queries:
        tasks.append(threading.Thread(target=run_task, args=(query, machine,), daemon=True))
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()

def get_remote_version_text():
    global REMOTE_VERSION
    global VERSION_TEXT_SPECS

    if REMOTE_VERSION == "unset":
        text: str = colors.get_string("++++++++", VERSION_TEXT_SPECS["version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
    elif REMOTE_VERSION == "unknown":
        text: str = colors.get_string("       ?", VERSION_TEXT_SPECS["version_mask"], text_color=ERROR_COLOR, scramble_color=SCRAMBLE_COLOR)
        VERSION_TEXT_SPECS["version_mask"] = colors.bump_mask(VERSION_TEXT_SPECS["version_mask"], MASK_STEP, DIRECTION)
    else:
        text: str = colors.get_string(REMOTE_VERSION, VERSION_TEXT_SPECS["version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        VERSION_TEXT_SPECS["version_mask"] = colors.bump_mask(VERSION_TEXT_SPECS["version_mask"], MASK_STEP, DIRECTION)
    return text

def get_machine_text(machine):
    global MACHINE_SPECS
    global MACHINE_TEXT_SPECS

    machine_color: str
    if MACHINE_SPECS[machine]["is_online"] == "true":
        is_online_text: str = colors.get_string("•", MACHINE_TEXT_SPECS[machine]["is_online_mask"], text_color=OK_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["is_online_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["is_online_mask"], MASK_STEP, DIRECTION)
        machine_color = OK_COLOR
    elif MACHINE_SPECS[machine]["is_online"] == "false":
        is_online_text: str = colors.get_string("-", MACHINE_TEXT_SPECS[machine]["is_online_mask"], text_color=ERROR_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["is_online_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["is_online_mask"], MASK_STEP, DIRECTION)
        machine_color = ERROR_COLOR
    else:
        is_online_text: str = colors.get_string("+", MACHINE_TEXT_SPECS[machine]["is_online_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        machine_color = STANDARD_COLOR

    if not COLOR_MACHINES:
        machine_color = STANDARD_COLOR

    machine_text: str = colors.get_string(machine.rjust(MAX_MACHINE_LENGTH), MACHINE_TEXT_SPECS[machine]["machine_mask"], text_color=machine_color, scramble_color=SCRAMBLE_COLOR)
    MACHINE_TEXT_SPECS[machine]["machine_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["machine_mask"], MASK_STEP, DIRECTION)
    return machine_text + " " + is_online_text

def get_automation_text(machine):
    global MACHINE_SPECS
    global MACHINE_TEXT_SPECS

    if MACHINE_SPECS[machine]["automation_status"] == "unset":
        text: str = colors.get_string("+", MACHINE_TEXT_SPECS[machine]["automation_status_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        return text
    if MACHINE_SPECS[machine]["automation_status"] == "automated":
        text: str = colors.get_string("•", MACHINE_TEXT_SPECS[machine]["automation_status_mask"], text_color=OK_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["automation_status_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["automation_status_mask"], MASK_STEP, DIRECTION)
        return text
    if MACHINE_SPECS[machine]["automation_status"] == "build failed":
        text: str = colors.get_string("!", MACHINE_TEXT_SPECS[machine]["automation_status_mask"], text_color=WARNING_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["automation_status_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["automation_status_mask"], MASK_STEP, DIRECTION)
        return text
    if MACHINE_SPECS[machine]["automation_status"] == "unknown":
        text: str = colors.get_string("?", MACHINE_TEXT_SPECS[machine]["automation_status_mask"], text_color=WARNING_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["automation_status_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["automation_status_mask"], MASK_STEP, DIRECTION)
        return text
    else:  # "none"
        text: str = colors.get_string(" ", MACHINE_TEXT_SPECS[machine]["automation_status_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["automation_status_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["automation_status_mask"], MASK_STEP, DIRECTION)
        return text

def get_version_text(machine):
    global MACHINE_SPECS
    global REMOTE_VERSION

    version_color: str


    if MACHINE_SPECS[machine]["nixos_version"] == "unset":
        version_text: str = colors.get_string("++++++++", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        version_match_text: str = colors.get_string("+", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        return version_text + " " + version_match_text

    elif MACHINE_SPECS[machine]["nixos_version"] == "none":
        version_text: str = colors.get_string("        ", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        version_match_text: str = colors.get_string(" ", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
        MACHINE_TEXT_SPECS[machine]["nixos_version_match_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
        return version_text + " " + version_match_text

    elif MACHINE_SPECS[machine]["nixos_version"] == "unknown":
        version_text: str = colors.get_string("        ", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        version_match_text: str = colors.get_string("?", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=ERROR_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
        MACHINE_TEXT_SPECS[machine]["nixos_version_match_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
        return version_text + " " + version_match_text

    else:  # has actual nixos_version

        if REMOTE_VERSION == "unset" or REMOTE_VERSION == "unknown":
            version_match_text: str = colors.get_string("?", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=WARNING_COLOR, scramble_color=SCRAMBLE_COLOR)
            MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
            version_color = WARNING_COLOR
        elif MACHINE_SPECS[machine]["nixos_version"] == REMOTE_VERSION:
            version_match_text: str = colors.get_string("•", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=OK_COLOR, scramble_color=SCRAMBLE_COLOR)
            MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
            version_color = OK_COLOR
        else:  # MACHINE_SPECS[machine]["nixos_version"] != REMOTE_VERSION:
            version_match_text: str = colors.get_string("!", MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=WARNING_COLOR, scramble_color=SCRAMBLE_COLOR)
            MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)
            version_color = WARNING_COLOR

        if not COLOR_VERSIONS:
            version_color = STANDARD_COLOR
        version_text: str = colors.get_string(MACHINE_SPECS[machine]["nixos_version"], MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], text_color=version_color, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["nixos_version_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["nixos_version_mask"], MASK_STEP, DIRECTION)

    return version_text + " " + version_match_text


def get_generation_text(machine):
    global MACHINE_SPECS

    if MACHINE_SPECS[machine]["generation"] == "unset":
        text: str = colors.get_string("++++", MACHINE_TEXT_SPECS[machine]["generation_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
    elif MACHINE_SPECS[machine]["generation"] == "none":
        text: str = colors.get_string("    ", MACHINE_TEXT_SPECS[machine]["generation_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["generation_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["generation_mask"], MASK_STEP, DIRECTION)
    elif MACHINE_SPECS[machine]["generation"] == "unknown":
        text: str = colors.get_string("   ?", MACHINE_TEXT_SPECS[machine]["generation_mask"], text_color=ERROR_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["generation_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["generation_mask"], MASK_STEP, DIRECTION)
    else:
        text: str = colors.get_string(MACHINE_SPECS[machine]["generation"].rjust(4), MACHINE_TEXT_SPECS[machine]["generation_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["generation_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["generation_mask"], MASK_STEP, DIRECTION)
    return text


def get_build_time_text(machine):
    global MACHINE_SPECS

    built_color: str

    if MACHINE_SPECS[machine]["last_build"] == "unset":
        build_text: str = colors.get_string("++++++++", MACHINE_TEXT_SPECS[machine]["last_build_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        build_warning_text: str = colors.get_string("+", MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
    elif MACHINE_SPECS[machine]["last_build"] == "none":
        build_text: str = colors.get_string("        ", MACHINE_TEXT_SPECS[machine]["last_build_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        build_warning_text: str = colors.get_string(" ", MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["last_build_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_mask"], MASK_STEP, DIRECTION)
        MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], MASK_STEP, DIRECTION)
    elif MACHINE_SPECS[machine]["last_build"] == "unknown":
        build_text: str = colors.get_string("        ", MACHINE_TEXT_SPECS[machine]["last_build_mask"], text_color=STANDARD_COLOR, scramble_color=SCRAMBLE_COLOR)
        build_warning_text: str = colors.get_string("?", MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], text_color=ERROR_COLOR, scramble_color=SCRAMBLE_COLOR)
        MACHINE_TEXT_SPECS[machine]["last_build_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_mask"], MASK_STEP, DIRECTION)
        MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], MASK_STEP, DIRECTION)
    else:
        try:
            days_since_last_build = int(MACHINE_SPECS[machine]["last_build"].split("d")[0])
            if days_since_last_build > 2:
                build_warning = True
            else:
                build_warning = False
        except ValueError:  # less than day
            build_warning = False

        if build_warning:
            build_warning_text: str = colors.get_string("!", MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], text_color=WARNING_COLOR, scramble_color=SCRAMBLE_COLOR)
            built_color = WARNING_COLOR
        else:
            build_warning_text: str = colors.get_string("•", MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], text_color=OK_COLOR, scramble_color=SCRAMBLE_COLOR)
            built_color = OK_COLOR

        if not COLOR_BUILT:
            built_color = STANDARD_COLOR

        MACHINE_TEXT_SPECS[machine]["last_build_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_mask"], MASK_STEP, DIRECTION)
        MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"] = colors.bump_mask(MACHINE_TEXT_SPECS[machine]["last_build_warning_mask"], MASK_STEP, DIRECTION)
        build_text: str = colors.get_string(MACHINE_SPECS[machine]["last_build"].rjust(8), MACHINE_TEXT_SPECS[machine]["last_build_mask"], text_color=built_color, scramble_color=SCRAMBLE_COLOR)

    return build_text + " " + build_warning_text

def assemble_text():
    global MACHINE_SPECS
    global MACHINE_TEXT_SPECS

    dashboard_string: str = ""
    dashboard_string += "╭" + "─" * (4 + MAX_MACHINE_LENGTH) + "┬───┬────────────┬───────┬────────────╮\n"
    dashboard_string += "│ " + "machine".rjust(2 + MAX_MACHINE_LENGTH) + " │aut│ v " + get_remote_version_text() + " │  gen. │      built │\n"
    dashboard_string += "├" + "─" * (4 + MAX_MACHINE_LENGTH) + "┼───┼────────────┼───────┼────────────┤\n"

    if commands.this_machine in MACHINE_LIST:
        this_machine = commands.this_machine
        dashboard_string += "│ " + get_machine_text(this_machine) +  " │ " + get_automation_text(this_machine) + " │ " + get_version_text(this_machine) + " │  " + get_generation_text(this_machine) + " │ " + get_build_time_text(this_machine) +" │\n"
        dashboard_string += "├" + "─" * (4 + MAX_MACHINE_LENGTH) + "┼───┼────────────┼───────┼────────────┤\n"

    for machine in MACHINE_LIST:
        if machine != commands.this_machine:
            dashboard_string += "│ " + get_machine_text(machine) + " │ " + get_automation_text(machine) + " │ " + get_version_text(machine) + " │  " + get_generation_text(machine) + " │ " + get_build_time_text(machine) +" │\n"

    dashboard_string += "╰" + "─" * (4 + MAX_MACHINE_LENGTH) + "┴───┴────────────┴───────┴────────────╯"

    return dashboard_string

def print_text():
    global DONE

    number_of_previous_lines = 0
    while not DONE:
        text = assemble_text()
        print(f"\033[{number_of_previous_lines + 2}A")  # reset screen
        number_of_previous_lines = text.count('\n')
        print(text)
        time.sleep(DELAY)

main_loop = threading.Thread(target=print_text, args=(), daemon=True)
tasks = []
for machine in MACHINE_LIST:
    tasks.append(threading.Thread(target=get_machine_specs, args=(machine,), daemon=True))
tasks.append(threading.Thread(target=get_remote_version, args=(URL, PAT_TOKEN), daemon=True))

main_loop.start()
for task in tasks:
    task.start()

try:
    for task in tasks:
        task.join()

    time.sleep(DELAY*(8+5))
    DONE = True
    main_loop.join()
except KeyboardInterrupt:
    exit(1)
