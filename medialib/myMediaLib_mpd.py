from myMediaLib_init import readConfigData

from myMediaLib_adm import db_request_wrapper
from myMediaLib_adm import getDbIdL_viaTagId
from myMediaLib_adm import getDbIdL_viaAlbumCRC32
from myMediaLib_adm import getDbIdL_viaAlbumCRC32_List
from myMediaLib_adm import getDbIdL_viaArtistCRC32_List
from myMediaLib_adm import getArtist_Album_relationD_and_simpleMetaD_viaCRC32L
from myMediaLib_adm import getAll_Related_to_main_Artist_fromDB
from myMediaLib_adm import getCurrentMetaData_fromDB_via_DbIdL
from myMediaLib_adm import getAlbumD_fromDB

import time
import asyncio
import logging
from mpd.asyncio import MPDClient
import os
import sys
import pickle
from os import scandir
import itertools

from os.path import join
from os import curdir, sep,getcwd 


from myMediaLib_CONST import BASE_ENCODING
from myMediaLib_CONST import mymedialib_cfg

cfgD = readConfigData(mymedialib_cfg)
logger = logging.getLogger('controller_logger.mpd_lib')

def my_fetch_status(client):
	try:
		print('Norm')
		client.fetch_idle()
		try:
			client.send_status()
			r = client.fetch_status()
			client.send_idle()
			return r
		except mpd.base.ConnectionError as e:
			print('Connect lost after Norm')
			client.disconnect()
			client.connect(host, 6600)
			client.send_status()
			r = client.fetch_status()
			client.send_idle()
			return r
	except mpd.base.PendingCommandError as e:
		print('Exc')
		#client.send_idle()
		#client.fetch_idle()
		try:
			client.send_status()
			r = client.fetch_status()
			client.send_idle()
			return r
		except mpd.base.ConnectionError as e:
			print('Connect lost')
			client.disconnect()
			client.connect(host, 6600)
			client.send_status()
			r = client.fetch_status()
			client.send_idle()
			return r
	print('strange')

def get_mpd_extend_status(mpd_client,host, socket, mpd_path_prefix, media_lib_allcrc32L):
	mpd_tuplL = get_mpd_playlist_as_crc32_tuplL(mpd_client,host,socket, mpd_path_prefix)
	
	return resolve_mpd_crc32_tuplL_with_all_medialib(set(media_lib_allcrc32L),mpd_tuplL)
	
	try:
		mpdHandle.connect(host, socket)
	except ConnectionError as e: 
		errorLog.append((None,e,None))
		return {'mpdHandle':mpdHandle,'sorted_crc32L':[],'errorLog':errorLog}
	
	mpdHandle.clear()
	
	#cur_pl_key_crc32 = self.get_cur_pl_key_crc32()
		#return 'puk'
	try:
		cur_pl_key_crc32 = self.getPlaylistFingerPrint()
	except Exception as e:
		print('Error:',e)
		return 
	cur_pl_pos = self.__winampObj.getPlaylistPosition()
	list_length = self.__winampObj.getListLength()
		
	return {'list_length':list_length,
				'pl_pos':cur_pl_pos,
				'pL_CRC32':cur_pl_key_crc32,
				'track_CRC32':self.get_cur_track_crc32(),
				'playBack_Mode':self.__winampObj.getPlaybackStatus(),
				'playingTrack_pos':self.__winampObj.getPlayingTrackPosition(),
				'rest_sec':(self.__winampObj.getPlayingTrackLength()*1000 - self.__winampObj.getPlayingTrackPosition())/1000,'duration_sec':(self.__winampObj.getPlayingTrackLength())}	
		

def get_mpd_playlist_as_crc32L(mpd_client,host, socket, mpd_path_prefix, media_lib_allcrc32L):
	mpd_tuplL = asyncio.run(get_mpd_playlist_as_crc32_tuplL(mpd_client,host,socket, mpd_path_prefix))
	
	return resolve_mpd_crc32_tuplL_with_all_medialib(set(media_lib_allcrc32L),mpd_tuplL)
	
