#! /usr/bin/python3
"""Parse the UTI database from system and write it to a json file."""
import subprocess
import sys
import re
import json
import os.path
from datetime import datetime

LOCALE = "LSDefaultLocalizedValue"
DB_RELOAD_INTERVAL = 90 # days

def load_system_database():
    """Load UTI database form system and return string of it"""
    cmd = ["/System/Library/Frameworks/CoreServices.framework/Frameworks/" + \
           "LaunchServices.framework/Versions/A/Support/lsregister", "-dump"]
    return subprocess.check_output(cmd).decode("utf-8")

def parse_system_database(system_database_str):
    """Parse the UTI database from system.
    Returns a list of dictionaries"""
    section_pattern = r"^-+$\n" \
                    r"((?:^.+:\s+.+$\n)+)"
    line_pattern = r"^(.+):\s+(.+)$"
    sections = re.findall(section_pattern, system_database_str, re.MULTILINE)
    uti_json_list = []
    for section in sections:
        if "uti:" in section:
            kv_pairs = dict(re.findall(line_pattern, section, re.MULTILINE))
            kv_pairs = {k: [item.strip() for item in v.split(",")] \
                        if "," in v else v for k, v in kv_pairs.items()}
            for k, v in kv_pairs.items():
                if '" = "' in v or \
                    (next((item for item in v if '" = "' in item), False) and \
                     isinstance(v, list)):
                    kv_pairs[k] = {key.strip(' "'): value.strip(' "') \
                                for key, value in \
                                (item.split("=") for item in v if "=" in item)}
            uti_json_list.append(dict(kv_pairs))
    return uti_json_list

def write_database_to_json(uti_json):
    """Write the UTI database to a json file"""
    with open('uti_database.json', 'w', encoding="utf-8") as f:
        json.dump(uti_json, f, indent=4)

def load_database_from_json():
    """Load UTI database from json file"""
    with open('uti_database.json', 'r', encoding="utf-8") as f:
        return json.load(f)

def generate_script_filter_json(uti_json_list):
    """Generate a json file for Alfred Script Filter"""
    output = {
        "items": []
        }
    for item in uti_json_list:
        if "uti" in item.keys():
            if not next((itm for itm in output["items"] if itm["arg"] == item["uti"]), False):
                if item["uti"] == 'org.freecad.fcstd':
                    pass
                if "localizedDescription" in item.keys():
                    if LOCALE in item["localizedDescription"].keys():
                        description = item["localizedDescription"][LOCALE]
                    elif "LSDefaultLocalizedValue" in item["localizedDescription"].keys():
                        description = item["localizedDescription"]["LSDefaultLocalizedValue"]
                if "tags" in item.keys():
                    if description:
                        if isinstance(item["tags"], list):
                            title = f"{description} (tags: {', '.join(item['tags'])})"
                        else:
                            title = f"{description} (tag: {item['tags']})"
                    else:
                        if isinstance(item["tags"], list):
                            title = ', '.join(item["tags"])
                        else:
                            title = item["tags"]
                elif description:
                    title = description
                else:
                    title = item["uti"]
                entry = {"uid": item["uti"],
                         "title": title,
                         "subtitle": item["uti"],
                         "arg": item["uti"]}
                if "iconFiles" in item.keys():
                    entry["icon"] = {"type": "filetype",
                                     "path": item["uti"]}
                output["items"].append(entry)
    return output

def write_script_filter_to_json(sc_json):
    """Write the UTI database to a json file"""
    with open('uti_script_filter.json', 'w', encoding="utf-8") as f:
        json.dump(sc_json, f, indent=4)

def load_script_filter_from_json():
    """Load UTI database from json file"""
    with open('uti_script_filter.json', 'r', encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    try:
        reload_interval = int(os.getenv("reload_interval"))
    except Exception:
        reload_interval = int(DB_RELOAD_INTERVAL)
    if os.path.exists('uti_script_filter.json'):
        last_modified = datetime.fromtimestamp(os.path.getmtime('uti_script_filter.json'))
        if (datetime.now() - last_modified).days < reload_interval:
            query = load_script_filter_from_json()
    else:
        database_json = parse_system_database(load_system_database())
        query = generate_script_filter_json(database_json)
        write_script_filter_to_json(query)
    sys.stdout.write(json.dumps(query))
