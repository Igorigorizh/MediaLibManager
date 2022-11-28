# -*- coding: utf-8 -*-
import os
from posixpath import join, dirname
from os import scandir
import pickle
import acoustid
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

import discid

import musicbrainzngs
import time
import logging
from pathlib import Path

from medialib.myMediaLib_init import readConfigData

from medialib.myMediaLib_cue import simple_parseCue
from medialib.myMediaLib_cue import parseCue
from medialib.myMediaLib_cue import GetTrackInfoVia_ext
from medialib.myMediaLib_cue import detect_cue_scenario

from medialib.myMediaLib_fs_util import Media_FileSystem_Helper as mfsh
find_new_music_folder = mfsh().find_new_music_folder
find_new_music_folder_simple = mfsh().find_new_music_folder_simple

from medialib import BASE_ENCODING
from medialib import mymedialib_cfg
from medialib import medialib_fp_cfg


from functools import wraps

import warnings
from configparser import ConfigParser

cfgD = readConfigData(mymedialib_cfg)

cfg_fp = ConfigParser()
cfg_fp.read(medialib_fp_cfg)

logger = logging.getLogger('controller_logger.tools')

musicbrainzngs.set_useragent("python-discid-example", "0.1", "your@mail")


posix_nice_value = int(cfg_fp['FP_PROCESS']['posix_nice_value'])

