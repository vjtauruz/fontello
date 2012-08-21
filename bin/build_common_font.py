#!/usr/bin/env python

import os
import sys
from sys import stderr
import argparse
import yaml
import json
import fontforge
from pprint import pprint

GLYPHS_CODE_START = 0xE800

def read_config(config_path):
    try:
        return yaml.load(open(config_path, 'r'))
    except IOError as (errno, strerror):
        stderr.write("Cannot open %s: %s\n" % (args.config, strerror))
        sys.exit(1)
    except yaml.YAMLError, e:
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            stderr.write("YAML parser error in file %s at line %d, col %d\n" %
                (args.config, mark.line + 1, mark.column + 1))
        else:
            stderr.write("YAML parser error in file %s: %s\n" % (args.config, e))
        sys.exit(1)

parser = argparse.ArgumentParser(description='Merge glyphs from '
        'several fonts to single font')
parser.add_argument('-i', '--input_fonts', type=str, required=True,
        action='append', nargs='+', help='Input fonts')
parser.add_argument('-o', '--dst_font', type=str, required=True,
        help='Output font')
parser.add_argument('-c', '--remap_config', type=argparse.FileType('wb', 0),
        required=True,
        help='Output font remap config file')

args = parser.parse_args()

input_fonts = []
for item in args.input_fonts:
    input_fonts += item

new_font_config = {'name': 'fontello', 'glyphs': []}

# init new font
new_font = fontforge.font()
new_font.encoding = 'UnicodeFull'

new_glyph_code = GLYPHS_CODE_START

for path in input_fonts:
    if os.path.isdir(path):
        config = read_config(os.path.join(path, 'config.yml'))

        if not config.get('font', {}).has_key('fontname'):
            stderr.write("Bad config format %s: \n" % os.path.join(path, 'config.yml') )

        font_name = config.get('font', {}).get('fontname', None)

        font_path = os.path.join(path, 'font', font_name + '.ttf')

        src_font = fontforge.open(font_path)

        for glyph in config['glyphs']:
            glyph_info = {
                'orig_code': glyph['code'],
                'code': new_glyph_code,
                'src': font_name
            }
            new_font_config['glyphs'].append(glyph_info)

            # cp glyph
            src_font.selection.select(("unicode",), glyph['code'])
            src_font.copy()
            new_font.selection.select(("unicode",), new_glyph_code)
            new_font.paste()

            new_glyph_code += 1

try:
    new_font.generate(args.dst_font)
except:
    stderr.write("Cannot write to file %s\n" %args.dst_font)
    sys.exit(1)


args.remap_config.write(json.dumps(new_font_config))
