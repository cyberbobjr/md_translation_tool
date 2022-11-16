import glob
import json
import os
import re
import signal
import sys

import deepl
from tqdm import tqdm
import yaml
from deepl import Translator
from InquirerPy import inquirer, prompt
from colorama import Fore, Style

conf = {}
translator: Translator = {}
alreadytranslated = {}


def init_config():
    global conf
    yaml.add_representer(str, quoted_presenter)
    conf = json.load(open("conf.json"))


def init_dic():
    global alreadytranslated
    try:
        alreadytranslated = json.load(open(conf['dict_filename'], "r+"))
    except:
        return


def init_deepl():
    global translator
    if "source_path" not in conf or conf["source_path"] == "":
        print(f"Source path not found")
        exit(1)
    if "deepl" not in conf or "key" not in conf["deepl"]:
        print(f"Deepl config not found")
        exit(1)
    if conf["deepl"]["key"] is None or conf["deepl"]["key"] == "":
        print(f"Deepl key not found")
        exit(1)
    if conf["deepl"]["lang"] is None or conf["deepl"]["lang"] == "":
        print(f"Deepl lang not found")
        exit(1)
    translator = deepl.Translator(conf["deepl"]["key"])


def read_source():
    return glob.glob(conf['source_path'] + "/**.yml")


def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


def translate(file: str):
    print(f"Translation start for file {file}")
    content = yaml.full_load(open(file))
    fp = open(file, 'r')
    pbar = tqdm(total=len(fp.readlines()))
    parse_content(content, pbar)
    return content


def encode_line_to_translate(line: str):
    regex = r"([§][a-zA-Z0..9]).*?([§])"
    line_to_translate = line
    found = re.finditer(regex, line, re.MULTILINE)
    for matchNum, match in enumerate(found, start=1):
        groups = match.groups()
        start_group_char = groups[0]
        color = start_group_char[1]
        end_group_char = groups[1]
        find = match.group()
        replace_by = find.replace(start_group_char, f"<COLOR={color}>").replace(end_group_char, "</COLOR>")
        line_to_translate = line_to_translate.replace(find, replace_by)
    return line_to_translate


def decode_line_from_translate(line: str):
    regex = r"\<COLOR\=(.*?)\>.*?\<\/COLOR\>"
    line_to_translate = line
    found = re.finditer(regex, line, re.MULTILINE)
    for matchNum, match in enumerate(found, start=1):
        groups = match.groups()
        color = groups[0]
        find = match.group()
        replace_by = find.replace(f"<COLOR={color}>", f"§{color}").replace("</COLOR>", "§")
        line_to_translate = line_to_translate.replace(find, replace_by)
    return line_to_translate


def translate_string(text: str):
    global translator
    return translator.translate_text(text, target_lang=conf['deepl']['lang'], source_lang='EN')


def is_already_translated(key: str):
    return key in alreadytranslated.keys()


def get_already_translated(key: str):
    return alreadytranslated[key]


def save_translation_in_dict(key: str, translated: str):
    alreadytranslated[key] = translated
    json.dump(alreadytranslated, open(conf['dict_filename'], "w+"), ensure_ascii=False)


def save_output_translation(content, file):
    dst_filename = compute_dst_filename(file)
    yaml.dump(content, open(dst_filename, "w+"), default_flow_style=False, sort_keys=False, width=10000,
              allow_unicode=True)


def compute_dst_filename(file):
    return f"{conf['dest_path']}/{os.path.basename(file)}"


def parse_content(content: dict, pbar):
    for key in content:
        value = content[key]
        if type(value) is dict:
            parse_content(value, pbar)
        else:
            pbar.update(1)
            if is_already_translated(content[key]):
                content[key] = alreadytranslated[content[key]]
            else:
                to_translate = encode_line_to_translate(content[key])
                if to_translate != '':
                    translated = translate_string(to_translate)
                    from_translate = decode_line_from_translate(translated.text)
                    save_translation_in_dict(to_translate, from_translate)
                    content[key] = from_translate


def check_translation(file: str):
    dst_filename = compute_dst_filename(file)
    source_yaml = yaml.full_load(open(file))
    dest_yaml = yaml.full_load(open(dst_filename))
    check_translation_line(source_yaml, dest_yaml, file, None)


def check_translation_line(source_yaml: dict, dest_yaml: dict, src_filename, parent: str = None):
    for key in source_yaml:
        value = source_yaml[key]
        if type(value) is dict:
            check_translation_line(value, dest_yaml, src_filename, key)
        else:
            print(f"{Fore.RED}{Style.BRIGHT}Original :{Style.RESET_ALL} " + source_yaml[key])
            if key is None:
                translated_line = dest_yaml[key]
            else:
                translated_line = dest_yaml[parent][key]
            print(f"{Fore.GREEN}{Style.BRIGHT}Translation :{Style.RESET_ALL} {translated_line}")
            confirm = inquirer.confirm(message="Validate ?", default=True).execute()
            if not confirm:
                new_translation = ask_edit_translation(translated_line)
                if new_translation is not None:
                    if key is None:
                        dest_yaml[key] = new_translation
                    else:
                        dest_yaml[parent][key] = new_translation
                    save_output_translation(dest_yaml, src_filename)
    exit(1)


def ask_edit_translation(value):
    questions = [
        {
            'type': 'input',
            'name': 'translation',
            'message': 'Edit the translation',
            'default': value,
            "multiline": True,
            "mandatory": False
        }
    ]

    answers = prompt(questions, raise_keyboard_interrupt=False)
    return answers['translation']


def is_dst_file_exist(file: str):
    dst_filename = compute_dst_filename(file)
    return os.path.exists(dst_filename)


def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    init_config()
    init_deepl()
    init_dic()
    must_check = len(sys.argv) > 1 and sys.argv[1] == "--check"
    for file in read_source():
        if not is_dst_file_exist(file):
            content = translate(file)
            save_output_translation(content, file)
            print(f"Translation finished for file {file}")
        if must_check:
            check_translation(file)
print(f"All translations finished")
