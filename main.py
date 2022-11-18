import argparse
import glob
import json
import os
import re
import signal

import deepl
from progress.bar import Bar
import yaml
from deepl import Translator
from InquirerPy import inquirer, prompt
from colorama import Fore, Style

conf = {}
translator: Translator = {}
alreadytranslated = {}
yaml_keys = []

parser = argparse.ArgumentParser(
    prog='MD translation tool',
    description='This software help translator for Millenium Dawn mod')

parser.add_argument('-c', '--check', default=False, action='store_true',
                    help='launch Validate translation after processing')
parser.add_argument('-s', '--skip-line', default=0, type=int, help='Set the start line for validation')
args = parser.parse_args()


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
    if data in yaml_keys:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='')
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


def translate(file: str):
    print(f"Translation start for file {file}")
    content = yaml.full_load(open(file))
    pbar = Bar(max=get_total_lines(file))
    parse_content(content, pbar)
    return content


def get_total_lines(file):
    fp = open(file, 'r')
    return len(fp.readlines())


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
    return translator.translate_text(text, target_lang=conf['deepl']['lang'], source_lang='EN',
                                     formality=conf['deep']['formality'])


def is_already_translated(key: str):
    return key in alreadytranslated.keys()


def get_already_translated(key: str):
    return alreadytranslated[key]


def save_translation_in_dict(key: str, translated: str):
    alreadytranslated[key] = translated
    json.dump(alreadytranslated, open(conf['dict_filename'], "w+"), ensure_ascii=False)


def save_output_translation(content, file):
    dst_filename = compute_dst_filename(file)
    yaml.dump(content,
              open(dst_filename, "w+"),
              default_flow_style=False,
              indent=2,
              sort_keys=False,
              width=10000,
              allow_unicode=True)


def compute_dst_filename(file):
    return f"{conf['dest_path']}/{os.path.basename(file)}"


def parse_content(content: dict, pbar: Bar):
    for key in content:
        value = content[key]
        yaml_keys.append(key)
        if type(value) is dict:
            parse_content(value, pbar)
        else:
            pbar.next()
            if is_already_translated(content[key]):
                content[key] = alreadytranslated[content[key]]
            else:
                to_translate = encode_line_to_translate(content[key])
                if to_translate != '':
                    translated = translate_string(to_translate)
                    from_translate = decode_line_from_translate(translated.text)
                    save_translation_in_dict(to_translate, from_translate)
                    content[key] = from_translate


def check_translation(file: str, skip_line=0):
    dst_filename = compute_dst_filename(file)
    source_yaml = yaml.full_load(open(file))
    dest_yaml = yaml.full_load(open(dst_filename))
    pbar = Bar(max=get_total_lines(dst_filename))
    check_translation_lines(source_yaml, dest_yaml, file, None, pbar, skip_line)
    exit(1)


def check_translation_lines(source_yaml: dict, dest_yaml: dict, src_filename, parent: str = None, pbar: Bar = None,
                            skip_line=0):
    for key in source_yaml:
        pbar.next()
        yaml_keys.append(key)
        value = source_yaml[key]
        if type(value) is dict:
            check_translation_lines(value, dest_yaml, src_filename, key, pbar, skip_line)
        else:
            if skip_line > 0 and pbar.index < skip_line:
                continue
            original_line = source_yaml[key]
            if original_line == "":
                continue
            print(f"\n{Fore.RED}{Style.BRIGHT}Original :{Style.RESET_ALL} " + original_line)

            if parent is None:
                translated_line = dest_yaml[key]
            else:
                translated_line = dest_yaml[parent][key]

            print(f"{Fore.GREEN}{Style.BRIGHT}Translation :{Style.RESET_ALL} {translated_line}")
            confirm = inquirer.confirm(message="Validate ?", default=True).execute()
            if not confirm:
                new_translation = ask_edit_translation(translated_line)
                if new_translation is not None:
                    if parent is None:
                        dest_yaml[key] = new_translation
                    else:
                        dest_yaml[parent][key] = new_translation
                    save_output_translation(dest_yaml, src_filename)


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
    must_check = args.check
    for file in read_source():
        print(f"{Fore.GREEN} Parse {file}{Style.RESET_ALL}")
        if not is_dst_file_exist(file):
            content = translate(file)
            save_output_translation(content, file)
            print(f"Translation finished for file {file}")
        if must_check:
            check_translation(file, args.skip_line)
print(f"All translations finished")
