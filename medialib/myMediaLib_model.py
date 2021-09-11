# # -*- coding: cp1251 -*-
#-*- coding: utf-8 -*-
#import  wx

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer


import logging
from PIL import Image
import json

#import winamp                      
import os
import codecs
import socket
from os import curdir, sep,getcwd
import re
import shutil
from mutagen.apev2 import APEv2, error
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.monkeysaudio import MonkeysAudioInfo
#from rss_processing_adm import urlopenWithCheck
from bs4 import BeautifulStoneSoup
import base64

from myMediaLib_init import readConfigData
from myMediaLib_init import loadTemplates_viaCFG
from myMediaLib_init import loadCommandRouting

from myMediaLib_adm import  getPlaylistsfromXML                 
from myMediaLib_adm import  getPlaylistGroupRelDic


import myMediaLib_adm
from myMediaLib_adm import getMedialibDb_Indexes
from myMediaLib_adm import createPlayList_fromMetaDataD
from myMediaLib_adm import Tag_Assignement_and_save
from myMediaLib_adm import getCurrentMetaData_fromDB_via_pL_pos
from myMediaLib_adm import getCurrentMetaData_fromDB_via_DbIdL
from myMediaLib_adm import getDbIdL_w_folderL_filter
from myMediaLib_adm import get_all_artists_in_metaD
from myMediaLib_adm import createPlayList_viaTagId
from myMediaLib_adm import createPlayList_viaAlbumCRC32
from myMediaLib_adm import createPlayList_viaArtistCRC32
from myMediaLib_adm import createNewTag_inDB
from myMediaLib_adm import getTrackList
from myMediaLib_adm import getCurrentMetaData_fromDB_via_CRC32L
from myMediaLib_adm import searchMediaLib_MetaData
from myMediaLib_adm import saveArtistD_intoDB
from myMediaLib_adm import getAll_Main_Artist_fromDB
from myMediaLib_adm import getMedialibAlbum_Indexes
from myMediaLib_adm import getVirtualAlbum_Indexes
from myMediaLib_adm import getAlbumD_fromDB

import mutagen
import pickle
import time
import zlib
import datetime
import sqlite3

logger = logging.getLogger('controller_logger.Model')
from myMediaLib_CONST import mymedialib_cfg

import http.server

def new_address_string(self):
	host, port = self.client_address[:2]
	return '%s (no getfqdn)' % host #used to call: socket.getfqdn(host)


