import os
import sys
from yaml import load, dump, Loader
from configparser import ConfigParser
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

medialib_test_cfg = './config/medialib_test.cfg'
from medialib import BASE_ENCODING

cfg = ConfigParser()
cfg.read(medialib_test_cfg)

cue_flac_file = cfg['AUDIO_DATA_PATH']['cue_flac'].encode(BASE_ENCODING)
cue_flac_data_file = cfg['TEST_DATA_PATH']['cue_flac_data']
cue_flac_data_br_file = cfg['TEST_DATA_PATH']['cue_flac_data_br']

print(cue_flac_data_file)
with open(cue_flac_data_file, 'r') as stream:
	cue_flac_data_file_expected = load(stream, Loader=Loader)

with open(cue_flac_data_br_file, 'r') as stream:
	cue_flac_data_file_br_expected = load(stream, Loader=Loader)