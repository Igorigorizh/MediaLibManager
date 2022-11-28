# -*- coding: utf-8 -*-
import os
from posixpath import join, dirname
from os import scandir
import pickle
import time
import zlib
import sqlite3
import chardet
import codecs
import re
import subprocess
import asyncio
from multiprocessing import Pool, cpu_count
from itertools import tee
import json
import logging
from pathlib import Path
from functools import wraps

from medialib.myMediaLib_init import readConfigData

from medialib.myMediaLib_adm import getFolderAlbumD_fromDB
from medialib.myMediaLib_adm import db_request_wrapper
from medialib.myMediaLib_adm import collect_albums_folders

from medialib.myMediaLib_fs_util import Media_FileSystem_Helper as mfsh

from medialib import BASE_ENCODING
from medialib import mymedialib_cfg
from medialib import medialib_fp_cfg

from configparser import ConfigParser


cfgD = readConfigData(mymedialib_cfg)
cfg_fp = ConfigParser()
cfg_fp.read(medialib_fp_cfg)

logger = logging.getLogger('controller_logger.tools')

posix_nice_value = int(cfg_fp['FP_PROCESS']['posix_nice_value'])


def quick_check_medialib_utf8_issue(*args):
	# быстрая проверка таблиц на соответствие unicode
	mlDL = [{'table':'album','filedL':['path','album','search_term']},
			{'table':'track','filedL':['path','artist','album','title','cue_fname']},
			{'table':'artist','filedL':['artist','search_term','description']},
			{'table':'artist_cat_rel','filedL':['artist_name']},
			{'table':'category','filedL':['category_short_name','category_descr']},
			{'table':'category_type','filedL':['categ_type_name','categ_type_descr']},
			{'table':'GROUPS_PL','filedL':['descr','ref_folder','short_name']},
			{'table':'tag','filedL':['tag_name','tag_descr']},
			{'table':'track_tag','filedL':['tag_name']}
			]
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)	
	c = db.cursor()		
	#print 'db.text_factory:',db.text_factory
	exec_err_L = []
	fetch_err_L = []
	for table_item in mlDL:
		for fld_name in table_item['filedL']:
			req_data = (fld_name,table_item['table'])
			req = 'select %s from %s'%req_data
			#print [req]
			msg_str = 'Table [%20s] field (%25s):'%(req_data[1].upper(),req_data[0])
			print(msg_str, end=' ')
			msg_exec = msg_fetch ='Failed'
			try:
				c.execute(req)
				msg_exec = 'OK'
			except Exception as e:
				print(e)
				exec_err_L.append((req_data,msg_str,e))
			
			if msg_exec == 'OK':
				try:	
					r = c.fetchall()	
					msg_fetch = 'OK'
				except Exception as e:
					#print e	
					fetch_err_L.append((req_data,msg_str,e))	
				
			print('[exec: %s, fetch:%s]'%(msg_exec,msg_fetch))	
		
		print("*"*50)	
		
	fld_erL = []	
	if 'with_fetch_detailes' in args:
		tabl_set = set([a[0][1] for a in fetch_err_L])
		print([tabl_set])
		for table in tabl_set:
			if 'track' == table:
				req = 'select id_track from %s'%(table)
			elif 'artist' == table:
				req = 'select id_artist from %s'%(table)
			elif 'album' == table:
				req = 'select id_album from %s'%(table)	
			else:
				continue
			
			c.execute(req)
			try:
				r = c.fetchall()	
			except Exception as e:
				print(e)
				
			
			print('Table:',table)
			idL = [a[0] for a in r]	
			filedL = [itm['filedL'] for itm in mlDL if itm['table'] == table][0]
			err_cnt = utf_8_err_cnt = 0
			#print filedL
			for a in filedL:
				print('Processing field:',a,' of ',table.upper())
				i = 0
				err_cnt = utf_8_err_cnt = 0
				for id in idL:
					
					req = 'select %s from %s where id_%s = %s'%(a,table,table,str(id))
					exec_ok = True
					try:
						c.execute(req)
					except Exception as e:
						if 'utf-8' in e.message.lower():
							utf_8_err_cnt+=1
						fld_erL.append({'table':table,'field':a,'id':id,'error':e,'request':req})
						exec_ok = False
						err_cnt+=1
						
					if exec_ok:	
						try:
							r = c.fetchone()	
						except Exception as e:
							fld_erL.append({'table':table,'field':a,'id':id,'error':e})		
							if 'utf-8' in e.message.lower():
								utf_8_err_cnt+=1
							err_cnt+=1
						
					if i%1000 == 0:
						print('%i[%i]'%(i,err_cnt), end=' ')
					i+=1
				if utf_8_err_cnt == err_cnt and err_cnt > 0:
					print()
					print('All issues %s %s are UTF-8'%(table,a))
				elif utf_8_err_cnt == err_cnt and err_cnt == 0:
					print()
					print('No issues in %s %s --> OK'%(table,a))
				print()	
				len_fld_erL = len(fld_erL)
				print('fld_erL:%i, utf_8_err_cnt:%i'%(len_fld_erL,utf_8_err_cnt))
				
			
	c.close()
	db.close()
	return {'exec_err_L':exec_err_L,'fetch_err_L':fetch_err_L,'fld_erL':fld_erL}
	
