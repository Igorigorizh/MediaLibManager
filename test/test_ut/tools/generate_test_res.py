import os
import sys

from .. import cue_flac_file
from .. import flac_file
from .. import cue_wavpack_file
from .. import BASE_ENCODING
import test

from yaml import dump
from pathlib import Path

from medialib.myMediaLib_cue import parseCue 
from medialib.myMediaLib_cue import simple_parseCue
from medialib.myMediaLib_cue import GetTrackInfoVia_ext

#1. flac
#res = parseCue(cue_flac_file,'with_bitrate')
#res = parseCue(cue_flac_file)
#res = simple_parseCue(cue_flac_file)

#dump_path = os.path.join(os.path.dirname(str(cue_flac_file,BASE_ENCODING)),'cue_flac.data')
#dump_path = os.path.join(os.path.dirname(str(cue_flac_file,BASE_ENCODING)),'cue_flac_simple.data')

#2. wavpack
#res = parseCue(cue_wavpack_file)
#res = parseCue(cue_wavpack_file, 'with_bitrate')

dump_path = os.path.join(os.path.dirname(str(cue_wavpack_file,BASE_ENCODING)),'cue_wavpack_with_bitrate.data')

#3. GetTrackInfoVia_ext
res = GetTrackInfoVia_ext(flac_file, 'flac')
dump_path = os.path.join(os.path.dirname(str(flac_file,BASE_ENCODING)),'flac_file.data')

dump_path = Path(dump_path).as_posix()
with open(dump_path, 'wt') as f:
	dump(res,f,default_flow_style=False, allow_unicode=True)
print('Done!',dump_path)