async def get_mpd_playlist_as_crc32_tuplL(mpd_client,host,socket, mpd_path_prefix):
	# Т.к невозможно восстановить способ генерации CRC32 (трэк, или сue), то формируем оба варианта
	# resolve_mpd_crc32_tuplL_with_all_medialib -> выбирает правильный вариант CRC32
	#mpd_path_prefix = "NAS/GoflexHomeUSB/Seagate/Music/"
	#mpd_host = 'moode-aoide.local'
	#mpdHandle = mpd.MPDClient()
	#mpdHandle.connect(mpd_host, 6600)
	pl_list = []
	errorLog = []
	
	#try:
	#	mpd_client.connect(host, socket)
	#except ConnectionError as e: 
	#	errorLog.append((None,e,None))
	#	print(e)
	#	return []
	
	try:
		await mpd_client.connect(host, socket)
	except Exception as e:
		print("Connection failed:", e)
        
		
	try:
		pl_list= await mpd_client.playlistinfo()
	except Exception as e:
		print("Connection failed pl_list:", e)
		mpd_client.disconnect()
        
	mpd_client.disconnect()	
			
	crc32L = []
	for item in pl_list:
		#file_name = item['file'].replace("/","\\").replace(mpd_path_prefix,'')
		file_name = item['file'].replace(mpd_path_prefix,'').replace("/","\\")
		crc32_cue = None
		track_num = 0
		if 'track' in item:
			track_num = item['track']
			crc32_cue = zlib.crc32((file_name+str(int(track_num))).encode(BASE_ENCODING))
			#crc32_cue = zlib.crc32((file_name+str(int(track_num))).encode('utf-8'))
		crc32 = zlib.crc32(file_name.encode(BASE_ENCODING))
		#crc32 = zlib.crc32(file_name.encode('utf-8'))
		#print(file_name,track_num) 
		crc32L.append((crc32_cue,crc32))

	return crc32L
	
def resolve_mpd_crc32_tuplL_with_all_medialib(media_lib_allcrc32L,mpd_tuplL):	
	# Call with set()!!! as first list for better perfomance--> resolve_mpd_crc32_tuplL_with_all_medialib(set(media_lib_allcrc32L),mpd_tuplL)
	#req = "select path_crc32 from track where ignore is NULL"
	#media_lib_allcrc32L = [a[0] for a in myMediaLib_adm.db_request_wrapper(db,req)]
	#return list(Intersection(media_lib_allcrc32L, list(itertools.chain.from_iterable(mpd_tuplL))))
	resL = []
	for a, b in mpd_tuplL:
		if a in media_lib_allcrc32L:
			resL.append(a)
		elif b in media_lib_allcrc32L:
			resL.append(b)
	return resL		

def load_mpd_playlist_via_tag_num(db,mpd_client,host,socket,mpd_path_preffix,object_key,mode):
	logger.debug('in load_mpd_playlist_via_tag_num[%s] - Start'%(host))
	DbIdL = []
	if mode.lower() == "track_tag":
		DbIdL=getDbIdL_viaTagId(object_key,db)
	elif mode.lower() == "album":		
		DbIdL=getDbIdL_viaAlbumCRC32(object_key,db)
	elif mode.lower() == "artist":	
		print('in artist',object_key) 
		artistCRC32L = []
		artistCRC32 = object_key
		artistCRC32L = getAll_Related_to_main_Artist_fromDB(None,db,artistCRC32)
		album_relL = []
		DbIdL = []
		print('Related ok artistCRC32L=',artistCRC32L) 
		
		# ���� ��� ������� ������, �� � ���� ����� �� ���� ��������� �������� �� ���� ������� �� ���� ��������.
		artist_rel_albumD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(None,db,[artistCRC32],[],'with_relation')['artist_rel_albumD']
		if artist_rel_albumD != {}:
			album_relL = artist_rel_albumD[artistCRC32]
			album_relL = [a for a in artist_rel_albumD[artistCRC32]['albumD']]	
			DbIdL =  getDbIdL_viaAlbumCRC32_List(None,album_relL,db)
		
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
		DbIdL = DbIdL + getDbIdL_viaArtistCRC32_List(artistCRC32L,db)
		
		
	metaD = getCurrentMetaData_fromDB_via_DbIdL(DbIdL,db)
	print('metaD len:',len(metaD))
	resD = asyncio.run(load_mpd_playlist_via_metaD(mpd_client,host,socket,metaD,mpd_path_preffix))
	if len(resD['errorLog']) > 0:
		print('errors at loading:',str(len(resD['errorLog'])))
		for a in resD['errorLog'][:10]:
			print(a)
	logger.debug('in load_mpd_playlist_via_tag_num - OK Finished')		
	return resD
	