class MediaLibPlayProcess_singletone(object):
	obj = None
	def __new__(cls,*dt,**mp):           # класса Singleton.
		if cls.obj is None:               # Если он еще не создан, то
			logger.info( "Singltone created" )
			cls.obj = object.__new__(cls,*dt,**mp) # вызовем __new__ родительского класса
		
		return cls.obj
	def __init__(self):
		try:
			if self.__instance_num > 0:
				self.__instance_num = self.__instance_num + 1
				logger.info( "Singltone link OK, link number:%d"%self.__instance_num)	
				return None
		except:	
			self.__instance_num = 0
			print('Ready to initialize the MediaLibPlayProcess_singletone')
			logger.info('in initialize singltone - START - OK')
			pass
		
		# Читаем конфигурация общей настройки системы
		print("Reading configuration from [%s] ...."%(mymedialib_cfg))
		self.__configDict = readConfigData(mymedialib_cfg)		
		port = int(self.__configDict['player_cntrl_port'])
		
		dbl_appl = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(str(port)))	
		try:
			res=dbl_appl.appl_status()['dbPath']
			print("Player server already running -> no copy allowed")
			print("Wait 5 sec for exit...[%s]"%(str(res)))
			time.sleep(5)

			return
		except:
			pass
		
		
		self.__winampext = ''
		self.__playlistpath = ''
		self.__mediaPath = ''
		self.__listName = ''
		self.__curList_crc32 = 0
		
		self.__songNum = 0
		self.__albumNum = 0
		self.__album_order_numb = 0
		self.__album_path = ''
		self.__pD = None
		self.__pD_crc32 = {}
		self.__prev_entry = None
		self.__cur_entry = None
		self.__stop_flag = ''
		self.__manual_stop_flag = False
		self.__group2PlayListD = None
		self.__playlistGroup = 'ALL_GRP'
		self.__mlXMLPath = ''
		self.__winampObj = None
		self.__DaemonRef = None
		self.__HistoryL = []
		self.__FavoritL = []
		self.__cover_page_obj = ''
		self.__controlPicD = {}
		self.__Cash_D = {}
		
		self.__CastPlayList = {}
		self.__CastPlayList[1] = {'cur_track_id':'','player_status':'','metaD':{},'castL':[],'crc32L':[]}
		self.__PlayListL = []
		self.__PlayList_asCRC32_L = []
		self.__metaD_of_cur_pL = {}
		self.__DB_metaIndxD = {}
		
		self.__myMediaLibPath = ''
		self.__dbPath = ''
		self.__SearchBuf_D = {}
		self.__mlFolderTreeAllBuf_D = {}
		self.__setAutoComplSearchBuf_D = {}
		self.__tracksPreloadRes_D = {}
		self.__SearchEditBuf_D = {}
		self.__Tmpl_D = {}
		self.__TagD = {}
		self.__PlayerControl = None
		self.__CurrentPlayerInstance = {'host':'','socket':'','remote_host':''}
		self.__RemHPlayerInstanceD = {}
		self.__PlayerInstanceL = []
		self.__isPlayerAlive = False
		self.__SearchListMetaD = None
		self.__PlayListQueueD = {}
		self.__PlayListQueue = []
		self.__Temp_MemCRC32_PlayList = []
		self.__commandRoutingDic = {}
		self.__DB_metaIndxD_album = {}
		self.__mpdMusicPathPrefix = ''
		
		
		# может стоит убрать общий буфер метаданных
		self.__All_metaD = {'search_key':'nonkey','resD':{}}
		self.__ReportBufD = {}
		# Список из таблицы артист только главные артисты
		self.__ArtistL = []
		# список и
		self.__Artist_metaBufL = []
		
		self.__genKeyListD = {}
		
		if 'mpd_host_list' in self.__configDict:
			self.__CurrentPlayerInstance['host'] = self.__configDict['mpd_host_list'][0]['host']
			self.__CurrentPlayerInstance['socket'] = self.__configDict['mpd_host_list'][0]['socket']
			self.__PlayerInstanceL = self.__configDict['mpd_host_list']
			self.__mpdMusicPathPrefix = self.__configDict['mpdMusicPathPrefix']
		
		self.__myMediaLibPath = self.__configDict['applicationPath']
		self.__dbPath = self.__configDict['dbPath']
		# читаем схему маршрутизации
		if 'commandRouting' in self.__configDict:
			print("Getting CommandRouting schema...")
			self.__commandRoutingDic = loadCommandRouting(self.__configDict['commandRouting'])
		
		# Строим список главных артистов
		print("Reading DB ...")
		db = sqlite3.connect(self.__dbPath)
		#db.text_factory = str
		
		main_artL = getAll_Main_Artist_fromDB(db)
		self.__ArtistL = [(a[1],a[0]) for a in main_artL]
		self.__ArtistL.sort()
		self.setSearchBufD('Search_text',{},None,'initial',{})
		# Загрузка индексов Бд
		
		self.__DB_metaIndxD = getMedialibDb_Indexes(db,'ignoring')
		
		self.__DB_metaIndxD_obratn = {}
		for a in self.__DB_metaIndxD:
			self.__DB_metaIndxD_obratn[self.__DB_metaIndxD[a][0]] = a
		
		self.__DB_metaIndxD_album = getMedialibAlbum_Indexes(self.__DB_metaIndxD,db)
		
		self.__DB_virtual_albumD = getVirtualAlbum_Indexes(db)
		
		# Загрузка шаблонов доморошенных
		#loadTemplates(self.__Tmpl_D,'info')
		#loadTemplates(self.__Tmpl_D,'scrpt_1.search')
		
		# Загрузка тэгов созданных вручную
		c = db.cursor()
		#db.text_factory = str
		c.execute("select * from tag")
		l =  c.fetchall()
		for a in l:
			self.__TagD[a[0]]={'tag_name':a[1],'tag_descr':a[2],'tag_type':a[3]}
		
		# Загрузка картинки "Нет  Изображения"
		self.__no_cover_page_obj_path = self.__myMediaLibPath +"images/no-image-available_110x110.jpg"
		try:
			fileObj = open(self.__no_cover_page_obj_path,"rb") 
			self.__no_cover_page_obj = fileObj.read()
			fileObj.close()
		except IOError as e:
			print('IoError',e)
			self.__no_cover_page_obj = None
		
		# Загрузка стандартных кнопок упрвления плеером
		
		for a in ['prev','next','play','stop','pause']:
			try:
				
				fileObj = open(self.__myMediaLibPath +"images/%s.jpg"%(a,),"rb")
				self.__controlPicD[a] = fileObj.read()
				fileObj.close()
			except IOError as e:
				print('IoError',e)
				self.__controlPicD[a] = None
				
		
			
		try:
			f = open(self.__myMediaLibPath+'\\medialibFavor.dat','r')
			self.__FavoritL = pickle.load(f)
			f.close()
		except:
			print('Favorites  not found')
		
		try:
			f = open(self.__myMediaLibPath+'\\medialibHist.dat','r')
			self.__HistoryL = pickle.load(f)
			f.close()
		except:
			print('history  not found')
				
		#configDict = {'mediaPath':'','winampext':'','player_cntrl_port':0,,'appl_cntrl_port':0}	
		
		
		
		
		
		self.__playlistpath = self.__configDict['mediaPath']
		
		#playList = winamp.getTrackList(playlistpath+'winamp.m3u')
		self.__mlXMLPath = self.__configDict['mediaPath']+'Plugins\\ml\\playlists.xml'
		#print 'mlXMLPath=',self.__mlXMLPath 
		self.__pD = getPlaylistsfromXML(self.__mlXMLPath)
		
		# Этот словарь нужен для вывода при поиске связанной с треком инфы по плейлистам в которые он входит
		#self.__listsMetaData=getMyMediaLib_ListsData(self.__pD,self.__configDict['mediaPath']+"Plugins\\ml\\")
		self.__listsMetaData = {}
		
		self.__mediaPath = self.__configDict['mediaPath']+"Plugins\\ml\\"
		
		# формируем актуальные контрольные суммы листов	
		pDkeyL = list(self.__pD.keys())
		for a in pDkeyL:
			curPlayList =  getTrackList(self.__configDict['mediaPath']+"Plugins\\ml\\"+a)
			self.__pD[a]['crc32'] = zlib.crc32(str(curPlayList))
			
			
		#Берем последний сгенерированный лист и делаем думми подмену для последнего игранного листа
		pLS =getTrackList(self.__configDict['mediaPath']+'winamp.'+self.__configDict['winampext'])
		checkCrc32 = zlib.crc32(str(pLS).encode('utf-8'))
		pd_crc32_keyL = [self.__pD[a]['crc32'] for a in self.__pD]
		
		if checkCrc32 in pd_crc32_keyL:
			checkCrc32 = 1234567
		self.__pD['search_play.m3u'] = {'title':'Last played list','filename':'search_play.m3u','crc32': checkCrc32, 'id': '{000}', 'songs': str(len(pLS))} 
		self.__pD['tag_play.m3u'] = {'title':'Last played list','filename':'tag_play.m3u','crc32': checkCrc32, 'id': '{000}', 'songs': str(len(pLS))} 	
		
		# Берем буффер связи групп и листов
		self.__group2PlayListD = getPlaylistGroupRelDic(db)
		db.close()
		host = socket.gethostbyname(socket.gethostname())
		#host = socket.gethostname()
		#if host.find('192.168.2.9') >= 0:
		print('we are at host ip: ',host, ' domain:',socket.gethostname())
		#	winampext_ = 'm3u8'
		#else:
		self.__winampext = self.__configDict['winampext']
		winampext_ =  self.__configDict['winampext']
		print('Starting RPC ...')		
		self.__PlayerControl = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(port))
		
		#print 'check -5'	
		l_data = []	
		try:
			l_data = zlib.decompress(self.__PlayerControl.get_cur_pl_as_list().data)
			self.__isPlayerAlive = True
		except socket.error as e:	
			print('\n'*3)
			print('Player RPC Server is not available '+str(e))
			print("Wait 5 sec for exit........")
			#time.sleep(5)

			#os._exit(0)
			#return
		except Exception as e:
			logger.critical('Error: in initialize self.__PlayerControl.get_cur_pl_as_list %s'%(str(e)))
			return	
		#print 'check -4'		
		
		PlayControl_CurStatusD = {'pl_pos':0,'playBack_Mode':1}
		if self.__isPlayerAlive:
			PlayControl_CurStatusD = self.__PlayerControl.get_status()
		
			
		print('check -3.9-->',PlayControl_CurStatusD)
		
		if self.__isPlayerAlive:
			self.__songNum = PlayControl_CurStatusD['pl_pos']
		
		#print 'check -3.8'
			self.__stop_flag = PlayControl_CurStatusD['playBack_Mode']
		#print 'check -3'	
		
			try:	
				self.__PlayListL = 	pickle.loads(l_data)
			except Exception as e:
				logger.critical('Error: in initialize NO PLAYER pleylist %s'%(str(e)))		
		
		#print 'check -2'		
			a_t_numD= self.get_current_album_track_num()
			if a_t_numD != None:
				self.__songNum = a_t_numD['songNum']
				self.__albumNum = a_t_numD['albumNum']
		#print 'a_t_numD -------->',a_t_numD	
		
		#print 'check -1'		
		
			try:
				self.__PlayList_asCRC32_L = [zlib.crc32(a.encode('raw_unicode_escape')) for a in self.__PlayListL]	
			except Exception as e:
				logger.critical('Error: in MediaLibPlayProcess_singletone conctructor %s'%(str(e)))
			
		
		#print 'check 0'	
		
			DbIdL = [self.__DB_metaIndxD[a][0] for a in self.__PlayList_asCRC32_L if a in self.__DB_metaIndxD]
		
		
		#print 'DbIdL',DbIdL
		
			print('check 1')
		
			self.__metaD_of_cur_pL =getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None)
			for a in self.__metaD_of_cur_pL:
				format = self.__metaD_of_cur_pL[a]['path'][self.__metaD_of_cur_pL[a]['path'].rfind('.')+1:]
				if self.__metaD_of_cur_pL[a]['cue_num'] != None:
				  format = format + ' cue'	
				self.__metaD_of_cur_pL[a]['format']   = format	
		
		#self.__PlayListL = self.getCurPlayListAsList()
		
		#print 'check 2'
			checkCrc32 = zlib.crc32(bytes(self.__PlayListL))
			self.__curList_crc32 = checkCrc32
		
		#print 'check 3'
		# актуализирвать путь к текущему альбому
			r = self.check_updadeCoverPage_change_state()
		#checkCrc32 = zlib.crc32(str(winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_)))
			curListName = ''
		#print 'check 4'
			for a in self.__pD:
				
				if self.__pD[a]['crc32'] == checkCrc32:
					curListName = self.__pD[a]['filename']
				
		#curListName =  findCorrespond_Ml_List(self.__playlistpath,self.__pD,winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_))
		#print 'check 5'
			if curListName != None and curListName != '':
		
				self.setplayList(str(curListName))
				
				
				for a in pDkeyL:
					self.__pD_crc32[self.__pD[a]['crc32']] = self.__pD[a]	
			else:
				print('\n'*3, 'Error --> no correspondent playlist found-2:',self.__configDict['mediaPath']+'winamp.'+self.__configDict['winampext'])
	#def getPlayListDic(self):
		#	return self.__pD
		
		# Грузим шаблоны
		# При инициализации грузится первая по списку система шаблонов, затем можно выбрать другую
		print('before templates load')
		for a in self.__configDict['templatesD']:
			if  self.__configDict['templatesD'][a]['active'] == True:
				path = self.__configDict['templatesD'][a]['templatesPath']
				
				logger.debug('in initialize loadtemplates %s'%path)
				
				self.__Tmpl_D  = loadTemplates_viaCFG(path)
		print('after templates load')		
			
		
		# Что бы предотвратить повторные инициализации
		self.__instance_num = self.__instance_num + 1
		
		#print self.__Tmpl_D
		

		

	def runApplServer(self):
		
		port = int(self.__configDict['appl_cntrl_port'])
		print('Appla port',port)
		server = SimpleXMLRPCServer(("127.0.0.1", port),allow_none = True)
		print("Listening on port %s..."%(str(port)))
		print('\n*3  avalable transit methods for player:',str(self.__PlayerControl.system.listMethods()))
		time.sleep(3)
		server.register_introspection_functions()
		server.register_function(self.getMediaLibPlayProcessContext, "appl_status")
		server.register_function(self.MediaLibPlayProcessDic_viaKey,"processDic_viaKey")
		server.register_function(self.PageGenerator,'page_generator')
		server.register_function(self.RefreshServerContent,'refresh_content')
		server.register_function(self.Appl_Controller,'appl_control')
		server.register_function(self.getCoverPageObj,'get_image')
		server.register_function(self.getConrolPicD,'get_control_pics')
		server.register_function(self.debug_get_controllist_for_main,'debug_get_controllist_for_main')
		server.serve_forever()	
	
	def getCurAlbumDir(self):
		file_name = pickle.loads(self.__PlayerControl.get_cur_track().data)
		print('file_name',file_name)
		
		path = ""
		trackL = []
		albumCRC32 = None
		
		# Check that Folder name is not empty, actually check RADIO option
		
		pos = file_name.rfind("\\")
		
		path = file_name[:pos+1]
		
		print("Path:",path)
		
		if not os.path.exists(path):
			# Calculate current playing track CRC32
			path_CRC32 = zlib.crc32(file_name.encode('raw_unicode_escape'))
			
			try:
				trackL=getCurrentMetaData_fromDB_via_CRC32L(self.__dbPath,[path_CRC32],None)[0]
			except:
				print('Error at 399 in getCurAlbumDir with album meta get')
			
			albumCRC32 = trackL[5]
			#print 'goga',path_CRC32,trackL,albumCRC32
			if albumCRC32:
				albumD=getAlbumD_fromDB(self.__dbPath,None,albumCRC32,[],'wo_reflist')
				print(albumD['albumD'])
				if albumD['albumD'][albumCRC32]['object_type'].lower() == 'radio':
					path = albumD['albumD'][albumCRC32]['path']
		
		#print 'PPPPPATH:',path	
		
		return path
		
	def setCurPlayerInstance(self,host,param_socket,remote_host):
		# socket.getfqdn('fe80::f90f:f996:8c36:f67c') --> 'OKA-MUSIC'
		self.__CurrentPlayerInstance['host']=host
		self.__CurrentPlayerInstance['socket']=param_socket
		self.__CurrentPlayerInstance['remote_host']=remote_host
		for item in self.__PlayerInstanceL:
			if  item['host'] == host:
				item['remote_host'] = remote_host
		logger.debug('in setCurPlayerInstance before socket.getfqdn, remote_host=[%s]'%(str(remote_host)))			
		try:
			self.__RemHPlayerInstanceD[remote_host] = {'host':host,'socket':param_socket,'remote_host_name':remote_host}
		except Exception as e:
			logger.critical('Error in setCurPlayerInstance [%s] '%(str(e)))	
			self.__RemHPlayerInstanceD[remote_host] = {'host':host,'socket':param_socket,'remote_host_name':'not determined'}
		logger.debug('in setCurPlayerInstance after socket.getfqdn')				
		return
		
	def getCurPlayerInstance(self,remote_host):
		if remote_host not in self.__RemHPlayerInstanceD:
			return self.__PlayerInstanceL[0]
		else:	
			return self.__RemHPlayerInstanceD[remote_host]
	
	def getRemHPlayerInstanceD(self):
		return self.__RemHPlayerInstanceD	
		
	def getPlayerInstanceList(self):
		return self.__PlayerInstanceL	
		
	def get_player_control_handler(self):
		return self.__PlayerControl
	def isPlayerAlive(self):
		if self.__isPlayerAlive:
			return True	
		else:
			return False	
	def do_play(self):
		pc = self.__PlayerControl.play()
		self.__manual_stop_flag	= False
		return pc
		
	def Appl_Controller(self,page_key,commandD):
		pc = None
		listType = listDescr = ''
	# Контроллер приложения, тут обрабатываются все команды со всех форм и страниц, тут же происходит проверка изменения листов и пергрузка их метаданных
		print("----------We are at old Appl_Controller--->",commandD)
						
		# if 'do_search'  == commandD['page_mode']:
			# search_term = commandD['search_term']
			# sD =  myMediaLib_adm.searchMediaLib_MetaData(search_term,[],self.__listsMetaData)
			# print len(sD)
			# if 'tagadmin' in commandD['page']:  # перенесено в контроллер MVC
				#эта функция пермещена в новый обработчик
				#self.setSearchBufD(search_term,sD,self.getSearchBufD()['tag_id'],self.getSearchBufD()['tag_form_mode'])
				# pass
			# else:
				# self.setSearchBufD(search_term,sD,None,None)
			# return 1
	
		return pc
		
	def RefreshServerContent(self,content_key,PlayControl_CurStatusD,*args):
		logger.info('in RefreshServerContent - START - OK')
		keyL = ['load_templates','play_list_sync','refresh_server','refresh_dbid','refresh_config','refresh_routing']
		if content_key in keyL:
			
			if content_key == 'load_templates':
				logger.debug('in RefreshServerContent - in [%s] 450 Start - OK'%(str(content_key)))
				tmpl_key = args[0]
				
				for a in self.__configDict['templatesD']:
					self.__configDict['templatesD'][a]['active'] = False
					
				
				# Load template profiles from CFG 
				path = self.__myMediaLibPath+'\\templates\\templates.cfg'
				logger.debug('in RefreshServerContent - load_templates with path:%s'%path)	
				self.__Tmpl_D  = loadTemplates_viaCFG(path)
				
				# Select active Template profile 
				self.__configDict['templatesD'][tmpl_key]['active'] = True
				
				
				
				
				logger.debug('in RefreshServerContent - load_template FINISH - OK')
				return 1
				
			elif content_key == 'refresh_config':
				logger.debug('in RefreshServerContent - in [%s] 476 Start - OK'%(str(content_key)))
				self.__configDict = readConfigData(mymedialib_cfg)
				print('Refreshing the base config:',mymedialib_cfg)
				for a in self.__configDict:
					print(a,'=',self.__configDict[a])
				logger.debug('in RefreshServerContent - refresh_config FINISH - OK')	
				return 1	
				
			elif content_key == 'refresh_routing':
				logger.debug('in RefreshServerContent - in [%s] 486 Start - OK'%(str(content_key)))
				# читаем схему маршрутизации
				if 'commandRouting' in self.__configDict:
					self.__commandRoutingDic = loadCommandRouting(self.__configDict['commandRouting'])	
					print('commandRoutingDic=',	list(self.__commandRoutingDic.keys()),'OK')
				logger.debug('in RefreshServerContent - in [%s]  FINISHED - OK'%(str(content_key)))
				return 1		
				
			elif content_key == 'refresh_dbid':
				logger.debug('in RefreshServerContent - in [%s] 494 Start - OK'%(str(content_key)))
				# загрузка главных артистов
				db = sqlite3.connect(self.__dbPath)
				main_artL = getAll_Main_Artist_fromDB(db)
				self.__ArtistL = [(a[1],a[0]) for a in main_artL]
				self.__ArtistL.sort()
				
				
				self.__DB_metaIndxD = getMedialibDb_Indexes(db,'ignoring')
				
				for a in self.__DB_metaIndxD:
					self.__DB_metaIndxD_obratn[self.__DB_metaIndxD[a][0]] = a
				
				self.__DB_metaIndxD_album = getMedialibAlbum_Indexes(self.__DB_metaIndxD,db)
				self.__DB_virtual_albumD = getVirtualAlbum_Indexes(db)
				
				# Загрузка тэгов созданных вручную
				c = db.cursor()
				c.execute("select * from tag")
				l =  c.fetchall()
				c.close()
				db.close()
				for a in l:
					self.__TagD[a[0]]={'tag_name':a[1],'tag_descr':a[2],'tag_type':a[3]}
				
				logger.debug('in RefreshServerContent - in [%s] and indexes FINISHED - OK'%(str(content_key)))
				#print 'self.__TagD.keys()=',self.__TagD.keys()
				return 1	
			elif content_key == 'play_list_sync':
				logger.debug('in RefreshServerContent - in [%s] 522 Start - OK'%(str(content_key)))
				# Вначале проверяем не находяться ли метаданные по листам уже в очереди листов если да то просто переназначить 
				# текущий контекст данными из очереди, иначе взять данные из БД
				#self.__PlayListQueueD[pL_CRC32] = {'listType':listType,'PlayListL':DbIdL,'metaD':{},'listDescr':listDescr,'cur_pos':0}
				
				self.__songNum = PlayControl_CurStatusD['pl_pos']
				self.__stop_flag = PlayControl_CurStatusD['playBack_Mode']
				
				
				# Получаем  содержимое листа от контроллера плеера
				l_data = zlib.decompress(self.__PlayerControl.get_cur_pl_as_list().data)
				self.__PlayListL = 	pickle.loads(l_data)
				# Генерируем его содержимое как crc32L
				if self.__curList_crc32 != PlayControl_CurStatusD['pL_CRC32']:
					self.__curList_crc32 = PlayControl_CurStatusD['pL_CRC32']
					try:
						self.__PlayList_asCRC32_L = [zlib.crc32(a.encode('raw_unicode_escape')) for a in self.__PlayListL]	
					except Exception as e:
						logger.critical('Error: in MediaLibPlayProcess_singletone RefreshServerContent-play_list_sync %s'%(str(e)))	
					

						
					print('In refreshing',self.__curList_crc32,list(self.__PlayListQueueD.keys()))
					if self.__curList_crc32 in self.__PlayListQueueD:
						if self.__PlayListQueueD[self.__curList_crc32]['metaD'] != {}:
							self.__metaD_of_cur_pL = self.__PlayListQueueD[self.__curList_crc32]['metaD']
							print('Got metaD from buffer')
							return 1
					# Тк. данные не обнаружены в очереди то взять из из БД
						
					
					# Сохраняем его CRC32 ключ	
					#PlayControl_CurStatusD = self.__PlayerControl.get_status()
					
					
					#Получаем все метаданные по нему
					DbIdL = [self.__DB_metaIndxD[a][0] for a in self.__PlayList_asCRC32_L if a in self.__DB_metaIndxD]
					
					self.__metaD_of_cur_pL =getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None)
					for a in self.__metaD_of_cur_pL:
						format = self.__metaD_of_cur_pL[a]['path'][self.__metaD_of_cur_pL[a]['path'].rfind('.')+1:]
						if self.__metaD_of_cur_pL[a]['cue_num'] != None:
						  format = format + ' cue'	
						self.__metaD_of_cur_pL[a]['format']   = format	
					#self.__PlayListL = self.getCurPlayListAsList()	
					
					logger.debug('in RefreshServerContent - in [%s]  FINISHED - OK'%(str(content_key)))
					return 1
			elif content_key == 'refresh_server':	
				logger.debug('in RefreshServerContent - in [%s] 570 Start - OK'%(str(content_key)))
				self.setSearchBufD('Search_text',{},None,None,{})
				# Загрузка индексов Бд
				print("DB index  loading... ")	
				db = sqlite3.connect(self.__dbPath)
				self.__DB_metaIndxD = getMedialibDb_Indexes(db,'ignoring')
				
				self.__DB_metaIndxD_album = getMedialibAlbum_Indexes(self.__DB_metaIndxD,db)
				self.__DB_virtual_albumD = getVirtualAlbum_Indexes(db)
				for a in self.__DB_metaIndxD:
					self.__DB_metaIndxD_obratn[self.__DB_metaIndxD[a][0]] = a
				
				self.__All_metaD = {'search_key':'nonkey','resD':{}}
				self.__ReportBufD = {}
				
				# Загрузка шаблонов доморошенных
				#loadTemplates(self.__Tmpl_D,'info')
				#loadTemplates(self.__Tmpl_D,'scrpt_1.search')
				
				# Загрузка тэгов созданных вручную
				print("Tags loading... ")	
				c = db.cursor()
				c.execute("select * from tag")
				l =  c.fetchall()
				for a in l:
					self.__TagD[a[0]]={'tag_name':a[1],'tag_descr':a[2],'tag_type':a[3]}
					
				
				
				# Загрузка картинки "Нет  Изображения"
				try:	
					self.__no_cover_page_obj_path = self.__myMediaLibPath + "images/no-image-available_110x110.jpg"
					fileObj = open(self.__no_cover_page_obj_path,"rb") 
					self.__no_cover_page_obj = fileObj.read()
					fileObj.close()
				except IOError as e:
					print('IoError',e)
					self.__no_cover_page_obj = None
				
				# Загрузка стандартных кнопок упрвления плеером
				print("Buttons loading...")
				for a in ['prev','next','play','stop','pause']:
					try:
						fileObj = open(self.__myMediaLibPath+"\\images\\%s.jpg"%(a,),"rb")
						self.__controlPicD[a] = fileObj.read()
						fileObj.close()
						
					except IOError as e:
						print('IoError',e)
						self.__controlPicD[a] = None
						
				
					
				try:
					f = open(self.__myMediaLibPath+'\\medialibFavor.dat','r')
					self.__FavoritL = pickle.load(f)
					f.close()
				except:
					print('Favorites  not found')
				
				try:
					f = open(self.__myMediaLibPath+'\\medialibHist.dat','r')
					self.__HistoryL = pickle.load(f)
					f.close()
				except:
					print('history  not found')
						
				#configDict = {'mediaPath':'','winampext':'','player_cntrl_port':0,,'appl_cntrl_port':0}	
				
				self.__configDict = readConfigData(mymedialib_cfg)			
				
				self.__playlistpath = self.__configDict['mediaPath']
				
				#playList = winamp.getTrackList(playlistpath+'winamp.m3u')
				self.__mlXMLPath = self.__configDict['mediaPath']+'Plugins\\ml\\playlists.xml'
				#print 'mlXMLPath=',self.__mlXMLPath 
				print("Winamp lists loading... ")	
				self.__pD = getPlaylistsfromXML(self.__mlXMLPath)
				
				print("Winamp lists metadata loading... ")	
				# Этот словарь нужен для вывода при поиске связанной с треком инфы по плейлистам в которые он входит
				self.__listsMetaData=getMyMediaLib_ListsData(self.__pD,self.__configDict['mediaPath']+"Plugins\\ml\\")
				print('OK')
				
				self.__mediaPath = self.__configDict['mediaPath']+"Plugins\\ml\\"
				
				# формируем актуальные контрольные суммы листов	
				pDkeyL = list(self.__pD.keys())
				for a in pDkeyL:
					curPlayList =  getTrackList(self.__configDict['mediaPath']+"Plugins\\ml\\"+a)
					self.__pD[a]['crc32'] = zlib.crc32(str(curPlayList))
					
					
				#Берем последний сгенерированный лист и делаем думми подмену для последнего игранного листа
				pLS =getTrackList(self.__configDict['mediaPath']+'winamp.'+self.__configDict['winampext'])
				checkCrc32 = zlib.crc32(str(pLS))
				pd_crc32_keyL = [self.__pD[a]['crc32'] for a in self.__pD]
				
				if checkCrc32 in pd_crc32_keyL:
					checkCrc32 = 1234567
				self.__pD['search_play.m3u'] = {'title':'Last played list','filename':'search_play.m3u','crc32': checkCrc32, 'id': '{000}', 'songs': str(len(pLS))} 
				self.__pD['tag_play.m3u'] = {'title':'Last played list','filename':'tag_play.m3u','crc32': checkCrc32, 'id': '{000}', 'songs': str(len(pLS))} 	
				
				# Берем буффер связи групп и листов
				self.__group2PlayListD = getPlaylistGroupRelDic(db)
				db.close()
				host = socket.gethostbyname(socket.gethostname())
				host = socket.gethostname()
				#if host.find('192.168.2.9') >= 0:
				print('we are at:',host)
				#	winampext_ = 'm3u8'
				#else:
				self.__winampext = self.__configDict['winampext']
				winampext_ =  self.__configDict['winampext']
						
				port = int(self.__configDict['player_cntrl_port'])
				
				self.__PlayerControl = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(port))
				self.__PlayerControl.refresh_player()
				
				try:
					l_data = zlib.decompress(self.__PlayerControl.get_cur_pl_as_list().data)
				except socket.error as e:	
					print('\n'*3)
					print('Player RPC Server is not available '+str(e))
					print("Wait 5 sec for exit.....")
					time.sleep(5)
					os.exit()
					return	
				PlayControl_CurStatusD = self.__PlayerControl.get_status()
				self.__songNum = PlayControl_CurStatusD['pl_pos']
				self.__stop_flag = PlayControl_CurStatusD['playBack_Mode']
				self.__PlayListL = 	pickle.loads(l_data)
				
						
				try:
					self.__PlayList_asCRC32_L = [zlib.crc32(a.encode('raw_unicode_escape')) for a in self.__PlayListL]	
				except Exception as e:
					logger.critical('Error: in MediaLibPlayProcess_singletone RefreshServerContent-refresh server %s'%(str(e)))	
					
					
				DbIdL = [self.__DB_metaIndxD[a][0] for a in self.__PlayList_asCRC32_L if a in self.__DB_metaIndxD]
				#print 'DbIdL',DbIdL
				self.__metaD_of_cur_pL =getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None)
				for a in self.__metaD_of_cur_pL:
					format = self.__metaD_of_cur_pL[a]['path'][self.__metaD_of_cur_pL[a]['path'].rfind('.')+1:]
					if self.__metaD_of_cur_pL[a]['cue_num'] != None:
					  format = format + ' cue'	
					self.__metaD_of_cur_pL[a]['format']   = format	
				
				#self.__PlayListL = self.getCurPlayListAsList()
				
				checkCrc32 = zlib.crc32(str(self.__PlayListL))
				self.__curList_crc32 = checkCrc32
				#checkCrc32 = zlib.crc32(str(winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_)))
				curListName = ''
				for a in self.__pD:
					
					if self.__pD[a]['crc32'] == checkCrc32:
						curListName = self.__pD[a]['filename']
						
				#curListName =  findCorrespond_Ml_List(self.__playlistpath,self.__pD,winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_))
				if curListName != None and curListName != '':
			
					self.setplayList(str(curListName))
					
					
				for a in pDkeyL:
					self.__pD_crc32[self.__pD[a]['crc32']] = self.__pD[a]	
				else:
					print('\n'*3, 'Error --> no correspondent playlist found-2:',self.__configDict['mediaPath']+'winamp.'+self.__configDict['winampext'])
			#def getPlayListDic(self):
				#	return self.__pD
				
				# Грузим шаблоны
				self.__Tmpl_D  = loadTemplates_viaCFG(self.__myMediaLibPath+'\\templates\\templates.cfg')
				#print self.__Tmpl_D
				
				logger.debug('in RefreshServerContent - in [%s]  FINISHED - OK'%(str(content_key)))
			else:
				pass
				
		else:
			return 'Wrong content key, use:',str(keyL)
	
	def check_updadeCoverPage_change_state(self):
		# Метод проверяет изменился ли путь к альбому проигрываемой месни, если да то актуализировать контрольную сумму и 
		# вернуть 1. если осталось как есть то вернуть 0. используется для принятия решения об обновлении картинки альбома
		try:
			filename = self.__PlayListL[self.__songNum]
		except:
			print('Error in check_updadeCoverPage_change_state--> Empty winamp list',self.__songNum)
			return 0
		path = filename[:filename.rfind('\\')+1]
		if self.__album_path  == path:
			return 0
		else:
			self.__album_path  = path
			return 1
			
	def getConrolPicD(self,picName):
		if picName in self.__controlPicD:
			return xmlrpc.client.Binary(self.__controlPicD[picName])
		
	def getCoverPageObj(self,*args):
		logger.debug( "in *PIC* getCoverPageObj - START: %s"%(str(args)))
		
		filename = ''
		#filename = self.__PlayListL[self.__songNum]
		#path = filename[:filename.rfind('\\')+1]
		id = 0
		#if path == '':
		#	print "path is empty:", args

		logger.debug( "in ****PIC***** getCoverPageObj: %s *** %s"%(str(filename),str(args)))
		cover_path_320 = ''
		cover_path = ''
		
		#cover_path_320 = path+'cover_320.jpg'
		#cover_path_100 = path+'cover_100.jpg'
		#cover_path = path+'cover.jpg'
		
		#print 'Cur image path:1.%s  2.%s  3.%s'%(cover_path,filename,str(self.__songNum))
		image = ''
		#path_prefixL = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audio_files_path_list']
		#path_prefixL = "G:\\SEAGATE\\MUSIC\\"
		path_prefixL = os.path.normpath(self.__configDict['audioFilesPathRoot'])
		print(path_prefixL)
		#"\\\\GOFLEX_HOME\\ExternalUSB\\Seagate\\Music\\"
		if 'search_icon' in args:
			logger.debug( "in **PIC** getCoverPageObj at 'search icon': %s *** "%(str(args)))
			id = int(args[1])
			
			
			#print self.__DB_metaIndxD_album.keys()
			
			if id in self.__DB_metaIndxD_album:
				#print 'id in self.__DB_metaIndxD_album'
				logger.debug( "in  getCoverPageObj at id: %s"%(str(id)))
				path = self.__DB_metaIndxD_album[id]
				logger.debug( "in  getCoverPageObj at path: %s"%(path))
				#print 'path:',path
				if path[-1] != '\\':
					path+='\\'
					
				if path[:1] != '\\':
					path ='\\'+path	
				path = path.replace("\\","/")
				cover_path = path_prefixL+path+'cover.jpg'	
				cover_path_100 = path_prefixL+path+'cover_100.jpg'
				
				logger.debug( "in  getCoverPageObj at cover_path_100: %s"%(cover_path_100))
				#print 'cover_path_100 =',cover_path_100
			else:
				# тут резолвер путей виртуальных альбомов
				# 1. поиск в корневой дирректории одного из связанных альбомов
				logger.debug( "in  getCoverPageObj: 928 Virtual album to be resolved: %s"%(str(id)))
				path_ref_to = self.__DB_virtual_albumD[id]['ref_to_path']
				pos = path_ref_to.rfind('\\')
				path = path_ref_to[:pos]
				path = path.replace("\\","/")
				cover_path_100 = path+'\\cover_100.jpg'
				cover_path = path+'\\cover.jpg'
				#if not os.path.exists(cover_path_100):
				#	cover_path_100 = path_ref_to+'\\cover_100.jpg'
					
				
				if not os.path.exists(cover_path_100):
					if not os.path.exists(cover_path):
						cover_path_100 = path_ref_to+'/cover_100.jpg'
						#print('resolved:',cover_path_100)
						logger.debug( "in  getCoverPageObj: 942 resolved: %s"%(cover_path_100))
					else:
						#print('is meta cover:',cover_path)
						logger.debug( "in  getCoverPageObj: 945 is meta cover: %s"%(cover_path))
				else:
					#print('is meta cover_100:',cover_path_100)
					logger.debug( "in  getCoverPageObj: 948 is meta cover_100: %s"%(cover_path_100))
					
				
				
				
				#print "cover_path_100",cover_path_100
				#print 'cover_path=',cover_path
			#print "cover_path_100",cover_path_100
			#print 'cover_path=',cover_path	
			
			if os.path.exists(cover_path_100):
				
				logger.debug( "in **PIC** getCoverPageObj at 'search icon' - OK Finished 875 [%s]"%(cover_path_100))
				print('cover_path_100='+str(type(cover_path_100)))
				dmp = pickle.dumps(base64.b64encode(bytes(cover_path_100,encoding = 'utf-8')))
				#print 'dmp - OK',type(cover_path_100)
				print('cover path - Finished OK')
				return xmlrpc.client.Binary(dmp)
				fileObj = open(cover_path_100,'rb')
				image = fileObj.read()
				fileObj.close()
			elif os.path.exists(cover_path):
				#print 'path ok:',cover_path
				fileObj = open(cover_path,'rb')
				im = Image.open(cover_path)
				if im.size[0] > 128 and  im.size[1] > 128:
					im = Image.open(fileObj)				
					im.thumbnail((128,128))
					im.save(cover_path_100,"JPEG")
					del(im)
					logger.debug( "in **PIC** getCoverPageObj at 'search icon' - OK Finished 889")
					return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path,encoding = 'utf-8'))))
					fileObj_100 = open(cover_path_100,'rb')
					image = fileObj_100.read()
					fileObj_100.close()
					fileObj.close()
					#print 'new Icon created!',cover_path_100
				else:		
				#print 'cover_path=',cover_path
					logger.debug( "in **PIC** getCoverPageObj at 'search icon' - OK Finished 898")
					return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path,encoding = 'utf-8'))))
					image = fileObj.read()
				#image = im.tostring()
				#s = f.read(4048)
					fileObj.close()
			else:	
				#fileObj = open(getcwd()+"\\images\\no-image-available_110x110.jpg","rb") 
				print('No File &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&???????????',self.__no_cover_page_obj_path)
				logger.debug( "in **PIC** getCoverPageObj at 996 'search icon' - OK Finished (No cover path)")
				return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(self.__no_cover_page_obj_path,encoding = 'utf-8'))))
				image = self.__no_cover_page_obj	
				
		elif 'album_images' in args:		
			logger.debug("in getCoverPageObj ->album_images :%s %s"%(str(args[0]),str(args[1])))
			imageD = args[1]
			if '.pdf' in imageD["image_crc32"]:
				#print 'pdf',imageD["image_crc32"][:-4]
				logger.debug( "in  getCoverPageObj at pdf: ")
				image_crc32=int(imageD["image_crc32"][:-4])
			else:
				image_crc32=int(imageD["image_crc32"])
			album_crc32=int(imageD["album_crc32"])
			
			imagesDL = self.__SearchBuf_D['sD']
			if 'get_images_from_cur_album' in self.__SearchBuf_D['searchTerm']:
				#print "ckeck 1",imageD
				#print imagesDL["album_crc32"],imageD["album_crc32"]
				if int(imagesDL["album_crc32"]) == album_crc32:
					#print "ckeck 2"
					logger.debug("in getCoverPageObj ->album_images->get_images_from_cur_album")
					if image_crc32 in imagesDL['imageD']:
						#print "ckeck 3"
						path= imagesDL['imageD'][image_crc32]
						logger.debug("in getCoverPageObj ->album_images->get_images_from_cur_album: Path %s"%(str([path])))
						if os.path.exists(path):
							logger.debug("in getCoverPageObj ->album_images - Path OK :%s %s"%(str(image_crc32),str([path])))	
							return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(path,encoding = 'utf-8'))))
						else:
							logger.critical("in getCoverPageObj -> Path not exists: %s"%(str([path])))
							
							
							#fileObj = open(path,'rb')
							#image = fileObj.read()
							#fileObj.close()
						
					
			print("Album Images processing",args)
			pass
		else:	
			# Ветка для большой картинки обычноых дисков
			#print 'if search_icon NOT!!!!!!!!!!!!!!!!!!!!! in args',len(args)
			logger.debug( "in *PIC* getCoverPageObj - other cases: %s"%(str(args)))
			if len(args)>0:
				id =  int(args[0])
				#print 'id=',id
				logger.debug( "in  getCoverPageObj at other cases id:%s: "%(str(id)))
				
			if id in self.__DB_metaIndxD_album:
				logger.debug( "in  getCoverPageObj at other cases [id in self.__DB_metaIndxD_album]: ")
				path = self.__DB_metaIndxD_album[id]
				logger.debug( "in  getCoverPageObj at other cases path=%s "%(path))
				#print 'path:',path
				if path[-1] != '\\':
					path+='\\'
				if path[:1] != '\\':
					path ='\\'+	path
				path = path.replace("\\","/")
				cover_path_320 = path_prefixL+path+'cover_320.jpg'
				cover_path_100 = path_prefixL+path+'cover_100.jpg'
				cover_path = path_prefixL+path+'cover.jpg'
				
			if os.path.exists(cover_path_320):
				#print 'path 320 ok:',cover_path
				logger.debug( "in **PIC** getCoverPageObj at 'search icon' - OK Finished (cover 320) 967")	
				return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path_320,encoding = 'utf-8'))))
				fileObj = open(cover_path_320,'rb')
				image = fileObj.read()
				fileObj.close()
			elif os.path.exists(cover_path):
				#print 'path ok:',cover_path
				fileObj = open(cover_path,'rb')
				im = Image.open(cover_path)
				if im.size[0] > 320 and  im.size[1] > 320:
					im = Image.open(fileObj)	
					im.thumbnail((320,320))	
					#im = im.resize((320, 320))
					im.save(cover_path_320,"JPEG")
					del(im)
					
					return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path_320,encoding = 'utf-8'))))
					fileObj_320 = open(cover_path_320,'rb')
					image = fileObj_320.read()
					fileObj_320.close()
					fileObj.close()
				else:		
				#print 'cover_path=',cover_path
					return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path,encoding = 'utf-8'))))
					image = fileObj.read()
				#image = im.tostring()
				#s = f.read(4048)
					fileObj.close()
			elif id	!= 0:
				# Ветка для большой картинки РАДИО, выявляем путь к радио папке, проверяя существование пути еще раз
				#print "radio",id
				
				if id in self.__DB_metaIndxD_album:
					cover_path = str(self.__DB_metaIndxD_album[id])
				if cover_path[-1] != '\\':
					cover_path+='\\'
				cover_path = cover_path.replace("\\","/")
				#print 'Radio cover path=',cover_path				
				logger.debug( "in  getCoverPageObj at Radio cover path==%s "%(cover_path))
				if os.path.exists(cover_path):
					cover_path = cover_path+'cover.jpg'	
					cover_path_100 = cover_path+'cover_100.jpg'
					return xmlrpc.client.Binary(pickle.dumps(base64.b64encode(bytes(cover_path,encoding = 'utf-8'))))
					fileObj = open(cover_path,'rb')
					image = fileObj.read()
					fileObj.close()
				else:
					#print "-------------->>>>>>>>>>>>>>>>>>>>No RADIO BIG IMAGE <<<<<<<<<<<< =-------------------------------"
					logger.error( "Error: 1023 in  getCoverPageObj -->No RADIO BIG IMAGE ")
					return xmlrpc.client.Binary(pickle.dumps(self.__no_cover_page_obj_path))
					
					image = self.__no_cover_page_obj
			else:	
				#fileObj = open(getcwd()+"\\images\\no-image-available_110x110.jpg","rb") 
				#print "-------------->>>>>>>>>>>>>>>>>>>>No IMAGE <<<<<<<<<<<< =-------------------------------"
				logger.error( "Error: 1030 in  getCoverPageObj -->No RADIO BIG IMAGE ")
				return xmlrpc.client.Binary(pickle.dumps(self.__no_cover_page_obj_path))
				image = self.__no_cover_page_obj
		return xmlrpc.client.Binary(pickle.dumps(self.__no_cover_page_obj_path))
		#return xmlrpclib.Binary(image)		
		
	def sendPicture(self,req_pic):
		
		#print '--------->',self.requestline
		
		if req_pic.find('cover.jpg')>=0 or req_pic.find('cover.gif')>=0:
			
			print("YEEESSS gif me!!!!!!!!",req_pic)
			
					
			self.send_response(200)
			
			if req_pic.find('.jpg')>=0:
				#self.send_header("Content-type", "image/jpg")
				#self.send_header('Cache-Control','private')
				#self.end_headers()

				image = self.getCoverPageObj()  
						
			else:
				#self.send_header("Content-type", "image/gif")
				#self.send_header('Cache-Control','private')
				#self.end_headers()

				image = self.getCoverPageObj() 
			
			#image = fileObj.read()
			#fileObj.close()	
			#image_s = pickle.dumps(image)
			
			
			return image
			
		elif req_pic.find('no-image-available_110x110.jpg')>=0:	
			#self.send_header("Content-type", "image/jpg")
			#self.send_header('Cache-Control','max-age=2592000')
			#self.end_headers()
			fileObj = open(self.__myMediaLibPath+"/images/no-image-available_110x110.jpg","rb") 		
			image = fileObj.read()
			fileObj.close()	
			#image_s = pickle.dumps(image)
			
			
			return image
		elif  req_pic.find('prev.jpg')>=0 or req_pic.find('next.jpg')>=0 or req_pic.find('play.jpg')>=0 or req_pic.find('pause.jpg')>=0 or req_pic.find('stop.jpg')>=0:
			#self.send_response(200)
			#print '-----------prev'
			#self.send_header("Content-type", "image/jpg")
			#self.send_header('Cache-Control','max-age=2592000')
			#self.end_headers()
			
			if  req_pic.find('prev.jpg')>=0:
				image = self.getConrolPicD('prev')
				#fileObj = open(getcwd()+"\\images\\prev.jpg","rb")
			elif  req_pic.find('next.jpg')>=0:
				image = self.getConrolPicD('next')
				#fileObj = open(getcwd()+"\\images\\next.jpg","rb")
			elif  req_pic.find('play.jpg')>=0:
				image = self.getConrolPicD('play')
				#fileObj = open(getcwd()+"\\images\\play.jpg","rb")
			elif  req_pic.find('stop.jpg')>=0:
				image = self.getConrolPicD('stop')
				#fileObj = open(getcwd()+"\\images\\stop.jpg","rb")	
			elif  req_pic.find('pause.jpg')>=0:
				image = self.getConrolPicD('pause')
				#fileObj = open(getcwd()+"\\images\\pause.jpg","rb")		
			
			#image = fileObj.read()
			#fileObj.close()	
			
			#image = libObj.getConrolPicD()
			#self.wfile.write(image)	
			return image	
			
		else:
			return 0
	
		
	def debug_get_controllist_for_main(self):
		listContentD  = self.getAlbumList_DATA()
		return xmlrpc.client.Binary(pickle.dumps(listContentD))	
	
	def update_model_state(self,PlayControl_CurStatusD):
		self.__songNum = PlayControl_CurStatusD['pl_pos']
		self.__stop_flag = PlayControl_CurStatusD['playBack_Mode']
		self.__curList_crc32 = PlayControl_CurStatusD['pL_CRC32']
		
		port = int(self.__configDict['player_cntrl_port'])
		s = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(port))
		l_data = zlib.decompress(s.get_cur_pl_as_list().data)
		self.__PlayListL = 	pickle.loads(l_data)
		#self.__PlayListL = PlayControl_CurStatusD['PlayListL']
		try:
			self.__PlayList_asCRC32_L = [zlib.crc32(a.encode('raw_unicode_escape')) for a in self.__PlayListL]	
		except Exception as e:
			logger.critical('Error: in update_model_state %s'%(str(e)))		
			
		return self.__PlayList_asCRC32_L
		
	def update_curList_metaD(self,metaD):
		self.__metaD_of_cur_pL = metaD	
	
	def update_process_context(self):
		port = int(self.__configDict['player_cntrl_port'])
		s = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(port))
		
		l_data = zlib.decompress(s.get_cur_pl_as_list().data)
		self.__PlayListL = 	pickle.loads(l_data)
		#self.__PlayListL = self.getCurPlayListAsList()
		
		checkCrc32 = zlib.crc32(str(self.__PlayListL))
		#checkCrc32 = zlib.crc32(str(winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_)))
		curListName = ''
		for a in self.__pD:
			
			if self.__pD[a]['crc32'] == checkCrc32:
				curListName = self.__pD[a]['filename']
				
		#curListName =  findCorrespond_Ml_List(self.__playlistpath,self.__pD,winamp.getTrackList(self.__playlistpath+'winamp.'+winampext_))
		if curListName != None and curListName != '':
			self.setplayList(str(curListName))
		else:
			self.setplayList('')
			
	def get_current_album_track_num(self):		
		l_sort = []
		logger.debug("in get_current_album_track_num:%s %s"%(str(len(self.__PlayListL)),str(self.__PlayListL)))
		#print 'in get_current_album_track_num',len(self.__PlayListL)
		l = self.__PlayListL
		
		if len(self.__PlayListL) <= 1:
			return {'albumNum':0,'songNum':0}
		
		lD = {}
		if l != [] and l != None:
			lD = DistinctAlbums_from_playlist(l)
			
			
		if lD != {}:
			l_sort = [lD[a]['firstFileIndex'] for a in lD] 
			l_sort.sort()
		#print l_sort
		try:	
			prev = 0
			for a in l_sort:
				if	self.__songNum < a:
					#print self.__songNum,a
					return {'albumNum':prev,'songNum':self.__songNum}
				prev = a	
			return {'albumNum':a,'songNum':self.__songNum}	
			
		except:
			return None
		return None	
		
	# def get_radio_stationData_list(self):
		# 'radio_statD' = self.__radio_stationD,
		# DbIdL=self.__model_instance.getDbIdL_viaTagId(455,None)
		# metaD = self.__model_instance.getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None)	
		# modelDic['radio_statD'] = {}
		# for a in metaD:
			# modelDic['radio_statD'][a]={'station_name':metaD[a]['title']}	
		
	def get_current_Album_order_Indx(self):
		print('in get_current_Album_order_Indx, len PlayListL:',len(self.__PlayListL))
		l = self.__PlayListL
		l_sort = []
				
		if len(self.__PlayListL) <= 1:
			print('album index=**************-------',0)
			return 0
		
		lD = {}
		if l != [] and l != None:
			lD = DistinctAlbums_from_playlist(l)
			
			
		if lD != {}:
			l_sort = [(lD[a]['firstFileIndex'],lD[a]['album_order_numb']) for a in lD] 
			l_sort.sort()
		#print l_sort
		try:	
			for a in l_sort:
				if	self.__songNum < a[0]:
					#print self.__songNum,a
					print('album index=******************-------',a[1]-1)
					return a[1]-1
			print('album index=-------',a[1])		
			return	a[1]	
			
		except:
			print('album index=******************------- ERROR', end=' ')	
			return None
		print('album index=********************------- ERROR', end=' ')	
		return None	
			
	def get_current_Album_Track_context(self):
		logger.debug( "in get_current_Album_Track_context, len PlayListL:[%s] - Start"%(str(len(self.__PlayListL))))
		
		l = self.__PlayListL
		l_sort = []
				
		if len(self.__PlayListL) <= 1:
			print('album index=**************-------',0)
			logger.debug( "in get_current_Album_Track_context 0000 Finished")	
			return {'albumNum':0,'songNum':0,'album_ord_index':0}
			
		
		lD = {}
		if l != [] and l != None:
			lD = DistinctAlbums_from_playlist(l)
			
			
		if lD != {}:
			l_sort = [(lD[a]['firstFileIndex'],lD[a]['album_order_numb']) for a in lD] 
			l_sort.sort()
		#print l_sort
		try:
			prev = 0
			for a in l_sort:
				if	self.__songNum < a[0]:
					#print self.__songNum,a
					print('album index=******************-------',a[1]-1)
					#return a[1]-1
					logger.debug( "in get_current_Album_Track_context 1194 Finished")	
					return {'albumNum':prev,'songNum':self.__songNum,'album_ord_index':a[1]-1}
				prev = a[0]	
			logger.debug( "in get_current_Album_Track_context 1195 Finished")	
			return {'albumNum':a[0],'songNum':self.__songNum,'album_ord_index':a[1]}	
			
			#print 'album index=-------',a[1]		
			#return	a[1]	
			
		except:
			print('album index=******************------- ERROR', end=' ')	
			logger.critical( "in get_current_Album_Track_context Error - 1 Finished")	
			return None
		print('album index=********************------- ERROR', end=' ')	
		logger.critical( "in get_current_Album_Track_context Error - 2 Finished")	
		return None	
		
	def get_Prev_Next_AlbumIndx(self):
		l = self.__PlayListL
		lD = {}
		l_sort = []
		if l != [] and l != None:
			lD = DistinctAlbums_from_playlist(l)
		if lD != {}:
			l_sort = [lD[a]['firstFileIndex'] for a in lD] 
			l_sort.sort()
		logger.info( "get_Prev_Next_AlbumIndx:%s %s"%(str(self.__albumNum),str(self.__songNum)))
		
		next = prev = None
		if len(l_sort) <= 1:
			return (prev,next)
			
		if self.__albumNum == 0:
			next = l_sort[1]
			return (prev,next)
		
			
		tmpL = [a for a in l_sort if a > self.__albumNum]
		#print l_sort,self.__albumNum,tmpL
		if len(tmpL) >= 1 :
			next = tmpL[0]
			prev = l_sort[l_sort.index(next)-2]
			return (prev,next)
			
		else:
			prev = l_sort[-2]
			return (prev,next)

	
	def setStopFlag(self,flag):
		self.__stop_flag = flag
	def setManualStopFlag(self,flag):
		self.__manual_stop_flag = flag	
		
	def setplaylistGroup(self,group_name):
		self.__playlistGroup = group_name 
	
	def setCashD(self,key,Obj):
		self.__Cash_D[key] = Obj
	
	def set_genKeyL(self,keyL,cfgD,*args):
	# метод установки списка ключей общего назначения, можно применять например для хранения дельта изменений-дополнений при модификации объектов в БД из web gui
	# action type - это тип действия со списком, для удаления или дополнений "add" ,"delete"
		return_res = str(time.time())
		if 'init' in args:
			self.__genKeyListD = {}
		else:
			self.__genKeyListD = {'keyL':keyL,'cfgD':cfgD,'time_stamp':return_res}
		return return_res	
		
	def get_genKeyL(self):
		return self.__genKeyListD
	
	def getSearchBufD(self,*args):
		if 'rpc' in args:
			return xmlrpc.client.Binary(pickle.dumps(self.__SearchBuf_D))
		return self.__SearchBuf_D
	def setSearchBufD(self,searchTerm,Obj,tag_id,tag_form_mode,paramD):
		self.__SearchBuf_D = {'searchTerm':	searchTerm,'sD':Obj,'tag_id':tag_id,'tag_form_mode':tag_form_mode,'paramD':paramD}
		
	def getSearch_editable_BufD(self):
		return self.__SearchEditBuf_D
	def setSearch_editable_BufD(self,Obj,tag_id,action_mode):
		self.__SearchEditBuf_D = {'sD':Obj,'tag_id':tag_id,'action_mode':action_mode}	
	def setMLFolderTreeAll_BufD(self,Obj):
		self.__mlFolderTreeAllBuf_D = Obj
	
	def setTracksPreloadRes_BufD(self,Obj):
		self.__tracksPreloadRes_D = Obj	
	
		
	def setAutoComplSearch_BufD(self,Obj):
		self.__setAutoComplSearchBuf_D = Obj				
		
	def getTracksPreloadRes_BufD(self):
		return self.__tracksPreloadRes_D		
		
	def getAutoComplSearch_BufD(self):
		return self.__setAutoComplSearchBuf_D
		
	def getMLFolderTreeAll_BufD(self):
		return self.__mlFolderTreeAllBuf_D
	def freeMLFolderTreeAll_BufD(self):
		self.__mlFolderTreeAllBuf_D	= {}
		
	def setplayList(self,List_name):
		self.__listName = List_name
		
	def setDaemon(self,DaemonRef):
		self.__DaemonRef = DaemonRef	
	
	def append_to_Temp_MemCRC32_PlayList(self,track_crc32):
		self.__Temp_MemCRC32_PlayList.append(track_crc32)
	
	def setSongAlbumNums(self,song_num,album_num):
		if song_num != None:
			self.__songNum = song_num
		if album_num != None:	
			self.__albumNum = album_num
			
	def setModelLoggerLevel(self,level):
		self.__modellogger.setLevel(level)
		
	def get_folderL_via_folder_key(self,srch_folder_key):
		if srch_folder_key in self.__group2PlayListD['groupD']:
			return self.__group2PlayListD['groupD'][srch_folder_key]['ref_folderL']
		else:
			return []
	
	def set_All_metaD(self,srch_folder_key,*args):
		print('in set_All_metaD',list(self.__All_metaD.keys()),self.__All_metaD['search_key'])
		folderL = []
		DbIdL =  []
		
		
		
		if srch_folder_key != '' and srch_folder_key != None and srch_folder_key not in self.__All_metaD['search_key']:
		
			if srch_folder_key in self.__group2PlayListD['groupD']:
				folderL = self.__group2PlayListD['groupD'][srch_folder_key]['ref_folderL']
				#print folderL
			
			if folderL != []:
				DbIdL = getDbIdL_w_folderL_filter(self.__dbPath,folderL,None)
			elif folderL == [] and self.__All_metaD['resD'] != {}:
				srch_folder_key = 'ALL_DATA'
				self.__All_metaD['search_key'] = srch_folder_key
				print('__All_metaD is buffered return! for folder=[] :',srch_folder_key)
				return
			
			if DbIdL != []:
				resD = getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None,'progress')
				self.__All_metaD ={'search_key':srch_folder_key,'resD':resD}
			else:
				resD = getCurrentMetaData_fromDB_via_DbIdL([],None,'progress','take_all')
				srch_folder_key = 'ALL_DATA'
				self.__All_metaD ={'search_key':srch_folder_key,'resD':resD}
			print(1)
			self.__Artist_metaBufL=[resD[a]['artist'] for a in resD]	
			print(2)
		elif ( srch_folder_key == '' or srch_folder_key == None ) and self.__All_metaD['search_key'] != 'ALL_DATA':	
			
			resD = getCurrentMetaData_fromDB_via_DbIdL([],None,'progress','take_all')
			srch_folder_key = 'ALL_DATA'
			self.__All_metaD ={'search_key':srch_folder_key,'resD':resD}
			print(3)		
			self.__Artist_metaBufL=[resD[a]['artist'] for a in resD]
			print(4)
			
		elif srch_folder_key != '' and srch_folder_key in self.__All_metaD['search_key'] and self.__All_metaD['resD'] != {}:	
			
			print('__All_metaD is buffered! with:',srch_folder_key)
		elif ( srch_folder_key == '' or srch_folder_key == None ) and self.__All_metaD['search_key'] == 'ALL_DATA'  and self.__All_metaD['resD'] != {}:	
			print('__All_metaD is buffered! with:','ALL_DATA')	
		else:
			print('__All_metaD is buffered! with:????',srch_folder_key)
		print(7)	
	
	def get_All_metaD(self,*args):
		if 'rfc' in args:
			compress_d = zlib.compress(pickle.dumps(self.__All_metaD))
			return xmlrpc.client.Binary(compress_d)
			
		else:	
			return self.__All_metaD
			
	def get_All_metaD_filter_key(self):
		if 'search_key' in self.__All_metaD:
			return self.__All_metaD['search_key']
		else:
			return None
			
		
	def setReportBuf_forArtist(self,ReportBufD):
		self.__ReportBufD = ReportBufD
	
	def getReportBuf_forArtist(self):
		return self.__ReportBufD
		
	
	
	def set_ReportBuf_forArtist_id(self, artist_crc32,value,*args):
		if 'artistD' in self.__ReportBufD:
			if artist_crc32 in self.__ReportBufD['artistD'][artist_crc32]:
				if 'main' in args:
					self.__ReportBufD['artistD'][artist_crc32]['main'] = value
			
	def changePlaylistQueueD_atPos(self,key,pos,value):
		logger.debug("Changing changePlaylistQueueD_atPos %s,%s,%s"%(str(key),str(pos),str(value)))
		
		if pos != None:
			self.__PlayListQueueD[key][pos] = value
		else:
			if 'cur_pos' in self.__PlayListQueueD[key]:
				self.__PlayListQueueD[key]['cur_pos'] = value
			else:
				print('__PlayListQueueD',key,' does not have key: cur_pos')
		
	def printLibStatus(self):
		print("mediaPath=%s \n winampext=%s\n mlXMLPath=%s \n'"%(self.__mediaPath,self.__winampext,self.__mlXMLPath))
		
	def getMediaLibPlayProcessContext(self):
		#self.update_process_context()
		#return {'winampext':self.__winampext,'playlistpath':self.__playlistpath,'mediaPath',self.__mediaPath}
		return {'winampext':self.__winampext,
				'playlistpath':self.__playlistpath,
				'mediaPath':self.__mediaPath,
				'prev_entry':self.__prev_entry,
				'cur_entry':self.__cur_entry,
				'stop_flag':self.__stop_flag,
				'mlXMLPath':self.__mlXMLPath,
				'curList_crc32':self.__curList_crc32,
				'playlistGroup':self.__playlistGroup,
				'listName':self.__listName,
				'albumNum':self.__albumNum,
				'songNum':self.__songNum,
				'manual_stop_flag':self.__manual_stop_flag,
				'myMediaLibPath':self.__myMediaLibPath,
				'dbPath':self.__dbPath,
				'mpdMusicPathPrefix':self.__mpdMusicPathPrefix
								
				}		
				
	def getMediaLibPlayProcess_State(self):
		# Эта функция аналогична getMediaLibPlayProcessContext, MediaLibPlayProcessDic - но должна выдавать параметры текущего состояния
		# модели процесса проигрывания без сложных структур метаданных 
		# функция будет применяться для формирования main view. Указанные выще фунции содержащие буферы метаданных должны выдавать свои
		# резултаты на остове этой функции т.е. getMediaLibPlayProcess_State
		#self.update_process_context()
		#return {'winampext':self.__winampext,'playlistpath':self.__playlistpath,'mediaPath',self.__mediaPath}
		return {
				'prev_entry':self.__prev_entry,
				'cur_entry':self.__cur_entry,
				'stop_flag':self.__stop_flag,  # Ок - текущий стоп статус
				'curList_crc32':self.__curList_crc32, # Ок - crc32 текущего листа
				'playlistGroup':self.__playlistGroup,
				'listName':self.__listName,
				'albumNum':self.__albumNum, # порядковый номер трека с которого начинается новый альбом в листе
				'songNum':self.__songNum, # порядковый номер текущего трека
				'manual_stop_flag':self.__manual_stop_flag, # Ок - флаг определяющий факт ручной остановки процесса
				'PlayerControl':self.__PlayerControl, # управляющий функциональный элемент медиаплеера 
				'Temp_MemCRC32_PlayList':self.__Temp_MemCRC32_PlayList
				}			
	
	def MediaLibPlayProcessDic(self,*args):
		# Метаданные при текущем состоянии модели
		# Этот метод должен содержать словари метаданных, текущие значения индексов для словарей должны браться из getMediaLibPlayProcess_State
		masResD = {}
		Player_RPC_methods = []
		if self.__isPlayerAlive:
			Player_RPC_methods = self.__PlayerControl.system.listMethods(),
		#if args == None:
		return {'pD':self.__pD,
				 'pD_crc32':self.__pD_crc32,
				'group2PlayListD':self.__group2PlayListD,
				'playlistGroup':self.__playlistGroup,
				'CashD':self.__Cash_D,
				'ReportBufD':self.__ReportBufD,
				'DB_metaIndxD':self.__DB_metaIndxD,
				
				'DB_metaIndxD_obratn':self.__DB_metaIndxD_obratn,
				'DB_virtual_albumD':self.__DB_virtual_albumD,
				
			
				'DB_metaIndxD_album':self.__DB_metaIndxD_album,
				'PlayList_asCRC32_L':self.__PlayList_asCRC32_L,
				'PlayListL':self.__PlayListL,
				
				'ArtistL':self.__ArtistL,
				'Artist_metaBufL':self.__Artist_metaBufL,
				'mlFolderTreeAllBufL':self.__mlFolderTreeAllBuf_D,
				
				#'AutoComplSearchBuf_D':self.__setAutoComplSearchBuf_D
				'listsMetaData':self.__listsMetaData,
				
				#'radio_statD' = self.__radio_stationD,
				
				'TagD':self.__TagD,
				'Tmpl':self.__Tmpl_D,
				'metaD_of_cur_pL':self.__metaD_of_cur_pL ,
				'player_cntrl_port':self.__configDict['player_cntrl_port'],
				'configDict' :  self.__configDict,
				'commandRouting':self.__commandRoutingDic,
				'pLQueueD':  {'PlayListQueueD':self.__PlayListQueueD,'PlayListQueue':self.__PlayListQueue},
				
				'Player_RPC_methods':Player_RPC_methods,
				'appl_cntrl_port':self.__configDict['appl_cntrl_port'],
				
				

				}
	def create_new_sessionContext(self,session_id):
		self.__CastPlayList[session_id] = self.__CastPlayList[1]
	def set_CastPlayList(self,session_id,list_dataD):
	#self.__CastPlayList[session_id]={'cur_track_id':'','player_status':'','metaD':{}}
		if session_id not in self.__CastPlayList:
			self.create_new_sessionContext(session_id)
		if session_id in self.__CastPlayList:
			for a in list_dataD:
			
				if a in self.__CastPlayList[1]:
					#print a
					logger.debug('%s added into session context'%(str(a)))
					self.__CastPlayList[session_id][a] = list_dataD[a]
					
		else:
			
			logger.error("session no found%s"%str(session_id))
			return None
		return 1

	def get_CastPlayList(self,session_id):	
		
		logger.debug('current sessions:%s id=%s'%(str(list(self.__CastPlayList.keys())),str(session_id)))
		try:
			return self.__CastPlayList[session_id]
		except Exception as e:
			logger.critical("session no found%s"%str(session_id))
			return self.__CastPlayList[1]
		
	def MediaLibPlayProcessDic_viaKey(self,key,*args):
		processDics = self.MediaLibPlayProcessDic()
		masResD = {}
		prDicNames = ['pD','group2PlayListD','playlistGroup','CashD','DB_metaIndxD','Tmpl','metaD_of_cur_pL','pLQueueD','player_cntrl_port','Player_RPC_methods','appl_cntrl_port','configDict','Artist_metaBufL','DB_metaIndxD_album','DB_metaIndxD_obratn','SearchBufD']
		if 'local' in args:
			if key in processDics:
				return processDics[key]
			else:
				print("Error: wrong key in MediaLibPlayProcessDic_viaKey:",key)
				return 0
		# For RPC process	
		if key in prDicNames:
			return xmlrpc.client.Binary(pickle.dumps(processDics[key]))
		else:
			print('This argument disabled, need to be activated:',key)
			return 0
	def set_new_pD_elem(self,keyElem,dicData):
		#pD['plf325.m3u8'] = {'title': 'song titel', 'seconds': u'50997', 'filename': u'plf325.m3u8', 'crc32': 1007471235, 'id': u'{790099AB-0E98-4E3D-AD11-1BE8F9E91CF7}', 'songs': u'247'}
		if 'crc32' not in dicData:
			print('Eroror: CRC32 not given --> no Assignement for',keyElem,dicData)
		else:	
			self.__pD[keyElem] = dicData
	def add_new_playList_to_queue(self,pL_CRC32,listType,listDescr):		
		if pL_CRC32 not in self.__PlayListQueueD:
			DbIdL = [self.__DB_metaIndxD[a][0] for a in self.__PlayList_asCRC32_L if a in self.__DB_metaIndxD]
			
			self.__PlayListQueueD[pL_CRC32] = {'listType':listType,'PlayListL':DbIdL,'metaD':self.__metaD_of_cur_pL,'listDescr':listDescr,'cur_pos':0}
			if len(self.__PlayListQueue)>= 12:
				a = self.__PlayListQueue.pop(0)
			self.__PlayListQueue.append(pL_CRC32)
			
	
