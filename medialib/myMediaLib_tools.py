# -*- coding: utf-8 -*-
import os
from os.path import join, dirname
from os import scandir
import pickle
import acoustid
import zlib
import sqlite3
import chardet

if os.name == 'nt':
	import discid
elif os.name == 'posix':
	pass
	#import libdiscid as discid
#import mktoc

import musicbrainzngs
import time
import logging
import ast
from pathlib import Path

from myMediaLib_init import readConfigData

from myMediaLib_adm import simple_parseCue
from myMediaLib_adm import getFolderAlbumD_fromDB
from myMediaLib_adm import db_request_wrapper
from myMediaLib_adm import collect_albums_folders

from myMediaLib_CONST import BASE_ENCODING
from myMediaLib_CONST import mymedialib_cfg

import warnings

cfgD = readConfigData(mymedialib_cfg)

logger = logging.getLogger('controller_logger.tools')

musicbrainzngs.set_useragent("python-discid-example", "0.1", "your@mail")

def make_temp_wav_cue(original_cue_path):
	# Пересобирирем CUE с новым именем образа temp.wav
	f = open(original_cue_path,'r')
	l = f.readlines()
	f.close()

	title_cnt = 0
	track_cnt = 1
	track_wavL = []
	orig_nameL = []
	newL = []
	track_flag = False
	stop_list_punct = ['.',';',',','/','\\','_','&','(',')','*','%','?','!','-',':','  ']
	
	for line_str in l:
		orig_name = 'error_file.dat'
		if """.ape"w""".lower() in line_str.replace(' ','').lower() :
			line_strL = line_str.split()
			
			if len(line_strL) > 3:
				if line_strL[0].lower().strip() == 'file' and line_strL[-1].lower().strip() == 'wave':
					orig_name = line_str[4:-5].strip().rstrip()[1:-1]
					

			newL.append("""FILE "temp%i.wav"  WAVE\n"""%track_cnt)
			track_wavL.append((orig_name,"temp%i.wav"%track_cnt))
			track_cnt+=1
			continue
		elif """.flac"w""".lower() in line_str.replace(' ','').lower():
			line_strL = line_str.split()
			
			if len(line_strL) > 3:
				if line_strL[0].lower().strip() == 'file' and line_strL[-1].lower().strip() == 'wave':
					orig_name = line_str[4:-5].strip().rstrip()[1:-1]
					
				
			newL.append("""FILE "temp%i.wav"  WAVE\n"""%track_cnt)
			track_wavL.append((orig_name,"temp%i.wav"%track_cnt))
			track_cnt+=1
			continue
		elif "title" in line_str.strip().lower()[0:]:
			if track_flag:
				for a in stop_list_punct:
					line_str = line_str.replace(a,' ')

				pos = line_str.rfind('"')
				if pos > 0:
					line_str = line_str[:pos].rstrip()+'"'


				line_str = line_str.strip()+"\n"

				#print line_str,
				title_cnt+=1
			else:
				# значит встретился TITLE первый раз и его надо пропустить
				continue


		if line_str.lower().strip().find('track ') == 0:
			track_flag=True

		newL.append(line_str)

	cue_dir_name = os.path.dirname(original_cue_path)
	try:
		f=open(original_cue_path+'temp','w')
	except OSError as e:
		print('Error in do_cue_2_track_split 5564:', e)
		return {'RC':-1,'newCueLineL':newL,'track_wavL':track_wavL,'title_numb':title_cnt,'track_cnt':track_cnt}
	f.writelines(newL)
	f.close()
	return {'RC':1,'newCueLineL':newL,'track_wavL':track_wavL,'title_numb':title_cnt,'track_cnt':track_cnt}
	