def check_medialib_TRACK_utf8_issue(fs_folderL,erL,*args):
	# аналог функции check_medialib_TRACK_utf8_issue, но входящие параметры другие, т.к. сравнение на шаге 3 с полным именем файла
	# т.е использовать один и тотже список нельзя!
	t_start = time.time()
	# Сценарий миграции БД на unicode: формирования списка пересчета CRC32 на основе пересчета CRC32 для путей в unicode
	# все преобразования .decode('cp1251') сделаны из-за первичного сохранения объектов в БД НЕ в UNICODE!
	dbPath = cfgD['dbPath']
	# таблица TRACK (пока только эта таблица) - собираем все CRC32 для путей из БД
	req = "select path_crc32, id_track  from track"
	db_TRACK_pathL = db_request_wrapper(None,req)
	
	convL = []
	dublicatL = []
	er_tb_deleteL = []
	er_cueL = []
	er_titleL = []
	er_artistL = []
	i = 0
	if erL == []:
		print("1. MediaLib db scanning...")
		db = sqlite3.connect(dbPath)	
		c = db.cursor()		
		for a in db_TRACK_pathL:
			if i%10000 == 0:
				print(i, end=' ')
			i+=1
			# Get single ALBUM entry via path_crc32
			req = "select path from track where id_track = %s"%(str(a[1]))
			
			try:
				c.execute(req)
			except Exception as e:
				if 'UTF-8' in e.message: 
				# отбираем записи где появилась ошибка преобразования unicode связанная path
				#print '*',
					if a[0] not in erL:
						erL.append(a[0])
					else:
						# в процессе добавления альбомов появились дубликаты. Из-за некорректного алгоритма добавления
						# Дубликаты надо собрать и исправить отдельно в БД 
						dublicatL.append((a[0],a[1]))	
						print('=', end=' ')
					
					
			req = "select cue_fname from track where id_track = %s"%(str(a[1]))
			try:
				c.execute(req)
			except Exception as e:
			# отбираем записи где появилась ошибка преобразования unicode связанная path
				#print '*',
				if 'UTF-8' in e.message: 
					if a[0] not in er_cueL:
						er_cueL.append(a[0])
						
						
			req = "select title from track where id_track = %s"%(str(a[1]))
			try:
				c.execute(req)
			except Exception as e:
			# отбираем записи где появилась ошибка преобразования unicode связанная title
				#print '*',
				if 'UTF-8' in e.message: 
					if a[0] not in er_titleL:
						er_titleL.append(a[0])			
						
			
			req = "select artist from track where id_track = %s"%(str(a[1]))
			try:
				c.execute(req)
			except Exception as e:
			# отбираем записи где появилась ошибка преобразования unicode связанная artist
				#print '*',
				if 'UTF-8' in e.message: 
					if a[0] not in er_titleL:
						er_artistL.append(a[0])				
				
		c.close()			
		db.close()
		
		check_cue = False
		time_stop_diff = int(time.time()-t_start)	
		print()
		if set(er_cueL).issubset(set(erL)):
			check_cue = True
			print('Cue error list is subset of Path error list')
		else:
			print('Warning! Cue errors are is NOT subset of Path error list, check it separately!')
			
			
		check_title = False
		print()
		if set(er_titleL).issubset(set(erL)):
			check_title = True
			print('Title error list is subset of Path error list')
		else:
			print('Warning! Title errors are is NOT subset of Path error list, check it separately!')	
			
			
		check_artist = False
		print()
		if set(er_artistL).issubset(set(erL)):
			check_artist = True
			print('Artist error list is subset of Path error list')
		else:
			print('Warning! Artist errors are is NOT subset of Path error list, check it separately!')		
			print('er_artistL dif len:',len(set(erL).intersection(set(er_artistL))))
		
		print()		
		print("		MediaLib containes UTF8 decoding issues:",len(erL))	
		print("		MediaLib Album containes dublicates (dublicatL):",len(dublicatL))	
		print('Finished in %i sec.'%(time_stop_diff))

	# check path existence for failed path_crc32
	print()
	print("2. Checking path existence for failed path_crc32 from erL:",len(erL))
	i = 0
	
	t_2 = time.time()	
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	# !! Первый проход с подключением к бд с db.text_factory = str
	if 'no_utf8' in args:
		db.text_factory = str	
	req = "select id_track, path_crc32, path, cue_fname,title,artist,cue_num from TRACK where path_crc32 in (%s)"%(str(erL)[1:-1])
	try:
		c.execute(req)
	except Exception as e:
		print(e)	
		
	try:	
		r = c.fetchall()	
	except Exception as e:
		print(e)	
		
	print('Pathes for erL retrieved in %i sec'%(int(time.time()-t_2)))  	
		
	track_path = ''
		
	for req_res_item in r:
			#print 'dublicat',req_res_item
			
		try:
			track_path = req_res_item[2]
		except	Exception as e:
			print(e)
			print('Error: request res: %s, req: %s'%(str(r),str(req)))
			return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':[]} 
		if not os.path.exists(track_path):
			er_tb_deleteL.append((req_res_item[1],req_res_item[0]))
		else:
			#id_track, path, cue_fname
			convL.append((req_res_item[0],req_res_item[1],req_res_item[2],req_res_item[3],req_res_item[4],req_res_item[5],req_res_item[6]))
		if i%1000 == 0:
			print(i, end=' ')
		i+=1	
			
	c.close()			
	db.close()					
	
	print()		
	print("		Media lib album not exists and to be deleted issues:",len(er_tb_deleteL))	
	print("		Media lib album to be matched and ajusted (convL):",len(convL))	
	time_stop_diff = int(time.time()-t_2)
	print('Finished in %i sec.'%(time_stop_diff))
	
	if set(erL) == set([a[0] for a in er_tb_deleteL]):
		print('2.1 Success: erL  is in sync with er_tb_deleteL')
	else:
		print('2.1 Issue: erL  is NOT in sync with er_tb_deleteL')
	
	dirL = []
	if 'collect_dirs_for_preproc' in args:
		
		for a in convL:
			dir_name = os.path.dirname(a[1])
			if dir_name not in dirL:
				dirL.append(dir_name)
		print('convL with dirL substituted dirL:',len(dirL))		
	
	
	t_2 = time.time()	
	matchL = []
	real_fs_folder_path = ''
	pathD = {}
	
	if 'fast_convL_processing' in args:
		print('fast_convL_processing is on') 
		print("3. DB and FS track names matching only at convL:%i..."%(len(convL)))
		i = 0
		t_2 = time.time()
		for b in convL:
			
			db_fs_dir_name = os.path.dirname(b[2].decode('cp1251'))
			crc32_db_fs_dir_name = zlib.crc32(db_fs_dir_name.encode(BASE_ENCODING))
			
			fileL = []			
			if crc32_db_fs_dir_name not in pathD:
				pathD[crc32_db_fs_dir_name] = []
				if os.path.exists(db_fs_dir_name):
					fileL = scandir.listdir(db_fs_dir_name)
					
					for file_name in fileL:
						for frm in ['.mp3','.ape','.flac']:
							if frm in file_name.lower():
								pathD[crc32_db_fs_dir_name].append(join(db_fs_dir_name,file_name))			
						
						
					# Not CUE scenario
			for real_fs_file_path in pathD[crc32_db_fs_dir_name]:
				db_fs_folder_file_path = b[2].decode('cp1251')
				if not os.path.exists(db_fs_folder_file_path):
					print('Error with decoded path file name:[%s]'%(db_fs_folder_file_path))
			
				if real_fs_file_path == db_fs_folder_file_path:
					crc32_1 = zlib.crc32(db_fs_folder_file_path.encode(BASE_ENCODING))
				
						#print "*",
					if b[1] in er_cueL:
						
						db_fs_cue_file_path = b[3].decode('cp1251')
						crc32_1 = zlib.crc32((db_fs_cue_file_path + ',' + str(b[6])).encode(BASE_ENCODING))
						# проверить доступность нового поти
						if not os.path.exists(db_fs_cue_file_path):
							print('Error with decoded cue file name:[%s]'%(db_fs_cue_file_path))
					else:
						db_fs_cue_file_path = None
					
					new_title = None	
					if b[1] in er_titleL:
						new_title = b[4].decode('cp1251')
						
					new_artist = None	
					if b[1] in er_artistL:
						new_artist = b[4].decode('cp1251')	
						
						
					matchL_item = {'new_crc32':crc32_1,'old_crc32':b[1],'new_path':db_fs_folder_file_path,'id_track': b[0],'new_cue_fname':db_fs_cue_file_path,'new_title':new_title,'new_artist':new_artist}
					
					if matchL_item not in matchL:
						matchL.append(matchL_item)
								# Еще могут быть дубликаты с темже crc32 и разными 'id_album' поэтому надо дополнить matchL значиниями из списка дубликатов
					else:
						print(b[2])
			if i%1000 == 0:
				print('%i[%i]'%(i,len(matchL)), end=' ')	
			i+=1		
			
		print()				
		print("Converded and Decoded:",len(matchL))
		print("Media dirs found:",len(pathD))
		time_stop_diff = int(time.time()-t_2)	
		print()
		print('Finished in %i sec.'%(time_stop_diff))
		
		
		return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':matchL,'dublicatL':dublicatL,'pathD':pathD,'check_cue':check_cue,'er_artistL':er_artistL}	
	
	if fs_folderL != []:
		print("3. DB and FS track names matching at %i folders..."%(len(fs_folderL)))
		i = 0
		fileL = []
		for a in fs_folderL:
			t_3 = time.time()
			
			real_fs_file_path = ''
			real_fs_file_pathL = []
			is_media = False
			
			
			real_fs_folder_path = join(a[0],a[1])
			crc32_real_fs_path = zlib.crc32(real_fs_folder_path.encode(BASE_ENCODING))
			if crc32_real_fs_path not in pathD:
				pathD[crc32_real_fs_path] = []
				if os.path.exists(real_fs_folder_path):
					fileL = scandir.listdir(real_fs_folder_path)
					is_media = False
					for file_name in fileL:
						for frm in ['.mp3','.ape','.flac']:
							if frm in file_name.lower():
								is_media = True
								pathD[crc32_real_fs_path].append(join(real_fs_folder_path,file_name))
					
					if not is_media:
						i+=1
						continue
					
				else:
					i+=1
					continue
					
			
			#print real_fs_folder_path
			for b in convL:
			
				dir_name = os.path.dirname(b[2].decode('cp1251'))
				
				if dir_name != real_fs_folder_path:
					continue
						
					# Not CUE scenario
				for real_fs_file_path in pathD[crc32_real_fs_path]:
					db_fs_folder_file_path = b[2].decode('cp1251')
				
					if real_fs_file_path == db_fs_folder_file_path:
						crc32_1 = zlib.crc32(db_fs_folder_file_path.encode(BASE_ENCODING))
				
						#print "*",
						matchL_item = {'new_crc32':crc32_1,'old_crc32':b[1],'new_path':db_fs_folder_file_path,'id_track': b[0]}
						if matchL_item not in matchL:
							matchL.append({'new_crc32':crc32_1,'old_crc32':b[1],'new_path':db_fs_folder_file_path,'id_track': b[0]})
								# Еще могут быть дубликаты с темже crc32 и разными 'id_album' поэтому надо дополнить matchL значиниями из списка дубликатов
						else:
							print(b[2])
		
			if i%100 == 0:
				print('%i[%i]'%(i,len(matchL)), end=' ')
				if i%1000 == 0:
					time_stop_diff = int(time.time()-t_3)
					print('Passed %i sec. len matchL: %i, pathD:%i'%(time_stop_diff,len(matchL),len(pathD)))	
				
				#print [real_fs_folder_path], type(real_fs_folder_path)
				#print [db_fs_folder_path], type(db_fs_folder_path)
			i+=1
		time_stop_diff = int(time.time()-t_2)	
		print()
		print('Finished in %i sec.'%(time_stop_diff))
		
	print("Matching found:",len(matchL))
	print("Matching media dirs found:",len(pathD))
		
	return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':matchL,'dublicatL':dublicatL,'pathD':pathD,'check_cue':check_cue}	
		

