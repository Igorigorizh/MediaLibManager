import os
import sys

from . import cue_flac_file
from . import BASE_ENCODING
import test
import json
from yaml import load, dump
from pathlib import Path

from medialib.myMediaLib_cue import parseCue

print(cue_flac_file)
res = parseCue(cue_flac_file,'with_bitrate')
#res = parseCue(cue_flac_file)
#for a in res['trackD']:
	
#	if 'OrigFile' in res['trackD'][a]:
#		res['trackD'][a]['OrigFile'] = str(res['trackD'][a]['OrigFile'],BASE_ENCODING)
#	print(a,res['trackD'][a])	
#	print('-'*60)
	
print(res.keys())
#pretty_data = json.dumps(res['trackD'],sort_keys=True, indent=4)
#print(pretty_data)
dump_path = os.path.join(str(cue_flac_file,BASE_ENCODING),'cue_flac_with_bitrate.data')
dump_path = Path(dump_path).as_posix()
print(dump_path)
#with open(dump_path, 'wt') as f:
#	dump(res,f,default_flow_style=False, allow_unicode=True)
#print(res)