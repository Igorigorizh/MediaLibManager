# -*- coding: utf-8 -*-

import time
import zlib
import datetime
import socket
import sqlite3
import urllib.request, urllib.error, urllib.parse
import operator
import json
import os

import pickle
from os import scandir
import chardet
import itertools

from os.path import join

import collections
import shutil
import subprocess
from os import curdir, sep,getcwd           
from random import randint
import logging
from bs4 import BeautifulStoneSoup

from mutagen.apev2 import APEv2, error
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.monkeysaudio import MonkeysAudioInfo
import acoustid
import mutagen

#import mktoc

import musicbrainzngs

from myMediaLib_cue import parseCue
from myMediaLib_cue import simple_parseCue
from myMediaLib_cue import GetTrackInfoVia_ext
from functools import reduce


musicbrainzngs.set_useragent("python-discid-example", "0.1", "your@mail")

from myMediaLib_CONST import BASE_ENCODING
from myMediaLib_CONST import mymedialib_cfg

#import win32security
#from ntsecuritycon import * 

logger = logging.getLogger('controller_logger.adm')
#
""""
#*************************   RPC medialib appl connectio wrapper *******************************
#************************* 1.  RPC WRAPPER ----->  Use it !!!!
#>>> import xmlrpclib
#>>> import pickle
#>>> s_appl = xmlrpclib.ServerProxy('http://127.0.0.1:9001')
#>>> s_appl.appl_status()
#>>> s = s_appl.processDic_viaKey('DB_metaIndxD_album').data
#>>> p = pickle.loads(s)p = pickle.loads(s)
#>>> print p.keys()
#************************************************************************************************
"""

""""
#*************************   Fast and simple DB connectio wrapper *******************************
#************************* 2.  WRAPPER ----->  Use it !!!!
#
#>>>  req = "select id_track,TITLE,album_crc32,path,path_crc32 from track where path like '%%%s%%' and id_track > 256000"%("http")
#>>>  for a in myMediaLib_adm.db_request_wrapper(None,req): print 'artist->',a

# ************************* 2. через sqlite
#>>> cfgD = myMediaLib_adm.readConfigData(myMediaLib_init.mymedialib_cfg)
#>>> dbPath = cfgD['dbPath']
#>>> import sqlite3
#>>> db = sqlite3.connect(dbPath)
#************************************************************************************************
"""

def Intersection(lst1, lst2): 
	return set(lst1).intersection(lst2)

def sec2hour(sec):
	return '%02i'%(int(sec/3600))+':'+'%02i'%(int(int(sec%3600)/60))+':'+'%02i'%(sec%60)+':00'
	
errorlist = { 


  200:('OK','The request is OK'), 
  201:('Created','The request is complete, and a new resource is created'), 
  202:('Accepted','The request is accepted for processing, but the processing is not complete'),
  203:('Non-authoritative Information','No Description'),  	  	 
  204:('No Content','No Description'),  	 
  205:('Reset Content','No Description'), 	 
  206:('Partial Content','No Description'),
  
  300: ('Multiple Choices','A link list. The user can select a link and go to that location. Maximum five addresses'),
  301:('Moved Permanently','The requested page has moved to a new url'),
  302:('Found','The requested page has moved temporarily to a new url '),
  303:('See Other','The requested page can be found under a different url'),
  304:('Not Modified ','No Description'),
  305:('Use Proxy','No Description'),
  306:('Unused','This code was used in a previous version. It is no longer used, but the code is reserved'),
  307:('Temporary Redirect','The requested page has moved temporarily to a new url'),
  
  400:('Bad Request','The server did not understand the request'),
  401: ('Unauthorized','The requested page needs a username and a password'),
  402: ('Payment required','No payment -- see charging schemes'),
  403: ('Forbidden','Access is forbidden to the requested page'),
  404: ('Not Found', 'The server can not find the requested page'),
  405: ('Method Not Allowed','Specified method is invalid for this server.'),
  406: ('Not Acceptable', 'URI not available in preferred format.'),
  407: ('Proxy Authentication Required', 'You must authenticate with this proxy before proceeding.'),
  408: ('Request Time-out', 'Request timed out; try again later.'),
  409: ('Conflict', 'Request conflict.'),
  410: ('Gone','URI no longer exists and has been permanently removed.'),
  411: ('Length Required', 'Client must specify Content-Length.'),
  412: ('Precondition Failed', 'Precondition in headers is false.'),
  413: ('Request Entity Too Large', 'Entity is too large.'),
  414: ('Request-URI Too Long', 'URI is too long.'),
  415: ('Unsupported Media Type', 'Entity body in unsupported format.'), 
  416: ('Requested Range Not Satisfiable','Cannot satisfy request range.'),
  417: ('Expectation Failed','Expect condition could not be satisfied.'),
  499: ('Anknown error 499','Check 499 kode.'),	
  500: ('Internal error', 'Server got itself in trouble'),
  501: ('Not Implemented','Server does not support this operation'),
  502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
  503: ('Service temporarily overloaded','The server cannot process the request due to a high load'),
  504: ('Gateway timeout','The gateway server did not receive a timely response'),
  505: ('HTTP Version not supported', 'Cannot fulfil request.')}

def isonline(reliableserver='http://www.google.com'):
	from urllib.request import urlopen
	try:
		urlopen(reliableserver)
		return True
	except IOError:
		return False

def urlopenWithCheck(inurl):
#"""Tests if a url can be reached - and prints an appropriate message depending on the result."""

	socket.setdefaulttimeout(5)
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	headers={'User-Agent':user_agent,}
	request=urllib.request.Request(inurl,None,headers)
	
	from urllib.request import urlopen
	try:
		#print inurl
		handler = urlopen(request)
		#print "zzz"
			#File "<string>", line 1, in sendall
			#UnicodeEncodeError: 'ascii' codec can't encode characters in position 34-35: ord
			#inal not in range(128)
		
	except IOError as e:
		
		
		if hasattr(e, 'reason'):
			print('Access failed before we reached a server.')
#			print 'Reason : ', e.reason
	   
			if isonline():
				mess =  "We have an internet connection - so either the server is down or doesn't exist."
				print(mess)
				return (None,998,mess)
			else: 
				mess = "We don't appear to have an internet connection - this is likely to be the source of the problem."
				print(mess)
				return (None,999,mess)
	   
		elif hasattr(e, 'code'):
			print('Url=',inurl)  				
			print('Server returned an error code.')
			print('Error Code : ', e.code)
			print('Error type : ', errorlist[e.code][0])
			print('Error msg : ', errorlist[e.code][1])
			return (None,e.code,errorlist[e.code][1])
		else:	return (None,1000,None)
	except:
		print('Strange Exeption for: ', inurl)
		return (None,1000,None)	

	
	return (handler,None,None)

def get_general_www_resource(url):
	h = urlopenWithCheck(url)
	if h[0] == None: 
		return None
	html = h[0].read()
	h[0].fp.close()
	print('connection closed:',h[0].fp.closed)
	#print dir(h)
	#print dir(h[0]),type(h[0])
	
	return html

def searchDiscDogs(obj_type,search_req,per_page_num):
	resultL=[]
	req = 'http://api.discogs.com/database/search?%s=%s&page=1&per_page=%d'%(obj_type,search_req,per_page_num)
	str_res = get_general_www_resource(req)
	print(type(str_res))
	if type(str_res) != str:

		for a in range(5):
			time.sleep(randint(10,20))
			print('Bad!!!  Wait....',a)
			str_res = get_general_www_resource(req)
			if type(str_res) != str:
				break
		if type(str_res) != str:
			return None

	res_obj = json.loads(str_res)
	page_obj = res_obj['pagination']
	page_max = page_obj['pages']
	if page_max == 1:
		return res_obj['results']


	resultL = res_obj['results']
	print(len(resultL))

	for page in range(2,page_max+1):
		req = 'http://api.discogs.com/database/search?%s=%s&page=%d&per_page=%d'%(obj_type,search_req,page,per_page_num)
		rnd = randint(10,20)
		time.sleep(rnd)
		print('ready',rnd)
		str_res = get_general_www_resource(req)
		print(type(str_res))
		if type(str_res) != str:
			
			for a in range(5):
				rnd = randint(10,20)
				time.sleep(rnd)
				print('Bad!!!  Wait....',rnd)
				print(req)
				
				str_res = get_general_www_resource(req)
				if type(str_res) == str:
					break
			if type(str_res) != str:
				return None
			else:
				res_obj = json.loads(str_res)
		else:
			res_obj = json.loads(str_res)

		page_obj = res_obj['pagination']
		print('***',page)
		print(page_obj)
		resultL+=res_obj['results']
	return	resultL

def get_radio_meta(url):
	request = urllib.request.Request(url)
	try:
		request.add_header('Icy-MetaData', 1)
		request.add_header('icy-name', 1)
		request.add_header('Stream-name', 1)
		response = urllib.request.urlopen(request)
		icy_metaint_header = response.headers.get('icy-metaint')
		name = response.headers.get('icy-name')
		if icy_metaint_header is not None:
			metaint = int(icy_metaint_header)
			read_buffer = metaint+255
			content = response.read(read_buffer)
			title = content[metaint:].split("'")[1]
			return {"title":title,"headers":response.headers,"St Name":name}
	except:
		return None	
	
def collectMBData(artistL):
	artistD = {}
	# q = Query()
	# for artist_name in artistL:
		# try:
			# f = ArtistFilter(artist_name, limit=5)
			# artistResults = q.getArtists(f)
		# except WebServiceError, e:
			# print 'Error:', e
		# artistD[artist_name] = artistResults
		# time.sleep(1)
		# print '*',
	return	artistD	

	
def get_free_drive():
	for a in 'FGHIJKLMNOPQRSTUVWXUZ':
		if not os.path.exists(a+':\\'):
			return a	
	
def getMyMediaLibStat_Lists(medialibObj):
	context=medialibObj.getMediaLibPlayProcessContext()
	try:
		plL = getPlaylistsfromXML(context['mlXMLPath'])
	except NameError:
		pass
		#import myMediaLib
		#plL = myMediaLib.getPlaylistsfromXML(context['mlXMLPath'])
	mlPath = context['playlistpath']+'Plugins\\ml\\'
	listD = {}
	for a in list(plL.keys()):
		#l = winamp_old.getTrackList(mlPath + a)
		l = winamp.getTrackList(mlPath + a)
		for b in l[1:]:
			try:
				crc32 = zlib.crc32(b.lower())
			except:
				print('CRC32 Error creation:',b)
				continue
				
			pos = b.lower().rfind('\\')
			try:
				
				crc32_d=zlib.crc32(b.lower()[:pos].encode(BASE_ENCODING))
			except Exception as e:
				logger.critical('in getMyMediaLibStat_Lists %s'%(str(e)))
				print('2:',b)
				#return b
				continue
			#print b.lower()[:pos]
			#if crc32_d == 406082769:
			#	print b.lower()[:pos]
			if crc32 in listD:
				#listD[crc32]['num']=listD[crc32]['num']+1
				
				if a not in listD[crc32]['list']:
					listD[crc32]['list'].append(a)
					continue
				listD[crc32]['num']=listD[crc32]['num']+1	
				listD[crc32]['album_crc32'] =crc32_d
			else:
				listD[crc32]= {'num':1,'file':b,'list':[a,],'album_crc32':crc32_d}
	return listD

def getMedialibCoverage(listD,folderD,*args):
	cnt = 0
	missedL = []
	fullAlbum_missedL = []
	for a in folderD['allmFD']:

		if a in listD:
			cnt+=1
		else:
			missedL.append(a)
	albumD = {}
	for a in missedL:
		if folderD['allmFD'][a]['album'] not in albumD:
			albumD[folderD['allmFD'][a]['album']] = [a]
		else:
			albumD[folderD['allmFD'][a]['album']].append(a)
	print('Ok entries-->',cnt, 'missed songs:', len(missedL), 'missed albumes:',len(albumD),'total in folder:',len(folderD['allmFD']))
	outputStr = 'Ok entries--> %-10d, missed songs:%-10d,missed albumes:%-10d,total in folder:%-10d'%(cnt,len(missedL),len(albumD),len(folderD['allmFD']))

	
	
	sL = list(albumD.keys())
	sL.sort()
	resOutputL = []
	#full_missed_cnt = 0
	full_missedL = []
	for a in sL:
		if getMissedFileInfo(listD,folderD,albumD[a][0],'only_missed_check') == 1:
			#full_missed_cnt +=1
			full_missedL.append('%-4d: %-5d: %s: %s'%(sL.index(a),len(albumD[a]),a[:a.rfind('\\')],','.join([str(b) for b in albumD[a][:1]])))	
		if 'print_res' in args:
			print(a, len(albumD[a]),albumD[a][:3])
		resOutputL.append('%-4d: %-5d: %s: %s'%(sL.index(a),len(albumD[a]),a,','.join([str(b) for b in albumD[a][:3]])))	
	
	return {'albumD':albumD,'missedL':missedL,'outputStr':outputStr,'resOutputL':resOutputL,'full_missedL':full_missedL}

def getMissedFileInfo(listD,folderD,fileCRC32,*args):
	outputStr = ''
	outputStr = outputStr + 'Album: %s, CRC32: %s \n'%(folderD['allmFD'][fileCRC32]['album'],str(folderD['allmFD'][fileCRC32]['album_crc32']))
	outputStr = outputStr +  'Checked File:%s \n'%(folderD['allmFD'][fileCRC32]['file'],)
	outputStr = outputStr + '\n'
	pListFile_CRC32_L = []
	if 'short_info' not in args:
		outputStr = outputStr +  'List Info:\n'
	if folderD['allmFD'][fileCRC32]['album_crc32'] in [listD[a]['album_crc32'] for a in listD]:
		if 'short_info' not in args:
			outputStr = outputStr +  'List has following files\n'
		pListFileL = [(listD[a]['file'],a) for a in listD if listD[a]['album_crc32'] == folderD['allmFD'][fileCRC32]['album_crc32']]
		pListFile_CRC32_L = [a for a in listD if listD[a]['album_crc32'] == folderD['allmFD'][fileCRC32]['album_crc32']]
		if pListFileL != []:
			pListFileL.sort()
			for a in pListFileL:
				if 'short_info' not in args:
					outputStr = outputStr +  '%3s. %-11s %s\n'%(pListFileL.index(a),a[1],a[0])
		else:
			outputStr = outputStr + 	'************ ---> List does not have any files related to the folder CRC32 - 1\n'

	else:
		outputStr = outputStr +  '************ ---> List does not have any files related to the folder file CRC32 - 2\n'

	outputStr = outputStr + '\n'
	outputStr = outputStr +  'Folder missed files check:\n'
	FolderFileL = [(folderD['allmFD'][a]['file'],a) for a in folderD['allmFD']  if folderD['allmFD'][a]['album_crc32'] == folderD['allmFD'][fileCRC32]['album_crc32']]
	FolderFileL.sort()
	
	FolderFile_CRC32_L = [a for a in folderD['allmFD']  if folderD['allmFD'][a]['album_crc32'] == folderD['allmFD'][fileCRC32]['album_crc32']]

	missedL = []
	missedL = [a for a in FolderFile_CRC32_L if a not in pListFile_CRC32_L]
	
	if 'only_missed_check' in args:
		if len(missedL) == len(FolderFile_CRC32_L):
			return 1
		else:
			return 0
	if missedL != []:
		outputStr = outputStr +  '----------->>>  Folder files found missed--> %d of %d\n'%(len(missedL),len(FolderFile_CRC32_L) )
		l = [(folderD['allmFD'][a]['file'],a) for a in missedL]
		l.sort()
		for a in l:
			outputStr = outputStr +  '%3s. %-11s %s\n'%(l.index(a),a[1],a[0])


	else:
		outputStr = outputStr +  '----------->>>  Folder and List Files are OK! <<<< ---------------------:'

	outputStr = outputStr + '\n'
	if 'short_info' not in args:
		outputStr = outputStr +  'Folder files:\n'

	if FolderFileL != []:
		
		for a in FolderFileL:
			if 'short_info' not in args:
				outputStr = outputStr +  '%3s. %-11s %s\n'%(FolderFileL.index(a),a[1],a[0]) 
				
	else:
		outputStr = outputStr +  '************ ---> FolderD does not have any files related to the folder CRC32\n'
	return outputStr
	
def collectAllMetaData(allmFD):
	# досбор метаданных на основе уже предварительно собранных ранее.
	# ПРИНЦИПИПИАЛЬНО! Изменена концепция вычисления CRC32 трэка для CUE при переходе на MPD
	# теперь за основу берется оригинальный медиа файл и к нему добавляется номер трэка - от этого считается CRC32 
	# это требует рефакторинга начальной сборки метаданных для CUE и cue tracKS
	logger.debug('in collectAllMetaData len->allmFD[%s]- start'%str(len(allmFD)))
	cnt = 0
	cueCRC32D =  {}
	cueD = {}
	errorLog = []
	for a in allmFD:
		print("*", end=' ')
		cnt +=1
		# Проверка на CUE
		if 'cue' in allmFD[a]:
			ftype = allmFD[a]['ftype']
			cue_num_pos = allmFD[a]['file'].rfind(b",")
			cue_num = ''
				
			if cue_num_pos >=0:
				cue_num=allmFD[a]['file'][cue_num_pos+1:] 
				
			#cueFile = allmFD[a]['file'][:cue_num_pos]
			cue_num = allmFD[a]['cueNameIndx']
			cueFile = allmFD[a]['cue_f_name_abs']
			
			cueCRC32 = zlib.crc32(cueFile)
			
			if cueCRC32 in cueCRC32D:
				cueD = cueCRC32D[cueCRC32]
			else:	
				filename = ''
				#print cueFile
				try:
					filename = cueFile
				except UnicodeDecodeError:
					filename = cueFile
					#print cueFile
					#continue
				#try:
				
				try:	
					cueD = parseCue(filename,'with_bitrate')
					if 'Error' in cueD:
						print("Error in parseCue -> skip")
						logger.critical('Exception 669 in collectAllMetaData after parseCue: %s'%(str(e)))		
						continue
						
				
				
				except Exception as e:
					print(e)
					print([filename], type(filename))
					#import myMediaLib	
					#cueD = myMediaLib.parseCue(filename)
					
				cueCRC32D[cueCRC32] = cueD

			try:
				print('before time calc',)
				time_sec = int(cueD['trackD'][int(cue_num)]['Time'].split(':')[0])*60+int(cueD['trackD'][int(cue_num)]['Time'].split(':')[1])

				allmFD[a]['metaD'] = {'album':cueD['trackD'][int(cue_num)]['Album'], 'artist':cueD['trackD'][int(cue_num)]['Performer']	,'artist_CRC32':cueD['trackD'][int(cue_num)]['Performer_CRC32'], 'title':cueD['trackD'][int(cue_num)]['Title'], 'ftype':cueD['fType'], 'time':cueD['trackD'][int(cue_num)]['Time'],'time_sec':time_sec,'pos_num':cue_num, 'tracknumber':cue_num,'bitrate':cueD['trackD'][int(cue_num)]['BitRate']} 	
			except KeyError as e:
				print('KeyError', e)
				logger.critical('Exception 688 in collectAllMetaData after parseCue: %s'%(str(e)))	
				print('expetion ok',a)
				errorLog.append({'message':'collectAllMetaData: Error after parseCue args','args':filename,'cueD':cueD,'cue_num':cue_num,'key':a,'data':allmFD[a]})
				
				continue
				return cueD[int(cue_num)],a,allmFD[a]
					
			if cueD == None:
				del cueCRC32D[int(cue_num)]
				continue
			continue
			
		if 'orig_fname' not in allmFD[a]:
			logger.critical('Error:  712 in collectAllMetaData Not CUE? no orig_fname in allmFD for index : %s'%(str(a)))	
			errorLog.append({'message':'collectAllMetaData: Error no orig_fname args','args':'','cueD':cueD,'key':a,'data':allmFD[a]})
			logger.debug('in collectAllMetaData - Error finished')	
			return {'errorLog':errorLog}
			
		try:
			origname = 	allmFD[a]['orig_fname']
			#print 'origname:',[origname]
		except UnicodeDecodeError as e:
			logger.critical('Exception in collectAllMetaData: %s'%(str(e)))	
			print(e, type(allmFD[a]['orig_fname']),[allmFD[a]['orig_fname']],a)
			#origname = 	allmFD[a]['orig_fname']
		except UnicodeEncodeError as e:	
			logger.critical('Exception in collectAllMetaData: %s'%(str(e)))	
			origname = 	allmFD[a]['orig_fname']
			print(e,type(allmFD[a]['orig_fname']),[allmFD[a]['orig_fname']],a)
		except TypeError as e:		
			print(e,a)
		
		# Сбор метаданных для НЕ CUE 
		try:	
			logger.debug('in collectAllMetaData: before GetTrackInfoVia_ext call: filename %s'%(str([origname])))
			metaD = GetTrackInfoVia_ext(origname,allmFD[a]['ftype'])
		except Exception as e:
			logger.critical('Exception in collectAllMetaData: %s'%(str(e)))
			errorLog.append({'message':'collectAllMetaData: Error after GetTrackInfoVia_ext args','Error':str(e),'args':origname,'key':a,'data':allmFD[a]})
			continue
		artist = ''
		
		artist = metaD['artist']
			
		try:						
			metaD['artist_CRC32']= zlib.crc32(metaD['artist'].lower().strip().encode(BASE_ENCODING))
		except Exception as e:
			logger.critical('Exception in collectAllMetaData: %s'%(str(e)))
			metaD['artist_CRC32']=999
			print('crc32 error:',artist)
			errorLog.append({'message':'collectAllMetaData: Error after crc32','Error':str(e),'args':origname,'key':a,'data':allmFD[a],'metaD':metaD,'artist':artist})
			
		metaD['pos_num'] = None
		#metaD['cueNameIndx'] = None
		allmFD[a]['metaD'] = metaD
		if cnt % 100 == 0:
			print('.',cnt, end=' ')
			
	logger.debug('in collectAllMetaData - finished')	
	return {'errorLog':errorLog}	
	
def getTableInfo(tab_name,db):
	tabD = {}
	c = db.cursor()
	req = "pragma table_info('%s')"%(tab_name,)
	#print req
	c.execute(req) 
	l = c.fetchall()
	#print l[0]
	#try:
	for a in l:
		tabD[a[0]] = {'field_name':str(a[1]),'pos':a[0],'type':str(a[2])}

	#except:
		#print 'wrong tab name:',tab_name
	return 	tabD
	
def getVirtualAlbum_Indexes(db,*args):	
	#db = sqlite3.connect(dbPath)
	if db != None:
		#db.text_factory = str
		pass
	else:
		print('Error in: getVirtualAlbum_Indexes')
	c = db.cursor()
	virt_album_indxD = {}
	album_indxD = {}
	
	req = """select album_crc32,album_crc32_ref,rel_type from album_REFERENCE"""
	c.execute(req)
	l =c.fetchall()
	
	for a in l:
		album_indxD[a[0]] = {'key':a[0],'key_ref':a[1],'rel_type':a[2]}
	relL = [ a[0] for a in l]
	
	if relL != []:
		req = 'select path_crc32,path from ALBUM where path_crc32 in (%s)'%(str(relL)[1:-1])
		c.execute(req)
		l_alb =c.fetchall()
	for a in l_alb:
		if a[1] == '':
			continue
		virt_album_indxD[album_indxD[a[0]]['key_ref']] = {'ref_to_key':a[0],'rel_type':album_indxD[a[0]]['rel_type'],'ref_to_path':a[1]}	
	
	c.close()
#	db.close()
	return virt_album_indxD

def getAlbumArtist_dbId_CRC32_mapping(db,*args):	
	logger.debug('in getAlbumArtist_dbId_CRC32_mapping - Start')
	db_init_flag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)		
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)
		db_init_flag = True
		
	indxAlbumD = {}
	indxArtistD = {}
	
	c = db.cursor()
	reqD = {}
	reqD['album'] = 'select id_album, path_crc32 from album'
	reqD['artist'] = 'select id_artist, artist_crc32 from artist'
	for key in reqD:
		
		try:	
			r = c.execute(reqD[key])
		except Exception as e:
			print(e)
			logger.critical('Exception: %s'%(str(e)))	
		
		#print reqD[key]
		try:	
			l = c.fetchall()
		except Exception as e:
			print(e)
			logger.critical('Exception: %s'%(str(e)))
			c.close()
			db_encode = db.text_factory
			#db.text_factory = str
			c = db.cursor()	
			try:
				r = c.execute(req)
				l = c.fetchall()
				#db.text_factory = db_encode
			except Exception as e:
				print('Error 2 db encode:',e)
				logger.critical('Exception2: %s'%(str(e)))	
				return 	{'Error:': str(e)}
	
		for a in l:
			if key == 'album':
				indxAlbumD[int(a[1])] = int(a[0])
			elif key == 'artist':
				indxArtistD[int(a[1])] = int(a[0])
	
	logger.debug('in getAlbumArtist_dbId_CRC32_mapping - Finish')
	c.close()
	if db_init_flag:
		db.close()
	return {'indxAlbumD':indxAlbumD,'indxArtistD':indxArtistD}
	
def getMedialibDb_Indexes(db,*args):
	logger.debug('in getMedialibDb_Indexes - Start')
	db_init_flag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)		
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)
		db_init_flag = True
		
	indxD = {}
	c = db.cursor()
	
	#print "getMedialibDb_Indexes -1"
	
	if 'ignoring' in args:
		req = 'select id_track, path_crc32, last_modify_date, album_crc32, artist_crc32, title,artist,album from track where ignore is NULL'
	else:
		req = 'select id_track, path_crc32, last_modify_date , album_crc32 from track'
		
	#print "getMedialibDb_Indexes -2"	
	try:	
		r = c.execute(req)
	except Exception as e:
		print(e)
		logger.critical('Exception: %s'%(str(e)))	
		
	#print "getMedialibDb_Indexes -3"		
	try:	
		l = c.fetchall()
	except Exception as e:
		print(e)
		logger.critical('Exception: %s'%(str(e)))
		c.close()
		db_encode = db.text_factory
		#db.text_factory = str
		c = db.cursor()	
		try:
			
			r = c.execute(req)
			l = c.fetchall()
			db.text_factory = db_encode
		except Exception as e:
			print('Error 2 db encode:',e)
			logger.critical('Exception2: %s'%(str(e)))	
			return 	{'Error:': str(e)}
	
	#print "getMedialibDb_Indexes -4",len(l)	
	c.close()
	if db_init_flag:
		db.close()
	if 'ignoring' in args:	
		for a in l:
			try:
				#id_track - 0, path_crc32 - 1, last_modify_date - 2, album_crc32 - 3, artist_crc32 - 4, title -5,artist - 6,album - 7, TAA - - 8'
				indxD[int(a[1])] = (int(a[0]),float(a[2]),int(a[3]),int(a[4]),a[5],a[6],a[7],(a[5]+' '+a[6]+' '+a[7]).lower())
			except TypeError:
				indxD[int(a[1])] = (int(a[0]),0,int(a[3]),int(a[4]),a[5],a[6],a[7],(a[5]+' '+a[6]+' '+a[7]).lower())
	else:
		for a in l:
			try:
				#id_track - 0, path_crc32 - 1, last_modify_date - 2, album_crc32 - 3, artist_crc32 - 4, title -5,artist - 6,album - 7, TAA - - 8'
				indxD[int(a[1])] = (int(a[0]),float(a[2]),int(a[3]))
			except TypeError:
				indxD[int(a[1])] = (int(a[0]),0,int(a[3]))
			
	logger.debug('in getMedialibDb_Indexes - Finished')		
	return indxD	
	
def getMedialibAlbum_Indexes(indxD,db):
	albumD = {}
	metaD = {}
	for a in indxD:
		if indxD[a][2] in albumD:
			continue
		else:
			albumD[indxD[a][2]] = indxD[a][0]
			
			
	idL = [albumD[a] for a in albumD]	
	emptyPathL =[]	
	addAlbumD ={}
	
	metaL = getCurrentMetaData_fromDB_via_DbIdL_alterntv(idL,db)					
	#print 'metaD:',len(metaD)
	
	for a in metaL:
		pos = a[6].rfind('\\')
		path = a[6][:pos+1]
		if path != "":
			albumD[a[5]] = a[6][:pos+1]
		else:
			#print a[5],"path is empty"
			emptyPathL.append(a[5])
			
	if len(emptyPathL) > 0:
		req = "select path_crc32,path from ALBUM where path_crc32 in (%s)"%str(emptyPathL)[1:-1]
		resL  = db_request_wrapper(db,req)
		
		#print 'resL:',resL
		for a in resL:
			albumD[a[0]] = a[1]
		
	#for a in albumD:
	#	print a,albumD[a]
	return albumD
	
	
def correctMediaLibDb_CRC32():
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	
	c = db.cursor()
	req = 'select id_track, path ,path_crc32,cue_num, cue_fname  from track'
	r = c.execute(req)
	l = c.fetchall()
	
	
	for a in l:
		
		if a[3] == None:
			crc32 = zlib.crc32(a[1])
		else:
			crc32 = zlib.crc32(a[4]+','+str(a[3]))
			
	
		req_ins = """update track set path_crc32 = "%s" where id_track = %s"""%(crc32,a[0])	
		c.execute(req_ins)
		
	db.commit()
	c.close()
	db.close()
	print('OK')
	return l
	
	
def saveLibClast_to_DB(dbPath,allmFD,*args):
	logger.info('in saveLibClast_to_DB dir - Start')
	insL = []
	updL = []
	if 'save' in args:		
		db = sqlite3.connect(dbPath)
		c  = db.cursor()
		#db.text_factory = str
	cnt = 0
	for a in allmFD:
		cnt += 1
		if cnt%1000 == 0:
			if 'save' in args:		
				db.commit()
			print('.',cnt, end=' ')
		tag_nameD = {'title':'','album':'','artist':''}	
		for tag in tag_nameD:	
			try:
				#print 'origional:',allmFD[a]['metaD'][tag],
				tag_nameD[tag] = str(allmFD[a]['metaD'][tag])
				#print 'Ok1'
			except UnicodeEncodeError as e:
				try:
					#print 'errror at saving3'
					tag_nameD[tag] = allmFD[a]['metaD'][tag].encode('utf8')
					#print 'Ok2',
				except UnicodeEncodeError as e:
					print('errror at saving4',e,tag_nameD[tag])
					logger.critical('in saveLibClast_to_DB dir - errror at saving 1199')
					tag_nameD[tag] = allmFD[a]['metaD'][tag]
					print('Ok3')
				except:
					print('errror at saving',tag_nameD[tag])
					logger.critical('in saveLibClast_to_DB dir - errror at saving 1203')
					tag_nameD[tag] = tag_nameD[tag].encode('cp1251')
					print('Ok4')
					#title = title
					
			except UnicodeDecodeError:
				print('errror at saving2',tag_nameD[tag]) 
				logger.critical('in saveLibClast_to_DB dir - errror at saving 1210')
			except KeyError as e:
				print(e,allmFD[a])
				if 'save' in args:		
					c.close()
					db.close()
				return
			try:
				if tag_nameD[tag][-1]=='\x00':
					tag_nameD[tag] = tag_nameD[tag][:-1]
					#print 'Ok5'
			except IndexError as e:
				tag_nameD[tag] = ''
				
		
			tag_nameD[tag] = tag_nameD[tag].replace('"',"'")
			#print 'Prepared:',tag,tag_nameD[tag]
		#fname = allmFD[a]['orig_fname'].replace("'","''")
		t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
		try:
			rec = (allmFD[a]['orig_fname'],a,tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
			allmFD[a]['metaD']['artist_CRC32'],\
			allmFD[a]['album_crc32'],allmFD[a]['metaD']['pos_num'],\
			allmFD[a]['last_modify_date'],allmFD[a]['cueNameIndx'],allmFD[a]['metaD']['bitrate'],
			allmFD[a]['metaD']['time'].strip(),t_date)
			#rec = rec.replace("'","''")
		except KeyError as e:
			#cnt+=1
			print('error at praparation saving in db:',e,a)
			logger.critical('in saveLibClast_to_DB dir - errror at saving 1240')
			#allmFD[a]['metaD']
			continue
			

		#rec = rec.replace("'","''")

		#req_ins = """insert into track (path,title,artist_crc32,album_crc32) values ("QuotedStr(%s)","QuotedStr(%s)",%s,%s)"""%rec
		# CREATE TABLE track (id_track INTEGER PRIMARY KEY AUTOINCREMENT, title varchar(256), artist varchar(128),album varchar(128) artist_crc32 integer,album_crc32 integer, path varchar(300),path_crc32 integer, last_modify_date float )
		# alter table track add column last_modify_date float

		#req_ins = """insert into track (path,title,artist_crc32,album_crc32) values ("+ QuotedStr(%s) + "," + QuotedStr(%s) + ",%s,%s)"""%rec
		rec_m = None
		
		try:
			if 'db_id' not in allmFD[a]:
				if allmFD[a]['metaD']['pos_num'] != None:
					req_ins = """insert into track (path,path_crc32,title,album,artist,artist_crc32,album_crc32,cue_num,last_modify_date,cue_fname,bitrate,time_str,add_date) values ("%s",%s,"%s","%s","%s",%s,%s,%s,%s,"%s",%s,"%s","%s") """%rec
				else:
					rec = (allmFD[a]['orig_fname'],a,tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],	allmFD[a]['album_crc32'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),t_date)
					req_ins = """insert into track (path,path_crc32,title,album,artist,artist_crc32,album_crc32,last_modify_date,bitrate,time_str,add_date) values ("%s",%s,"%s","%s","%s",%s,%s,%s,%s,"%s","%s")"""%rec
			else:
				if allmFD[a]['metaD']['pos_num'] != None:
					rec_m = (tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],allmFD[a]['album_crc32'],allmFD[a]['metaD']['pos_num'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),t_date,\
					allmFD[a]['db_id'])	
					req_ins = """update track set title = "%s", album  = "%s", artist = "%s", artist_crc32  = %s ,album_crc32  = %s, cue_num = %s, last_modify_date = %s, bitrate = %s, time_str = "%s", add_date= "%s" where id_track = %s"""%rec_m
				else:
					rec_m = (tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],allmFD[a]['album_crc32'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),t_date,\
					allmFD[a]['db_id'])	
					req_ins = """update track set title = "%s", album  = "%s", artist = "%s", artist_crc32  = %s ,album_crc32  = %s, last_modify_date = %s ,bitrate = %s, time_str =
 "%s", add_date = "%s" where id_track = %s"""%rec_m
				updL.append(allmFD[a]['db_id'])
		except TypeError as e:
			print('Error at insertint modifying:',e)
			logger.critical('in saveLibClast_to_DB dir - errror at saving 1280')
			print('req_m:',rec_m,'cnt:',cnt,'key=',a,'db_id in allmFD[a]:',('db_id' in allmFD[a]))
			print(allmFD[a])
			#continue
			return

		try:
			if 'save' in args:		
				r = c.execute(req_ins)
				lastrowid  = c.lastrowid
				logger.info('in saveLibClast_to_DB dir - Saved OK. LastrowID:%s'%(str(lastrowid)))
				if lastrowid != None:
					insL.append(c.lastrowid)
				
					
		except sqlite3.OperationalError as e:
			print(cnt,':',req_ins)
			print('SQl Error:',e)
			logger.critical('in saveLibClast_to_DB dir - errror at saving Sql Error 1298')
			continue
			if 'save' in args:		
				c.close()
				db.close()
			return
	if 'save' in args:		
		db.commit()
		#lastRowId = c.lastrowid
		c.close()
		db.close()
		print('lastRowIdL = ',updL,insL)
		logger.info('in saveLibClast_to_DB dir - Finished')
		return {'updL':updL,'insL':insL}

