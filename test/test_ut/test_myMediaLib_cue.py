from . import flac_file
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