def do_cue_2_track_split(codec_path,album_path,*args):
	# разбивка CUE если необходимо, если потрэковый CUE или трэки (апе, flac mp3) - просто возврат			
	mode = ''
	modeL = []
	replace_flag = False
	image_cue = ''
	image_name = ''
	origfD = {}
	newL = []
	part_l = []
	prog = ''
	params = ()
	origfD = {}	
	orig_cue_title_cnt = 0
	f_numb = 0
	real_track_numb=0
	mess = ''
	discID = None
	error_logL=[]
	if not os.path.exists(codec_path):
		print('---!Codecs path Error:%s - not exists'%codec_path)
		error_logL.append('[CUE check]:---!Codecs path Error:%s - not exists'%codec_path)
		return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':0,'mode':modeL,'to_be_split':False,'error_logL':error_logL}	
	
	if not os.path.exists(album_path):
		print('---!Album path Error:%s - not exists'%album_path)
		error_logL.append('[CUE check]:---!Album path Error:%s - not exists'%album_path)
		return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':0,'mode':modeL,'to_be_split':False,'error_logL':error_logL}
	
	filesL = os.listdir(album_path)

	if 'convert_cue_delete' in args:
		for a in filesL:
			if '.cuetemp' in a:
				print(a,"-----")
				if os.path.exists(album_path+a):
					os.remove(album_path+a)
					continue
			
	
	stop_list_punct = ['.',';',',','/','\\','_','&','(',')','*','%','?','!','-',':','  ']

	if 'convert_cue_delete' in args:
		if os.path.exists(album_path+'convert_cue\\'):
			
			for f_name in os.listdir(album_path+'convert_cue\\'):
				os.remove(album_path+'convert_cue\\'+f_name)
					
			if os.listdir(album_path+'convert_cue\\') == []:
				os.rmdir(album_path+"convert_cue\\")
				print('--->   '+album_path+"convert_cue\\"+" --> is deleted")
		else:
			print('--->   '+album_path+"convert_cue\\"+" --> was not found")
		return {'RC':0,'f_numb':f_numb,'orig_cue_title_numb':0,'title_numb':0,'mode':modeL}	
	
	
	cue_cnt = 0
	#Валидация CUE через соответствие реальным данным для цели дальнейшей разбивки
	# Либо это нормальный CUE (TITLES > 1 и образ физически есть) -> нужна разбивка на трэки - ОК 
	# Либо это любой в тч 'битый' CUE, но есть отдельные трэки -> разбивка не нужна проверить соотв. количества трэков и титлов в #`CUE приоритет tracks и сверка с КУЕ
	
	to_be_split=False
	error_logL=[]
	for a in filesL:
		#print a
		if a.lower().rfind('.cue')>0:
			
			image_cue = a
			
			try:	
				origfD = simple_parseCue(album_path+image_cue)	
			except Exception as e:
				print(e)
				
				return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':0,'mode':['cue_corrupted'],'to_be_split':False}
				
			cue_cnt+=1
			if cue_cnt>1:
				print('--!-- Error Critical! several CUE Files! Keep only one CUE!')
				error_logL.append('[CUE Split]:--!-- Error Critical! several CUE Files! Keep only one CUE!')
				return {'RC':-1,'f_numb':0,'orig_cue_title_numb':0,'title_numb':0,'mode':['cue','cue_error'],'to_be_split':False,'error_logL':error_logL}
			
			if 'cue' not in modeL:
				modeL.append('cue')
						
			if 'orig_file_path' in origfD:
				orig_cue_title_cnt = origfD['cue_tracks_number']
				if os.path.exists(origfD['orig_file_path']):
					if orig_cue_title_cnt>0:
						to_be_split=True
						
				else:
					modeL.append('cue_error')
					
		else:
			ext=''
			pos = a.rfind('.')
			if pos>0:
				ext=a[pos+1:]
				if ext in ['ape','mp3','flac']:
					real_track_numb+=1
					
					if 'tracks' not in modeL:
						modeL.append('tracks')
	
	RC = 0	
	
	# это обычный образ CUE	уделяем категорию tracks	
	if real_track_numb == 1 and 'cue' in modeL:
		modeL.remove('tracks') 
		RC = origfD['cue_tracks_number']
	elif 'tracks' in modeL:
		if real_track_numb > 1:
			RC = real_track_numb	
	
		
	#1. ОК - single CUE, 1 -original image, several tracks frof cue -> split is possible
	#2. ОК - several tracks > 1 ape,mp3,flac - no mix of them -> no split 
	#3. OK 2. tracks > 1 + splited CUE files from CUE tracks = cue title - Good cue can me ignored  -> no needed
	#4.  2. tracks > 1 + cue with no existed 1 image file  - BAD cue can me ignored  -> no needed
	#5.  2. tracks > 1 + cue with no existed several slitted tracks files - BAD cue can me ignored  -> no needed
	
	# В этом месте необходимо иметь образ wav и ссылку на него во временном CUE
	
		
	
	if 'is_cue' in args or not	to_be_split:
		return {'RC':RC,'to_be_split':to_be_split,'orig_cue_title_numb':orig_cue_title_cnt,'mode':modeL,'title_numb':0,'f_numb':real_track_numb,'discID':discID}
	
	
	print('image_cue=',image_cue)		
	
	if not os.path.exists(album_path+'convert_cue\\'):
		os.mkdir(album_path+'convert_cue\\')
		
	#print 'origfD - OK',origfD
	
	image_name = origfD['orig_file_path']
		
	format = ''
	if origfD['orig_file_path'].lower().rfind('.ape') >0:
		format = 'ape'
	elif origfD['orig_file_path'].lower().rfind('.flac') >0:
		format = 'flac'	
	
	
	# Пересобирирем CUE с новым именем образа temp.wav
	mk_cue_res = make_temp_wav_cue(album_path+image_cue)
	paramsL = []
	title_cnt = mk_cue_res['title_numb']
	for tmp_wav_nam in 	mk_cue_res['track_wavL']:
		params = ()
		prog = ''
		if format == 'ape':
			params = ('mac',"\""+join(album_path,tmp_wav_nam[0])+"\"","\""+join(album_path,tmp_wav_nam[1])+"\"",'-d')
			prog = 'mac.exe'
		if format == 'flac':
			prog = 'flac.exe'
			params = ('flac','-d','-f',"\""+join(album_path,tmp_wav_nam[0])+"\"",'-o',"\""+join(album_path,tmp_wav_nam[1])+"\"")
			
		if prog != '' and params != ():	
			try:
				print("Decompressing with:",prog)
				r = os.spawnve(os.P_WAIT, join(codec_path,prog), params , os.environ)		
			except OSError as e:
				print('Error in do_cue_2_track_split 5576:', e, "-->", join(codec_path,prog),params)
				return {'RC':-1,'to_be_split':to_be_split,'f_numb':f_numb,'orig_cue_title_numb':orig_cue_title_cnt,'title_numb':title_cnt,'mode':modeL}
		else:
			print('Error in do_cue_2_track_split 283:', e, "-->", codec_path,prog,image_name)
			
	#else:
	#	return {'RC':-1,'to_be_split':to_be_split,'f_numb':f_numb,'orig_cue_title_numb':orig_cue_title_cnt,'title_numb':title_cnt,'mode':modeL}
			
	image_cue = album_path+image_cue+'temp'
	image_name = ''
	tobe_splitted_image_name = ''
	# В этом месте необходимо иметь образ wav и ссылку на него во временном CUE
	discID = None	
	if to_be_split:
		tobe_splitted_image_name = join(album_path,mk_cue_res['track_wavL'][0][1])
		try:
			discID=Calculate_DiscID(join(album_path,image_cue))
			print() 
		except Exception as e:
			print("Error in DiscID calc:",e)
	
	
	
	
	tempwav_exists = False
	if to_be_split:
		if os.path.exists(tobe_splitted_image_name):
			tempwav_exists = True
		else:
			print("Error at check 302:",e)
	else:	
		for a in os.listdir(album_path):
			for t in mk_cue_res['track_wavL']:
				if t[1] == a:
					tempwav_exists = True
					break
			if tempwav_exists:
				break
			
	if not tempwav_exists:			
		mess = '--!Critical Error at decompressing [%s] not found. Decompressing failed - check image file and try manual decompr.'%tobe_splitted_image_name
		print(mess)
		return {'RC':-2,'to_be_split':to_be_split,'f_numb':f_numb,'orig_cue_title_numb':orig_cue_title_cnt,'title_numb':title_cnt,'mode':modeL,'error_logL':[mess],'discID':discID}
	
		
	output_dir = ('-d',""" "%sconvert_cue" """%(album_path))
	output_form = output_dir + ('-t',""" "(%n).%t" """)
	tr_name_conv = ('-m',":-/_*x")
		
	extract_list = ''
	try:
		part_l = ','.join([str(int(b[1:-1])) for b in key_cueD[a]['track_numL']])
		extract_list = ('-x', part_l)
	except:
		pass
	if 	part_l == '':
		extract_list = ''
		
	if to_be_split:	
		print("Splitting from:",format,tobe_splitted_image_name)	
		params = ('shntool','split',"\""+tobe_splitted_image_name+"\"",'-O','always')+('-f',"\""+image_cue+"\"")+output_form
		
		try:	
			r = os.spawnve(os.P_WAIT, join(codec_path,'shntool.exe'),params, os.environ)
		except Exception as e:
			mess = 'Error in do_cue_2_track_split 5612:', e, "shntool.exe not found"
			print(mess)
			print(params)
			return {'RC':-2,'to_be_split':to_be_split,'f_numb':f_numb,'orig_cue_title_numb':orig_cue_title_cnt,'title_numb':title_cnt,'mode':modeL,'error_logL':['Error at Splitting:shntool.exe not found'],'discID':discID}
		
		
				
		if 'keep_temp_wav' not in args:		
			if '.wav' in image_name and tempwav_exists:
				if 'temp' in tobe_splitted_image_name:
					os.remove(image_cue)
			for a in os.listdir(join(album_path,'convert_cue\\')):
				if a.lower().rfind('.wav')>0:
					new_name = album_path+'convert_cue\\'+a	
					if "pregap.wav" in new_name:
						print("pregap.wav --> deleted")
					os.remove(new_name)
			
		f_numb = len(os.listdir(album_path+'convert_cue\\'))		
		if orig_cue_title_cnt == title_cnt == f_numb:
			res_str = " --OK-- Successfully splitted:%i files"%orig_cue_title_cnt
		else:
			res_str = " --- Warning!----: %i files skipped at splitting."%(orig_cue_title_cnt-f_numb)		
				
	else:
		if 'keep_temp_wav' not in args:	
			for t in mk_cue_res['track_wavL']:
				os.remove(join(album_path,t[1]))
	
		
	print(f_numb,title_cnt,orig_cue_title_cnt)	
	print(res_str)
		
	return {'RC':1,'to_be_split':to_be_split,'f_numb':f_numb,'orig_cue_title_numb':orig_cue_title_cnt,'title_numb':title_cnt,'mode':modeL,'discID':discID}		