def validate_ArtistAlbumLibClast_from_DB(dbPath,album_artistD,*args):
	# Проверка удаления/создания/модификации совокупопности альбом,артист, трэк; совокупность удаляется модифициуется только
	# если add_date одинаковая у всех объектов, т.е. они были созданы в один день
	# + модификация album_artistD новым значением DB_ID, установка track_add_date для альбома, если альбома еще нет
	logger.info('in validate_ArtistAlbumLibClast_from_DB - Start')		
	
	album_remove = False
	album_remove = False
	remove_check = True
	track_album_ref_ok = False
	action = True
	action_info = ''
	
	album_modify = False
	artist_modify = False
	track_ref_ok = False
	track_add_date = album_add_date = artist_add_date = None
	ins_alb_L = []
	upd_alb_L = []
	del_alb_L = []
	del_art_L = []
	ref_track_L = []
	
	ins_art_L = []
	upd_art_L = []
	cr_upd_art_L = []
	track_add_dateL = []
	insL = []
	updL = []
	reqD = {}
	reqD['album'] = {'req':'select id_album, add_date from album where path_crc32 = %s', 'action':''}
	reqD['artist_list'] = {'req':'select id_artist, add_date from artist where artist_crc32 in (%s)', 'action':''}
	reqD['artist'] = {'req':'select id_artist, add_date from artist where artist_crc32 = %s', 'action':''}
	reqD['track'] = {'req':'select id_track, add_date from track where album_crc32 = %s', 'action':''}
	reqD['track_tag'] = {'req':'select id_track  from track_tag where id_track = %s', 'action':''}
	reqD['album_cat_rel'] = {'req':'select id_album from album_cat_rel where album_crc32 = %s', 'action':''}
	reqD['album_reference'] = {'req':'select id_album from album_reference where album_crc32 = %s or album_crc32_ref = %s', 'action':''}
	reqD['artist_cat_rel'] = {'req':'select id_artist from artist_cat_rel where artist_crc32 = %s', 'action':''}
	reqD['artist_reference'] = {'req':'select id_artist from artist_reference where artist_crc32 = %s or artist_crc32_ref = %s', 'action':''}
	
	
	for alb_key in album_artistD:
		# Track checking DB only makes sence when remooving all: tracks-album-artist-alb_art_rel
		track_add_dateL = []
		track_add_date = album_add_date = artist_add_date = None
		
		#if 'remove_check' in args:
		req = reqD['track']['req']%(str(alb_key))
		resL = db_request_wrapper(None,req)
		if resL == []:
			logger.warning('in validate_ArtistAlbumLibClast_from_DB track ref empty - in DB [%s]'%(str(alb_key)))		
			logger.warning('in validate_ArtistAlbumLibClast_from_DB track ref empty - request: [%s]'%(req))
		else:
			track_album_ref_ok = True
			
			for track in resL:
				req = reqD['track_tag']['req']%(str(track[0]))
				res_trackL = db_request_wrapper(None,req)
				if res_trackL !=[]:
					action = False
					
					return {'updL':updL,'insL':insL,'ins_alb_L':ins_alb_L,'upd_alb_L':upd_alb_L,'ins_art_L':ins_art_L,'cr_upd_art_L':cr_upd_art_L,'del_alb_L':del_alb_L,'del_art_L':del_art_L,'ref_track_L':ref_track_L,'action':action,'action_info':'track_tag_exists: entry for TAG and Track'}
				
			for track_item in resL:
				ref_track_L.append(track_item[0])
				track_add_dateL.append(track_item[1])
					
			logger.debug('in validate_ArtistAlbumLibClast_from_DB track ref OK - in DB [%s]'%(str(alb_key)))		
			print('track_add_dateL:',track_add_dateL)
			if track_add_dateL != []:
				if track_add_dateL.count(track_add_dateL[0]) == len(track_add_dateL):
					track_add_date = track_add_dateL[0]
					logger.debug('in validate_ArtistAlbumLibClast_from_DB from track restore date is OK [%s]'%(str(track_add_date)))
		print('track_add_date',track_add_date,track_album_ref_ok)		
			
		# Album checking DB
		req = reqD['album']['req']%(str(alb_key))
		#print req 
		resL = db_request_wrapper(None,req)
		
		# Album is not found in DB -> tobe created with date from track_add_date
		if resL == []:
			album_artistD[alb_key]['isDB'] = False
			if track_add_date:
				album_artistD[alb_key]['add_date'] = track_add_date
			else:
				album_artistD[alb_key]['add_date'] = ''
			
		print('album_db_check',resL)
		for album_item in resL:
		# album_artistD - Album setting DB
			db_id = album_item[0]
			album_artistD[alb_key]['db_id'] = album_item[0]
			album_add_date = album_item[1]
			album_artistD[alb_key]['isDB'] = True
			
			logger.debug('in validate_ArtistAlbumLibClast_from_DB album - in DB [%s]'%(str(alb_key)))		
			print(album_item,album_artistD[alb_key]['db_id'])
		
		if 'remove_check' in args:
			remove_check = True
			if album_add_date == track_add_date:
				req = reqD['album_cat_rel']['req']%(str(alb_key))
				#INSERT INTO "ALBUM_CAT_REL" ("id_album", "id_object", "album_name", "object_name", "album_crc32", "rel_type") VALUES (3503, 7, 'Antonio Vivaldi: Concerti per Fagotto e Oboe (Sonatori de la Giosiosa Marca)', 'CLASSICL', 2017292393, 'general_categ')
				print('----->','*'*50)
				print(req)
				resL = db_request_wrapper(None,req)
				print("album_refer validation album_cat_rel:",resL)
				if resL != []:
					remove_check = False
				logger.debug('in validate_ArtistAlbumLibClast_from_DB album_cat_rel check %s'%(str(resL)))		
				logger.debug('in validate_ArtistAlbumLibClast_from_DB album_cat_rel check %s'%(req))		
				print('----->','^'*50)
				req = reqD['album_reference']['req']%(str(alb_key),str(alb_key))
				print(req)
				resL = db_request_wrapper(None,req)
				print("album_refer validation album_reference:",resL)
				logger.debug('in validate_ArtistAlbumLibClast_from_DB album_reference check %s'%(str(resL)))		
				logger.debug('in validate_ArtistAlbumLibClast_from_DB album_reference check %s'%(req))		
				if album_artistD[alb_key]['isDB'] and remove_check:
					album_remove = True
					del_alb_L.append(album_artistD[alb_key]['db_id'])
					
				
				print('add_date tr,alb',track_add_date,track_album_ref_ok,album_remove)	
				action = remove_check	
				
		if not action:
		# Если action на этом этапа уже False, дальнейшая логика не имеет смысла => выход
			return {'updL':updL,'insL':insL,'ins_alb_L':ins_alb_L,'upd_alb_L':upd_alb_L,'ins_art_L':ins_art_L,'cr_upd_art_L':cr_upd_art_L,
			'del_alb_L':del_alb_L,'del_art_L':del_art_L,'ref_track_L':ref_track_L,'action':action}
		
		# Артистов собрать в список и запускать 1-ну проверку запрос по списку
		#artL = [art_key for art_key in album_artistD[alb_key]['artistDataD']]
		print('artist_db_check')
		for art_key in album_artistD[alb_key]['artistDataD']:
			resL = []
			req = reqD['artist']['req']%(str(art_key))
			print('art_key:',art_key)
			resL = db_request_wrapper(None,req)
			if resL == []:
				print('crt-date_check-1',art_key)
				if 'create_update_check' in args:
					print('crt-date_check-2',art_key)
					
					if track_add_date:
						artist_add_date = track_add_date
					else:
						artist_add_date = ''
					cr_upd_art_L.append({'action':'create','artist_crc32':art_key,'alb_key':alb_key,'add_date':artist_add_date, 'db_id':''})
					logger.warning('in validate_ArtistAlbumLibClast_from_DB artist - NOT in DB [%s]'%(str(art_key)))		
			else:
				if 'create_update_check' in args:
					print('crt-date_check-3',art_key)
					cr_upd_art_L.append({'action':'update','artist_crc32':art_key,'alb_key':alb_key,'add_date':'', 'db_id':resL[0][0]})
				if 'remove_check' in args:
					if track_add_date == resL[0][1]:
						del_art_L.append({'id_album':album_artistD[alb_key]['db_id'],'id_artist':resL[0][0]})
						logger.debug('in validate_ArtistAlbumLibClast_from_DB artist - in DB [%s]'%(str(art_key)))
					else:
						logger.warning('in validate_ArtistAlbumLibClast_from_DB artist [%s] - in DB but not OK tobe delete add_date [%s]/[%s]'%(str(art_key),str(resL[0][1]),str(track_add_date)))
				
		print('cr_upd_art_L/del_art_L',cr_upd_art_L,del_art_L)
	
	logger.info('in validate_ArtistAlbumLibClast_from_DB - Finish')	

	return {'updL':updL,'insL':insL,'ins_alb_L':ins_alb_L,'upd_alb_L':upd_alb_L,'ins_art_L':ins_art_L,'cr_upd_art_L':cr_upd_art_L,
			'del_alb_L':del_alb_L,'del_art_L':del_art_L,'ref_track_L':ref_track_L,'action':action}	
		
def saveLibClast_to_DB_unicode(dbPath,allmFD,album_artistD,add_date,*args):
	logger.info('in saveLibClast_to_DB_unicode - Start')
	insL = []
	ins_alb_L = []
	upd_alb_L = []
	ins_art_L = []
	upd_art_L = []
	album_modify = False
	artist_modify = False
	artist_tobe_createL = []
	cue_f_name_rel = None
	updL = []
	reqD = {}
	reqD['album'] = {'req':'select id_album from album where path_crc32 = %s', 'action':''}
	reqD['artist_list'] = {'req':'select id_artist from artist where artist_crc32 in (%s)', 'action':''}
	reqD['artist'] = {'req':'select id_artist from artist where artist_crc32 = %s', 'action':''}
	reqD['track'] = {'req':'select id_track from track where path_crc32 in (%s)', 'action':''}
	if album_artistD == None:
		album_artistD = getAlbumArtista_from_allMetaData(allmFD)	
		
	validateD = validate_ArtistAlbumLibClast_from_DB(dbPath,album_artistD,'create_update_check')	
	artist_tobe_createL = validateD['cr_upd_art_L']
	

	
	if 'save' in args:		
		db = sqlite3.connect(dbPath)
		c  = db.cursor()
	
	
	cnt = 0
	for a in allmFD:
		cnt += 1
		if cnt%1000 == 0:
			if 'save' in args:		
				db.commit()
			print('.',cnt, end=' ')
		tag_nameD = {'title':'','album':'','artist':''}	
		for tag in tag_nameD:	
			try:
				#print 'origional:',allmFD[a]['metaD'][tag],
				#print tag,a
				tag_nameD[tag] = allmFD[a]['metaD'][tag]
				#print type(tag_nameD[tag]),[tag_nameD[tag]]
				#print 'Ok1'
			except Exception as e:
				print('errror at saving',e)
				print(tag_nameD[tag])
				logger.critical('in saveLibClast_to_DB_unicode  - error at saving 1023 [%s]'%(str(e)))
				if 'save' in args:		
					c.close()
					db.close()
				return
					
			
			tag_nameD[tag] = tag_nameD[tag].replace('"',"'")
		#print 'tag passed:',cnt	
		
		
		file = ''
					
		if 'f_name_rel' in allmFD[a]:	
			try:
				if isinstance(allmFD[a]['f_name_rel'],bytes):
					file = allmFD[a]['f_name_rel'].decode('utf-8')
				else:
					file = allmFD[a]['f_name_rel']
				print(allmFD[a])	
			except:
				file = allmFD[a]['f_name_rel']
			
		
		if 'cue_f_name_rel' in allmFD[a]:
			try:
				if isinstance(allmFD[a]['cue_f_name_rel'],bytes):
					cue_f_name_rel = allmFD[a]['cue_f_name_rel'].decode('utf-8')
				else:
					cue_f_name_rel = allmFD[a]['cue_f_name_rel']
			except:
				cue_f_name_rel = allmFD[a]['cue_f_name_rel']


			try:
				if isinstance(allmFD[a]['file'],bytes):
					file = allmFD[a]['file'].decode('utf-8')
				else:
					file = allmFD[a]['file']
				print(allmFD[a])	
			except:
				file = allmFD[a]['file']
		
		if file == '':
			logger.critical('in saveLibClast_to_DB_unicode  - error at saving 1397 fname tb save is empty: '%(allmFD[a]['file']))
			continue	
		
		print('chck_2:',cnt)	
		try:
			rec = (file,a,tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
			allmFD[a]['metaD']['artist_CRC32'],\
			allmFD[a]['album_crc32'],allmFD[a]['metaD']['pos_num'],\
			allmFD[a]['last_modify_date'],cue_f_name_rel,allmFD[a]['metaD']['bitrate'],
			allmFD[a]['metaD']['time'].strip(),add_date)
			#rec = rec.replace("'","''")
		except KeyError as e:
			#cnt+=1
			print('error at praparation saving in db:',e,a)
			logger.critical('in saveLibClast_to_DB_unicode dir - errror at saving 1240')
			#allmFD[a]['metaD']
			continue
		
			
		print('chck_3:',cnt)	
		#rec = rec.replace("'","''")

		#req_ins = """insert into track (path,title,artist_crc32,album_crc32) values ("QuotedStr(%s)","QuotedStr(%s)",%s,%s)"""%rec
		# CREATE TABLE track (id_track INTEGER PRIMARY KEY AUTOINCREMENT, title varchar(256), artist varchar(128),album varchar(128) artist_crc32 integer,album_crc32 integer, path varchar(300),path_crc32 integer, last_modify_date float )
		# alter table track add column last_modify_date float

		#req_ins = """insert into track (path,title,artist_crc32,album_crc32) values ("+ QuotedStr(%s) + "," + QuotedStr(%s) + ",%s,%s)"""%rec
		rec_m = None
		
		try:
			if 'db_id' not in allmFD[a]:
				if allmFD[a]['metaD']['pos_num'] != None:
					req_ins = """insert into track (path,path_crc32,title,album,artist,artist_crc32,album_crc32,cue_num,last_modify_date,cue_fname,bitrate,time_str,add_date) values ("%s",%s,"%s","%s","%s",%s,%s,%s,%s,"%s",%s,"%s","%s") """%rec
				else:
					rec = (file,a,tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],	allmFD[a]['album_crc32'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),add_date)
					req_ins = """insert into track (path,path_crc32,title,album,artist,artist_crc32,album_crc32,last_modify_date,bitrate,time_str,add_date) values ("%s",%s,"%s","%s","%s",%s,%s,%s,%s,"%s","%s")"""%rec
			else:
				if allmFD[a]['metaD']['pos_num'] != None:
					rec_m = (tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],allmFD[a]['album_crc32'],allmFD[a]['metaD']['pos_num'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),\
					allmFD[a]['db_id'])	
					req_ins = """update track set title = "%s", album  = "%s", artist = "%s", artist_crc32  = %s ,album_crc32  = %s, cue_num = %s, last_modify_date = %s, bitrate = %s, time_str = "%s" where id_track = %s"""%rec_m
				else:
					rec_m = (tag_nameD['title'],tag_nameD['album'],tag_nameD['artist'],\
					allmFD[a]['metaD']['artist_CRC32'],allmFD[a]['album_crc32'],\
					allmFD[a]['last_modify_date'],allmFD[a]['metaD']['bitrate'],allmFD[a]['metaD']['time'].strip(),\
					allmFD[a]['db_id'])	
					req_ins = """update track set title = "%s", album  = "%s", artist = "%s", artist_crc32  = %s ,album_crc32  = %s, last_modify_date = %s ,bitrate = %s, time_str = "%s" where id_track = %s"""%rec_m
				updL.append(allmFD[a]['db_id'])
		except TypeError as e:
			print('Error at insertint modifying:',e)
			logger.critical('in saveLibClast_to_DB_unicode track - errror at saving 1280')
			print('req_m:',rec_m,'cnt:',cnt,'key=',a,'db_id in allmFD[a]:',('db_id' in allmFD[a]))
			print(allmFD[a])
			#continue
			return
		
			
		
		if 'save' in args:		
			try:
				r = c.execute(req_ins)
				lastrowid  = c.lastrowid
				logger.info('in saveLibClast_to_DB_unicode track - Saved OK. LastrowID:%s'%(str(lastrowid)))
				if lastrowid != None:
					insL.append(c.lastrowid)
			except sqlite3.OperationalError as e:
				#print cnt,':',req_ins
				#print 'SQl Error:',e
				logger.critical('in saveLibClast_to_DB_unicode track - error at saving Sql Error 1278 [%s]'%(str(e)))
				logger.critical('in saveLibClast_to_DB_unicode track - error at saving Sql Error 1278 [%s]'%(str(req_ins)))
				continue
				if 'save' in args:		
					c.close()
					db.close()
				return
				
				
	# Preapare album save
	for alb_key in album_artistD:
		req_ins = ''
		print(list(album_artistD[alb_key].keys()))
		album_modify = False
		
		
		try:
			if isinstance(album_artistD[alb_key]['path'],bytes):
				album_path = album_artistD[alb_key]['path'].decode('utf-8')
			else:
				album_path = album_artistD[alb_key]['path']
		except:
			album_path = album_artistD[alb_key]['path']
		
		if not album_artistD[alb_key]['isDB']:
			
			print('album prepare save insert',alb_key)
			
			print('after validate album_add_date:',album_artistD[alb_key]['add_date']) 
			
			# Album is not exist and tracks is NOT existed before 	
			if album_artistD[alb_key]['add_date'] == '':
				album_add_date = add_date
			else:
				# Album is not exist and tracks IS existed before 	
				album_add_date = album_artistD[alb_key]['add_date'] 
				
			try:
				#'album', 'album_name_crc32', 'album_type', 'artistDataD', 'album_crc32', 'format', 'add_date', 'path', 'album_track_number'
				rec = (album_artistD[alb_key]['album'],album_artistD[alb_key]['album_name_crc32'],album_path,alb_key,
						album_artistD[alb_key]['format'],album_artistD[alb_key]['album_type'],album_artistD[alb_key]['album_track_number'],album_add_date)
			except KeyError as e:
				print('error at praparation saving in db:',e,a)
				logger.critical('in saveLibClast_to_DB_unicode album - errror at saving album 1252')
				continue

			try:
				req_ins = """insert into album (album,album_crc32,path,path_crc32,format_type,album_type,tracks_num,add_date)  values ("%s",%s,"%s",%s,"%s","%s",%s,"%s")"""%rec
			except Exception as e:
				print('error at praparation saving in db client:',e)
				logger.critical('Error: in saveLibClast_to_DB_unicode album - error at saving album 1262 [%s]'%(str(e)))
				#allmFD[a]['metaD']
				continue
				
			album_modify = True	
		else:
			print('album prepare save update',alb_key,album_artistD[alb_key]['db_id'])
			try:
				#'album', 'album_name_crc32', 'album_type', 'artistDataD', 'album_crc32', 'format', 'add_date', 'path', 'album_track_number'
				rec = (album_artistD[alb_key]['album'],album_artistD[alb_key]['album_name_crc32'],album_path,alb_key,
						album_artistD[alb_key]['format'],album_artistD[alb_key]['album_type'],album_artistD[alb_key]['album_track_number'],album_artistD[alb_key]['db_id'])
			except KeyError as e:
				print('error at praparation saving in db:',e,a)
				logger.critical('in saveLibClast_to_DB_unicode album - errror at saving album 1252')
				continue
			
			try:
				req_ins = """update album set album = "%s", album_crc32  = %s, path = "%s", path_crc32 = %s, format_type = "%s", album_type = "%s", tracks_num = %s where id_album = %s"""%rec
			except Exception as e:
				print('error at praparation saving in db client:',e)
				logger.critical('Error: in saveLibClast_to_DB_unicode album - error at saving album 1262 [%s]'%(str(e)))
				logger.critical('Error: in saveLibClast_to_DB_unicode album - error at saving album 1262 [%s]'%(str(req_ins)))
				#allmFD[a]['metaD']
				continue
			
			album_modify = True
			
		
		
		if 'save' in args and album_modify:		
			try:
				r = c.execute(req_ins)
				lastrowid  = c.lastrowid
				
				logger.info('in saveLibClast_to_DB_unicode album - Saved OK. LastrowID:%s'%(str(lastrowid)))
				
				if lastrowid != None:
					album_artistD[alb_key]['db_id'] = lastrowid
					album_artistD[alb_key]['isDB'] = True
					ins_alb_L.append(lastrowid)
			except sqlite3.OperationalError as e:
					#print cnt,':',req_ins
					#print 'SQl Error:',e
				logger.critical('Exception: in saveLibClast_to_DB_unicode album - error at saving Sql Error 1323 [%s]'%(str(e)))
				logger.critical('Exception: 1323 request detailes [%s]'%(str(req_ins)))
				continue
				if 'save' in args:		
					c.close()
					db.close()
				return
		#<--------------- Preapare album save end block		
		
	# Prepare artist creation  		
	for item in  artist_tobe_createL:
		#item = {'action':'update','artist_crc32':art_key,'alb_key':alb_key, 'db_id':resL[0]}
		#artistD = ['add_date', 'tobeSave', 'artist_crc32', 'artist']
		print("item.keys:",list(item.keys()))
		print('item:',item)
		artistD = album_artistD[item['alb_key']]['artistDataD'][item['artist_crc32']]
		req_ins = ''
		artist_modify = False
		if item['action'] == 'create':
			print('in action create')
			if item['add_date'] != '':
				album_add_date = item['add_date']
				print('date from track -> artist:',album_add_date)
			else:
				album_add_date = add_date
				print('date NEW -> artist:',album_add_date)
			rec = (artistD['artist'],artistD['artist_crc32'],album_add_date) 
			
			try:
				req_ins = """insert into artist (artist,artist_crc32,add_date)  values ("%s",%s,"%s")"""%rec
			except Exception as e:
				print('error at praparation saving in db client:',e)
				logger.critical('Exception: in saveLibClast_to_DB_unicode artist insert - error at prepare saving Sql Error 1356 [%s]'%(str(e)))
				#allmFD[a]['metaD']
				continue
			artist_modify = True	
			
			
			if 'save' in args and artist_modify:	
				try:
					r = c.execute(req_ins)
					lastrowid  = c.lastrowid
					logger.info('in saveLibClast_to_DB_unicode artist - Saved OK. LastrowID:%s'%(str(lastrowid)))
					if lastrowid != None:
						ins_art_L.append(lastrowid)
				except sqlite3.OperationalError as e:
					logger.critical('Exception: in saveLibClast_to_DB_unicode artist - error at saving Sql Error 1369 [%s]'%(str(e)))
					continue
				
				if lastrowid != None:	
					tracks_num_per_artist = album_artistD[item['alb_key']]['artistDataD'][artistD['artist_crc32']]['tracks_num_per_artist']
					try:
						rec = (lastrowid,album_artistD[item['alb_key']]['db_id'], artistD['artist_crc32'],item['alb_key'],tracks_num_per_artist)
					except Exception as e:
						logger.critical('Exception: in saveLibClast_to_DB_unicode artist [action create] - error at saving Sql Error 1498 [%s]'%(str(e)))
						logger.critical('Exception [data]: 1498 [%s] [%s] [%s]'%(str(item['alb_key']),str(album_artistD[item['alb_key']]),str(artistD['artist_crc32'])))
						return
				
					try:
						req_ins = """insert into artist_album_ref (id_artist,id_album,artist_crc32,album_crc32,tracks_num)  values (%s,%s,%s,%s,%s)"""%rec
					except Exception as e:
						print('error at praparation saving in db client artist_album_ref:',e)
						logger.critical('Exception: in saveLibClast_to_DB_unicode artist_album_relation insert relation - error at prepare saving Sql Error 1368 [%s]'%(str(e)))
						print('rec',[rec])
						#allmFD[a]['metaD']
						continue		
					
			
		elif item['action'] == 'update':
			print('in action update')
			tracks_num_per_artist = album_artistD[item['alb_key']]['artistDataD'][artistD['artist_crc32']]['tracks_num_per_artist']
			try:
				rec = (item['db_id'],album_artistD[item['alb_key']]['db_id'], artistD['artist_crc32'],item['alb_key'],tracks_num_per_artist)
			except Exception as e:
				logger.critical('Exception: in saveLibClast_to_DB_unicode artist [action update]- error at saving Sql Error 1519 [%s]'%(str(e)))
				logger.critical('Exception [data]: 1519 [%s] [%s] [%s] artistD:[%s]'%(str(item['alb_key']),str(album_artistD[item['alb_key']]),str(list(artistD.keys())),str(artistD)))
				return	
					
			try:
				req_ins = """insert into artist_album_ref (id_artist,id_album,artist_crc32,album_crc32,tracks_num)  values (%s,%s,%s,%s,%s)"""%rec
			except Exception as e:
				print('error at praparation saving in db client artist_album_ref [update]:',e)
				logger.critical('Exception: in saveLibClast_to_DB_unicode artist_album_relation insert relation - error at prepare saving Sql Error 1368 [%s]'%(str(e)))
				#allmFD[a]['metaD']
				continue
		
			artist_modify = True	
			
		if 'save' in args and artist_modify:	
			try:
				r = c.execute(req_ins)
				lastrowid  = c.lastrowid
				logger.info('in saveLibClast_to_DB_unicode artist_album_ref - Saved OK. LastrowID:%s'%(str(lastrowid)))
				if lastrowid != None:
					ins_art_L.append(lastrowid)
			except sqlite3.OperationalError as e:
				logger.critical('Exception: in saveLibClast_to_DB_unicode artist - error at saving Sql Error 1369 [%s]'%(str(e)))
				continue		
			
	if 'save' in args:		
		db.commit()
		#lastRowId = c.lastrowid
		c.close()
		db.close()
		print('lastRowIdL = ',updL,insL,ins_alb_L,upd_alb_L)
		logger.info('in saveLibClast_to_DB_unicode commit all - Finished')
		return {'updL':updL,'insL':insL,'ins_alb_L':ins_alb_L,'upd_alb_L':upd_alb_L,'ins_art_L':ins_art_L,'upd_art_L':upd_art_L}	
	
	return album_artistD
		


def initialMediaLibGRP2PL_into_DBLoad(grD,gr2lD,db,*args):
# ��������������� ������� ��������� �������� ������������ �������� � �� sqlite
	c = db.cursor()
	if 'group' in args:
		for a in grD:

			descr = grD[a]['descr'].decode('cp1251').encode('utf-8')

			rec = (grD[a]['group_key'],grD[a]['num'],descr,grD[a]['short_name'])
			req = """insert into groups_pl(group_key,pos,descr,short_name) values ("%s",%s,"%s","%s")"""%rec
			r = c.execute(req)

	if 'group2playlist' in args:
		for a in gr2lD:
			for b in gr2lD[a]:

				req = """insert into LIST2GROUP_REL (group_key, listname) values ("%s","%s")"""%(a,b)
#				print req
				c.execute(req)
	db.commit()	
	
def getAlbumArtista_from_allMetaData(allmFD,*args):
	logger.debug('in getAlbumArtista_from_allMetaData  - Start')
	album_artistD = {}
	
	cnt = 0
	for a in allmFD:
		cnt += 1
		if cnt%1000 == 0:
			print('.',cnt, end=' ')
		
		
		if allmFD[a]['album_crc32'] not in album_artistD:
			artistDataD = {}
			artistDataD[allmFD[a]['metaD']['artist_CRC32']] = {'artist_crc32':allmFD[a]['metaD']['artist_CRC32'],'artist':allmFD[a]['metaD']['artist'], 'add_date':'','tobeSave':False,'tracks_num_per_artist':1}
			# if 'reuse_add_date' in args:
			# # reuse add_date from track
				# if not modify_time:
					# modify_time = artistDataD[allmFD[a]['metaD']['artist_CRC32']]['add_date']
			# else:
				# if modify_time:
					# artistDataD[allmFD[a]['metaD']['artist_CRC32']]['add_date'] = modify_time
				
			album_name_crc32 = 0
			#print(a,allmFD[a]['metaD']['album'])
			try:
				album_name_crc32 = zlib.crc32(allmFD[a]['metaD']['album'].encode(BASE_ENCODING))
			except Exception as e:
				logger.critical('Error in getAlbumArtista_from_allMetaData - error crc32 calc [%s]'%(str(e)))
				
			#print(album_name_crc32)
			format = ''
			if b".cue" in allmFD[a]['file']:
				format = allmFD[a]['ftype']+' cue'
			else:
				format = allmFD[a]['ftype']
			
			album_artistD[allmFD[a]['album_crc32']] = {'artistDataD':artistDataD,'album':allmFD[a]['metaD']['album'],
															'album_crc32':allmFD[a]['album_crc32'],'path':allmFD[a]['album_path'], 'add_date':'','album_name_crc32':album_name_crc32,'format':format,'album_track_number':1}
			
		else:
			artist_CRC32 = allmFD[a]['metaD']['artist_CRC32']
			if artist_CRC32 in album_artistD[allmFD[a]['album_crc32']]['artistDataD']:
				#print a,allmFD[a]['metaD']['artist_CRC32'],album_artistD[allmFD[a]['album_crc32']]['artistDataD'][allmFD[a]['metaD']['artist_CRC32']].keys()
				album_artistD[allmFD[a]['album_crc32']]['artistDataD'][allmFD[a]['metaD']['artist_CRC32']]['tracks_num_per_artist']+=1
				#print '-1--'
			elif artist_CRC32 not in album_artistD[allmFD[a]['album_crc32']]['artistDataD']:
				album_artistD[allmFD[a]['album_crc32']]['artistDataD'][artist_CRC32] = {'artist_crc32':allmFD[a]['metaD']['artist_CRC32'],'artist':allmFD[a]['metaD']['artist'], 'add_date':'','tobeSave':False,'tracks_num_per_artist':1}
				
			album_artistD[allmFD[a]['album_crc32']]['album_track_number'] = album_artistD[allmFD[a]['album_crc32']]['album_track_number']+1
	print('for finished')
	for album_key in album_artistD:
		if len(album_artistD[album_key]['artistDataD']) == 1:
			album_artistD[album_key]['album_type'] = 'ONE_ARTIST'
		else:
			album_artistD[album_key]['album_type'] = ''
			
	logger.debug('in getAlbumArtista_from_allMetaData - Finish')		
	return album_artistD
	