def check_tracks_in_cue_album(db,mpdHandle,mpd_host,mpd_socket,mpd_path_prefix,cue_album_crc32L):
	
	for album_crc32 in cue_album_crc32L:
		r = load_mpd_playlist_via_tag_num(db,mpdHandle,mpd_host,mpd_socket,mpd_path_prefix,album_crc32,"album")
		mpdHandle.connect(mpd_host, mpd_socket)
		print('checking:', album_crc32)
		for a in range(len(mpdHandle.playlistinfo())):
			mpdHandle.play(a)
			time.sleep(2)
			s = mpdHandle.status()
			if 'song' in s:
				if a != int(s['song']):
					print('issue:',a,'ref:',s['song'])
			else:
				print('issue2:',a)
		mpdHandle.close()
		mpdHandle.disconnect()
		
def navigate_check_all_cue_image_albums(db,mpdHandle,mpd_host,mpd_socket,mpd_path_prefix,saved_dump,*args):
	req = """select path_crc32 from album where format_type in ('flac cue','ape cue')"""
	cue_album_crc32L = [a[0] for a in db_request_wrapper(db,req)]

	req = """select path_crc32 from track where ignore is NULL"""
	media_lib_allcrc32L = [a[0] for a in db_request_wrapper(db,req)]
	resDAll = getAlbumD_fromDB(None,db,None,[a for a in media_lib_allcrc32L])	
	mode_dif = 10
	
	checkedL = saved_dump['checkedL']
	album_issueL = saved_dump['reslist']['album_issueL']
	i = len(checkedL)
	
	
	print("start checking: [%i] total albumes, already checked [%i]" %(len(cue_album_crc32L),len(checkedL)))
		
	
	for album_crc32 in cue_album_crc32L:
		if album_crc32 in checkedL:
			continue
		ts = time.time()	
		try:
			r = load_mpd_playlist_via_tag_num(db,mpdHandle,mpd_host,mpd_socket,mpd_path_prefix,album_crc32,"album")
		except Exception as e:
			print(e)
			resD = getAlbumD_fromDB(None,db,None,[a[0]for a in album_issueL])	
			return {"album_issueL":album_issueL,'albumD':resD['albumD']}	
		try:	
			l = get_mpd_playlist_as_crc32L(mpdHandle,mpd_host, mpd_socket, mpd_path_prefix, set(media_lib_allcrc32L))
		except Exception as e:	
			print(e)
			resD = getAlbumD_fromDB(None,db,None,[a[0]for a in album_issueL])	
			return {"album_issueL":album_issueL,'albumD':resD['albumD']}		
			
		print('timing:',(time.time()-ts))
		print("*"*20)	
		#mpdHandle = r['mpdHandle']
		if len(r['sorted_crc32L']) != len(l):
			album_issueL.append((album_crc32,len(r['sorted_crc32L']),(len(r['sorted_crc32L']) - len(l))))
			if len(r['sorted_crc32L']) != (len(r['sorted_crc32L']) - len(l)):
				print("Issue prtl:",album_crc32,'[load/skipped',len(r['sorted_crc32L']), (len(r['sorted_crc32L']) - len(l)),']')
				if album_crc32 in resDAll['albumD']:
					resDAll['albumD'][album_crc32]['file']
			else:	
				print('Issue full:',len(album_issueL),'[',len(r['sorted_crc32L']),(len(r['sorted_crc32L']) - len(l)),']')
				if album_crc32 in resDAll['albumD']:
					resDAll['albumD'][album_crc32]['file']
		if i%mode_dif == 0:
			print('checked:',i,'from:',len(cue_album_crc32L), 'issue found:',len(album_issueL))
			f = open('cuecheck.dat','wb')
			resD = getAlbumD_fromDB(None,db,None,[a[0]for a in album_issueL])
			d = pickle.dump({'reslist':{"album_issueL":album_issueL,'albumD':resD['albumD']},'checkedL':checkedL},f)
			f.close()
		i+=1

		checkedL.append(album_crc32)	
		#print(album_crc32) 	
	
	if 'check_tracks' in args:
		
		album_crc32_issueL = [a[0] for a in album_issueL if a[1] != a[2]]
		print('check_tracks:',len(album_crc32_issueL))
		rt = check_tracks_in_cue_album(db,mpdHandle,mpd_host,mpd_socket,mpd_path_prefix,album_crc32_issueL)
	resD = getAlbumD_fromDB(None,db,None,[a[0]for a in album_issueL])
	return {'reslist':{"album_issueL":album_issueL,'albumD':resD['albumD']},'checkedL':checkedL}
	
