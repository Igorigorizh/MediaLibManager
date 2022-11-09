import os
from . import medialib_test_cfg
from configparser import ConfigParser
import test

print(dir(test))
print("current dir:",os.getcwd())
cfg = ConfigParser()
cfg.read(medialib_test_cfg)
print(cfg['AUDIO_DATA_PATH']['cue_flac'])

from .. import medialib