def do_mass_album_FP_and_AccId(codec_path,album_path,*args):	
	# Генерация FP и AccuesticIDs по альбомам из указанной дирректории, для загрузок двойных альбомов и других массовых загрузок
	# d=myMediaLib_adm.do_mass_album_FP_and_AccId('c:\\LocalCodecs','C:\Temp\SharedPreprCD4Lib')
	
	if not os.path.exists(codec_path):
		print('---!Codecs path Error:%s - not exists'%codec_path)
		return 
	
	if not os.path.exists(album_path):
		print('---!Album path Error:%s - not exists'%album_path)
		return 
	dirL = collect_albums_folders([album_path])
	print("Folders structure build with folders:",len(dirL))
	fpDL = []
	cnt=1
	t_all_start = time.time()
	for a in dirL:
		album_path = a+"\\"
		print(cnt, ' of:',len(dirL),'-->', album_path)
		t_start = time.time()
		try:
			cnt+=1
			fpRD = generate_FP_file_in_album(codec_path,album_path,*args)
			process_time = 	int(time.time()-t_start)
			fpRD['album_path']=album_path
			fpRD['process_time'] = process_time
			fpDL.append(fpRD)	
			print('album finished in:',	process_time, "time since starting the job:",int(time.time()-t_all_start))
			
			print()
		except Exception as e:	
			print("Exception with FP generation %s: \n in %s"%(str(e),str(a)))			
			
	d = pickle.dumps(fpDL)
	fname='fpgen_%s.dump'%str(int(time.time()))
	f = open(album_path+fname,'w')
	f.write(d)
	f.close()
	time_stop_diff = time.time()-t_all_start
	print('\n\n\n')
	print("*********************************************************************")
	print("**********Generation Summary. All takes:%i sec.***********************"%(int(time_stop_diff)))
	print("*********************************************************************\n")
	for a in fpDL:
		if a['RC'] < 0:
			print("RC=(",a['RC'],")",a['album_path'],'IN TIME:',a['process_time'])
			print('*****************************')
			for b in a['error_logL']:
				print(b)
			print('*****************************')
			print()
			
		if 'RC' in a['splitRes']:
			if a['splitRes']['RC']==-1:
				
				print("CUE-RC=(",a['splitRes']['RC'],")",a['album_path'],'IN TIME:',a['process_time'])
				print('*****************************')
			elif a['splitRes']['RC']==-4:
				if 'error_logL' in a['splitRes']:
					for b in a['error_logL']:
						print(b)
						print('*****************************')
						print()
					
			
	print('Some statistics:')
	print("Collected: albums%i, pro album %i sec."%(len(fpDL),int(time_stop_diff/len(fpDL))))	
	print("Skipped [FP is ready]:",len([a for a in fpDL if a['process_time'] < 2]))
	print("Error while generation FP:",len([a['RC'] for a in fpDL if a['RC'] < 0]))
	print("Albums with bad FP:",len([a['RC'] for a in fpDL if a['RC'] < 0]))
	print("Albums with OK FP:",len([a['RC'] for a in fpDL if a['RC'] > 0]))
	
	return fpDL
	
