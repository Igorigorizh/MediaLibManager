import sys
#windows path trick
sys.path.insert(0,'./medialib')
from myMediaLib_CONST import medialib_fp_cfg
from configparser import ConfigParser

from redis import Redis
from rq import Queue, Worker

import myMediaLib_scheduler
import pickle

import os

#dump_path = b'//192.168.1.66/OMVNasUsb/MUSIC/ORIGINAL_MUSIC/ORIGINAL_EASY/Los Incas - El Condor Pasa (1985)/fpgen_1652531874.dump'



if __name__ == '__main__':
	import argparse

	#parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
	#parser.add_argument('--nas_path_prefix', metavar='path', required=True,
        #                help='nas path prefix like //192.168.1.12/folderUSB')	
	#args = parser.parse_args()
	nas_path_prefix="//RPI-NAS-OMV/OMVNasUSB"
	path_cl = bytes(nas_path_prefix,'utf-8')+b'/MUSIC/ORIGINAL_MUSIC/ORIGINAL_RODINA'	
	path_cl = bytes(nas_path_prefix,'utf-8')+b'/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/Vivaldi/Antonio Vivaldi - 19 Sinfonias and Concertos for Strings and Continuo/'	
	dump_path = bytes('//192.168.1.66/OMVNasUsb/MUSIC/ORIGINAL_MUSIC/ORIGINAL_RODINA/Федор Чистяков/2008 - Ноль - Лучшие песни/fpgen_1652646620.dump','utf-8')
	with open(dump_path, 'rb') as f:
		sD_prev = pickle.load(f)
	if os.path.exists(path_cl):
		#sD = myMediaLib_tools.do_mass_album_FP_and_AccId(path_cl,0,sD_prev['fpDL'],sD_prev['music_folderL'],'multy','FP','ACOUSTID_FP_REQ','MB_DISCID_REQ')
		folderL = myMediaLib_scheduler.music_folders_generation_scheduler(path_cl,[],[])
		sD = myMediaLib_scheduler.mass_FP_scheduler(folderL,0,'multy','FP','ACOUSTID_FP_REQ','MB_DISCID_REQ')
		pass    
	else:
		print('path failed')
	
	while input('type exit >>>') != 'exit': pass
		