import sys
#windows path trick
sys.path.insert(0,'./medialib')
import myMediaLib_tools

import os
if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
	parser.add_argument('--nas_path_prefix', metavar='path', required=True,
                        help='nas path prefix like //192.168.1.12/folderUSB')	
	args = parser.parse_args()
	
	path_cl = bytes(args.nas_path_prefix,'utf-8')+b'/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/Vivaldi'	
	
	if os.path.exists(path_cl):
		sD = myMediaLib_tools.do_mass_album_FP_and_AccId(path_cl,0,None,None,'multy','FP','ACOUSTID_FP_REQ','MB_DISCID_REQ')		
	else:
		print('path failed')
	
	while input('type exit >>>') != 'exit': pass
	
	
		