def generate_FP_file_in_album(codec_path,album_path,*args):
	# modified in 03.2017
	# создает или читает уже созданный файл FP для трэков альбома
	# album_path это корневой каталог в котором лежат папки альбомов 
	#  пример для отладки: album_path = cfgD['preprocessAlb4libPath']+os.listdir(cfgD['preprocessAlb4libPath'])[0]
	# проблема 
	# APE+CUE - OK, FLAC+CUE - OK(иногда не разбивает)
	# 1. со странным FLAC не считается FP и не декомпрессуется
	result = ''
	temp_dir = ''
	convDL = []
	
	
	#----------  Delete this later--------------------
	if os.path.exists(album_path +'medialib_fngp.ffp'):
		os.remove(album_path +'medialib_fngp.ffp')
		#----------  Delete this later--------------------	
	
	if os.path.exists(album_path+'MdLbShrmFngp.fp'):
		if 'force_create' not in args:
			print('----FP----- already exist in: %s, existed FP is retrieved.'%(album_path))
			
			# Проверить актуальность существующего MdLbShrmFngp.fp по количеству FP в нем.
			# если это куе то сравнить с кол-вом треков по CUE 
			f = open(album_path+'MdLbShrmFngp.fp','r')
			l = f.readlines()
			f.close()
			print("---------------")
			for a in l:
				fp = []
				pos = a.find('.wav(')
				if pos > 0:
					f_name = a[:pos+4]
					FP_str = a[pos+4:]
					fp = eval(FP_str)
					convDL.append({"fname":f_name,"fp":fp})
				
			
			checkCueD = do_cue_2_track_split(codec_path,album_path,'is_cue')
			print(" =============retrive finished",checkCueD)
			if checkCueD['mode'] == 'cue':
				if checkCueD['orig_title_numb'] == len(convDL):
					return {'RC':len(convDL),'FP':convDL,'splitRes':None}	
				else:
					print("Error in retrieved FP file. Continue to new FP generation.")
			
		
		
	# Разбиваем на треки если это необходимо для CUE	
	if 	'convert_cue_delete' in args:
		splitRes = do_cue_2_track_split(codec_path,album_path,'convert_cue_delete')
			
	else:
		splitRes = do_cue_2_track_split(codec_path,album_path)
		print('Result CUE =',splitRes['f_numb'])
		#r=1
	# Если успешно разбили на трэки	
	convDL = []
	DirL =[]
	if splitRes['f_numb'] > 0:
		
		result = ''
		convL = []
		
		temp_dir = 'convert_cue\\'
		#print os.listdir(album_path+'convert_cue\\')
		DirL = os.listdir(album_path+'convert_cue\\')
		
		for a in DirL:
			#print 'curent file:',a
			
			if a.lower().rfind('.wav')>0:
				new_name = album_path+temp_dir+a	
				#if "pregap.wav" in new_name:
				#	print "pregap.wav --> skipped"
				#	continue
				fp = acoustid.fingerprint_file(new_name)
				result = result + a + str(fp)+"\n"
				convL.append(new_name)
				convDL.append({"fname":new_name,"fp":fp})
				print("*", end=' ')
				
	else:
	# Это уже было потрэковая компоновка без CUE	
		format = ''
		convL = []
		for a in os.listdir(album_path):
			#print a
			if a.lower().rfind('.ape')>0:
				if format != '' and format != 'ape':
					print('Mixed formats in folder: skipped ',a)
					return {'RC':0,'FP':[],'splitRes':splitRes}
				format = 'ape'	
			elif a.lower().rfind('.flac')>0:
				if format != '' and format != 'flac':
					print('Mixed formats in folder: skipped ',a)
					return	{'RC':0,'FP':[],'splitRes':splitRes}	
				format = 'flac'	
			elif a.lower().rfind('.mp3')>0:
				if format != '' and format != 'mp3':
					print('Mixed formats in folder: skipped ',a)
				format = 'mp3'
			else:
				continue
	
			new_name = album_path+a
			DirL.append(new_name)
			try:
				
				fp = acoustid.fingerprint_file(new_name)
				
				#	params = ('fpcalc',new_name)
				#	p = subprocess.Popen(params, stdout=subprocess.PIPE)
				#	r = result + p.communicate()[0]
			except Exception as e:
				print("Error in Fingerprint 5706 Probably broken file:",e,new_name)
				temp_dir = 'convert_wav\\'
				new_name = album_path+temp_dir+a+'.wav'
				if not os.path.exists(album_path+temp_dir):
					os.mkdir(album_path+temp_dir)
				r = convertLosless_2_lossy('',codec_path,{},"\""+album_path+a+"\"",'',temp_dir,'stop_and_save_wav')
				if r == -1:
					print("File is broken and be skipped:",a)
					continue
				print("Single Conversion res:",r,album_path+a)
				if os.path.exists(new_name):
					try:
						os.remove(new_name)
					except Exception as e:	
						print("Exception with remooving %s:%s"%(a,str(e)))
				try:		
					os.rename(album_path+temp_dir+'temp.wav', new_name)
				except Exception as e:	
						print("Exception with renaming %s:%s"%(a,str(e)))	
						return {'RC':-1,'FP':[],'splitRes':splitRes}
				fp = acoustid.fingerprint_file(new_name)		
				
			result = result + a + str(fp)+"\n"
			convL.append(new_name)
			convDL.append({"fname":new_name,"fp":fp})
			print("*", end=' ')
	
	res_str = ''
	if 	len(convDL) == len(DirL):
		res_str = " --OK-- "
	else:
		res_str = " some FP was not generated due to issue."
		
	print('Conversion fineshed:',len(convDL), '-->saved FP,',  len(DirL), "--> files converted.",res_str)
		
	if result != ''  and convL != []:
		f_name = album_path +temp_dir+'names.txt'
		
		s = '\n'.join(convL)
		#print "file  is ??",f_name	
		f = open(f_name,'w')
		f.write(s)
		f.close()
		#print "file  is OK",f_name
		convL.append(album_path +temp_dir+'names.txt')
		
		f = open(album_path + 'MdLbShrmFngp.fp','wb')
		f.write(result)
		f.close()		
	
	for temp_dir in ['convert_wav\\','convert_cue\\']:
		if os.path.exists(album_path+temp_dir):
			
			if len(os.listdir(album_path+temp_dir)) == 0:
				os.rmdir(album_path+temp_dir)
			else:
				for a in os.listdir(album_path+temp_dir):
					os.remove(album_path+temp_dir+a)
				
				if len(os.listdir(album_path+temp_dir)) == 0:
					os.rmdir(album_path+temp_dir)	
		
	return {'RC':len(convDL),'FP':convDL,'splitRes':splitRes}	
	