def load_mpd_playlist_viaTrackCRC32L(db,mpdHandle,host,socket,trackCRC32L,mpd_path_preffix,*args):
	logger.debug('in load_mpd_playlist_viaTrackCRC32L: [%s] - Start'%(str(trackCRC32L)))
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
	logger.debug('load_mpd_playlist_viaTrackCRC32L: metaD[%s]'%(str(metaD)))
	resL = asyncio.run(load_mpd_playlist_via_metaD(mpdHandle,host,socket,metaD,mpd_path_preffix))
	logger.debug('createPlayList_viaTrackCRC32L - finished')
	
	if db_init_flag:
		db.close()
	return resL	
	
async def load_mpd_playlist_via_metaD(mpdHandle,host,socket,metaD,mpd_path_preffix,*args):
	logger.debug('in async  load_mpd_playlist_via_metaD- Start: [%s] [%s]'%(str(host),str(socket)))
	#	 Test Scenario
	#client = mpd.MPDClient()
	#client.connect("localhost", 6600)
	#cfgD = myMediaLib_adm.readConfigData(myMediaLib_adm.mymedialib_cfg)
	#dbPath = cfgD['dbPath']
	#db = sqlite3.connect(dbPath)
	
	#
	#DbIdL=myMediaLib_adm.getDbIdL_viaTagId(435,db)
	#metaD = myMediaLib_adm.getCurrentMetaData_fromDB_via_DbIdL(DbIdL,db)
	#r=myMediaLib_adm.load_mpd_playlist_via_metaD(client,metaD,'G:\\MUSIC\\')
	errorLog = []
		
	resL = []
	sortedL = []

	for a in metaD:
		if metaD[a]['cue_num']==None:
			resL.append((metaD[a]['path'],a))
		else:
			resL.append((('%s,%02d'%(metaD[a]['cue_fname'],metaD[a]['cue_num'])),a))
	resL.sort()
	
	sortedL = [a[1] for a in resL]
	#mpdHandle = MPDClient()
	# Not necessary, but should not cause any trouble either
	#mpdHandle.disconnect()
	#try:
	#	mpdHandle.connect(host, socket)
	#except ConnectionError as e: 
	#	errorLog.append((None,e,None))
	#	return {'mpdHandle':mpdHandle,'sorted_crc32L':[],'errorLog':errorLog}
	print("MPD 1")
	ts = time.time()
	try:
		await mpdHandle.connect(host, socket)
	except Exception as e:
		logger.critical('MPD connection Error: in load_mpd_playlist_via_metaD [%s]'%(str(e)))
	print("MPD 2 -connect time:", ts - time.time())    
	
	try:
		await mpdHandle.clear()
	except Exception as e:
		logger.critical('MPD clear: in load_mpd_playlist_via_metaD [%s]'%(str(e)))
		
	
	for key in sortedL:
		if metaD[key]["cue_num"]:
			f = mpd_path_preffix + metaD[key]["cue_fname"]
			
			f=f.replace("\\","/")
			#print("MPD key:",key)
			try:
				await mpdHandle.load(f,metaD[key]["cue_num"]-1)
			except Exception as e:
				logger.critical('MPD connection Error: in load_mpd_playlist_via_metaD [%s]'%(str(e)))
				errorLog.append((f,e,'cue'))
				mpdHandle.disconnect()
			#print('c', end=' ')
		else:
			if "http://" in metaD[key]["path"] or "https://" in metaD[key]["path"]:
				f = metaD[key]["path"]
			else:
				f = mpd_path_preffix + metaD[key]["path"]
			f=f.replace("\\","/")
			#print("MPD add")
			try:
				await mpdHandle.add(f)
				#print('*', end=' ')
			except Exception as e:
				errorLog.append((f,e,'file'))
				mpdHandle.disconnect()
			#print("MPD add fin")	
	try:
		await mpdHandle.play()
	except Exception as e: 
		print("Connection failed:", e)
		mpdHandle.disconnect()
	print("mpd load finita")	
	mpdHandle.disconnect()	
	print("mpd load finita -connect time+load:", ts - time.time())    
	logger.info('in async  load_mpd_playlist_via_metaD- finish')
	return {'mpdHandle':mpdHandle,'sorted_crc32L':sortedL,'errorLog':errorLog}
	
	