def mediaLib_intoDb_Load_withUpdateCheck(dbPath,init_dirL,audioFilesPathRoot,creation_time,*args):
	logger.info('in mediaLib_intoDb_Load_withUpdateCheck dir:[%s] args:[%s]- Start'%(str(init_dirL),str(args)))	
	# 1. Get all db_id list from table track
	db = sqlite3.connect(dbPath)
	indxD = getMedialibDb_Indexes(db)
	
	resD = getAlbumArtist_dbId_CRC32_mapping(db)
	indxArtistD = resD['indxArtistD']
	indxAlbumD = resD['indxAlbumD']
	
	# 2. Get all path crc32 from table track, with time creation check --->
	c = db.cursor()
	if creation_time:
		print('ml_tree_buf creation_time:',creation_time)
		req = """select path_crc32 from track where add_date < '%s' """%(str(creation_time))
	else:
		req = 'select path_crc32 from track'
	try:	
		c.execute(req)
	except Exception as e:
		print(e)
		print(req)
		logger.critical('Error in mediaLib_intoDb_Load_withUpdateCheck sqlite:[%s]'%(str(e)))	
		logger.critical('Error in mediaLib_intoDb_Load_withUpdateCheck sqlite:[%s]'%(req))	
	#print 1
	resL = c.fetchall()
	#print 2
	c.close()
	db.close()
	# <------------------
	
	curDbL = [a[0] for a in resL]
	set_curDbL = set(curDbL)
	
	
	t_init = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
	print('Collecting the path data start at:',time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
	
	# 3. Предварительный сбор метаданных из указанной папки с проверкой CUE(image,tracs) и просто трэки в папке для не CUE 
	# результирующий словарь allmFD, его ключи - это path_crc32
	rD = collectMyMediaLib_folder_new(init_dirL,audioFilesPathRoot)
	if 'Error' in rD:
		print('1245 Error after collectMyMediaLib_folder_new')
		return {'Error':'Error after collectMyMediaLib_folder_new','rD':rD, 'new_allmFD':{}}
	new_allmFD = {}
	update_allmFD = {}
	print()
	print('Number of files:',len(rD['allmFD']))
	logger.debug('in mediaLib_intoDb_Load_withUpdateCheck, Number of files:[%s]'%(str(len(rD['allmFD']))))	
	
	# get PATH_CRC32 tracks keys 
	set_rD_keys = set(rD['allmFD'].keys())
	if 'reload' in args or 'reloadsimpl' in args:
		difL = 	set_rD_keys
	else:
		difL = list(set_curDbL.intersection(set_rD_keys))
	print('intesection',len(difL),len(set_curDbL),len(set_rD_keys))
	# ��������. �������� ���������� ������ ���� ���� ����������� ������ ������ � �� ��� ���� ��� �����������. ���� ������������. �� ����� �� ����������.
	
	change_flag = False
	if len(difL) == 0:
		for a in rD['allmFD']:
			new_allmFD[a] = rD['allmFD'][a]
	elif len(difL) == len(set_rD_keys):
		change_flag = True	
		for a in difL:
			new_allmFD[a] = rD['allmFD'][a]
	elif len(set_curDbL) != len(set_rD_keys):
		difL = list(set_rD_keys.difference(set_curDbL))
		for a in difL:
			new_allmFD[a] = rD['allmFD'][a]
	
	
	# Тут проверяется наличие по БД для CRC32 и выставляются поля 'db_track' и ['db_id']
	if 'ml_buf_time_with_db_check' in args:
		print('before  ml_buf_time_with_db_check')
		#print new_allmFD.keys()
		#print 'kokok'
		for a in new_allmFD:
			if a in indxD:
				new_allmFD[a]['db_track'] = 'X'
				new_allmFD[a]['db_id'] = indxD[a][0]
			else:
				new_allmFD[a]['db_track'] = '-'
	else:
		for a in new_allmFD:
			new_allmFD[a]['db_track'] = '-'
		
	print()
	print('Getting the difference with DB start at:',time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),len(difL),'change_flag=',change_flag)
	# ���� �� ����������� intersection ���� ������� .. ��� ����� ������ ��� ���������. 
	if change_flag:
		
		for a in difL:
			#if a not in curDbL:
			#	new_allmFD[a] = rD['allmFD'][a]
			#	continue	
			#else:
			if 'reloadsimpl' in args:
				new_allmFD[a] = rD['allmFD'][a]
				if 'db_id' in new_allmFD[a]: 
					new_allmFD[a]['db_track'] = 'X'
					new_allmFD[a]['db_id'] = indxD[a][0]
					continue
				else:
					logger.critical('Error: in mediaLib_intoDb_Load_withUpdateCheck check db_id for index:[%s] '%(str(a)))		
					
			
			# Учитываем изменения, только если действительно было изменение в файле, т.е. дата измения новая
			# сравиваем дату измения файла и дату этого файла в БД
			
			if 'reload' in args:
				if int(rD['allmFD'][a]['last_modify_date']) > int(indxD[a][1]):
					new_allmFD[a] = rD['allmFD'][a]
			elif 'reloadsimpl' in args:
				new_allmFD[a] = rD['allmFD'][a]
				
				
			try:
				if 'db_id' in new_allmFD[a]:
					new_allmFD[a]['db_id'] = indxD[a][0]
				else:
					new_allmFD[a]['db_id'] = '0'
				if 'db_track' in new_allmFD[a]:	
					new_allmFD[a]['db_track'] = 'X'
				else:
					new_allmFD[a]['db_track'] = 'E'
			except Exception as e:
				logger.critical('Error in mediaLib_intoDb_Load_withUpdateCheck - last_modify_date check:[%s]'%(str(e)))	
				print('allmFD:',rD['allmFD'].keys())
				#print('new_allmFD:',new_allmFD.keys())
				#new_allmFD[a] = rD['allmFD'][a]
				#new_allmFD[a]['db_id'] = '0'
				#new_allmFD[a]['db_track']='E'
				print(a,rD['allmFD'][a])	
				
				#else:
				#	print time.ctime(rD['allmFD'][a]['last_modify_date']), time.ctime(indxD[a][1])
	print('Number do be checked and  inserted:',len(new_allmFD))		
	print('Number do be update:',len([a for a in new_allmFD if 'db_id' in new_allmFD[a]]))		
	print('Collecting the mediaMeta data start at:',time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
	
	lenResD = 0
	album_artistD = {}
	resD = {}
	errorLog = {}
	if new_allmFD != {}:	
	# 4. Только для дельты собрать недостающие метаданные из медиафайлов битрейт, время и т.д.
		errorLog = collectAllMetaData(new_allmFD)
		
		for error_item in errorLog['errorLog']:
			#print(error_item)
			error_key = error_item['key']
			#print(error_key)
			new_allmFD.pop(error_key)
			logger.critical('Error in mediaLib_intoDb_Load_withUpdateCheck after collectAllMetaData errorLog key skipped:[%s]'%str(error_key))
		
		#logger.debug('Error in mediaLib_intoDb_Load_withUpdateCheck after collectAllMetaData errorLog:[%s]'%str(errorLog))

# 5. Только для дельты собрать метаданные по Альбому-Артисту для последующего сохранения и добавить add_date
	# new modification 06.2018 Album-Artist Data collection	
		album_artistD = getAlbumArtista_from_allMetaData(new_allmFD)
	
	#6. Check Album Artist existance in DB
		for a in new_allmFD:
			if new_allmFD[a]['album_crc32'] in indxAlbumD:
				new_allmFD[a]['album_db_id'] = indxAlbumD[new_allmFD[a]['album_crc32']]
				new_allmFD[a]['db_album'] = 'X'
			else:	
				new_allmFD[a]['album_db_id'] = None
				new_allmFD[a]['db_album'] = '-'
			
			
			if new_allmFD[a]['metaD']['artist_CRC32'] in indxArtistD:
				new_allmFD[a]['artist_db_id'] = indxArtistD[new_allmFD[a]['metaD']['artist_CRC32']]
				new_allmFD[a]['db_artist'] = 'X'
			else:	
				new_allmFD[a]['artist_db_id'] = None
				new_allmFD[a]['db_artist'] = '-'
			
			
	if 'save_db' in args and new_allmFD != {} :
		print()
		print('Saving into DB start at:',time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
		t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
		resD = saveLibClast_to_DB_unicode(dbPath,new_allmFD,album_artistD,t_date,'save')
		if resD['insL'] != []:
			lenResD = len(resD['insL'])
			logger.debug('in mediaLib_intoDb_Load_withUpdateCheck: Correct artist CRC32 for:[%s] check'%(str(resD['insL'])))	
			print('Correct artist CRC32 for:',lenResD)
			#correct_CRC32_in_DB(dbPath,resD['insL'])
		#saveLibClast_to_DB(update_allmFD,'update')
	print()	
	print('Process finished at:',time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), ' from:',t_init)	
	if 'update_db_crc32' in args and resD != {}:
		pass
		
	logger.info('in mediaLib_intoDb_Load_withUpdateCheck resD len:[%s] - Finished'%(str(lenResD)))		
	return {'new_allmFD':new_allmFD, 'errorLog':errorLog, 'album_artistD':album_artistD}
def getTempdb(mediaLib,*args):
	if 'save' in args:
		f = open('mymedialib_db.dat','w')
		s=pickle.dumps(mediaLib)
		pack_s = zlib.compress(s)
		pickle.dump(pack_s,f)
		f.close()
	elif 'load' in args:
		f = open('mymedialib_db.dat','r')
		pack_s = pickle.load(f)
		s = zlib.decompress(pack_s)
		obj = pickle.loads(s)
		f.close()
		return obj 
		


def getCurrentMetaData_fromDB_via_pL_pos(plPosL,curL,indxD,db):
	crc32L = []
	mapD = {}
	for a in plPosL:

		if a == len(curL):
			continue
		try:	
			crc32 = zlib.crc32(curL[a].encode('utf-8').lower())
		except UnicodeDecodeError as e:
			print("Error in getCurrentMetaData_fromDB_via_pL_pos:",  a,curL[a],e)
			crc32 = zlib.crc32(curL[a].lower())
			
			
		if crc32 in indxD:
			crc32L.append(indxD[crc32][0])
		#print crc32,indxD[crc32]
			mapD[indxD[crc32][0]] =  {'plPos':a,'orderPos':plPosL.index(a)}
		else:
			print('Error in getCurrentMetaData_fromDB_via_pL_pos: wrong index:',crc32)
	#c = db.cursor()
	metaD = getCurrentMetaData_fromDB_via_DbIdL(crc32L,db,'progress')
	#req = 'select * from track where id_track in (%s)'%(str(crc32L)[1:-1])
	#print req	
	#c.execute(req)
	

	#l =c.fetchall()
	#print 'metaDd', metaD.keys()
	#print 'MapD', mapD.keys()
	for a in metaD:
		t = os.path.splitext(metaD[a]['path'])[1]
		format = ''
		if t != '':
			format = t[1:]
			if metaD[a]['cue_num'] != None:
				format = format + ' cue'
		metaD[a]['format'] = format		
		#print metaD[a].keys()
		for b in list(metaD[a].keys()):
			#print b
			mapD[metaD[a]['id_track']][b]=metaD[a][b]
	#c.close()
	return mapD

def getDbIDL_via_CRC32L(dbPath,CRC32L,db):
	db = sqlite3.connect(dbPath)	
	#db.text_factory = str
	c = db.cursor()
	req = 'select id_track from track where ignore is NULL and path_crc32 in (%s)'%(str(CRC32L)[1:-1])
	c.execute(req)
	#print req

	l =c.fetchall()
	
	c.close()
	db.close()
	return l					

def getCurrentMetaData_fromDB_via_CRC32L(dbPath,CRC32L,db):
	db = sqlite3.connect(dbPath)	
	#db.text_factory = str
	c = db.cursor()
	req = 'select * from track where ignore is NULL and path_crc32 in (%s)'%(str(CRC32L)[1:-1])
	c.execute(req)
	#print req

	l =c.fetchall()
	
	c.close()
	db.close()
	return l				

def getCurrentMetaData_fromDB_via_DbIdL_alterntv(DbIdL,db):
	
	if db == None:
		print('Error: None db handler in getCurrentMetaData_fromDB_via_DbIdL_alterntv')
	else:		
	#db = sqlite3.connect(dbPath)	
		#db.text_factory = str
		pass
	logger.info('in getCurrentMetaData_fromDB_via_DbIdL_alterntv')	
	c = db.cursor()
	#print '4'
	req = 'select * from track where ignore is NULL and id_track in (%s)'%(str(DbIdL)[1:-1])
	
	try:
		c.execute(req)
	except Exception as e:
		logger.critical('Exception [%s] in getCurrentMetaData_fromDB_via_DbIdL_alterntv'%(str(e)))
	#print req

	l =c.fetchall()
	
	c.close()
	
	return l		
	
def getCurrentMetaData_fromDB_via_DbIdL(DbIdL,db,*args):
	logger.debug('in getCurrentMetaData_fromDB_via_DbIdL [%s]'%(str(args)))	
	logger.debug('in getCurrentMetaData_fromDB_via_DbIdL DbIdL: [%s]'%(str(DbIdL)))
		
	db_init_flag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)		
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)
		db_init_flag = True
		
		
	# get table metadata
	fieldD = getTableInfo('track',db)
	fieldL = [fieldD[a]['field_name']for a in fieldD]
	
	c = db.cursor()
	str_fld = ''
	str_fld = ','.join([a for a in fieldL])
		
	
	if 'take_all' in args:
		req = 'select %s from track where ignore is NULL'%(str_fld)
		print(req)
	else:
		req = 'select %s from track where id_track in (%s)'%(str_fld,str(DbIdL)[1:-1])
	#print req
	
	logger.debug('in getCurrentMetaData_fromDB_via_DbIdL db.text_factory: [%s]'%(str(db.text_factory)))
	
	try:
		c.execute(req)
	except Exception as e:
		logger.critical('Exception [%s] in getCurrentMetaData_fromDB_via_DbIdL'%(str(e)))
		return []
	
	#print '5'
	l =c.fetchall()
	
	resD = {}
	l_partL = []
	
	step = 2000
	j = 0
	if len(l)>step:
		
		for i in range(step,len(l),step):
			l_partL.append(l[j:i])
			j = i
			
		l_partL.append(l[i:])
	else:
		l_partL.append(l)
	#for a in 	l_partL:
		#print len(a)
	#print '6'	
	c_index = 0
	for p in l_partL:
		#print 'p=',p
		for a in p:
			lineD = {}
			#print 'a=',a
			for i in range(len(a)):
				lineD[fieldL[i]] = a[i]
			resD[lineD['path_crc32']] = 	lineD
			#print 'lineD=',lineD['path_crc32']
			if 'progress' in args:
				if (c_index+p.index(a))%1000 ==0 and c_index+p.index(a) != 0:
#					c_index = c_index + 1000
					print(c_index+p.index(a), end=' ')
		c_index = c_index + len(p)		
			
	c.close()
	
	#print '6'
	logger.debug('in getCurrentMetaData_fromDB_via_DbIdL, len resD=%i'%(len(resD)))	
	for a in resD:
		t = os.path.splitext(resD[a]['path'])[1]
		format = ''
		if t != '':
			format = t[1:]
			if resD[a]['cue_num'] != None:
				format = format + ' cue'
		resD[a]['format'] = format	
		#resD[a]['artist_crc32']= zlib.crc32(resD[a]['artist'].lower().strip())
		
	#print '7'	
	
	
	if db_init_flag:
		db.close()
	
	logger.debug('in getCurrentMetaData_fromDB_via_DbIdL - Finished, len resD=%i'%(len(resD)))		
	return resD	
	
def getDbIdL_viaTagId(tagId,db):
	extDbFlag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
		
	c = db.cursor()
	req = """select id_track from track_tag where id_tag = %s """%(str(tagId))
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	l = [a[0] for a in l]
	if extDbFlag:
		db.close()
	return l	

def getDbIdL_w_folderL_filter(dbPath,folderL,db):
	ts = time.time()
	extDbFlag = False
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
	c = db.cursor()
	l_tmp = []
	l = []
	resLs = []
	cnt = 0
	
	for a in folderL:
		try:
			req = """select id_track from track where path like '%%%s%%' and ignore is NULL """%(str(a))
		except Exception as e:
			logger.critical('Exception [%s] in getDbIdL_w_folderL_filter'%(str(e)))
			return []
		#print req	
		
		try:
			c.execute(req)
		except Exception as e:
			
			logger.critical('Exception [%s] in getDbIdL_w_folderL_filter'%(str(e)))
			return []
			
		l =  c.fetchall()
		l = [b[0] for b in l]	
		print('timing:',(time.time()-ts),len(l))
		
		if cnt == 0:
			resLs = set(l)

		if cnt > 0:
			resLs = resLs.union(set(l))
			
		cnt+=1	
		
	c.close()
	if extDbFlag:
		db.close()
	
	#r = [l.append(a[0]) for a in l_tmp if a[0] not in l]
	print('len res %s timing2:'%str(len(resLs)),(time.time()-ts))
	return list(resLs)	
	
def getArtistDbIdL_viaTagId(tagId,db):
	c = db.cursor()
	req = """select id_artist,artist_crc32 from artist_cat_rel where id_object = %s """%(str(tagId))
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	#l = [a[0] for a in l]
	return l	
	
def getDbIdL_viaAlbumCRC32(albumCRC32,db):
	
	c = db.cursor()
	req = """select id_track from track where ignore is NULL and album_crc32 = %s """%(str(albumCRC32))
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	l = [a[0] for a in l]
	return l		
	
def getDbIdL_viaAlbumCRC32_List(dbPath,albumCRC32L,db):
	extDbFlag = False
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
	
	c = db.cursor()
	req = """select id_track from track where ignore is NULL and album_crc32 in (%s) """%(str(albumCRC32L)[1:-1])
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	if extDbFlag:
		db.close()
	l = [a[0] for a in l]
	return l		
	
def getDbIdL_viaArtistCRC32(artistCRC32,db):
	c = db.cursor()
	req = """select id_track from track where artist_crc32 = %s """%(str(artistCRC32))
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	l = [a[0] for a in l]
	return l

	
	
def getDbIdL_viaArtistCRC32_List(artistCRC32L,db):
	c = db.cursor()
	
	req = """select id_track from track where ignore is NULL and artist_crc32 in (%s) """%(str(artistCRC32L)[1:-1])
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	l = [a[0] for a in l]
	return l		
def createPlayListBuffer(playL,indxD,db):
	#l=myMediaLib_adm.createPlayListBuffer(Mobj.getCurPlayListAsList(),myMediaLib.getMedialibDb_Indexes(db),db)
	if db != None:
		#db.text_factory = str
		pass
	else:
		print('Error in: createPlayListBuffer')
	playL_CRC32D = {}
	notFoundCRC32L =[]
	playCRC32L =[]
	for a in playL:
		pos = a.rfind('\\')
		fname = a[:pos].decode('utf-8').encode('cp1251')+'\\'+a[pos+1:].decode('utf8').encode('cp1251')
		
		
		#print a
		crc32 = zlib.crc32(a.lower())
		playCRC32L.append(crc32)
		if crc32 not in indxD:
			notFoundCRC32L.append(crc32)
			#print a,fname
			#return a
		
		last_modify_date = 0
		try:
			fname = a
			pos = a.lower().rfind('.cue')
			if pos >= 0:
				fname = a[:pos+4]
				#print fname
			last_modify_date = os.stat(fname.decode('utf8').encode('cp1251')).st_mtime
		except WindowsError as e:
			print('Eroror:',e,a)
			pass

		if crc32 not in playL_CRC32D:
			playL_CRC32D[crc32] = {'orig_fname':a,'last_modify_date':last_modify_date}
	
	print('Len playL_CRC32D = ',len(playL_CRC32D),'original curren plaing list len:',len(playL))
	for a in playL_CRC32D:
		if a in indxD :
			if int(playL_CRC32D[a]['last_modify_date']) == int(indxD[a][1]):
				playL_CRC32D[a]['indb_OK'] = 'X'
			else:
				print('Reject due to strange date comp',a,playL_CRC32D[a]['last_modify_date'],indxD[a][1])
		else:
			pass
			#print a,playL_CRC32D[a]
	dbL = [indxD[a][0] for a in playL_CRC32D if 'indb_OK' in playL_CRC32D[a]]
	#print 'bbL',dbL
	req = 'select * from track where id_track in (%s)'%(str(dbL)[1:-1])
	c = db.cursor()
	print('createPlayListBuffer:',req)
	c.execute(req)
	
	l = c.fetchall()
	c.close()
	return {'DBBuf':l,'notFoundCRC32L':notFoundCRC32L,'playCRC32L':playCRC32L}
	
	
def searchMediaLib_dbid(dbPath,search_term,searchFieldL):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	resL = []
	if searchFieldL == []:

		req = """select id_track, from track where ( artist like '%%%s%%' or album like  '%%%s%%' or title like '%%%s%% ) and ignore is NULL'"""%(search_term,search_term,search_term)
	else:
		where_expr = 'ignore is NULL and ( '
		for a in searchFieldL:
			where_expr = where_expr + ' '+ a + " like '%%%s%%' and "%(search_term)

		where_expr = where_expr[:-4]
		where_expr += ' )'
		req = "select id_track from track where  %s"%(where_expr)
	#print req

	try:	
		c.execute(req)
	except:
		print('SQl Error in searchMediaLib_dbid:',req)
	l = c.fetchall()
	resL = [a[0] for a in l]


	c.close()
	db.close()
	return resL

def searchMediaLib_MetaData(dbPath,search_term,searchFieldL,listD):
	logger.debug('in searchMediaLib_MetaData: [%s, %s] -Start'%(str(searchFieldL),str(type(search_term))))
	print([search_term])
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	metaData_plD = {}
	metaD = {}
	#print 'in searchMediaLib_MetaData-1'
	if searchFieldL == []:

		req = """select id_track,path_crc32,title,artist,album,path,cue_num,cue_fname,bitrate,artist_crc32,album_crc32 from track where ( artist like '%%%s%%' or album like  '%%%s%%' or title like '%%%s%%' ) and ignore is NULL"""%(search_term,search_term,search_term)
	else:
		where_expr = 'ignore is NULL and ('
		for a in searchFieldL:
			where_expr = where_expr + ' '+ a + " like '%%%s%%' or "%(search_term)

		where_expr = where_expr[:-4]
		where_expr += ' )'
		req = "select id_track,path_crc32,title,artist,album, path, cue_num,cue_fname,bitrate,artist_crc32,album_crc32 from track where  %s"%(where_expr)
	#print req
	
	try:	
		c.execute(req)
	except:
		print('SQl Error in searchMediaLib_MetaData:',req)
		
	l = c.fetchall()
	print(len(l))
	
	for a in l:
		t = os.path.splitext(a[5])[1]
		format = ''
		if t != '':
			format = t[1:]
			if a[6] != None:
				format = format + ' cue'
		#print 'format', format
		try:
			metaD[a[1]] = {'id_track':a[0],'title':a[2],'artist':a[3],'album':a[4], 'path':a[5], 'cue_num':a[6],'cue_fname':a[7],
														'format':format,'bitrate':a[8],'artist_crc32':a[9],'album_crc32':a[10]}
		except Exception as e:
			logger.critical('searchMediaLib_MetaData: [%s] '%(str(a)))
			print('Error:[%s] at [%s]'%(str(e),str(a)))
			return metaD
	
	
	c.close()
	db.close()
	#print 'in searchMediaLib_MetaData-3'
	#listD = getMyMediaLibStat_Lists(medialibObj)
	for a in metaD:
		if a in listD:
			metaD[a]['listD'] = listD[a]

			
	#print 'searchMediaLib_MetaData		-4'
	
	
	return metaD
	
def PlayListDic2SortList(sD):
	resL = []
	for a in sD:
		if 'listD' not in sD[a]:
			resL.append((sD[a]['path'],sD[a]['title'],sD[a]['artist'],sD[a]['album'],sD[a]['format'],[]))
		else:
			resL.append((sD[a]['path'],sD[a]['title'],sD[a]['artist'],sD[a]['album'],sD[a]['format'],sD[a]['listD']['list']))
	resL.sort()		
	return resL		
	
def checkCue_inLibConsistenc_folder(init_dirL,*args):
# ���� ��������� ����������� �� ������ ���� � CRC32 c ������ CUE
#r = myMediaLib.collectMyMediaLib_folder(['G:\\MUSIC\\ORIGINAL_MUSIC'])
	cnt = 0
	allmFD = {}
	cueD = {}
	cueDupl = {}
	notRelevCue = {}
	cueDupResD = {}
	flac_no_cueL = []
	ape_num = flac_num = all_alb_cnt = flac_no_cue_num = 0
	for init_dir in init_dirL:
		for root, dirs, files in os.walk(init_dir):
			cue_flag = False
			origf = ''
			ftype = ''

			for a in files:
			       #if a.find('.ape') > 0 or a.find('.flac')
				#if "image" in a:
				#	print a  
				#if "ergole" in a:
				#	print a   
				cue_flag = False
				#if a[a.rfind('.'):].lower().find('.cue') >= 0:
				if '.cue' in a:
					origf = ''
					ftype = ''
					

					cue_name = (root+'\\'+a)

					try:	
						origfD = simple_parseCue(cue_name)	
					except NameError:
						import myMediaLib
						origfD = myMediaLib.simple_parseCue(cue_name)	
	#return {'orig_file':orig_file,'orig_file_path':orig_file_path,'fType':fType,'songL':songL} 
	
					try:
						if os.path.exists(origfD['orig_file_path']):
							cue_dirname = os.path.dirname(origfD['orig_file_path'])
							check_dircrc32 =  zlib.crc32(cue_dirname.lower())
							if check_dircrc32 in cueDupl :
								cueDupl[check_dircrc32]['dupL'].append((origfD['orig_file_path'],a)) 
							else:
								cueDupl[check_dircrc32] = {'dupL':[(origfD['orig_file_path'],a),],'dirName':cue_dirname,'cueFile':a}
								
							cue_flag = True
							if origfD['fType'].lower() == 'flac':
								flac_num+=1
							elif origfD['fType'].lower() == 'ape':
								ape_num+=1
							else:
								print(origfD['fType'])
							origf = origfD['orig_file_path']
							ftype = origfD['fType']
							crc32 = zlib.crc32(origf.lower())
							last_modify_date = 0
							try:
								last_modify_date = os.stat(cue_name).st_mtime
							except:
								print('eroror cue time',origfD['orig_file_path'])
								pass
							cueD[crc32]={'dir':root,'filename':a,'file':origf,'ftype':ftype,'songL':origfD['songL'],'last_modify_date':last_modify_date,'cueFName':cue_name}
						else:
							if  zlib.crc32(cue_name) in  notRelevCue:
								notRelevCue[zlib.crc32(cue_name)]['fL'].append(origfD['orig_file_path']) 
							else:
								notRelevCue[zlib.crc32(cue_name)] = {'fL':[origfD['orig_file_path'],],'cueFile':a}
							#print 'Cue not relevant:',origfD['orig_file_path']
							continue
					except:
						print('error:',origfD)
					#break
			
			continue
			
			for a in files:
				
				ftype = None
				if a[a.rfind('.'):].lower().find('.ape') >= 0:
					ftype = 'ape'
					
				elif a[a.rfind('.'):].lower().find('.flac') >= 0:
					ftype = 'flac'
				elif a[a.rfind('.'):].lower().find('.mp3') >= 0:
					ftype = 'mp3'
				
				if	ftype != None:
					fname = (root+'\\'+a).lower() 
					orig_fname = join(root,a) 
					
					crc32 = zlib.crc32(fname.encode(BASE_ENCODING))
					#if crc32 == 1133272172:
					#	return fname
					last_modify_date = 0
					try:
						last_modify_date = os.stat(orig_fname).st_mtime
					except:
						pass
					
					
					pos = root.rfind('\\')
					#pos_1 = a[:pos_2-2].rfind('\\')+1
					album = root[pos+1:]
					#print root
					if crc32 in cueD:
						for b in cueD[crc32]['songL']:
							crc32_i = zlib.crc32(b.lower().encode(BASE_ENCODING))
							pos = b.rfind(',')
							allmFD[crc32_i] = {'orig_fname':cueD[crc32]['file'],'last_modify_date':cueD[crc32]['last_modify_date'],'album':album,'album_crc32':zlib.crc32(root.lower().encode(BASE_ENCODING)),'file':b.lower(),'cueNameIndx':b[:pos],'ftype':ftype,'cue':'X'}
					else:
						allmFD[crc32] = {'orig_fname':orig_fname,'last_modify_date':last_modify_date,'album':album,'album_crc32':zlib.crc32(root.lower().encode(BASE_ENCODING)),'file':fname,'ftype':ftype,'cueNameIndx':None}
			
			if 'stat' not in args:
				continue
				
			for a in files:
				#crc32 = zlib.crc32(str(root).lower()+'\\'+a.lower())
				#allmFL[crc32] = str(root).lower()+'\\'+a.lower() 
				if a[a.rfind('.'):].find('.mp3') >= 0:
					all_alb_cnt += 1
					break
				elif a[a.rfind('.'):].find('.ape') >= 0:
					all_alb_cnt += 1
					break
				elif a[a.rfind('.'):].find('.flac') >= 0:
					if not cue_flag:
						flac_no_cue_num +=1
						flac_no_cueL.append(root)
					else:
						#print 'cue',
						pass
					all_alb_cnt += 1
					break
			cnt+=1
			if cnt%100 == 0:
				print('.',len(allmFD), end=' ')
				
	for a in cueDupl:
		if len(cueDupl[a]['dupL'])>1:
			cueDupResD[a] = cueDupl[a]
	return 	{'cueDupl':cueDupResD,'notRelevCue':notRelevCue}	
	
	if 'stat' in args:
		print()
		print('cueL:',len(cueD),'ape_num:',ape_num,'flac_num:',flac_num,'flac_no_cue_num:',flac_no_cue_num,'all_alb_cnt:',all_alb_cnt)
		return {'allmFD':allmFD,'cueL':cueD,'flac_no_cueL':flac_no_cueL,'ape_num':ape_num,'flac_num':flac_num,'all_alb_cnt':all_alb_cnt,'flac_no_cue_num':flac_no_cue_num}
	else:
		return {'allmFD':allmFD,'cueL':cueD}	

def createPlayList_fromMetaDataD(metaD,*args):
	# �������� ������� �������� ���������, ��� ��������� �������, �� �������� ����� ������ winamp ��� ������� ����� ������� � winamp ����� �������� �������
	# ������ ������� �� ������ ���������, ��� ��� ���������� ������� �������� ������ � winamp ����� ������ ������. �� ���� ���� ���������� ���� ���� � ����������
	# ������ ������ ��� ��� ������, ��� ��� ��������� ���� � �����.
	# ������ ������� ������������ ��� �������� � ��������, ���� �������� �������� ����� � ���������� ������ ����� ����������� ������, ��� ������� �� �����������.
	logger.debug('in createPlayList_fromMetaDataD: [%s] - Start'%(str(args)))
	s = ''
	resL = []
	sortedL = []
	for a in metaD:
		if metaD[a]['cue_num']==None:
			resL.append((metaD[a]['path'],a))
		else:
			resL.append((('%s,%02d'%(metaD[a]['cue_fname'],metaD[a]['cue_num'])),a))
	resL.sort()
	
	sortedL = [a[1] for a in resL]	
	if 'no_file_play_list' in args:
		return resL
	
			
	for a in sortedL:
		if metaD[a]['cue_num']==None:
			entry = metaD[a]['path']+'\n'
		else:
			entry = metaD[a]['cue_fname']+','+str(metaD[a]['cue_num'])+'\n'
		s+=entry
		
		logger.debug('in createPlayList_fromMetaDataD entry: [%s]'%(entry))	
	logger.debug('in createPlayList_fromMetaDataD: - Finished')	
	return s

def get_AllTags_asDic(dbPath,indexDic):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	req = """select id_tag,id_track from track_tag"""
	#print req
	
	c.execute(req)
	l = c.fetchall()
	c.close()
	db.close()
	
	tagsLDic = {}
	for a in l:
		#print a
		try:
			cur_crc32 = indexDic[a[1]]
		except:
			#print 'error with ',a[1]
			continue
		if cur_crc32 in tagsLDic:
			tagsLDic[cur_crc32].append(a[0])
		else:
			tagsLDic[cur_crc32] = [a[0]]	
	#print 'tagsLDic:',tagsLDic
	return tagsLDic
	
	
def findTags_via_TrackId(dbPath,id_track):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	req = """select id_tag from track_tag where id_track = %s """%(str(id_track))
	#print req
	c.execute(req)
	l = c.fetchall()
	c.close()
	db.close()
	l = [a[0] for a in l]
	return l
	
def findCateg_via_ObjectId(dbPath,ObjectDic,categDic,*args):
	print('ObjectDic:',ObjectDic)
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	catD = {}
	catDL = []
	artistL = []
	albumL = []
	rel_artL = []
	
	if 'album' in ObjectDic:
		albumL.append(ObjectDic['album'])
		# � ������� ����� ���� ����������� ������ ���� �������� ���
		objD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(None,db,[],[ObjectDic['album']],'with_relation')
		if ObjectDic['album'] in objD['album_rel_artistD']:
			rel_artL = [key for key in objD['album_rel_artistD'][ObjectDic['album']]['artistD']]
			if 'artist' in ObjectDic:
				if ObjectDic['artist'] in rel_artL:
					rel_artL.remove(ObjectDic['artist'])
					
			
		
		# ��� ��������� ���� �� ���������� ������� � ��� ������� ��� ����������� (�������� ����� �����) �� ������������ ���������
		albumD = getAlbum_relation_metaD(None,db,ObjectDic['album'],'from','get_neibor')
		# ������� ������
		if albumD['albums_from_relLD'] != []:
			albumL += [item['key'] for item in albumD['albums_from_relLD']]
			albumL.append(ObjectDic['album'])
			#print 'CATEG  album main------>        albumL:',albumL
			
		elif albumD['albums_to_relLD'] != []:	
			albumL =  [item['key'] for item in albumD['albums_all_relLD']]
			albumL+=[item['key'] for item in albumD['albums_to_relLD']]
						
			#print 'CATEG  album ------>        albumL:',albumL
	
		req = """select id_object,rel_type from album_cat_rel where album_crc32 in (%s) """%(str(albumL)[1:-1])
		#print req
		c.execute(req)
		l = c.fetchall()
		
		for a in l:
			catD[a[0]] = categDic[a[0]].copy()
			#catD['rel_type'] = a[2]
		#print 'albumCatL:',l	
		
	if 'artist' in ObjectDic or rel_artL != []:
		artistL.append(ObjectDic['artist'])
		# ��� ��������� ���� �� ���������� ������� � ��� ������� ��� ����������� (�������� ����� �����) �� ������������ ���������
		artistD = getArtist_relation_metaD(dbPath,ObjectDic['artist'],'main','get_neibor')
		# �� �������� ������
		if artistD['artists_from_main_relLD'] == []:
			artistL = [item['key'] for item in artistD['artists_all_relLD']]
			#print 'CATEG artist------>         '
			#print 'CATEG  artist------>        artistL:',artistL
			
		elif	artistD['artists_main_to_relLD'] == []:
			artistL += [item['key'] for item in artistD['artists_from_main_relLD']]
			
			#print 'CATEG  artist------>           '
			#print 'CATEG  artist------>main artistL:              ',artistL
			
		if rel_artL != []:
			artistL+=rel_artL
				
		
		req = """select id_object,rel_type from artist_cat_rel where artist_crc32 in (%s) """%(str(artistL)[1:-1])
		print(req)
		c.execute(req)
		l = c.fetchall()
		print('artistCatL:',l)
		for a in l:
			if a[0] not in catD:
				catD[a[0]] = categDic[a[0]].copy()
	
	c.close()
	db.close()		
	
	if 'result_like_list' in args:	
		for a in catD:
			catDL.append(catD[a])
		
	return {'categoryD':catD,'categoryL':catDL}	
	
def createNewTag_inDB(dbPath,newTagName,TagDescr,TagType):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	
	#check existense in DB
	req = 'select id_tag from tag where tag_name = "%s"'%(newTagName)
	c.execute(req)
	l = c.fetchone()
	if l != None:
		return -1	
		
	req_ins = """insert into tag (tag_name,tag_descr,tag_type) values ("%s","%s","%s") """%(newTagName.lower(),TagDescr,TagType.upper())
	#print req
	c.execute(req_ins)
	lastRowId = c.lastrowid
	
	db.commit()
	
	c.close()
	db.close()
	return lastRowId
	
def delete_Empty_Tag_inDB(dbPath,tag_id):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	
	#check existense in DB
	req = 'delete from tag where id_tag = %s'%(tag_id)
	
	try:
		c.execute(req)
		#lastRowId = c.lastrowid
	except:	
		print('error with;',req)
		c.close()
		db.close()
		return 0
	
	db.commit()
	
	c.close()
	db.close()
	print('tag deleted:',tag_id)
	return 1	
	
def createPlayList_viaTagId_cast(tagId,db):
	dbIdL = getDbIdL_viaTagId(tagId,db)
	
	logger.info('in createPlayList_viaTagId_cast')
	return 	createPlayList_via_dbIdl_cast(dbIdL,db)
	
def createPlayList_viaAlbumCRC32_cast(albumCRC32,db):
	dbIdL =  getDbIdL_viaAlbumCRC32(albumCRC32,db)

	return 	createPlayList_via_dbIdl_cast(dbIdL,db)	

def createPlayList_via_dbIdl_cast(dbIdL,db):
	metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
	
	resL = []
	sortedL = []
	for a in metaD:
		if metaD[a]['cue_num']==None:
			resL.append((metaD[a]['path'],a))
		else:
			resL.append((('%s,%02d'%(metaD[a]['cue_fname'],metaD[a]['cue_num'])),a))
	resL.sort()
	sortedL = [a[1] for a in resL]	
	
	
	return 	{'sortedL':sortedL,'metaD':metaD}			
	
def db_request_wrapper(db,request,*args):
	db_init_flag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)		
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)
		db_init_flag = True
		if 'no_utf8' in args:
			# this DB setting is a last optional non Unicode instruction
			db.text_factory = str	
	
	
	c = db.cursor()
	
	res = None
	try:
		c.execute(request)
	except Exception as e:
		logger.critical('Exception: in db_request_wrapper %s'%(str(e)))
		print('Exception: in db_request_wrapper %s'%(str(e)))
		return res
	
	
	if 'modi' not in args:
		res = c.fetchall()
	else:
		db.commit()
	c.close()
	
	if db_init_flag:
		db.close()
	
	if 'modi' not in args:
		return res
	else:
		return
	
def createPlayList_viaTagId(tagId,db,*args):
	logger.debug('in createPlayList_viaTagId: [%s] - Start'%(str(tagId)))
	dbIdL_before = getDbIdL_viaTagId(tagId,db)
	req = "select id_track from track where ignore = 'X'"
	ignor_trackL = db_request_wrapper(db,req)
	ignor_trackL = [a[0] for a in ignor_trackL]
	
	dbIdL = [a for a in dbIdL_before if a not in ignor_trackL]
	#print dbIdL,ignor_trackL
	if len(dbIdL_before) != len(dbIdL):
		print('check tag_track relation against ignored tracks:', [a for a in dbIdL_before if a in ignor_trackL])
	
	metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
	if 'no_file_play_list' in args:
		resL = createPlayList_fromMetaDataD(metaD,'no_file_play_list')
	else:	
		resL = createPlayList_fromMetaDataD(metaD)
	logger.debug('in createPlayList_viaTagId - finished')	
	return resL	