def Calculate_DiscID(cue_name):
	# Вычисляет DiscId только для CUE c реальным wav образом в ссылке
	# Для работы необходимо сгенерировать временный CUE, распаковать образ в wav и сделать ссылку в CUE на этот WAVE
	# cue файл не содержит времени трэков. врямя вычисляется как разница между предыдущим и текущим трэком
	# но для последнего трэка это невозможно, т.к. нет информации о конце файла. т.е. нужен образ для вычисления
	# последнего фрейма. А это возможно только при наличии физического образа
	
	errorLog = []
	f = open(cue_name)
	#parsedH = mktoc.parser.CueParser('.',False)
	parsedH = mktoc.parser.CueParser(dirname(cue_name),find_wav=True)
	try:
		cue = parsedH.parse(f)
	except mktoc.parser.FileNotFoundError as e:
		print('WAV not found:[%s --> is not wav] at discID calc:'%str(e))
		errorLog.append('WAV not found:[%s --> is not wav] at discID calc:'%str(e))
		return {'error_logL':errorLog}
		
	f.close()
	start_offset = 150
	result = None

	offsetL = []
	for a in  cue._tracks:
		if len(a.indexes)>1:
			track_frames = a.indexes[0].time.frames+a.indexes[1].len_.frames

		else:
			track_frames = a.indexes[0].time.frames
		offsetL.append(track_frames+start_offset)

	total = start_offset+a.indexes[0].time.frames+a.indexes[0].len_.frames
	#discID = discid.put(1,len(cue._tracks),total,offsetL)
	if discID:
		try:
			result = musicbrainzngs.get_releases_by_discid(discID,includes=["artists"])
		except musicbrainzngs.ResponseError as e:
			print('Error in musicbrainzngs get TOC:',e)
			print((1,len(cue._tracks),total,offsetL))
			errorLog.append('Error in musicbrainzngs get TOC:'+str(e))
			return {'error_logL':errorLog,'discID':discID}

		if result:
			for a in result["disc"]["release-list"][0]:
				if a == 'artist-credit':
					for b in result["disc"]["release-list"][0][a]:
						if type(b) == dict:
							print(b['artist'])
				elif a == 'id':
					print(result["disc"]["release-list"][0][a])
			return {'discID':discID,'mbResult':result}
		errorLog.append('Error (no-result) in musicbrainzngs get TOC.')	
		return {'error_logL':errorLog,'discID':discID}	
			
	else:
		return {'error_logL':['discID not calculated']}	
		
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