def get_FP_and_discID_for_album(self, album_path,fp_min_duration,cpu_reduce_num,*args):
	hi_res = False
	scenarioD = detect_cue_scenario(album_path,*args)
	print('Self:',type(self))

	TOC_dataD = get_TOC_from_log(album_path)
	
	guess_TOC_dataD = {}
	if TOC_dataD['TOC_dataL']:
		print("Log TOC is here!:", TOC_dataD['toc_string'])
	else:
		print("No Log TOC detected")
	cueD = {}	
	paramsL = []	
	result = b''
	convDL = []
	prog = b''
	MB_discID_result = ''		
	API_KEY = 'cSpUJKpD'
	meta = ["recordings","recordingids","releases","releaseids","releasegroups","releasegroupids", "tracks", "compress", "usermeta", "sources"]	
	discID = log_discID = ''
	if os.name == 'nt':
		prog = b'ffmpeg.exe'
	elif os.name == 'posix':
		prog = b'ffmpeg'
	t_all_start = time.time()
	failed_fpL=[]
	if 0 <= cpu_reduce_num < cpu_count():
		cpu_num = cpu_count()-cpu_reduce_num
	else:
		cpu_reduce_num = 1
		print("Wrong CPU reduce provided, changed to ",cpu_reduce_num)
		cpu_num = cpu_count()-cpu_reduce_num
	#redis_state_notifier('medialib-job-fp-albums-total-progress','progress')
	#redis_state_notifier('medialib-job-fp-album-progress','init')
	
	if scenarioD['cue_state']['single_image_CUE']:
		print("\n\n-------FP generation for CUE scenario:  single_image_CUE-----------")
		try:
			print("Full cue parsing")
			cueD = parseCue(scenarioD['cueD']['cue_file_name'],'with_bitrate')
		except Exception as e:
				print(e)
				return {'RC':-1,'cueD':cueD}	
		if 'multy' in args and ('FP' in  args or 'split_only_keep' in args):
			print('--MULTY processing of FP --- on [%i] CPU Threads'%(cpu_num))
			image_name = cueD['orig_file_pathL'][0]['orig_file_path']
			
			command_ffmpeg = b'ffmpeg -y -i "%b" -t %.3f -ss %.3f "%b"'
			
			# Get 4 iterators for image name,  total_sec, start_sec, temp_file_name
			iter_image_name_1 = iter(image_name for i in range(len(cueD['trackD'])))
			iter_params = iter(args for i in range(len(cueD['trackD'])))
			iter_dest_tmp_name_4 = iter(join(album_path,b'temp%i.wav'%(num))  for num in cueD['trackD'])
			#iter_dest_tmp_name_4 = iter(b'temp%i.wav'%(num)  for num in cueD['trackD'])
			iter_dest_tmp_name_4, iter_dest_tmp_name = tee(iter_dest_tmp_name_4)
			iter_start_sec_3 = iter(cueD['trackD'][num]['start_in_sec']  for num in cueD['trackD'])
			if fp_min_duration > 10:
				iter_total_sec_2 = iter(fp_time_cut(cueD['trackD'][num]['total_in_sec'],fp_min_duration)	for num in cueD['trackD'])
				iter_total_sec_orig = iter(float('%.1f'%cueD['trackD'][num]['total_in_sec'])  for num in cueD['trackD'])
				# get iterator for ffmpeg command
				iter_command_ffmpeg = map(lambda x: command_ffmpeg%x,zip(iter_image_name_1,iter_total_sec_2,iter_start_sec_3,iter_dest_tmp_name_4))
			else:
				iter_total_sec_2 = iter(cueD['trackD'][num]['total_in_sec']  for num in cueD['trackD'])
				# get iterator for ffmpeg command
				iter_command_ffmpeg = map(lambda x: command_ffmpeg%x,zip(iter_image_name_1,iter_total_sec_2,iter_start_sec_3,iter_dest_tmp_name_4 ))
			
			
			res = ''
			if self:
				#progress_recorder = ProgressRecorder(self)
				progress_recorder_descr = 'medialib-job-folder-FP-album:'+str(album_path)
				#progress_recorder.set_progress(0, len(cueD['trackD']), description=progress_recorder_descr)

			start_t = time.time()
			try:
				with Pool(cpu_num) as p:
					res = p.starmap_async(worker_ffmpeg_and_fingerprint, zip(iter_command_ffmpeg,iter_dest_tmp_name,iter_params,)).get()
			except Exception as e:
				print("Caught exception in map_async 1",str(e))
				return {'RC':-1,'cueD':cueD}
				#p.terminate()
			#	p.join()
			p.join()	
			print('\n -----  album splite FP calc processing finished in [%i]sec'%(time.time()-start_t))
			try:
				if fp_min_duration > 10:
					convDL_iter = zip(iter_total_sec_orig, res)
					#a[1]:(fp,f_name,failed_fpL)
					convDL = [{'fname':a[1][1],'fp':(a[0],a[1][0][1])} for a in convDL_iter]
				else:
					convDL = [{'fname':a[1],'fp':a[0]} for a in res]
					
				failed_fpL = [a[2] for a in res if a[2] != []]
			except Exception as e:
				print('Error ar async get:',str(e))
				convDL = []
				failed_fpL = []
				
			
		else:
			cnt=1
			image_name = cueD['orig_file_pathL'][0]['orig_file_path']
			for num in cueD['trackD']:
				new_name = b'temp%i.wav'%(cnt)
				start_sec = int(cueD['trackD'][num]['start_in_sec'])
				total_sec = int(cueD['trackD'][num]['total_in_sec'])
				if 'FP' in  args:
					print("Track extact from from:",image_name,start_sec, total_sec)	
					ffmpeg_command = str(b'ffmpeg -y -i "%b" -aframes %i -ss %i "%b"'% (image_name,total_sec,start_sec,join(album_path,new_name)),BASE_ENCODING)
						
					#b"\""+join(album_path,new_name)+b"\"")
						
					
					print (ffmpeg_command)
					
					if prog != '' and ffmpeg_command != ():	
						try:
							print("Decompressing partly with:",prog)
							res = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE ,stdout=subprocess.PIPE,shell=True)
							out, err = res.communicate()
						except OSError as e:
							print('get_FP_and_discID_for_cue 232:', e, "-->",prog,ffmpeg_command)
							return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':num,'errorL':['Error at decocmpression of [%i]'%(int(num))] }
						except Exception as e:
							print('Error in get_FP_and_discID_for_cue 235:', e, "-->", prog,ffmpeg_command)
							return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':num,'errorL':['Error at decocmpression of [%i]'%(int(num))]}	
					else:
						print('Error in get_FP_and_discID_for_cue 243:', e, "-->", prog,cueD['orig_file_pathL'][0]['orig_file_path'])
						return{'RC':-1,'cueD':cueD,'TOC_dataD':TOC_dataD,'scenarioD':scenarioD}		
					fp = []
					try:
						
						fp = acoustid.fingerprint_file(str(join(album_path,new_name),BASE_ENCODING))
					except  Exception as e:
						print("Error in fp gen with:",new_name,e)
						
						os.rename(join(album_path,new_name),join(album_path,bytes(str(time.time())+'_failed_','utf-8')+new_name))
						failed_fpL.append((new_name,e))
						cnt+=1
						continue
						#result = result + str(a,BASE_ENCODING) + str(fp)+"\n"
					#result = result + a + bytes(str(fp),BASE_ENCODING)+b'\n'
					
					convDL.append({"fname":new_name,"fp":fp})
					print("*", end=' ')
				
					os.remove(join(album_path,new_name))
					cnt+=1
					
					
					if self:
						#progress_recorder = ProgressRecorder(self)
						progress_recorder_descr = 'medialib-job-folder-FP-album:'+str(album_path)
						#progress_recorder.set_progress(0, len(cueD['trackD']), description=progress_recorder_descr)
	elif scenarioD['cue_state']['multy_tracs_CUE']:
		print("\n\n FP generation for CUE scenario:  multy_tracs_CUE")
		try:
			print("Full cue parsing")
			cueD = parseCue(scenarioD['cueD']['cue_file_name'],'with_bitrate')
		except Exception as e:
				print(e)
				return {'RC':-1,'cueD':cueD}	
		cnt=1
		
		if 'multy' in args and 'FP' in  args:
			#print('--MULTY---:',list(map(lambda x: str(join(album_path,x),BASE_ENCODING),scenarioD['normal_trackL'])))
			
			print('--MULTY processing of FP --- on [%i] CPU Threads'%(cpu_num))
			
			
			try:
				with Pool(cpu_num) as p:
					res = p.map_async(worker_fingerprint, [a['orig_file_path'] for a in cueD['orig_file_pathL']]).get()
					
			except Exception as e:
				print("Caught exception in map_async 2",e)
				return {'RC':-1,'cueD':cueD}	
			#	p.join()
			p.join()	
			#print(res)
			#return res
			try:	
				convDL = [{'fname':a[1],'fp':a[0]} for a in res]
			except Exception as e:
				print('Error:',str(e))	
		else:
			for track_item in cueD['orig_file_pathL']:
				track = track_item['orig_file_path']
				if 'FP' in  args:
					fp = []
					try:
						fp = acoustid.fingerprint_file(track)
					except  Exception as e:
						print("Error in fp gen with:",track)
						continue
						#result = result + str(a,BASE_ENCODING) + str(fp)+"\n"
					#result = result + a + bytes(str(fp),BASE_ENCODING)+b'\n'
					
					convDL.append({"fname":os.path.basename(track),"fp":fp})
					print("*", end=' ')
		
		
	elif scenarioD['cue_state']['only_tracks_wo_CUE']:
		print("\n\n FP generation for scenario only_tracks_wo_CUE")	
		scenarioD['normal_trackL'].sort()
		trackL = []
		for a in scenarioD['normal_trackL']:
			trackL.append(str(album_path,BASE_ENCODING)+str(a,BASE_ENCODING))
		
		try:	
			guess_TOC_dataD = guess_TOC_from_tracks_list(trackL)
		except Exception as e:
			print('Error in guess_TOC_from_tracks_list:',e)	
		
		sample_rate = guess_TOC_dataD['trackDL'][0]['sample_rate']
		if sample_rate > 44100:
			print('------------HI-RES check scenario details------------')
			hi_res = True	
		
		if 'multy' in args and 'FP' in  args:
			#print('--MULTY---:',list(map(lambda x: str(join(album_path,x),BASE_ENCODING),scenarioD['normal_trackL'])))
			print('--MULTY processing of FP --- on [%i] CPU Threads'%(cpu_num))
			
			
			try:
				with Pool(cpu_num) as p:
					res = p.map_async(worker_fingerprint, list(map(lambda x: str(join(album_path,x),BASE_ENCODING),scenarioD['normal_trackL']))).get()
					
			except Exception as e:
				print("Caught exception in map_async 3",e)
				return {'RC':-2,'normal_trackL':scenarioD['normal_trackL']}
				#p.terminate()
			#	p.join()
			p.join()	
			try:	
				convDL = [{'fname':a[1],'fp':a[0]} for a in res]
			except Exception as e:
				print('Error:',str(e))	
				
				
			if self:
				#progress_recorder = ProgressRecorder(self)
				progress_recorder_descr = 'medialib-job-folder-FP-album:'+str(album_path)
				#progress_recorder.set_progress(0, len(trackL), description=progress_recorder_descr)	
		else:
			for track in  scenarioD['normal_trackL']:
				fp = []
				if 'FP' in  args:	
					try:
						fp = acoustid.fingerprint_file(str(join(album_path,track),BASE_ENCODING))
					except  Exception as e:
						print("Error in fp gen with:",track)
						continue
							#result = result + str(a,BASE_ENCODING) + str(fp)+"\n"
						#result = result + a + bytes(str(fp),BASE_ENCODING)+b'\n'
					
					convDL.append({"fname":track,"fp":fp})
					print("*", end=' ')
					
					if self:
						#progress_recorder = ProgressRecorder(self)
						progress_recorder_descr = 'medialib-job-folder-FP-album:'+str(album_path)
						#progress_recorder.set_progress(0, len(cueD['trackD']), description=progress_recorder_descr)
		
			
	time_stop_diff = time.time()-t_all_start	
	if 'FP' in  args: 
		print("\n********** Album FP takes:%i sec.***********************"%(int(time_stop_diff)))
		
	#redis_state_notifier('medialib-job-fp-album-progress','progress-stop')
	
				
	time_ACOUSTID_FP_REQ = time.time()
	if 'ACOUSTID_FP_REQ' in args and 'LOCAL' in args:
		print("\n Getting Album ACOUSTID_FP_REQ from https://acoustid.org/ **********************")
		err_cnt = 0
		scoreL = []
		for fp_item in convDL: 	
			response=asyncio.run(acoustID_lookup_wrapper_parent(fp_item['fp']))
			#response = acoustid.lookup(API_KEY, fp_item['fp'][1], fp_item['fp'][0],meta)
			if 'error' in response:
				err_cnt+=1
			else:
				if 'results' in response:
					l = [item['score'] for item in response['results']  if 'score' in item]
					if l != []:
						scoreL.append(max(l))
			if response == {'results': [], 'status': 'ok'}:
				duration_init = fp_item['fp'][0]
				fp_item['fp'] = list(fp_item['fp'])
				print('\n Empty FP response. duration [%s], trying to guess duration'%str(duration_init))
				for i in range(1,10):
					fp_item['fp'][0] = fp_item['fp'][0] - i
					response=asyncio.run(acoustID_lookup_wrapper_parent(fp_item['fp']))
					if response != {'results': [], 'status': 'ok'}:
						if 'results' in response:
							print('Succeceed with duration:',fp_item['fp'][0])
							l = [item['score'] for item in response['results']  if 'score' in item]
							if l != []:
								scoreL.append(max(l))
						
							break
				if response == {'results': [], 'status': 'ok'}:		
					fp_item['fp'][0] = duration_init
					
			fp_item['response'] = response
			
		if err_cnt > 0 and err_cnt < len(convDL):
			print('Errors %i in responses from %i'%(err_cnt,len(convDL)))
			for fp_item in convDL: 	
				if 'error' in fp_item['response']:
					response=asyncio.run(acoustID_lookup_wrapper_parent(fp_item['fp']))
					if 'error' not in  response:
						fp_item['response'] = response
						print('No more error in response %i'%(convDL.index(fp_item)))
						if 'results' in response:
							l = [item['score'] for item in response['results']  if 'score' in item]
							if l != []:
								scoreL.append(max(l))
					else:
						print('Error 2-nd time in response %i'%(convDL.index(fp_item)))
		if 	convDL:			
			if len(scoreL) == len(convDL):
				print('FP score rate:',sum(scoreL)/len(convDL))
			elif len(scoreL) < len(convDL) and len(scoreL) > 0:
				print('FP score rate with skipped FP:',sum(scoreL)/len(scoreL),'%i of %i'%(len(scoreL),len(convDL)))
			else:	
				print('Wrong FP scoreL:',scoreL)
		else:
			print("Error: convDL is empty")
			
	
		print("********** Album ACOUSTID_FP_REQ request takes:%i sec.***********************"%(int(time.time() - time_ACOUSTID_FP_REQ )))		
	
	# Выделеить в отдельную функцию
	TOC_src = ''
	
	time_discid_MB_REQ = time.time()
	if scenarioD['cue_state']['only_tracks_wo_CUE']:
		print("Try guess TOC from tracks list")	
		try:
			discID = discid.put(guess_TOC_dataD['discidInput']['First_Track'],guess_TOC_dataD['discidInput']['Last_Track'],guess_TOC_dataD['discidInput']['total_lead_off'],guess_TOC_dataD['discidInput']['offsetL'])
			print('Guess Toc:',discID.toc_string)
			TOC_src = 'guess'
			print("discId from guess - is OK")	
		except Exception as e:
			print("Issue with Guess TOC")
			print(e)
	else:
		print("Try TOC from CUE")	
		try:
			discID = discid.put(1,cueD['cue_tracks_number'],cueD['lead_out_track_offset'],cueD['offsetL'])
			print('Cue TOC:',discID.toc_string)
		except Exception as e:
			if 'offsetL' not in cueD: 
				print('offsetL is missing in cueD')
			else:	
				print("Issue with CUE TOC len(offsetL)",len(cueD['offsetL']))
			print(e)
	
	if TOC_dataD['discidInput'] and discID:
		if TOC_dataD['toc_string'] == discID.toc_string:
			TOC_src = 'cue'
			print("TOCs log and cue are identical")
		else:
			print("TOCs log and cue are NOT identical")
			print((TOC_dataD['toc_string']))
			TOC_src = 'log'
			print((discID.toc_string))	
		
	if TOC_dataD['discidInput']:
		print("Try TOC from log")
		try:
			log_discID = discid.put(TOC_dataD['discidInput']['First_Track'],TOC_dataD['discidInput']['Last_Track'],TOC_dataD['discidInput']['total_lead_off'],TOC_dataD['discidInput']['offsetL'])
			print('Log Toc:',log_discID.toc_string)
			print("discId from log is taken for MB request")	
		except Exception as e:
			print("Issue with Log TOC")
			print(e)
			
	if log_discID:
		discID = log_discID

	if 'MB_DISCID_REQ' in args:	
		if discID:
			
			try:
				MB_discID_result = musicbrainzngs.get_releases_by_discid(discID,includes=["artists","recordings","release-groups"])
			except Exception as e:
				print(e)
			if 'disc' in MB_discID_result:	
				print("DiskID MB - OK", MB_discID_result['disc']['id'],TOC_src) 	
				MB_discID_result['TOC_src'] = TOC_src
			else:
				print("DiskID MB - NOT detected") 	
				
			print("********** Album MB_DISCID_REQ MusicBrainz request takes:%i sec.***********************"%(int(time.time() - time_discid_MB_REQ )))		
	
	print("********** Album process in total takes:%i sec.***********************"%(int(time.time() - t_all_start )))
	
	return{'RC':len(convDL),'cueD':cueD,'TOC_dataD':TOC_dataD,'scenarioD':scenarioD,'MB_discID':MB_discID_result,'convDL':convDL,'discID':str(discID),'failed_fpL':failed_fpL,'guess_TOC_dataD':guess_TOC_dataD,'hi_res':hi_res,'album_path':album_path,'TOC_src':TOC_src}