def str2_RusLine(in_line,res_size):
	r_line = "N/A "
	try:	
		r_line = """%s"""%(in_line)
	except UnicodeEncodeError:	
		try:
			s = ''.join([chr(ord(b)) for b in in_line])
			r_line = s #.decode('cp1251').encode('utf8')
							#print '2-ok','-->',mp3L.index(a)
		except ValueError:
			try:
								#print 'b=',b,mp3L.index(a),a
				r_line = in_line.encode('utf8')
			except:
				r_line = "N/A Decode error "
	if res_size > 0:			
		return r_line[:res_size]			
	else:
		return r_line
		
def getMyMediaLib_ListsData(pD,mlPath):
	#context=medialibObj.getMediaLibPlayProcessContext()
	#try:
	#	plL = getPlaylistsfromXML(context['mlXMLPath'])
	#except:
	#	import myMediaLib
	#	plL = myMediaLib.getPlaylistsfromXML(context['mlXMLPath'])
	#mlPath = context['playlistpath']+'Plugins\\ml\\'
	listD = {}
	errorL = []
	ok_cnt = 0
	print('Winamp list number:',len(list(pD.keys())))
	for a in list(pD.keys()):
		l = getTrackList(mlPath + a)
		print('*', end=' ')
		for b in l[1:]:
			
			try:
				crc32 = zlib.crc32(b.encode('raw_unicode_escape'))
			except Exception as e:
				logger.critical('at getMyMediaLib_ListsData Error %s %s'%(str(a),str(e)))
				continue
				
			pos = b.rfind('\\')
			try:
				crc32_d=zlib.crc32(b.encode('raw_unicode_escape').lower()[:pos])
				#crc32_d=zlib.crc32(b.lower()[:pos])
				ok_cnt+=1	
			except:
				#print '2:',b
				errorL.append(b)
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
	if errorL != []:
		print() 
		print('Winamp list Track issues:%s of %s'%(str(len(errorL)),str(ok_cnt)))			
	return listD	