def identify_music_folder(init_dirL,*args):
	#print args
	logger.debug('in identify_music_folder - start [%s]'%str(init_dirL))
	music_folderL = []
	file_extL = ['.flac','.mp3','.ape']

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
				if not entry.name.startswith('.') and entry.is_file():
					#print(entry.name, os.path.splitext(entry.name)[-1])
					if os.path.splitext(entry.name)[-1] in file_extL:

						dir_name = os.path.dirname(''.join((new_folder,'/',entry.name)))
						#print(dir_name)
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
	
def find_new_music_folder(init_dirL, prev_folderL, DB_folderL,*args):
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
			print(init_dir)
			init_dirL[init_dirL.index(init_dir)] = init_dir.decode('utf8')
		else:
			if not os.path.exists(init_dir):
				print(init_dir, 'does not exists')
				return {'folder_list':[],'NewFolderL':[]}
	i = 0
	t = time.time()
	print("Folders scanning ...")
	for init_dir in init_dirL:
		for root, dirs, files in os.walk(init_dir):
			for a in dirs:
				if i%100 == 0:
					print(i, end=' ')
				i+=1
				f_l.append((root,a))
				#f_l.append(join(root,a))
	print()
	time_stop_diff = time.time()-t
	
	if prev_folderL == []:
		print('First run: Finished in %i sec'%(int(time_stop_diff)))
		if resBuf_save_file_name != '':
			f = open(f_name,'wb')
			d = pickle.dump({'folder_list':f_l,'NewFolderL':[],'music_folderL':[],'creation_time':creation_time},f)
			f.close()
			print('save buffer',f_name)
			logger.info('in find_new_music_folder - finished: Buff saved in:%s'%(f_name))
			return {'resBuf_save':f_name}
		else:
			return {'folder_list':f_l,'NewFolderL':[]}
	
	if DB_folderL != []:
		prev_folderL = list(set([os.path.join(a[0],a[1]) for a in DB_folderL]).difference(set([os.path.join(a[0],a[1]) for a in prev_folderL])))
	# Вычисление пересеченеия новых папок с последним сохраненным деревом папок
	new_folderL = list(set([os.path.join(a[0],a[1]) for a in f_l]).difference(set([os.path.join(a[0],a[1]) for a in prev_folderL])))
	#new_folderL = list(set(f_l).difference(set(prev_folderL)))
	new_folderL.sort()

	if len(new_folderL) == 0:
		print('No Change: Finished')
	elif len(new_folderL) > 0:
		print('Changes found!', len(new_folderL))
		print(new_folderL)
	# Collect music folders
	music_folderL = []
	file_extL = ['.flac','.mp3','.ape']
	
	
	for new_folder in new_folderL:
		#print "new_folder:",[new_folder]
		for root, dirs, files in os.walk(new_folder):
			
			for a in files:
				
				if os.path.splitext(a)[-1] in file_extL:
					#file_codec = chardet.detect(a)
					#file = a.decode(file_codec['encoding'])
					#print [root,a]
					dir_name = ''
					try:
						dir_name = os.path.dirname(os.path.join(root,a))
					except Exception as e:
						logger.critical('in find_new_music_folder [%s]:'%str(e))
					#print dir_name,type(dir_name)		
					#print [join(root.decode('utf8'),a.decode('utf8'))]
					if dir_name not in music_folderL:
						
						music_folderL.append(dir_name)
						#print 'dir_name:',type(dir_name),[dir_name]
						break
						
	if resBuf_save_file_name != '':
		f = open(f_name,'wb')
		d = pickle.dump({'folder_list':f_l,'NewFolderL':new_folderL,'music_folderL':music_folderL,'creation_time':creation_time},f)
		f.close()
		print('save buffer',f_name)
		logger.info('in find_new_music_folder - finished: Buff saved in:%s'%(f_name))
		return {'resBuf_save':f_name}
	
	logger.debug('in find_new_music_folder found[%s]- finished'%str(len(music_folderL)))
	return {'folder_list':f_l,'NewFolderL':new_folderL,'music_folderL':music_folderL}
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
	
def get_parent_folder_stackL(path,stop_nodeL):
	
	if not os.path.isabs(path):
		return([])	
	nodesL =[]
	
	for a in range(20):
		parent_dir = os.path.dirname(path)
		if path == parent_dir:
			break
		path = parent_dir
		if path in stop_nodeL:
			break
		nodesL.append(path)
	return(nodesL)

def path_to_posix(f_path):
	return Path(f_path).as_posix()

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
	