def check_medialib_ALBUM_utf8_issue(fs_folderL,erL,*args):
	# Сценарий миграции БД таблицы ALBUM на unicode: формирования списка пересчета CRC32 на основе пересчета CRC32 для путей в unicode
	dbPath = cfgD['dbPath']
	t_start = time.time()
	# таблица ALBUM (пока только эта таблица) - собираем все CRC32 для путей из БД
	req = "select path_crc32, id_album  from ALBUM"
	db_ALBUM_pathL = db_request_wrapper(None,req)
	
	convL = []
	dublicatL = []
	er_tb_deleteL = []
	i = 0
	if erL == []:
		print("1. MediaLib db scanning...")
		db = sqlite3.connect(dbPath)	
		
		for a in db_ALBUM_pathL:
			if i%1000 == 0:
				print(i, end=' ')
			i+=1
			# Get single ALBUM entry via path_crc32
			r = getFolderAlbumD_fromDB(None,db,a[0],[],'folder_tree_nodes')
			# отбираем записи где появилась ошибка преобразования unicode связанная path
			if 'error_message' in r:
				#print '*',
				if a[0] not in erL:
					erL.append(a[0])
				else:
					# в процессе добавления альбомов появились дубликаты. Из-за некорректного алгоритма добавления
					# Дубликаты надо собрать и исправить отдельно в БД 
					dublicatL.append((a[0],a[1]))	
					#print '=',
		db.close()			
		print()		
		print("		MediaLib containes UTF8 decoding issues:",len(erL))	
		print("		MediaLib Album containes dublicates (dublicatL):",len(dublicatL))	
	
	time_stop_diff = int(time.time()-t_start)
	print('Finished DB scanning in %i sec.'%(time_stop_diff))
	# check path existence for failed path_crc32
	print()
	print("2. Checking path existence for failed path_crc32 from erL:",len(erL))
	i = 0
	t_2 = time.time()
	
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	# !! Первый проход с подключением к бд с db.text_factory = str -> флаг 'no_utf8'
	if 'no_utf8' in args:
		print(' db.text_factory = str --> Activated')
		db.text_factory = str	
	else:
		print(' db.text_factory = Default')
	req = "select id_album, path, path_crc32 from ALBUM where path_crc32 in (%s)"%(str(erL)[1:-1])
	try:
		c.execute(req)
	except Exception as e:
		print(e)	
		
	try:	
		r = c.fetchall()	
	except Exception as e:
		print(e)	
		
	#print 'Pathes for erL retrieved in %i sec'%(int(time.time()-t_2)) 
	
	t_2 = time.time()
	for req_res_item in r:
		#print 'dublicat',req_res_item
		try:
			album_path = req_res_item[1]
		except	Exception as e:
			print(e)
			print('Error: request res: %s, req: %s'%(str(r),str(req)))
			return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':[]} 
		if not os.path.exists(album_path):
			er_tb_deleteL.append((req_res_item[2],req_res_item[1],req_res_item[0]))
		else:
			convL.append((req_res_item[2],req_res_item[1],req_res_item[0]))
		if i%100 == 0:
			print(i, end=' ')
		i+=1	
	
	print()		
	print("		Media lib album not exists and to be deleted issues:",len(er_tb_deleteL))	
	print("		Media lib album to be matched and ajusted (convL):",len(convL))	
	
	c.close()			
	db.close()
	time_stop_diff = int(time.time()-t_2)
	print('Finished conversionL generation in %i sec.'%(time_stop_diff))
	
	if set(erL) == set([a[0] for a in er_tb_deleteL]):
		print('2.1 Success: erL  is in sync with er_tb_deleteL')
	else:
		print('2.1 Issue: erL  is NOT in sync with er_tb_deleteL')
		#print set(erL)
		#print set([a[0] for a in er_tb_deleteL])
	# delete from ALBUM, TRACK
	
	ignL = [a[0] for a in er_tb_deleteL]
	
	
	# match DB path and file system folder path	
	t_2 = time.time()
	matchL = []
	
	if 'fast_convL_processing' in args:
		print('fast_convL_processing is on') 
		print("3. DB folders names converted only at convL:%i..."%(len(convL)))
		i = 0
		t_2 = time.time()
		for b in convL:	
			db_fs_folder_path = b[1].decode('cp1251')
			crc32_2 = zlib.crc32(db_fs_folder_path.encode(BASE_ENCODING))
			matchL_item = {'new_crc32':crc32_2,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]}
			if matchL_item not in matchL:
				matchL.append({'new_crc32':crc32_2,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]})
				# Еще могут быть дубликаты с темже crc32 и разными 'id_album' поэтому надо дополнить matchL значиниями из списка дубликатов
				convL_found = True	
	
			if i%1000 == 0:
				print('%i[%i]'%(i,len(matchL)), end=' ')
			i+=1	
					
		
		time_stop_diff = int(time.time()-t_2)	
	
		print()
		print('Finished with fast mode in %i sec.'%(time_stop_diff))	
		print("Matching found:",len(matchL))
		return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':matchL,'dublicatL':dublicatL}
	
	
	
	
	if fs_folderL != []:
		print("3. DB and FS folders names matching...")
		i = 0
		for a in fs_folderL:
			real_fs_folder_path = join(a[0],a[1])

			#print real_fs_folder_path
			convL_found = False
			for b in convL:
				db_fs_folder_path = b[1].decode('cp1251')
				
				if real_fs_folder_path == db_fs_folder_path:
					crc32_1 = zlib.crc32(real_fs_folder_path.encode(BASE_ENCODING))
					crc32_2 = zlib.crc32(db_fs_folder_path.encode(BASE_ENCODING))
					#print "*",
					matchL_item = {'new_crc32':crc32_1,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]}
					if matchL_item not in matchL:
						matchL.append({'new_crc32':crc32_1,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]})
						# Еще могут быть дубликаты с темже crc32 и разными 'id_album' поэтому надо дополнить matchL значиниями из списка дубликатов
						convL_found = True	
			
			# На всякий случай проверка, что хоть что-то нашли	
			#if not convL_found:			
			#	print '-',		
			#	pass
			#else:	
			#	print '+',		
				
			if i%1000 == 0:
				print('%i[%i]'%(i,len(matchL)), end=' ')
				#print [real_fs_folder_path], type(real_fs_folder_path)
				#print [db_fs_folder_path], type(db_fs_folder_path)
			i+=1	
					
		
		time_stop_diff = int(time.time()-t_2)	
		print()
		print('Finished in %i sec.'%(time_stop_diff))	
		print("Matching found:",len(matchL))
	return {"erL":erL,"er_tb_deleteL":er_tb_deleteL,'convL':convL,'matchL':matchL,'dublicatL':dublicatL}
	