class MediaLibPlayProcess_singletone_Wrapper():
	def __init__(self):
		self.__instance = MediaLibPlayProcess_singletone()
		#print dir(self.__instance)
	def get_instance(self):
		#print dir(self.__instance)
		return self.__instance
	

			
 	
class PlayerController():
	def __init__(self):
		self.__winampext = ''
		self.__playlistpath = ''
		self.__mediaPath = ''
		self.__listName = ''
		self.__songNum = 0
		self.__albumNum = 0
		self.__pD = None
		self.__prev_entry = None
		self.__cur_entry = None
		self.__stop_flag = ''
		self.__group2PlayListD = None
		self.__playlistGroup = 'ALL_GRP'
		self.__mlXMLPath = ''
		self.__winampObj = None
		self.__DaemonRef = None
		self.__HistoryL = []
		self.__FavoritL = []
		self.__cover_page_obj = ''
		self.__controlPicD = {}
		self.__Cash_D = {}
		self.__PlayListL = []
		self.__DB_metaIndxD = {}
		self.__myMediaLibPath = ''
		self.__SearchBuf_D = {}
		self.__Tmpl_D = {}
		self.__TagD = {}
		self.__configDict = {}
		
		# self.__configDict = readConfigData(mymedialib_cfg)
		# port = int(self.__configDict['player_cntrl_port'])
		# dbl_appl = xmlrpclib.ServerProxy('http://127.0.0.1:%s'%(str(port)))	
		# try:
			# res = dbl_appl.get_status()['playBack_Mode']
			# print "Player server already running -> no copy allowed."
			# 		print "Wait 5 sec for exit..."
			#time.sleep(5)

			# os.exit()
		# except:
			# pass
		
		for a in range(5):
			try:
				self.__winampObj = winamp.Winamp()
				if self.__winampObj.getVersion() != None and self.__winampObj.getVersion() != '0.':
					print('Winamp %s is OK'%(self.__winampObj.getVersion()))
					break
				
				print('No Winamp at the moment try to start it ...')
					
				#startfile('winamp.exe')
				for i in range(10):
					time.sleep(1)
					print('.', end=' ')
					self.__winampObj = winamp.Winamp()
					if self.__winampObj.getVersion() != None and self.__winampObj.getVersion() != '0.':
						print('Winamp %s is OK'%(self.__winampObj.getVersion()))
						break
			
				
			except:
				print('No Winamp at the moment try to start it ...')
				for i in range(10):
					time.sleep(1)
					print('.', end=' ')
				
		#configDict = {'mediaPath':'','winampext':'','player_cntrl_port':0,,'appl_cntrl_port':0}	
		
		
		self.__configDict = readConfigData(mymedialib_cfg)
		self.__myMediaLibPath = self.__configDict['applicationPath']
		self.__dbPath = self.__configDict['dbPath']
	
	def runPlayerServer(self):
		
		port = int(self.__configDict['player_cntrl_port'])
		print(port)
		dbl_appl = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(str(port)))	
		try:
			res = dbl_appl.get_status()['playBack_Mode']
			print("Player server already running -> no copy allowed.")
			print("Wait 5 sec for exit...[%s]"%(str(res)))
			time.sleep(5)

			return
		except:
			pass
	

		http.server.BaseHTTPRequestHandler.address_string = new_address_string

		server = SimpleXMLRPCServer(("127.0.0.1", port),allow_none = True)
		print("Listening on port %s..."%(str(port)))
		#print 'avalable  methods:',str(server.system.listMethods())
		server.register_introspection_functions()
		server.register_function(self.play, "play")
		server.register_function(self.stop, "stop")
		server.register_function(self.get_cur_track_pos, "get_cur_track_pos")
		server.register_function(self.set_cur_track_pos, "set_cur_track_pos")
		server.register_function(self.__next__, "next")

		server.register_function(self.prev, "prev")
		server.register_function(self.pause, "pause")
		server.register_function(self.rewind, "rewind")
		server.register_function(self.forward, "forward")
		server.register_function(self.refreshPlayerControl, "refresh_player")
		server.register_function(self.set_new_playList_withPos,'new_list_load')
		server.register_function(self.set_new_playList_direct_withPos,'new_list_load_direct')
															  
		server.register_function(self.get_cur_pl_as_list,'get_cur_pl_as_list')
		
		server.register_function(self.getPlaylistFingerPrint,'getPlaylistFingerPrint')
		
		server.register_function(self.play_from_fileL,'play_from_fileL')
		
		server.register_function(self.get_cur_pl_key_crc32,'get_cur_pl_key_crc32')
		server.register_function(self.get_cur_track_crc32,'get_cur_track_crc32')
		server.register_function(self.get_cur_pl_as_list_of_crc32,'get_cur_pl_as_list_of_crc32')
		server.register_function(self.set_position_within_the_track,'set_position_within_the_track')
		server.register_function(self.get_status,'get_status')
		server.register_function(self.get_cur_track,'get_cur_track')
		server.register_function(self.closeWinamp,'closeWinamp')
		server.serve_forever()
		
	def refreshPlayerControl(self):
		self.__winampext = ''
		self.__playlistpath = ''
		self.__mediaPath = ''
		self.__listName = ''
		self.__songNum = 0
		self.__albumNum = 0
		self.__pD = None
		self.__prev_entry = None
		self.__cur_entry = None
		self.__stop_flag = ''
		self.__group2PlayListD = None
		self.__playlistGroup = 'ALL_GRP'
		self.__mlXMLPath = ''
		self.__winampObj = None
		self.__DaemonRef = None
		self.__HistoryL = []
		self.__FavoritL = []
		self.__cover_page_obj = ''
		self.__controlPicD = {}
		self.__Cash_D = {}
		self.__PlayListL = []
		self.__DB_metaIndxD = {}
		self.__myMediaLibPath = ''
		self.__SearchBuf_D = {}
		self.__Tmpl_D = {}
		self.__TagD = {}
		self.__configDict = {}
		
		for a in range(5):
			try:
				self.__winampObj = winamp.Winamp()
				if self.__winampObj.getVersion() != None:
					print('Winamp %s is OK'%(self.__winampObj.getVersion()))
					break
			except:
				print('No Winamp at the moment try to start it ...')
				for i in range(10):
					time.sleep(1)
					print('.', end=' ')
				
		#configDict = {'mediaPath':'','winampext':'','player_cntrl_port':0,,'appl_cntrl_port':0}	
		
		
		self.__configDict = readConfigData(mymedialib_cfg)
		
	def set_new_playList_withPos(self,list_path_name,pos):
		#prog_path = prog_path+'\\'+'clamp.exe' 
		#L = [' ','/stop','/clear', '/load','"%s"'%(list_path_name)]
		#L = [' ','/clear /load "%s"'%(list_path_name)]
		#command = '/'+command
		#print L
		#os.spawnv(os.P_WAIT,prog_path,L)
		mode = self.__winampObj.getPlaybackStatus()	
		self.__winampObj.stop()
		self.__winampObj.clearPlaylist()
		self.__winampObj.enqueueFileW(list_path_name)
		self.__winampObj.setPlaylistPosition(pos)
		if mode  == 1:
			self.__winampObj.play()
		elif mode  == 3:	
			self.__winampObj.pause()
		
		return self.get_status()		
		
	def set_new_playList_direct_withPos(self,bin_list,pos):
		#prog_path = prog_path+'\\'+'clamp.exe' 
		#L = [' ','/stop','/clear', '/load','"%s"'%(list_path_name)]
		#L = [' ','/clear /load "%s"'%(list_path_name)]
		#command = '/'+command
		playlistL = zlib.decompress(bin_list.data)
		playlistL = pickle.loads(playlistL)
		''.join(playlistL)
		#print "Gogo!!!!",len(playlistL)
		#os.spawnv(os.P_WAIT,prog_path,L)
		mode = self.__winampObj.getPlaybackStatus()	
		self.__winampObj.stop()
		self.__winampObj.clearPlaylist()
		#for a in playlistL:
		self.__winampObj.enqueueFile(''.join(playlistL))
		self.__winampObj.setPlaylistPosition(pos)
		if mode  == 1:
			self.__winampObj.play()
		elif mode  == 3:	
			self.__winampObj.pause()
		
		return self.get_status()	
	
	def getPlaylistFingerPrint(self):
		return self.__winampObj.getPlaylistFingerPrint()
	
	def play_from_fileL(self,fL,pos):
		
		pc = self.__winampObj.stop()
		pc = self.__winampObj.clearPlaylist()
		for a in fL:
			pc = self.__winampObj.enqueueFileW(a)
			
		self.__winampObj.setPlaylistPosition(pos)
		pc = self.__winampObj.play()
		
		return self.get_status()

	
	def get_status_short(self):
		cur_pl_key_crc32 = self.get_cur_pl_key_crc32()
		cur_pl_pos = self.__winampObj.getPlaylistPosition()
		return {
				'pl_pos':cur_pl_pos,
				'pL_CRC32':cur_pl_key_crc32,
				'track_CRC32':self.get_cur_track_crc32(),
				'playBack_Mode': 1
				#self.__winampObj.getPlaybackStatus()
				
				}	
		
	def get_status(self):
		
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
				'playBack_Mode': 1,
				#self.__winampObj.getPlaybackStatus(),
				'playingTrack_pos':self.__winampObj.getPlayingTrackPosition(),
				'rest_sec':(self.__winampObj.getPlayingTrackLength()*1000 - self.__winampObj.getPlayingTrackPosition())/1000,'duration_sec':(self.__winampObj.getPlayingTrackLength())}	
		
	def play(self):
		if self.__winampObj.getPlaybackStatus() != 1:
			self.__winampObj.play()
		return self.get_status()

	def stop(self):
		self.__winampObj.stop()	
		return self.get_status()

	def pause(self):
		if self.__winampObj.getPlaybackStatus() == 1:
			self.__winampObj.pause()
			return self.get_status()
			
		elif self.__winampObj.getPlaybackStatus() == 3:	
			self.__winampObj.play()	
			return self.get_status()
		

	def prev(self):
		prev = cur_track = self.__winampObj.getPlaylistPosition()
		if cur_track > 0:  
			prev = self.__winampObj.getPlaylistPosition()-1
		else:
			return self.get_status()
		self.__winampObj.setPlaylistPosition(prev)	
		self.__winampObj.play()
		
		
		if self.__winampObj.getPlaybackStatus() == 0:	
			self.__winampObj.setPlaylistPosition(prev)	
		elif self.__winampObj.getPlaybackStatus() == 3:
			self.__winampObj.stop()	
			self.__winampObj.setPlaylistPosition(prev)	
		elif self.__winampObj.getPlaybackStatus() == 1:	
			self.__winampObj.setPlaylistPosition(prev)	
			
		return self.get_status()		
		
	def __next__(self):
	
		if self.__winampObj.getListLength() == self.__winampObj.getPlaylistPosition()+1:
			return self.get_status()
		else:
			next = self.__winampObj.getPlaylistPosition()+1
			
		if self.__winampObj.getPlaybackStatus() == 0:	
			self.__winampObj.setPlaylistPosition(next)	
		elif self.__winampObj.getPlaybackStatus() == 3:
			self.__winampObj.stop()	
			self.__winampObj.setPlaylistPosition(next)	
		elif self.__winampObj.getPlaybackStatus() == 1:	
			self.__winampObj.setPlaylistPosition(next)	
			self.__winampObj.play()
			
		return self.get_status()
		
		
		
	def get_cur_track_pos(self):
		return self.__winampObj.getPlaylistPosition()
		
	def get_cur_track_crc32(self):
		file_track = self.__winampObj.getPlaylistFileW(self.__winampObj.getPlaylistPosition())
		try:
			res_crc32 = zlib.crc32(file_track.encode('raw_unicode_escape'))
		except Exception as e:
			print('Error:',str(e))
			print([file_track])
			return
			
		return res_crc32	
		
	def set_cur_track_pos(self,pos):
		self.__winampObj.setPlaylistPosition(pos)
		if self.__winampObj.getPlaybackStatus() == 1:
			self.__winampObj.stop()
			self.__winampObj.play()
			return self.get_status()
		elif self.__winampObj.getPlaybackStatus() == 3:	
			self.__winampObj.stop()
			self.__winampObj.pause()	
			return self.get_status()	
		return self.get_status()

	def get_cur_pl_as_list(self):
		l = self.__winampObj.getPlaylistFilenames()	
		compress_l = zlib.compress(pickle.dumps(l))
		return xmlrpc.client.Binary(compress_l)	
		
	def get_cur_track(self):
		l = self.__winampObj.getPlaylistFilenames()	
		#file_track = l[self.__winampObj.getPlaylistPosition()].lower()
		file_track = l[self.__winampObj.getPlaylistPosition()]
		#print zlib.crc32(file_track)	
		return xmlrpc.client.Binary(pickle.dumps(file_track))		
		
	def get_cur_pl_as_list_of_crc32(self):
		l = self.__winampObj.getPlaylistFilenames()
		resL = []
		try:
			resL = [zlib.crc32(a.encode('raw_unicode_escape')) for a in l]	
		except:
			pass
		return 	resL	
		
	def get_cur_pl_key_crc32(self):
		l = self.__winampObj.getPlaylistFilenames()
		checkCrc32 = zlib.crc32(str(l))	
		return checkCrc32		
		
	def closeWinamp(self):
		return self.__winampObj.closeWinamp()	

	def rewind(self):
		if self.__winampObj.getPlaybackStatus() == 1:
			self.__winampObj.setPlayingTrackPosition(self.__winampObj.getPlayingTrackPosition()-10000)
		return self.get_status()	
		
	def set_position_within_the_track(self,pos):
		if self.__winampObj.getPlaybackStatus() == 1:
			self.__winampObj.setPlayingTrackPosition(pos*1000)
		return self.get_status()		
		
	def forward(self):
		if self.__winampObj.getPlaybackStatus() == 1:
			self.__winampObj.setPlayingTrackPosition(self.__winampObj.getPlayingTrackPosition()+10000)
		return self.get_status()			
		
