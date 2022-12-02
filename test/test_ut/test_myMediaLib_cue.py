from . import flac_file
from . import ape_file
from . import wv_file
from . import mp3_file
from . import m4a_file
from . import cue_flac_file
from . import flac_file_data_expected
from . import cue_flac_data_file_expected
from . import cue_flac_data_file_br_expected
from . import cue_flac_simple_data_file_expected
from . import cue_flac_file_no_unicode
from . import cue_flac_tracks_file
from . import cue_flac_tracks_data_file_expected
from . import cue_flac_tracks_data_file_br_expected
from . import cue_flac_tracks_simple_data_file_expected

from . import cue_ape_file
from . import cue_ape_data_file_expected
from . import cue_ape_data_file_br_expected


from . import cue_wavpack_file
from . import cue_wavpack_data_file_expected
from . import cue_wavpack_data_file_br_expected

from medialib.myMediaLib_cue import parseCue
from medialib.myMediaLib_cue import simple_parseCue
from medialib.myMediaLib_cue import GetTrackInfoVia_ext
from medialib.myMediaLib_cue import get_audio_object

import datetime


def test_flac_tracks_parseCue():
	assert parseCue(cue_flac_tracks_file) == cue_flac_tracks_data_file_expected

def test_flac_tracks_parseCue_with_bitrate():
	assert parseCue(cue_flac_tracks_file,'with_bitrate') == cue_flac_tracks_data_file_br_expected

def test_flac_tracks_simple_parseCue():
	assert simple_parseCue(cue_flac_tracks_file) == cue_flac_tracks_simple_data_file_expected

def test_flac_parseCue():
	assert parseCue(cue_flac_file) == cue_flac_data_file_expected


def test_flac_parseCue_with_bitrate():
	assert parseCue(cue_flac_file, 'with_bitrate') == cue_flac_data_file_br_expected


def test_flac_simple_parseCue():
	assert simple_parseCue(cue_flac_file) == cue_flac_simple_data_file_expected

def test_flac_no_unicode_simple_parseCue():
	assert simple_parseCue(cue_flac_file_no_unicode) == {'Error':'Not Unicode filename'}

def test_wavpack_parseCue():
	assert parseCue(cue_wavpack_file) == cue_wavpack_data_file_expected


def test_wavpack_parseCue_with_bitrate():
	assert parseCue(cue_wavpack_file, 'with_bitrate') == cue_wavpack_data_file_br_expected


def test_ape_parseCue():
	assert parseCue(cue_ape_file) == cue_ape_data_file_expected


def test_ape_parseCue_with_bitrate():
	assert parseCue(cue_ape_file, 'with_bitrate') == cue_ape_data_file_br_expected
	
	
def test_GetTrackInfoVia_ext(): 
	assert GetTrackInfoVia_ext(flac_file,'flac') ==  flac_file_data_expected

def test_get_audio_object_flac():
	assert get_audio_object(flac_file) ==  {'sample_rate': 44100, 
						'full_length': 3616.2266666666665,
						'full_time': datetime.timedelta(seconds=3616),
						 'bitrate': 1, 'bits_per_sample': 16}

def test_get_audio_object_ape():
	assert get_audio_object(ape_file) ==  {'sample_rate': 44100, 
						'full_length': 3616.2266666666665,
						'full_time': datetime.timedelta(seconds=3616),
						 'bitrate': 1, 'bits_per_sample': 16}

def test_get_audio_object_wv():
	assert get_audio_object(wv_file) ==  {'sample_rate': 44100, 
						'full_length': 3616.2266666666665,
						'full_time': datetime.timedelta(seconds=3616),
						 'bitrate': 1, 'bits_per_sample': 16}

def test_get_audio_object_mp3():
	assert get_audio_object(mp3_file) ==  {'sample_rate': 44100, 
						'full_length': 124.64,
						'full_time': datetime.timedelta(seconds=124),
						 'bitrate': 128, 'bits_per_sample': None}

def test_get_audio_object_m4a():
	assert get_audio_object(m4a_file) ==  {'sample_rate': 44100, 
						'full_length': 142.89333333333335,
						'full_time': datetime.timedelta(seconds=142),
						 'bitrate': 7,'bits_per_sample': 16}