async def load_mpd_playlist_via_pathL(mpdHandle,host,socket,pathTupelL, isCue,*args):
	# upload mpd playlist via path tupels where 1-st elem is path (cue or media file) 2-nd is track numbet in CUE file
	# asume that path list is mpd ready and has right sorting order
	#	 Test Scenario
	#client = mpd.MPDClient()
	#client.connect("localhost", 6600)
	#cfgD = myMediaLib_adm.readConfigData(myMediaLib_adm.mymedialib_cfg)
	logger.debug('in load_mpd_playlist_via_pathL[%s] - Start'%(str(len(pathTupelL))))
	errorLog = []
	try:
		await mpdHandle.connect(host, socket)
	except Exception as e:
		logger.critical('MPD connection Error: in load_mpd_playlist_via_pathL [%s]'%(str(e)))
	   
	
	try:
		await mpdHandle.clear()
	except Exception as e:
		logger.critical('MPD clear: in load_mpd_playlist_via_pathL [%s]'%(str(e)))
		
	
	for track_item in pathTupelL:
		if isCue:
			try:
				await mpdHandle.load(track_item[0],track_item[1])
			except Exception as e:
				mpdHandle.disconnect()
				logger.critical('MPD connection Error: in load_mpd_playlist_via_pathL [%s]'%(str(e)))
				errorLog.append((track_item,e,'cue'))
		else:

			try:
				print([track_item],len(track_item))
				await mpdHandle.add(track_item[0])
				#print('*', end=' ')
			except Exception as e:
				mpdHandle.disconnect()
				logger.critical('MPD connection Error: in load_mpd_playlist_via_pathL [%s]'%(str(e)))
				errorLog.append(((track_item,e,'Notcue')),e,'file')
	try:
		await mpdHandle.play()
	except Exception as e: 
		print("Connection failed:", e)
		mpdHandle.disconnect()
	print("mpd load finita")	
	mpdHandle.disconnect()				
	
	logger.debug('in load_mpd_playlist_via_pathL - Finished')
	
	return {'mpdHandle':'','errorLog':errorLog}

