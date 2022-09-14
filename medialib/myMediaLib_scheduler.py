# -*- coding: utf-8 -*-
import os
from posixpath import join, dirname
from os import scandir
import pickle
import zlib
import sqlite3
import chardet
import codecs
import re
import subprocess
import asyncio
from multiprocessing import Pool, cpu_count
from itertools import tee
import configparser

from redis import Redis

import musicbrainzngs
import time
import logging
from pathlib import Path

from myMediaLib_init import readConfigData

from myMediaLib_CONST import BASE_ENCODING
from myMediaLib_CONST import mymedialib_cfg
from myMediaLib_CONST import medialib_fp_cfg

from configparser import ConfigParser

import warnings
from myMediaLib_tools import get_FP_and_discID_for_album
from myMediaLib_tools import find_new_music_folder
from myMediaLib_tools import redis_state_notifier

#from worker import app

from functools import wraps

cfgD = readConfigData(mymedialib_cfg)
cfg_fp = ConfigParser()
cfg_fp.read(medialib_fp_cfg)

logger = logging.getLogger('controller_logger.scheduler')

musicbrainzngs.set_useragent("python-discid-example", "0.1", "your@mail")

redis_connection = Redis(host=cfg_fp['REDIS']['host'], port=cfg_fp['REDIS']['port'], db=0)


def music_folders_generation_scheduler(self, folder_node_path, prev_fpDL, prev_music_folderL,*args):	
	# Генерация линейного списка папок с аудио данным с учетом вложенных папок
	# Промежуточные статусы писать в Redis!!!!
	
	
	if not os.path.exists(folder_node_path):
		print('---!Album path Error:%s - not exists'%folder_node_path)
		return 
	cnt=1	
	fpDL = []
	music_folderL = []
	use_prev_res = False
	prev_fpDL_used = False
	dump_path = ''

	if prev_music_folderL:
		if len(prev_music_folderL)>0:
			music_folderL = prev_music_folderL
			print("Media Folders structure is taken from prev music_folderL with len:",len(music_folderL))
	else:	
		dirL = find_new_music_folder(self,[folder_node_path],[],[],'initial')
		music_folderL = list(map(lambda x: bytes(x+'/',BASE_ENCODING),dirL['music_folderL']))
		print("Media folders structure build with initial folders:",len(music_folderL))
	
	tmp_music_folderL = music_folderL
	
	if prev_fpDL:
		if len(prev_fpDL) > 0:
			print(len(prev_fpDL),prev_fpDL[0:4])
			
			tmp_music_folderL = list(set(music_folderL) - set([a['album_path'] for a in prev_fpDL]))
			
			fpDL = prev_fpDL
			cnt = len(music_folderL) - len(tmp_music_folderL) + 1
			prev_fpDL_used = True
			print("Media Folders structure is recalculated from prev music_folderL with len:",len(tmp_music_folderL))

		if fpDL == []:		
			print('Error with last result folder. Not found in current folders structures')
			return{'music_folderL':music_folderL,'last_folder':last_folder}
			
	print(tmp_music_folderL,len(tmp_music_folderL))
	return tmp_music_folderL
	#job_folders_collect = q.enqueue('myMediaLib_tools.find_new_music_folder', [folder_node_path],[],[],'initial')
	


	