def fp_time_cut(x,cut_sec):
	if x > cut_sec:
		return cut_sec
	else:
		return x

def worker_ffmpeg_and_fingerprint(ffmpeg_command, new_name, *args):
	#command template b'ffmpeg -y -i "%b" -aframes %i -ss %i "%b"'( new_name )
	failed_fpL = []
	#print('in worker')				
	f_name = os.path.basename(new_name)			
	#print (ffmpeg_command)
	prog = 'ffmpeg'				
	
	#redis_state_notifier(state_name='medialib-job-fp-album-progress',action='progress')
	#print("Worker before ffmmeg pid:",os.getpid())
	if os.name == 'posix':
		try:
			nice_value = os.nice(posix_nice_value)	
		except Exception as e:
			print('Error in nice:',e)
	
	try:
		#print("Decompressing partly with:",prog)
		res = subprocess.Popen(ffmpeg_command.decode(), stderr=subprocess.PIPE ,stdout=subprocess.PIPE,shell=True)
		out, err = res.communicate()
	except OSError as e:
		print('get_FP_and_discID_for_cue 232:', e, "-->",prog,ffmpeg_command)
		return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':num,'errorL':['Error at decompression of [%i]'%(int(num))] }
	except Exception as e:
		print('Error in get_FP_and_discID_for_cue 235:', e, "-->", prog,ffmpeg_command)
		return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':num,'errorL':['Error at decompression of [%i]'%(int(num))]}
	
	fp = []
	#print("+", end=' ')
	
	if len(args)>0:
		if 'split_only_keep' in args[0]:
			return (fp,f_name,failed_fpL)	
	
	try:
		
		fp = acoustid.fingerprint_file(str(new_name,BASE_ENCODING))
	except  Exception as e:
		print("Error in fp gen with:",new_name,e)
		print('ffmpeg command:',ffmpeg_command)
		f_name = os.path.basename(new_name)
		os.rename(new_name,new_name.replace(f_name,bytes(str(time.time()).replace('.','_'),BASE_ENCODING)+f_name))
		failed_fpL.append((new_name,e))

	#print("*", end=' ')
		
	os.remove(new_name)	
	
	return (fp,f_name,failed_fpL)
	
