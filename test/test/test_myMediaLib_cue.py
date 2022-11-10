import os
import pytest

from . import cue_flac_file
from . import BASE_ENCODING
from . import cue_flac_data_file_expected
from . import cue_flac_data_file_br_expected
import test
import json
from yaml import load, dump
from pathlib import Path

from medialib.myMediaLib_cue import parseCue

def test_parseCue():
	assert parseCue(cue_flac_file) == cue_flac_data_file_expected
	
def test_parseCue_with_bitrate():
	assert parseCue(cue_flac_file,'with_bitrate') == cue_flac_data_file_br_expected
