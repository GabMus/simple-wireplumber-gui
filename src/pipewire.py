import os
import re
from dataclasses import dataclass
from typing import List, Dict

PATTERN_IDS = r"id (\d+), type ([\w:\/]+)"
PATTERN_DATA = r'(\w+\.\w+)\s*=\s*"([^"]+)"'


@dataclass
class Device:
    id: str
    hidden: bool
    name: str
    description: str
    nick: str


input_devices: List[Device] = []

output_devices: List[Device] = []


def parse_pw_cli_ls_data(data: str) -> Dict[str, Dict[str, str]]:
    parsed_data = {}

    last_match_character = -1
    last_match_id = None

    def append_last_id_data(current_start: int):
        if last_match_character < 0:
            return

        current_data = data[last_match_character:current_start]
        matches = re.findall(PATTERN_DATA, current_data)

        parsed_data[last_match_id].update(dict(matches))

    for match in re.finditer(PATTERN_IDS, data):
        id_, type_ = match.groups()
        parsed_data[id_] = {"type": type_}

        append_last_id_data(match.start())

        last_match_character = match.end()
        last_match_id = id_

    append_last_id_data(len(data))

    return parsed_data


def get_pipewire_objects_data():
    stream = os.popen("pw-cli list-objects")
    return parse_pw_cli_ls_data(stream.read())


def get_pipewire_devices_data():
    pipewire_objects = get_pipewire_objects_data()

    pipewire_devices = filter(
        lambda obj: obj.get("media.class") == "Audio/Device",
        pipewire_objects.values(),
    )

    return pipewire_devices


output_devices = list(
    map(
        lambda d: Device(
            id=d["object.serial"],
            name=d.get("device.name", ""),
            description=d.get("device.description",""),
            nick=d.get("device.nick", ""),
            hidden=False,
        ),
        get_pipewire_devices_data(),
    )
)

active_input_devices = filter(lambda d: not d.hidden, input_devices)
disabled_input_devices = filter(lambda d: d.hidden, input_devices)

active_output_devices = filter(lambda d: not d.hidden, output_devices)
disabled_output_devices = filter(lambda d: d.hidden, output_devices)