def createPlayList_viaTrackCRC32L(trackCRC32L,db):
	logger.debug('in createPlayList_viaTrackCRC32L: [%s] - Start'%(str(trackCRC32L)))
	db_init_flag = False
	if db == None:
		cfgD = readConfigData(mymedialib_cfg)		
		dbPath = cfgD['dbPath']
		db = sqlite3.connect(dbPath)
		db_init_flag = True
		#db.text_factory = str	
	
	
	req = 'select id_track from track where ignore is NULL and path_crc32 in (%s)'%(str(trackCRC32L)[1:-1])
	resL = db_request_wrapper(db,req)
	dbIdL = [a[0] for a in resL]
	print(str(dbIdL))
	
	metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
	logger.debug('in createPlayList_viaTrackCRC32L: metaD[%s]'%(str(metaD)))
	resL = createPlayList_fromMetaDataD(metaD)
	logger.debug('createPlayList_viaTrackCRC32L - finished')
	
	if db_init_flag:
		db.close()
	return resL		

	
def createPlayList_viaAlbumCRC32(albumCRC32,db):
	logger.debug('in createPlayList_viaAlbumCRC32: [%s] - Start'%(str(albumCRC32)))
	
	
	album_rel_Dic =  getAlbum_relation_metaD(None,db,albumCRC32,'from')['albums_from_relLD']
	relL = [item['key'] for item in album_rel_Dic]
	if relL != []:
		dbIdL =  getDbIdL_viaAlbumCRC32_List(None,relL,db)
		logger.debug('2809 in createPlayList_viaAlbumCRC32: relL <> []: [%i]'%(len(dbIdL)))
	else:
		dbIdL =  getDbIdL_viaAlbumCRC32(albumCRC32,db)
		logger.debug('2812 in createPlayList_viaAlbumCRC32: relL == []: [%i]'%(len(dbIdL)))
		
	metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
	logger.debug('in createPlayList_viaAlbumCRC32: metaD[%s]'%(str(metaD)))
	resL = createPlayList_fromMetaDataD(metaD)
	logger.debug('in createPlayList_viaAlbumCRC32 - finished')
	return resL		
	
def createPlayList_viaArtistCRC32(artistCRC32,db):
	
	artistCRC32L = []
	artistCRC32L = getAll_Related_to_main_Artist_fromDB(None,db,artistCRC32)
	album_relL = []
	dbIdL = []
	print('Related ok artistCRC32L=',artistCRC32L) 
	
	# ���� ��� ������� ������, �� � ���� ����� �� ���� ��������� �������� �� ���� ������� �� ���� ��������.
	artist_rel_albumD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(None,db,[artistCRC32],[],'with_relation')['artist_rel_albumD']
	if artist_rel_albumD != {}:
		album_relL = artist_rel_albumD[artistCRC32]
		album_relL = [a for a in artist_rel_albumD[artistCRC32]['albumD']]	
		dbIdL =  getDbIdL_viaAlbumCRC32_List(None,album_relL,db)
	
	if artistCRC32L == []:
		# Artist not main --> get Neibor
		artistCRC32L = getAll_Related_to_main_Artist_fromDB(None,db,artistCRC32,'get_neibor','with_parent')
		
	
	if artistCRC32L == []:
		# Add main artist to the list
		artistCRC32L = [artistCRC32]
	else:	
		artistCRC32L = [a[0] for a in artistCRC32L]
		artistCRC32L.append(artistCRC32)
		
	#print 'artistCRC32L=',artistCRC32L
	dbIdL = dbIdL + getDbIdL_viaArtistCRC32_List(artistCRC32L,db)
	#print '1',dbIdL 
	metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
	#print '2'
	resL = createPlayList_fromMetaDataD(metaD)
	#print '3'
	return resL	

def getTag_indexL_viaCategId(dbPath,categId,mode_L,categ_key):
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	
	c = db.cursor()
	if type(categId) == str:
		req = """select id_tag from TAG_CAT_REL where object_name = "%s" """%(str(categId))
	elif type(categId) == int:
		req = """select id_tag from TAG_CAT_REL where id_object = %s """%(categId)
	print(req)	
	c.execute(req)
	l = c.fetchall()
	tagL = [a[0] for a in l]	
	
	req = """select id_tag, tag_descr, tag_type from tag where id_tag in (%s)"""%(str(tagL)[1:-1])
	print(req)
	c.execute(req)
	l = c.fetchall()
	tagLDDL_L = [{'key':a[0],'value':a[1],'object_type':a[2]} for a in l]
	c.close()
	db.close()
	print('ddl ok')
	return {'tagL':tagLDDL_L}	
	
def getArtistAlbum_indexL_viaCategId(dbPath,categId,mode_L,categ_key):

	# ���������������� ���� ������������ :
	#getArtist_Album_metaD_fromDB(search_termD,folderL,artistCRC32,albumCRC32,*args):
	# ������� �� � crc32 �� crc32L
	# ��� ������� ��������
	
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	
	c = db.cursor()
	if type(categId) == str:
		req = """select id_artist from artist_cat_rel where object_name = "%s" """%(str(categId))
	elif type(categId) == int:
		req = """select id_artist from artist_cat_rel where id_object = %s """%(categId)
	
		
	#print req
	c.execute(req)
	l = c.fetchall()
	artistL = [a[0] for a in l]
	
	
	req = """select artist_crc32,artist,object_type from artist where id_artist in (%s) """%(str(artistL)[1:-1])
	c.execute(req)
	l = c.fetchall()
	
	artistDDL_L = [{'key':a[0],'value':a[1],'object_type':a[2]} for a in l]
	#print artistDDL_L
	
	if type(categId) == str:
		req = """select id_album from album_cat_rel where object_name = "%s" """%(str(categId))
	elif type(categId) == int:
		req = """select id_album from album_cat_rel where id_object = %s """%(categId)
	#print req
	c.execute(req)
	l = c.fetchall()
	albumL = [a[0] for a in l]
	
	req = """select path_crc32,album,album_type,object_type from album where id_album in (%s) """%(str(albumL)[1:-1])
	c.execute(req)
	l = c.fetchall()
	albumDDL_L = [{'key':a[0],'value':a[1],'album_type':a[2],'object_type':a[3]} for a in l]
	
	c.close()
	db.close()
	print('ddl ok')
	return {'artistL':artistDDL_L,'albumL':albumDDL_L}		

def artist_album_categorisation_delete(dbPath,objectL,categ_id,mode):	
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	
	if mode == 'artist':
		req = "delete from artist_cat_rel where id_artist in (%s) and id_object = %s"%(str(objectL)[1:-1],categ_id)
		c.execute(req)
		db.commit()
		#print req
		
	elif mode == 'album':
		req = "delete from album_cat_rel where id_album in (%s) and id_object = %s"%(str(objectL)[1:-1],categ_id)
		c.execute(req)
		db.commit()	
		#print req
		
	c.execute("select changes()")
	l = c.fetchone()	
	
	
	c.close()
	db.close()	
		
	if len(objectL) == l[0]:
		print('delete cat is OK')
		return 1
	else:
		print("error is dele cat",l[0])
		return 0
	
	
def artist_album_categorisation_and_save(dbPath,metaD,tagKey,tagD,rel_type,mode):
	if tagKey == 0:
		print('Eror : Noassgnement to 0-TAG')
		return
	s = ''
	resL = []
	sortedL = []
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	
	for a in metaD:
		req_ins = ''
		
		if mode == 'artist':
			rec = (tagKey,metaD[a]['id_artist'],tagD[tagKey],metaD[a]['artist'],metaD[a]['artist_crc32'],rel_type)
			req_ins = """insert into artist_cat_rel (id_object,id_artist,object_name,artist_name,artist_crc32,rel_type) values (%s,%s,"%s","%s",%s,"%s") """%rec
		elif mode == 'album':
			print(1)
			rec = (tagKey,metaD[a]['id_album'],tagD[tagKey],metaD[a]['album'],metaD[a]['path_crc32'],rel_type)
			print(2,rec)
			req_ins = """insert into album_cat_rel (id_object,id_album,object_name,album_name,album_crc32,rel_type) values (%s,%s,"%s","%s",%s,"%s") """%rec	
			
		try:
			c.execute(req_ins)
		except Exception as e:
			logger.critical('Exception: %s'%(str(e)))
		#print req_ins
		
	c.execute("select changes()")
	l = c.fetchone()	
	res = l[0]
	
	db.commit()
	c.close()
	db.close()	
	
	print('Updated for %s:%s'%(mode,res))
	return res
	
def Tag_Assignement_and_save(dbPath,metaD,tagKey,tagD):
	if tagKey == 0:
		logger.error('Error : No assgnement to 0-TAG')
		return
	s = ''
	resL = []
	sortedL = []
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	for a in metaD:
		rec = (tagKey,metaD[a]['id_track'],tagD[tagKey],a)
		req_ins = """insert into track_tag (id_tag,id_track,tag_name,path_crc32) values (%s,%s,"%s",%s) """%rec
		
		try:
			c.execute(req_ins)
		except Exception as e:
			logger.critical('Exception: %s in [%s]'%((str(e),str(req_ins))))
			logger.critical('a = %s'%((str(a))))
	
		
	db.commit()
	c.close()
	db.close()	
	
	return resL	
	
def Tag_to_Categ_save(dbPath,tagID,catID,tagD,categoryD):
	logger.debug('in Tag_to_Categ_save: tagID[%s],catID[%s] Start '%(str(tagID),str(catID)))		
	if tagID == 0:
		logger.error('Error : No assgnement to 0-TAG')
		return
	s = ''
	resL = []
	sortedL = []
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	try:
		rec = (str(tagID),str(catID),tagD[tagID]['tag_descr'],categoryD[catID]['cat_key'],tagD[tagID]['tag_type'])
	except Exception as e:	
		logger.critical('Error in Tag_to_Categ_save [%s] '%(str(e)))		
		print(str(tagD)[:300])
		print(str(categoryD)[:300])
		return 0
	req_ins = """insert into tag_cat_rel (id_tag,id_object,tag_name,object_name,rel_type) values (%s,%s,"%s","%s", "%s") """%rec
	print(req_ins)
		
	try:
		resL = c.execute(req_ins)
	except Exception as e:
		logger.critical('Exception: %s in [%s]'%((str(e),str(req_ins))))
		logger.critical('a = %s'%((str(a))))
	
	
	db.commit()
	c.close()
	db.close()	
	logger.debug('in Tag_to_Categ_save: Finished with res [%s] '%(str(resL)))		
	return resL		

def Tag_Assignement_delta_update(dbPath,deltaL,action,DB_metaIndxD,tagKey,tagD):
	# action - ��� �������� ���������: 'delete' �������� �� ������ ��� ���������� 'add'
	if tagKey == 0:
		print('Eror : Noassgnement to 0-TAG')
		return
	s = ''
	resL = []
	sortedL = []
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	#print "Tag_Assignement_delta_update --1"
	try:
		if action == 'add':
			#print "Tag_Assignement_delta_update --2",deltaL
			for a in deltaL:
				
				#print tagKey,a,len(metaD),metaD[a],tagD[tagKey]
				rec = (tagKey,DB_metaIndxD[a][0],tagD[tagKey],a)
			#	print rec
				req_ins = """insert into track_tag (id_tag,id_track,tag_name,path_crc32) values (%s,%s,"%s",%s) """%rec
			#	print req_ins
				c.execute(req_ins)
		elif action == 'delete':		
			#print "Tag_Assignement_delta_update --3"
			removeL_id = [DB_metaIndxD[a][0] for a in deltaL]
			req_del = """delete from track_tag where id_track in (%s) """%(str(removeL_id)[1:-1])
			#print req_del
			c.execute(req_del)
			
	except:
		print('db error in Tag_Assignement_delta_update')
		db.commit()
		c.close()
		db.close()	
		return 0
			
	db.commit()
	c.close()
	db.close()	
	
	return 1	

def create_stat_metaDataL_viaMetaD(metaD,*args):
	if args == ():
		print('Use: "artist" or "track" as a paramert')
	artistD ={}
	titleD ={}
	if 'artist' in args:
		for a in metaD:
			if 'artist' not in metaD[a]:
				continue
			if metaD[a]['artist'] not in artistD:
				artistD[metaD[a]['artist']]={'track_num':1}

			else:
				n = artistD[metaD[a]['artist']]['track_num']
				artistD[metaD[a]['artist']]['track_num'] = n +1


		l = [(artistD[a]['track_num'],a) for a in artistD]
		l.sort(reverse = True)
		return l
	if 'track' in args:
		for a in metaD:
			title = metaD[a]['title'].lower().replace(',',' ').replace('/',' ').replace('_',' ').replace('.',' ').strip()
			title = title.replace('the ',' ').replace(' a ',' ').replace('  ',' ').strip()
			
			if 'artist' in metaD[a]:
				artist = metaD[a]['artist'].lower().strip().replace(',',' ').replace('.',' ').replace('/',' ').replace('_',' ')
				artist = artist.replace('the ',' ').replace(' a ',' ').replace('  ',' ')
			
			if 'title' not in metaD[a]:
				continue
			
			
			if title not in titleD:
				artistD = {}
				if 'artist' in metaD[a]:
					artistD[artist] = 1
				else:
					artistD['NO_ARTIST'] = 1
				titleD[title]={'track_num':1,'artistD':artistD}
			else:
				artistD = {}
				titleD[title]['track_num'] = titleD[title]['track_num'] + 1
				if 'artist' in metaD[a]:
					if artist not in titleD[title]['artistD']:
						titleD[title]['artistD'][artist] = 1
					else:
						n = titleD[title]['artistD'][artist]
						titleD[title]['artistD'][artist] = n + 1
						
					
				else:
					if 'NO_ARTIST' in titleD[title]['artistD']:
						titleD[title]['artistD']['NO_ARTIST'] = titleD[title]['artistD']['NO_ARTIST'] + 1
					else:
						titleD[title]['artistD']['NO_ARTIST'] = 1
					
		l = [(titleD[a]['track_num'],a) for a in titleD]	
		l.sort(reverse = True)
		l = [a[1]	for a in l]	
		sorted_filteredL = []
		
		for a in l[1:]:
			if len(titleD[a]['artistD']) > 1:
				sorted_filteredL.append(a)


		for a in d['sorted_filteredL'][:200]:
		#	print '###############'
			print(d['sorted_filteredL'].index(a),' ->',a,len(d['titleD'][a]['artistD']))
		
		return	{'titleD':titleD,'sortedKeyL':l,'sorted_filteredL':sorted_filteredL}	

def getCategoryProfileDic(dbPath,*args):
	# returnes the Category dictionary, using the 'list_item_like' parametr returnes  items like structures 
	cat_typeD = {}
	categoryD = {}
	cat_profD = {}
	folderD = {}
	cat_prof_itemDL = []
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	c = db.cursor()
	
	if 'general_cat_folder' in args:
	# ����� ��������� ����� ��������� �������, ����� ��� ��������� ��������
		req = 'select id_group,ref_folder from groups_pl where ref_folder not NULL'
		c.execute(req)
		folderL = c.fetchall()
		for a in folderL:
			folderD[a[0]] = a[1]
	
	req = 'select * from category_type'
	c.execute(req)
	cat_typeL = c.fetchall()
	for a in cat_typeL:
		cat_typeD[a[0]] = {'indx':a[0],'type_key':a[1],'type_name':a[2],'descr':a[3],'relCatD':{},'relCatL':[]}
		
	req = 'select * from category'
	c.execute(req)
	catL = c.fetchall()
	for a in catL:
		folder = None
		if 'general_cat_folder' in args:
			if a[0] in folderD:
				folder = folderD[a[0]]	
		categoryD[a[0]] = {'cat_id':a[0],'cat_key':a[1],'cat_name':a[2],'descr':a[3],'color_set':a[4],'folder':folder}


	req = 'select * from category_profile'
	c.execute(req)
	relL = c.fetchall()
	
	for a in relL:
		if a[1] in categoryD and a[0] in cat_typeD:
			if 'list_item_like' in args:
				cat_typeD[a[0]]['relCatD'][a[1]]=categoryD[a[1]]
			cat_typeD[a[0]]['relCatL'].append(a[1])
	if 'list_item_like' in args:
		for a in cat_typeD:
			#print cat_typeD[a[0]]['relCatD']
			#print a[0],    cat_typeD[a[0]]

			if cat_typeD[a]['relCatD'] != {}:
				cat_type_item = cat_typeD[a].copy()
				del cat_type_item['relCatD']
				cat_type_item['relCatL'] = []

				for b in cat_typeD[a]['relCatD']:
					cat_type_item['relCatL'].append(cat_typeD[a]['relCatD'][b])
				cat_prof_itemDL.append(cat_type_item)

	return {'cat_typeD':cat_typeD,'categoryD':categoryD,'cat_prof_itemDL':cat_prof_itemDL}

	

def getPlaylistGroupRelDic(db):
	groupD = {}
	group2PlistD = {}
	# get group dictionary
	#{group_key,num,Short description, description}
	#f = open('group.cfg','r')
	#groupL = f.readlines()
	#f.close()
	
	c = db.cursor()
	req = 'select * from groups_pl'
	c.execute(req)
	groupL = c.fetchall()
	for a in groupL:
		try:
			folderL = []
			if a[7] != None:
				folderL = [str(b) for b in a[7].split(';') if b!='']
			groupD[str(a[1])] =  {'group_id':int(a[0]),'group_key':str(a[1]),'num':int(a[2]),'short_name':str(a[4]),'descr':a[3],'play_tag':a[5],'color_set':a[6],'ref_folderL':folderL}
		except:
			print('error at getPlaylistGroupRelDic:',str(a[1]),str(a[4]))
			continue
	
	for a in groupD:
		req = 'select listname from LIST2GROUP_REL where group_key = "%s"'%(a)
		c.execute(req)
		resL = c.fetchall()
		group2PlistD[str(a)] = []
		for b in resL:
			group2PlistD[str(a)].append(str(b[0]))
		#print 	group2PlistD[a]

	return {'groupD':groupD,'group2PlistD':group2PlistD}				
def loadTemplates_viaCFG(fname):
	f = open(fname,'r')
	l = f.readlines()
	f.close()
	configDict = {}	
	tmplD = {}	
	for a in l:
		if a.strip()[0] == '#': continue
		
		if '::' in a:
			configDict[a.split('::')[0].strip()] = {'TMPL':a.split('::')[1].strip()}
			continue
		# �������� ��� ������� ������ ���� ������ ������	
		if '=' in a:
			configDict[a.split('=')[0].strip()] = {'fname':a.split('=')[1].strip()}
			continue	
	
	
	#print configDict
	cur_dir = os.path.dirname(fname)
	for a in configDict:
		if 'fname' not in configDict[a]:
			continue
		f_name = cur_dir+'//'+configDict[a]['fname']	
		f = open(f_name,'r', encoding="cp1251")
		read_error_flag = False
		try:
			line = f.read()
		except Exception as e:
			logger.critical('Exception [%s] [%s] [%s] in loadTemplates_viaCFG'%(str(e),a,f_name))
			f.close()
			read_error_flag = True
			# код ниже оформить как отдельную ветку при ошибке
			#f = open(f_name,'r', errors='ignore')
			#return configDict
		if read_error_flag:
			f = open(f_name,'r', errors='ignore')
			try:
				line = f.read()
			except Exception as e:
				logger.critical('Exception 2 [%s] [%s] [%s] in loadTemplates_viaCFG'%(str(e),a,f_name))
				f.close()
				return configDict
				
			
		# try:
			# configDict[a]['TMPL'] = line.decode('utf8')
		# except Exception,e:
			# logger.critical("Error at loadTemplates_viaCFG[%s]: %s "%(a,str(e)))
		configDict[a]['TMPL'] = line
			
		f.close()
	return configDict
	

def readConfigData(fname):
	f = open(fname,'r')
	l = f.readlines()
	f.close()
	configDict = {'mpdMusicPathPrefix':'','audioFilesPathRoot':'','logPath':'','mediaPath':'','templatesPath':'','lossless_path':'','winampext':'','player_cntrl_port':0,'appl_cntrl_port':0,'commandRouting':'','dbPath':'','audio_files_path_list':[],'applicationPath':'','radioNodePath':'','imageNodePath':'','preprocessAlb4libPath':'','ml_folder_tree_buf_path':'','mpd_host_list':[]}	
	configDictCmlx = {'templatesPath':'','audio_files_path_list':[],'mpd_host_list':[]}	

	for a in l:
		
		if a == '\n': continue
		if a.strip()[0] == '#':	continue
		

# 		Обработка простых параметров конфига			
		for key in configDict:
			pos = a.find(key)
			if pos >=0:
				
				if key in configDictCmlx:
					break
				else:	
					configDict[key] = a.split('=')[1].strip()
				break
# 		Обработка сложных параметров конфига	
		
		if key == 'audio_files_path_list':
			configDict[key] = []
			try:
				path_strL = a.split('=')[1].strip().split(';')
				chkL = [b.strip() for b in  path_strL if b != '']
				for path in chkL:
					if not os.path.exists(path):
						print('Wrong  path! 3294:',[path], "-->Check in config:'audio_files_path_list='")
						#logger.critical("Wrong  path!:'%s, '-->Check in config:audio_files_path_list="%(str([path])))
						logger.critical("Wrong  path! -->Check in config:audio_files_path_list=")
					else:	
						configDict[key].append(path)
				continue		
						
			except:
				print("Error getting 'audio_files_path_list'")
				continue
				
		elif key == 'mpd_host_list':
			configDict[key] = []
			
			try:
				host_s = a.split('=')[1].strip().split(';')
				chkL = [b.strip() for b in  host_s if b != '']
				for host in chkL:
					hostL = host.split(':')
					configDict[key].append({'host':hostL[0],'socket':hostL[1]})
				continue		
						
			except:
				print("Error getting 'mpd_host_list'")
				continue		
				
			
		if key == 'templatesPath':	 
		
			if 'templatesD' not in configDict:
				configDict['templatesD'] = {l.index(a):{key:a.split('=')[1].strip(),'active':True}}
			else:
				configDict['templatesD'][l.index(a)] = {key:a.split('=')[1].strip(),'active':False}
				
			continue	

	return 	configDict	
				
def getTrackList(sPlaylistFilepath):
#   ������� ������������ �� ������� ����������� ��������
	return []    
	playlistfile = open(sPlaylistFilepath, "r")
	lines = playlistfile.readlines()
	playlistfile.close()
	playlist = []
	for line in lines:
		if ( not line[0]=='#' ) and ( not '#EXTM3U'in line):
			try:
				playlist.append(line.rstrip())
			except UnicodeEncodeError as e:
				logger.warning('3320 Error in getTrackList:%s'%(str(e)))
				playlist.append(line.rstrip())
				
	#	playlist.append(line)
	return playlist			
	
def DistinctAlbums_from_metaD(metaD,orderL):
	logger.debug(' in DistinctAlbums_from_metaD - start')
	resD = {}
	if orderL == []:
		orderL = list(metaD.keys())
	indx = 0	
	album_order_numb = 0
	for a in orderL:
		
		if a not in metaD:
			indx+=1
			logger.critical("-- Logical ERROR in DistinctAlbums_from_metaD - No metaD key:"+str(a))
			continue
			
		album = metaD[a]['album']
		
		if 'NA_' in metaD[a]['album'] or 'NA al' in metaD[a]['album']:
			try:
				album = os.path.dirname(metaD[a]['path'])
			except KeyError as e:
				print('Wrong key in album distinct prob metaD and orderLare not compatible:',e)
				indx+=1
				logger.debug('-- Logical ERROR in DistinctAlbums_from_metaD NA_ :'+str((key,album,indx)))
				logger.debug('--- in DistinctAlbums_from_metaD NA_ :'+str(e))
				continue
			pos = album.rfind('\\')+1
			album = album[pos:]
		
		#print album,pos
		key = metaD[a]['album_crc32']
		#indx = orderL.index(a)
		
		if key not in resD:
			# �������� ������ � �������
			resD[key]={'album':album,'firstFileIndex':indx,'album_order_numb':album_order_numb,'albumL':[(metaD[a]['title'],indx,metaD[a]['artist'],a,metaD[a]['time_str'],metaD[a]['artist_crc32'],metaD[a]['bitrate'])]}
			album_order_numb+=1
		else:
			resD[key]['albumL'].append((metaD[a]['title'],indx,metaD[a]['artist'],a,metaD[a]['time_str'],metaD[a]['artist_crc32'],metaD[a]['bitrate']))
		
		indx+=1	
		#print key,album,indx	
		logger.debug('-- in DistinctAlbums_from_metaD - OK:'+str((key,album,indx)))
	logger.debug('DistinctAlbums_from_metaD - OK')
	return resD
	
def rus_name_folder_test(init_dirL,*args):
	cnt = 0
	allmFD = {}
	cueD = {}
	flac_no_cueL = []
	ape_num = flac_num = all_alb_cnt = flac_no_cue_num = 0
	for init_dir in init_dirL:
		print()
		print('Scanning:',init_dir)
		i = 0
		for root, dirs, files in os.walk(init_dir):
			cue_flag = False
			origf = ''
			ftype = ''
			if i%100 == 0:
				print(i, end=' ')
			i+=1

			for a in files:

				ftype = None
				if a[a.rfind('.'):].lower().find('.ape') >= 0:
					ftype = 'ape'

				elif a[a.rfind('.'):].lower().find('.flac') >= 0:
					ftype = 'flac'
				elif a[a.rfind('.'):].lower().find('.mp3') >= 0:
					ftype = 'mp3'

				if	ftype != None:
					try:
						fname = (root+'\\'+a).lower()
					except:
						print(root+'\\'+a)
						return
						
					pos = root.rfind('\\')
					#pos_1 = a[:pos_2-2].rfind('\\')+1
					album = root[pos+1:]
					
					orig_fname = root+'\\'+a

					crc32 = zlib.crc32(fname)
					allmFD[crc32] = {'orig_fname':orig_fname,'album':album,'file':fname,'ftype':ftype,'cueNameIndx':None}
	return 	allmFD
	
	
def collect_albums_folders(init_dirL,*args):
# аналог функции myMediaLib_adm.collectMyMediaLib_folder_new(['G:\\MUSIC\\ORIGINAL_MUSIC']), только папки альбомов
	
	cnt = 0
	allmFD = {}
	albumDirL = []
	cueD = {}
	flac_no_cueL = []
	ape_num = flac_num = all_alb_cnt = flac_no_cue_num = 0
	for init_dir in init_dirL:
		print()
		print('Scanning:',init_dir)
		i = 0
		for root, dirs, files in os.walk(init_dir):
			cue_flag = False
			origf = ''
			ftype = ''
			if i%100 == 0:
				print(i, end=' ')
			i+=1	
			for a in files:
				cue_flag = False
				if a[a.rfind('.'):].lower().find('.cue') >= 0:
					origf = ''
					ftype = ''
					cue_name = (root+'\\'+a)

					try:	
						origfD = simple_parseCue(cue_name)	
					except NameError:
						import myMediaLib
						origfD = myMediaLib.simple_parseCue(cue_name)	

					try:
						if os.path.exists(origfD['orig_file_path']):
							cue_flag = True
							
							if root not in albumDirL:
								albumDirL.append(root)
							
						else:
							continue
					except:
						print('error:',origfD)
					break
			
			for a in files:
				
				ftype = None
				if a[a.rfind('.'):].lower().find('.ape') >= 0:
					ftype = 'ape'
					
				elif a[a.rfind('.'):].lower().find('.flac') >= 0:
					ftype = 'flac'
				elif a[a.rfind('.'):].lower().find('.mp3') >= 0:
					ftype = 'mp3'
				
				if	ftype != None:
					fname = (root+'\\'+a)
					orig_fname = root+'\\'+a 
					if root not in albumDirL:
						albumDirL.append(root)
			
			cnt+=1
			if cnt%100 == 0:
				print('.',len(allmFD), end=' ')

		return albumDirL		
	
def collectMyMediaLib_folder_new(init_dirL,audioFilesPathRoot,*args):
# Предварительный сбор метаданных для каждого из трэков из списка папок, с проверкой CUE и регистрацией последних изменений
# результат в allmFD - ключи это path_crc32 для трэка в дальнейшем
# path_crc32 для CUE - это CRC32(cue_file_name-запятая-порядковый номер трэка)  origfD['cue_f_name']+','+str(i)

# ���� ��������� ����������� �� ������ ���� � CRC32 c ������ CUE
#fd = """\\\\GOFLEX_HOME\\ExternalUSB\\Seagate\\Music\\ORIGINAL_MUSIC\\ORIGINAL_CLASSICAL\\Михаил Глинка\\Великие композиторы CD3-Глинка"""
#PathPrefix = '//GOFLEX_HOME/ExternalUSB/Seagate/Music/'
#rD = myMediaLib_adm.collectMyMediaLib_folder_new([fd],PathPrefix)
	logger.info('in collectMyMediaLib_folder_new dir:[%s].... - Start'%(str(init_dirL))[:500])
	cnt = 0
	allmFD = {}
	albumDirL = []
	cueD = {}
	songL = []
	flac_no_cueL = []
	cue_orig_files_crc32L = []
	
	cue_run_warning = False
	
	origfD = {}
	ape_num = flac_num = all_alb_cnt = flac_no_cue_num = 0
	
	audioFilesPathRoot = bytes(audioFilesPathRoot,encoding = BASE_ENCODING) 
	
	init_dir_checkedL = []
	
	for init_dir in init_dirL:
		init_dir_modif = b""
		if isinstance(init_dir, str):
			#char_codec = chardet.detect(init_dir)
			print([init_dir])
			try:
				#init_dir_modif = init_dir.decode(char_codec['encoding'])
				init_dir_modif = bytes(init_dir,encoding = BASE_ENCODING)
				init_dir_checkedL.append(init_dir_modif)
			except Exception as e:
				logger.critical('Exception [%s] in collectMyMediaLib_folder_new'%(str(e)))	
				return {'Error':e}
				
			if not os.path.exists(init_dir_modif):
				print([init_dir_modif], 'does not exists',type(init_dir_modif))
				logger.critical('Error: dir [%s] not exists in collectMyMediaLib_folder_new'%(str(init_dir_modif)))	
				return {'allmFD':allmFD,'cueL':cueD,'albumDirL':albumDirL}		
			
		elif isinstance(init_dir, bytes):
			if not os.path.exists(init_dir):
				print([init_dir], '2946 dir does not exists')
				logger.critical('Error: dir [%s] not exists in collectMyMediaLib_folder_new'%(init_dir))	
				return {'allmFD':allmFD,'cueL':cueD,'albumDirL':albumDirL,'Error':'dir %s not exists:'%(init_dir),'ErrorData':init_dir}
			else:
				init_dir_checkedL.append(init_dir)
	
	
	
	for init_dir in init_dir_checkedL:
		print()
		print('Scanning:',[init_dir])
		i = 0
		for root, dirs, files in os.walk(init_dir):
			cue_flag = False
			cue_run_warning = False
			origf = ''
			ftype = ''
			if i%100 == 0:
				print(i, end=' ')
			i+=1	
			
			#pos = root.rfind('\\')
			#album_path = root[pos+1:]
			album_rel_path = os.path.relpath(root,audioFilesPathRoot)
			if isinstance(album_rel_path,bytes):
				album_path_crc32 = zlib.crc32(album_rel_path)
			elif isinstance(album_rel_path,str):	
				album_path_crc32 = zlib.crc32(album_rel_path.encode(BASE_ENCODING))
			#print(album_rel_path)
			for a in files:
			       #if a.find('.ape') > 0 or a.find('.flac')
				cue_flag = False
				cue_run_warning = False
				# CUE file processing scenario
				if a[a.rfind(b"."):].lower().find(b".cue") >= 0:
					origf = ''
					ftype = ''
					#cue_name = (root+'\\'+a)
					cue_name = os.path.join(root,a)

					try:	
						# извлечение части метаданных для CUE образа или трэков
						# остальная часть (битрейт, время) будут извлекаться уже для точечно позже.
						origfD = parseCue(cue_name)
						
					except Exception as e:
						logger.critical('Error: 2955 in collectMyMediaLib_folder_new after parseCue[%s] '%(str(e)))
						logger.critical('Error: 2955 detailes cue_name:[%s] '%(str([cue_name])))
						return {'Error':e,'origfD':origfD,'parseCue-args':cue_name}
					
					ftype = origfD['fType']
					#origfD['cue_f_name_rel'] = os.path.relpath(cue_name,audioFilesPathRoot)
					
					if 'cue_tracks_number' in origfD:
					
						last_modify_date = 0
						try:
							last_modify_date = os.stat(origfD['cue_f_name']).st_mtime
						except:
							logger.critical('Error: 3590 in collectMyMediaLib_folder_new at last_modify_date cue_f_name:[%s] '%(origfD['cue_f_name']))
							print('eroror cue time',origfD['cue_f_name'])
							pass
					
						for i in range(1,origfD['cue_tracks_number']+1):
							
							
							if len(origfD['orig_file_pathL']) > 1 and origfD['cue_tracks_number'] == len(origfD['orig_file_pathL']):
								orig_file_path = origfD['orig_file_pathL'][i-1]['orig_file_path']
							elif len(origfD['orig_file_pathL']) == 1 and origfD['cue_tracks_number'] > 1:
								orig_file_path = origfD['orig_file_pathL'][0]['orig_file_path']
							else:
								orig_file_path = 'uncompliant and broken cue %d %d'%(origfD['cue_tracks_number'],len(origfD['orig_file_pathL']))
								
							fNameRel = os.path.relpath(orig_file_path,audioFilesPathRoot)
							CuefNameRel  = os.path.relpath(cue_name,audioFilesPathRoot)
							#origfD['cue_f_name_rel'] = os.path.relpath(cue_name,audioFilesPathRoot)
							#cue_crc32 = zlib.crc32(fNameRel.encode(BASE_ENCODING))
							
							#cue_item_name = origfD['cue_f_name']+','+str(i)
							#cue_item_name = fNameRel+','+str(i)
							if isinstance(fNameRel,bytes):
								cue_item_name_for_crc32 = fNameRel+bytes(str(i),encoding = BASE_ENCODING)
							elif isinstance(fNameRel,str):
								cue_item_name_for_crc32 = bytes((fNameRel+str(i)),encoding = BASE_ENCODING)
								
							cue_item_name = fNameRel
							songL.append(cue_item_name)	
							
							cue_item_name_crc32 = zlib.crc32(cue_item_name_for_crc32)
							
							print(i,'crc32=',cue_item_name_crc32,cue_item_name,'cue_item_name_for_crc32:',cue_item_name_for_crc32)
							cue_run_warning = True
							#allmFD[cue_item_name_crc32] = {'cue_f_name':origfD['cue_f_name'],'orig_fname':orig_file_path,'last_modify_date':last_modify_date,'album':origfD['trackD'][i]['Album'],'album_path':root,'album_crc32':album_path_crc32,'file':cue_item_name,'cueNameIndx':i,'ftype':ftype,'cue':'X','album_tracks_number':origfD['cue_tracks_number']}
							allmFD[cue_item_name_crc32] = {'cue_f_name':fNameRel,'cue_f_name_abs':cue_name,'orig_fname':orig_file_path,'last_modify_date':last_modify_date,'album':origfD['trackD'][i]['Album'],'album_path':album_rel_path,'album_crc32':album_path_crc32,'file':cue_item_name,'cueNameIndx':i,'ftype':ftype,'cue':'X','album_tracks_number':origfD['cue_tracks_number'],'cue_f_name_rel':CuefNameRel}
							
							
					
					cue_crc32 = origfD['cue_crc32']
					
					cue_orig_files_crc32L = []
					for track_fileD in origfD['orig_file_pathL']:
					# Пока реализация только для Image надо сделать и для tracks CUE
					# это нужно толко для статистики
						if track_fileD['file_exists']:
							cue_orig_files_crc32L.append(track_fileD['file_crc32'])
							cue_flag = True
							if origfD['fType'].lower() == 'flac':
								flac_num+=1
							elif origfD['fType'].lower() == 'ape':
								ape_num+=1
							else:
								print(origfD['fType'])
							origf = origfD['orig_file_pathL'][0]['orig_file_path']
							ftype = origfD['fType']
							#crc32 = zlib.crc32(origf.encode(BASE_ENCODING))
							last_modify_date = 0
							try:
								last_modify_date = os.stat(cue_name).st_mtime
							except:
								logger.critical('Error: 3634 in collectMyMediaLib_folder_new at last_modify_date orig_file_pathL:[%s] '%(origfD['orig_file_pathL'][0]))
								print('eroror cue time',origfD['orig_file_pathL'][0])
								pass
								
							if root not in albumDirL:
								albumDirL.append(root)
						else:
							continue
							
						cueD[cue_crc32]={'dir':root,'filename':a,'file':origf,'ftype':ftype,'songL':songL,'last_modify_date':last_modify_date,'cueFName':cue_name}	
					
					break
			
			for a in files:
				
				ftype = None
				if a[a.rfind(b"."):].lower().find(b".ape") >= 0:
					ftype = 'ape'
					
				elif a[a.rfind(b"."):].lower().find(b".flac") >= 0:
					ftype = 'flac'
				elif a[a.rfind(b"."):].lower().find(b".mp3") >= 0:
					ftype = 'mp3'
				
				if	ftype != None:

					orig_fname = os.path.join(root,a)
					fname_rel = os.path.relpath(orig_fname,audioFilesPathRoot)

					#print type(root),type(a),type(orig_fname)
					#logger.debug('3652 in collectMyMediaLib_folder_new. orig_fname:[%s] [%s]'%(root,a))
					
					# Расчитываем 2 CRC32 для оригинального имени, чтобы отсечь попадание файла образа в список и CRC32 для относительных имен, для сохранения и проверок по BD
					if isinstance(fname_rel,bytes):
						crc32 = zlib.crc32(fname_rel)
					elif isinstance(fname_rel,str):	
						crc32 = zlib.crc32(bytes(fname_rel, encoding = BASE_ENCODING))
						
					if isinstance(orig_fname,bytes):
						cue_crc32 = zlib.crc32(orig_fname)
					elif isinstance(orig_fname,str):	
						cue_crc32 = zlib.crc32(bytes(orig_fname, encoding = BASE_ENCODING))	
					#if crc32 == 1133272172:
					#	return fname
					
					last_modify_date = 0
					try:
						last_modify_date = os.stat(orig_fname).st_mtime
					except:
						logger.critical('Error: 3673 in collectMyMediaLib_folder_new at last_modify_date')
						pass
					
					
					pos = root.rfind(b"\\")
					#pos_1 = a[:pos_2-2].rfind('\\')+1
					album = root[pos+1:]
					print(album) 
					album = os.path.dirname(root)
					print(album) 
					#logger.debug('3667 in collectMyMediaLib_folder_new. orig_fname:[%s] [%s]'%(orig_fname,str(type(orig_fname))))
					
					#print root
					
					# Проверка новая на уже зарегистрированные для CUE медиафайлы, 
					# Пропускать их или зафиксировать изменение отдельного медиафайла, для куе надо регистрировать изменение CUE 
					# изменения дат медиафайлов не важны
					# словарь allmFD для CUE был сформирована выше
					if cue_crc32 in cue_orig_files_crc32L:
						continue
						pass
					
					else:
						# Формируем предварительный словарь метаданных для случая отдельных трэков НЕ CUE !!! NOT CUE
						if root not in albumDirL:
							albumDirL.append(root)
						if len(cue_orig_files_crc32L) > 0 and cue_run_warning:
							print('Warning, might be error with this file in CUE',cue_crc32)
							print(origfD['orig_file_pathL']) 
							print('fname=',[orig_fname])
							if orig_fname == origfD['orig_file_pathL'][0]['orig_file_path']:
								print('fname - OK')
							logger.warning('Warning in collectMyMediaLib_folder_new: might be error with this file in CUE [%s]'%(str(cue_crc32)))		
							logger.warning('Warning in collectMyMediaLib_folder_new: might be error with this file in CUE 2 [%s]'%(str(orig_fname)))		
						
						allmFD[crc32] = {'orig_fname':orig_fname,'last_modify_date':last_modify_date,'album_path':album_rel_path,'album':'','album_crc32':album_path_crc32,'file':orig_fname,'ftype':ftype,'cueNameIndx':None,'dir':root,
						'album_tracks_number':0,'f_name_rel':fname_rel}
			
			if 'stat' not in args:
				continue
				
			for a in files:
				#crc32 = zlib.crc32(str(root).lower()+'\\'+a.lower())
				#allmFL[crc32] = str(root).lower()+'\\'+a.lower() 
				if a[a.rfind('.'):].find('.mp3') >= 0:
					all_alb_cnt += 1
					break
				elif a[a.rfind('.'):].find('.ape') >= 0:
					all_alb_cnt += 1
					break
				elif a[a.rfind('.'):].find('.flac') >= 0:
					if not cue_flag:
						flac_no_cue_num +=1
						flac_no_cueL.append(root)
					else:
						#print 'cue',
						pass
					all_alb_cnt += 1
					break
			cnt+=1
			if cnt%100 == 0:
				print('.',len(allmFD), end=' ')
				
	logger.info('in collectMyMediaLib_folder_new - Finished')			
	if 'stat' in args:
		print()
		print('cueL:',len(cueD),'ape_num:',ape_num,'flac_num:',flac_num,'flac_no_cue_num:',flac_no_cue_num,'all_alb_cnt:',all_alb_cnt)
		return {'allmFD':allmFD,'cueL':cueD,'flac_no_cueL':flac_no_cueL,'ape_num':ape_num,'flac_num':flac_num,'all_alb_cnt':all_alb_cnt,'flac_no_cue_num':flac_no_cue_num}
	else:
		
		return {'allmFD':allmFD,'cueL':cueD,'albumDirL':albumDirL}	
		