def worker_fingerprint(file_path):
	print("Worker acoustid.fingerprint pid:",os.getpid())
	#redis_state_notifier(state_name='medialib-job-fp-album-progress',action='progress')
	
	if os.name == 'posix':
		try:
			nice_value = os.nice(posix_nice_value)	
		except Exception as e:
			print('Error in nice:',e)
		
	try:
		fp = acoustid.fingerprint_file(file_path)
	except  Exception as e:
		print("Error [%s] in fp gen with:"%(str(e)),file_path)
		return ((),os.path.split(file_path)[-1])
	#print(fp[0],os.path.split(file_path)[-1])	

	return (fp,os.path.split(file_path)[-1])	
	

def do_mass_album_FP_and_AccId(folder_node_path,min_duration,prev_fpDL,prev_music_folderL,*args):	
	# Генерация FP и AccuesticIDs по альбомам из указанной дирректории (folder_node_path), для загрузок двойных альбомов и других массовых загрузок
	
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
		dirL = find_new_music_folder([folder_node_path],[],[],'initial')
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
	print(tmp_music_folderL)
	

	mode_dif = 30
	t_all_start = time.time()
	process_time = 	0

	for album_path in tmp_music_folderL:
		fpRD = {}
		
		print(cnt, ' of:',len(music_folderL),'--> Album folder:', [album_path])
		t_start = time.time()
		try:
			cnt+=1
			process_time = 0
			fpRD = get_FP_and_discID_for_album(album_path,min_duration,*args)
			process_time = 	int(time.time()-t_start)
			fpRD['album_path']=album_path
			fpRD['process_time'] = process_time
			fpDL.append(fpRD)	
			print('album finished in:',	process_time, "time since starting the job:",int(time.time()-t_all_start))
			print('\n-------------------   Validation ------------------')
			validatedD = album_FP_discid_response_validate([fpRD])
			print()
		except Exception as e:	
			print("Exception with FP generation [%s]: \n in %s"%(str(e),str(album_path)))	
			fpRD = {'RC':-3,'error_logL':["Exception with FP generation [%s]:  [%s]"%(str(e),str(album_path))],'album_path':album_path,'process_time': process_time}
			fpDL.append(fpRD)	

			
		if cnt%mode_dif == 0:
			if dump_path:
				try:
					os.remove(dump_path)
				except Exception as e:
					print('Last dump not deleted:',str(e))
					
			fname=b'fpgen_%i.dump'%int(time.time())
			dump_path = album_path+fname
			d = ''
			try:	
				with open(dump_path, 'wb') as f:
					d = pickle.dump({'fpDL':fpDL,'music_folderL':music_folderL,'dump_path':dump_path},f)
			except Exception as e:
				print('Error in pickle',e)
			print('Saved temp dump in:',fname)	
	

	d = ''
	fname=b'fpgen_%i.dump'%int(time.time())
	dump_path = folder_node_path+fname
	try:	
		with open(folder_node_path+fname, 'wb') as f:
			d = pickle.dump( {'fpDL':fpDL,'music_folderL':music_folderL,'dump_path':dump_path},f)
	except Exception as e:
		print('Error in pickle',e)
	
	time_stop_diff = time.time()-t_all_start
	print('\n\n\n')
	print("*********************************************************************")
	print("**********Generation Summary for %i albums. All takes:%i sec.***********************"%(len(fpDL),int(time_stop_diff)))
	print("*********************************************************************\n")
	for a in fpDL:
		if 'RC' not in a: a['RC'] = -3
		if 'error_logL' not in a: a['error_logL'] = []
		
		if a['RC'] < 0:
			print("RC=(",a['RC'],")",a['album_path'],'IN TIME:',a['process_time'])
			print('*****************************')
			for b in a['error_logL']:
				print(b)
			print('*****************************')
			print()

			
	print('Some statistics:')
	if fpDL:
		print("Collected: albums number %i, time pro album %i sec."%(len(fpDL),int(time_stop_diff/len(fpDL))))	
	if prev_fpDL_used:	
		print("Skipped [FP is ready]:",len(prev_fpDL))
	else:
		print("All FP are initialy generagetd")
	print("Error while generation FP:",len([a['RC'] for a in fpDL if a['RC'] < 0]))
	print("Albums with bad FP:",len([a['RC'] for a in fpDL if a['RC'] < 0]))
	print("Albums with OK FP:",len([a['RC'] for a in fpDL if a['RC'] > 0]))
	
	check_MB_discID_in_fpDL(fpDL)
	
	return {'fpDL':fpDL,'music_folderL':music_folderL}
	
