import os
import sys

from . import cue_flac_file
from . import BASE_ENCODING
import test

from yaml import load, dump
from pathlib import Path

from medialib.myMediaLib_cue import parseCue

print(cue_flac_file)
res = parseCue(cue_flac_file,'with_bitrate')
#res = parseCue(cue_flac_file)


dump_path = os.path.join(os.path.dirname(str(cue_flac_file,BASE_ENCODING)),'cue_flac_with_bitrate.data')
dump_path = Path(dump_path).as_posix()
print(dump_path)
with open(dump_path, 'wt') as f:
	dump(res,f,default_flow_style=False, allow_unicode=True)
print('Done!',dump_path)