async def check_update_mpd_db(mpdHandle,mpd_host,mpd_socket,uri_check_node_folder,uri_file):
	logger.debug('in check_update_mpd_db- Start')
	#get folder URI
	uri_folder = ''
	isInMpdDb = False

	isFolderInMpdDb = False
	
	try:
		await mpdHandle.connect(mpd_host, mpd_socket)
	except Exception as e:
		logger.critical('MPD connection Error: in check_update_mpd_db [%s]'%(str(e)))
  

	# check file exists
	try:
		resL = await mpdHandle.find('file',uri_file)
	except  mpd.base.ConnectionError as e:
		logger.critical('MPD  Error: in check_update_mpd_db find [%s]'%(str(e)))

	for a in resL:
		if a['file'] == uri_file:
			isInMpdDb = True
			logger.debug('in check_update_mpd_db - Found OK Finished')
			return isInMpdDb

	uri_folder = os.path.dirname(uri_file)

	while uri_folder != '' and uri_folder != uri_check_node_folder and not isFolderInMpdDb:
		uri_folder = os.path.dirname(uri_folder)

		try:
			resL= await mpdHandle.find('base',uri_folder)
		except  mpd.base.CommandError as e:
			if 'No such directory' in str(e):
				print('No such directory')
				uri_folder = os.path.dirname(uri_folder)
				continue

		for a in resL:
			if uri_folder in a['file']:
				isFolderInMpdDb = True
				break
		if isFolderInMpdDb:
			break
	#print(uri_folder)
	try:
		res = await mpdHandle.update(uri_folder)
	except  mpd.base.CommandError as e:
		logger.critical('MPD  Error: in check_update_mpd_db update [%s]'%(str(e)))
	try:	
		status_mpd = await mpdHandle.status()
	except  mpd.base.CommandError as e:
		logger.critical('MPD  Error: in check_update_mpd_db status [%s]'%(str(e)))	
		
	while 'updating_db' in status_mpd:
		print(status_mpd['updating_db'])
		time.sleep(3)
		try:	
			status_mpd = await mpdHandle.status()
		except  mpd.base.CommandError as e:
			logger.critical('MPD  Error: in check_update_mpd_db status [%s]'%(str(e)))	
		
	logger.debug('in check_update_mpd_db - Updating MPD DB')
	#check existence
	try:
		resL = await mpdHandle.find('file',uri_file)
		if resL == []:
			print('Not in DB after update')
			print(type(uri_file))
			logger.critical('in check_update_mpd_db - Not in db after update 1')
			logger.critical(uri_file)
			mpdHandle.disconnect()	
			return isInMpdDb
			
	except  mpd.base.CommandError as e:
		print(str(e))
		logger.debug('in check_update_mpd_db - Error [%s]'%(str(e)))
		mpdHandle.disconnect()	
		return isInMpdDb


	for a in resL:
		if a['file'] == uri_file:
			isInMpdDb = True
			logger.debug('in check_update_mpd_db - In db after update - OK Finished')
			mpdHandle.disconnect()	
			return isInMpdDb
	
	logger.debug('in check_update_mpd_db - Finished [%s]'%str(isInMpdDb))
	print('Finished with ', str(isInMpdDb))
	return isInMpdDb
	
async def get_mpd_status(mpd_client,host,socket):
	try:
		await mpd_client.connect(host, socket)
	except Exception as e:
		logger.critical('MPD connection Error: in get_mpd_status [%s]'%(str(e)))
	
	mpd_status = {}
	try:	
		mpd_status = await mpd_client.status()
		print("mpd_status=",mpd_status)
	except Exception as e:
		logger.critical('Error: in get_mpd_status')
		mpd_client.disconnect()	
		
	mpd_client.disconnect()	
	return mpd_status
	
async def get_mpd_playlistinfo(mpd_client,host,socket,track_list_num):	
	try:
		await mpd_client.connect(host, socket)
	except Exception as e:
		logger.critical('MPD connection Error: in get_mpd_playlistinfo [%s]'%(str(e)))
	track_info = []	
	try:	
		track_info= await mpd_client.playlistinfo(track_list_num)
	except Exception as e: 
		logger.critical('MPD error: in get_mpd_playlistinfo [%s]'%(str(e)))
		mpd_client.disconnect()	
		return []
	mpd_client.disconnect()		
	return track_info	