def check_MB_discID_in_fpDL(fpDL):
	cnt = 0
	no_discid_cnt = more_release_cnt = 	no_mb_data_for_discid_cnt = no_release_data_cnt = one_release_cnt = 0
	for item in fpDL:
		if 'MB_discID' in item:
			if 'disc' in item['MB_discID']:
				if 'release-list' in item['MB_discID']['disc']: 
					if len(item['MB_discID']['disc']['release-list']) == 1:
						print(cnt,item['MB_discID']['disc']['release-list'][0]['title'],'\n',item['album_path'],'utf-8')
						print(cnt,item['discID'])
						one_release_cnt+=1
					elif len(item['MB_discID']['disc']['release-list']) > 1:
						print(cnt, "! Releases:",len(item['MB_discID']['disc']['release-list']),'\n',item['album_path'],'utf-8')
						more_release_cnt+=1
					else:
						print(cnt,"MB out of data [release-list] is empty for %s: %s "%(str(item['MB_discID']['disc']['id']),str(item['album_path'],'utf-8')))
						no_mb_data_for_discid_cnt+=1
						#return (item['MB_discID']['disc'],item['album_path'])
					cnt+=1
				else:                
					print('-r', end=' ')
					no_release_data_cnt+=1
					cnt+=1		
			else:
				cnt+=1	
				continue
				
		else:
			print(cnt,"No discID in:",item['album_path'])
			no_discid_cnt +=1
			cnt+=1
	print('No discId generated in:',no_discid_cnt)		
	print('No MB release data for existed mb discId:',no_mb_data_for_discid_cnt)
	print('Strange case with no release:',no_release_data_cnt)
	print('OK - One release in MB:',one_release_cnt)
	print('OK - More releases in MB:',more_release_cnt)

def guess_TOC_from_tracks_list(tracksL):
	track_offset_cnt = 0
	total_track_sectors = 0
	first_track_offset = 150
	pregap = 0
	offset_mediaL = []
	discidInputD = {}
	next_frame = 0
	trackDL = []
	print('in guess_TOC_from_tracks_list')
	track_num = 0
	for track in tracksL:
		
		fType = os.path.splitext(track)[1][1:]
		try:
			trackD = GetTrackInfoVia_ext(track,fType)
		except Exception as e:
			print('Error in guess_TOC_from_tracks_list:',e)
			print('No TOC calculation possible')
			return{'TOC_dataL':[],'discidInput':{},'toc_string':''}
		full_length = trackD['full_length']
		
		total_track_sectors = total_track_sectors + int(full_length *75)+1
		if track_num == 0:
			offset_mediaL.append(first_track_offset + pregap)	
			next_frame = total_track_sectors - track_offset_cnt - pregap + first_track_offset - 1	
		else:
			offset_mediaL.append(next_frame)
		#print('Sector:',next_frame)	
		next_frame = total_track_sectors - track_offset_cnt - pregap + first_track_offset - 1		
		track_offset_cnt+=1	
		track_num +=1
		trackDL.append(trackD)
		
		
	lead_out_track_offset=next_frame	
	toc_string = 	''		
	if offset_mediaL:
		discidInputD = {'First_Track':1,'Last_Track':len(tracksL),'offsetL':offset_mediaL,'total_lead_off':lead_out_track_offset}
		toc_string = '%s %s %s %s'	%(discidInputD['First_Track'],discidInputD['Last_Track'],discidInputD['total_lead_off'],str(discidInputD['offsetL'])[1:-1].replace(',',''))
	
	return{'discidInput':discidInputD,'toc_string':toc_string,'trackDL':trackDL}	
	