def mass_album_track_artist_table_update_path_crc32_ajust(matchL,mode):
	# Функция исправления БД таблиц(ALBUM,..) на основании списка matchL
	# matchL[{'new_crc32':crc32_1,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]},]
	# resBuf_ml_folder_tree_buf_path = cfgD['ml_folder_tree_buf_path']
	# f = open(resBuf_ml_folder_tree_buf_path,'r')
	# Obj = pickle.load(f)
	
	#res = myMediaLib_tools.check_medialib_utf8_issue(Obj['folder_list'],[])
	#ss = myMediaLib_tools.mass_album_table_update_path_crc32_ajust(res['matchL'])
	#>>> f = open(resDBS['resBuf_save'],'r')
	#>>> Obj = pickle.load(f)
	#>>> f.close()
	#>>> r.keys()
	t_2 = time.time()
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)
	requestD = {}
	if mode.lower() == 'album'  or mode.lower() == 'album_crc32':
		mode_dif = 100
		requestD['album'] = {'cursor':db.cursor(),'req':''}
		requestD['album_cat_rel'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_album_ref'] = {'cursor':db.cursor(),'req':''}
		requestD['album_reference'] = {'cursor':db.cursor(),'req':''}
		requestD['album_reference_2'] = {'cursor':db.cursor(),'req':''}
		requestD['track'] = {'cursor':db.cursor(),'req':''}
	elif mode.lower() == 'artist' or mode.lower() == 'artist_crc32':	
		mode_dif = 100
		requestD['artist'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_album_ref'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_cat_rel'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_reference'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_reference_2'] = {'cursor':db.cursor(),'req':''}
		requestD['track'] = {'cursor':db.cursor(),'req':''}
			
	elif mode.lower() == 'track' or mode.lower() == 'track_crc32':
		
		mode_dif = 1000
		requestD['track'] = {'cursor':db.cursor(),'req':''}
		requestD['track_tag'] = {'cursor':db.cursor(),'req':''}
		
		if mode.lower() == 'track':
			requestD['track_title'] = {'cursor':db.cursor(),'req':''}

		
	i=0
	resL=[]
	reqL = []
	res = ''
	print('matchL:',len(matchL))
	for a in matchL:
		# update ALBUM
		if mode.lower() == 'album' or mode.lower() == 'album_crc32':
			if mode.lower() == 'album':
				rec_m = (a['new_path'],a['new_crc32'],a['id_album'])
				requestD['album']['req'] = """update album set path = "%s", path_crc32 = %s where id_album = %s"""%rec_m
			
			if mode.lower() == 'album_crc32':
				rec_m = (a['new_crc32'],a['id_album'])
				requestD['album']['req'] = """update album set path_crc32 = %s where id_album = %s"""%rec_m
			
			
			# update album_cat_rel
			rec_m = (a['new_crc32'],a['id_album'])
			requestD['album_cat_rel']['req'] = """update album_cat_rel set album_crc32 = %s where id_album = %s"""%rec_m
			#reqL.append(req)
			
			# update artist_album_ref
			requestD['artist_album_ref']['req'] = """update artist_album_ref set album_crc32 = %s where id_album = %s"""%rec_m
			#reqL.append(req)
			
			# update ALBUM_REFERENCE
			requestD['album_reference']['req'] = """update ALBUM_REFERENCE set album_crc32 = %s where id_album = %s"""%rec_m
			#reqL.append(req)
			requestD['album_reference_2']['req'] = """update ALBUM_REFERENCE set album_crc32_ref = %s where id_album_ref = %s"""%rec_m
			#reqL.append(req)
			
			rec_m = (a['new_crc32'],a['old_crc32'])
			requestD['track']['req'] = """update track set album_crc32 = %s where album_crc32 = %s"""%rec_m
		
		elif mode.lower() == 'artist' or mode.lower() == 'artist_crc32':
			if mode.lower() == 'artist':
				rec_m = (a['new_crc32'],a['id_artist'])
				requestD['artist']['req'] = """update artist set artist_crc32 = %s where id_artist = %s"""%rec_m
			
			if mode.lower() == 'artist_crc32':
				rec_m = (a['new_crc32'],a['id_artist'])
				requestD['artist']['req'] = """update artist set artist_crc32 = %s where id_artist = %s"""%rec_m
			
			
			# update artist_cat_rel
			rec_m = (a['new_crc32'],a['id_artist'])
			requestD['artist_cat_rel']['req'] = """update artist_cat_rel set artist_crc32 = %s where id_artist = %s"""%rec_m
			#reqL.append(req)
			
			# update artist_album_ref
			requestD['artist_album_ref']['req'] = """update artist_album_ref set artist_crc32 = %s where id_artist = %s"""%rec_m
			#reqL.append(req)
			
			rec_m = (a['new_crc32'],a['old_crc32'])
			# update artist_REFERENCE
			requestD['artist_reference']['req'] = """update artist_REFERENCE set artist_crc32 = %s where artist_crc32 = %s"""%rec_m
			#reqL.append(req)
			requestD['artist_reference_2']['req'] = """update artist_REFERENCE set ref_artist_crc32 = %s where ref_artist_crc32 = %s"""%rec_m
			#reqL.append(req)
			
			rec_m = (a['new_crc32'],a['old_crc32'])
			requestD['track']['req'] = """update track set artist_crc32 = %s where artist_crc32 = %s"""%rec_m
		
		elif mode.lower() == 'track' or mode.lower() == 'track_crc32':
			if mode.lower() == 'track':
				if a['new_cue_fname'] == None:
					rec_m = (a['new_path'],a['new_crc32'],a['id_track'])
					requestD['track']['req'] = """update track set path = "%s", path_crc32 = %s  where id_track = %s"""%rec_m
				else:
					rec_m = (a['new_path'],a['new_crc32'],a['new_cue_fname'],a['id_track'])
					requestD['track']['req'] = """update track set path = "%s", path_crc32 = %s, cue_fname = "%s" where id_track = %s"""%rec_m
					
				
				if a['new_title'] != None:
					rec_m = (a['new_title'],a['id_track'])
					requestD['track_title']['req'] = """update track set title = "%s" where id_track = %s"""%rec_m
			elif mode.lower() == 'track_crc32':		
				rec_m = (a['new_crc32'],a['id_track'])
				requestD['track']['req'] = """update track set path_crc32 = %s  where id_track = %s"""%rec_m
			
			rec_m = (a['new_crc32'],a['id_track'])
			requestD['track_tag']['req'] = """update track_tag set path_crc32 = %s where id_track = %s"""%rec_m	
			
				
			
				
		#reqL.append(req)
		
		for tabl_key in requestD:
			try:
				requestD[tabl_key]['cursor'].execute(requestD[tabl_key]['req'])
				#res = c.fetchall()
			except Exception as e:
				print('\n',e,'\n')
				print(requestD[tabl_key]['req'])
				for tabl_key in requestD:
					requestD[tabl_key]['cursor'].close()
				db.close()				
				logger.critical('Exception: %s'%(str(e)))
				return res
				
		#res = c.fetchall()
		#resL.append(res)	
				
		if i%mode_dif == 0:
			print(i, end=' ')
			
		i+=1
	for tabl_key in requestD:
		requestD[tabl_key]['cursor'].close()
	
	db.commit()
	db.close()	
	time_stop_diff = int(time.time()-t_2)
	print()
	print('Finished in %i sec.'%(time_stop_diff))	
	return resL
	
def mass_album_track_table_delete_path_not_existed(del_path_crc32L,mode,*args):
	#del_path_crc32L-album_item->(path_crc32,path,id_album)
	#res = myMediaLib_tools.check_medialib_utf8_issue(Obj['folder_list'],[])
	#ss = myMediaLib_tools.mass_album_table_update_path_crc32_ajust(res['matchL'])
	#>>> f = open(resDBS['resBuf_save'],'r')
	#>>> r = pickle.load(f)
	#>>> f.close()
	#>>> r.keys()
	
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)
	requestD = {}
	if mode.lower() == 'album':
		requestD['album'] = {'cursor':db.cursor(),'req':''}
		requestD['album_cat_rel'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_album_ref'] = {'cursor':db.cursor(),'req':''}
		requestD['album_reference'] = {'cursor':db.cursor(),'req':''}
		requestD['album_reference_2'] = {'cursor':db.cursor(),'req':''}
		requestD['track'] = {'cursor':db.cursor(),'req':''}
	elif mode.lower() == 'artist':	
		requestD['artist'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_album_ref'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_cat_rel'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_reference'] = {'cursor':db.cursor(),'req':''}
		requestD['artist_reference_2'] = {'cursor':db.cursor(),'req':''}
		requestD['track'] = {'cursor':db.cursor(),'req':''}
		
	elif mode.lower() == 'track':
		requestD['track'] = {'cursor':db.cursor(),'req':''}
		requestD['track_tag'] = {'cursor':db.cursor(),'req':''}
		
	i=0
	resL=[]
	reqL = []
	res = ''
	for a in del_path_crc32L:
		# delete from ALBUM
		if mode.lower() == 'album':	
			requestD['album']['req'] = """delete from album where id_album = %s"""%(a[2])
			
			# delete from album_cat_rel
			requestD['album_cat_rel']['req'] = """delete from album_cat_rel where id_album = %s"""%(a[2])
			
			# delete from artist_album_ref
			requestD['artist_album_ref']['req'] = """delete from artist_album_ref  where id_album = %s"""%(a[2])
			#reqL.append(req)
			
			# delete from  ALBUM_REFERENCE
			requestD['album_reference']['req'] = """delete from  ALBUM_REFERENCE where id_album = %s"""%(a[2])
			
			requestD['album_reference_2']['req'] = """delete from ALBUM_REFERENCE  where id_album_ref = %s"""%(a[2])
			#reqL.append(req)
			
			requestD['track']['req'] = """delete from track where album_crc32 = %s"""%(a[0])
			
			
			#reqL.append(req)
		elif mode.lower() == 'artist':	
			requestD['artist']['req'] = """delete from artist where id_artist = %s"""%(a[0])
			
			requestD['artist_cat_rel']['req'] = """delete from artist_cat_rel where id_artist = %s"""%(a[0])
			
			# delete from artist_album_ref
			requestD['artist_album_ref']['req'] = """delete from artist_album_ref  where id_artist = %s"""%(a[0])
			#reqL.append(req)
			
			# delete from  ARTIST_REFERENCE
			requestD['artist_reference']['req'] = """delete from  ARTIST_REFERENCE where artist_crc32 = %s"""%(a[2])
			
			requestD['artist_reference_2']['req'] = """delete from ARTIST_REFERENCE  where ref_artist_crc32 = %s"""%(a[2])
			#reqL.append(req)
			
			requestD['track']['req'] = """delete from track where artist_crc32 = %s"""%(a[2])
			
			#reqL.append(req)
		elif mode.lower() == 'track':
			
			requestD['track']['req'] = """delete from track where id_track = %s"""%(a[1])
			requestD['track_tag']['req'] = """delete from track_tag where id_track = %s"""%(a[1])
			
		
		for tabl_key in requestD:
			try:
				requestD[tabl_key]['cursor'].execute(requestD[tabl_key]['req'])
				if "res_log" in args:
					resL.append((requestD[tabl_key]['cursor'].rowcount,a,requestD[tabl_key]['req']))
					
				#res = c.fetchall()
			except Exception as e:
				print(e)
				print(requestD[tabl_key]['req'])
				logger.critical('Exception: %s'%(str(e)))
				return res
				
		#res = c.fetchall()
		#resL.append(res)	
				
		if i%10 == 0:
			print(i, end=' ')
			
		i+=1
	for tabl_key in requestD:
		requestD[tabl_key]['cursor'].close()
	
	db.commit()
	db.close()	
	return resL	
	
def unicode_migration_scenario():
	cfgD = readConfigData(mymedialib_cfg)
	resBuf_ml_folder_tree_buf_path = cfgD['ml_folder_tree_buf_path']
	f = open(resBuf_ml_folder_tree_buf_path,'r')
	#Obj = pickle.load(f)
	f.close()
	
	t = time.time()
	check_res_before_migrationD = quick_check_medialib_utf8_issue('with_fetch_detailes')
	print()
	print('*'*50)
	print('Unicode issues ALBUM check')
	print('*'*50)
	
	#res_check_album = check_medialib_ALBUM_utf8_issue(Obj['folder_list'],[],'no_utf8','fast_convL_processing')
	res_check_album = check_medialib_ALBUM_utf8_issue([],[],'no_utf8','fast_convL_processing')
	print('*'*50)
	if res_check_album['er_tb_deleteL'] == []:
		print('Nothing to delete from album')
	else:	
		print('Unicode issues ALBUM not existed delete')
		res_del_albumD   = mass_album_track_table_delete_path_not_existed(res_check_album['er_tb_deleteL'],'album')
		
	print()	
	print('*'*50)	
	if res_check_album['matchL'] == []:	
		print('Nothing to ajust from album')
	else:	
		print('Unicode issues ALBUM ajusting')
		res_ajustD = mass_album_track_artist_table_update_path_crc32_ajust(res_check_album['matchL'],'album')	
	
	# check TRACK
	print('*'*50)
	print('Unicode issues TRACK check')
	print('*'*50)
	res_check_track = check_medialib_TRACK_utf8_issue([],[],'no_utf8','fast_convL_processing')
	print('*'*50)
	if res_check_track['er_tb_deleteL'] == []:
		print('Nothing to delete from track')
	else:	
		print('Unicode issues TRACK not existed delete')
		res_delD = mass_album_track_table_delete_path_not_existed(res_check_track['er_tb_deleteL'],'track')
		
	print()	
	print('*'*50)
	if res_check_track['matchL'] == []:
		print('Nothing to ajust from album')
	else:	
		print('Unicode issues TRACK ajusting')
		res_ajustD = mass_album_track_artist_table_update_path_crc32_ajust(res_check_track['matchL'],'track')	
		
	print('*'*50)	
	print("Ajusting scenario finished in %i sec"%(int(time.time()-t)))
	check_after_migrationD = quick_check_medialib_utf8_issue('with_fetch_detailes')
	

def update_album_track_path(path_conv_func,*args):
	# Фунция для разового вызова изменений path в таблицах ALBUM и TRACK
	# послее ее запуска необходимо пересчитать CRC32 всех объектов через mass_album_track_artist_table_update_path_crc32_ajust
	# tobe_removed_substr = "G:\\MUSIC\\"
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)
	if "album" in args:
		mode_dif = 100
		i = 0
		l = db_request_wrapper(db,"select id_album, path from album")

		for a in l:
			path_converted = path_conv_func(a[1])
			print(a[1],path_converted)
			if not path_converted:
				if i%mode_dif == 0:
					print("-", end=' ')
				i+=1
				continue
			rec = (path_converted,a[0])
			req = """update album set path = "%s" where id_album = %s"""%rec
			if 'modi' in args:
				db_request_wrapper(db,req,'modi')
		
			if i%mode_dif == 0:
				print(i, end=' ')
			i+=1
		print("Album path is updated")
		
	if "track" in args:
		mode_dif = 1000
		l = db_request_wrapper(db,"select id_track, path, cue_fname from track where path not like '%http%'")
		i = 0
		for a in l:
			if a[2]:
				if '.cue' in a[2].lower():
					path_converted = path_conv_func(a[1])
					path_converted_cue_fname = path_conv_func(a[2])
					if not path_converted  and  not path_converted_cue_fname:
						if i%mode_dif == 0:
							print("-", end=' ')
							i+=1
							continue
					if i%mode_dif == 0:
						print("*", end=' ')
					rec = (path_converted, path_converted_cue_fname,a[0])
					req = """update track set path = "%s", cue_fname = "%s" where id_track = %s"""%rec
					if 'modi' in args:
						db_request_wrapper(db,req,'modi')
			else:
				path_converted = path_conv_func(a[1])
				if not path_converted:
					if i%mode_dif == 0:
						print("-", end=' ')
						i+=1
						continue

				rec = (path_converted,a[0])
				req = """update track set path = "%s" where id_track = %s"""%rec
				if 'modi' in args:
					db_request_wrapper(db,req,'modi')
			if i%mode_dif == 0:
				print(i, end=' ')
			i+=1
		print("track path is updated")
	db.close()
	
def get_not_exists_album_pathL(music_path_root,mode):
	# music_path_root = "\\\\GOFLEX_HOME\\внешняя память\\Seagate\\Music\\"
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	
	mode_dif = 1000
	not_existsL = []
	errorL = []
	t_all_start = time.time()
	if mode.lower() == 'album':
		req = "select id_album, path, path_crc32 from ALBUM where album_type <> 'RADIO'"
	elif mode.lower() == 'track':	
		req = "select id_track, path, path_crc32,  cue_fname,title,artist,cue_num from TRACK where path not like '%http%'"
	db = sqlite3.connect(dbPath)
	resL = db_request_wrapper(db,req)
	db.close()
	i = 0
	for a in resL:
		try:
			if not Path(music_path_root+a[1]).exists():
				not_existsL.append((a[2],a[1],a[0]))
		except Exception as e:
			errorL.append((a,resL.index(a),e))
		if i%mode_dif == 0:
			print(i, '[',len(not_existsL),']', end=' ')
		i+=1
		
	print('track finished in:',int(time.time()-t_all_start))
	return {"not_existsL":not_existsL,"errorL":errorL}
	
def relative_path_migration_scenario(music_path_root):
	# music_path_root = "\\\\GOFLEX_HOME\\внешняя память\\Seagate\\Music\\"
	#matchL[{'new_crc32':crc32_1,'old_crc32':b[0],'new_path':db_fs_folder_path,'id_album': b[2]},]
	match_albumL = []
	match_trackL = []
	res_ajust_albumD = res_ajust_trackD = {}
	
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	
	mode_dif = 1000
	not_existsL = []
	errorL = []
	t_all_start = time.time()
	db = sqlite3.connect(dbPath)
	req = "select id_album, path, path_crc32 from ALBUM where album_type <> 'RADIO'"
	res_albumL = db_request_wrapper(db,req)
	
	print("1. Calculating new album crc32 list")
	i = 0
	
	for a in res_albumL:
		#ниже формула расчета CRC32 для альбома
		crc32_1 = zlib.crc32(a[1].encode(BASE_ENCODING))
		rec = {'new_crc32':crc32_1,'old_crc32':a[2],'id_album': a[0]}

		match_albumL.append(rec)
		if i%mode_dif == 0:
			print(i, end=' ')
		i+=1
	print()
	print("2. Updating album crc32 DB")
	res_ajust_albumD = mass_album_track_artist_table_update_path_crc32_ajust(match_albumL,"album_crc32")
		
	print('Album finished in:',int(time.time()-t_all_start))
		
	#	return {"match_trackL":match_trackL,"match_albumL":match_albumL,'res_ajust_albumD':res_ajust_albumD}
	print()
	print("2. Calculating new track crc32 list")
	t_all_start = time.time()
	
	req = "select id_track, path, path_crc32, cue_num from TRACK where path not like '%http%'"
	res_trackL = db_request_wrapper(db,req)
	db.close()
	
	mode_dif = 10000
	i = 0
	cue_cnt = 0
	for a in res_trackL:
		if a[3]:
			#ниже формула расчета CRC32 для трэка с CUE
			crc32_1 = zlib.crc32((a[1]+str(a[3])).encode(BASE_ENCODING))
			cue_cnt+=1
		else:
			#ниже формула расчета CRC32 для просто трэка в формате ape,flac,mp3
			crc32_1 = zlib.crc32(a[1].encode(BASE_ENCODING))
			
		rec = {'new_crc32':crc32_1,'old_crc32':a[2],'id_track': a[0]}
		
		match_trackL.append(rec)
		if i%mode_dif == 0:
			print(i, '[',cue_cnt,']', end=' ')
		i+=1
	
	print()
	print("2. Updating track crc32 DB")
	res_ajust_trackD = mass_album_track_artist_table_update_path_crc32_ajust(match_trackL,"track_crc32")	
	
	print('track finished in:',int(time.time()-t_all_start))
	return {"match_trackL":match_trackL,"match_albumL":match_albumL,'res_ajust_albumD':res_ajust_albumD,'res_ajust_trackD':res_ajust_trackD}
	
def remove_not_exists_objects_from_DB(music_path_root):
	# сценарий удаление объектов с путями к несуществующим медиа объектам. идем от альбомов и всех связанных с ними объектов, затем по трэкам
	# часть трэков удаляется по связи с альбомами, остальная напрямую в таблице трэка.
	# music_path_root = "\\\\GOFLEX_HOME\\внешняя память\\Seagate\\Music\\"
	track_substL = []
	print("1. Remooving from album and related tables")
	print()
	print("1.1 Colleacting from albums")
	r_not_exists_albumD = get_not_exists_album_pathL(music_path_root,'album')
	print("1.2 Remooving from albums, expected:%s"%str(len(r_not_exists_albumD['not_existsL'])))
	r_albumL = mass_album_track_table_delete_path_not_existed(r_not_exists_albumD['not_existsL'],'album',"res_log")
	
	print()
	print("Not deleted from track referencing from album: %s"%(str(len([a for a in r_albumL if 'delete from track ' in a[2] and a[0] == 0]))))
	print()
	print("2. Remooving from track and related tables")
	
	
	
	print()
	print("2.1 Colleacting trom tracks")
	r_not_existsD = get_not_exists_album_pathL(music_path_root,'track')
	
	print()
	print("2.2 Remooving from tracks, expected:%s"%str(len(r_not_existsD['not_existsL'])))
	for a in r_not_existsD['not_existsL']:
		track_substL.append((a[0],a[2]))
	r_trackL = mass_album_track_table_delete_path_not_existed(track_substL,'track',"res_log")
	
	return {"r_not_exists_albumD":r_not_exists_albumD,"r_not_existsD":r_not_existsD,'r_albumL':r_albumL,'r_trackL':r_trackL} 
	