def remove_missing_fromDB(dbPath,metaD,dirL):
# cleares TRACK table from not existed path
	if dirL == [] or dirL == None:
		dirL = ['G:\\MUSIC\\ORIGINAL_MUSIC','G:\\MUSIC\\MP3_COLLECTION']
	
	r = collectMyMediaLib_folder_new(dirL)
	metaD = r['allmFD']
	db = sqlite3.connect(dbPath)
	db_indxD = getMedialibDb_Indexes(db)
			
	removeL = [] 
	removeL_id = [] 
	for a in db_indxD:
		if a not in metaD:
			removeL.append(a)
			removeL_id.append(db_indxD[a][0])
			
	missedD = getCurrentMetaData_fromDB_via_DbIdL(removeL_id,db)
			#print missedD
			
	for a in removeL:
		print(removeL.index(a),missedD[a]['path'])
		
	req = "delete from track where id_track in (%s)"%(str(removeL_id)[1:-1])
	c = db.cursor()
	r = c.execute(req)
#print r
	c.close()
	db.commit()
	db.close()
	#print req
		
def get_artist_stats_from_metaD(metaD,search_term):
	albumD = {}
	for a in metaD:
		if search_term.lower() in metaD[a]['artist'].lower():
			if metaD[a]['album_crc32'] in albumD:
				albumD[metaD[a]['album_crc32']]['songNum'] = albumD[metaD[a]['album_crc32']]['songNum']+1
			else:
				albumD[metaD[a]['album_crc32']] = {'artist':metaD[a]['artist'],'album':metaD[a]['album'],'songNum':1}
	return  albumD

def get_all_artists_in_metaD(metaD,search_obj_key,search_termL,*args):
	# ������ ������� ����� ������ �� ��������� �������, �����, ��� ��� � ������� metaD ���� ������ ��� ���������.
	# search_obj_key - ���������� �� ������ ������� ������� ��� ������� ����� ���� �����-����������
	logger.debug('in get_all_artists_in_metaD mode=[%s], len=[%s] args=[%s]- Start'%(str(search_obj_key),str(len(metaD)),str(args)))
	if 'Search_text' in search_termL:
		search_termL = ['',]
	else:
		if '' in search_termL and len(search_termL)>1:
			search_termL.remove('')
	artistD = {}
	dirD = {}
	
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	
	
	ref_artL = [a[0] for a in getAll_Main_Artist_fromDB(db)]
	all_artL = [a[0] for a in getAll_Main_Artist_fromDB(db,'all')]
	
	albumMapD =  getAlbumD_fromDB(None,db,None,[])['albumMapD']
	
	db.close()
	
	all_albumL = [albumMapD[a] for a in albumMapD]
	#print all_albumL
	if 'with_album_stat' in args:
		artistBufType = 'with_album_stat'
	else:
		artistBufType = 'simple'
	foundL = []
	#print 'get_all_artists_in_metaD-1',search_termL
	skip_flag = True
	for a in metaD:
		#print('get_all_artists_in_metaD-1',a)
		skip_flag = True
		
		if 'new_only' in args:
			if metaD[a]['album_crc32'] in all_albumL:
				continue
		
		
		for search_term in search_termL:
			try:
				if search_term.lower().strip() not in metaD[a][search_obj_key].lower().strip() and search_term.lower().strip() != '':
					
					continue
			except UnicodeDecodeError:
				try:
					if search_term.lower().strip() not in metaD[a][search_obj_key].decode('utf-8').lower().strip() and search_term.lower().strip() != '':
						continue
				except UnicodeDecodeError as e:	
					logger.warning('3820 Error in get_all_artists_in_metaD:%s'%(str(e)))
					try:
						if search_term.lower().strip() not in metaD[a][search_obj_key].decode('cp1251').lower().strip() and search_term.lower().strip() != '':
							continue
					except UnicodeDecodeError:	
						logger.critical('3825 Error in get_all_artists_in_metaD:%s'%(str(e)))
						print('Decoding error with key in get_all_artists_in_metaD',a) 
						continue
						
					print('Decoding error with key in get_all_artists_in_metaD',a) 
					continue
			skip_flag = False	
			
			break
		
		if skip_flag: continue	
		
		if search_term not in foundL:
			foundL.append(search_term)
		
		#print 'artist:',metaD[a]['artist']		
			#print 'error at search term conversion',search_term
			#,search_term = ''
			
		print('before len',a)	
			
		if len(metaD[a]['artist'].lower().strip()) >= 2:
			try:
				artist_crc32 = zlib.crc32(bytes(metaD[a]['artist'].lower().strip(),encoding = 'utf8'))
				#logger.debug('in get_all_artists_in_metaD found artist crc32[%s]'%str(artist_crc32))
			except Exception as e:
				logger.critical('in get_all_artists_in_metaD Error 3946: [%s], %s'%(str(e),str(a)))
				
			dir_path = os.path.dirname(metaD[a]['path'])
			
			#dir_path_crc32 =  zlib.crc32(dir_path)
			#if dir_path_crc32 not in dirD:
			#	dirD[dir_path_crc32] = {'dir_path':dir_path,'album':metaD[a]['album'],'id_trackL':[metaD[a]['id_track']]}
			#else:
		#		dirD[dir_path_crc32]['id_trackL'].append(metaD[a]['id_track'])
			try:
				key_2 = zlib.crc32(bytes(metaD[a]['album'].lower().strip(),encoding = 'utf8'))	
				#logger.debug('in get_all_artists_in_metaD found album crc32[%s]'%str(key_2))
			except Exception as e:
				logger.critical('in get_all_artists_in_metaD Error 3960: [%s], %s'%(str(e),str(a)))	
				
			key = metaD[a]['album_crc32']
			
			
			album_is_in_db = False
			if key in all_albumL:
			
				album_is_in_db = True	
			
			# ���� ������ ��� �� ��������������  � ������� �� ������� ��� ���� ��������� ������ � �������
			print('before 3962',a)
			if artist_crc32 not in artistD:
				main = False
				if artist_crc32 in ref_artL:
					main = True
					
				is_in_db = False
				if artist_crc32 in all_artL:
					is_in_db = True	
				
				
					
				artistD[artist_crc32] = {'artist':metaD[a]['artist'].lower().strip(),'id_trackL':[metaD[a]['id_track']],'albumD':{},'dir_pathD':{},'main':main,
																																	'is_in_db':is_in_db,'is_in_rep':False}
				if	artistBufType == 'simple':
					continue
				
				
				
					
				artistD[artist_crc32]['albumD'][key] = {'album':metaD[a]['album'],'format':metaD[a]['format'],'song_num':1,'album_crc32':key_2,'dir_path_crc32':metaD[a]['album_crc32'],'dir_path':dir_path,'is_in_db':album_is_in_db}
				artistD[artist_crc32]['dir_pathD'][dir_path] = {'format':metaD[a]['format'],'song_num':1,'dir_path_crc32':key}
				
				
			else:
				if	artistBufType == 'simple':
					continue
				artistD[artist_crc32]['id_trackL'].append(metaD[a]['id_track'])
				
				if key not in artistD[artist_crc32]['albumD']:
					artistD[artist_crc32]['albumD'][key] = {'album':metaD[a]['album'],'format':metaD[a]['format'],'song_num':1,
					'album_crc32':key_2,'dir_path_crc32':metaD[a]['album_crc32'],'dir_path':dir_path,'is_in_db':album_is_in_db}
					
				else:
					artistD[artist_crc32]['albumD'][key]['song_num'] = artistD[artist_crc32]['albumD'][key]['song_num']+1
					
				if 	dir_path not in artistD[artist_crc32]['dir_pathD']:
					artistD[artist_crc32]['dir_pathD'][dir_path] = {'format':metaD[a]['format'],'song_num':1,'dir_path_crc32':metaD[a]['album_crc32']}
				else:	
					artistD[artist_crc32]['dir_pathD'][dir_path]['song_num']= artistD[artist_crc32]['dir_pathD'][dir_path]['song_num'] +1
	
	logger.debug('in get_all_artists_in_metaD 4001- After search')	
	l = []
	if	artistBufType == 'with_album_stat':
		l = [(len(artistD[a]['albumD']),len(artistD[a]['dir_pathD']),len(artistD[a]['id_trackL']),a) for a in artistD]
		l.sort(reverse=True)	
		
	not_single_artist_albumL = []
	album_songD = {}	
	if 'album_va_check' in args:
		print('in album_va_check:')
		if foundL != []:
			
			all_albumes_keyLset = set()
			for a in artistD:
				#print 'set:',set(artistD[a]['albumD'].keys())
				all_albumes_keyLset = all_albumes_keyLset.union(set(artistD[a]['albumD'].keys()))
			
			#print 'all_albumes_keyLset:',all_albumes_keyLset	
			
			
			for a in metaD:
				album_crc32 = metaD[a]['album_crc32']
				try:
					key_2 = zlib.crc32(bytes(metaD[a]['album'].lower().strip(),encoding = 'utf8'))
					#logger.debug('in get_all_artists_in_metaD found album va crc32[%s]'%str(key_2))
				except Exception as e:
					logger.critical('in get_all_artists_in_metaD Error 4037: [%s], %s'%(str(e),str(a)))	
				
				if album_crc32 in all_albumes_keyLset:
					
					
					artist_crc32 = metaD[a]['artist_crc32']
					
					album_is_in_db = False
					if album_crc32 in all_albumL:
						album_is_in_db = True
					
					artist_is_in_db = False
					if artist_crc32 in all_artL:
						artist_is_in_db = True	
						
					main_artist = False
					if artist_crc32 in ref_artL:
						main_artist = True	
					
					if album_crc32 not in album_songD:
						cur_album_artistD = {}
						
						cur_album_artistD[artist_crc32] = {'artist':metaD[a]['artist'],'songL':[a,],'song_num':1,'main':main,'is_in_db':artist_is_in_db}
						album_songD[album_crc32]={'album':metaD[a]['album'],'artistD':cur_album_artistD,'format':metaD[a]['format'],
													'album_songL':[a,],'album_song_num':1,'is_in_db':album_is_in_db,'not_single_artist':True,
													'dir_path_crc32':album_crc32,'dir_path':os.path.dirname(metaD[a]['path']),'album_crc32':key_2}
													
				
						
					else:
						if artist_crc32 not in album_songD[album_crc32]['artistD']:
							
							album_songD[album_crc32]['artistD'][artist_crc32] = {'artist':metaD[a]['artist'],'songL':[a,],
																				'song_num':1,'is_in_db':artist_is_in_db,'main':main_artist}
							
						else:
							album_songD[album_crc32]['artistD'][artist_crc32]['songL'].append(a)
							album_songD[album_crc32]['artistD'][artist_crc32]['song_num'] += 1
							
						album_songD[album_crc32]['album_songL'].append(a)
						album_songD[album_crc32]['album_song_num'] += 1
			
			#print 1
			for a in artistD:
				for b in artistD[a]['albumD']:
					#print a,b
					#print 'artistD[a].keys():',artistD[a].keys()
					real_song_num = album_songD[b]['album_song_num']
					if artistD[a]['albumD'][b]['song_num'] != real_song_num:
						artistD[a]['albumD'][b]['not_single_artist'] = True
						#album_songD[b]['song_num'] = real_song_num
						if b not in not_single_artist_albumL:
							not_single_artist_albumL.append(b)
					else:
						artistD[a]['albumD'][b]['not_single_artist'] = False
			
				
	logger.debug('in get_all_artists_in_metaD - Finished')			
	return  {'artistD':artistD,'statL':l,'search_term':str(search_termL),'foundL':foundL,'search_termL':search_termL,'ref_artL':ref_artL,
					'artistBufType':artistBufType,'not_single_artist_albumL':not_single_artist_albumL,'album_songD':album_songD}

def get_artists_in_metaD_via_ArtistDbL(metaD,artist_crc32L,*args):
	
	artistD = {}
	dirD = {}
	ref_artL = [a[0] for a in getAll_Main_Artist_fromDB(db)]
	all_artL = [a[0] for a in getAll_Main_Artist_fromDB(db,'all')]
	if 'with_album_stat' in args:
		artistBufType = 'with_album_stat'
	else:
		artistBufType = 'simple'
	foundL = []
	
	skip_flag = True
	for a in metaD:
		#print 'get_all_artists_in_metaD-1',a
		skip_flag = True
		for crc32 in artist_crc32L:
			
			if crc32 not in metaD:
				continue
			
			skip_flag = False	
			
			break
		
		if skip_flag: continue	
		
			
		
		artist_crc32 = zlib.crc32(metaD[a]['artist'].lower().strip())
		dir_path = os.path.dirname(metaD[a]['path'])
				
		if artist_crc32 not in artistD:
			main = False
			if artist_crc32 in ref_artL:
				main = True
				
			is_in_db = False
			if artist_crc32 in all_artL:
				is_in_db = True	
			
				
			artistD[artist_crc32] = {'artist':metaD[a]['artist'].lower().strip(),'id_trackL':[metaD[a]['id_track']],'albumD':{},'dir_pathD':{},'main':main,
																																'is_in_db':is_in_db,'is_in_rep':False}
			if	artistBufType == 'simple':
				continue
			artistD[artist_crc32]['albumD'][metaD[a]['album']] = {'format':metaD[a]['format'],'song_num':1,'album_crc32':zlib.crc32(metaD[a]['album'].lower().strip())}
			artistD[artist_crc32]['dir_pathD'][dir_path] = {'format':metaD[a]['format'],'song_num':1}
			
			
		else:
			if	artistBufType == 'simple':
				continue
			artistD[artist_crc32]['id_trackL'].append(metaD[a]['id_track'])
			
			if metaD[a]['album'] not in artistD[artist_crc32]['albumD']:
				artistD[artist_crc32]['albumD'][metaD[a]['album']] = {'format':metaD[a]['format'],'song_num':1,'album_crc32':zlib.crc32(metaD[a]['album'].lower().strip())}
				
			else:
				artistD[artist_crc32]['albumD'][metaD[a]['album']]['song_num'] = artistD[artist_crc32]['albumD'][metaD[a]['album']]['song_num']+1
				
			if 	dir_path not in artistD[artist_crc32]['dir_pathD']:
				artistD[artist_crc32]['dir_pathD'][dir_path] = {'format':metaD[a]['format'],'song_num':1}
			else:	
				artistD[artist_crc32]['dir_pathD'][dir_path]['song_num']= artistD[artist_crc32]['dir_pathD'][dir_path]['song_num'] +1
	
	l = []
	if	artistBufType == 'with_album_stat':
		l = [(len(artistD[a]['albumD']),len(artistD[a]['dir_pathD']),len(artistD[a]['id_trackL']),a) for a in artistD]
		l.sort(reverse=True)	
				
	return  {'artistD':artistD,'statL':l,'foundL':foundL,'ref_artL':ref_artL,'artistBufType':artistBufType}
	
	
def getAlbumD_fromDB(dbPath,db,albumCRC32,albumCRC32L,*args):
	logger.debug('in getAlbumD_fromDB - Start')
	extDbFlag = False
	
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
		#db.text_factory = str
		
	
		
	fieldD = getTableInfo('album',db)
	fieldL = [fieldD[a]['field_name']for a in fieldD]
		
	str_fld = ''
	str_fld = ','.join([a for a in fieldL])
	
	resD = {}
	
	c = db.cursor()
	mode_str = '' 
	if albumCRC32L != []:
		req = 'select * from ALBUM where path_crc32 in (%s)'%(str(albumCRC32L)[1:-1])
		mode_str = str(albumCRC32L)
	elif albumCRC32 != None:
		req = 'select * from album where path_crc32 = %s'%(str(albumCRC32))
		mode_str = str(albumCRC32)
	else:
		req = 'select * from album'
		mode_str = '[all]'
	try:	
		c.execute(req)
	except Exception as e:	
		print(e)
		print(req)

	l =c.fetchall()
	
	#print req
	#print l
	lineD = {}
	for a in l:
		lineD = {}
		for i in range(len(a)):
			lineD[fieldL[i]] = a[i]
			
		lineD['ref_artistL'] = []	
		lineD['all_track_num'] = 0
		resD[lineD['path_crc32']] = lineD
		
		
		#print lineD['artist_crc32'],lineD
		#print resD[lineD['artist_crc32']],resD[lineD['artist_crc32']]['artist']
		#print '-------------------'
		
	
		
	if 'wo_reflist'	in args:
		c.close()
		if extDbFlag:
			db.close()
		#print 'OK wo_reflist'
		logger.debug('in getAlbumD_fromDB - Finished 1')
		return {'albumD':resD,'albumMapD':{}}	
		
		
	if albumCRC32 != None:
		req = 'select * from ARTIST_ALBUM_REF where album_crc32 = %s'%(str(albumCRC32))
	elif albumCRC32L != []:
		req = 'select * from ARTIST_ALBUM_REF where album_crc32 in (%s)'%(str(albumCRC32L)[1:-1])	
	else:
		req = 'select * from ARTIST_ALBUM_REF'	
	
	try:
		c.execute(req)
	except Exception as e:	
		print(e)
		print(req)
	#print req

	l =c.fetchall()
	
	if 'with_tracks_number'	in args:
		track_cnt = 0
		for a in l:
			resD[a[3]]['all_track_num']+=a[5]
			
	
					
	if 'with_ref_artistL' not in args:
		c.close()
		
		print('OK with_ref_artistL not in args:',mode_str)
		logger.debug('in getAlbumD_fromDB - Finished 2')
		return {'albumD':resD,'albumMapD':{}}	
	
	albumMapD = {}
	for a in resD:
		albumMapD[a] = resD[a]['path_crc32']

	for a in resD:
		for b in l:
			if a == b[1]:
				resD[a]['ref_artistL'].append(b[0])	
				
				
	if 'with_ref_album2album' not in args:
		c.close()
		
		print('OK with_ref_album2album')
		logger.debug('in getAlbumD_fromDB - Finished 3')
		return {'albumD':resD,'albumMapD':{}}	
		
		
	if albumCRC32 != None:
		req = 'select * from ALBUM_REFERENCE where album_crc32 = %s'%(str(albumCRC32))
	elif albumCRC32L != []:
		req = 'select * from ALBUM_REFERENCE where album_crc32 in (%s)'%(str(albumCRC32L)[1:-1])
	else:
		req = 'select * from ALBUM_REFERENCE'	
	
	try:	
		c.execute(req)
	except Exception as e:	
		print(e)
		print(req)
	#print req

	l =c.fetchall()
	
	

	for a in resD:
		for b in l:
			if a == b[0]:
				resD[a]['ref_album_crc32L'].append(b[1])				
		
	
	c.close()
	if extDbFlag:
		db.close()
		
	logger.debug('in getAlbumD_fromDB - Finished 4')
	return {'albumD':resD,'albumMapD':albumMapD}
	
	
def getArtistD_fromDB(dbPath,artistCRC32,artistCRC32L,*args):

	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	fieldD = getTableInfo('artist',db)
	fieldL = [fieldD[a]['field_name']for a in fieldD]
		
	str_fld = ''
	str_fld = ','.join([a for a in fieldL])
	
	resD = {}
	
	c = db.cursor()
	if artistCRC32L != []:
		req = 'select * from ARTIST where artist_crc32 in (%s)'%(str(artistCRC32L)[1:-1])
	elif artistCRC32 != None:
		req = 'select * from ARTIST where artist_crc32 = %s'%(str(artistCRC32))
	else:
		#print "get All artist"
		req = 'select * from ARTIST'
		#print req
		
		
	c.execute(req)
	#print req

	l =c.fetchall()
	
	#print l
	lineD = {}
	for a in l:
		lineD = {}
		for i in range(len(a)):
			lineD[fieldL[i]] = a[i]
			
		lineD['ref_artist_crc32L'] = []	
		resD[lineD['artist_crc32']] = lineD
		
		#print lineD['artist_crc32'],lineD
		#print resD[lineD['artist_crc32']],resD[lineD['artist_crc32']]['artist']
		#print '-------------------'
		
	if 'wo_reflist'	in args:
		c.close()
		db.close()
		return resD		
		
		
	if artistCRC32 != None:
		req = 'select * from ARTIST_REFERENCE where artist_crc32 = %s'%(str(artistCRC32))
	else:
		req = 'select * from ARTIST_REFERENCE'	
		
	c.execute(req)
	#print req

	l =c.fetchall()
	
	

	for a in resD:
		for b in l:
			if a == b[0]:
				resD[a]['ref_artist_crc32L'].append(b[1])	
		
	
	c.close()
	db.close()
	return resD	
	
def getAlbum_parentObjects(dbPath,album_crc32):
	album_p_D = {}
	artist_p_D = {}
	artistD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(dbPath,None,[],[album_crc32],'with_artist_metaD','with_album_metaD','with_relation')
	try:
		artist_p_D = artistD['album_rel_artistD'][album_crc32]['artistD']
		artist_p_D = [{'key':a,'rel_type':artist_p_D[a]['rel_type']} for a in artist_p_D if artist_p_D[a]['track_num'] == 0]
	except:
		print('3523 Error in getArtist_Album_relationD_and_simpleMetaD_viaCRC32L:',artistD)
		logger.critical('3523 Error in getArtist_Album_relationD_and_simpleMetaD_viaCRC32L:')

	albumD = getAlbum_relation_metaD(dbPath,None,album_crc32,'only_to_rel','get_neibor')
	try:
		album_p_D = albumD['albums_to_relLD']
		
	except:
		print('Error in getArtist_Album_relationD_and_simpleMetaD_viaCRC32L:',artistD)
		logger.critical('3531 Error in getArtist_Album_relationD_and_simpleMetaD_viaCRC32L:')
		
	# �������� ��� �� ������� ����.������������ 3� ��������� �������� ��������
	if album_p_D != {}:
		pass
	artistL = [item['key'] for item in artist_p_D]	
	albumL = [item['key'] for item in album_p_D]	
	
	artist_albumD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(dbPath,None,artistL,albumL,'with_artist_metaD','with_album_metaD')
	for item in artist_p_D:
		if item['key'] in artist_albumD['artistD']:
			item['artist'] = artist_albumD['artistD'][item['key']]['artist']
	
	for item in album_p_D:
		if item['key'] in artist_albumD['albumD']:
			item['album'] = artist_albumD['albumD'][item['key']]['album']	
			
	#print artist_albumD	
	
	return {'album_p_D':album_p_D,'artist_p_D':artist_p_D}
	
def getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(dbPath,db,artistCRC32L,albumCRC32L,*args):	
	# ������� ��������� ����
	extDbFlag = False
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
		#db.text_factory = str
		
	c = db.cursor()
	
	album_relD = {}
	obratn_relD = {}
	artist_relD = {}
	albumD = {}
	artistD = {}
	artistL_extend = []
	
	if artistCRC32L != []:
		if 'with_relation'  in args:
			req = 'select * from ARTIST_ALBUM_REF where artist_crc32 in (%s)'%(str(artistCRC32L)[1:-1])	
				#print req 
			c.execute(req)	
			l =c.fetchall()
			
			for a in l:
				if a[2] not in artist_relD:
					artist_relD[a[2]] = {'id_artist':a[0],'albumD':{a[3]:{'track_num':a[5],'rel_type':a[4]}}}
				else:
					artist_relD[a[2]]['albumD'][a[3]] = {'track_num':a[5],'rel_type':a[4]}
				
		if 'with_artist_metaD' in args:
			req = 'select * from ARTIST where artist_crc32 in (%s)'%(str(artistCRC32L)[1:-1])	
			c.execute(req)	
			l =c.fetchall()
			
			for a in l:
				if a[2] not in artistD:
					artistD[a[2]] = {'id_artist':a[0],'artist':a[1],'main':a[3],'search_term':a[4],'search_term_crc32':a[5]}	
				else:
					logger.critical('Logical error (duplicat artist crc32) in artist meta data fm getArtist_Album_relationD_and_simpleMethD_viaCRC32L key:%s'%str(a[2]))
					
				
	if albumCRC32L != []:
		if 'with_relation'  in args:
			req = 'select * from ARTIST_ALBUM_REF where album_crc32 in (%s)'%(str(albumCRC32L)[1:-1])	
				#print req 
			c.execute(req)	
			l =c.fetchall()
			
			for a in l:
				if a[3] not in album_relD:
					album_relD[a[3]] = {'id_album':a[1],'artistD':{a[2]:{'track_num':a[5],'rel_type':a[4]}}}
				else:
					album_relD[a[3]]['artistD'][a[2]] = {'track_num':a[5],'rel_type':a[4]}
				# �������� ��� ������ ����� ����������� ������� (�� NSA) �� �������� ������� ���������� �������, ��������� ����� ����� �������� � ����������� ������
				if artistCRC32L != []:
					if a[2]	not in artistD:
						if a not in artistL_extend:
							artistL_extend.append(a[2])
				
		if 'with_album_metaD' in args:
			req = 'select * from ALBUM where path_crc32 in (%s)'%(str(albumCRC32L)[1:-1])	
			c.execute(req)	
			l =c.fetchall()
			
			
			
			
			for a in l:		
				album_type = a[12]
				key = a[4]
				#if album_type == '' and key in artistL_extend:
				#	artistL_extend.remove(key)
				if key not in albumD:
					albumD[key] = {'id_album':a[0],'album':a[1],'main':a[3],'format':a[5],'search_term':a[8],'search_term_crc32':a[9],'main':a[10],'album_type':album_type,'tracks_num':a[13]}	
				else:
					logger.critical('Logical error (duplicat album crc32) in album meta data fm getArtist_Album_relationD_and_simpleMethD_viaCRC32L key:%s'%str(a[2]))
		
	c.close()
	if extDbFlag:
		db.close()
	return {'artist_rel_albumD':artist_relD,'album_rel_artistD':album_relD,'artistD':artistD,'albumD':albumD,'artistL_extend':artistL_extend}
	
def getAlbum_list_db_via_AAT_search_term(dbnew_search_termL,prev_search_res_idL,DB_meta_Search_IndxD):
	# Get album list via intersection of Artist-Album-Track search
	#cfgD = readConfigData(mymedialib_cfg)
	#dbPath = cfgD['dbPath']
	resultL = resL = []
	resD = {}
	time_1 = time.time()
	for term in dbnew_search_termL:
		
		resL = []
		for idx in DB_meta_Search_IndxD:
			#print idx, DB_meta_Search_IndxD[idx],DB_meta_Search_IndxD[idx][7]
			#print '*',
			if term.lower() in DB_meta_Search_IndxD[idx][7]:
				resL.append((idx,DB_meta_Search_IndxD[idx][2]))
		
		#resL = list(set(resL))
		
		#print len(resL)
		if resL not in prev_search_res_idL:
			prev_search_res_idL.append(resL)

	#print 'prev_search_res_idL:',len(prev_search_res_idL)

	result = list(reduce(set.intersection, [set(item) for item in prev_search_res_idL ]))

	#print 'result:',len(result),result	
	#print DB_meta_Search_IndxD[idx]
	if DB_meta_Search_IndxD != {}:
		for a in result:
			
			#TAA_str 'title':a[5],'artist':a[6],'album':a[7]
			#id_track - 0, path_crc32 - 1, last_modify_date - 2, album_crc32 - 3, artist_crc32 - 4, title -5,artist - 6,album - 7, TAA - - 8'
			if a[0] in DB_meta_Search_IndxD:
				resultL.append({'artist':DB_meta_Search_IndxD[a[0]][6],'album':DB_meta_Search_IndxD[a[0]][7],'track':DB_meta_Search_IndxD[a[0]][5],'album_crc32':DB_meta_Search_IndxD[a[0]][2]})
			else:
				logger.critical('3796 Error in getAlbum_list_db_via_AAT_search_term with key:'+str(a))
				
			
		resultL.sort(key=operator.itemgetter('artist'),reverse=True)
	print('Passed:',time.time()-time_1)
	return {'resultID':result,'resultL':resultL,'indx_TAA':DB_meta_Search_IndxD}
	

def getArtist_Album_list_db_via_search_term(dbPath,search_termD,max_elem,*args):
	# ������� ������ �� �������� �������� � �� ��� autocomplete
	# 
	objectL = []
	
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	
	c = db.cursor()
	stop_list = ['the','a','and']
		
	search_term = None
	
	if 'artist' in search_termD:
		search_term = search_termD['artist']
	elif 'album' in search_termD:
		search_term = search_termD['album']
	elif 'tag' in search_termD:
		search_term = search_termD['tag']	
		
	
		
	#for a in  stop_list:
	#	search_term.remove()
	
	print(search_termD,search_term)
	t_col_name = 1
	
	req = ''	
	l = []
	if search_term != None and 'album' in search_termD:
			req = """select * from ALBUM where ignore is NULL and album like  '%%%s%%' limit %s"""%(search_term,max_elem+1)	
			crc_index = 4
	elif search_term != None  and 'artist' in search_termD:		
			req = """select * from ARTIST where artist like  '%%%s%%' limit %s"""%(search_term,max_elem+1)
			crc_index = 2	
	elif search_term != None  and 'tag' in search_termD:		
			t_col_name = 2
			req = """select * from TAG where tag_descr like  '%%%s%%' limit %s"""%(search_term,max_elem+1)
			crc_index = 0			
			
	if req != '':		
		try:		
			c.execute(req)		
		except Exception as e:	
			#print 'Error:',req
			print(e)
			
		l =c.fetchall()
	
	c.close()
	db.close()
	if 'album' in search_termD or 'artist' in search_termD:
		for a in l:
			objectL.append({'key':a[crc_index],'name':a[t_col_name]})
	elif 'tag' in search_termD:
		for a in l:
			objectL.append({'key':a[0],'name':a[3]+':'+a[2]})
	list_len = len(objectL)
	if list_len > max_elem:
		objectL[max_elem] = {'key':0,'name':'...more then '+str(list_len)}	
	return objectL


		