def get_TOC_from_log(album_folder):
	files = os.listdir(album_folder)
	logs = [f for f in files if os.path.splitext(f)[1] == b'.log']
	logs.sort()
	TOC_dataL = []
	discidInputD = {}
	TOC_lineD= {}
	for f in logs:
		print(f)
		# detect file character encoding
		with open(os.path.join(album_folder,f),'rb') as fh:
			d = chardet.universaldetector.UniversalDetector()
			for line in fh.readlines():
				d.feed(line)
			d.close()
			encoding = d.result['encoding']
			print(encoding)
		with codecs.open( os.path.join(album_folder,f),'rb', encoding=encoding) as fh:
			lines = fh.readlines()
			regex = re.compile(r'^\s+[0-9]+\s+\|.+\|\s+(.+)\s+\|\s+[0-9]+\s+|\s+[0-9]+\s+$')
			
		matches = [tl for tl in map(regex.match,lines) if tl]

		if matches:
			start_offset = 150
			offsetL = []
			for tl in matches:
			     TOC_line = tl.string.split('|')
			     TOC_lineD = {'Track':int(TOC_line[0]),'Start':TOC_line[1],'Length':TOC_line[2],'Start_Sector':int(TOC_line[3]),'End_Sector':int(TOC_line[4])}
			     TOC_dataL.append(TOC_lineD)
			     offsetL.append(start_offset+int(TOC_line[3]))
			break
	toc_string = 	''		
	if TOC_dataL:
		discidInputD = {'First_Track':TOC_dataL[0]['Track'],'Last_Track':TOC_dataL[-1]['Track'],'offsetL':offsetL,'total_lead_off':1+start_offset+int(TOC_lineD['End_Sector'])}
		toc_string = '%s %s %s %s'	%(discidInputD['First_Track'],discidInputD['Last_Track'],discidInputD['total_lead_off'],str(discidInputD['offsetL'])[1:-1].replace(',',''))
	return{'TOC_dataL':TOC_dataL,'discidInput':discidInputD,'toc_string':toc_string}
	
		
def get_acoustID_from_FP_collection(fpDL):
	API_KEY = 'cSpUJKpD'
	resD = {}
	album_OK_cnt = 0
	album_missed_cnt = 0
	album_partly_covered=0
	album_RC_ge_0_cnt = 0
	meta = ["recordings","recordingids","releases","releaseids","releasegroups","releasegroupids", "tracks", "compress", "usermeta", "sources"]
	meta = ["recordings"]

	
	fpDL_len = len([a['RC'] for a in fpDL if a['RC']>0])  
	for a in fpDL:
		if a['RC']>0:
			album_RC_ge_0_cnt +=1
			print(a['album_path'])
			track_OK_cnt = 0
			for trackD in a['FP']:
				duration, fp = trackD['fp']
				time.sleep(.3)
				response = acoustid.lookup(API_KEY, fp, duration,meta)
				res = acoustid.parse_lookup_result(response)
				trackD['recording_idL']=[]
				for score, recording_id, title, artist in res:
					resD = {'score':score,'recording_id': recording_id,'title':title, 'artist':artist}
					trackD['recording_idL'].append(resD)

				if len(trackD['recording_idL'])> 0:
					track_OK_cnt+=1
					print(len(trackD['recording_idL']), end=' ')
			if track_OK_cnt == 0:
				print("[ :-( Album missed")
				album_missed_cnt+=1
			elif	len(a['FP'])	> track_OK_cnt:
				album_partly_covered +=1
				print("[ Partly covered: %i of %i tracks."%(track_OK_cnt,len(a['FP'])))
				
			elif	len(a['FP'])	== track_OK_cnt:
				album_OK_cnt+=1
				print("[ Album - OK: %i tracks.  "%track_OK_cnt)
			print(album_RC_ge_0_cnt,' .Total OK:{0} -> [{3:.0%}] Missed:{1} -> [{4:.0%}] Partly: {2} -> [{5:.0%}] from {6}.'.format(album_OK_cnt,album_missed_cnt,album_partly_covered,
			float(album_OK_cnt)/fpDL_len,float(album_missed_cnt)/fpDL_len,float(album_partly_covered)/fpDL_len,fpDL_len))	
		print()
	return resD		


	
def is_discId_release_in_FP_response(discId_MB_resp,acoustId_resp):
	recordingsL = []
	release_groupL = []
	releasesL = []
	mediumDL = []
	if 'disc' not in discId_MB_resp:
		print('Error key [disc] is missing in:',discId_MB_resp)
		return False
	releasesL_discId = [a['release-group']['id'] for a in discId_MB_resp['disc']['release-list']]
	if 'results' not in acoustId_resp:
		print('Error in:',acoustId_resp)
		return False

	releasesL_FP = collect_MB_release_from_FP_response(acoustId_resp)['release_groupL']
	#print('discId:',releasesL_discId)
	#print('FP:',releasesL_FP)
	
	for a in releasesL_discId:
		if a in releasesL_FP:
			return True
	return 	False	
	
def match_discId_release_in_FP_response(discId_MB_resp,acoustId_resp,Release_ReleaseGroupD):
	recordingsL = []
	
	release_groupL_FP = releases_FP = releases_discId = release_groupL_discId = []
	mediumDL = []
	release_groupL_discId = [a['release-group']['id'] for a in discId_MB_resp['disc']['release-list']]
	releases_discId = [a['id'] for a in discId_MB_resp['disc']['release-list']]
	
	if 'results' not in acoustId_resp:
		print('Error in:',acoustId_resp)
		return False
	release_groupL_FP = collect_MB_release_from_FP_response(acoustId_resp)['release_groupL']
	releases_FP = collect_MB_release_from_FP_response(acoustId_resp)['releasesL']
	#print('discId:',releasesL_discId)
	#print('FP:',releasesL_FP)
	
	for a in release_groupL_discId:
		if a in release_groupL_FP and a not in Release_ReleaseGroupD['release-group']:
			Release_ReleaseGroupD['release-group'].append(a)		
			
	for a in releases_discId:
		if a in releases_FP and a not in Release_ReleaseGroupD['release-list']:
			Release_ReleaseGroupD['release-list'].append(a)		
			
	return 	{'release-list':Release_ReleaseGroupD['release-list'],'release-group':Release_ReleaseGroupD['release-group']}

