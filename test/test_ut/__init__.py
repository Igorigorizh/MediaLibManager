import os
import sys
from yaml import load, Loader
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from medialib import BASE_ENCODING
medialib_test_cfg = './test/config/medialib_test.cfg'

# get config data
cfg = ConfigParser()
cfg.read(medialib_test_cfg)

flac_file = cfg['AUDIO_DATA_PATH']['flac_file'].encode(BASE_ENCODING)
ape_file = cfg['AUDIO_DATA_PATH']['flac_file'].encode(BASE_ENCODING)
wv_file = cfg['AUDIO_DATA_PATH']['flac_file'].encode(BASE_ENCODING)
mp3_file = cfg['AUDIO_DATA_PATH']['mp3_file'].encode(BASE_ENCODING)
m4a_file = cfg['AUDIO_DATA_PATH']['m4a_file'].encode(BASE_ENCODING)
flac_file_data = cfg['TEST_DATA_PATH']['flac_file_data'].encode(BASE_ENCODING)
cue_flac_file = cfg['AUDIO_DATA_PATH']['cue_flac'].encode(BASE_ENCODING)
cue_flac_file_no_unicode = cfg['AUDIO_DATA_PATH']['cue_flac']
cue_flac_data_file = cfg['TEST_DATA_PATH']['cue_flac_data']
cue_flac_data_br_file = cfg['TEST_DATA_PATH']['cue_flac_data_br']
cue_flac_simple_data_file = cfg['TEST_DATA_PATH']['cue_flac_simple_data']

cue_flac_tracks_file = cfg['AUDIO_DATA_PATH']['cue_flac_tracks'].encode(BASE_ENCODING)
cue_flac_tracks_data_file = cfg['TEST_DATA_PATH']['cue_flac_tracks_data']
cue_flac_tracks_data_br_file = cfg['TEST_DATA_PATH']['cue_flac_tracks_data_br']
cue_flac_tracks_simple_data_file = cfg['TEST_DATA_PATH']['cue_flac_tracks_simple_data']



cue_ape_file = cfg['AUDIO_DATA_PATH']['cue_ape'].encode(BASE_ENCODING)
cue_ape_data_file = cfg['TEST_DATA_PATH']['cue_ape_data']
cue_ape_data_br_file = cfg['TEST_DATA_PATH']['cue_ape_data_br']


cue_wavpack_file = cfg['AUDIO_DATA_PATH']['cue_wavpack'].encode(BASE_ENCODING)
cue_wavpack_data_file = cfg['TEST_DATA_PATH']['cue_wavpack_data']
cue_wavpack_data_br_file = cfg['TEST_DATA_PATH']['cue_wavpack_data_br']
cue_wavpack_simple_data_file = cfg['TEST_DATA_PATH']['cue_wavpack_simple_data']


# get expected test data
try:
	with open(cue_ape_data_file, 'r') as stream:
		cue_ape_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_ape_data_file', e)
	print(cue_ape_data_file, '--not ready')

try:
	with open(cue_ape_data_br_file, 'r') as stream:
		cue_ape_data_file_br_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_ape_data_file_br', e)
	print(cue_ape_data_br_file, '--not ready')


try:
	with open(cue_flac_data_file, 'r') as stream:
		cue_flac_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_data_file', e)
	print(cue_flac_data_file, '--not ready')

try:
	with open(cue_flac_data_br_file, 'r') as stream:
		cue_flac_data_file_br_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_data_file_br', e)
	print(cue_flac_data_br_file, '--not ready')

try:
	with open(cue_flac_simple_data_file, 'r') as stream:
		cue_flac_simple_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_simple_data_file', e)
	print(cue_flac_simple_data_file, '--not ready')


try:
	with open(cue_wavpack_data_file, 'r') as stream:
		cue_wavpack_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_wavpack_data_file', e)
	print(cue_wavpack_data_file, '--not ready')

try:
	with open(cue_wavpack_data_br_file, 'r') as stream:
		cue_wavpack_data_file_br_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_wavpack_data_file_br', e)
	print(cue_wavpack_data_br_file, '--not ready')

try:
	with open(flac_file_data, 'r') as stream:
		flac_file_data_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with flac_data_file_br', e)
	print(flac_file_data, '--not ready')


try:
	with open(cue_flac_tracks_data_file, 'r') as stream:
		cue_flac_tracks_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_tracks_data_file', e)
	print(cue_flac_tracks_data_file, '--not ready')

try:
	with open(cue_flac_tracks_data_br_file, 'r') as stream:
		cue_flac_tracks_data_file_br_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_tracks_data_br_file', e)
	print(cue_flac_tracks_data_br_file, '--not ready')

try:
	with open(cue_flac_tracks_simple_data_file, 'r') as stream:
		cue_flac_tracks_simple_data_file_expected = load(stream, Loader=Loader)
except Exception as e:
	print('error with cue_flac_tracks_simple_data_file', e)
	print(cue_flac_tracks_simple_data_file, '--not ready')