def DistinctAlbums_from_playlist(playlist):
	logger.debug( "in DistinctAlbums_from_playlist, len PlayListL:[%s] - Start"%(str(len(playlist))))
	# Только на основе данных плейлиста функция возвращает словарь альбомов из плейлиста и песен в каждом альбоме
	albumD = {}
	index=0
	album_order_numb =0
	for a in playlist:
		#index = playlist.index(a)
		#print index
		
		pos_2 = a.rfind('\\')
		pos_1 = a[:pos_2-2].rfind('\\')+1
		#album = a[pos_1:pos_2]
		try:
			album_key = zlib.crc32(a[0:pos_2].encode('raw_unicode_escape'))
		except UnicodeEncodeError as e:
			#print 'Decode error:',a
			logger.critical("Error:%s,%s"%(str(e),a))
			continue
			
		#print album

		if album_key not in albumD:
			albumD[album_key] = {'firstFileIndex':index,'albumL':[(a[a.rfind('\\')+1:],index)],'album_order_numb':album_order_numb}
			album_order_numb +=1
			#print a[a.rfind('\\')+1:]
		else:
			albumD[album_key]['albumL'].append((a[a.rfind('\\')+1:],index))
		index+=1	
	
	logger.debug( "in DistinctAlbums_from_playlist - Finished")	
	return 	albumD	



		
if __name__ == '__main__':
	
	PlayerContr_serv = PlayerController()
	PlayerContr_serv.runPlayerServer()
	