def build_FP_db_tracks_record(fpDL):
	# база FP - будет основой формирования метаданных медиатеки. формируется полностью автоматически, с возможностью добавления набора альбомов или единичных #альбомов. 
	# содержит статистику покрытия FP, discId, положительными резульатами запросов по FP к musicbrainz содержит ссылки по CRC32 на рабочую medialib.db3
	# даст оценку доли автоматического и ручного ведения метаданных для рабочей medialib.db3
	# должна содержать на начальном этапе потрэковую информацию "recording", альбомную "releases", артистов, работы "works"
	# подготовка записи в базе FP для последующего сохранения в БД
	# учитывать полное или частичное отсутствие FP для трэка - это позволит иметь статистику покрытия медиа коллекции FP, делать регулярный повторный расчет,
	# иметь снимок всей медиатеки
	for item in fpDL:
		if item['scenarioD']['cue_state']['only_tracks_wo_CUE']:
			for track in 'normal_trackL':
				pass
	return db_record	

def album_FP_discid_response_validate(fpDL):
	# валидация ответов MB и acoustId (далее просто ответы MB) для собранных потрэково и поальбомно acousticId fingerprints и discid
	# задача, по набору FP и discID однозначно идентифицироваь релиз. Чем больше критериев валидации исполнено, тем выше вероятность праильной идентификации
	# релиза альбома. наличие discID упрощает выбор правильного релиза. Если его нет, необходимо идентифицировать релиз только на основании набора FP всех трэков альбома.
	# когда нет данных  по discID или они не достоверны?: TOC не сформирован, ТОС не идентифицируется в ответе MB, результаты по TOC не совпдадают с результатами FP (различные релизы)
	# сценарии валидации:
	# 1. все FP трэков принадлежат одному релизу по этому релизу совпадает количество трэков в ответе MB = > альбом - accepted
	## 1.1для очень коротких трэков <20 сек acoustId не дает разультата. такой трэк надо просто пропустить. не считая его за ошибку. 
	## 1.2совпадение может быть только по части трэков. для остальной части FP не идентифицируется на сервисе, возможно некорректное формирование FP локально, что становиться критичным для коротких трэков.
	## 1.3возможны ошибки при получении результата, в этом случае отфильтровав по коду ошибки, заново запросить результат для FP
	# 2. при наличии TOC и положительной его идентификации соотв. релиз совпадает с результатами соотв. релизов по FP трэков. при наличии нескольких релизов связанных с FP трэков, момогает идентифицировать правильный релиз. Если релиз всего один и он совпал по всем FP и discId => альбом strongly accepted 
	# discId релиз
	index = 0
	release_id_checkL = []
	Release_ReleaseGroupD = {'release-list':[],'release-group':[]}
	ReleaseGroupL = []
	not_confirmed_cnt = confirmed_cnt = partly_confirmed_cnt = partly_fp_confirmed_cnt = hi_res_cnt = failed_cnt = 0
	
	for item in fpDL:
		Release_ReleaseGroupD = {'release-list':[],'release-group':[]}
		print('\n',index, '  ========== %s'%(item['album_path'] ))
		if 'convDL' not in item:
			print('Hi-res proc issue')
			hi_res_cnt +=1
			failed_cnt+=1
			index+=1
			continue
		
		
		#release_id = check_album_from_acoustId_resp_list(item['convDL'],len(item['convDL']))['release_id']
		#print('release_id:',release_id)
		# scenario without discId
		if 'MB_discID' not in item:
			print('i', end=' ')
			print('Error (2138) with fpDL index:',index,item['album_path'])
			return
			
		if item['MB_discID']:
			print('==== MB_discID scenario:')
			track_index = 1
			in_MB_discID_cnt = 0
			for trac_data in item['convDL']:
				if is_discId_release_in_FP_response(item['MB_discID'], trac_data['response']):
					print('*',end=' ')
					Release_ReleaseGroupD = match_discId_release_in_FP_response(item['MB_discID'], trac_data['response'],Release_ReleaseGroupD)
					in_MB_discID_cnt +=1
				else:
					if trac_data['fp'][0] < 20:
						print('\n very short track %i:[%i]sec'%(track_index,int(trac_data['fp'][0])))
					elif 'error' in trac_data['response']:
						print('\n with MB_discID scenario issue in track %i: FP service return error. Recall FP response'%(track_index))
					elif trac_data['response']['results'] == []:	
						print('\n with MB_discID scenario issue in track %i: FP service result is empty. Recalculate and recheck FP'%(track_index))
				
				try:	
					recordinds = collect_MB_release_from_FP_response( trac_data['response'])['recordingsL']		
					print('Recording id:',recordinds)
				except Exception as e:
					print('Error in recording extraction',str(e))

				track_index+=1	
			if in_MB_discID_cnt == len(item['convDL']):
				print('MB_discID and FP results successuly validated')
				confirmed_cnt+=1
				
			if in_MB_discID_cnt < len(item['convDL']) and in_MB_discID_cnt > 0:
				print('MB_discID and FP results only partly [%i of %i] validated'%(in_MB_discID_cnt,len(item['convDL'])))
				partly_confirmed_cnt+=1	
			elif in_MB_discID_cnt == 0:
				not_confirmed_cnt+=1
				
		else:
			print('		==== Only FP scenario:')
			release_id_checkL = []
			
			for trac_data in item['convDL']:
				release_id = get_release_from_acoustId_resp_list_via_track_number(item['convDL'],len(item['convDL']))
				if not release_id:
				#	failed_cnt+=1
					continue
					
				release_id_checkL.append(release_id)
				try:	
					recordinds = collect_MB_release_from_FP_response( trac_data['response'])['recordingsL']		
					print('Recording id:',recordinds)
				except Exception as e:
					print('Error in recording extraction',str(e))	
					
			if 	len(release_id_checkL) == len(item['convDL']) and len(list(set(release_id_checkL))) == 1:	
				print('		release from MB resp:', set(release_id_checkL))
				confirmed_cnt+=1
				Release_ReleaseGroupD['release-list'] = set(release_id_checkL).pop()
			elif len(release_id_checkL) != len(item['convDL']) and len(list(set(release_id_checkL))) > 1:
				print('		Wrong release from MB resp:',set(release_id_checkL))
				partly_fp_confirmed_cnt+=1
				Release_ReleaseGroupD['release-list'] = set(release_id_checkL).pop()
				#for trac_data in item['convDL']:
				#	return collect_MB_release_from_FP_response(trac_data['response'])
			else:
				failed_cnt+=1
		item['ReleasesD'] = Release_ReleaseGroupD		
		print('ReleasesD:',Release_ReleaseGroupD)
		index+=1			
	print('Confirmed: %i, Partly_confirmed: %i, Partly fp confirmed:%i, Total confirmed: %i, Failed %i'%(confirmed_cnt,partly_confirmed_cnt,partly_fp_confirmed_cnt,confirmed_cnt+partly_confirmed_cnt+partly_fp_confirmed_cnt,failed_cnt))	
	print('hi_res issue:',hi_res_cnt)
	print('Not confirmed:',not_confirmed_cnt)
	
	return release_id_checkL
	