def getArtist_Album_metaD_fromDB(dbPath,search_termD,folderL,artistCRC32,albumCRC32,*args):
	# ������� ������ �� �������� �������� � �� �� ������ ��������: ���������� (�� �������), ���������� ����� � ������� ��� �������, �����CRC32 ������� ��� �������
	# 
	artistD = {}
	albumD = {}
	
	db = sqlite3.connect(dbPath)	
	#db.text_factory = str
		
	fieldD = getTableInfo('artist',db)
	fieldL = [fieldD[a]['field_name']for a in fieldD]
		
	str_fld = ''
	str_fld = ','.join([a for a in fieldL])
	try:
		search_term_artist = search_termD['artist'].strip()
	except:
		search_term_artist = None
		
	try:
		search_term_album = search_termD['album'].strip()
	except:
		search_term_album = None		
	
	if 	search_term_album == '':
		search_term_album = None		
	if 	search_term_artist == '':
		search_term_artist = None	
	
	resD = {}
	print('Start')
	c = db.cursor()
	# id_artist,artist,artist_crc32,main,search_term,search_term_crc32
	
	# ��������������� ������� �������� �� ��������: ���32 � ��������� �����
	
	l_album_presel = []
	if albumCRC32 != None:
		req = """select id_album from ALBUM where path_crc32 = %s """%(str(albumCRC32))
		c.execute(req)
		l =c.fetchall()
		l_album_presel = [a[0] for a in l]
		print('singl album=',req)
		print(l_album_presel)
	else:
		if search_term_album != None:
			req = """select id_album from ALBUM where ignore is NULL and album like  '%%%s%%' """%(search_term_album)
			c.execute(req)
			l =c.fetchall()
			l_album_presel = [a[0] for a in l]
		
	# -----> ���� ���� ������ ��������, �� ������������ ���������� ����� ������� � ������ ������� <---------
	album_idL_folder_filtered = []
	artist_idL_presel_filtered = []
	if folderL != []:
		if l_album_presel != []:
			req = """select id_album,path from ALBUM where ignore is NULL and id_album in (%s)""" %(str(l_album_presel)[1:-1])	
		else:
			req = """select id_album,path from ALBUM where ignore is NULL""" 
		print(req) 
		c.execute(req)
		l =c.fetchall()
		
		for a in l:
			album_idL_folder_filtered = album_idL_folder_filtered + [a[0] for b in folderL if b.lower() in a[1].lower()]
			#print a[1].lower(),b
		
		l_album_presel = [a for a in l_album_presel if a in  album_idL_folder_filtered]
		
		print('album_idL_folder_filtered:',	len(album_idL_folder_filtered))
		req = 'select id_artist,id_album from ARTIST_ALBUM_REF where id_album in (%s)'%(str(album_idL_folder_filtered)[1:-1])	
		#print req 
		c.execute(req)	
		l =c.fetchall()
		artist_idL_presel_filtered = list(set([a[0] for a in l]))
		
		album_ref_chkL = list(set([a[1] for a in l]))	
			
		if artist_idL_presel_filtered == []:
			artist_idL_presel_filtered.append(1231974)
		else:
			# �.� ����� �������� ���������� �� ���������� �������� �� ����� ������ ��� ����� �������� ��������
			if len(album_ref_chkL) < len(l_album_presel):
				artist_idL_presel_filtered.append(1231974)
		
		
		print('artist_idL_presel_filtered_1:',	len(artist_idL_presel_filtered))
	
	else:
		if l_album_presel != []:
			req = 'select id_artist,id_album from ARTIST_ALBUM_REF where id_album in (%s)'%(str(l_album_presel)[1:-1])	
			#print req 
			c.execute(req)	
			l =c.fetchall()
			artist_idL_presel_filtered = list(set([a[0] for a in l]))
			
			# ���������, ��� �� ����� ������������� ����������� ������
			
			album_ref_chkL = list(set([a[1] for a in l]))	
			
			if artist_idL_presel_filtered == []:
				print("got dummy aartist")
				artist_idL_presel_filtered.append(1231974)
			else:
				# �.� ����� �������� ���������� �� ���������� �������� �� ����� ������ ��� ����� �������� ��������
				if len(album_ref_chkL) < len(l_album_presel):
					print("got dummy aartist")
					artist_idL_presel_filtered.append(1231974)
				
			
			
			
			
			print('artist_idL_presel_filtered_2:',	len(artist_idL_presel_filtered),len(l_album_presel),len(album_ref_chkL))
		

	# -----> ����� ��������
	
	# ������ ������� �� �������.
	# 1. ��������� �� ������� artistCRC32
	# 2. ����� ��������� �� ������� ���������� ����� ������� � ������������ � ���������
	if artistCRC32 != None:
		req = 'select * from ARTIST where artist_crc32 = %s'%(str(artistCRC32))
	else:
		if search_term_artist == None:
			if artist_idL_presel_filtered == []:
				print("bad")
				req = 'select * from ARTIST where id_artist = 99991234'
			else:
				req = """select * from ARTIST where id_artist in (%s) """%(str(artist_idL_presel_filtered)[1:-1])
				
		else:	
			if artist_idL_presel_filtered == []:
				req = """select * from ARTIST where artist like  '%%%s%%' """%(search_term_artist)
			else:
				req = """select * from ARTIST where id_artist in (%s) and artist like  '%%%s%%' """%(str(artist_idL_presel_filtered)[1:-1],search_term_artist)
	c.execute(req)
	#print req

	l_artist =c.fetchall()
	print('Got ARTIST',len(l_artist))
	artist_idL = [a[0] for a in l_artist]
	
	#######################################################
	# !!! ���� �������� ����� ������� � �������
	#######################################################
	if l_album_presel != []:
		req = 'select * from ARTIST_ALBUM_REF where id_artist in (%s) and id_album in (%s)'%(str(artist_idL)[1:-1],str(l_album_presel)[1:-1])	
	else:
		if album_idL_folder_filtered == []:
			req = 'select * from ARTIST_ALBUM_REF where id_artist in (%s)'%(str(artist_idL)[1:-1])	
		else:
			req = 'select * from ARTIST_ALBUM_REF where id_artist in (%s) and id_album in (%s) '%(str(artist_idL)[1:-1],str(album_idL_folder_filtered)[1:-1])	
	c.execute(req)
	
	l =c.fetchall()
	artist_album_refL = l
	album_idL = list(set([a[1] for a in l]))
	try:
		print('got A-A refDB',len(artist_album_refL),len(artist_idL),len(l_album_presel),len(album_idL),'['+str(album_idL[:100])+']')
	except:
		print('got A-A refDB < 100',len(artist_album_refL),len(artist_idL),len(l_album_presel),len(album_idL),'['+str(album_idL)+']')
	
	
	
	
	if albumCRC32 != None:
		req = """select * from ALBUM where path_crc32 = %s """%(str(albumCRC32))
	else:
		if search_term_album != None:
			req = """select * from ALBUM where ignore is NULL and album like  '%%%s%%' """%(search_term_album)
		else:
			req = """select * from ALBUM where ignore is NULL and id_album in (%s)"""%(str(album_idL)[1:-1])
	c.execute(req)
	#print req

	l_album =c.fetchall()
	print('Get ALBUM',len(l_album))
	#print l
	lineD = {}
	for a in l_artist:
		lineD = {'id_artist':a[0],'artist':a[1],'main':a[3],'search_term':a[4],'search_term_crc32':a[5],'albumD':{},'ref_artist_crc32L':[],'artist_song_num':0,'for_nsa_only':False,'object_type':a[9]}	
		artistD[a[2]] = lineD
		#print lineD['artist_crc32'],lineD
	
	lineD = {}
	
	virtual_albumD = {}
	albumD_map = {}
	for a in l_album:
		lineD = {'id_album':a[0],'album':a[1],'album_crc32':a[2],'path':a[3],'path_crc32':a[4],'format':a[5],'search_term_crc32':a[9],'main':a[10],
		'album_type':a[12],'album_song_num':a[13],'album_obj_type':a[14],'obj_type':a[15],'artistD':{},'ref_album_crc32L':[]}	
		albumD[a[4]] = lineD
		albumD_map[a[0]] = a[4]
		#print a[0]
		
		#if lineD['obj_type'] <> None:
		#	virtual_albumD[a[4]] = lineD
	
	print('Created Dicts')
	
	if (artist_album_refL == [] and l_album_presel != []) or (artist_album_refL != [] and len(album_idL) < len(l_album_presel)):
		artistD[1231974] = {'id_artist':0,'artist':'NOT_EXISTED_ARTIST_NOT_PROCESS_IT','main':False,'search_term':'','search_term_crc32':0,'albumD':{},'ref_artist_crc32L':[],'artist_song_num':0,'for_nsa_only':False,'object_type':'dummy_artist'}	
		for a in l_album_presel:
			#print a
			artist_album_refL.append((0,a,1231974,albumD_map[a],'dummy',0))	
			
	
	
	print('check not existed done')
	# Check virtial albums
	if virtual_albumD != {}:
		# ��������� ������ ����� ������� ������� ���� ����� ��� �� �������� ��.
		for virt_key in virtual_albumD:
			in_ref_list = False
			for item in artist_album_refL:
				if item[3] == virt_key:
					in_ref_list = True
					break 
			if not in_ref_list:
				if 1231974 not in artistD:
					artistD[1231974] = {'id_artist':0,'artist':'NOT_EXISTED_ARTIST_NOT_PROCESS_IT','main':False,'search_term':'','search_term_crc32':0,'albumD':{virt_key:{'song_num':0,'not_single_artist':False}},'ref_artist_crc32L':[],'artist_song_num':0,'for_nsa_only':False,'object_type':a[9]}	
				else:
					artistD[1231974]['albumD'][virt_key]={'song_num':0}
	for a in artistD:
		for b in artist_album_refL:
			if a == b[2]:
				artistD[a]['albumD'][b[3]] ={'song_num':b[5]}
	print('artistD ready',len(artistD))			
	for a in albumD:
		for b in artist_album_refL:
			if a == b[3]:
				albumD[a]['artistD'][b[2]] = {'song_num':b[5]	}
				artistD[b[2]]['artist_song_num']+=b[5]
				
	print('albumD ready',len(albumD))
	#album_keyL = albumD.keys()	
				
	print('Create Dicts A-A ref')	

	artist_album_refL_crc32 = [a[2] for a in artist_album_refL]	
		
	if artistCRC32 != None:
		req = 'select * from ARTIST_REFERENCE where artist_crc32 = %s'%(str(artistCRC32))
	else:
		req = 'select * from ARTIST_REFERENCE where artist_crc32 in (%s)'%(str(artist_album_refL_crc32)[1:-1])		
		
	c.execute(req)
	
	print('Artist ref db',len(l))			
	#print req

	l =c.fetchall()
	
	for a in artistD:
		for b in l:
			if a == b[0]:
				artistD[a]['ref_artist_crc32L'].append((b[1],b[2]))	
				
	if albumCRC32 != None:
		req = 'select * from ALBUM_REFERENCE where album_crc32 = %s'%(str(albumCRC32))
	else:
		req = 'select * from ALBUM_REFERENCE where id_album in (%s)'%(str(album_idL)[1:-1])	
	
	print(req)	
	c.execute(req)
	
	
	l =c.fetchall()
	print('Album ref db',len(l))			
	
	for a in albumD:
		for b in l:
			if a == b[2]:
				albumD[a]['ref_album_crc32L'].append((b[2],b[3],b[5]))				
		
	print('Album ref create')			
	
	
	l = [(len(artistD[a]['albumD']),0,0,a) for a in artistD]
	l.sort(reverse=True)	
	not_single_artist_albumL = []
	for a in albumD:
		for b in albumD[a]['artistD']:
			#print a,b
			#print 'artistD[a].keys():',artistD[a].keys()
			real_song_num = albumD[a]['album_song_num']
			if albumD[a]['artistD'][b]['song_num'] != real_song_num:
				artistD[b]['albumD'][a]['not_single_artist'] = True
				#album_songD[b]['song_num'] = real_song_num
				if a not in not_single_artist_albumL:
					not_single_artist_albumL.append(a)
			else:
				artistD[b]['albumD'][a]['not_single_artist'] = False
	
	if	not_single_artist_albumL != []: 
		
		album_keyL_nsa = [albumD[a]['id_album'] for a in not_single_artist_albumL]
		# ��������� ������ �������� ��� NSA
		req = 'select * from ARTIST_ALBUM_REF where id_album in (%s)'%(str(album_keyL_nsa)[1:-1])	
		c.execute(req)
		#print req
		l =c.fetchall()
		
		artist_idL = [a[0] for a in l if a[0] not in artistD]
		#print artist_idL,l
		req = """select * from ARTIST where id_artist in (%s) """%(str(artist_idL)[1:-1])		
		c.execute(req)
		
		l_artist = []
		l_artist =c.fetchall()	
		
		for a in l_artist:
			if a[2] in artistD:
				continue
			lineD = {'id_artist':a[0],'artist':a[1],'main':a[3],'search_term':a[4],'search_term_crc32':a[5],'albumD':{},'ref_artist_crc32L':[],'artist_song_num':0,'for_nsa_only':True,'object_type':a[9]}	
			artistD[a[2]] = lineD
			
			#print a[1]
			
		for a in not_single_artist_albumL:
			for b in l:
				if a == b[3]:
					#print 'tuaua'
					albumD[a]['artistD'][b[2]] = {'song_num':b[5]	}
					#artistD[b[2]]['artist_song_num']+=b[5]	
					
	c.close()
	
	db.close()	

	artist_album_refLD = []	
	for a in artist_album_refL:
		artist_album_refLD.append({'artist_key':a[2],'album_key':a[3],'rel_type':a[4],'tracks_num':a[5]})
	
	return {'artistD':artistD,'albumD':albumD,'statL':l,'not_single_artist_albumL':not_single_artist_albumL,'artist_album_refLD':artist_album_refLD}		
	
def getAll_Main_Artist_fromDB(db,*args):
	if db != None:
		#db.text_factory = str
		pass
	else:
		print('Error: in getAll_Main_Artist_fromDB')
	resD = {}
	
	c = db.cursor()
	if 'all' in args:
		req = """select artist_crc32,artist,search_term,id_artist from ARTIST"""
	else:	
		req = """select artist_crc32,artist,search_term,id_artist from ARTIST where main = 'X'"""
		
	
	c.execute(req)
	#print req

	l =c.fetchall()
	#print l
	
	l.sort(key=operator.itemgetter(1))
	c.close()

	return l		

def get_artist_ref_relation_type(dbPath,artist_CRC32):
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	c = db.cursor()
	req = """select * from ARTIST_REFERENCE where artist_crc32 = %s"""%(str(artist_CRC32))
	c.execute(req)
	l =c.fetchall()
	c.close()
	db.close()

	resL = []
	for a in l:
		if a[2] not in resL:
			resL.append(a[2])
	if resL == []:
		return None

	if len(resL)>1:
		logger.error('Error at artist_ref relation type get-> No relation')

	return resL[0]	
	
def getAlbum_relation_metaD(dbPath,db,albumCRC32,*args):	
	# ������� ��������� ��������� ����� �� ���������� �������-������ � � ���� "from" "to"
	extDbFlag = False
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
		#db.text_factory = str
		
	c = db.cursor()
		
	resD = {}
	resL = []
	relD = {}
	
	albums_from_relLD = []
	albums_to_relLD = []
	albums_all_relLD  = []
	
	c = db.cursor()
	if 'from' in args:
		# ���� �������� ������� ������
		req = """select album_crc32,rel_type from album_REFERENCE where album_crc32_ref = %s"""%(albumCRC32)
		c.execute(req)
		l =c.fetchall()
		#print 'l=',l
		
		
		albums_from_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
	
	if 'get_neibor' in args:	
		# �������� �� �������.
		#print '1'
		req = """select album_crc32_ref,rel_type from album_REFERENCE where album_crc32 = %s"""%(albumCRC32)
		c.execute(req)
		l =c.fetchall()
		print(l)
		albums_to_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
		
		l = [str(a[0]) for a in l]
		str_in = ','.join(l)
		#print '2'
		
		if not ('only_to_rel' in args):
			if l != []:
				#print '3'
				req = """select album_crc32,rel_type from album_REFERENCE where album_crc32_ref in (%s)"""%(str_in)
				c.execute(req)
				l = c.fetchall()
					
				albums_all_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
			
	
	c.close()
	if extDbFlag:
		db.close()		
			
	#print 'rel from DB is OK'
	
	return {'albums_all_relLD':albums_all_relLD,'albums_to_relLD':albums_to_relLD,'albums_from_relLD':albums_from_relLD}
	
	
def getArtist_relation_metaD(dbPath,artistCRC32,*args):	
	# ������� ��������� ��������� ����� �� ���������� ������� � � ����
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	c = db.cursor()
		
	resD = {}
	resL = []
	relD = {}
	
	artists_from_main_relLD = []
	artists_main_to_relLD = []
	artists_all_relLD  = []
	
	c = db.cursor()
	if 'main' in args:
		# ���� �������� ������� ������
		req = """select artist_crc32,rel_type from ARTIST_REFERENCE where ref_artist_crc32 = %s"""%(artistCRC32)
		c.execute(req)
		l =c.fetchall()
		#print 'l=',l
		
		
		artists_from_main_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
	
	if 'get_neibor' in args:	
		# �������� �� �������.
		#print '1'
		req = """select ref_artist_crc32,rel_type from ARTIST_REFERENCE where artist_crc32 = %s"""%(artistCRC32)
		c.execute(req)
		l =c.fetchall()
		
		artists_main_to_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
		
		l = [str(a[0]) for a in l]
		str_in = ','.join(l)
		#print '2'
		
		
		if l != []:
			#print '3'
			req = """select artist_crc32,rel_type from ARTIST_REFERENCE where ref_artist_crc32 in (%s)"""%(str_in)
			c.execute(req)
			l = c.fetchall()
				
			artists_all_relLD = [{'key':a[0],'rel_type':a[1]} for a in l]
			
	
	c.close()
	db.close()		
			
	print('rel from DB is OK')
	
	return {'artists_all_relLD':artists_all_relLD,'artists_main_to_relLD':artists_main_to_relLD,'artists_from_main_relLD':artists_from_main_relLD}
	
def getAll_Related_to_main_Artist_fromDB(dbPath,db,artistCRC32,*args):
	# ������� ��������� ��������� ����� �� ���������� ������� � � ����
	extDbFlag = False
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = True
		#db.text_factory = str
	c = db.cursor()
		
	resD = {}
	resL = []
	relD = {}
	
	c = db.cursor()
	if 'get_neibor' not in args:
		# ���� �������� ������� ������
		req = """select * from ARTIST_REFERENCE where ref_artist_crc32 = %s"""%(artistCRC32)
		c.execute(req)
		l =c.fetchall()
		#print 'l=',l
		l = [str(a[0]) for a in l]
		str_in = ','.join(l)
		
		for a in l:
			relD[a[0]] = a[2]
	
		req = """select artist_crc32,artist,search_term from ARTIST where artist_crc32 in (%s)"""%(str_in)
		#print req
		c.execute(req)
		resL =c.fetchall()
	
	elif 'get_neibor' in args:	
		# �������� �� �������.
		#print '1'
		req = """select ref_artist_crc32,rel_type from ARTIST_REFERENCE where artist_crc32 = %s"""%(artistCRC32)
		c.execute(req)
		l =c.fetchall()
		l = [str(a[0]) for a in l]
		str_in = ','.join(l)
		#print '2'
		
		
		if l != []:
			#print '3'
			req = """select artist_crc32,rel_type from ARTIST_REFERENCE where ref_artist_crc32 in (%s)"""%(str_in)
			c.execute(req)
			l = list(c.fetchall())
				
			l.sort()	
			
			for a in l:
				relD[a[0]] = a[1]
			
			l = [str(a[0]) for a in l]	
			str_in = ','.join(l)
			#print '4'
			req = """select artist_crc32,artist,search_term from ARTIST where artist_crc32 in (%s)"""%(str_in)
			#print req
			c.execute(req)
			l =c.fetchall()
			resL = [a for a in l if a[0]!=artistCRC32]
			
	if 'with_parent' in args:	
		#print '5',artistCRC32
		req = """select ref_artist_crc32,rel_type from ARTIST_REFERENCE where artist_crc32 = %s"""%(artistCRC32)	
		c.execute(req)
		
		l =c.fetchone()
		#print '6',req,l
		if l != () and l != None:
			#print '7',l
			req = """select artist_crc32,artist,search_term from ARTIST where artist_crc32 = %s"""%(str(l[0]))
			#print req
			c.execute(req)
			l =c.fetchone()
			#print l
			if l != ():
				resL = resL + [l]		
	
	c.close()
	if extDbFlag:
		db.close()		
			
	#print req

	
	#print l
	#print '11'
	resL.sort(key=operator.itemgetter(1))
	#print '12',resL
	#print 'resL=',resL,args
	
	return resL	
	
def delete_tracks_via_DbIdL(dbPath,tracks_dbIdL,*args):
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "delete from track where id_track in (%s)"%(str(tracks_dbIdL)[1:-1])
	try:
		r = c.execute(req)	
	except Exception as e:
		logger.critical('Exception at delete_tracks_via_DbIdL [%s]'%(str(e)))
	
	if 'remove' in args:
		db.commit()
	c.close()
	db.close()
	return 1
	
def delete_album_via_DbIdL(dbPath,albums_dbIdL,*args):
	# Удаление Альбома и связи артист-альбом
	relL = []
	logger.debug('at delete_album_via_DbIdL [%s]'%(str(albums_dbIdL)))
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "delete from album where id_album in (%s)"%(str(albums_dbIdL)[1:-1])
	logger.debug('at delete_album_via_DbIdL request=[%s]'%(req))
	try:
		r = c.execute(req)	
	except Exception as e:
		logger.critical('Exception at delete_album_via_DbIdL [%s]'%(str(e)))
		logger.critical('Exception at delete_album_via_DbIdL - 2 [%s]'%(str(req)))
	
	if 'with_artist_album_ref_check' in args:
		req = "select id_album from  artist_album_ref where id_album in (%s)"%(str(albums_dbIdL)[1:-1])
		c.execute(req)
		relL =list(c.fetchone())
		
	if relL !=[]:
		for id_album in relL:
			req = """delete from  artist_album_ref where id_album = %s"""%(str(id_album))
			try:	
				c.execute(req)
				l =c.fetchone()	
				print('del art_album_rel:',id_album)
				logger.info('at delete from artist_album_ref id_album=[%s] in delete_Album_Artist'%(str(id_album)))
			except Exception as e:
				logger.critical('Exception at delete from artist_album_ref [%s] in delete_Album_Artist'%(str(e)))
				return
	if 'remove' in args:
		db.commit()
	c.close()
	db.close()
	return 1	

def delete_Artist(dbPath,id_artist,artist_crc32,*args):
	#	
	logger.debug('at delete_Album_Artist [%s] - Start'%(str(id_artist)))
	db = sqlite3.connect(dbPath)	
	c = db.cursor()
	art_key = ''
	if id_artist:
		req = """delete from  artist where id_artist = %s"""%(str(id_artist))
		art_key = id_artist

	elif artist_crc32:
		req = """delete from  artist where artist_crc32 = %s"""%(str(artist_crc32))
		art_key = artist_crc32

	try:	
		c.execute(req)
		l =c.fetchone()	
		#print 'del Artist:',l
		logger.info('at delete from artist id=[%s] in delete_Album_Artist'%(str(art_key)))
	except Exception as e:
		logger.critical('Exception at delete from artist [%s] in delete_Album_Artist'%(str(e)))
		return 
		
	c.close()
	if 'remove' in args:
		db.commit()
	db.close()
	logger.debug('at delete_Album_Artist - Finished')
	return 1	
	
def delete_Album_Artist_relation(dbPath,artist_crc32,album_crc32,relD,*args):			
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	if 'rel_type' in relD:
		req = """select count(id_album) from  artist_album_ref where album_crc32 = %s and artist_crc32 = %s and rel_type = '%s' """%(str(album_crc32),str(artist_crc32),relD['rel_type'])
	else:
		req = "select count(id_album) from  artist_album_ref where album_crc32 = %s and artist_crc32 = %s "%(str(album_crc32),str(artist_crc32))
	c.execute(req)
	l =c.fetchone()
	
	if l[0] == 1:
		if 'rel_type' in relD:
			req = """delete from  artist_album_ref where album_crc32 = %s and artist_crc32 = %s  and rel_type = '%s' """%(str(album_crc32),str(artist_crc32),relD['rel_type'])
		else:
			req = "delete from  artist_album_ref where album_crc32 = %s and artist_crc32 = %s "%(str(album_crc32),str(artist_crc32))	
		c.execute(req)
		db.commit()
		
		c.execute("select changes()")
		l = c.fetchone()	

		if 1 == l[0]:
			print('delete relation is OK')
			
		else:
			print("error is dele cat",l[0])
			c.close()
			db.close()
			return -1
		
	else:
		print("logical error at delete_Album_Artist_relation request do delete: %s enries "%(str(l[0])))
	
	
	c.close()
	db.close()
	return 1
	
def delete_Albums_relation(dbPath,album_crc32,ref_album_crc32):	
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "select count(id_album) from album_reference where album_crc32 = %s and album_crc32_ref = %s "%(str(album_crc32),str(ref_album_crc32))	
	c.execute(req)	
	l = c.fetchone()
	if l[0] == 1:
		req = "delete from album_reference where album_crc32 = %s and album_crc32_ref = %s "%(str(album_crc32),str(ref_album_crc32))
		try:
			c.execute(req)	
			print(req)
		except Exception as e:
			logger.critical('Exception at delete from album_reference [%s] in set_Albums_relation'%(str(e)))
			c.close()
			db.close()
			return -1
	else:
		print('relation not found or can remove mre than desired num entries:',l[0],'check request:','\n',req)
		
		return -1
			
	
	db.commit()
	c.execute("select changes()")
	l = c.fetchone()	

	if 1 == l[0]:
		print('delete relation is OK')
		
	else:
		print("error is dele cat",l[0])
		c.close()
		db.close()
		return -1
	
	
	c.close()
	db.close()
	return 1		
	
	
def delete_Artist_relation(dbPath,artist_crc32,ref_artist_crc32):	
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "select count(artist_crc32) from artist_reference where artist_crc32 = %s and ref_artist_crc32 = %s "%(str(artist_crc32),str(ref_artist_crc32))	
	c.execute(req)	
	l = c.fetchone()
	if l[0] == 1:
		req = "delete from artist_reference where artist_crc32 = %s and ref_artist_crc32 = %s "%(str(artist_crc32),str(ref_artist_crc32))
		try:
			c.execute(req)	
			print(req)
		except Exception as e:
			logger.critical('Exception at delete from artist_reference [%s] in delete_Artist_relation'%(str(e)))
			c.close()
			db.close()
			return -1
	else:
		print('relation not found or can remove mre than desired num entries:',l[0])
		return -1
			
	
	db.commit()
	c.execute("select changes()")
	l = c.fetchone()	

	if 1 == l[0]:
		print('delete relation is OK')
		
	else:
		print("error is dele cat",l[0])
		c.close()
		db.close()
		return -1
	
	
	c.close()
	db.close()
	return 1			


