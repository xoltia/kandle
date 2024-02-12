import json
import os
from jamdict import Jamdict
import requests
jam = Jamdict()

def download_confusables() -> dict:
    url = 'http://www.unicode.org/Public/security/8.0.0/confusables.txt'
    r = requests.get(url, allow_redirects=True)
    confusables = {}
    for line in r.text.split('\n'):
        c = line.find('#')
        if c != -1:
            line = line[:c]
        line = line.strip()
        if len(line) == 0:
            continue
        fields = line.split(';')
        fields = [f.strip() for f in fields]
        if len(fields) < 3:
            continue

        def char_from_hex_string(hex_string: str) -> str:
            if len(hex_string) > 4:
                chars_codes = hex_string.split(' ')
                chars = [chr(int(c, 16)) for c in chars_codes]
                return ''.join(chars)
            return chr(int(hex_string, 16))

        confusable, mapping, _ = fields
        confusable_char = char_from_hex_string(confusable)
        mapping_char = char_from_hex_string(mapping)
        if not confusable_char in confusables:
            confusables[confusable_char] = mapping_char
        else:
            print(f'confusable {confusable_char} already exists')

    return confusables

# read filenames from ./public/kanji
dir_path = os.path.dirname(os.path.realpath(__file__))
public_path = os.path.join(dir_path, 'public')
kanji_path = os.path.join(public_path, 'kanji')
_WORDS_OUTPUT = os.path.join(public_path, 'words.json')
_KRAD_OUTPUT = os.path.join(public_path, 'krad.json')
_CONFUSABLES_OUTPUT = os.path.join(public_path, 'confusables.json')
kanji_files = os.listdir(kanji_path)
kanji_files = [f for f in kanji_files if f.endswith('.svg') and len(f) == 9]
kanji_utf8_codes = [f[0:5] for f in kanji_files]

max_length = 4

accepted_pos = [
    'noun (common) (futsuumeishi)',
    'noun or participle which takes the aux. verb suru',
    'pronoun',
]

common_tags = [
    'ichi1',
    'news1',
    'spec1',
    'nf01',
    'nf02',
]

final_kanji_forms = []
result = jam.lookup_iter('%', pos=accepted_pos)
for word in result.entries:
    forms = []
    for form in word.kanji_forms:
        if not any(tag in form.pri for tag in common_tags):
            continue

        if len(form.text) > max_length:
            continue

        valid = True
        for c in form.text:
            if not c in jam.krad:
                valid = False
                break
            utf8_code = hex(ord(c))[2:]
            while len(utf8_code) < 5:
                utf8_code = f'0{utf8_code}'
            if not utf8_code in kanji_utf8_codes:
                valid = False
                break

        if valid:
            forms.append(form.text)

    if len(forms) > 0:
        final_kanji_forms.extend(forms)

# print stats
lens = [0] * max_length
for form in final_kanji_forms:
    lens[len(form)-1] += 1

print(lens)

with open(_WORDS_OUTPUT, 'w') as f:
    f.write(json.dumps(final_kanji_forms))

with open(_KRAD_OUTPUT, 'w') as f:
    f.write(json.dumps(jam.krad))

confusables = download_confusables()
with open(_CONFUSABLES_OUTPUT, 'w') as f:
    f.write(json.dumps(confusables))