def collect_MB_release_from_FP_response(acoustId_resp):
	recordingsL = []
	release_groupL = []
	releasesL = []
	mediumDL = []
	release_id = 0
	if 'results' not in acoustId_resp and 'error' in acoustId_resp:
		print('Error in response')
		return{'recordingsL':recordingsL,'release_groupL':release_groupL,'releasesL':releasesL,'mediumDL':mediumDL,'error':acoustId_resp['error']}
	for res_item in acoustId_resp['results']:
		if 'recordings' not in res_item:
			continue
		for rcrds in res_item['recordings']:
			if 'id' not in rcrds:
				#print('Error in FP response rec id',rcrds)
				return{'recordingsL':recordingsL,'release_groupL':release_groupL,'releasesL':releasesL,'mediumDL':mediumDL}
			#else:	
			recordingsL.append(rcrds['id'])
			#yield rcrds['id']
			if 'releasegroups' in rcrds:
				
				for rel_group in rcrds['releasegroups']:
					release_groupL.append(rel_group['id'])
				

					for release in rel_group['releases']:
						releasesL.append(release['id'])
						
						for medium in release['mediums']:
							medium['release_id'] = release['id']
							mediumDL.append(medium)

	return{'recordingsL':recordingsL,'release_groupL':release_groupL,'releasesL':releasesL,'mediumDL':mediumDL}
	
def get_release_from_acoustId_resp_list_via_track_number(acoustId_respL,track_number):
	
	try:

		mediumDL_List = [collect_MB_release_from_FP_response(a['response'])['mediumDL'] for a in acoustId_respL]
		for c in [b for b in mediumDL_List if b != []]:
			return set(e['release_id'] for e in c if e['track_count'] == track_number ).pop() 
		
	except Exception as e:
		
		print('error in get_release_from_acoustId_resp_list_via_track_number [%s]'%str(e))
			
	return 
		
def acoustID_lookup_celery_wrapper(self,*fp_args):
	scoreL = fp_item = []
	err_cnt = 0
	
	print('fp:',fp_args)
	API_KEY = 'cSpUJKpD'
	meta = ["recordings","recordingids","releases","releaseids","releasegroups","releasegroupids", "tracks", "compress", "usermeta", "sources"]
	response=acoustid.lookup(API_KEY, fp_args[1], fp_args[0],meta)
	print(response)
	return {'response':response,'fname':fp_args[2]}

def MB_get_releases_by_discid_celery_wrapper(self,*discID_arg):	
	discID = discID_arg[0]
	MB_discID_result = ''
	try:
		MB_discID_result = musicbrainzngs.get_releases_by_discid(discID,includes=["artists","recordings","release-groups"])
	except Exception as e:
		print(e)
		return {'RC':-6,'error':str(e)}
		
	if 'disc' not in MB_discID_result:	
		return {'RC':-7,'error':'DiskID MB - NOT detected','MB_discID_result':MB_discID_result}
	
		
	return {'RC':1,'MB_discID_result':MB_discID_result}
	
async def acoustID_lookup_wrapper(fp):
    API_KEY = 'cSpUJKpD'
    meta = ["recordings","recordingids","releases","releaseids","releasegroups","releasegroupids", "tracks", "compress", "usermeta", "sources"]
    return acoustid.lookup(API_KEY, fp[1], fp[0],meta)	
	
	
	
async def acoustID_lookup_wrapper_parent(fp):
    return await acoustID_lookup_wrapper(fp)	

if __name__ == '__main__':
	import argparse
	job_list = []
	parser = argparse.ArgumentParser(description='media lib tools')
	parser.add_argument('ml_folder_tree', metavar='saves medialib folders as pickled object, taking the path from config',
                        help='ml_folder_tree')	
	args = parser.parse_args()	
	
	cfg_fp.read(medialib_fp_cfg)
	nas_path_prefix = cfg_fp['FOLDERS']['nas_path_prefix']
	ml_folder_tree_buf_path = cfg_fp['FOLDERS']['ml_folder_tree_buf_path']
	audio_files_path_list = cfg_fp['FOLDERS']['audio_files_path_list']
	
	dirL = json.loads(cfg_fp.get('FOLDERS',"audio_files_path_list"))
	
	creation_time = time.time()
	
	folders_list_obj = find_new_music_folder_simple(None,dirL)
	print()
	print('Passed:', time.time()-creation_time)
	try:
		with open(ml_folder_tree_buf_path, 'wb') as f:
			d = pickle.dump({'folder_list':folders_list_obj['folder_list'],'NewFolderL':folders_list_obj['NewFolderL'],'music_folderL':folders_list_obj['music_folderL'],'creation_time':creation_time},f)
	except Exception as e:
		print('Error in pickle',e)				
	
	