def set_Artist_relation(dbPath,artist_crc32,artist_crc32_ref,relD,*args):
	# ������������� ����� ����� ��������� ���� �rtist ��� ������� ��������� �������������
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "select id_artist from artist where artist_crc32 = %s"%(str(artist_crc32))
	c.execute(req)
	l = c.fetchone()	
	
	track_range_mask = ''
	
		
	
	if 'rel_type' in relD:
		rel_type = relD['rel_type']	
	else:
		logger.critical('Error Setting_Artist_relation_1 no-->rel_type  check it:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
			
	try:
		id_artist = l[0]
	except Exception as e:		
		logger.critical('Error Setting_Artist_relation_1 artist  check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
	
	req = "select id_artist from artist where artist_crc32 = %s"%(str(artist_crc32_ref))
	c.execute(req)
	l = c.fetchone()	
	
	try:
		id_album_ref = l[0]
	except Exception as e:		
		logger.critical('Error Setting_Album_relation_2 artist  check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
		
	req = "select * from artist_reference where artist_crc32 = %s and ref_artist_crc32 = %s "%(str(artist_crc32),str(artist_crc32_ref))	
	c.execute(req)	
	l = c.fetchone()
	if l != None:
		req = "delete from artist_reference where artist_crc32 = %s and ref_artist_crc32 = %s "%(str(artist_crc32),str(artist_crc32_ref))
		try:
			c.execute(req)	
		except Exception as e:
			logger.critical('Exception at delete from album_reference [%s] in set_Artist_relation'%(str(e)))
			c.close()
			db.close()
			return -1
		
	rec = (artist_crc32,artist_crc32_ref,rel_type.upper())
	req = """insert into artist_reference (artist_crc32,ref_artist_crc32,rel_type) values(%s,%s,"%s") """%rec
	res = -1
	try:
		c.execute(req)	
		db.commit()
	except Exception as e:
		logger.critical('Exception at insert to artist_reference [%s] in set_Artist_relation'%(str(e)))
		
	res  = c.lastrowid	
	
	
	c.close()
	db.close()
	return res
	
def set_Albums_relation(dbPath,album_crc32,album_crc32_ref,relD,*args):
	# ������������� ����� ����� ��������� ���� ������ ��� ������� ��������� �������������
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	
	
	req = "select id_album from album where path_crc32 = %s"%(str(album_crc32))
	c.execute(req)
	l = c.fetchone()	
	
	track_range_mask = ''
	if 'track_range_mask' in relD:
		track_range_mask = relD['track_range_mask']
		
	
	if 'rel_type' in relD:
		rel_type = relD['rel_type']	
	else:
		logger.critical('Error Setting_Album_relation_1 no-->rel_type  check it:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
			
	try:
		id_album = l[0]
	except Exception as e:		
		logger.critical('Error Setting_Album_relation_1 album  check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
	
	req = "select id_album from album where path_crc32 = %s"%(str(album_crc32_ref))
	c.execute(req)
	l = c.fetchone()	
	
	try:
		id_album_ref = l[0]
	except Exception as e:		
		logger.critical('Error Setting_Album_relation_2 album  check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
		
	req = "select * from album_reference where album_crc32 = %s and album_crc32_ref = %s "%(str(album_crc32),str(album_crc32_ref))	
	c.execute(req)	
	l = c.fetchone()
	if l != None:
		req = "delete from album_reference where album_crc32 = %s and ref_album_crc32 = %s "%(str(album_crc32),str(album_crc32_ref))
		try:
			c.execute(req)	
		except Exception as e:
			logger.critical('Exception at delete from album_reference [%s] in set_Albums_relation'%(str(e)))
			c.close()
			db.close()
			return -1
		
	rec = (id_album,id_album_ref,album_crc32,album_crc32_ref,rel_type.upper(),track_range_mask)
	req = """insert into album_reference (id_album,id_album_ref,album_crc32,album_crc32_ref,rel_type,track_range_mask) values(%s,%s,%s,%s,"%s","%s") """%rec
	res = -1
	try:
		c.execute(req)	
		db.commit()
	except Exception as e:
		logger.critical('Exception at insert to album_reference [%s] in set_Albums_relation'%(str(e)))
		
	res  = c.lastrowid	
	
	
	c.close()
	db.close()
	return res
	
	
	
def restore_Album_Artist_relation(dbPath,artist_crc32,album_crc32,relD,*args):		
	# �������������� ������������ ����� ����� �������� � �������� ��� ������� ������������� �����
	
	db = sqlite3.connect(dbPath)	
	c = db.cursor()	

	req = "select count(id_track) from track where album_crc32 = %s and artist_crc32 = %s "%(str(album_crc32),str(artist_crc32))
		
	c.execute(req)
	l =c.fetchone()
	track_num = 0
	try:
		track_num = l[0]
	except Exception as e:		
		logger.critical('Error restore_Album_Artist_relation_1 album track num check:%s')%(str(e))
	

	req = "select id_album from album where path_crc32 = %s"%(str(album_crc32))
	c.execute(req)
	l = c.fetchone()	
			
	try:
		id_album = l[0]
	except Exception as e:		
		logger.critical('Error restore_Album_Artist_relation_2 album  check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1

	req = "select id_artist from artist where artist_crc32 = %s"%(str(artist_crc32))
	c.execute(req)
	l = c.fetchone()	
	
	try:
		id_artist = l[0]
	except Exception as e:		
		logger.critical('Error restore_Album_Artist_relation_2 artist check:%s')%(str(e))
		c.close()
		db.commit()
		db.close()
		return -1
	

	if 'rel_type' in relD:
		req = """insert into artist_album_ref (id_artist,id_album,artist_crc32,album_crc32,rel_type,tracks_num) values(%s,%s,%s,%s,"%s",%s)"""%(str(id_artist),str(id_album),str(artist_crc32),str(album_crc32),relD['rel_type'],str(track_num))	
	else:
		req = "insert into artist_album_ref (id_artist,id_album,artist_crc32,album_crc32,tracks_num) values(%s,%s,%s,%s,%s)"%(str(id_artist),str(id_album),str(artist_crc32),str(album_crc32),str(track_num))	
	
	try:
		c.execute(req)
		db.commit()
		res  = c.lastrowid
	except Exception as e:		
		#print 'Error saveAlbum_intoDB_via_artistD album_artist_ref:',e
		res = -1
		logger.critical('Exception (at artist_album_ref insert) [%s] in restore_Album_Artist_relation'%(str(e)))	
		print(req)
	

	c.close()
	db.close()
	
	print("relation A-A saved OK")
	
	return res
	
def saveAlbum_intoDB_via_artistD(dbPath,albumD,artist_crc32,album_crc32,db,*args):	
	# ����������� ��� ������������� ���������� ������� � ����� ������� �������
	
	# ������� ������� �� ��������� �� � ����������� �� ������� � albumD �������� ������ ��������.
	# ������� �������� ����� song_num � album_song_num
	
	# ������������� ���������� VA ������� �� ��� ������������� �������
	logger.info("In saveAlbum_intoDB_via_artistD - artist[%s] album[%s]"%(str(artist_crc32),str(album_crc32)))
	
	
	relation_song_num = 0
	album_song_num = 0
	if 'artist_view'in args:
		relation_song_num = albumD['song_num']
		album_song_num = albumD['song_num']
		if albumD['not_single_artist']:
				
			logger.critical('Saving the VA like album is forbidden under the artist View ')
			return -1
		
	elif 'album_NSA_view' in args:
		#print artist_crc32,album_crc32
		#print albumD.keys()
		#print albumD['artistD'].keys()
		#print albumD['artistD'][artist_crc32]
		
		relation_song_num = albumD['artistD'][artist_crc32]['song_num']
		album_song_num = albumD['album_song_num']
		
	#print relation_song_num,album_song_num
	
	extDbFlag = True
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = False
		
	c = db.cursor()	
	
	#albumD = artistD[album_crc32]
	#print albumD
	if not 'only_artist_relation_creation' in args:
		add_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
		res = None
		id_album = None
		req = "select count(id_track) from track where album_crc32 = %s"%(str(album_crc32))
		
		c.execute(req)
		l =c.fetchone()
		album_type = '' 
		# ������� ���� � ������� ��� ��������� ������ ���.
		# �� ��� ������� ��� ����� 'album_song_num', ���� "song_num" ������� � ����������� �� ���� ������� �������� ���� ��� ���������� ����� �������
		# ���� ���������� ����� ������� �����������. � ������ �������� VA ������ �� �������������� ���������� ������ ������� ��� �������������� �������
		# ����� ������ ������ ����������� ������ �� ��� ������������� ������ ������ NSA
		# ������� � �
		try:
			if l[0] == relation_song_num:
				album_type = 'ONE_ARTIST'
		except Exception as e:		
			logger.critical('Error saveAlbum_intoDB_via_artistD album track num check:%s')%(str(e))
			
				
		rec = (albumD['album'],albumD['album_crc32'],albumD['dir_path'],albumD['dir_path_crc32'],albumD['format'],add_date,album_type,album_song_num)
		req = """insert into album (album,album_crc32,path,path_crc32,format_type,add_date,album_type,tracks_num) values("%s",%s,"%s",%s,"%s","%s","%s",%s)"""%rec
		#print req
		try:
			c.execute(req)
		except Exception as e:		
			
			logger.critical('Exception (at insert) [%s] in saveAlbum_intoDB_via_artistD'%(str(e)))
			res = -1
			
			c.close()
			if not extDbFlag:
				db.commit()
				db.close()
			
			return -1
		if res == None:		
			c.execute("select last_insert_rowid()")
			l = c.fetchone()	
			id_album = l[0]
			res = id_album		
	
	if 'without_artist_relation' in args:
		c.close()
		if not extDbFlag:
			#print 'Saved album'
			db.commit()
			db.close()
		return res
	# save main album entry
	
	if 'only_artist_relation_creation' in args:
	#if 'only_artist_relation_creation' in args and artist_crc32 <> None:
		#print 'r1'
		req = "select id_album from album where path_crc32 = %s"%(str(album_crc32))
		c.execute(req)
		l = c.fetchone()	
		#print 'r1',l
		id_album = l[0]
		
	#print 'r2',id_album
	# save artist2album relation
	req = "select id_artist from artist where artist_crc32 = %s"%(str(artist_crc32))
	c.execute(req)
	l = c.fetchone()	
	#print 'r3',artist_crc32,l
	id_artist = l[0]
	#print 'r4'
	#print 'artist_id:',id_artist
	#Get tracks number per album
	#print albumD.keys()
	req = "insert into artist_album_ref (id_artist,id_album,artist_crc32,album_crc32,tracks_num) values(%s,%s,%s,%s,%s)"%(str(id_artist),str(id_album),str(artist_crc32),str(album_crc32),str(relation_song_num))
	#print 'r5'	
	try:
		res = c.execute(req)
	except Exception as e:		
		#print 'Error saveAlbum_intoDB_via_artistD album_artist_ref:',e
		res = -1
		logger.critical('Exception (at artist_album_ref insert) [%s] in saveAlbum_intoDB_via_artistD'%(str(e)))	
	
	
	c.close()
	if not extDbFlag:
		#print 'Saved Item'
		db.commit()
		db.close()
		
	
	
	return res
	
def modifyAlbum_viaCRC32(dbPath,album_crc32,attrsD):
	db = sqlite3.connect(dbPath)	
	#db.text_factory = str	
	
	
	searchTerms = ''
	search_term_crc32 = 0
	
	if 'searchTerms' in attrsD:
		searchTerms = attrsD['searchTerms']
		
		print("-->:",searchTerms)
		try:	
			search_term_crc32 = zlib.crc32(searchTerms)
		except:
			search_term_crc32 = zlib.crc32(searchTerms.encode('utf-8'))
			
	main = ''
	if 'main' in attrsD:
		main = attrsD['main']
	
	date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
	print(date)
	res = None
	id_album = 0
	
			
	if (main != 'X') and (main != True):
		main = ''
	
	c = db.cursor()
	# Check existance in DB
	req = "select id_album,search_term_crc32,main from album where album_crc32 = %s"%album_crc32
	c.execute(req)
	l =c.fetchone()
	
	todoL = []
	if l!=None:
		id_album = l[0]
		
		rec_m = (searchTerms,search_term_crc32,date,main,id_album)
		req = """update album set search_term = "%s", search_term_crc32 = %s,last_modify_date = "%s",  main = "%s" where id_album = %s"""%rec_m
		print(req)
		try:
			c.execute(req)	
			res = id_album
		except Exception as e:
			res = -1
			logger.critical('Exception (at update) [%s] in saveArtistD_intoDB'%(str(e)))
	
	db.commit()
	db.close()
		
	
	return {'result':res,'id_album':id_album}
	
	

def modifyArtist_viaCRC32(dbPath,artist_crc32,attrsD):
	db = sqlite3.connect(dbPath)	
	#db.text_factory = str	
	
	
	searchTerms = ''
	search_term_crc32 = 0
	
	if 'searchTerms' in attrsD:
		searchTerms = attrsD['searchTerms']
		
		try:	
			search_term_crc32 = zlib.crc32(searchTerms)
		except:
			search_term_crc32 = zlib.crc32(searchTerms.encode('utf-8'))
			
	main = ''
	if 'main' in attrsD:
		main = attrsD['main']
	
	date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
	res = None
	id_artist = 0
	
			
	if (main != 'X') and (main != True):
		main = ''
	
	c = db.cursor()
	# Check existance in DB
	req = "select id_artist,search_term_crc32,main from artist where artist_crc32 = %s"%artist_crc32
	c.execute(req)
	l =c.fetchone()
	print(req)
	todoL = []
	if l!=None:
		id_artist = l[0]
		
		rec_m = (searchTerms,search_term_crc32,date,main,id_artist)
		req = """update artist set search_term = "%s", search_term_crc32 = %s,last_modify_date = "%s",  main = "%s" where id_artist = %s"""%rec_m
		print(req)
		try:
			c.execute(req)	
			res = id_artist
		except Exception as e:
			res = -1
			logger.critical('Exception (at update) [%s] in saveArtistD_intoDB'%(str(e)))
	
	db.commit()
	db.close()
		
	
	return {'result':res,'id_artist':id_artist}
	
def saveArtistD_intoDB(dbPath,artistName,searchTerm,main,object_type,refArtist_CRC32L,reference_type,db):
	
	extDbFlag = True
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = False
		#db.text_factory = str	
	
	try:
		artist_crc32 = zlib.crc32(artistName)
	except:
		artist_crc32 = zlib.crc32(artistName.encode('utf-8'))
	try:	
		search_term_crc32 = zlib.crc32(searchTerm)
	except:
		search_term_crc32 = zlib.crc32(searchTerm.encode('utf-8'))
	
	print('saving artist:',artistName,artist_crc32)
	
	lastInsert_IDL = []
	
	#print 'refArtist_CRC32L=', refArtist_CRC32L
	add_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
	res = None
	id_artist = 0
	
	#if refArtist_CRC32L == None or refArtist_CRC32L == []:
	#	ref_artist_crc32 = 'NULL'
	#else:
	#	ref_artist_crc32 = int(refArtist_CRC32)
		
	if 	main != 'X':
		main = ''
	
	c = db.cursor()
	# Check existance in DB
	req = "select id_artist from artist where artist_crc32 = %s"%artist_crc32
	c.execute(req)
	l =c.fetchone()
	#print l
	if l!=None:
		id_artist = l[0]
		
		
		rec_m = (searchTerm,search_term_crc32,main,id_artist)
		req = """update artist set search_term = "%s", search_term_crc32 = %s,  main = "%s" where id_artist = %s"""%rec_m
		try:
			c.execute(req)	
			res = id_artist
		except Exception as e:
			res = -1
			logger.critical('Exception (at update) [%s] in saveArtistD_intoDB'%(str(e)))
			
	
		#print 'newRefL;',newRefL
		del_str_lst = ','.join([str(a) for a in refArtist_CRC32L])
		req = "delete from artist_reference where artist_crc32 = %s and ref_artist_crc32 not in (%s) "%(str(artist_crc32),del_str_lst)
		try:
			c.execute(req)	
		except Exception as e:
			logger.critical('Exception at delete from artist_reference [%s] in saveArtistD_intoDB'%(str(e)))
		# ������� ��� ������ �
		for a in refArtist_CRC32L:
			rec_m = (artist_crc32,a,reference_type.lower())
			req = """insert into artist_reference (artist_crc32,ref_artist_crc32,rel_type) values(%s,%s,"%s") """%rec_m
			try:
				c.execute(req)	
				#print req
			except Exception as e:
				logger.critical('Exception at insert into artist_reference [%s] in saveArtistD_intoDB'%(str(e)))
		
			
	else:		
		if main != 'X':
			rec_m = (artistName,artist_crc32,searchTerm,search_term_crc32,add_date,object_type)
			req = """insert into artist (artist,artist_crc32,search_term,search_term_crc32,add_date,object_type) values("%s",%s,"%s",%s,"%s","%s") """%rec_m
			try:
				c.execute(req)	
				
			except Exception as e:
				res = -1
				logger.critical('Exception (at insert not main) [%s] in saveArtistD_intoDB'%(str(e)))
				
				
			
			#res = c.execute("SELECT last_insert_rowid()")
			#print res
			
				
			for a in refArtist_CRC32L:
				rec_m = (artist_crc32,a,reference_type.lower())
				req = """insert into artist_reference (artist_crc32,ref_artist_crc32,rel_type) values(%s,%s,"%s") """%rec_m
				try:
					c.execute(req)	
				except Exception as e:
					logger.critical('Exception 4 [%s] in saveArtistD_intoDB'%(str(e)))
					
			
		else:
			rec_m = (artistName,artist_crc32,searchTerm,search_term_crc32,main,add_date,object_type)
			req = """insert into artist (artist,artist_crc32,search_term,search_term_crc32,main,add_date,object_type) values("%s",%s,"%s",%s,"%s","%s","%s") """%rec_m
			try:
				c.execute(req)	
			except Exception as e:
				logger.critical('Exception  (at insert main)  [%s] in saveArtistD_intoDB'%(str(e)))
				res = -1
		if res == None:		
			c.execute("select last_insert_rowid()")
			l = c.fetchone()	
			id_artist = l[0]
			res = id_artist
				
	#print req
	c.close()
	if not extDbFlag:
		db.commit()
		db.close()
		
	
	return {'result':res,'artist_crc32':artist_crc32,'id_artist':id_artist}
	
	
	
def saveAlbum_simple_intoDB(dbPath,albumName,searchTerm,main,object_type,refalbum_CRC32L,reference_type,db):
	# ������� ������������� ��� ���������� ���������� ��������
	extDbFlag = True
	if db == None:
		db = sqlite3.connect(dbPath)	
		extDbFlag = False
		#db.text_factory = str	
	
	search_term_crc32 = None
	add_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
	
	try:
		album_crc32 = zlib.crc32(albumName)
		path_crc32 = zlib.crc32(albumName+add_date)
	except:
		album_crc32 = zlib.crc32(albumName.encode('utf-8'))
		path_crc32 = zlib.crc32((albumName+add_date).encode('utf-8'))
		
	if 	searchTerm != None:
		try:	
			search_term_crc32 = zlib.crc32(searchTerm)
		except:
			search_term_crc32 = zlib.crc32(searchTerm.encode('utf-8'))
	
		
			
	
	print('saving album:',albumName,album_crc32)
	
	lastInsert_IDL = []
	
	#print 'refalbum_CRC32L=', refalbum_CRC32L
	
	res = None
	res_ref = None
	id_album = 0
	
			
	if 	main != 'X':
		main = None
	
	c = db.cursor()
	
	
	if refalbum_CRC32L != []:
		# ���� � ������� �������� �������
		
		str_lst = ','.join([str(a) for a in refalbum_CRC32L])
		req = "select id_album,path_crc32 from album where path_crc32 in (%s) "%(str_lst)
		#print req
		c.execute(req)
		l =c.fetchall()
		refalbum_CRC32L = [a for a in l]
		#print refalbum_CRC32L
		
			
	# Check existance in DB
	req = "select id_album from album where album_crc32 = %s"%album_crc32
	c.execute(req)
	l =c.fetchone()
	#print l
	if l!=None:
		id_album = l[0]
		id_album_ref = l[0]
		
		rec_m = (searchTerm,search_term_crc32,main,id_album)
		req = """update album set search_term = "%s", search_term_crc32 = %s,  main = "%s" where id_album = %s"""%rec_m
		try:
			c.execute(req)	
			res = id_album
		except Exception as e:
			res = -1
			logger.critical('Exception (at update) [%s] in savealbumD_intoDB .1 req:[%s]'%(str(e),str(req)))
			return {'result':res,'album_crc32':album_crc32,'id_album':None}	
			
		if refalbum_CRC32L != []:
			#print 'newRefL;',newRefL
			#del_str_lst = ','.join([str(a) for a in refalbum_CRC32L])
			#req = "delete from album_reference where album_crc32 = %s and ref_album_crc32 not in (%s) "%(str(album_crc32),del_str_lst)
			#try:
			#	c.execute(req)	
			#except Exception,e:
			#	logger.critical('Exception at delete from album_reference [%s] in savealbumD_intoDB'%(str(e)))
			pass 
		# ������� ��� ������ �
		for a in refalbum_CRC32L:
			rec_m = (a[0],id_album_ref,a[1],path_crc32,reference_type.lower())
			print(rec_m)
			req = """insert into album_reference (id_album,id_album_ref,album_crc32,album_crc32_ref,rel_type) values(%s,%s,%s,%s,"%s") """%rec_m
			try:
				c.execute(req)	
				print(req)
			except Exception as e:
				logger.critical('Exception at insert into album_reference [%s] in savealbumD_intoDB .2'%(str(e)))
				return {'result':-1,'album_crc32':album_crc32,'id_album':None}	
		
			
	else:	
		album_type = ''
		if main == None:
			if searchTerm != None:
				rec_m = (albumName,album_crc32,'',path_crc32,searchTerm,search_term_crc32,add_date,album_type,object_type)
				req = """insert into album (album,album_crc32,path,path_crc32,search_term,search_term_crc32,add_date,album_type,object_type) values("%s",%s,"%s",%s,"%s",%s,"%s","%s","%s") """%rec_m
			else:
				rec_m = (albumName,album_crc32,'',path_crc32,add_date,album_type,object_type)
				req = """insert into album (album,album_crc32,path,path_crc32,add_date,album_type,object_type) values("%s",%s,"%s",%s,"%s","%s","%s") """%rec_m
			try:
				c.execute(req)	
				
			except Exception as e:
				res = -1
				logger.critical('Exception (at insert not main) [%s] in savealbumD_intoDB .3'%(str(e)))
				print(req)
				return {'result':res,'album_crc32':album_crc32,'id_album':None}	
			if 	res != -1:
				c.execute("select last_insert_rowid()")
				l = c.fetchone()	
				id_album_ref = l[0]	
				res = l[0]	
			
			#res = c.execute("SELECT last_insert_rowid()")
			#print res
			
				
						
				for a in refalbum_CRC32L:
					rec_m = (a[0],id_album_ref,a[1],path_crc32,reference_type.lower())
					req = """insert into album_reference (id_album,id_album_ref,album_crc32,album_crc32_ref,rel_type) values(%s,%s,%s,%s,"%s") """%rec_m
					try:
						c.execute(req)	
					except Exception as e:
						logger.critical('Exception 4 [%s] in savealbumD_intoDB'%(str(e)))
						res_ref = -1
						return {'result':res,'album_crc32':album_crc32,'id_album':None}	
					
			
		else:
			rec_m = (albumName,album_crc32,'',path_crc32,searchTerm,search_term_crc32,main,add_date,album_type,object_type)
			req = """insert into album (album,album_crc32,path,path_crc32,search_term,search_term_crc32,main,add_date,album_type,object_type) values("%s",%s,"%s",%s,"%s",%s,"%s","%s","%s","%s") """%rec_m
			try:
				c.execute(req)	
			except Exception as e:
				logger.critical('Exception  (at insert main)  [%s] in savealbumD_intoDB .5'%(str(e)))
				res = -1
		
				
	#print req
	c.close()
	if res != -1 and res_ref != -1:
		db.commit()
	else:
		res = -1
	if not extDbFlag:
		db.close()
		
	
	return {'result':res,'album_crc32':album_crc32,'id_album':id_album}	
	
def check_loaded_albums_2_lib(check_date):

	cfgD = readConfigData(mymedialib_cfg)		
		
	dbPath = cfgD['dbPath']
	db = sqlite3.connect(dbPath)

	req = "select id_event, param_1 from event_control where event = 'update_lib_cur_dir' and album_loaded is NULL"
	albumsL = db_request_wrapper(db,req)
	db_albumD = getAlbumD_fromDB(None,db,None,[],'wo_reflist')['albumD']
	
	db_albumD_bad = {}
	for a in db_albumD:
		check_crc32 = zlib.crc32(db_albumD[a]['path'].lower().strip())
		if check_crc32 != a:
			if db_albumD[a]['object_type'] != None:
				continue
			db_albumD_bad[check_crc32] = db_albumD[a]
			print('Bad:	', a,db_albumD[a]['path'])
	print('Bad albumes in table ALBUM:',len(db_albumD_bad))
	
	ne_albumsL = []
	albumsD = {}
	# ���������� ������� �������� �� ���� ���� ��������� ��������
	for a in albumsL:
		if not os.path.exists(a[1]):

			ne_albumsL.append(a[0])
			req = "update event_control set album_loaded = '-' where id_event = %s"%(a[0])
			res = db_request_wrapper(db,req,'modi')
			print(res, end=' ')
		else:
			key = zlib.crc32(a[1].lower().strip())
			if key not in albumsD:
				albumsD[key] = {'event_idL':[a[0]],'album_registered':False,'orig_folder':a[1],'folder_key':key}
			else:
				albumsD[key]['event_idL'].append(a[0])
	
	
	
	
	cnt = 0
	cnt_bad = 0
	for a in albumsD:
		if a in db_albumD:
			#print 'yo',a,albumsD[a]
			albumsD[a]['album_registered'] = True
			cnt +=1
		elif a in db_albumD_bad:
			cnt_bad+=1
			print('Bad album:',a,db_albumD_bad[a]['path'])
			
			
	print('initial loaded albums:%d,  in albumes db registered %d, bad album %d: '%(len(albumsD),cnt,cnt_bad))

	if len(albumsD)>0:
		print('update registered albumes event log:')
		print()
		
	cnt = 0
	for a in albumsD:
		if albumsD[a]['album_registered']:
			for b in albumsD[a]['event_idL']:
				req = "update event_control set album_loaded = 'X' where id_event = %s"%(b)
				res = db_request_wrapper(db,req,'modi')
				if cnt % 100 == 0:
					print('*', end=' ')
				cnt += 1
	db.close()
	return albumsD	
	
def get_Tasks_in_queue(dbPath):
	db = sqlite3.connect(dbPath)
	c = db.cursor()
	
	
	req = """select id_event,event from event_control where running = 1 """
	r = c.execute(req)
	l = c.fetchall()	
	
	if l!=[]: 
		for a in l:
			logger.critical('in get_Tasks_in_queueError: medialib last update: last task entry [%s] tobe corrected to status = 3 '%str(a))
			rec = (3,a[0])	
			req = """update event_control set running = "%s" where id_event = %s"""%rec
			r = c.execute(req)
			db.commit()
	

	req = """select id_event,event from event_control where running = 0 """
	r = c.execute(req)
	l = c.fetchall()
	
	c.close()
	db.close()	
	return l
	
	
def maintain_Task_for_event(dbPath,event_id,param,*args):
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	c = db.cursor()
	req = """select * from event_control where id_event = %s """%(event_id)	
	r = c.execute(req)
	l = c.fetchone()
	if l == None:
		return None
	else:
		t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
		if 'run_task' in args:
			rec = (1,param,event_id)	
			req = """update event_control set running = "%s", param_1 = "%s"  where id_event = %s"""%rec
		elif 'finish_task' in args:	
			rec = (2,param,t_date,event_id)	
			req = """update event_control set running = "%s", param_1 = "%s", finish_date_time = "%s" where id_event = %s"""%rec
		
		try:
			print(req)
			r = c.execute(req)
			db.commit()
			c.close()
			db.close()	
			return l
		except:	
			print('Erroro:',req)
			c.close()
			db.close()
		
def triggerBatchJob_via_event(dbPath,event,param,*args):
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	c = db.cursor()
	# �������� ��� �������� ����� ��� �� ������
	req = """select * from event_control where event = "%s" and running = 1 and finish_date_time is NULL """%(event)
	c.execute(req)
	l = c.fetchone()
	#print l
	if l != None:
		
		logger.info("in triggerBatchJob_via_event: Task for event %s is running"%event )	
		c.close()
		db.close()
		return -3
		
	req = """select * from event_control where event = "%s" and running = 0 and finish_date_time is NULL """%(event)
	c.execute(req)
	l = c.fetchone()	
	#print l
	if l != None:
		logger.info("in triggerBatchJob_via_event: Task for event %s is already registered"%event )	
		c.close()
		db.close()
		return -2
	if 'only_check' in args:
		return None
	t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())	
	rec = (event,0,t_date,param)	
	req = """insert into event_control (event,running,add_date_time,param_1) values("%s",%s,"%s","%s") """%rec
	#print req 
	#print l
	try:
		r = c.execute(req)
		c.execute("select last_insert_rowid()")
		l = c.fetchone()	
		#print 'l=',l
		db.commit()
		c.close()
		db.close()
		return l[0]
	except:
		c.close()
		db.close()
		return -1	
	
	# ������ ��� ����� 
	
def correct_CRC32_in_DB(dbPath,idDBL):
	if idDBL == [] or idDBL == None:
		metaD = getCurrentMetaData_fromDB_via_DbIdL([],None,'progress','take_all')
	else:
		metaD = getCurrentMetaData_fromDB_via_DbIdL(idDBL,None,'progress')

	print('Metedata retrieved from DB:',len(metaD))
	loop_cnt = 0
	artist_cnt = 0
	album_cnt = 0
	path_cnt =0

	db = sqlite3.connect(dbPath)
	c  = db.cursor()

	for a in metaD:
		artist_crc32 = zlib.crc32(metaD[a]['artist'].lower().strip())
		pos = metaD[a]['path'].lower().strip().rfind('\\')
		album_crc32 = zlib.crc32(metaD[a]['path'][:pos].lower().strip())
		path_crc32 = zlib.crc32(metaD[a]['path'].lower().strip())
		update = False
		if metaD[a]['artist_crc32'] != artist_crc32:
			metaD[a]['artist_crc32'] = artist_crc32
			artist_cnt+=1
			update = True

		if metaD[a]['album_crc32'] != album_crc32:
			metaD[a]['artist_crc32'] = album_crc32
			album_cnt+=1
			update = True

		if metaD[a]['path_crc32'] != path_crc32:
			#metaD[a]['path_crc32'] = path_crc32
			path_cnt+=1
		if update:
			rec = (artist_crc32,album_crc32,metaD[a]['id_track'])
			req = """update track set artist_crc32  = %s ,album_crc32  = %s where id_track = %s"""%rec
			try:
				c.execute(req)
			except:
				print('Error with:',a)
			loop_cnt += 1
			if loop_cnt%1000 == 0:
				db.commit()
				print('.',loop_cnt, end=' ')
	db.commit()
	c.close()
	db.close()

	print('album_cnt',album_cnt,'artist_cnt',artist_cnt,'path_cnt',path_cnt)	
	
def split_2_fix_lines(seq, length):
	# �������� �� ��������� ����� ���������� ������ �� ����� ��� length
	l = []
	word = ""
	old_i = 0
	for i in range(0, len(seq)):
		if i+1 == len(seq):
			l.append(word.strip()+seq[-1:])
			break
		word+=seq[i]


		if len(word) > length and seq[i+1] != ' ':
			pos = word.rfind(' ')
			if pos == -1:
				continue
			l.append(word[:pos].strip())
			hvost = word[pos+1:]

			#print '-->',word
			word = hvost
		elif	len(word) > length and seq[i+1] == ' ':
			l.append(word.strip())
			#print '-->',word
			word = ""

	l = [a for a in l if a != ""]
	max_len = max([len(a) for a in l])
	return {'strL':l,'max_len':max_len}
	
	
def checkReplicaMapping(track_metaD,format,replica_mapD):
	#1. create replica path CUE 
	
	
	if track_metaD['cue_fname'] != None:
		track_key = '(%02d)'%track_metaD['cue_num']
		pos = track_metaD['path'].rfind('\\')
		album_path = track_metaD['path'][:pos+1]
		album_path = album_path.replace(replica_mapD['orig'],replica_mapD['repl'])
		
		
		
		#print
		#print '---------->replica_path--:', replica_path
		if os.path.exists(album_path):
			
			for f_name in os.listdir(album_path):
				if track_key in f_name:
					try:
						(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(album_path+f_name)
					except:
						return {'message':'ERROR','track':album_path+f_name,'cue_key':track_key,'cue_num':track_metaD['cue_num']}
					if mtime < track_metaD['last_modify_date']:
						return {'message':'outdated','track':album_path+f_name,'cue_key':track_key,'cue_num':track_metaD['cue_num']}
					else:
						return {'message':'OK','track':album_path+f_name,'cue_key':track_key,'cue_num':track_metaD['cue_num']}

			return {'message':'no_replica','track':album_path,'cue_key':track_key}
		else:
			return {'message':'no_replica','track':album_path,'cue_key':track_key}


	else:
		replica_path = track_metaD['path'].replace(replica_mapD['orig'],replica_mapD['repl'])
				
		replica_path = os.path.splitext(replica_path)[0]+'.'+format
		
					
		#print replica_path
		if os.path.exists(replica_path):
			try:
				(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(replica_path+f_name)
			except:
				return {'message':'ERROR','track':replica_path}
			if mtime < track_metaD['last_modify_date']:
				return {'message':'outdated','track':replica_path}
			else:
				return {'message':'OK','track':replica_path}

		else:
			return {'message':'no_replica','track':replica_path}

		
		
def convertLosless_2_lossy(format,codec_path,codecD,f_name,dest_dir,temp_dir,*args):
	# ��� ������� ������ �������� ������ ��� ���� � ���. ���� ���������� ��� ��� ����������� �������� ��� ��������� �� ��������� ��� ����, ���� �� ��������,
	
	if f_name[0] != "\"" and f_name[-1] != "\"":
		print("Error in input file name format: ZABIL KAVICHKI!!! ")
		return -1
	if 	dest_dir != '' and dest_dir != None:
		if not os.path.exists(dest_dir):
			raise Exception( "DirError", 'Dest dir does not exist')
	r = 0
	mp3_name = os.path.split(f_name)[1]
	
	if format == "mp3":
		mp3_name = os.path.splitext(mp3_name)[0]+'.mp3'
	elif format == "ogg":
		mp3_name = os.path.splitext(mp3_name)[0]+'.ogg'
	f_path = os.path.split(f_name)[0]
	mp3_name = "\""+dest_dir+'\\'+mp3_name+"\""
	temp_wav_name = f_path+'\\'+temp_dir+'temp.wav'+"\""
	#print mp3_name
	#print temp_wav_name
	prog = None
	if '.flac' in f_name.lower():
		params = ('flac','-d','-f',f_name,'-o',temp_wav_name)
		prog = 'flac.exe'
		r = os.spawnve(os.P_WAIT, codec_path+prog, params , os.environ)	
		
	elif '.ape' in f_name.lower():

		params = ('mac',f_name,temp_wav_name,'-d')
		#print params
		#print codec_path
		prog = 'mac.exe'
		r = os.spawnve(os.P_WAIT, codec_path+prog, params , os.environ)
	elif '.mp3' in f_name.lower():
		params = ('lame','-S','--decode',f_name,temp_wav_name)
		prog = 'lame.exe'
		r = os.spawnve(os.P_WAIT, codec_path+prog, params , os.environ)		
	elif '.wav' in f_name.lower():
		temp_wav_name = f_name
		pass
	else:
		return -1

	#print f_name	
	#os.path.exists(f_name)
	
	#print temp_wav_name
	#print params
	#print codec_path+prog
	
	
	if r != 0:
		return -1
		
	if 	'stop_and_save_wav' in args:
		return r
	#print "wav is OK"
	#params = ('lame','--noreplaygain','-V','2',temp_wav_name,mp3_name)
	if format == "mp3":
		params = ('lame','-S','--noreplaygain','--preset','fast','standard',temp_wav_name,mp3_name)
		codec_path = codec_path+'lame.exe'
		try:
			r = os.spawnve(os.P_WAIT, codec_path,params, os.environ)
		except:
			print("Eroro line 5349: with:",mp3_name)
			return -1
	elif format == "ogg":
		codec_path = codec_path+'oggenc2.exe'
		
		params = ('oggenc2', '-Q','-q2',temp_wav_name,'-o',mp3_name)
		#print params
		try:
			r = os.spawnve(os.P_WAIT, codec_path,params, os.environ)
		except:
			print("Eroro line 5349: with:",mp3_name)
			return -1
	else:
		print('format not defined',format)
	
	if 'keep_wav' not in args:
		os.remove(temp_wav_name[1:-1])
	if r != 0:
		return -1
	#print "mp3 is OK",mp3_name
	return r
	
def doMP3_replication_from_metaD(branch_filter,format,replica_prefix,metaD,*args):
	# ������� ���������� ����������� �� lossless �������� � mp3, � ������ ���������
	key_cueL = []
	key_normL = []
	key_cueD = {}
	key_normD = {}
	delta_map_cueD ={}
	temp_dir = ''

	cnt = 0
	codec_path = "D:\\Local Soft\\Codecs\\"
	print('Collecting album data and statistics')
	for a in metaD:
		if cnt%10000 ==0:
			print(cnt, end=' ')
		cnt+=1
		if metaD[a]['cue_fname'] != None:
			if metaD[a]['cue_fname'] not in key_cueD:
				key_cueD[metaD[a]['cue_fname']] = {'metaKeyL':[a],'track_numL':[]}
			else:
				key_cueD[metaD[a]['cue_fname']]['metaKeyL'].append(a)
		else:
			if '.flac' in metaD[a]['path'].lower() or '.ape' in metaD[a]['path'].lower():
				pos = metaD[a]['path'].rfind('\\')
				album_path = metaD[a]['path'][:pos+1]
				if album_path not in key_normD:
					key_normD[album_path] = [a]
				else:
					key_normD[album_path].append(a)
	key_cueL = list(key_cueD.keys())
	key_cueL.sort()
	key_normL = list(key_normD.keys())
	key_normL.sort()
	
	print()
	print("cue albums number:",len(key_cueL))
	print("losles albums number:",len(key_normL))
	
	replica_postfix = format.upper()

	replica_mapD = {'orig':'G:\MUSIC\ORIGINAL_MUSIC','repl':replica_prefix+'\\REPLICA_'+replica_postfix}
	print(replica_mapD)
	r = None
	resD = {'okeyL':[],'outdatedL':[],'missedL':[]}
	
	
	# ��������� ������ ��� ��������� ������
	print("Calculating the delta list for normal single tracks data and deleting the rest of convert_single folder [format:%s]"%format)
	delta_normL = []
	for a in key_normL:
		
		if branch_filter != None: 
			if branch_filter not in a:
				continue
		checkD = {'message':'','track':None}
		alb_copyL = []
		for b in key_normD[a]:
			checkD = checkReplicaMapping(metaD[b],format,replica_mapD)

			if checkD['message'] == 'OK':
				
				resD['okeyL'].append(checkD)
				
				continue
			elif checkD['message'] == 'no_replica':
				resD['missedL'].append(checkD)
				
				orig_path = metaD[b]['path']
				if orig_path not in delta_normL:
					delta_normL.append(orig_path)
				continue
			elif checkD['message'] == 'outdated':
				orig_path = metaD[b]['path']
				resD['outdatedL'].append(checkD)
				if orig_path not in delta_normL:
					delta_normL.append(orig_path)
				continue
			elif checkD['message'] == 'ERROR':	
				if len(checkD['track']) > 255:
					print()
					print("Long track path(norm) %s"%str(len(checkD['track'])))	
					print(checkD['track'])
			else:
				print('*', end=' ')
				continue
	# ��������� ������ ��� CUE
	print("Calculating the delta list for cue data and deleting the rest of convert_cue folder [format:%s]"%format)
	delta_cueL = []
	for a in key_cueL:
		if branch_filter != None:
			#if 'Biber' in a:
			#	print branch_filter,a 
			if branch_filter not in a:
				continue
		checkD = {'message':'','track':None}
		alb_copyL = []
		for b in key_cueD[a]['metaKeyL']:
			checkD = checkReplicaMapping(metaD[b],format,replica_mapD)

			if checkD['message'] == 'OK':
				
				resD['okeyL'].append(checkD)
				#.................................
				# ���� ��������� ������� ��� �������� ��� ��������� ����� �������
				# ���� ����� ����� ����� �������� ���� �������� �� ��������� ������� �����.
				pos = a.rfind('\\')
				album_path = a[:pos+1]
				
				track_key = checkD['cue_key']
				
				
				
				if os.path.exists(album_path+'convert_cue\\'):
					convert_dir_empty = True
					for f_name in os.listdir(album_path+'convert_cue\\'):
						convert_dir_empty = False
						if track_key in f_name:
							#raw_input("%s to be removed >Press a key"%(f_name))
							os.remove(album_path+'convert_cue\\'+f_name)
							
							if len(os.listdir(album_path+'convert_cue\\')) > 0:
							
								#raw_input("%s  folder rest >Press a key"%(os.listdir(str(album_path+'convert_cue\\'))))
								for m3u_name in os.listdir(album_path+'convert_cue\\'):
									if 'm3u' in m3u_name:
										os.remove(album_path+'convert_cue\\'+m3u_name)
								if len(os.listdir(album_path+'convert_cue\\')) == 0:
									os.rmdir(album_path+"convert_cue\\")
									print('--->   '+album_path+"convert_cue\\"+" --> is deleted")
									continue
							elif len(os.listdir(album_path+'convert_cue\\')) == 0:
								os.rmdir(album_path+"convert_cue\\")
								print('--->   '+album_path+"convert_cue\\"+" --> is deleted")	
						else:
							if '(0)' in f_name or '(00)'  in f_name:	
								os.remove(album_path+'convert_cue\\'+f_name)
									
						if convert_dir_empty:
							os.rmdir(album_path+"convert_cue\\")
							print('--->   '+album_path+"convert_cue\\"+" --> is deleted")
						
				# .............. ����� ���������� ����� �������� �������
				continue
				
			elif checkD['message'] == 'ERROR':	
				if len(checkD['track']) > 255:
					print()
					print("Long track path(CUE) %s"%str(len(checkD['track'])))	
					print(checkD['track'])					
			elif checkD['message'] == 'no_replica':
				if os.path.exists(album_path+'convert_cue\\'):
					convert_dir_empty = True
					#print "****������**"
					for f_name in os.listdir(album_path+'convert_cue\\'):
						convert_dir_empty = False
						break
					if convert_dir_empty:
						os.rmdir(album_path+"convert_cue\\")
						print('--->   '+album_path+"convert_cue\\"+" --> is deleted")	
						
				resD['missedL'].append(checkD)
				alb_copyL.append(checkD['cue_key'])
				if a not in delta_cueL:
					delta_cueL.append(a)
					
				continue
			elif checkD['message'] == 'outdated':
				if os.path.exists(album_path+'convert_cue\\'):
					convert_dir_empty = True
					for f_name in os.listdir(album_path+'convert_cue\\'):
						convert_dir_empty = False
						break
					if convert_dir_empty:
						os.rmdir(album_path+"convert_cue\\")
						print('--->   '+album_path+"convert_cue\\"+" --> is deleted")		
					
				alb_copyL.append(checkD['cue_key'])
				resD['outdatedL'].append(checkD)
				if a not in delta_cueL:
					delta_cueL.append(a)
				
				continue
			else:
				print('*Strange:',checkD)
				continue
		
		key_cueD[a]['track_numL'] = alb_copyL	
	if 'only_info' in args:
		return resD
		
	# ������ ������ ������ ��� ������� ������, ���� � ��� �������� ������ ������� ������	
	print("The delta list for general single track data ->%d entries"%(len(delta_normL)))	
	delta_normL.sort()
	for a in delta_normL:
		
		pos = a.rfind('\\')
		album_path = a[:pos+1]
		print('Album at normal: %s ->converting to %s, tracks:%s :'%(album_path,format,str(len(key_normD[album_path]))))
		tz = time.time()
		if os.path.exists(a):
			dest_dir = album_path.replace(replica_mapD['orig'],replica_mapD['repl'])
			print(dest_dir)
			if not os.path.exists(dest_dir):
				#raw_input("%s to be created >Press a key"%(dest_dir))
				os.makedirs(dest_dir)
				print()
				print('created:',dest_dir)
			if 'no_norm_convert'	not in args:	
				r = convertLosless_2_lossy(format,codec_path,{}, "\""+a+ "\"",dest_dir,temp_dir)
		
			if r ==0:
				print('*', end=' ')
		
	# ������ ������ ������ ��� CUE, ���� � ��� �������� ������ CUE ������	
	print("The delta list for cue data ->%d entries"%(len(delta_cueL)))
	for a in delta_cueL:

		pos = a.rfind('\\')
		album_path = a[:pos+1]
		tz = time.time()
		
		# ��������� �������� ����� ���� ���� �� ������� ������� ������, � ��� ���� ������������, � ���� ������ ����� �������������� �� �����. ��.� ���������� ��� ����������
		# ���� ��������� ����� ����������� �� ������ ��� ������ �����������, �� � ����� ���� ��� �� ���������������� ������ �� ����
		if not os.path.exists(album_path+'convert_cue\\'):
			# ��� �������������� ��� ����������� ���������� ������, ���� ��� �������, ��� ������� �������������� cue �����
			# ����� ������ ���������� ������� ����� � �������
			os.mkdir(album_path+'convert_cue\\')
		if 	key_cueD[a]['track_numL'] != []:
			metad_key = key_cueD[a]['metaKeyL'][0]
			image_cue = metaD[metad_key]['cue_fname']
			image_name = metaD[metad_key]['path']
			#print image_name
			
			output_dir = ('-d',""" "%sconvert_cue" """%(album_path))
			output_form = output_dir + ('-t',""" "(%n). %p - %t" """)
			tr_name_conv = ('-m',":-/_*x")
			
			extract_list = ''
			try:
				part_l = ','.join([str(int(b[1:-1])) for b in key_cueD[a]['track_numL']])
				extract_list = ('-x', part_l)
			except:
				pass
			if 	part_l == '':
				extract_list = ''
			
			replace_flag = False
			newL = []
			if '.ape' in image_name:
				prog = 'mac.exe'
				f = open(image_cue,'r')
				l = f.readlines()
				f.close()
	
				for line_str in l:
					if """.ape"w""".lower() in line_str.replace(' ','').lower():
						newL.append("""FILE "temp.wav"  WAVE\n""")
					else:
						newL.append(line_str)
						
				f=open(image_cue+'temp','w')
				f.writelines(newL)
				f.close()
				
				params = ('mac',"\""+image_name+"\"","\""+album_path+'temp.wav'+"\"",'-d')
				#print params
				try:
					r = os.spawnve(os.P_WAIT, codec_path+prog, params , os.environ)
				except Exception as e:
					print("Error at mac execution:",e)
					
				image_cue = image_cue+'temp'
				image_name = album_path+'temp.wav'
				
				replace_flag = True

			params = ('shntool','split',"\""+image_name+"\"",'-O','always')+tr_name_conv+extract_list+('-f',"\""+image_cue+"\"")+output_form
			try:
				r = os.spawnve(os.P_WAIT, codec_path+'shntool.exe',params, os.environ)
			except Exception as e:
					print("Error at shntool split execution:",e)
			
				
			
			if '.wav' in image_name and replace_flag:
				if 'temp' in image_cue:
					os.remove(image_cue)
				if 'temp.wav' in image_name:
					os.remove(image_name)

			
			#shntool split "image.flac"  -O always -x 2,5,6 -f "image.cue"  -t "(%n). %p - %t"
			
		
		if os.path.exists(album_path+'convert_cue\\'):
			print('Album at cue: %s ->converting to mp3, tracks:%s :'%(album_path,str(len(key_cueD[a]['track_numL']))))
			
			for f_name in os.listdir(album_path+'convert_cue\\'):
				f_key = f_name[:f_name.find('.')]
				#print '#####################'
				#print f_key
				#print key_cueD[a]['track_numL']
				if f_key not in key_cueD[a]['track_numL']:
					#print f_key
					# ���������� ���� ������� �������� CUE �����
					#print f_key,keyD[a]
					continue
				#print f_key,'OK!'
				if os.path.exists(album_path+"convert_cue\\"+f_name):
					full_name =  "\""+album_path+"convert_cue\\"+f_name+"\""
					ext = os.path.splitext(album_path+"convert_cue\\"+f_name)[1].lower()
					#print '-->',ext
					# !! ������ ������� ��� �������� ��� ��� �� ��������� ���������� ��������� ������� ������ ��� ���, � ���� ���!!!???
					
					doL = ['.ape','.flac']
					doL = ['.ape','.flac','.wav']
					if ext not in doL:
						continue
					#if '.flac' in ext:
					#	continue
					#print full_name
					dest_dir = album_path.replace(replica_mapD['orig'],replica_mapD['repl'])
					if not os.path.exists(dest_dir):
						os.makedirs(dest_dir)
						print('created:',dest_dir)
						
					r = 1
					if 'no_cue_convert'	not in args:
						r = convertLosless_2_lossy(format,codec_path,{},full_name,dest_dir,temp_dir)
					#r = 0
					if r == 0:
						print('*', end=' ')
						#raw_input("%s to be removed >Press a key"%(full_name))
						if '.wav' not in full_name:
							os.remove(full_name[1:-1])
						if len(os.listdir(album_path+'convert_cue\\')) == 2:
						# delete m3u 
							#raw_input("%s  folder rest >Press a key"%(os.listdir(str(album_path+'convert_cue\\'))))
							for m3u_name in os.listdir(album_path+'convert_cue\\'):
								if 'm3u' in m3u_name:
									os.remove(album_path+'convert_cue\\'+m3u_name)
							if len(os.listdir(album_path+'convert_cue\\')) == 0:
								os.rmdir(album_path+"convert_cue\\")
								print('album finished in:',	str(int(time.time()-tz)),album_path)	
								continue
						if len(os.listdir(album_path+'convert_cue\\')) == 0:
								os.rmdir(album_path+"convert_cue\\")		
		print('album finished in:',	str(int(time.time()-tz)),album_path)	
		
	input("Finished %s albumes  >Press a key"%(str(len(delta_cueL))))	
	return resD

def do_fingerprint_from_metaD(branch_filter,metaD,*args):
	# ������� ���������� ����������� �� lossless �������� � mp3, � ������ ���������
	key_cueL = []
	key_normL = []
	key_cueD = {}
	key_normD = {}
	delta_map_cueD ={}

	ts=time.time()			
	cnt = 0
	codec_path = "D:\\Local Soft\\Codecs\\"
	print('Collecting album data and statistics')
	for a in metaD:
		if cnt%10000 ==0:
			print(cnt, end=' ')
		cnt+=1
		if metaD[a]['cue_fname'] != None:
			if metaD[a]['cue_fname'] not in key_cueD:
				key_cueD[metaD[a]['cue_fname']] = {'metaKeyL':[a],'track_numL':[]}
			else:
				key_cueD[metaD[a]['cue_fname']]['metaKeyL'].append(a)
		else:
			if '.flac' in metaD[a]['path'].lower() or '.ape' in metaD[a]['path'].lower() or '.mp3' in metaD[a]['path'].lower():
				pos = metaD[a]['path'].rfind('\\')
				album_path = metaD[a]['path'][:pos+1]
				if album_path not in key_normD:
					key_normD[album_path] = [a]
				else:
					key_normD[album_path].append(a)
	key_cueL = list(key_cueD.keys())
	key_cueL.sort()
	key_normL = list(key_normD.keys())
	key_normL.sort()
	
	print()
	print("cue albums number:",len(key_cueL))
	print("losles albums number:",len(key_normL))

	
	r = None
	resD = {'okeyL':[],'outdatedL':[],'missedL':[]}
	
	
	# ��������� ������ ��� ��������� ������
	print("Calculating the delta list for normal single tracks data and deleting the rest of convert_single folder [format:%s]"%format)
	delta_normL = []
	for a in key_normL:
		if branch_filter != None: 
			if branch_filter not in a:
				continue
		tz=time.time()		
		r = create_fingerprint_file(codec_path,a)
		
		print('album [%s] finished in:%s total hours:%3.3f'%(str(a),str(int(time.time()-tz)),float(float(time.time()-ts)/3600)))
	# ��������� ������ ��� CUE
	print("Calculating the delta list for cue data and deleting the rest of convert_cue folder [format:%s]"%format)
	delta_cueL = []
	for a in key_cueL:
		if branch_filter != None:
			if branch_filter not in a:
				continue
		tz=time.time()		
		pos = a.rfind('\\')
		album_path = a[:pos+1]
		r = create_fingerprint_file(codec_path,album_path)
				
		
		print('album [%s] finished in:%s total hours:%3.3f'%(str(a),str(int(time.time()-tz)),float(float(time.time()-ts)/3600)))
		
	input("Finished %s albumes  >Press a key"%(str(len(delta_cueL))))	
	return resD

	
def getPlaylistsfromXML(mlPath):
	return {}
	f = open(mlPath,'rb')
	#print mlPath
	xml = f.readline()
	f.close()
	soup = BeautifulStoneSoup(xml)
	p = soup.findAll("playlist")
	playListD = {}
	for a in p:
		#print a.attrs
		playListD[str(a.attrs[0][1])]={}
		for b in a.attrs:
			playListD[str(a.attrs[0][1])][str(b[0])]=b[1]
	return playListD	
	
def getCoverPage(url,dest_dir):
	logger.debug('in getCoverPage dest dir[%s] - Start'%(dest_dir))
	h = urlopenWithCheck(url)
	#print h[0].headers.dict
	httpCheckL = ['http:\\','http://','https://','https:\\']
	if h[0] == None:
		#print 'h[0] == None'
		return None
	
	
	
	for httpp_ref in httpCheckL:
		pos = url.find(httpp_ref)
		if pos == -1:
			continue
		else:	
			print('pos=',pos,url)
			break
		
	if pos == -1:
		print('WRONG pos=',pos,url)
		logger.critical('Error 6913: in getCoverPage WRONG pos - Finished')
		return -1
		
	if 	dest_dir[-1] != '\\':
		dest_dir  += '\\'
		
	if 'content-type' in h[0].headers.dict:
		#print 'Yes Content-Type'
		#if h[0].headers.dict['content-type'] == 'image/jpeg' or h[0].headers.dict['content-type'] == 'text/html':
		if True:
			#print 'Yes JPG'
			obj = h[0].read()
			if os.path.exists(dest_dir+'cover.jpg'):
				cur_time_stamp = time.strftime('%Y%m%d%H%M%S', time.localtime())
				shutil.copy(dest_dir+"cover.jpg", dest_dir+"cover%s.jpg"%(cur_time_stamp))
			
			#print 'Cover page get!!!'
			f = open(dest_dir+'cover.jpg','wb')
			f.write(obj)
			f.close()
			#print 'Cover page get 22!!!'
			os.remove(dest_dir+'cover_320.jpg')
			#startfile(dest_dir+'cover.jpg')
			print('Cover page get 22!!!')
			logger.debug('in getCoverPage 1 - Finished')
			return 1
	else:
		print('rebug- ',h[0].headers.dict)	
	print('Error at picture getting')
	print("the headers are:")
	print(h[0].headers.dict)
	logger.critical('Error 6944: in getCoverPage 2 - Finished')	
	return -1		
	
def cue_check_and_error_correct(fName,separator,seqL,*args):
	fType = ''
	try:
		f = open(fName,'r')
	except:
		print('File not found:',fName)
		return None
	l = f.readlines()
	f.close()
	track_flag = False
	album = ''
	full_time = ''
	orig_file = ''
	orig_file_path = ''
	perform_main = ''
	track_num = 0
	trackD = {}
	resL = []
	got_file_info = False
	do_job = False
	for a in l:
		if 'TRACK 01 AUDIO' in a:
			do_job = True
			
		if not do_job:
			resL.append(a)
			continue
			
		pos = a.find('"')+1
		if 'separate' in args:

			if a.lower().strip().find('performer') == 0:
				index = None
				if seqL[0].lower() == 'artist':
					index = 0
				else:
					index = 1

				if index == None:
					print('Error')
					return 0


				
				partsL = a[pos:-2].split(separator)
				print(partsL)
				try:
					line = '\t'+'PERFORMER "'+partsL[index].strip()+'"'+'\n'
				except:
					resL.append(a)
					print('Eroror',a)
					continue		
			elif a.lower().strip().find('title') == 0:
				index = None
				if seqL[0].lower() == 'artist':
					index = 1
				else:
					index = 0

				if index == None:
					print('Error')
					return 0
					
					
				
				partsL = a[pos:-2].split(separator)
				print(partsL)
				try:
					line = '\t'+'TITLE "'+partsL[index].strip()+'"'+'\n'
				except:
					resL.append(a)
					print('Eroror',a)
					continue	
			else:
				line = a
			resL.append(line)
	file_name_new =	'corrected_'+fName
	f = open(file_name_new,'w')
	l = f.writelines(resL)
	f.close()
	
def get_discs_duplacates(dbPath,albumD,minimum_folder_depth,*args):
	length_clastersD = {}
	checkL = [' cd',' disc','(disc','(disk',' disk',' vol',' volume']
	punctL = ['_','.',',',':']

	albums_clastD = {}

	rel_typeL = ['DBL_DISC','SERIA','BOX']

	for a in albumD:
		if albumD[a]['format']==None:
			continue
		r = os.path.split(albumD[a]['path'])
		length =  len(r[0].split('\\'))
		if length <= minimum_folder_depth:
			continue

		disc_name = r[1].lower()

		for punct in punctL:
			if punct in disc_name:
				disc_name.replace(punct,' ')
		for word in checkL:
			if word in disc_name:
				#print disc_name,a
				parentD = None
				albums_to_relLD = getAlbum_relation_metaD(dbPath,None,a,'get_neibor','only_to_rel')['albums_to_relLD']
				if albums_to_relLD != []:
					if 'with_exist_in_db' in args:
						parentD = [rel_item for rel_item in albums_to_relLD if rel_item['rel_type'] in rel_typeL][0]
					else:
						continue
							
					
				
				if length in length_clastersD:
					length_clastersD[length].append({'key':a,'head':r[0],'disc_name':r[1],'path':albumD[a]['path'],'parentD':parentD})
				else:
					length_clastersD[length] = [{'key':a,'head':r[0],'disc_name':r[1],'path':albumD[a]['path'],'parentD':parentD}]
				break
			
	

	for depth_node in length_clastersD:
		length_clastersD[depth_node].sort(key=operator.itemgetter('path'))
		for item in length_clastersD[depth_node]:
			if item['head'] not in albums_clastD:
				item['depth'] = depth_node
				prop_clast_name = os.path.split(item['head'])[-1]
				albums_clastD[item['head']] = {'prop_clast_name':prop_clast_name,'clast_contentLD':[item]}
			else:
				albums_clastD[item['head']]['clast_contentLD'].append(item)
##dd = get_discs_duplacates(d['albumD'],4)
	#for a in dd:
	#	print '*****',a,len(dd[a]['clast_contentLD']),'[',dd[a]['prop_clast_name']
	#	for item in dd[a]['clast_contentLD']:
	#		print item['head'],'--->',item['disc_name']
	#	print

	return albums_clastD
	
def checkMediaLibResposeTime(num):
	statL =[]
	statL2 =[]
	p_appl = xmlrpclib.ServerProxy('http://localhost:9000')
	s_appl = xmlrpclib.ServerProxy('http://localhost:9001')
	for a in range(num):
		t = time.time()
		r=p_appl.get_status()
		statL.append(time.time()-t)
		t = time.time()
		r=s_appl.appl_status()
		statL2.append(time.time()-t)
		print('.', end=' ')
	return 	sum(statL)/len(statL),sum(statL2)/len(statL2)	


	
	
	
def checkANDkillMLPids(*args):
	import win32api
	pidsL = os.popen("tasklist").readlines()
	pidL =[]
	res = ''
	for a in pidsL:
		if 'winamp' in a or 'python.exe' in a  or 'python2.exe' in a  or 'python3.exe' in a:
			try:
				pidL.append(int(a[29:34]))
				if 'kill' not in args:
					res += "<BR>%s" % str(a)
			except Exception as e:
				res += "Error:[%s]"%(str(e))
				pass
	if 'kill' in args:
		for pid in pidL:
			try:
				handle = win32api.OpenProcess(1, False, pid)
				win32api.TerminateProcess(handle, 0)
				win32api.CloseHandle(handle)
				res += "Successfully killed process on pid %d.<BR>" % (pid)
			except win32api.error as err:
				res += str(err)+"<BR>"
				continue
	return res

	
	
def RebootServer(message='Rebooting', timeout=1, bForce=1, bReboot=1): 
	import win32api
	AdjustPrivilege(SE_SHUTDOWN_NAME) 
	try: 
		win32api.InitiateSystemShutdown(None, message, timeout, bForce, bReboot) 
	finally: 
        # Now we remove the privilege we just added. 
		AdjustPrivilege(SE_SHUTDOWN_NAME, 0) 


def registerRadio(dbPath,radioUrl,RadioName,existed_station,bitrate):
	db = sqlite3.connect(dbPath)
	#db.text_factory = str
	t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
	
	lastrowid = None
	return_message = ''
	
	radioPathnode = None
	
	try:
		radioNodePath = readConfigData(mymedialib_cfg)['radioNodePath']	
	except:
		logger.critical('Exception in registerRadio: RadioNodePath not or wrong maintained')

	#print 'Radio - 1'	
	c = db.cursor()
	
	title = RadioName
	titleCRC32 = None
	

	# Радио кодируем обычным способом чисто из URL	
	radioCRC32 = zlib.crc32(radioUrl)
	
	
	# CRC32 Артиста и Альбом кодируем уникальным способом один раз по дате, если соотве записи Альбома и Артиста создаются потом, то их
	#надо подтягивать из таблицы Трэк - это нужно для совместимости с общем подходом для обычных трэков для получения картинки 
	try:
		artist_crc32 = album_crc32 = titleCRC32 = zlib.crc32(title+t_date)
	except:
		artist_crc32 = album_crc32 = titleCRC32 = zlib.crc32((title+t_date).encode('utf-8'))
		
		
	try:
		artist_crc32 =  zlib.crc32(title)
	except:
		artist_crc32 = zlib.crc32((title).encode('utf-8'))	
	
	#print 'Radio - 2'
	#print 'radioCRC32:',radioCRC32

	#check radio entry existense in DB Track
	req = 'select id_track,path,artist_crc32,album_crc32 from track where path_crc32 = "%s"'%(radioCRC32)
	try:
		c.execute(req)
	except Exception as e:
		logger.critical('Exception [%s] in registerRadio'%(str(e)))
		c.close()
		db.close()
		return 
	
	l = c.fetchone()
	#print 'Radio - 3',l
	if l != None:
		return_message = "Station already registerd:"+str(l)
		logger.debug(return_message)
		artist_crc32 = l[2]
		album_crc32 = l[3]
		return
	else:
		# Радио нет, а необходимо только обновить URI ресурс уже существующеего радио
		if existed_station:
			rec = (radioUrl,radioCRC32,existed_station)
			req_upd = """update track set path = "%s", path_crc32 = %s where id_track = %s"""%rec
			try:
				logger.debug('Before Radio update %s,[%s]'%(existed_station,req_upd))
				r = c.execute(req_upd)
				lastrowid  = c.lastrowid
				print("Updated radio track:", lastrowid, existed_station)
				
			except Exception as e:
				logger.critical('Exception [%s] in registerRadio [update] track'%(str(e)))
				c.close()
				db.close()
				return
				
			rec = (radioCRC32,existed_station)	
			req_upd = """update track_tag set path_crc32 = %s where id_track = %s"""%rec			
			try:
				logger.debug('Before Radio update track_tag %s,[%s]'%(existed_station,req_upd))
				r = c.execute(req_upd)
				lastrowid  = c.lastrowid
				print("Updated radio track_tag crc32:", radioCRC32, existed_station)
				
			except Exception as e:
				logger.critical('Exception [%s] in registerRadio [update] track_tag'%(str(e)))
				c.close()
				db.close()
				return				
			
			
			db.commit()
			c.close()
			db.close()	
			return lastrowid
			
		else:
			rec = (radioUrl,radioCRC32,title,title,title,titleCRC32,titleCRC32,bitrate,t_date)
			req_ins = """insert into track (path,path_crc32,title,album,artist,artist_crc32,album_crc32,bitrate,add_date) values ("%s",%s,"%s","%s","%s",%s,%s,%s,"%s") """%rec

			try:
				logger.debug('Before Radio insert %s'%(existed_station))
				r = c.execute(req_ins)
				lastrowid  = c.lastrowid
				print("inserted radio:", lastrowid)
			except Exception as e:
				logger.critical('Exception [%s] in registerRadio [insert] track'%(str(e)))
				c.close()
				db.close()
				return
	
	
	logger.debug('Radio Artist/Albul processing start %s'%(existed_station))
	#print 'Radio - 4'
	#check radio entry existense in DB Artist
	req = 'select id_artist,artist_crc32 from artist where artist_crc32 = "%s"'%(artist_crc32)
	c.execute(req)
	l = c.fetchone()
	
	#print 'Radio - 5'
	if l != None:
		print("Artist already registerd",l)
		return_message += '\n'+"Artist already registered"+str(l)
	else:
		rec = (title,artist_crc32,title,titleCRC32,t_date,'RADIO')
		req_ins = """insert into artist (artist,artist_crc32,search_term,search_term_crc32,add_date,object_type) values ("%s",%s,"%s",%s,"%s","%s") """%rec
		#print req_ins
		try:
			r = c.execute(req_ins)
		except Exception as e:
			c.close()
			db.close()
			logger.critical('Exception [%s] in registerRadio artist'%(str(e)))
			return

	#print 'Radio - 6'
	lastrowid_artist  = c.lastrowid
	
	
	if not radioNodePath:
		lastrowid_artist  = c.lastrowid
		db.commit()
		c.close()
		db.close()
		return lastrowid,lastrowid_artist,return_message		
	
	#print 'Radio - 7'	
	#check radio entry existense in DB Album
	print("At Album radio saving:",radioNodePath)
	req = 'select id_album,album_crc32 from album where album_crc32 = "%s"'%(album_crc32)
	c.execute(req)
	l = c.fetchone()
	#print l
	if l != None:
		print("Album already registerd:  ",l)
		return_message += '\n'+"Album already registerd"+str(l)
	else:
		
		#create Radio Folder Path
		if radioNodePath[-1] == '\\':
			path =  radioNodePath+title
		else:	
			path =  radioNodePath+"\\"+title
		
		rec = (title,titleCRC32,path,album_crc32,t_date,title,titleCRC32,'mp3','RADIO',1,'RADIO')
		
		req_ins = """insert into album (album,album_crc32,path,path_crc32, add_date,search_term,search_term_crc32, format_type,album_type,tracks_num,object_type) values ("%s",%s,"%s",%s,"%s","%s",%s,"%s","%s",%s,"%s") """%rec
		
		
		try:
			r = c.execute(req_ins)
		except Exception as e:
			c.close()
			db.close()
			logger.critical('Exception [%s] in registerRadio Album'%(str(e)))
			
			return
		# Check path existance and if not create	
		print('Checking path:',path)
		if not os.path.exists(path):
			os.mkdir(path+'\\')
			print("New Radio Folder created:",path)
		

	lastrowid_album  = c.lastrowid
	

	db.commit()
	c.close()
	db.close()
	return lastrowid,lastrowid_artist,lastrowid_album,return_message		
	
def getHardWareInfo():
	cpu_info_keyL = ['ProcessorId','ProcessorType','CurrentClockSpeed','Manufacturer','Name','CurrentVoltage','NumberOfCores','Caption','Family','SystemName']

	try:
		w = wmi.WMI(namespace="root\wmi")
	except (wmi.x_wmi,wmi.x_access_denied,wmi.x_wmi_invalid_query,wmi.x_wmi_uninitialised_thread) as e:
		return 'error after w = wmi.WMI:'+str(e)
		
	temperature_info = w.MSAcpi_ThermalZoneTemperature()[0]
	res = 'System temperature:'+str(float(temperature_info.CurrentTemperature-2732)/10)

	w = wmi.WMI(namespace="root\CIMV2")
	CPU_info = w.Win32_Processor()[0]


	for instance in CPU_info.properties:
		if instance in cpu_info_keyL:
			res+= '<BR>\n'+str(instance)+'-->'+str(getattr(CPU_info,instance))
	return res


	
def collect_images_for_album(album_crc32,album_path,*args):
	logger.debug('in collect_images_for_album [%s,%s]- Start'%(str(album_crc32),str(album_path)))
	imageL=[]
	imageLD={}
	pathL = []
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	path = None
	
	if album_crc32 != None:
		r = getAlbumD_fromDB(dbPath,None,album_crc32,[])
		if album_crc32 in r['albumD']: 
			path= r['albumD'][album_crc32]['path']
		else:
			logger.critical('Error in collect_images_for_album album_crc32[%s] not in albumD- finished'%(str(album_crc32)))
			return []
			
		if path[:1] != '/':
			path ='/'+	path
		
		path = cfgD['audioFilesPathRoot']+path		
	else: 	
		path = album_path
        
	logger.debug('in collect_images_for_album check path:[%s] '%(str(path)))
	init_dir_checkedL = []	
	init_dir_modif = b""
	if isinstance(path, str):
		#char_codec = chardet.detect(init_dir)
		
		try:
			init_dir_modif = bytes(path,encoding = BASE_ENCODING)
			init_dir_checkedL.append(path)
		except Exception as e:
			logger.critical('Exception [%s] in  collect_images_for_album'%(str(e)))	
			return []
				
		if not os.path.exists(init_dir_modif):
			print([init_dir_modif], '8049 does not exists',type(init_dir_modif))
			logger.critical('Error: dir [%s] not exists in  collect_images_for_album'%(str(init_dir_modif)))	
			return []
			
	elif isinstance(path, bytes):
		if not os.path.exists(path):
			print([path], '8055 dir does not exists')
			logger.critical('Error: dir [%s] not exists in  collect_images_for_album'%(path))	
			return []
		else:
			init_dir_checkedL.append(path)	
	pathL.append(path)
	cover_insert_index=0
	
	if album_crc32 != None:
		albumD = getAlbum_relation_metaD(dbPath,None,album_crc32,'get_neibor')
		if albumD['albums_all_relLD'] != []:
			for a in albumD['albums_all_relLD']:
				r = getAlbumD_fromDB(dbPath,None,a['key'],[])
				path=r['albumD'][a['key']]['path']
				if path not in pathL:
					pathL.append(path)
	# Проверить, что на уровне выше нет директории с картинками			
	parent_dirL = []
	parent_imageL = []
	separate_image_dir_indicator = False
	if len(pathL) > 1:
		for a in pathL:
			#print '7438 :',pathL
			
			parent = a[:a[:-1].rfind('/')]
			#print '7441',parent
			if parent not in parent_dirL:
				parent_dirL.append(parent)
				#print '7444',parent_dirL
		if len(parent_dirL)	== 1:
			for root, dirs, files in os.walk(parent_dirL[0]):
				#print 'root',root
				if root in parent_dirL[0]:
					continue
				if root in pathL:
					continue
				else:
					#print "7454",root
					imageL = []
					for f_name in files:
						
						if f_name[f_name.rfind('.'):].lower().find('.jpg') >= 0 or f_name[f_name.rfind('.'):].lower().find('.pdf') >= 0 or f_name[f_name.rfind('.'):].lower().find('.png') >= 0:
							print("7459",f_name)
							separate_image_dir_indicator = True	
							f_path = os.path.join(root,f_name)
							if os.path.exists(f_path):
								crc32 = zlib.crc32(f_path.lower().encode(BASE_ENCODING))
								
								if 'cover' in f_name.lower():
									
									imageL.insert(cover_insert_index,{"image_crc32":crc32,'f_path':f_path,'f_name':f_name})
									cover_insert_index+=1
								else:	
									imageL.append({"image_crc32":crc32,'f_path':f_path,'f_name':f_name})
							
						elif '.mp3' in f_name.lower() or '.ape' in f_name.lower() or '.flac' in f_name.lower():	
							separate_image_dir_indicator = False
				
					if not separate_image_dir_indicator:
						imageL = []
					else:
						parent_imageL += imageL	
	
	#print parent_imageL,imageL
	imageL = []
						
	for init_dir in pathL:
		print()
		print('Scanning:',init_dir,len(pathL))
		i = 0
		for root, dirs, files in os.walk(init_dir):
			
			if i%100 == 0:
				print(i, end=' ')
			i+=1
			for a in files:
				
				if a[a.rfind('.'):].lower().find('.jpg') >= 0 or a[a.rfind('.'):].lower().find('.pdf') >= 0 or a[a.rfind('.'):].lower().find('.png') >= 0:
					f_path = root+'/'+a
					if os.path.exists(f_path):
						crc32 = zlib.crc32(f_path.lower().encode(BASE_ENCODING))
						#imageLD[crc32]=f_path
						if 'cover' in a.lower():
							if a == 'cover_100.jpg' or a == 'cover_320.jpg':
								continue
							imageL.insert(cover_insert_index,{"image_crc32":crc32,'f_path':f_path,'f_name':a})
							cover_insert_index+=1
						else:	
							imageL.append({"image_crc32":crc32,'f_path':f_path,'f_name':a})
							
	resL = parent_imageL+imageL
	if (len(parent_imageL+imageL) > 30):
			logger.critical(' Warning: in collect_images_for_album - Finished with Huge result image list! total [%s] parent_imageL: [%s] restribted to 30'%(str(len(parent_imageL+imageL)),str(len(parent_imageL))))
			resL = resL[:30]	
			return resL
	logger.debug('in collect_images_for_album - Finished with resL total: len[%s] parent_imageL:len[%s]'%(str(len(parent_imageL+imageL)),str(len(parent_imageL))))		
	return resL
	
def getFolderPathL_fromDB_viaTermL(dbPath,db,TermL,audioFilesPathRoot):	
	logger.debug('in getFolderPathL_fromDB_viaTermL [%s]- Start'%(str(TermL)))
	extDbFlag = False
	resL = []
	if not isinstance(TermL,list):
		logger.critical('Error in getFolderPathL_fromDB_viaTermL TermL is not a list')

	if db == None:
		db = sqlite3.connect(dbPath)
		extDbFlag = True
		#db.text_factory = bytes
	resD = {}
	resLD = []

	
	
	try:
		MLFolderTreeNodeL = getFolderAlbumD_fromDB(None,db,None,[],'all','folder_tree_nodes')
	except Exception as e:
		if extDbFlag:
			db.close()	
	print("*****Tut1****",len(MLFolderTreeNodeL))
	extract_dirL = [] # Additional dir list for nodes at higher level
	node_key = 'folder_node'
	node_key = 'path'
		
	tempL = []
	for a in MLFolderTreeNodeL:
		found_term = True	
		for term in TermL:
			try:
				path_lower = a[node_key].lower()
			except:
				print("---------------------->>error:", MLFolderTreeAll_List.index(a),a)
				
			if term not in path_lower:
				found_term = False
				break 
		if not found_term:
			continue
			
		path = audioFilesPathRoot+'/'+a[node_key]
		resL.append(os.path.split(path))
		
		
	if extDbFlag:
		db.close()	
	logger.debug('in getFolderPathL_fromDB_viaTermL [%i]- Finished'%(len(resL)))	
	return resL	
		
def getFolderAlbumD_fromDB(dbPath,db,albumCRC32,albumCRC32L,*args):
	extDbFlag = False

	if db == None:
		db = sqlite3.connect(dbPath)
		extDbFlag = True
		#db.text_factory = bytes
	resD = {}
	resLD = []

	c = db.cursor()
	mode_str = ''
	if 'all' in args:
		req = 'select id_album, album, album_crc32, path,path_crc32 from album'
		mode_str = "all entries from ALBUM"
	elif albumCRC32L != []:
		req = 'select id_album, album, album_crc32, path,path_crc32 from ALBUM where path_crc32 in (%s)'%(str(albumCRC32L)[1:-1])
		mode_str = str(albumCRC32L)
	elif albumCRC32 != None:
		req = 'select id_album, album, album_crc32, path,path_crc32 from album where path_crc32 = %s'%(str(albumCRC32))
		mode_str = str(albumCRC32)

	try:
		#print req
		c.execute(req)
	except Exception as e:
		c.close()
		if extDbFlag:
			db.close()	
		return {'error_message':e,'path_crc32':mode_str}
	
	try:
		db_ALBUM_pathL =c.fetchall()
	except Exception as e:
		#print e,mode_str
		c.close()
		if extDbFlag:
			db.close()
		return {'error_message':e,'path_crc32':mode_str}
	c.close()
	if extDbFlag:
		db.close()
		
	
	nodesLD = []
	for a in db_ALBUM_pathL:
		if 'folder_tree_nodes' in args:
			try:
				dir_name = os.path.dirname(a[3])
			except Exception as e:
				print('Error: extract dirname:',a[3],a)
				return {'error_message':e,'path_crc32':mode_str,'item':a}
			if dir_name not in nodesLD:
				nodesLD.append(dir_name)
				resLD.append({'id_album':a[0], 'album':a[1], 'album_crc32':a[2], 'path':a[3],'path_crc32':a[4],'folder_node':dir_name})
		else:		
			resLD.append({'id_album':a[0],'album':a[1], 'album_crc32':a[2], 'path':a[3],'path_crc32':a[4],'folder_node':''})

	resLD.sort(key=operator.itemgetter('path'),reverse=True)	
	return resLD
	
if __name__ == '__main__':
	
	cfgD = readConfigData(mymedialib_cfg)
	dbPath = cfgD['dbPath']
	#l = MediaLibCoverageCheck_GUI('')
	
	#Mobj = MediaLibPlayProcess()
	#pD = Mobj.MediaLibPlayProcessDic()['pD']
	#playlistpath = mediaPath
	
	#metaDAll = myMediaLib_adm.getCurrentMetaData_fromDB_via_DbIdL([],None,'take_all')
	#pD = refresh_server()['pD']
	#group2listMaintain(dbPath,pD)				
