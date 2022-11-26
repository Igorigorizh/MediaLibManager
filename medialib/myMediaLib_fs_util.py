# -*- coding: utf-8 -*-
import os
from posixpath import join, dirname
from os import scandir

import json
import time
import logging
from pathlib import Path
import functools
logger = logging.getLogger('controller_logger.fs_utils')

def time_mesure(function):
    """A general decorator function"""
    import time
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        t = time.time()
        result = function(*args, **kwargs)
        print('Passed:%i sec'%int(time.time() -t))
        return result
    return wrapper

class Media_FileSystem_Helper:
	""" Media file system processing helper"""
	
	def __init__(self):
		self._current_iteration = 0
		self._file_extL = ['.flac','.mp3','.ape','.wv','.m4a','.dsf']
		self._EXT_CALL_FREQ = 100
		#
        #progress_recorder = ProgressRecorder(self)
		#self._progress_recorder_descr = 'medialib-job-folder-scan-progress-media_files'
		#self._progress_thredhold = 10
	def iterrration_extention_point(self, *args):
        """ iterrration_extention_point designed for redefine in a child class"""
		if 'verbose' in args:
			if self._current_iteration%self._EXT_CALL_FREQ == 0:
				print(self._current_iteration, end=' ',flush=True)
        #нельзья даже оценить начальное количество папок до конца обхода дерева, поэтому
        # вначале считать прогресс до self._progress_thredhold. а затем каждый раз оценивать
        # по отношению текущего итератора к итератору +1.    
        #progress_recorder.set_progress(i, i+1, description=progress_recorder_descr)
            

	def _collect_media_files_in_folder_list(self, folderL, *args):
		""" Looks for audio files in folder and coolects such folder"""
		music_folderL = []

		self._current_iteration = 0

		for new_folder in folderL:	
			for root, dirs, files in os.walk(new_folder):
				for a in files:
					if os.path.splitext(a)[-1] in self._file_extL:
						if root not in music_folderL:
							music_folderL.append(Path(root).as_posix())
							break
			
				self.iterrration_extention_point(self._current_iteration,*args)	
				self._current_iteration +=1
           
		return 	music_folderL				

	def _bulld_subfolders_list(self, folderL, *args):
        # Возвращает пары(root,folder) любого типа, без вильтра 
		""" Collects all any type subfolders recursivelly  of a given folders list in folderL """

		for new_folder in folderL:
			if 'verbose' in args:
				print()
				if not os.path.exists(new_folder):
					print(new_folder,'  Not exists')
					continue
				else:
					print(new_folder,'  Ok')
			i = 0		
			for root, dirs, files in os.walk(new_folder):
				for a in dirs:
					self.iterrration_extention_point(self._current_iteration)	
					self._current_iteration += 1
					yield(Path(root).as_posix(),a)
		return


	def identify_music_folder(self, init_dirL,*args):
		""" Collects folders with media files with respect to hard coded file_extL"""
		logger.debug('in identify_music_folder - start [%s]'%str(init_dirL))
		music_folderL = []
		

		for init_dir in init_dirL:
			if not isinstance(init_dir, str):
				print(init_dir)
				init_dirL[init_dirL.index(init_dir)] = init_dir.decode('utf8')
			else:
				if not os.path.exists(init_dir):
					print(init_dir, ': does not exists')
					return {'music_folderL':[]}
		i = 0
		t = time.time()
		print("Folders scanning ...")
		for new_folder in init_dirL:
			print("new_folder:",new_folder)
			with os.scandir(new_folder) as it:
				for entry in it:
					print(entry)
					if not entry.name.startswith('.') and entry.is_file():
						if os.path.splitext(entry.name)[-1] in self._file_extL:
							dir_name = os.path.dirname(''.join((new_folder,entry.name)))
							print(dir_name)
							#print [join(root.decode('utf8'),a.decode('utf8'))]
							if dir_name not in music_folderL:
								music_folderL.append(dir_name)
								#print 'dir_name:',type(dir_name),[dir_name]
								break

		print()
		time_stop_diff = time.time()-t
		print('Scanning for music folder: Finished in %i sec'%(int(time_stop_diff)))
		logger.debug('in identify_music_folder found[%s]- finished'%str(len(music_folderL)))
		return {'music_folderL':music_folderL}

	def find_new_music_folder_simple(self, init_dirL,*args):
		""" similar to find_new_music_folder but more simple without db filter and pickle """
		logger.info('in find_new_music_folder_simple - start')
		folders_list = tuple(self._bulld_subfolders_list(init_dirL,'verbose'))	
		t = time.time()
		print()
		print('Passed:',time.time()-t)
		joined_folder_list = list(set([join(a[0],a[1]) for a in folders_list]))
		joined_folder_list.sort()
		t = time.time()
		music_folderL = self._collect_media_files_in_folder_list(joined_folder_list,'verbose')
		print()
		print('Passed:',int(time.time() - t))
		logger.debug('in find_new_music_folder_simple found[%s]- finished'%str(len(music_folderL)))
		return {'folder_list':folders_list,'NewFolderL':joined_folder_list,'music_folderL':music_folderL}
	

	def find_new_music_folder(self, init_dirL, prev_folderL, DB_folderL,*args):
		# по умолчанию ищет музыкальную папку в пересечении множеств исходного дерева папок (сохраненного в ml_folder_tree_buf_path)и узла,
		# который содержит новые данные + если запрошено по наличию папки в таблице album из DB_folderL
		
		#print args
		logger.info('in find_new_music_folder - start')
		f_l = []
		new_folderL = []
		resBuf_save_file_name = ''
		f_name = ''
		
		creation_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		
		# Новый сценарий получение списка части дерева папок относительно искомого узла (init_dirL) из БД
		if args != ():
			if type(args[0]) == dict:
				if 'resBuf_save' in args[0]:
					resBuf_save_file_name = args[0]['resBuf_save']
					f_name = cfgD['ml_folder_tree_buf_path']
		
		print('resBuf_save_file_name',resBuf_save_file_name)
		for init_dir in init_dirL:
			if not isinstance(init_dir, str):
				print('Not string:',init_dir)
				init_dirL[init_dirL.index(init_dir)] = init_dir.decode('utf8')
			else:
				if not os.path.exists(init_dir):
					print(init_dir, 'does not exists')
					return {'folder_list':[],'NewFolderL':[]}
		i = 0
		t = time.time()
		print("Folders scanning ...")
		
		f_l= tuple(self._bulld_subfolders_list(init_dirL, *args))			
		print()
		time_stop_diff = time.time()-t
		print('Takes sec:',time_stop_diff)
		if prev_folderL == [] and not 'initial' in args:
			print('First run: Finished in %i sec'%(int(time_stop_diff)))
			if resBuf_save_file_name != '':
				with open(f_name,'wb') as f:
					d = pickle.dump({'folder_list':f_l,'NewFolderL':[],'music_folderL':[],'creation_time':creation_time},f)
					
				logger.info('in find_new_music_folder - finished: Buff saved in:%s'%(f_name))
				return {'resBuf_save':f_name}
			else:
				return {'folder_list':f_l,'NewFolderL':[]}
		
		if DB_folderL != []:
			prev_folderL = list(set([join(a[0],a[1]) for a in DB_folderL]).difference(set([join(a[0],a[1]) for a in prev_folderL])))
		# Вычисление пересеченеия новых папок с последним сохраненным деревом папок
		new_folderL = list(set([join(a[0],a[1]) for a in f_l]).difference(set([join(a[0],a[1]) for a in prev_folderL])))
		#print(new_folderL[0])
		#new_folderL = list(set(f_l).difference(set(prev_folderL)))
		new_folderL.sort()

		if len(new_folderL) == 0:
			print('No Change: Finished')
		elif len(new_folderL) > 0:
			print('Changes found!', len(new_folderL))
			#print(new_folderL)
		# Collect music folders
		music_folderL = []
		
		t = time.time()
		print("Media Folders collecting ...")
		music_folderL = self._collect_media_files_in_folder_list(new_folderL)
		time_stop_diff = time.time()-t
		print('2nd scan takes sec:',time_stop_diff)
		# check if initial folder root folder itself containes media
		if not music_folderL:
			music_folderL = self._collect_media_files_in_folder_list(init_dirL)
							
		
		
		music_folderL = list(set(map(lambda x: x.replace('\\','/'),music_folderL)))	
		if resBuf_save_file_name != '':
			with open(f_name,'wb') as f:
				d = pickle.dump({'folder_list':f_l,'NewFolderL':new_folderL,'music_folderL':music_folderL,'creation_time':creation_time},f)
			logger.info('in find_new_music_folder - finished: Buff saved in:%s'%(f_name))
			return {'resBuf_save':f_name}
		
		logger.debug('in find_new_music_folder found[%s]- finished'%str(len(music_folderL)))
		return {'folder_list':f_l,'NewFolderL':new_folderL,'music_folderL':music_folderL}
	
	

def get_parent_folder_stackL(path,stop_nodeL):
	""" Builds folder parents stack from given folder root with respect to folders stop list """
	if not os.path.isabs(path):
		return([])	
	nodesL =[]
	
	for _ in range(20):
		parent_dir = os.path.dirname(path)
		if path == parent_dir:
			break
		path = parent_dir
		if path in stop_nodeL:
			break
		nodesL.append(path)
	return(nodesL)