import sys
#windows path trick
sys.path.insert(0,'./medialib')
import myMediaLib_tools
import pickle
from flask import Flask

import os



app = Flask(__name__)

@app.route('/')
def index():
	return 'Hello World'

@app.route('/dump/<num>')
def dump(num):
	dump_path = b'//192.168.1.66/OMVNasUsb/MUSIC/ORIGINAL_MUSIC/ORIGINAL_EASY/Los Incas - El Condor Pasa (1985)/fpgen_1652531874.dump'
	with open(dump_path, 'rb') as f:
		sD = pickle.load(f)
	res = '---------------<BR>'    
	cnt = 1
	for item in sD['fpDL'][int(num)]['convDL']:
		try:
			res += '<BR><BR>%i------[%s]<BR>'%(cnt,str(sD['fpDL'][int(num)]['album_path'],'utf-8'))
		except:
			pass 
		res += str(item['response'])
		cnt+=1        
	return res
if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
	parser.add_argument('--nas_path_prefix', metavar='path', required=True,
                        help='nas path prefix like //192.168.1.12/folderUSB')	
	args = parser.parse_args()
	
	path_cl = bytes(args.nas_path_prefix,'utf-8')+b'/MUSIC/ORIGINAL_MUSIC/ORIGINAL_EASY'	
	
	if os.path.exists(path_cl):
		#sD = myMediaLib_tools.do_mass_album_FP_and_AccId(path_cl,0,None,None,'multy','FP','ACOUSTID_FP_REQ','MB_DISCID_REQ')
		pass    
	else:
		print('path failed')

	app.run()
	
	
	
		