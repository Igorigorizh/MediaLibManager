# # -*- coding: cp1251 -*-
#-*- coding: utf-8 -*-
#import  wx

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import time
import base64

from myMediaLib_init import readConfigData
from myMediaLib_init import loadTemplates_viaCFG
from myMediaLib_init import loadCommandRouting

from myMediaLib_model import MediaLibPlayProcess_singletone_Wrapper

import pickle
import zlib
import sqlite3
import datetime
import os
import io
from os.path import join
import operator
from os import curdir, sep,getcwd
import socket
import asyncio

from mpd.asyncio import MPDClient
from ipaddress import ip_address

import cProfile
import pstats

from myMediaLib_adm import getMedialibDb_Indexes
from myMediaLib_adm import createPlayList_fromMetaDataD
from myMediaLib_adm import Tag_Assignement_and_save
from myMediaLib_adm import getCurrentMetaData_fromDB_via_pL_pos
from myMediaLib_adm import getCurrentMetaData_fromDB_via_DbIdL
from myMediaLib_adm import get_all_artists_in_metaD

from myMediaLib_adm import createPlayList_viaTagId
from myMediaLib_adm import createPlayList_viaAlbumCRC32
from myMediaLib_adm import createPlayList_viaArtistCRC32
from myMediaLib_adm import createPlayList_viaTrackCRC32L
from myMediaLib_adm import createPlayList_viaTagId_cast
from myMediaLib_adm import createPlayList_viaAlbumCRC32_cast

from myMediaLib_adm import getDbIDL_via_CRC32L

from myMediaLib_adm import createNewTag_inDB
from myMediaLib_adm import getTrackList
from myMediaLib_adm import getCurrentMetaData_fromDB_via_CRC32L
from myMediaLib_adm import searchMediaLib_MetaData
from myMediaLib_adm import saveArtistD_intoDB
from myMediaLib_adm import saveAlbum_simple_intoDB
from myMediaLib_adm import saveAlbum_intoDB_via_artistD
from myMediaLib_adm import findTags_via_TrackId
from myMediaLib_adm import findCateg_via_ObjectId
from myMediaLib_adm import DistinctAlbums_from_metaD
from myMediaLib_adm import get_AllTags_asDic
from myMediaLib_adm import getDbIdL_viaTagId
from myMediaLib_adm import getArtistDbIdL_viaTagId
from myMediaLib_adm import Tag_Assignement_delta_update
from myMediaLib_adm import triggerBatchJob_via_event
from myMediaLib_adm import delete_Empty_Tag_inDB
from myMediaLib_adm import getAll_Main_Artist_fromDB
from myMediaLib_adm import get_artist_ref_relation_type
from myMediaLib_adm import getArtistD_fromDB
from myMediaLib_adm import getAlbumD_fromDB
from myMediaLib_adm import getAll_Related_to_main_Artist_fromDB
from myMediaLib_adm import artist_album_categorisation_and_save
from myMediaLib_adm import getArtistAlbum_indexL_viaCategId
from myMediaLib_adm import checkReplicaMapping
from myMediaLib_adm import getCoverPage
from myMediaLib_adm import getArtist_Album_metaD_fromDB
from myMediaLib_adm import getAlbumArtist_dbId_CRC32_mapping

from myMediaLib_adm import getArtist_Album_relationD_and_simpleMetaD_viaCRC32L
from myMediaLib_adm import artist_album_categorisation_delete
from myMediaLib_adm import getArtist_Album_list_db_via_search_term
from myMediaLib_adm import getAlbum_list_db_via_AAT_search_term
from myMediaLib_adm import restore_Album_Artist_relation
from myMediaLib_adm import delete_Album_Artist_relation
from myMediaLib_adm import set_Albums_relation
from myMediaLib_adm import delete_album_via_DbIdL
from myMediaLib_adm import delete_Albums_relation
from myMediaLib_adm import set_Artist_relation
from myMediaLib_adm import delete_Artist_relation

from myMediaLib_adm import delete_Artist

from myMediaLib_adm import check_loaded_albums_2_lib
from myMediaLib_adm import getDbIdL_viaAlbumCRC32_List
from myMediaLib_adm import collect_images_for_album
from myMediaLib_adm import getFolderAlbumD_fromDB

from myMediaLib_adm import getDbIdL_viaAlbumCRC32
from myMediaLib_adm import getCurrentMetaData_fromDB_via_DbIdL_alterntv
from myMediaLib_adm import getAlbum_parentObjects

from myMediaLib_adm import getArtist_relation_metaD
from myMediaLib_adm import getAlbum_relation_metaD
from myMediaLib_adm import modifyArtist_viaCRC32
from myMediaLib_adm import modifyAlbum_viaCRC32
from myMediaLib_adm import getDbIdL_w_folderL_filter
from myMediaLib_adm import get_discs_duplacates
from myMediaLib_adm import saveLibClast_to_DB_unicode
from myMediaLib_adm import delete_tracks_via_DbIdL
from myMediaLib_adm import validate_ArtistAlbumLibClast_from_DB

from myMediaLib_adm import getCategoryProfileDic
from myMediaLib_adm import registerRadio
from myMediaLib_adm import mediaLib_intoDb_Load_withUpdateCheck
from myMediaLib_adm import getFolderPathL_fromDB_viaTermL

from myMediaLib_mpd import load_mpd_playlist_via_tag_num
from myMediaLib_mpd import load_mpd_playlist_viaTrackCRC32L
from myMediaLib_mpd import load_mpd_playlist_via_pathL
from myMediaLib_mpd import check_update_mpd_db
from myMediaLib_mpd import get_mpd_playlist_as_crc32L

from myMediaLib_mpd import get_mpd_status
from myMediaLib_mpd import get_mpd_playlistinfo

from myMediaLib_tools import find_new_music_folder
from myMediaLib_tools import identify_music_folder
from myMediaLib_tools import get_parent_folder_stackL

from myMediaLib_cue import generate_play_list_from_fileData

from PIL import Image
import json
import logging

from myMediaLib_CONST import BASE_ENCODING
from myMediaLib_CONST import mymedialib_cfg

def is_ip(address):
    return address.replace('.', '').isnumeric()

class MediaLib_Controller(MediaLibPlayProcess_singletone_Wrapper):
	def __init__(self):
	
		# вызываем явно конструктор родителя, чтобы в этом классе иметь доступ к атрибутам родителя
		# таким образом инстанция контролера является одновременно инстанцией модели, зачем это???? 
		# это сделано на начальном этапе чтобы минимально изменять старый код, когда в модели был реализовани контроллер 
		# напрямую. в будущем сделать в модели методы, которые выдавали бы соответсвущие объекты модели 
		#super(MediaLib_Controller, self).__init__()
		
		# Одной из необходимых задач контроллера MVC должна быть поодержка модели в актуальном состоянии
		# эти функции небоходимо перенести сюда из старой фукции генерации страниц
		#global logger
		self.__logger = logging.getLogger('controller_logger')
		#logger = self.__logger
		self.__logger.setLevel(logging.DEBUG)
		# create file handler which logs even debug messages
		configDict = readConfigData(mymedialib_cfg)
		
		logPath='no Path'
		
		try:
			logPath=configDict['logPath']
		except Exception as e:
			print(e)
			
		
		#fh = logging.FileHandler('spam.log')
		fh = logging.FileHandler(logPath,'a', 'utf-8')
		fh.setLevel(logging.ERROR)
		#fh.setLevel(logging.DEBUG)
		# create console handler with a higher log level
		ch = logging.StreamHandler()
		ch.setLevel(logging.CRITICAL)
		#ch.setLevel(logging.DEBUG)
		
		# create formatter and add it to the handlers
		formatter = logging.Formatter('%(asctime)s - %(name)25s - %(levelname)s - %(message)50s')
		ch.setFormatter(formatter)
		fh.setFormatter(formatter)
		
		self.__logger.addHandler(ch)
		self.__logger.addHandler(fh)
		
		MediaLibPlayProcess_singletone_Wrapper.__init__(self)
		self.__model_instance = self.get_instance()
		self.__player_handler = self.__model_instance.get_player_control_handler()
		pc = {'list_length':0}
		if self.__model_instance.isPlayerAlive():
			try:
				pc = self.__player_handler.get_status()
			except Exception as e:
				print(e)	
			if 'list_length' in pc: 
				if pc['list_length'] == 0:
					mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']
					playlistpath = mediaPath + 'Plugins\\ml\\'
					#self.__player_handler.new_list_load(playlistpath+'queuePL.m3u',0)
					
					self.__player_handler.new_list_load(playlistpath+'tag_play.m3u',0)
				
		
		self.__modelDic = {}
		
		try:
			self.__logger.info('View instance Initialiazin')
			self.__instance_VIEW = MediaLib_ViewGen()
		except:
			from myMedialib_view import MediaLib_ViewGen
			self.__instance_VIEW = MediaLib_ViewGen()
		
		ignor_namesL = ['__doc__', '__module__', 'self_func']
		self.__signatura_list_CONTROLLER = [a for a in dir(self) if a not in ignor_namesL]
		
		# Получить список сигнатур класса генератора представления MediaLib_ViewGen
		self.__signatura_list_VIEW = [a for a in dir(self.__instance_VIEW) if a not in ignor_namesL]
		
				
		self.__logger.debug('signatura_list_VIEW:%s'%(str(self.__signatura_list_VIEW)))
		# в этом словаре содержаться связи:
		#		идентификатора отработавшего элемента управления:
						#'player_control'- базовые функции плеера
						# "navigation_control" - загрузка новых листов и навигация по листам с необходимой реакцией плеера(листы, тэги)
		# 		метода изменения состояния муз плеера и  модели отражающей его состояние. 
		#		списка элементов представления требующих обновления, спи
		self.__commandRoutingDic = self.__model_instance.MediaLibPlayProcessDic_viaKey('commandRouting','local')
		if self.__commandRoutingDic != {}:
			
			
			self.__logger.debug('commandRouting is OK:%s'%(str(list(self.__commandRoutingDic.keys()))))
		else:
			
			self.__logger.error('#Command routing#  is not imported:%s'%(str(self.__commandRoutingDic)))
			return
						
								  		  
	def get_modelDic(self,view_elem_id_Dic,PlayControl_CurStatusD):
		# Интерфес к модели: метод применяется для того чтобы получить из модели данные характеризующие состояние плеера и приложения
		# тут не предпологается никаких вычислений, только получение уже готовый структур
		# извлечение и вычисление происходят например в функции get_data_for_player_context
		
		self.__logger.info('in begin of get_modelDic [%s] START OK.'%(str(list(view_elem_id_Dic.keys()))))
		modelDic = self.__modelDic
		
		#if 'curState' in view_elem_id_Dic or 'play_status'in view_elem_id_Dic:
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		self.__logger.debug('get_modelDic tracking--->')
		cnt = 0
		if 'tag_name' in view_elem_id_Dic:
			self.__logger.debug('-------tracking------>tag_name')
			try:
				# в данном случае ожидается что переменная PlayControl_CurStatusD имеет значение возвращенное из метода контроллера int
				if type(PlayControl_CurStatusD) == int:
					res = PlayControl_CurStatusD
					modelDic['tag_name'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[res]['tag_name']
					self.__logger.debug('tag_name=',modelDic['tag_name'])
					
			except Exception as e:
				self.__logger.critical('Exception in get_modelDic for tag_name %s'%(modelDic['tag_name']))
				modelDic['tag_name'] = 'NA_'
			cnt=1
			
		if 'search_res_buf' in view_elem_id_Dic:
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			modelDic['SearchBufD'] = self.__model_instance.getSearchBufD()
			modelDic['TagD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			
			# Сгенерируем словарь тэгов tagsLDic для связанных с ними композиций. Генерируем динамически, теоретически это можно перенести в контруктор.
			tagsLDic =  {}
			DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')	
			
			# Генерируем словать соответствий индексов трэков в БД и их СРЦ32	
			DB_metaIndxD_inverted = {}
			for a in DB_metaIndxD:
				DB_metaIndxD_inverted[DB_metaIndxD[a][0]] = a
				
			tagsLDic = get_AllTags_asDic(dbPath,DB_metaIndxD_inverted)
			
			
			self.__logger.debug('search_res_buf get is OK')
			
			modelDic['tagsLDic'] = tagsLDic
			
		if 'search_res_buf_image' in view_elem_id_Dic:
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			modelDic['SearchBufD'] = self.__model_instance.getSearchBufD()
			modelDic['TagD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			
			# Сгенерируем словарь тэгов tagsLDic для связанных с ними композиций. Генерируем динамически, теоретически это можно перенести в контруктор.
			tagsLDic =  {}
			DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')	
			
			# Генерируем словать соответствий индексов трэков в БД и их СРЦ32	
			DB_metaIndxD_inverted = {}
			for a in DB_metaIndxD:
				DB_metaIndxD_inverted[DB_metaIndxD[a][0]] = a
				
			tagsLDic = get_AllTags_asDic(dbPath,DB_metaIndxD_inverted)
			
			
			self.__logger.debug('search_res_buf_image get is OK')
			
			modelDic['tagsLDic'] = tagsLDic	
			
		if 'albumD'	 in view_elem_id_Dic:
			# Нужен вроде для выдачи картинок, и формирования дропдаун листа альбомов
			modelDic['DB_metaIndxD_album'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD_album','local')
			self.__logger.debug('albumD get is OK')
			
		if 'tag_adm_search_res_buf' in view_elem_id_Dic:
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			modelDic['SearchBufD'] = self.__model_instance.getSearchBufD()	
			
			self.__logger.debug('tag_adm_search_res_buf get is OK')
			
		if 	'artist_search_res_buf' in view_elem_id_Dic:
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			modelDic['ReportBufD'] = self.__model_instance.getReportBuf_forArtist()
			self.__logger.debug('artist_search_res_buf get is OK')
			
		if 	'artist_search_vars' in view_elem_id_Dic:	
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			# в данном случае ожидается что переменная PlayControl_CurStatusD имеет значение возвращенное из метода контроллера [list]
			view_elem_id_Dic['artist_search_vars']=PlayControl_CurStatusD
			self.__logger.debug('artist_search_vars get is OK')
			
		if 	'artist_search_vars_opt' in view_elem_id_Dic:	
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			# в данном случае ожидается что переменная PlayControl_CurStatusD имеет значение возвращенное из метода контроллера [list]
			view_elem_id_Dic['artist_search_vars_opt']=PlayControl_CurStatusD	
			self.__logger.debug('artist_search_vars_opt get is OK')
		if 'debug' in view_elem_id_Dic:
			pass
		
		if 'gen_page_elements' in view_elem_id_Dic:
			#print 'in gen_page_elements of get_modelDic'
			#if '192.' in socket.gethostbyname(socket.gethostname()):
			#	modelDic['host'] = socket.gethostbyname(socket.gethostname())
			#else:
			#	modelDic['host'] = socket.gethostname()
			print('*'*10)
			print('****************************************in gen_page_elements of get_modelDic:',modelDic['host'])	
			#port = int(self.__configDict['player_cntrl_port'])
			modelDic['host_name'] = modelDic['host']+'/medialib'
			modelDic['html_title'] = 'Music Navigation System'
			modelDic['host_image_name'] = modelDic['host']+'/images'
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			self.__logger.info('344: gen_page_elements get is OK, host: %s'%modelDic['host'])
			
		if 'change_delta_list' in view_elem_id_Dic:
			modelDic['Search_Editable_BufD'] = self.__model_instance.getSearch_editable_BufD()
			self.__logger.debug('change_delta_list get is OK')
			
		if 'admin_page_elements'	in view_elem_id_Dic:
			try:
				modelDic['templatesD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['templatesD']
			except Exception as e:
				self.__logger.critical('Excepption in admin_page_elements in get_modelDic:%s'%e)
				modelDic['templatesD'] = {}
			
			
			try:
				DbIdL=getDbIdL_viaTagId(455,None)
				metaD = getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None)	
				modelDic['radio_statDL'] = []
				for a in metaD:
					modelDic['radio_statDL'].append({'key':metaD[a]['id_track'],'station_name':metaD[a]['title']})
				modelDic['radio_statDL'].sort(key=operator.itemgetter('station_name'))
				
			except Exception as e:
				self.__logger.critical('Excepption in admin_page_elements for [radio stations] in get_modelDic:%s'%e)
				modelDic['radio_statD'] = {}	
			
			
			try:
				modelDic['RemHPlayerInstanceD'] = self.__model_instance.getRemHPlayerInstanceD()	
			except Exception as e:
				self.__logger.critical('Excepption in admin_page_elements for [RemHPlayerInstanceD] in get_modelDic:%s'%e)
				modelDic['RemHPlayerInstanceD'] = {}	
				
				
			try:
				if 'mpd_instanceDL' not in modelDic:
					modelDic['mpd_instanceDL'] = []
				
					cfgD = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')
					mpdDL = cfgD['mpd_host_list']
					for item in mpdDL:
						modelDic['mpd_instanceDL'].append({'key':item['host'],'instance_name':item['host'],'socket':item['socket']})
				
				
			except Exception as e:
				self.__logger.critical('Excepption in admin_page_elements for [radio stations] in get_modelDic:%s'%e)
				modelDic['mpd_instanceDL'] = []
				
			self.__logger.debug('admin_page_elements get is OK')
			
		if 'cfgD'	in view_elem_id_Dic:
			try:
				modelDic['cfgD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')
			except Exception as e:
				self.__logger.critical('Excepption in debug_page_elements in get_modelDic:%s'%e)
				modelDic['templatesD'] = {}
			self.__logger.debug('debug_cfgD get is OK')	
			
		if 'tagAdmin_page_elements'	in view_elem_id_Dic:
			try:
				modelDic['TagD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			except  Exception as e:
				self.__logger.critical('Excepption in Tagadmin_page_elements in get_modelDic:%s'%e)
				
				modelDic['TagD'] = {}
			self.__logger.debug('tagAdmin_page_elements get is OK')
			
		if 'graf_input_data_tag'	in view_elem_id_Dic:
			try:
				modelDic['TagD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			except  Exception as e:
				
				self.__logger.critical('Excepption in graf_input_data_tag in get_modelDic:%s'%e)
				modelDic['TagD'] = {}
			
			self.__logger.debug('graf_input_data_tag get is OK')
			
		if 'category_data' in view_elem_id_Dic or 'style_claster_groupL' in view_elem_id_Dic:
			modelDic['cat_profD'] = getCategoryProfileDic(dbPath,'list_item_like','general_cat_folder')['cat_prof_itemDL']	
		
		if 'mpdHostL' in view_elem_id_Dic:
			modelDic['mpdHostDL'] = self.__model_instance.getPlayerInstanceList()
			try:
				if 'mpd_instanceDL' not in modelDic:
					modelDic['mpd_instanceDL'] = []
				
					cfgD = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')
					mpdDL = cfgD['mpd_host_list']
					for item in mpdDL:
						modelDic['mpd_instanceDL'].append({'key':item['host'],'instance_name':item['host'],'socket':item['socket']})
				
				
			except Exception as e:
				self.__logger.critical('Excepption in admin_page_elements for [radio stations] in get_modelDic:%s'%e)
				modelDic['mpd_instanceDL'] = []
			
			
			
			
		if 'graf_input_data_navi'	in view_elem_id_Dic or 'style_claster_groupL' in view_elem_id_Dic:
		
			modelDic['cat_profD'] = getCategoryProfileDic(dbPath,'list_item_like')['cat_prof_itemDL']
			try:
				modelDic['plGroupD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('group2PlayListD','local')['groupD']
				#print modelDic['plGroupD']
			except  Exception as e:
				
				self.__logger.critical('Excepption in graf_input_data_navi in get_modelDic:%s'%e)
				modelDic['plGroupD'] = {}
				
				
			self.__logger.debug('graf_input_data_navi get is OK')
				
		if 'main_page_elements'	in view_elem_id_Dic:
			modelDic['pD_crc32'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('pD_crc32','local')
			modelDic['pD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('pD','local')
			modelDic['group2PlayListD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('group2PlayListD','local')
			self.__logger.debug('main_page_elements get is OK')
		
		if 'cast_frame3' in view_elem_id_Dic:
			# Получаем  содержимое листа от контроллера плеера
			print('cast_frame3 -1')
			modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
			print('cast_frame3 -2')
			DB_metaIndxD_obratn= self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD_obratn','local')	
			print('cast_frame3 -3')
			CastPlayList = self.__model_instance.get_CastPlayList(self.__modelDic['REMOTE_ADDR'])	
			print('cast_frame3 -4',list(CastPlayList.keys()),CastPlayList['cur_track_id'])
			#print (CastPlayList['cur_track_id'] in DB_metaIndxD_obratn)
			#for a in DB_metaIndxD_obratn:
			#	print a,DB_metaIndxD_obratn[a]
			#	break
			try:
				cur_crc32 = 9999999
				#cur_crc32 = DB_metaIndxD_obratn[CastPlayList['cur_track_id']]
				print('-!!!!!!!--- Uncoment to fix a bug')
			except  Exception as e:
				self.__logger.critical('Excepption in cast_frame3 in get_modelDic:%s'%e)
				cur_crc32 = 99999
			#print 'cur_crc32:------------------------------',cur_crc32,
			print((cur_crc32 in CastPlayList['metaD']),'-------<<<<')
			modelDic['CastPlayListD'] = CastPlayList	
			modelDic['cur_crc32'] = cur_crc32	
			modelDic['cast_albumD'] = DistinctAlbums_from_metaD(CastPlayList['metaD'],CastPlayList['crc32L'])
			self.__logger.debug('cast_frame3 get is OK')
			
		if 'frame3' in view_elem_id_Dic or 'trackL' in view_elem_id_Dic or 'albumL' in view_elem_id_Dic:
			if 'oldvers' in view_elem_id_Dic:
			# Получаем  содержимое листа от контроллера плеера
				l_data = zlib.decompress(self.__player_handler.get_cur_pl_as_list().data)
				modelDic['PlayListL'] = pickle.loads(l_data)
				modelDic['Tmpl'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('Tmpl','local')
				self.__logger.debug('frame3 get is OK')

				
		
		if 'cast_tagsL' in view_elem_id_Dic:
			#print 'Tagd prepare'
			tagsL = []
			TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			CastPlayList = self.__model_instance.get_CastPlayList(self.__modelDic['REMOTE_ADDR'])	
			curDbId = CastPlayList['cur_track_id']
			
			tagsL = findTags_via_TrackId(dbPath,curDbId)
			modelDic['tagsL']	= tagsL
			modelDic['TagD']	= TagD
			
			self.__logger.debug('cast_tagsL get is OK')
		
		if 'categL' in view_elem_id_Dic:
			#print 'Tagd prepare'
			categL = []
			
		if 'tagsL' in view_elem_id_Dic:
			#print 'Tagd prepare'
			tagsL = []
			TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
			DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')	
			try:
				curDbId = DB_metaIndxD[PlayControl_CurStatusD['track_CRC32']][0]
			except KeyError as e:
				
				self.__logger.critical('Excepption KeyError in 381 tagsL in get_modelDic:%s'%(str(e)))
				curDbId = 0
			except Exception as e:
				self.__logger.critical('Excepption  in tagsL in 384 get_modelDic:%s'%str(e))
				curDbId = 0
			
			try:
				tagsL = findTags_via_TrackId(dbPath,curDbId)
			except Exception as e:
				self.__logger.critical('Excepption  in tagsL in 388 get_modelDic:%s'%str(e))	
				
				
			modelDic['tagsL']	= tagsL
			modelDic['TagD']	= TagD
			tagsDL = {}
			modelDic['tagsDL'] = []
			for a in tagsL:
				
				if a in TagD:
					if TagD[a]['tag_type'] == 'SYSTEM':
						continue
					tags_item = {'tagType':TagD[a]['tag_type'],'tagId':a,'tagName':TagD[a]['tag_name']}
					
					if TagD[a]['tag_type'] not in tagsDL:
						tagsDL[TagD[a]['tag_type']] = [{'tagId':a,'tagName':TagD[a]['tag_name']}]
					else:
						tagsDL[TagD[a]['tag_type']].append({'tagId':a,'tagName':TagD[a]['tag_name']})
			#print 'ZZZZZZ----->'
			if tagsDL != {}:
				for tag_type in tagsDL:
					item = []
					for tag in tagsDL[tag_type]:
						#print tag
						item.append({'tagId':tag['tagId'],'tagName':TagD[tag['tagId']]['tag_name']})
					#print tag_type	
					modelDic['tagsDL'].append({'tag_type':tag_type,'item':item})
				
			
			if 'cur_track_in_album_pos' not in modelDic:
				cur_stateDic = self.__model_instance.getMediaLibPlayProcess_State()
				modelDic['cur_track_in_album_pos'] = cur_stateDic['songNum']-cur_stateDic['albumNum']
			
			
			#print 'tagsL=',modelDic['tagsL']
			self.__logger.debug('tagsL get is OK')
		
		if 'cast_trackL' in view_elem_id_Dic or 'cast_albumL' in view_elem_id_Dic:		
			modelDic['DB_metaIndxD_album'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD_album','local')
			self.__logger.debug('cast_trackL get is OK')
			
		if 'track_pos' in view_elem_id_Dic:
			#print
			#print 'track changed!...............',view_elem_id_Dic['track_pos']
			#print PlayControl_CurStatusD['pl_pos']
			#delta = view_elem_id_Dic['track_pos_changed'] - PlayControl_CurStatusD['pl_pos']
			#modelDic['cur_track_in_album_pos'] = view_elem_id_Dic['track_pos']
			
			#print modelDic['cur_track_in_album_pos']
			pass
			
			
		if 'trackL' in view_elem_id_Dic or 'albumL' in view_elem_id_Dic:
			if 'oldvers' in view_elem_id_Dic:
				pass
				#modelDic['albumD'] = myMediaLib.DistinctAlbums_from_playlist_withCueCheck(modelDic['PlayListL'])
			else:
				if 'playerMData' not in view_elem_id_Dic:
					print('prackkkkk!...............',list(view_elem_id_Dic.keys()))
					if 'trackL' in view_elem_id_Dic and self.__model_instance.isPlayerAlive():
						self.get_data_for_player_context(PlayControl_CurStatusD,modelDic,view_elem_id_Dic)
						
					if 'albumL' in view_elem_id_Dic:
						view_elem_id_Dic['playerMData']=''
					
				
				
			self.__logger.debug('trackL get is OK')
			
		if 'queueL'	in view_elem_id_Dic:
			modelDic['PlayListQueueD'] = self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueueD']
			modelDic['PlayListQueue'] = self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueue']
			self.__logger.debug('queueL get is OK')
			
			
		if 'playerMData' in view_elem_id_Dic and self.__model_instance.isPlayerAlive():
		
			self.get_data_for_player_context(PlayControl_CurStatusD,modelDic,view_elem_id_Dic,'album_initial')
			
			self.__logger.debug('playerMData get is OK')
			

			
			
		if 'frame3' in view_elem_id_Dic:
			
			modelDic['metaD_of_cur_pL'] = self.__model_instance.MediaLibPlayProcessDic()['metaD_of_cur_pL']
			
			try:
				modelDic['PlayList_asCRC32_L'] = [zlib.crc32(a.encode(BASE_ENCODING)) for a in modelDic['PlayListL']]	
			except Exception as e:
				self.__logger.critical('Excepption  in frame3 in get_modelDic:%s'%e)
			self.__logger.debug('frame3 get is OK')
			
		if 'current_Album_order_Indx' in modelDic:
			print() 
			print('>>>>>>>>>>>>>>   current_Album_order_Indx:',modelDic['current_Album_order_Indx'])
		
		self.__logger.info('in GetmodelDic - FINISHED-OK')
		return modelDic
	
	def get_audio(self,id,format,*attr):
		
		self.__logger.info('!!! in get_audio: is Ok %s %s'%(str(id),str(format)))
		#raw_input('press any key')
		replica_mapD = {'orig':'ORIGINAL_MUSIC','repl':'REPLICA_'+format.upper()}
		if format.lower() == 'ogg':
			
			replica_mapD = {'orig':'ORIGINAL_MUSIC','repl':'REPLICA_'+format.upper()+'_96'}
		audio = ""
		
		
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
		#db.text_factory = str
		c = db.cursor()
		req = 'select path,path_crc32,cue_num from track where id_track = %s'%(str(id))
			
		c.execute(req)
		
	#print req

		l =c.fetchone()
		#print l
		
		c.close()
		db.close()
		
		
		metaD = getCurrentMetaData_fromDB_via_DbIdL([id,],None)
		#print 'in audio 2'
		#print metaD
		audio_path = l[0]
		cue_num = l[2]
		path_crc32 = l[1]
		
		
		self.__logger.debug('!!! in get_audio: before replicka: %s '%(str(audio_path)))
		if '.mp3' not in audio_path and '.flac' not in audio_path:
			checkD = {'message':'','track':None}
			#print replica_mapD
			checkD = checkReplicaMapping(metaD[path_crc32],format.lower(),replica_mapD)
			#print checkD
			#print 'in audio 3'
			if checkD['message']=='OK' or checkD['message'] == 'outdated':
				audio_path = checkD['track']
			else:
				audio_path = "G:\MUSIC\REPLICA_MP3\ORIGINAL_CDTEST\VA  Denon - Digital Sound Of The Future (Test CD)\(02). Balance and Phase Check.mp3"
				#print 'new path = ',audio_path
			
		# попытаемся взять реплику.
		
		#print "path =", audio_path
		if os.path.exists(audio_path):
			print('audio_path:',audio_path)
			return audio_path
			fileObj = open(audio_path,'rb')
			audio = fileObj.read()
			fileObj.close()
			#print "Path is ok len=",audio_path,len(audio)
		return 	
		return xmlrpc.client.Binary(audio)	
	
	def command_dispatcher(self,signatura_pool,*attr):
		print("In command dispatcher now !",signatura_pool)
		pc = None
		modelStateDic = {}
		
		do_profile = False
		
		self.__modelDic['host'] = socket.gethostname()
		self.__modelDic['host_name'] = self.__modelDic['host']+'/medialib'
		self.__modelDic['host_image_name'] = self.__modelDic['host']+'/images'
		self.__modelDic['user_agent'] = ''
		
		if attr != ():
			if type(attr[0]) == dict:
				if 'REMOTE_ADDR' in attr[0]:
					self.__modelDic['REMOTE_ADDR'] = attr[0]['REMOTE_ADDR']
	
				if  'HTTP_HOST' in attr[0]:
					try:
                        
						ip_address(attr[0]['HTTP_HOST'])
						self.__modelDic['host'] = socket.gethostbyname(self.__modelDic['host'])
						self.__modelDic['host_name'] = self.__modelDic['host']+'/medialib'
						self.__modelDic['host_image_name'] = self.__modelDic['host']+'/images'
					except ValueError as e:
						print('Error in dispatcher:'+str(e))
                        
					if  'localhost' in attr[0]['HTTP_HOST'].lower():
						self.__modelDic['host'] = attr[0]['HTTP_HOST']
						self.__modelDic['host_name'] = self.__modelDic['host']+'/medialib'
						self.__modelDic['host_image_name'] = self.__modelDic['host']+'/images'
						self.__modelDic['user_agent'] = ''
                
				if  'SERVER_NAME' in attr[0] and 'SERVER_ADDR' in attr[0]:
					if attr[0]['SERVER_NAME'] == attr[0]['SERVER_ADDR']:
						# addressing py IP
						pass
					elif attr[0]['SERVER_NAME'] != attr[0]['SERVER_ADDR']:
						if is_ip(attr[0]['SERVER_NAME']):
							# addresing by ip and we are in isolated network inside Docker bridge     
							# return parent ip back from ['SERVER_NAME'] 
							self.__modelDic['host'] = attr[0]['SERVER_NAME']
							self.__modelDic['host_ name'] = self.__modelDic['host']+'/medialib'
							self.__modelDic['host_image_name'] = self.__modelDic['host']+'/images'
							self.__modelDic['user_agent'] = ''
							print('GitHub Bridge:',self.__modelDic['host'])
											
				if  'HTTP_USER_AGENT' in attr[0]:
					self.__modelDic['user_agent'] = attr[0]['HTTP_USER_AGENT']	
		print('*'*50)
		self.__logger.info('699: gen_page_elements get is OK, host: %s, uaser_agent:%s'%(self.__modelDic['host'],self.__modelDic['user_agent']))
		listType = listDescr = ''
		
		#print dir(self)
		
		self.__logger.debug('signatura_pool: %s, attr: %s'%(str(signatura_pool),str(attr)))
		
		signatura = None
		signatura_group = None
		command = None
		http_Reply = ''
		self.__commandRoutingDic = self.__model_instance.MediaLibPlayProcessDic_viaKey('commandRouting','local')
		# Ниже в цикле определяем методы представления и методы контроллера сответствующие запросу через схему self.__commandRoutingDic
		for a in signatura_pool:
			
			if a in self.__commandRoutingDic:
				command = signatura_pool[a]
		#		print 'command=',command
				if command not in self.__commandRoutingDic[a]:
					
					self.__logger.error("command not yet defind:%s"%(str(command)))
					continue
					
				if 'model_update_method' in self.__commandRoutingDic[a][command]:	
					signatura = self.__commandRoutingDic[a][command]['model_update_method']
					
		#		print 'signatura?=',signatura
				signatura_view_method = self.__commandRoutingDic[a][command]['view_method']
				view_elemD = self.__commandRoutingDic[a][command]['view_elem_id_Dic'].copy()
				if 'cover' in view_elemD:
					view_elemD['cover'] = 0
				
				self.__logger.debug('Found command for command_group:%s -->%s,%s'%(str(a),str(signatura),str(signatura_view_method)))
				break
		if 	signatura == None:
			
			self.__logger.error('Commands not in command routing or not a model_update_method:%s'%(str(signatura_pool)))
			return 0
		
		#print 'attr =',attr
		
		ignor_namesL = ['__doc__', '__module__', 'self_func']
		
		#print '-->1',a,signatura
		# Так как диспетчер универсальный то данные проверки релевантны только для процесса контроля плеера
		if 'logic_process' in self.__commandRoutingDic[a][command]:
			if 'player_state' in self.__commandRoutingDic[a][command]['logic_process']:
				
				self.__logger.debug('player_state -->1.3 %s'%str((list(self.__commandRoutingDic[a][command].keys()))))
				#сохранить текущее состояние модели
				old_stateDic = self.__model_instance.getMediaLibPlayProcess_State()
				old_stateDic['playBack_Mode'] = 1
				print( '759 old_stateDic song key:%s'%str(old_stateDic))
		
		# Вызвать необходимый метод контроллера, - модификация модели в соответствии с данной командой и тек. состоянием плеера
		# в зависимости от запроса вызываем метод с параметрами или без
		if signatura in self.__signatura_list_CONTROLLER:
			if len(signatura_pool)>1:
				#print 'Doing:',signatura,signatura_pool
				if do_profile:
					try:
						cProfile.run("pc = getattr(self,signatura)(signatura_pool)", '_profile_control_meth1') 
						print('profile OK')
					except Exception as e:
						print(e)
				else:	
					pc = getattr(self,signatura)(signatura_pool)
			else:
				#print 'Doing:',signatura
				if do_profile:
					cProfile.run("pc = getattr(self,signatura)()",  '_profile_control_meth1') 
				else:	
					pc = getattr(self,signatura)()
				
				#print 'status2=',dir(self.__instance_VIEW)
				
		else: 
			
			self.__logger.info(' Not yet a method of MediaLib_Controller, signatura = player_state -->1.3 %s'%str((signatura)))
			return 0
		
		
		self.__logger.debug('Before logic_process check:%s'%(str(self.__commandRoutingDic[a][command])))
		# Так как диспетчер универсальный то данные проверки релевантны только для процесса контроля плеера
		if 'logic_process' in self.__commandRoutingDic[a][command] and self.__model_instance.isPlayerAlive():
			if 'client_merge' in self.__commandRoutingDic[a][command]['logic_process']:
				#print "------------------------- Client merge",signatura_pool
				if 'client_state' in signatura_pool:
					if pc == None:
						pc = self.__player_handler.get_status()
					#print type(signatura_pool['client_state'])	
					#client_state = json.loads(signatura_pool['client_state'])
					client_state = signatura_pool['client_state']
					dum  = self.client_layout_merge('client',client_state,pc,view_elemD)	
			if 'player_state' in self.__commandRoutingDic[a][command]['logic_process']:
				#print '-->3'
				listType = listDescr = "!!!"
				
				# Проверить произошло ли изменение текущего альбома если да то в генерации для генерации вью запросить новый список треков
				cur_stateDic = self.__model_instance.getMediaLibPlayProcess_State()
		
				# Определяем нужно ли переслать картинку альбома
				if 'cover' in view_elemD:
					try:
						cover_res = self.__model_instance.check_updadeCoverPage_change_state()
					except:
						print('Error With cover: brobalby the list is empty')
						cover_res = 0
					if cover_res == 1:
						self.__logger.info('Send page OK')
						
						view_elemD['cover'] = 1
					else:
						view_elemD['cover'] = 0
				
					
				if pc == None:
					pc = self.__player_handler.get_status()
				#print 
				#print 'albumnunm-----',self.__model_instance.get_current_album_track_num()
		
				if type(pc)	== dict:
					pc['cur_track_in_album_pos'] = 0
					#print '101'
					
				# Блок синхронизации данных плейлиста, его содержимого, его как срц32L представления, и мета данных с ним связанных
				# аналого функции client_layout_merge
					try:	
						if cur_stateDic['curList_crc32'] != pc['pL_CRC32']:
							#print '111'
							# profile  this -------------------------------
							if do_profile:
								cProfile.run("self.__model_instance.RefreshServerContent('play_list_sync',pc)",  '_profile_refresh_meth1') 
							else:	
								print('dispatcher:=============> Refresh player state:')
								self.__model_instance.RefreshServerContent('play_list_sync',pc)
							if 'listType' in pc:
								listType = pc['listType']
								
							if 'listDescr' in pc:
								listDescr = pc['listDescr']	
								
							self.__model_instance.add_new_playList_to_queue(pc['pL_CRC32'],listType,listDescr)
							
						if pc['pL_CRC32'] in self.__model_instance.MediaLibPlayProcessDic_viaKey('pLQueueD','local')['PlayListQueueD']:	
							self.__model_instance.changePlaylistQueueD_atPos(pc['pL_CRC32'],None,pc['pl_pos'])
							
					except Exception as e:
						self.__logger.critical('Exception:%s'%(str(e)))	
						
					#a_t_numD= self.__model_instance.get_current_album_track_num()
					a_t_numD = self.__model_instance.get_current_Album_Track_context()
					albumNum = 0
					if a_t_numD != None:
						albumNum = a_t_numD['albumNum']	
					self.__model_instance.setSongAlbumNums(pc['pl_pos'],albumNum)
					self.__model_instance.setStopFlag(pc['playBack_Mode'])
		

				# Проверить произошло ли изменение текущего альбома если да то в генерации для генерации вью запросить новый список треков
				pc['cur_track_in_album_pos'] = cur_stateDic['songNum']-cur_stateDic['albumNum']
				print("dispatcher: album positions :",cur_stateDic['songNum'], cur_stateDic['albumNum'])
				
				if old_stateDic['curList_crc32'] != pc['pL_CRC32']:
					self.__logger.debug('Albume change from list change:%s %s'%(str(old_stateDic['curList_crc32']),str(pc['pL_CRC32'])))
					view_elemD['trackL']=''
					view_elemD['albumL']=''
					view_elemD['tagsL']=''
					view_elemD['tplgDL']=''
					view_elemD['obj_categDL']=''
					view_elemD['playerMData']=''
					
					
					
				elif old_stateDic['albumNum'] != cur_stateDic['albumNum']:
					
					self.__logger.debug('Albume change from :%s %s'%(str(old_stateDic['curList_crc32']),str(cur_stateDic['albumNum'])))
					view_elemD['trackL']=''
					view_elemD['tagsL']=''
					view_elemD['tplgDL']=''
					view_elemD['obj_categDL']=''
					#print cur_stateDic.keys()
					
				elif old_stateDic['songNum'] != cur_stateDic['songNum']:
					self.__logger.debug('Track change from :%s %s'%(str(old_stateDic['songNum']),str(cur_stateDic['songNum'])))
					view_elemD['tagsL'] = ''
					#view_elemD['obj_categDL']=''
					#print  "----------->tagsL"
					pass
					
					#print 'diff:',cur_stateDic['songNum'],cur_stateDic['albumNum']
				else:
					print()
					print("---------------aaaaaaaaaaaaaaa NOTHING!!!!!!!!!!!!!")
					print()
					print('old:',old_stateDic['songNum'],old_stateDic['albumNum'])
					print()
					print('cur:',cur_stateDic['songNum'], cur_stateDic['albumNum'])
		
				#print 'before vie1:',signatura_view_method,view_elemD.keys()
				
				modelStateDic = self.__model_instance.getMediaLibPlayProcess_State()
				#print 'before vie2'	,signatura_view_method	
				
		# Перед вызовов метода view MVC необходимо подготовить все управляющие структуры, словари, списки эти элементы мы берем из модели MVC
		# profile  this -------------------------------
		
		if 'current_Album_order_Indx' not in self.__modelDic:
			#self.__modelDic['current_Album_order_Indx'] = self.__model_instance.get_current_Album_order_Indx()
			a_t_numD = self.__model_instance.get_current_Album_Track_context()
			print('1.get_current_Album_Track_context ok:',a_t_numD)
			albumNum = 0
			if a_t_numD != None:
				self.__modelDic['current_Album_order_Indx'] = a_t_numD['album_ord_index']	
				albumNum = a_t_numD['albumNum']	
				self.__model_instance.setSongAlbumNums(a_t_numD['songNum'],albumNum)	
			print('dispatcher: OK2')
		
		#print "new song num:",pc['track_CRC32']
		self.__logger.debug('in command_dispatcher Before get_modelDic 862')
		if do_profile:
			cProfile.run("modelDic = self.get_modelDic(view_elemD,pc)",  '_profile_get_modelDic1') 
		else:	
			modelDic = self.get_modelDic(view_elemD,pc)		
		#print '-->5 %s pc=%s'%(str(signatura_view_method),str(pc))	
		#----------------------
		# Тут происходит вызов метода представления, возвращающего либо готовую страницу либо json ответ для части страницы
		# self.__instance_VIEW - инстанция класса MediaLib_ViewGen (medialib_pages.py)
		# signatura_view_method - метод класса MediaLib_ViewGen автоматически определенный через схему  self.__commandRoutingDic
		#-----------------------
		
		self.__logger.debug('Before view method:%s'%(str(signatura_view_method)))
		
		if do_profile:
		# profile  this -------------------------------
			cProfile.run("http_Reply = getattr(self.__instance_VIEW,signatura_view_method)(pc,view_elemD,modelStateDic,modelDic)",  '_profile_get_modelDic1') 
		else:	
			http_Reply = getattr(self.__instance_VIEW,signatura_view_method)(pc,view_elemD,modelStateDic,modelDic)
		#print 'http_Reply1=',signatura_view_method,http_Reply
		
		if 'cover' in view_elemD:
			pass
			
		if 'async' in view_elemD:
			pass	
		#print http_Reply
		return http_Reply

	def do_nothing(self,*args):
		self.__logger.info("method do nothing in MVC controller")
		
		return None
		
	def remember_current(self):
		
		self.__logger.info("method remember_current in MVC controller")
		#pc = self.__model_instance.do_play()
		pc = self.__player_handler.get_status()
		self.__model_instance.append_to_Temp_MemCRC32_PlayList(pc['track_CRC32'])
		self.__logger.debug('pc =%s'%(str(pc)))
		
		return None
		
	def get_data_for_player_context(self,PlayControl_CurStatusD,modelDic,view_elemD,*args):
	# функция - расширение для get_modelDic, сложные алгоритмы в рамках get_modelDic должны реализоваываться в подобных функциях.
	# функция по заданиям определенным в view_elemD и анализируя текущий буфер данных modelDic
	# собирает данные контекста плеера и помещает их по ключам в modelDic
		print("get_data_for_player_context ----> START OK",list(view_elemD.keys()))
		self.__logger.debug("get_data_for_player_context ----> START OK. "+str(list(view_elemD.keys())))
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 		
		if 'albumDL' in modelDic:
			del modelDic['albumDL']
		if 'albumD_db' in modelDic:	
			del modelDic['albumD_db']
			
		if 'tplgDL' in modelDic:
			del modelDic['tplgDL']
			
		if 'obj_categDL'  in modelDic:
			del modelDic['obj_categDL']
		
		cur_track_key = PlayControl_CurStatusD['track_CRC32']
		#if 'cur_track_in_album_pos' not in modelDic:
		cur_stateDic = self.__model_instance.getMediaLibPlayProcess_State()
		
		self.__logger.debug('calculating cur_track_in_album_pos:'+str(cur_stateDic['songNum'])+","+str(cur_stateDic['albumNum']))
		
		modelDic['cur_track_in_album_pos'] = cur_stateDic['songNum']-cur_stateDic['albumNum']
			
		print(' 1 cur_track_in_album_pos',	modelDic['cur_track_in_album_pos'])
		
		if 'current_Album_order_Indx' not in modelDic:
			#modelDic['current_Album_order_Indx'] = self.__model_instance.get_current_Album_order_Indx()
			a_t_numD = self.__model_instance.get_current_Album_Track_context()
			print('2.get_current_Album_Track_context ok:',a_t_numD)
			albumNum = 0
			if a_t_numD != None:
				modelDic['current_Album_order_Indx'] = a_t_numD['album_ord_index']	
				albumNum = a_t_numD['albumNum']	
				self.__model_instance.setSongAlbumNums(pc['pl_pos'],albumNum)	
			print()
			print('|||||||||| ---- current_Album_order_Indx:',modelDic['current_Album_order_Indx'])
		else:
			print()
			print(' ---- current_Album_order_Indx:',modelDic['current_Album_order_Indx'])
		
		
		self.__logger.debug('in 859 get_modelDic playerMData trackL')
		try:
			modelDic['metaD_of_cur_pL'] = self.__model_instance.MediaLibPlayProcessDic()['metaD_of_cur_pL']
		except:	
			self.__logger.info("""modelDic['metaD_of_cur_pL'] is empty""")
			modelDic['metaD_of_cur_pL'] = {}
			
		self.__logger.debug('in 868 get_modelDic playerMData trackL')
		
		try:	
			cur_album_crc32 = modelDic['metaD_of_cur_pL'][cur_track_key]['album_crc32']
			cur_artist_crc32 = modelDic['metaD_of_cur_pL'][cur_track_key]['artist_crc32']
		except:	
			self.__logger.info("""modelDic['metaD_of_cur_pL'] is empty""")	
			cur_album_crc32 = 0
			cur_artist_crc32  = 0
			return
		#print 'cur_album_crc32-------',cur_album_crc32
		
		if 'tplgDL' in view_elemD or 'playerMData' in  view_elemD:	
			modelDic['tplgDL'] = getAlbum_parentObjects(dbPath,cur_album_crc32)	
			self.__logger.debug("""--modelDic['tplgDL']->"""+str(modelDic['tplgDL']))
			
			
		if 'obj_categDL' in view_elemD or 'playerMData' in  view_elemD:	
			cat_profD = getCategoryProfileDic(dbPath)['categoryD']	
			modelDic['obj_categDL'] = findCateg_via_ObjectId(dbPath,{'album':cur_album_crc32,'artist':cur_artist_crc32},cat_profD,'result_like_list')['categoryL']		
			
			
			self.__logger.debug("""--modelDic['obj_categDL']->"""+str(modelDic['obj_categDL']))
		
		# Заменить нижнюю конструкцию на взятие данных из модели.
		modelDic['PlayList_asCRC32_L'] = self.__model_instance.MediaLibPlayProcessDic()['PlayList_asCRC32_L']
		
		crc32L=[]
		crc32L = modelDic['PlayList_asCRC32_L']
		
		self.__logger.debug("""900 Check albumD and album_initial, crc32L: """+str(crc32L))
		
		if 'albumD' not in modelDic:
			albumD = DistinctAlbums_from_metaD(modelDic['metaD_of_cur_pL'],crc32L)
		else:
			albumD = modelDic['albumD']
		
		self.__logger.debug("""907 Check albumD and album_initial""")	
		
		if 'album_initial' in args:
			albumD_db = getAlbumD_fromDB(dbPath,None,None,list(albumD.keys()),'with_tracks_number')['albumD']
		
	
		self.__logger.debug("""913 Check albumD and album_initial""")
		albumL = []
		
		#тут вычислить тип альбома на НСА и сохранить этот атрибут isNSA
		isNSA = False
		
		#print albumD.keys()
		album_numb = len(albumD)
		track_numb = 0
		trackL = []
		trackL_flat = []
		for a in albumD:
		
			if 'album_initial' in args:
				restoreTracks = False
				isNSA = False
				format = ''
				#print a
				try:
					if albumD_db[a]['album_type'] != 'ONE_ARTIST':
						isNSA = True	
					format = albumD_db[a]['format_type']
					#print albumD_db[a].keys()
					if albumD_db[a]['all_track_num'] > len(albumD[a]['albumL']):
						restoreTracks = True
				except Exception as e:
					print('Error in not yet registred album:',e,a)
					self.__logger.critical("954 Error in not yet registred album:------>"+str(e))
					format = 'no'#modelDic['metaD_of_cur_pL'][a]['format']
					
				albumItem = {'album':albumD[a]['album'],'album_order_numb':albumD[a]['album_order_numb'],'album_key':a,'firstFileLPos':albumD[a]['firstFileIndex'],'isNSA':isNSA,'format':format}	
			
		
		
			track_keysL = [track_i[3] for track_i in albumD[a]['albumL']]
			track_numb+=len(track_keysL)
			
			trackL_restore = []
			
			
			index = 0
			index_flat = 0
			cur_in_album_pos_flat = 0
			cur_in_album_pos = 0
			for track_i in albumD[a]['albumL']:
			
				if cur_track_key == track_i[3]:
					cur_in_album_pos_flat = index_flat
	# ВНИМАНИЕ!!! Ни в коем случае не обрезать длину названия трэка, альбома, артиста это приводи к ошибки декодирования UTF			
				trackL_flat.append({'track':track_i[0],'artist':track_i[2],'artist_key':track_i[5],'lPos':track_i[1],'in_alb_pos':track_i[1]-albumD[a]['firstFileIndex']+1,'even_odd':'even','track_key':track_i[3],'track_time':track_i[4],'bitrate':track_i[6]})
				index_flat+=1
				
				if cur_album_crc32 == a: 
					#print a
					if cur_track_key == track_i[3]:
						cur_in_album_pos = index
	# ВНИМАНИЕ!!! Ни в коем случае не обрезать длину названия трэка, альбома, артиста это приводи к ошибки декодирования UTF
					trackL.append({'track':track_i[0],'artist':track_i[2],'artist_key':track_i[5],'lPos':track_i[1],'in_alb_pos':track_i[1]-albumD[a]['firstFileIndex']+1,'even_odd':'even','track_key':track_i[3],'track_time':track_i[4],'bitrate':track_i[6]})
					index+=1
		
			if 'album_initial' in args:
			# тут проверить совпадает ли количество трэков в листе с количеством реальных трэков в альбоме, и если нет, то сделать список востановленных трэков
				trackL.sort(key=operator.itemgetter('lPos'))
				albumItem['tbRestored'] = restoreTracks
				albumL.append(albumItem)	
				albumL.sort(key=operator.itemgetter('firstFileLPos'))
				modelDic['albumDL'] = albumL
				
		
		if trackL_flat != []:	
			trackL_flat.sort(key=operator.itemgetter('lPos'))
			
		modelDic['trackDL'] = trackL
		
		self.__logger.debug("1001  album_numb: %s , album_numb)/track_numb: %s"%(str(album_numb),str(float(album_numb)/track_numb)))
		if (album_numb  > 1) and (float(album_numb)/track_numb > 0.3):
			modelDic['list_type_flat'] = True
			modelDic['trackDL'] = trackL_flat
			modelDic['cur_track_in_album_pos'] = cur_in_album_pos_flat
		else:
			modelDic['list_type_flat'] = False
			#modelDic['cur_track_in_album_pos'] = cur_in_album_pos
			
		print("get_data_for_player_context ----> FINISHED OK")	
						
		
	def client_layout_merge(self,mode,client_state,pc, view_elemD):	
		# Определяет необходимые изменения в представлении клиента на основе его текущего статуса!!client_state!!
		self.__logger.info("method client_layout_merge in MVC controller:%s"%(str(client_state)))
		print()
		print('####################>>>>>>>>> client_layout_merge')
		print("pL_CRC32:",client_state['pL_CRC32'],pc['pL_CRC32'])
		
		if client_state['pL_CRC32'] != pc['pL_CRC32']:
			print("---New list")
			if 'current_Album_order_Indx' in self.__modelDic:
				del self.__modelDic['current_Album_order_Indx']
			if 'cur_track_in_album_pos' in self.__modelDic:
				del self.__modelDic['cur_track_in_album_pos']	
				
			view_elemD['trackL']=''
			view_elemD['albumL']=''
			view_elemD['tagsL']=''
			view_elemD['playerMData']=''
			return
			
		#print 	
		if 'current_Album_order_Indx' not in self.__modelDic:
			#self.__modelDic['current_Album_order_Indx'] = self.__model_instance.get_current_Album_order_Indx()
			a_t_numD = self.__model_instance.get_current_Album_Track_context()
			print('3.get_current_Album_Track_context ok:',a_t_numD)
			albumNum = 0
			if a_t_numD != None:
				self.__modelDic['current_Album_order_Indx'] = a_t_numD['album_ord_index']	
				albumNum = a_t_numD['albumNum']	
				self.__model_instance.setSongAlbumNums(pc['pl_pos'],albumNum)	
			
			
		#print "albumL:",client_state['cur_album_pos'],self.__modelDic['current_Album_order_Indx']
		if client_state['cur_album_pos'] != self.__modelDic['current_Album_order_Indx']:			
			print("---New Album")
			view_elemD['tagsL']=''
			view_elemD['trackL']=''
			view_elemD['tplgDL']=''
			view_elemD['obj_categDL']=''
			return
		
		#print 'trackL:',client_state['track_CRC32'],pc['track_CRC32']			
		if client_state['track_CRC32'] != pc['track_CRC32']:		
			print("---New track")
			view_elemD['tagsL']=''
			return	
		# не будет изменений но надо восстановить убитые в view переменные	
		if 'cur_track_in_album_pos' not in self.__modelDic:
			cur_stateDic = self.__model_instance.getMediaLibPlayProcess_State()
			self.__modelDic['cur_track_in_album_pos'] = cur_stateDic['songNum']-cur_stateDic['albumNum']	
			
		return
	def refresh_check_player_state(self,commandD):
		self.__logger.info("method refresh_check_player_state:%s"%(str(commandD)))
		#print 'refresh_check_player_state!!!!'
		#pc = self.__model_instance.do_play()
		
		
		if not self.__model_instance.isPlayerAlive():
			self.__logger.info("method refresh_check_player_state NO PLYER")
			return {}
		pc = self.__player_handler.get_status()
		if 'get_player_process_info' not in commandD:
			if 'refresh_check' in commandD:
				old_state = json.loads(commandD['refresh_check'])
				#print old_state,type(old_state)
				#print old_state.keys()
				print(list(pc.keys()))
				for a in ['pL_CRC32','track_CRC32']:
					try:
						print('old/new state-----------------:',a,old_state[a],pc[a])
					except:
						print('old/new state-----------------:',a,old_state[a],'no')
					
		
		pLQueueD = self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']
		lenQueue = len(pLQueueD['PlayListQueue'])
		MediaLibPlayProcess_StateD = self.__model_instance.getMediaLibPlayProcess_State()
		
		if pc['playBack_Mode']	== 0 and MediaLibPlayProcess_StateD['manual_stop_flag'] == False and pc['list_length'] == (MediaLibPlayProcess_StateD['songNum']+1) and lenQueue>1: 
			print('-------->Here pop plist from queue')
			
			pop_index = pLQueueD['PlayListQueue'].pop(lenQueue-1)
			print('last_plst',pop_index)
			del(pLQueueD['PlayListQueueD'][pop_index])
			print(pLQueueD['PlayListQueue'])
			cur_index = pLQueueD['PlayListQueue'][len(pLQueueD['PlayListQueue'])-1]
			print('cur_index',cur_index)
			
			
			metaD = {}
			if 'metaD' in pLQueueD['PlayListQueueD'][cur_index]:
				if pLQueueD['PlayListQueueD'][cur_index]['metaD'] != {}:
					metaD = pLQueueD['PlayListQueueD'][cur_index]['metaD']
				
			if metaD == {}:	
				dbIdL = pLQueueD['PlayListQueueD'][cur_index]['PlayListL']
			
				db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
				metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
				db.close()
					
			
			plS = createPlayList_fromMetaDataD(metaD)
				#print 'getPlistQueue2',plS
			mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']
			playlistpath = mediaPath + 'Plugins\\ml\\'	
			
			
			f = open(playlistpath+'queuePL.m3u','w')
			f.write(plS)
			f.close()
			len_pls = len(plS)
				
			if 'cur_pos' in pLQueueD['PlayListQueueD'][cur_index]:
				song_pos = pLQueueD['PlayListQueueD'][cur_index]['cur_pos']
				#print 'PREV_PLST_CHECK2'	
			pc = self.__player_handler.new_list_load(playlistpath+'queuePL.m3u',song_pos)	
	
			print('pc=',pc)
			self.__model_instance.setplayList('queuePL.m3u')
			pc = self.play()
			
			if 'listDescr' in pLQueueD['PlayListQueueD'][cur_index] and 'listType' in pLQueueD['PlayListQueueD'][cur_index]:
				listType = pLQueueD['PlayListQueueD'][cur_index]['listType']
				listDescr = pLQueueD['PlayListQueueD'][cur_index]['listDescr']
			else:
				listType = 'bad'
				listDescr = 'bad'
				
			dicData = {'title': """Queue list for '%s'"""%(str(cur_index)),  'filename': 'queuePL.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len_pls)}	
			self.__model_instance.set_new_pD_elem('queuePL.m3u',dicData)	
			
			
			
			self.__model_instance.update_model_state(pc)
			
			
			# Получаем  содержимое листа от контроллера плеера
			#l_data = zlib.decompress(self.__player_handler.get_cur_pl_as_list().data)
			#self.__PlayListL = 	pickle.loads(l_data)
			# Генерируем его содержимое как crc32L
			#try:
			#	self.__PlayList_asCRC32_L = [zlib.crc32(a) for a in self.__PlayListL]	
			#except:
			#	pass
				
			self.__model_instance.update_curList_metaD(metaD)
			return pc
			
		
		next = pc['pl_pos']
		#print '2:',pc['pl_pos']
		prev_next = self.__model_instance.get_Prev_Next_AlbumIndx()
		album_num = self.__model_instance.getMediaLibPlayProcessContext()['albumNum']
		#print 'next, prev_next,album_num ',next, prev_next,album_num 
		if prev_next[1] == None:
			pass
			#self.setSongAlbumNums(next,album_num)
		elif next >= prev_next[1] :
			album_num = prev_next[1]	
			#print next,album_num
			
		# ---> 	ВНИМАНИЕ - Необходима актуализация модели
		self.__model_instance.setSongAlbumNums(next,album_num)
		#print 'End of next'
		return pc
		
		
		
	def play(self):
		pc = self.__model_instance.do_play()
		
		return pc
		
	def stop(self):
		pc = self.__player_handler.stop()
		self.__model_instance.setManualStopFlag(True)
		return pc
		
	def pause(self):
		pc = self.__player_handler.pause()	
		#print pc
		return pc
		
	def next_trc(self):
		#print 'Catch next track!!!!'
		pc = next(self.__player_handler)
		#print '1:',pc['pl_pos']
		next = pc['pl_pos']
		#print '2:',pc['pl_pos']
		prev_next = self.__model_instance.get_Prev_Next_AlbumIndx()
		album_num = self.__model_instance.getMediaLibPlayProcessContext()['albumNum']
		#print 'next, prev_next,album_num ',next, prev_next,album_num 
		if prev_next[1] == None:
			pass
			#self.setSongAlbumNums(next,album_num)
		elif next >= prev_next[1] :
			album_num = prev_next[1]	
			#print next,album_num
			
		# ---> 	ВНИМАНИЕ - Необходима актуализация модели
		self.__model_instance.setSongAlbumNums(next,album_num)
		#print 'End of next'
		return pc
		
	def prev_trc(self):
		pc = self.__player_handler.prev()
		prev = pc['pl_pos']
		prev_next = self.__model_instance.get_Prev_Next_AlbumIndx()
		album_num = self.__model_instance.getMediaLibPlayProcessContext()['albumNum']	
			
		if prev < album_num:
			album_num = prev_next[0]	
			
		# ---> 	ВНИМАНИЕ - Актуализация модели	
		self.__model_instance.setSongAlbumNums(prev,album_num)
			#print 'next:',prev,'album_num:',album_num
		return pc	
		
	def forward(self):
		#print 'Catch forward track!!!!'
		# При перемотках не требуется изменение модели, так как единственно, что меняется при этом это "время до конца",
		# а оно возвращается в статусе и передается в генератор представления напрямую
		
		pc = self.__player_handler.forward()		
		return pc
		
	def set_song_pos(self,commandD):
		#print 'set_song_pos!!!!',commandD
		
		if 'set_song_pos' in commandD:
			pos = int(commandD['set_song_pos'])
			#print "pos = ",commandD['set_song_pos']
		# При перемотках не требуется изменение модели, так как единственно, что меняется при этом это "время до конца",
		# а оно возвращается в статусе и передается в генератор представления напрямую
		
			pc = self.__player_handler.set_position_within_the_track(pos)		
			return pc	
		return -1	
		
	def set_song_pos_(self,commandD):
		#print 'set_song_pos!!!!',commandD
		
		if 'set_song_pos_' in commandD:
			pos = int(commandD['set_song_pos_'])
			#print "pos = ",commandD['set_song_pos']
		# При перемотках не требуется изменение модели, так как единственно, что меняется при этом это "время до конца",
		# а оно возвращается в статусе и передается в генератор представления напрямую
		
			pc = self.__player_handler.set_position_within_the_track(pos)		
			return pc	
		return -1		
		
	def rewind(self):
		# При перемотках не требуется изменение модели, так как единственно, что меняется при этом это "время до конца",
		# а оно возвращается в статусе и передается в генератор представления напрямую
		pc = self.__player_handler.rewind()
		return pc
	def goto_Track(self,commandD):
		
		self.__logger.info('method goto_Track:%s'%(str(commandD)))
		if 'sel_idL' in commandD:
			track_pos = int(commandD['sel_idL'][0])
			#print track_pos
			pc = self.__player_handler.set_cur_track_pos(track_pos)
			self.__model_instance.setSongAlbumNums(track_pos,None)
			return pc
		else:
			print('sel_idL is missing in command')
	
	def goto_Track_(self,commandD):
		
		self.__logger.info('method goto_Track:%s'%(str(commandD)))
		
		track_pos = int(commandD['goto_track_'])
			#print track_pos
		pc = self.__player_handler.set_cur_track_pos(track_pos)
		self.__model_instance.setSongAlbumNums(track_pos,None)
		return pc
		
		
	def goto_Album(self,commandD):
		#print '!!!!:',commandD
		self.__logger.info('method goto_Album:%s'%(str(commandD)))
		if 'sel_idL' in commandD:
			track_pos = int(commandD['sel_idL'][0])
			#print track_pos
			pc = self.__player_handler.set_cur_track_pos(track_pos)
			self.__model_instance.setSongAlbumNums(track_pos,track_pos)
			return pc
		else:
			print('sel_idL is missing in command')
			
	def goto_Album_(self,commandD):
		#print '!!!!:',commandD
		self.__logger.info('method goto_Album_:%s'%(str(commandD)))
		try:
			track_pos = int(commandD['goto_album_'])
		except:
			track_pos = 0
			#print track_pos
		pc = self.__player_handler.set_cur_track_pos(track_pos)
		self.__model_instance.setSongAlbumNums(track_pos,track_pos)
		return pc
		
			
	def next_alb(self):
		
		self.__logger.info('method next_alb')
		prev_next = self.__model_instance.get_Prev_Next_AlbumIndx()
		print('prev_next',prev_next)
		pc = None
		if prev_next[1] != None:
			trackNum = prev_next[1]
			pc = self.__player_handler.set_cur_track_pos(trackNum)
			self.__model_instance.setSongAlbumNums(trackNum,trackNum)
		return pc		
				
			
	def prev_alb(self):
		self.__logger.info('method prev_alb')
		prev_next = self.__model_instance.get_Prev_Next_AlbumIndx()
		print('prev_next',prev_next)
		pc = None
		if prev_next[0] != None:
			trackNum = prev_next[0]
			pc = self.__player_handler.set_cur_track_pos(trackNum)
			self.__model_instance.setSongAlbumNums(trackNum,trackNum)
		return pc	
	
#	Это надо модифицировать под новую архитектуру	

	def play_list_from_queueL(self,listCRC32_key):
		
		if listCRC32_key not in self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueueD']:
			print('Wrong key for Quelist--> Action ignored')
			return
		#'pLQueueD':  {'PlayListQueueD':self.__PlayListQueueD,'PlayListQueue':self.__PlayListQueue},
		#self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueueD']
		
		cur_listD = self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueueD'][listCRC32_key]
		
		dbIdL = cur_listD['PlayListL']
			#print listCRC32,dbIdL
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
		metaD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
		db.close()
		plS = createPlayList_fromMetaDataD(metaD)
			#print 'getPlistQueue2',plS 
			
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']
		playlistpath = mediaPath + 'Plugins\\ml\\'
		f = open(playlistpath+'queuePL.m3u','w')
			#print playlistpath+'search_play.m3u'
			#print plS
		f.write(plS)
		f.close()
			#print 'getPlistQueue3'
		len_pls = len(plS)
		
			
		if 'cur_pos' in cur_listD:
			song_pos = cur_listD['cur_pos']
		pc = self.__player_handler.new_list_load(playlistpath+'queuePL.m3u',song_pos)
		
		self.__model_instance.setplayList('queuePL.m3u')
		
			#print pc
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		if pc['playBack_Mode']  == 1:
			pc = self.play()
		else:	
			pc = self.play()
			
			#search_term = 'search'
			
			
		dicData = {'title': """Queue list for '%s'"""%(str(listCRC32_key)),  'filename': 'queuePL.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len_pls)}
			
			
		if 'listDescr' in cur_listD and 'listType' in cur_listD:
			listType = cur_listD['listType']
			listDescr = cur_listD['listDescr']
		else:
			listType = 'bad'
			listDescr = 'bad'
			
		self.__model_instance.set_new_pD_elem('queuePL.m3u',dicData)
		print('OK')
		return pc
		

		
	def goto_queueL(self,commandD):
		
		self.__logger.info('method goto_queueL:%s'%(str(commandD)))
		
		if 'sel_idL' in commandD:
			listCRC32 = int(commandD['sel_idL'][0])
		else:
			print('sel_idL is missing in command')
			return	
		#'pLQueueD':  {'PlayListQueueD':self.__PlayListQueueD,'PlayListQueue':self.__PlayListQueue},
		#self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueueD']
		
		pc = self.play_list_from_queueL(listCRC32)
		return pc
		
		
	def prev_plst(self):
		print('prev_plst!!!!',len(self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueue']))
		
		if len(self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueue']) == 0:
			print("Queue is Empty")
			return
		PlayListQueue = self.__model_instance.MediaLibPlayProcessDic()['pLQueueD']['PlayListQueue']
		pop_index = PlayListQueue.pop(len(PlayListQueue)-1)
		
		print('last_plst',pop_index)
		#del(PlayListQueue[pop_index])
		print(PlayListQueue)
		cur_index = PlayListQueue[len(PlayListQueue)-1]
		print('cur_index',cur_index)
		
		pc = self.play_list_from_queueL(cur_index)
		return pc
		
	def goto_libL(self,commandD):
		print('goto_libL!!!!:',commandD)	
		if 'sel_idL' in commandD:
			listKey = commandD['sel_idL'][0]
		else:
			print('sel_idL is missing in command')
			return	
			
		
		
		return self.play_libL_general(listKey,0)
	

	def play_libL_general(self,listKey,pos):
		
			
		#self.__listName = commandD['getPlayList']
		#self.__playlistGroup = commandD['getGroupOfPlayList']
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']
		list_path_name = mediaPath+"Plugins\\ml\\"+listKey
			#print list_path_name
		pc = self.__player_handler.new_list_load(list_path_name,pos)
		
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		if pc['playBack_Mode']  == 1:
			pc = self.play()
		elif pc['playBack_Mode']  == 3:	
			pc = self.__player_handler.pause()
				
		listType = 'MediaLib'
		#print 'pass 1'
		pD = self.__model_instance.MediaLibPlayProcessDic_viaKey('pD','local')
		#print 'pass 2'
		listDescr = pD[listKey]['title']	
		#print 'pass 3'
		pc['listType'] = listType
		pc['listDescr'] = listDescr
		
		return pc
		
	def goto_tag_general(self,tagId,tagType,title_crc32):	
		self.__logger.info('method goto_tag_general:%s'%(str([tagId,tagType,title_crc32])))
		listType = ''
		listDescr = ''
		curCRC32 = 0
		resL = []
		song_pos = 0
		pc = {}
		remote_host = self.__modelDic['REMOTE_ADDR']
		
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		
		mpd_socket = mpd_instance['socket']
		host = mpd_instance['host']
		host_ip = socket.gethostbyname(host)
		print(host_ip) 
		self.__logger.info('in method goto_tag_general: play to [%s]'%(str(host)))
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']
		
		
		client = MPDClient()
		# Not necessary, but should not cause any trouble either
		client.disconnect()
		
		if title_crc32 == None:
			# Если перегенерация на основе данных текущей композиции, то сохраняем ее СРЦ32
			#PlayControl_CurStatusD = self.__player_handler.get_status()
			#curCRC32 = PlayControl_CurStatusD['track_CRC32']	
			pass 
		elif title_crc32 == 0:
			# Если нет, то переход в точку указанную в параметрах 
			curCRC32 = title_crc32	
		else:
			# Если нет, то переход в точку указанную в параметрах 
			curCRC32 = title_crc32
		
		#print "DECEMBER 2015 *********** curCRC32:",curCRC32	
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		db = sqlite3.connect(dbPath)
		if tagId == None:
			return pc
			
		if tagType == 'hard_tag':	
			self.__logger.debug('method 1611 goto_tag_general: before hard_tag mpd gen')
			l =  load_mpd_playlist_via_tag_num(db,client,host_ip,mpd_socket,mpdMusicPathPrefix,tagId,'track_tag')
			
			
		elif tagType == 'artist_tag':	
			#print 'Before PL generation'
			self.__logger.debug('method 1611 goto_tag_general: before artist mpd gen')
			
			l =  load_mpd_playlist_via_tag_num(db,client,host_ip,mpd_socket,mpdMusicPathPrefix,tagId,'artist')
			#print ' ************* artist_tag pl generated',tagId	
		elif tagType == 'album_tag':	
			self.__logger.debug('method 1622 goto_tag_general: before album mpd gen')
			l =  load_mpd_playlist_via_tag_num(db,client,host_ip,mpd_socket,mpdMusicPathPrefix,tagId,'album')
			
		db.close()	
		
			
		#l = load_mpd_playlist_via_tag_num(db,client,host,mpdMusicPathPrefix,artist_key,'artist')
		return pc
	def goto_tag_general_old(self,tagId,tagType,title_crc32):
		self.__logger.info('method goto_tag_general:%s'%(str([tagId,tagType,title_crc32])))
		listType = ''
		listDescr = ''
		curCRC32 = 0
		resL = []
		song_pos = 0
		
		if title_crc32 == None:
			# Если перегенерация на основе данных текущей композиции, то сохраняем ее СРЦ32
			PlayControl_CurStatusD = self.__player_handler.get_status()
			curCRC32 = PlayControl_CurStatusD['track_CRC32']	
		elif title_crc32 == 0:
			# Если нет, то переход в точку указанную в параметрах 
			curCRC32 = title_crc32	
		else:
			# Если нет, то переход в точку указанную в параметрах 
			curCRC32 = title_crc32
		#print "DECEMBER 2015 *********** curCRC32:",curCRC32	
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		db = sqlite3.connect(dbPath)
		if tagId == None:
			return pc
		
		# Проверка концепции загрузки листов минуя файловую систему	
		t_start = time.time()
		if tagType == 'hard_tag':	
			plS=createPlayList_viaTagId(tagId,db)
			
			
		elif tagType == 'artist_tag':	
			#print 'Before PL generation'
			plS=createPlayList_viaArtistCRC32(tagId,db)
			#print ' ************* artist_tag pl generated',tagId	
		elif tagType == 'album_tag':	
			plS=createPlayList_viaAlbumCRC32(tagId,db)		
			
		db.close()
		
		try:
			resL = [zlib.crc32(a.encode(BASE_ENCODING)) for a in plS.split('\n')]	
		except Exception as e:
			print('List is empty ???')
			self.__logger.critical('Error: %s in method goto_tag_general after crc32'%(str(e)))
			return []
			pass
		
		print('song pos:',song_pos)
		if len(resL) == 1:
			print('List is empty ???:',resL)
			self.__logger.critical('Error in method goto_tag_general after len(resL)'%(str(len(resL))))
			return []
		try:
			if resL != [] and curCRC32 != 0:
				#print 'song pos:',song_pos
				song_pos = resL.index(curCRC32)
				#print 'song pos after:',song_pos,curCRC32
				#print resL
		except Exception as e:
			print('ERRRRRRRRRR song pos:',song_pos)
			self.__logger.critical('Error: %s in method goto_tag_general after crc32'%(str(e)))
			pass
		
		print() 
		print('----> new pls=',len(resL),song_pos,curCRC32,tagId)
		self.__logger.debug('in method goto_tag_general result check new pls= %s'%(str([len(resL),song_pos,curCRC32,tagId])))	
		
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']	
		playlistpath = mediaPath + 'Plugins\\ml\\'
		
		
		f = io.open(playlistpath+'tag_play.m3u8','w',encoding='utf-8')
		try:
			f.write(plS)
			f.close()
		except Exception as e:
			self.__logger.critical('Error: %s in method goto_tag_general at playlist file write'%(str(e)))
			d = pickle.dumps({'Dump_Data':plS,'Error':str(e),'ErrorContext':'AT method goto_tag_general at playlist file write failed:line 1614'})
				
			self.__logger.info('Dump saved at debug.dat in [%s]'%(str(os.getcwd())))
			f = open('debug.dat','w')
			f.write(d)
			f.close()
			print('Dump saved ok')
			
			
			
			
		len_pls = len(plS)
		
		pc = self.__player_handler.new_list_load(playlistpath+'tag_play.m3u8',song_pos)
		
		print("list generated:",playlistpath)
		self.__model_instance.setplayList('tag_play.m3u')
		print("list is set")
			#print pc
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		print("get stop flag:",pc)
		if pc['playBack_Mode']  == 1:
			pc = self.play()
			#print "pc1=",pc
		elif pc['playBack_Mode']  == 3:	
			#print "pc3=",pc
			pc = self.__player_handler.pause()
		print('load artist list finished in:',	str(int(time.time()-t_start)))	
		print("4",tagType,pc)	
		
		if tagType == 'hard_tag':	
			print("4.1")
			search_term =  self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
			print("4.2",pc)
			dicData = {'title': """Tag Temp list for '%s'"""%(search_term),  'filename': 'tag_play.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len(plS))}
			print("4.3")
			
			listType = 'TagNavi'
			listDescr = search_term
		elif tagType == 'artist_tag':	
			artistName = "artistName"
			dicData = {'title': """Tag Artist Temp list for '%s'"""%(artistName),  'filename': 'tag_play.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len(plS))}
			
			listType = 'ArtistTag'
			listDescr = artistName
		elif tagType == 'album_tag':
			albumName = 'albumName'
			dicData = {'title': """Tag Album Temp list for '%s'"""%(albumName),  'filename': 'tag_play.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len(plS))}
			
			listType = 'AlbumTag'
			listDescr = albumName
		
			
		print("5")
		self.__model_instance.set_new_pD_elem('tag_play.m3u',dicData)
			
		print('OK:',tagType)
		pc['listType'] = listType
		pc['listDescr'] = listDescr
		
		return pc	
		
	def goto_tagL(self,commandD):	
		
		self.__logger.info('method goto_tagL:%s'%(str(commandD)))
		tagId = None
		title_crc32 = None
		if 'sel_idL' in commandD:
			tagId = commandD['sel_idL'][0]
			try:
				title_crc32 = commandD['sel_idL'][1]
			except:
				pass
		else:
			print('sel_idL is missing in command')
			return	
		try:	
			pc = self.goto_tag_general(tagId,'hard_tag',title_crc32)	
		except Exception as e:
			self.__logger.critical('Exception in gotoTagsL:%s'%str(e))
			
		if 'force_play' in commandD:
			if pc['playBack_Mode']  == 0 or  pc['playBack_Mode']  == 1:
				print('pc=',pc['playBack_Mode'])
				pc = self.play()
			
		return pc	
		
		
	def cast_goto_Track(self,commandD):	
		self.__logger.info('method cast_goto_Track:%s'%(str(commandD)))
		
		# Создаем в рамках думми сессии данные по ее текущему листу в будущем сессия создается при логине и тут вместо 1 передается настоящий индекс сессии	
		

		
		try:	
			self.__model_instance.set_CastPlayList(self.__modelDic['REMOTE_ADDR'],{'cur_track_id':commandD['track_id'],'player_status':''})	
			#self.__modelDic['CastPlayListD'] = self.__model_instance.get_CastPlayList(1,{'cur_track_id':commandD['track_id'],'player_status':''})	
		except:
			print("error in self.__model_instance.set_CastPlayList")
		return 		
		
	def cast_next_trc(self,commandD):	
		
		self.__logger.info('method goto_next_tarck:%s'%(str(commandD)))
		# Создаем в рамках думми сессии данные по ее текущему листу в будущем сессия создается при логине и тут вместо 1 передается настоящий индекс сессии	
		

		
		try:	
			self.__model_instance.set_CastPlayList(self.__modelDic['REMOTE_ADDR'],{'cur_track_id':commandD['track_id'],'player_status':''})	
			#self.__modelDic['CastPlayListD'] = self.__model_instance.get_CastPlayList(1,{'cur_track_id':commandD['track_id'],'player_status':''})	
		except:
			print("error in self.__model_instance.set_CastPlayList")
		return 	
	
	def cast_prev_trc(self,commandD):	
		self.__logger.info('method goto_prev_tarck:%s'%(str(commandD)))
		# Создаем в рамках думми сессии данные по ее текущему листу в будущем сессия создается при логине и тут вместо 1 передается настоящий индекс сессии	
		try:	
			self.__model_instance.set_CastPlayList(self.__modelDic['REMOTE_ADDR'],{'cur_track_id':commandD['track_id'],'player_status':''})	
			#self.__modelDic['CastPlayListD'] = self.__model_instance.get_CastPlayList(1,{'cur_track_id':commandD['track_id'],'player_status':''})	
			
		except:
			print("error in self.__model_instance.set_CastPlayList")
		return 
	
	def goto_dynamicle_tagL_cast(self,commandD):	
		
		self.__logger.info('goto_dynamicle cast!!!!:%s'%(str(commandD	)))
		key = None
		
		if 'sel_idL' in commandD:
			key = commandD['sel_idL'][0]
			
		else:
			
			self.__logger.error('sel_idL is missing in command')
			return	
			
		navi_mode = ''	
		if 'cast_navigation_control' in commandD:
			navi_mode = commandD['cast_navigation_control']
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])
		if 'goto_tagL' in navi_mode:
			self.__logger.debug('in goto_dynamicle_tagL_cast-->goto_tagL')
			resD = createPlayList_viaTagId_cast(key,db)
		elif 'goto_album_tagL'	in navi_mode:
			self.__logger.debug('in goto_dynamicle_tagL_cast-->goto_album_tagL')
			resD = createPlayList_viaAlbumCRC32_cast(key,db)
		else:
			self.__logger.debug('in goto_dynamicle_tagL_cast--> ??4')
			resD = {}
		db.close()	
		castL  = []
		crc32L = []
		
		#print resD
		
		#self.__CastPlayList[session_id]={'cur_track_id':'','player_status':'','metaD':{}}
		
		for a in resD['sortedL']:
			castL.append(resD['metaD'][a]['id_track'])
			
		# Создаем в рамках думми сессии данные по ее текущему листу в будущем сессия создается при логине и тут вместо 1 передается настоящий индекс сессии	
		try:	
			self.__model_instance.set_CastPlayList(self.__modelDic['REMOTE_ADDR'],{'cur_track_id':castL[0],'player_status':'','metaD':resD['metaD'],'castL':castL,'crc32L':resD['sortedL']})	
		except Exception as e:
			self.__logger.critical("error in self.__model_instance.set_CastPlayList")
		
		if key == None:
			return 0
		CastPlayList = self.__model_instance.get_CastPlayList(self.__modelDic['REMOTE_ADDR'])	
		self.__modelDic['CastPlayListD'] = CastPlayList		
		self.__modelDic['castL'] = castL
			
		return 
	
	def goto_tagL_cast(self,commandD):	
		
		self.__logger.info('method goto_tagL_cast:%s'%(str(commandD)))
		tagId = None
		title_crc32 = None
		if 'sel_idL' in commandD:
			tagId = commandD['sel_idL'][0]
			try:
				title_crc32 = commandD['sel_idL'][1]
			except:
				pass
		else:
			print('sel_idL is missing in command')
			return	
			
			
			
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])
		resD = createPlayList_viaTagId_cast(tagId,db)
		db.close()	
		castL  = []
		crc32L = []
		
		#print resD
		
		#self.__CastPlayList[session_id]={'cur_track_id':'','player_status':'','metaD':{}}
		
		for a in resD['sortedL']:
			castL.append(resD['metaD'][a]['id_track'])
			
		# Создаем в рамках думми сессии данные по ее текущему листу в будущем сессия создается при логине и тут вместо 1 передается настоящий индекс сессии	
		try:	
			self.__model_instance.set_CastPlayList(self.__modelDic['REMOTE_ADDR'],{'cur_track_id':castL[0],'player_status':'','metaD':resD['metaD'],'castL':castL,'crc32L':resD['sortedL']})	
		except:
			print("error in self.__model_instance.set_CastPlayList")
		
		if tagId == None:
			return 0
		CastPlayList = self.__model_instance.get_CastPlayList(self.__modelDic['REMOTE_ADDR'])	
		self.__modelDic['CastPlayListD'] = CastPlayList		
		self.__modelDic['castL'] = castL
		
			
		return 		
		
	def play_navi_object_viaId(self,commandD):
		self.__logger.info('method play_navi_object_viaId:%s'%(str(commandD)))
		objectCRC32 = None
		title_crc32 = None
		if 'mpd_instance' in commandD:
			self.set_mpd_instance(commandD)
		
		if 'object' in commandD:
			
			if 	commandD['object'] == 'artist':
				objectCRC32 = int(commandD['id'])
				try:
					title_crc32 = int(commandD['indx'])
				except:
					print('Error 1504  ',commandD)
				#print "tagsg..................................",title_crc32
				pc = self.goto_tag_general(objectCRC32,'artist_tag',title_crc32)	
				#if pc['playBack_Mode']  == 0 or  pc['playBack_Mode']  == 1:
					#print 'pc=',pc['playBack_Mode']
				#	pc = self.play()
			elif 	commandD['object'] == 'album':
				objectCRC32 = int(commandD['id'])
				pc = self.goto_tag_general(objectCRC32,'album_tag',title_crc32)	
				
				
				#if pc['playBack_Mode']  == 0 or  pc['playBack_Mode']  == 1:
					#print 'pc=',pc['playBack_Mode']
					#pc = self.play()
					
			elif 	commandD['object'] == 'tplg_album':
				objectCRC32 = int(commandD['id'])
				#print 'play_navi_object_viaId--------',commandD
				#pc = self.goto_tag_general(objectCRC32,'album_tag',title_crc32)	
				
				
				#if pc['playBack_Mode']  == 0 or  pc['playBack_Mode']  == 1:
					#print 'pc=',pc['playBack_Mode']
					#pc = self.play()		
					
			elif 	commandD['object'] == 'tplg_artist':
				print('play_navi_object_viaId--------',commandD)
				objectCRC32 = int(commandD['id'])
				#pc = self.goto_tag_general(objectCRC32,'album_tag',title_crc32)	
				
				
				#if pc['playBack_Mode']  == 0 or  pc['playBack_Mode']  == 1:
					#print 'pc=',pc['playBack_Mode']
					#pc = self.play()				
					
			elif 	commandD['object'] == 'genre':
				objectCRC32 = commandD['id']
				
				groupD = self.__model_instance.MediaLibPlayProcessDic_viaKey('group2PlayListD','local')['groupD']
				
				if objectCRC32 in groupD:
					tagId = groupD[objectCRC32]['play_tag']	
					if tagId != None:
						
						pc = self.goto_tag_general(tagId,'hard_tag',title_crc32)
						#pc = self.play()
						
			elif 	commandD['object'] == 'tag':
				objectCRC32 = int(commandD['id'])
				try:
					title_crc32 = int(commandD['indx'])
				except:
					print('Error 1752  ',commandD)
				print("tagsg..................................")
				tagId = objectCRC32
				if tagId != None:
						
					pc = self.goto_tag_general(tagId,'hard_tag',title_crc32)
					#pc = self.play()			
			return pc
		if 'tag_id' in commandD:	
			self.__logger.info('method play_navi_object_viaId 2004:%s'%(commandD['tag_id']))
			tagId = int(commandD['tag_id'])
			pc = self.goto_tag_general(tagId,'hard_tag',None)
			#pc = self.play()			
			return pc
	
	def goto_artist_tagL(self,commandD):
		
		
		self.__logger.info('method goto_artist_tagL:%s'%(str(commandD)))
		artistCRC32 = None
		title_crc32 = None
		if 'sel_idL' in commandD:
			artistCRC32 = commandD['sel_idL'][0]
			try:
				title_crc32 = commandD['sel_idL'][1]
			except:
				pass
		else:
			print('sel_idL is missing in command')
			return		
			
		pc = self.goto_tag_general(artistCRC32,'artist_tag',title_crc32)	
		return pc	
		
	def goto_album_tagL(self,commandD):
		
		self.__logger.info('method goto_album_tagL:%s'%(str(commandD)))
		artistCRC32 = None
		title_crc32 = None
		
		if 'sel_idL' in commandD:
			albumCRC32 = commandD['sel_idL'][0]
			try:
				title_crc32 = commandD['sel_idL'][1]
			except:
				pass
		else:
			print('sel_idL is missing in command')
			return		
			
		pc = self.goto_tag_general(albumCRC32,'album_tag',title_crc32)	
		return pc	
		
	def play_rel_lib_pl(self,commandD):	
		
		self.__logger.info('method play_rel_lib_pl:%s'%(str(commandD)))
		
		
		entryCRC32 = int(commandD['track_in_listStr'].split(',')[0])
		listKey = commandD['track_in_listStr'].split(',')[1]
		track_pos = 0
		PlayList_asCRC32_L = []
		
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']
		list_path_name = mediaPath+"Plugins\\ml\\"+listKey
		# так как пока позиция в листе неизвестна, то ставим ее на начало списка
		pc = self.__player_handler.new_list_load(list_path_name,track_pos)
		
		# Получаем  содержимое всех CRC32 значений листа от контроллера плеера
		PlayList_asCRC32_L = self.__player_handler.get_cur_pl_as_list_of_crc32()
		
		# Получаем номер позиции в списке
		if entryCRC32 in PlayList_asCRC32_L:
			track_pos = PlayList_asCRC32_L.index(entryCRC32)
			
		#print "entryCRC32=",entryCRC32,'track_pos=',track_pos,'len(PlayList_asCRC32_L)=',len(PlayList_asCRC32_L)	
		pc = self.__player_handler.set_cur_track_pos(track_pos)
		#print pc
		
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		if pc['playBack_Mode']  == 1:
			pc = self.play()
		elif pc['playBack_Mode']  == 3:	
			pc = self.__player_handler.pause()
		
		self.__model_instance.setplayList(listKey)
		
		listType = 'MediaLib'
		listDescr = self.__model_instance.MediaLibPlayProcessDic_viaKey('pD','local')[listKey]['title']
		
		pc['listType'] = listType
		pc['listDescr'] = listDescr
		
		
				
		return pc
		
	def play_search_selectedL_new(self,commandD):	
		# Новый метод загрузки плейлиста в MPD через список CRC32 трэков без использование буфера придыдучего поиска
		self.__logger.info('method play_search_selectedL_new via MPD:%s'%(str(commandD)))
		remote_host = self.__modelDic['REMOTE_ADDR']
		
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		
		mpd_socket = mpd_instance['socket']
		host = mpd_instance['host']
		host_ip = socket.gethostbyname(host)
		
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		
		client = MPDClient()
		# Not necessary, but should not cause any trouble either
		client.disconnect()
		
		crc32L = [] 
		if 'selL'  in commandD:
			crc32L_str = base64.b64decode(commandD['selL']).decode("utf-8")
			crc32L = [int(a) for a in crc32L_str.split(',')]
		
		
		db = sqlite3.connect(dbPath)
		self.__logger.info('in play_search_selectedL_new: play to [%s]'%(str(host)))
		resL = asyncio.run(load_mpd_playlist_viaTrackCRC32L(db,client,host_ip,mpd_socket,crc32L,mpdMusicPathPrefix))
		db.close()
		
		self.__logger.debug('in play_search_selectedL_new: metaD[%s]'%(str('Finished')))
		pc = {}
		return pc
		
	def play_search_selectedL_new_old(self,commandD):	
		# Новый метод загрузки плейлиста через список CRC32 трэков без использование буфера придыдучего поиска
		self.__logger.info('method play_search_selectedL_new:%s'%(str(commandD)))
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		crc32L = [] 
		if 'selL'  in commandD:
			crc32L = [int(a) for a in commandD['selL']]
			
		plS = createPlayList_viaTrackCRC32L(crc32L,None)
		#load_mpd_playlist_viaTrackCRC32L(crc32L,None)
		
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']	
		playlistpath = mediaPath + 'Plugins\\ml\\'
		
		
		f = io.open(playlistpath+'search_play.m3u8','w',encoding='utf-8')
		try:
			f.write(plS)
			f.close()
		except Exception as e:
			self.__logger.critical('Error: %s in method play_search_selectedL_new at playlist file write'%(str(e)))
			d = pickle.dumps({'Dump_Data':plS,'Error':str(e),'ErrorContext':'AT method play_search_selectedL_new at playlist file write failed:line 1614'})
				
			self.__logger.info('Dump saved at debug.dat in [%s]'%(str(os.getcwd())))
			f = open('debug.dat','w')
			f.write(d)
			f.close()
			print('Dump saved ok')
			
			
		len_pls = len(plS)
		
		pc = self.__player_handler.new_list_load(playlistpath+'search_play.m3u8',0)
		
		self.__model_instance.setplayList('search_play.m3u')
		
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		if pc['playBack_Mode']  == 1:
			pc = self.play()
		elif pc['playBack_Mode']  == 3:	
			pc = self.__player_handler.pause()
			
		#print 	'play_search_selectedL--3:'	,pc
		listType = 'Search'
		listDescr = 'play_selected'	
			
		#print search_term,type(search_term)
						
		dicData = {'title': """Search Temp list for '%s'"""%(listDescr),  'filename': 'search_play.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len_pls)}
		self.__model_instance.set_new_pD_elem('search_play.m3u',dicData)
		
		#print 	'play_search_selectedL--4:'
		pc['listType'] = listType
		pc['listDescr'] = listDescr
		
		
		print("list generated:",playlistpath)
		self.__logger.debug('in play_search_selectedL_new: metaD[%s]'%(str('Finished')))
		
		return pc
		
		
	def play_search_selectedL(self,commandD):
		self.__logger.info('method play_search_selectedL:%s'%(str(commandD)))
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		
		search_term  = ''
		searchBuf = self.__model_instance.getSearchBufD()
		
			
		if "searchTerm" in searchBuf and 'sD'in searchBuf:
			search_term = searchBuf['searchTerm']
			
		#print 	'play_search_selectedL:',search_term,len(searchBuf['sD'])
		# Убрать ниже стоящий буфер и брать из БД по db_id
		sD = searchBuf['sD']
		copy_sD = {}
			
		for a  in commandD['selL']:
			copy_sD[int(a)] = sD[int(a)]
		
		if copy_sD == {}:
			print('empty Sel list')
			return 0	
		mediaPath =	self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['mediaPath']	
		playlistpath = mediaPath + 'Plugins\\ml\\'
		
		f = open(playlistpath+'search_play.m3u','w')
		
		plS = createPlayList_fromMetaDataD(copy_sD)
		#print 	'play_search_selectedL--2:'
			#print plS
		f.write(plS)
		f.close()
		len_pls = len(plS)
		pc = self.__player_handler.new_list_load(playlistpath+'search_play.m3u',0)
		
		self.__model_instance.setplayList('search_play.m3u')
		
		pc['playBack_Mode'] = self.__model_instance.getMediaLibPlayProcess_State()['stop_flag']
		if pc['playBack_Mode']  == 1:
			pc = self.play()
		elif pc['playBack_Mode']  == 3:	
			pc = self.__player_handler.pause()
			
		#print 	'play_search_selectedL--3:'	,pc
		listType = 'Search'
		listDescr = search_term	
			
		#print search_term,type(search_term)
						
		dicData = {'title': """Search Temp list for '%s'"""%(search_term),  'filename': 'search_play.m3u', 'crc32': pc['pL_CRC32'], 'id': '{000}', 'songs': str(len_pls)}
		self.__model_instance.set_new_pD_elem('search_play.m3u',dicData)
		
		#print 	'play_search_selectedL--4:'
		pc['listType'] = listType
		pc['listDescr'] = listDescr
		
		print('OK')
		
		return pc

	def new_object_create(self,commandD):
		self.__logger.info('method action new_object_create:%s'%(str(commandD)))
		object_data = {}
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']		
		if 'object_data' in commandD:
			object_data = commandD['object_data']
			
			fieldL =['object_name','object_search_list','object_type','object']
			for a in fieldL:
				if a not in object_data:
					print("Wrong data params  for artist save",a)
					return 
			
			
		if 	object_data != {}:
			if object_data['object'] == 'artist':
				try:
					retD = saveArtistD_intoDB(dbPath,object_data['object_name'],object_data['object_search_list'],None,object_data['object_type'],[],'',None)
					if retD['result'] != None and retD['result']!= -1:
						artist_crc32 = retD['artist_crc32']
				except Exception as e:
					print("Error at artist save",e)		
					
				print('retD:',retD)	
				
			elif object_data['object'] == 'album':	
				try:
					retD = saveAlbum_simple_intoDB(dbPath,object_data['object_name'],object_data['object_search_list'],None,object_data['object_type'],[],'',None)
					if retD['result'] != None and retD['result']!= -1:
						album_crc32 = retD['album_crc32']
				except Exception as e:
					print("Error at album save",e)		
					
				print('retD:',retD)	
				
		#print 	object_data
		
		
		return 1
		
		
		
	def artist_refinment_db_save(self,commandD):
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		self.__logger.info('method action artist_refinment_db_save:%s'%(str(commandD)))
		fieldL =['artist_name','search_term','main_artist','sel_idL']
		for a in fieldL:
			if a not in commandD:
				print("Wrong data params  for artist save",a)
				return 
			#print commandD['search_term']
		artist_name = commandD['artist_name']
		search_term = commandD['search_term']
		main_artist = commandD['main_artist']
		reference_type = commandD['refer_type']
		if commandD['sel_idL'] != '':
			ref_artistL = commandD['sel_idL']
		else:
			ref_artistL = []
			#print artist_name,search_term,main_artist
		artist_crc32 = None
		print('ref_artistL=',ref_artistL)
			#artist_crc32 = saveArtistD_intoDB(artist_name,search_term,ref_artistL,main_artist)
			
		retD = {}	
		try:
			
			retD = saveArtistD_intoDB(dbPath,artist_name,search_term,main_artist,None,ref_artistL,reference_type,None)
			
			if retD['result'] != None and retD['result']!= -1:
				artist_crc32 = retD['artist_crc32']
				
		except Exception as e:
			print("Error at artist save",e)
		if artist_crc32 != None:
			print("Artist %s saved Ok"%str(artist_crc32))
			if main_artist == 'X':
				#self.__ReportBufD['artistD'][artist_crc32]['main'] = True
				self.__model_instance.set_ReportBuf_forArtist_id(artist_crc32,True,'main')
				print("Artist report buffer update  Ok")
			else:
				self.__model_instance.set_ReportBuf_forArtist_id(artist_crc32,False,'main')
				print("Artist report buffer update  Ok")
				
			
		else:
			print("Artist %s not saved due to ERROR"%str(artist_crc32))
			return 0
		return 1	
		
	def tag_assignament_db_save(self,commandD):
		
		self.__logger.info('method action do_assignement save:%s'%(str(commandD)))
		#{'keyL':keyL,'cfgD': {'list_type':'edit_hard_tag','action_mode':commandD['action_mode'],'tagId':tagId},'time_stamp':time.time()}
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		deltaL_Dic = self.__model_instance.get_genKeyL()
		cfgD = deltaL_Dic['cfgD']
		print('cfgD:',cfgD,"""deltaL_Dic['time_stamp']=""",deltaL_Dic['time_stamp'])
		if commandD['action_key'] != str(deltaL_Dic['time_stamp']):
			print('save fail 1',commandD['action_key'],str(deltaL_Dic['time_stamp']))	
			return 0
		if int(commandD['tag_id']) != cfgD['tagId']:
			print('save fail 2')	
			return 0	
		print('save 1')	
		TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
		print('save 2')	
		DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')
		print('save 3',deltaL_Dic['keyL'],cfgD['action_mode'],	cfgD['tagId'])	
	
		res = Tag_Assignement_delta_update(dbPath,deltaL_Dic['keyL'],cfgD['action_mode'],DB_metaIndxD,cfgD['tagId'],TagD)
		print('save 4')
		if res == 1:
			self.__model_instance.set_genKeyL({},{},'init')
			return 1
		else:
			return 0
			
	def get_albumes_cmpl_clast(self,commandD):			
		self.__logger.info('get_albumes_cmpl_clast: [%s] '%(str(commandD)))
		search_termL = commandD['search_term'].split(';')
		folderL =[]
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		if 'srch_folder_key' in commandD:
			srch_folder_key=commandD['srch_folder_key']
			folderL = self.__model_instance.get_folderL_via_folder_key(srch_folder_key)
			print('folderL:',folderL)
		
		search_object_key = "artist"	
		
		if 'object' in commandD:
			if commandD['object'] in ['artist','album']:
				search_object_key = commandD['object']
				
		
		t = time.time()
		print("artist album db duplicates search Start") 
		search_termD = {}
			
		if search_object_key == 'artist':
			search_termD['album'] = None
			search_termD['artist'] = search_termL[0]
		else:
			search_termD['album'] = search_termL[0]
			search_termD['artist'] = None		
		
		album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,search_termD,folderL,None,None)
		
		compls_clastDL = get_discs_duplacates(dbPath,album_artist_metaD_db['albumD'],4)
		
		albumes_cmplDL = []
		cnt = 0	
		for a in compls_clastDL:
			cnt+=1
			cmpnt_key = zlib.crc32(bytes(str(time.time()),encoding = 'utf-8')+bytes(cnt))
			print(cnt,':*****',a,len(compls_clastDL[a]['clast_contentLD']),'[',compls_clastDL[a]['prop_clast_name'])
			item_cmpl = {'prop_clast_name':compls_clastDL[a]['prop_clast_name'],'clast_contentLD':[],'index':cnt,'cmpnt_key':cmpnt_key,'colorcl':'artist init even','checked':True,'rel_type':''}
			for item in compls_clastDL[a]['clast_contentLD']:
				#if 'part' in item['disc_name'].lower():
				
				item_cmpl['clast_contentLD'].append({'disc_name':item['disc_name'],'index':item['key'],'colorcl':'album init even','checked':True})
				print(item['head'],'--->',item['disc_name'],item['parentD'])
			print()
			
			albumes_cmplDL.append(item_cmpl)
			
		self.__modelDic['albumes_cmpl_maintain_buf'] = albumes_cmplDL
		return 1
		
	def maintain_album_component(self,commandD):	
		self.__logger.info('maintain_album_component: [%s] '%(str(commandD)))
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		result = False
		if 'alb_cmpl_struct' in commandD:
			album_component = commandD['alb_cmpl_struct']['parent_album_name']	
			rel_type = commandD['alb_cmpl_struct']['rel_type']	
			cmpnt_key =  commandD['alb_cmpl_struct']['cmpnt_key']	
			cmpnt_index = commandD['alb_cmpl_struct']['cmpnt_index']	
			refalbum_CRC32L = [item['index'] for item in commandD['alb_cmpl_struct']['clast_contentLD'] if item['checked']]
			print('album;',album_component,rel_type,refalbum_CRC32L)
			try:
				retD = saveAlbum_simple_intoDB(dbPath,album_component,None,None,rel_type,refalbum_CRC32L,rel_type,None)
				if retD['result'] != None and retD['result']!= -1:
					album_crc32 = retD['album_crc32']
					result = True
			except Exception as e:
				print("Error at album save",e)		
			
			
			self.__modelDic['maintain_album_component'] = {'result':result,'cmpnt_key':cmpnt_key,'cmpnt_index':cmpnt_index}	
						
			print('retD:',retD)	
		
		
		return 1
		
	def	do_artist_search(self,commandD):	
		# В этой функции в зависимости от команды искать либо в буфере всех метаданных либо только в метаданных по базе Артистов.
		self.__logger.debug('do_artist_search: [%s] '%(str(commandD)))
		search_termL = commandD['search_term'].split(';')
		srch_folder_key = ''
		command = commandD['artists_maintain']
		folderL =[]
		folder_keyL = []
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		new_only = False
		idl_param = None
		if 'idl_param' in commandD:
			idl_param = commandD['idl_param'].upper()
			if idl_param == "TRCKIDLONEW":
				new_only=True
			elif idl_param == "TRCKIDLWOEC":
				pass
			elif idl_param == "ALBLOGFULL":	
				albumD = check_loaded_albums_2_lib('')
				folder_keyL = [albumD[a]['folder_key'] for a in albumD if not albumD[a]['album_registered']]
			elif idl_param == "ALBLOGl10":	
				albumD = check_loaded_albums_2_lib('')
				folder_keyL = [albumD[a]['folder_key'] for a in albumD if not albumD[a]['album_registered']]
			
		search_object_key = "artist"	
		
		if 'object' in commandD:
			if commandD['object'] in ['artist','album']:
				search_object_key = commandD['object']
			
			
		if search_termL[0].strip() == 'Search_text':
			search_termL = ['',]
		self.__logger.debug('before set_All_metaD')
		
		if 'srch_folder_key' in commandD:
			srch_folder_key=commandD['srch_folder_key']
			if folderL == []:
				folderL = self.__model_instance.get_folderL_via_folder_key(srch_folder_key)
			print('folderL:',len(folderL),idl_param,list(commandD.keys()))
			
		if commandD['artists_maintain'] == "search_artist_db":
			t = time.time()
			print("artist album db retrieve Start") 
			search_termD = {}
			
			if search_object_key == 'artist':
				search_termD['album'] = None
				search_termD['artist'] = search_termL[0]
			else:
				search_termD['album'] = search_termL[0]
				search_termD['artist'] = None
			album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,search_termD,folderL,None,None)
			print("artist album db retrieve End" ,str(str((time.time()-t))))
			self.__modelDic['artist_album_maintain_proc_buf_db'] = album_artist_metaD_db
			
			self.__logger.debug('before 1 map_meta_artist_album_struct_to_view_json ')	
			artistD = self.map_db_artist_album_struct_to_view_json(album_artist_metaD_db,'init')	
			# ВНИМАНИЕ! proc_state - является ключем для bufferD													
			vldt_art_key = zlib.crc32(b'art_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
			vldt_albNSA_key = zlib.crc32(b'alb_NSA_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
			self.__modelDic['artist_album_maintain_proc_buf'] = {
																'artist_view':{'dataD':{'initial':artistD['artistD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
																'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
																'checked_pageL':[1]
																},
																'album_NSA_view':{'dataD':{'initial':artistD['not_single_artist_albumD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
																'proc_state':'initial','validity_key':vldt_albNSA_key,'message_log':'','cur_page':1,
																'checked_pageL':[1]
																},
																'active_view':'artist',
																'proc_type':'data_from_db'
																}
			
		
		
			
		# Если метаданные еще не получены то нижестоящая фукция их соберет, если уже были собраны,то из нее быстрый выход
		elif commandD['artists_maintain'] == "search_artist_data":
			if 'ALBLOG' in idl_param and folder_keyL != []:
				DbIdL = getDbIdL_viaAlbumCRC32_List(dbPath,folder_keyL,None)
				albumlog_metaD = getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None,'progress')
				ReportBufD = get_all_artists_in_metaD(albumlog_metaD,search_object_key,search_termL,'with_album_stat','album_va_check','new_only')
				self.__modelDic['ReportBufD']	= ReportBufD
				self.__model_instance.setReportBuf_forArtist(ReportBufD)
			else:
				self.__model_instance.set_All_metaD(srch_folder_key)
				self.__logger.debug('before get_All_metaD')
				# Получаем текущие метаданные ARTIST --> ALBUMES на основе данных из трэков
				All_metaD = self.__model_instance.get_All_metaD()['resD']
				
				folder_filter_key = self.__model_instance.get_All_metaD_filter_key()
				# В буффере контроллера All_metaD находится только для отладочных целей, его надо удалить
				#print "Do not forger to delete this!!! "
				#self.__modelDic['All_metaD'] = All_metaD
				self.__modelDic['folder_filter_key'] = folder_filter_key
				ReportBufD = {}
				self.__logger.debug('before get_all_artists_in_metaD,search_termL:%s'%(str(search_termL)))	
				if new_only:
					ReportBufD = get_all_artists_in_metaD(All_metaD,search_object_key,search_termL,'with_album_stat','album_va_check','new_only')
				else:
					ReportBufD = get_all_artists_in_metaD(All_metaD,search_object_key,search_termL,'with_album_stat','album_va_check')
				self.__modelDic['ReportBufD']	= ReportBufD
				self.__logger.debug('before setReportBuf_forArtist')	
				self.__model_instance.setReportBuf_forArtist(ReportBufD)
				
				self.__logger.debug('before 2 map_meta_artist_album_struct_to_view_json')	
				
			artistD = self.map_meta_artist_album_struct_to_view_json(ReportBufD,'init')	
			
			# Надо сделать такой же список только со стороны альбомов но не всех а только сборников по критерию песни разных артистов
			#print artistD.keys()
			
															
			# ВНИМАНИЕ! proc_state - является ключем для bufferD													
			vldt_art_key = zlib.crc32(b'art_buf'+bytes(str(time.time()),encoding = 'utf-8'))
			vldt_albNSA_key = zlib.crc32(b'alb_NSA_buf'+bytes(str(time.time()),encoding = 'utf-8'))
			self.__modelDic['artist_album_maintain_proc_buf'] = {
																'artist_view':{'dataD':{'initial':artistD['artistD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
																'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
																'checked_pageL':[1]
																},
																'album_NSA_view':{'dataD':{'initial':artistD['not_single_artist_albumD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
																'proc_state':'initial','validity_key':vldt_albNSA_key,'message_log':'','cur_page':1,
																'checked_pageL':[1]
																},
																'active_view':'artist',
																'proc_type':'data_initial_load'
																}
																
				
			
			self.__logger.debug('in do_artist_search DATA OK')
		
		if commandD['artists_maintain'] == "search_artist":
		# эта функция очень медленная так как собирает фактически всю статистику АРТИСТ->АЛЬБОМ->Список трэков ID и Статистика трэков и альбомов 
			self.__model_instance.set_All_metaD(srch_folder_key)
			self.__logger.debug('before get_All_metaD')
			# Получаем текущие метаданные ARTIST --> ALBUMES на основе данных из трэков
			All_metaD = self.__model_instance.get_All_metaD()['resD']
			# В буффере контроллера All_metaD находится только для отладочных целей, его надо удалить
			#print "Do not forger to delete this!!! "
			#self.__modelDic['All_metaD'] = All_metaD
			
			
			self.__logger.debug('before get_all_artists_in_metaD,search_termL:%s'%(str(search_termL)))	
			ReportBufD = get_all_artists_in_metaD(All_metaD,search_object_key,search_termL,'with_album_stat')
			self.__modelDic['ReportBufD']	= ReportBufD
			self.__logger.debug('before setReportBuf_forArtist')	
			self.__model_instance.setReportBuf_forArtist(ReportBufD)
			
			self.__logger.debug('in do_artist_search OK')
		elif commandD['artists_maintain'] == "search_artist_db":
			# тут берем метаданных данные из таблицы Артистов, естественно без живой статистики альбомов и трэков
			# фильтруем по поисковому слову 
			# устанавливаем все буфферы
			
			pass
		self.__logger.debug('do_artist_search: - Finished ')	
	
	def map_artist_album_categ_assignment_to_view_json(self,artist_album_categ_structD,process_phase):
		# Назначение функции подготовить вью по аналогии с вью начальной загрузки или ДБ вью
		# Данные об индексах артистов и альбомов получаются из чтения назначения категоризаций
		# 
		# Т.к альбомы информации о пересечении артистов и альбомов в сатегоризационном назначении нет 
		# то его надо восстановить
		# во View показываются только те объекты, которые явно присутствуют в категоризации
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		not_single_artist_albumD_list = []
		artistD_list = []
		
		artistD_extend = {}
		
		artistL = [item['key'] for item in artist_album_categ_structD['artistL']]
		print('artistL:',artistL)
		self.__logger.debug('In map_artist_album_categ_assignment_to_view_json -> Start')
		
		albumL = [item['key'] for item in artist_album_categ_structD['albumL']]
		print('albumL:',albumL)
		
		
		
		
		artist_to_album_relD = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(dbPath,None,artistL,albumL,'with_album_metaD','with_artist_metaD','with_relation')
		album_metaD = artist_to_album_relD['albumD']
		artist_metaD = artist_to_album_relD['artistD']
		
		artist_rel_albumD = artist_to_album_relD['artist_rel_albumD']
		album_rel_artistD = artist_to_album_relD['album_rel_artistD']
		
		# Восстанавиваем пересечение артистов и альбомов
		if artist_to_album_relD['artistL_extend'] != []:
			artistD_extend = getArtist_Album_relationD_and_simpleMetaD_viaCRC32L(dbPath,None,artist_to_album_relD['artistL_extend'],[],'with_artist_metaD','with_relation')
			for a in artistD_extend['artistD']:
				artist_metaD[a] = artistD_extend['artistD'][a]
				artistL.append(a)
			
		
		self.__modelDic['artist_to_album_relD'] = artist_to_album_relD
		
		print('Got relation ok')
		
		
		
		artistD  = {}
		artist_metaD_db = {}
		
		artist_index = 1
		for artistcrc32 in artistL:
		
			
			print('-------artist>',artistcrc32)
			
			
			album_num = 0
			if artistcrc32 in artist_rel_albumD:
				album_num = len(artist_rel_albumD[artistcrc32]['albumD'])
			else:	
				print('missed albumes for ',artistcrc32,artist_metaD[artistcrc32]['artist'], end=' ')
				print(list(artist_rel_albumD.keys()))
			
			#albumL = artist_rel_albumD[artistcrc32]['albumD']
			checked = True
			if artistcrc32 in artist_to_album_relD['artistL_extend']:
					checked = False
			artistD_elem = {'key':artistcrc32,'album_num':album_num,'song_num':0,
						'albumL':[],'checked':checked,
						'expanded':False,'process_type':process_phase,'main':artist_metaD[artistcrc32]['main'],
						'obj_type':'artist','index':'art'+str(artist_index),'artist':artist_metaD[artistcrc32]['artist'],
						'is_in_db':False,'id_artist':artist_metaD[artistcrc32]['id_artist']}
						
						
			artistD_elem['pos_num'] = artist_index
			
			if ( artist_index % 2 ):
				even_odd = 'even'
			else:
				even_odd = 'odd'
			obj_type = 'artist'	
			artist_index+=1
			
			try:
				artistD_elem['colorcl']	= ' '.join([obj_type,process_phase,even_odd])
			except Exception as e:
				print('Error colored artist:',e)	
			
			artistD_list.append(artistD_elem)			
		
		
		albumD = {}
		album_metaD_db = {}
		
		album_index = 1
		pos = 1
		
		print() 
		print('artist map OK')
		
		# Читаем метаданные по альбомам
		tb_removed_NSA_L = []
		for albumcrc32 in albumL:
			# Суть этой ветки получить метаданные альбома и восстановить артиста по альбому если он не назначен в категории, если аольбом NSA то засунуть его в НСА лист
			
			print('album>',albumcrc32)
				
			album_display_name = str(pos)+'. '+album_metaD[albumcrc32]['album']
			
			album_checked = True
			obj_type = 'album'	
			not_single_artist = False
			
			if (pos % 2):
				even_odd = 'even'
			else:
				even_odd = 'odd'
			
			album_item = {'key':albumcrc32,'album':album_metaD[albumcrc32]['album'],'album_display_name':album_display_name,'expanded':False,
						'colorcl':' '.join([obj_type,process_phase,even_odd]),'album_crc32':albumcrc32, 'song_num': album_metaD[albumcrc32]['tracks_num'],
						'format': album_metaD[albumcrc32]['format'],'checked':album_checked,'process_type':process_phase,'artistL':[],
						'is_in_db':False,'obj_type':'album','not_single_artist':not_single_artist,'album_pos':pos,'index':'alb'+str(album_index)}
			pos+=1
			album_index+=1
			
			
			
			if album_metaD[albumcrc32]['album_type'] == '':
				print(album_metaD[albumcrc32]['album'], '-->is NSA')
				album_item['not_single_artist'] = True
				if albumcrc32 in album_rel_artistD:
					#print albumcrc32, album_metaD[albumcrc32]['album_type'] 	
				#print 'album_rel_artistD:',album_rel_artistD
					for artistcrc32 in album_rel_artistD[albumcrc32]['artistD']:
						print(artistcrc32)
						for item in artistD_list:
							#print item.keys()
							if item['key'] == artistcrc32:
								item_copy = item.copy()
								item_copy['visible'] = True
								if artistcrc32 not in tb_removed_NSA_L and artistcrc32 in artist_to_album_relD['artistL_extend']: 
									tb_removed_NSA_L.append(artistcrc32)
								album_item['artistL'].append(item_copy)
								
								
				
				
				not_single_artist_albumD_list.append(album_item)
			else:
				if albumcrc32 in album_rel_artistD:
					print(albumcrc32, album_metaD[albumcrc32]['album_type']) 	
				#print 'album_rel_artistD:',album_rel_artistD
					for artistcrc32 in album_rel_artistD[albumcrc32]['artistD']:
						print(artistcrc32)
						for item in artistD_list:
							#print item.keys()
							if item['key'] == artistcrc32:
								
								album_item['visible'] = True
								album_item['album_song_num'] = album_metaD[albumcrc32]['tracks_num']
								item['albumL'].append(album_item)
								
				
			
		print() 
		print()
		print('album map OK')
	
		
		artist_index = 1
		
		for a in tb_removed_NSA_L:
			for item in artistD_list:
				if item['key'] == a:
					#pass
					artistD_list.remove(item)
					#item['visible'] = False
		
		# Ключи {'key':a[0],'value':a[1],'album_type':a[2]} 
		print(' mapping OK',artistD_list)
		
		self.__logger.debug('In map_artist_album_categ_assignment_to_view_json -> Finished')
		return {'artistD_list':artistD_list,'not_single_artist_albumD_list':not_single_artist_albumD_list}	
		
	def map_db_artist_album_struct_to_view_json(self,db_artist_album_structD,process_phase):
		self.__logger.debug('in map_db_artist_album_struct_to_view_json - Start')
		artistD = db_artist_album_structD['artistD']
		albumD = db_artist_album_structD['albumD']
		not_single_artist_albumL = db_artist_album_structD['not_single_artist_albumL'] 
		artistD_list = []
		
		phase = process_phase
		
		even_odd = ''
		album_KeyL = ['artist', 'is_in_rep','is_in_db', 'main','albumD']
		names_ignorL = ['va','na','na_','various','various artists','na album']
		artist_index=1
		album_index=1
		
		for a in artistD:
			obj_type = 'artist'	
			# если артист для NSA пропускаем его тут
			
			if artistD[a]['for_nsa_only']:
				continue
			artistD_elem = {'key':str(a),'album_num':len(artistD[a]['albumD']),'song_num':artistD[a]['artist_song_num'],'albumL':[],'checked':True,
						'expanded':False,'process_type':process_phase,'main':artistD[a]['main'],
						'obj_type':'artist','index':'art'+str(artist_index),'artist':artistD[a]['artist'],'is_in_db':False,'id_artist':artistD[a]['id_artist']}
						
			
			artistD_elem['pos_num'] = artist_index
			
			if ( artist_index % 2 ):
				even_odd = 'even'
			else:
				even_odd = 'odd'
			obj_type = 'artist'	
			
			artist_index+=1
			
			try:
				artistD_elem['colorcl']	= ' '.join([obj_type,phase,even_odd])
			except Exception as e:
				print('Error colored artist:',e)	
				
			pos = 1	
			albumD_tmp = {}
			for b in artistD[a]['albumD']:
				cD = albumD[b]
				
				obj_type = 'album'	
				album_checked = True
				not_single_artist = artistD[a]['albumD'][b]['not_single_artist']
				
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
				obj_type = 'album'	
							
				#album_display_name = str(pos)+'. '+cD['album']
				
				
				
				album_item = {'album':cD['album'],'key':str(b),'album_display_name':'',
								'colorcl':' '.join([obj_type,phase,even_odd]),'album_crc32':str(cD['album_crc32']), 'album_song_num': cD['album_song_num'],
								'format': cD['format'],'visible':False,'checked':album_checked,'artist_key':str(a),'process_type':process_phase,'main':cD['main'],
								'is_in_db':False,'obj_type':'album','not_single_artist':not_single_artist,'index':'alb'+str(album_index),'id_album':cD['id_album']}
				album_index+=1
				pos+=1
								
				albumD_tmp[b]= album_item
				
			album_keysL = [(albumD_tmp[b]['album'],b) for b in albumD_tmp]
			album_keysL.sort()
			for b in album_keysL:
				key = b[1]
				album_display_name = str(album_keysL.index(b)+1)+'. '+albumD_tmp[key]['album']
				albumD_tmp[key]['album_display_name'] = album_display_name
				artistD_elem['albumL'].append(albumD_tmp[key])
			
			
			artistD_list.append(artistD_elem)
			
			
		
		pos = 1
		artist_index = 1
		album_index = 1	
		not_single_artist_albumD_list = []
		
		for a in not_single_artist_albumL:
		
			artistL = []	
			artist_pos = 1	
			for b in albumD[a]['artistD']:
					obj_type = 'artist'
					#print artistD[a].keys()
					if ( artist_pos % 2 ):
						even_odd = 'even'
					else:
						even_odd = 'odd'
						
					try:
						colorcl	= ' '.join([obj_type,phase,even_odd])
					except Exception as e:
						print('Error colored artist:',e)			
						
					#print 'artist:',artistD[a]['artist']
						
					
					artist_checked = True
					
					artist_item = {'key':str(b),'artist':'   '+artistD[b]['artist'],'album_num':1,'song_num':albumD[a]['artistD'][b]['song_num'],'checked':artist_checked,
										'process_type':process_phase,'obj_type':'artist','pos_num':artist_pos,'visible':False,
										'colorcl':colorcl,'is_in_db':False,'main':artistD[b]['main'],'index':'art'+str(artist_index)}	
					artist_pos+=1
					artistL.append(artist_item)
					artist_index+=1
			
			album_display_name = str(pos)+'. '+albumD[a]['album']
			#print album_display_name
			album_checked = True
			obj_type = 'album'	
			not_single_artist = True
			
			if (pos % 2):
				even_odd = 'even'
			else:
				even_odd = 'odd'
			
			album_item = {'key':str(a),'album':albumD[a]['album'],'album_display_name':album_display_name,'expanded':False,
			'colorcl':' '.join([obj_type,phase,even_odd]),'album_crc32':str(a), 'song_num': albumD[a]['album_song_num'],
			'format': albumD[a]['format'],'checked':album_checked,'process_type':process_phase,'artistL':artistL,
			'is_in_db':False,'obj_type':'album','not_single_artist':not_single_artist,'album_pos':pos,'index':'alb'+str(album_index)}
			pos+=1
			album_index+=1
			
			not_single_artist_albumD_list.append(album_item)
		
		print('mapping db Ok')
		self.__logger.debug('in map_db_artist_album_struct_to_view_json - Finished')
		return {'artistD_list':artistD_list,'not_single_artist_albumD_list':not_single_artist_albumD_list}
		
	def map_meta_album_tracks_struct_to_view_json(self,meta_tracks_structD,album_artistD):
		# Формирование структурного представления для JSON упаковки и передачи на web клиент
		self.__logger.debug('in map_meta_album_tracks_struct_to_view_json: [%s] - start'%(str(len(meta_tracks_structD))))
		album_listD = {}
		albumL =[]
		
		#allmFD[cue_item_name_crc32] = #{'orig_fname':orig_file_path,'last_modify_date':last_modify_date,'album':album_path,'album_path':album_path,'album_crc32':album_path_crc32#,'file':cue_item_name,'cueNameIndx':i,'ftype':ftype,'cue':'X'}
		
		# Collect all albumes
		cnt = 0
		for track_crc32, item in list(meta_tracks_structD.items()):
			cnt+=1
			#print 'track_crc32:',track_crc32
			try:
				item['metaD']['number'] = int(item['metaD']['tracknumber'])
			except Exception as e:
				self.__logger.critical('Exception [%s] in map_meta_album_tracks_struct_to_view_json  [number] crc32 %s'%(str(e),str(track_crc32)))	
				item['metaD']['number'] = cnt
			
			#print 1.2
			#print item['metaD'].keys()
			#print item.keys()
			item['metaD']['track_crc32'] = track_crc32
			#print 1.3
			item['metaD']['time_sec'] = int(item['metaD']['time_sec'])
			#print 1.4
			if 'db_track' in item:
				item['metaD']['db_track'] = item['db_track']
			else:
				item['metaD']['db_track'] = 0
			#print 1.5,item['db_track']
			if 'db_artist' in item:
				item['metaD']['db_artist'] = item['db_artist']
			else:
				item['metaD']['db_artist'] = 0
			
			NSA = '-'
			#print 2
			if item['album_crc32'] not in album_listD:
				#print 3, item['album_crc32'], album_artistD.keys()
				if len(album_artistD[item['album_crc32']]['artistDataD']) > 1:
					NSA = 'X'
				
				album_listD[item['album_crc32']]={'album_crc32':item['album_crc32'],'album':item['metaD']['album'],'format':item['ftype'],'TrackL':[item['metaD']],'db_album':item['db_album'], 'NSA':NSA,'tracks_number':item['album_tracks_number']}
				if 'cue' in item:
					album_listD[item['album_crc32']]['cue'] = 'cue'
				else:
					album_listD[item['album_crc32']]['cue'] = '-'
				
			else:
				album_listD[item['album_crc32']]['TrackL'].append(item['metaD'])
			
		for a in album_listD:
			album_listD[a]['TrackL'].sort(key=operator.itemgetter('number'),reverse=False)
		
		# Build album list based on album_listD	
		for a in album_listD:
			albumL.append(album_listD[a])
			
		albumL.sort(key=operator.itemgetter('album'),reverse=False)	
		self.__logger.debug('in map_meta_album_tracks_struct_to_view_json: [%s] - finished'%(str(len(albumL))))
		return {'albumL':albumL,'not_single_artist_albumD_list':[]}
		
	def map_meta_artist_album_struct_to_view_json(self,meta_artist_album_structD,process_phase):
		# формироует начальные буфера для двойного представления 'artistD_list':artistD_list,'not_single_artist_albumD_list':not_single_artist_albumD_list
		# ВНИМАНИЕ album_song_num касается только представления альбома по артисту NSA в представлении артиста есть song_num т.е. количество песен по этому
		# артисту в альбоме	
		ReportBufD = meta_artist_album_structD
		artistD_list = []
			
		#phase = 'tb_save'
		phase = process_phase
		
		even_odd = ''
		album_KeyL = ['artist', 'is_in_rep','is_in_db', 'main','albumD']
		names_ignorL = ['va','na','na_','various','various artists','na album']
		artist_index=1
		album_index=1
		for a in ReportBufD['statL']:
		
			artistD = {'key':a[3],'album_num':a[0],'song_num':a[2],'albumL':[],'checked':True,
						'expanded':False,'process_type':process_phase,
						'obj_type':'artist','index':'art'+str(artist_index)}
			artist_index+=1
			
			skip = False
			
			for b in ReportBufD['artistD'][a[3]]:
				#print b
				if b in album_KeyL:
					#if (new_only) and (b == 'is_in_db'):
						# сделать первую проверку на наличие в дб и если только новые то далее допроверить и если опят в ДБ то пропуск.
					if b == 'albumD':
					
						
						cD = ReportBufD['artistD'][a[3]][b]
						#print cD
						pos = 1
						for c in cD:
							
							if (pos % 2):
								even_odd = 'even'
							else:
								even_odd = 'odd'
							obj_type = 'album'	
							
							album_display_name = str(pos)+'. '+cD[c]['album']
							
							try:
								album_is_in_db = cD[c]['is_in_db']
								album_checked = True
								#album_is_in_db = cD[c]['is_in_db']
								if album_is_in_db or cD[c]['not_single_artist']:
									album_checked = False
									
								album = cD[c]['album']
								if album.strip().lower() in names_ignorL: 
									album_checked = False
								
								album_item = {'key':c,'album':cD[c]['album'],'album_display_name':album_display_name,
								'colorcl':' '.join([obj_type,phase,even_odd]),'album_crc32':cD[c]['album_crc32'], 'album_song_num': cD[c]['song_num'],
								'format': cD[c]['format'],'visible':False,'checked':album_checked,'artist_key':a[3],'process_type':process_phase,
								'is_in_db':album_is_in_db,'obj_type':'album','not_single_artist':cD[c]['not_single_artist'],'index':'alb'+str(album_index)}
								album_index+=1
								
								
								artistD['albumL'].append(album_item)
								
									
							except Exception as e:
								print('Error :',e)
							pos+=1
					elif b == 'is_in_db':
						#print b,ReportBufD['artistD'][a[3]].keys()
						if ReportBufD['artistD'][a[3]][b]:
							artistD['checked'] = False
						else:
							artistD['checked'] = True
							
						artistD[b] = ReportBufD['artistD'][a[3]][b]	
					
						
					else:	
						artistD[b] = ReportBufD['artistD'][a[3]][b]
						
					
			
			pos_num = ReportBufD['statL'].index(a)+1			
			artistD['pos_num'] = pos_num
			
			if ( pos_num % 2 ):
				even_odd = 'even'
			else:
				even_odd = 'odd'
			obj_type = 'artist'	
			
			try:
				artistD['colorcl']	= ' '.join([obj_type,phase,even_odd])
			except Exception as e:
				print('Error colored artist:',e)	
				
			artist = artistD['artist']
			if artist.strip().lower() in names_ignorL: 
				artistD['checked'] = False
				
			
			artistD_list.append(artistD)	
		# Проверяем есть ли альбомы в которых задействован не только выявленыые выше артисты
		# Для таких альбомов делаем специальную структуру для которой будет дополнительное представление		
		not_single_artist_albumD_list = []
		
		album_songD = meta_artist_album_structD['album_songD']
		
		keysL = [(meta_artist_album_structD['album_songD'][a]['album'],a) for a in meta_artist_album_structD['not_single_artist_albumL']]
		keysL.sort()
		keysL = [a[1] for a in keysL]
		print(keysL)
		pos = 1
		artist_index = 1
		album_index = 1	
		for c in keysL:
			
			
			
			album_display_name = str(pos)+'. '+album_songD[c]['album']
			
			try:
				album_is_in_db = album_songD[c]['is_in_db']
				album_checked = True
				#album_is_in_db = album_songD[c]['is_in_db']
				if album_is_in_db:
					album_checked = False
					
				album = album_songD[c]['album']
				#print album,album_is_in_db
				if album.strip().lower() in names_ignorL: 
					album_checked = False
					
				artistL = []	
				artistD = album_songD[c]['artistD']
				artist_pos = 1
				
				for a in artistD:
					obj_type = 'artist'
					#print artistD[a].keys()
					if ( artist_pos % 2 ):
						even_odd = 'even'
					else:
						even_odd = 'odd'
						
					try:
						colorcl	= ' '.join([obj_type,phase,even_odd])
					except Exception as e:
						print('Error colored artist:',e)			
						
					#print 'artist:',artistD[a]['artist']
						
					
					artist_checked = True
					if artistD[a]['is_in_db']:
						artist_checked = False
					
					artist_item = {'key':a,'artist':'   '+artistD[a]['artist'],'album_num':1,'song_num':artistD[a]['song_num'],'checked':artist_checked,
										'process_type':process_phase,'obj_type':'artist','pos_num':artist_pos,'visible':False,
										'colorcl':colorcl,'is_in_db':artistD[a]['is_in_db'],'main':artistD[a]['main'],'index':'art'+str(artist_index)}	
					artist_pos+=1
					artistL.append(artist_item)
					artist_index+=1
			
				obj_type = 'album'		
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
					
				album_item = {'key':c,'album':album_songD[c]['album'],'album_display_name':album_display_name,'expanded':False,
				'colorcl':' '.join([obj_type,phase,even_odd]),'album_crc32':c, 'song_num': album_songD[c]['album_song_num'],
				'format': album_songD[c]['format'],'checked':album_checked,'process_type':process_phase,'artistL':artistL,
				'is_in_db':album_is_in_db,'obj_type':'album','not_single_artist':album_songD[c]['not_single_artist'],'album_pos':pos,'index':'alb'+str(album_index)}
				album_index+=1
				
				not_single_artist_albumD_list.append(album_item)
				
					
			except Exception as e:
				print('Error in not_single_artist_albumL:',e)
			pos+=1
			
		
		return {'artistD_list':artistD_list,'not_single_artist_albumD_list':not_single_artist_albumD_list}
	
	def client_struct_restore(self,client_struct,server_struct,list_node_key,new_process_type):
		# функция проверяет логическую целостность артистов и их альбомов и сихронизирует клиентскую и серверную структуры в процессе массового сохранения,
		# до самого сохранения.
		# сохранено будет то, что выделено к сохранению в этой структуре. на клиенте активировать кнопку сохранения только после прихода этой структуры
		# любое изменение в этой структура должно блокировать сохранение. если изменили то опять проверка.
		
		# Если артист уже в базе, то он предлагается как невыбранный checked = False, проверка его альбомов происходит всегда
		# проверочная иерархия всегда если есть альбомы на сохранение
		
		# Если артист не в БД и не выделен, то отменить выборку  его альбомом, даже если они выбраны
		self.__logger.debug('in function client_struct_restore: [%s] '%(str('')))

		print('in client_struct_restore') 
		for artist_item_serv in server_struct:
			artist_index = server_struct.index(artist_item_serv)
			artist_item_client = client_struct[artist_index]
			for a in artist_item_serv:
				if a not in artist_item_client:
					artist_item_client[a] = artist_item_serv[a]
			
			list_node_serv = artist_item_serv[list_node_key]	
			list_node_client = artist_item_client[list_node_key]	
			
			
			no_albumes = True
			for album_item_serv in list_node_serv:
				list_node_index = list_node_serv.index(album_item_serv)
				list_node_item_client = list_node_client[list_node_index]
				
				
									
				for b in album_item_serv:
					if b not in list_node_item_client:
						list_node_item_client[b] = album_item_serv[b]
				
					
		return	
	def artist_album_struct_client_server_sinc_categ(self,categ_key,artist_album_struct_serv,artist_album_struct_client,list_node_key,new_process_type,mode):
		# !!!Внимание функция  вызывается ТОЛЬКО для отдельного вью.!!! или АРТИСТ или АЛЬБОМ
		
		# функция проверяет логическую целостность артистов и их альбомов и сихронизирует клиентскую и серверную структуры в процессе массового сохранения,
		# до самого сохранения.
		# сохранено будет то, что выделено к сохранению в этой структуре. на клиенте активировать кнопку сохранения только после прихода этой структуры
		# любое изменение в этой структура должно блокировать сохранение. если изменили то опять проверка.
		
		# Если артист уже в базе, то он предлагается как невыбранный checked = False, проверка его альбомов происходит всегда
		# проверочная иерархия всегда если есть альбомы на сохранение
		
		
		self.__logger.debug('in function artist_album_struct_client_server_sinc: [%s] '%(str('')))

		print('in sinc--->',list_node_key,new_process_type,mode)
		
		if list_node_key == 'artistL':
			reqParent = "select id_album from ALBUM_CAT_REL where album_crc32 = %s and object_name = '%s'"
			reqChild = "select id_artist from ARTIST_CAT_REL where artist_crc32 = %s and object_name = '%s'"
			colorcl_parent = 'album errisindb'
			colorcl_child = 'artist errisindb'
			
		elif 'albumL':
			reqParent = "select id_artist from ARTIST_CAT_REL where artist_crc32 = %s and object_name = '%s'"
			reqChild = "select id_album from ALBUM_CAT_REL where album_crc32 = %s and object_name = '%s'"
			colorcl_parent = 'artist errisindb'
			colorcl_child = 'album errisindb'
		
		# 1 Для режима add проверка, что элементы не существуют в базе.
		if mode == "add":
			db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])
			#db.text_factory = str
			c = db.cursor()
			
			
			for artist_item_client in artist_album_struct_client:
				key = artist_item_client['key']	
				req = reqParent%(key,categ_key)
				c.execute(req)
				l =c.fetchone()
				#print l
				if l != None:
					artist_item_client['checked'] = False
					artist_item_client['colorcl'] = colorcl_parent
					print('found art:',l)
				
				albumL_client = artist_item_client[list_node_key]		
				for album_item_client in albumL_client:
					key = album_item_client['key']	
					req = reqChild%(key,categ_key)
					c.execute(req)
					l =c.fetchone()
					#print l
					if l != None:
						album_item_client['checked'] = False
						album_item_client['colorcl'] = colorcl_child
						print('found album:',l)
				
			db.close()
		
		# Для режима добавления, все что селектед + все что не выбрано - игнорируется. свертывается, невидимится.
		
		for artist_item_serv in artist_album_struct_serv:
			artist_index = artist_album_struct_serv.index(artist_item_serv)
			artist_item_client = artist_album_struct_client[artist_index]
			
			
				
			for a in artist_item_serv:
				
				
				if a == 'checked' :
				
					if mode == "add" and ( not artist_item_client['checked'] ):
						pass
					else:	
						# Это поле служит индикатором, что его надо учесть при апдейте БД. либо удалить, либо добавить
						artist_item_client['process_type'] = new_process_type
						if mode == "update":
							if artist_item_client[a] != artist_item_serv[a]:
								
								if not artist_item_client[a]:   # значить удалить
									artist_item_client['process_type'] = 'tb_delete'
									artist_item_client['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],new_process_type+' remove')
								else:
									artist_item_client['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],new_process_type+' add')
								
								continue
							else:
								artist_item_client['process_type'] = 'tb_ignore'
								continue
						elif mode == "add":
							if artist_item_client['checked']:
								artist_item_client['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],new_process_type+' add')
								continue
								
					
				if a not in artist_item_client:
					artist_item_client[a] = artist_item_serv[a]
					
			
				artist_item_client['expanded'] = True
			
			albumL_serv = artist_item_serv[list_node_key]	
			
			albumL_client = artist_item_client[list_node_key]	
			
			
			
			no_albumes = True
			for album_item_serv in albumL_serv:
				album_index = albumL_serv.index(album_item_serv)
				album_item_client = albumL_client[album_index]
				
				album_item_client['visible'] = False
				artist_item_client['expanded'] = False					
				for b in album_item_serv:
					if b == 'checked' :
						if mode == 'add' and ( not album_item_client['checked'] ):
							album_item_client['visible'] = True
						else:	
							if 	mode == 'update':
								if album_item_client[b] != album_item_serv[b]:
									album_item_client['process_type'] = new_process_type
									album_item_client['visible'] = True
									artist_item_client['expanded'] = True
							
									if not album_item_client[b]:   # значить удалить
										album_item_client['process_type'] = 'tb_delete'
										album_item_client['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],new_process_type+' remove')
									else:
										album_item_client['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],new_process_type+' add')
										
									continue		
							elif mode == 'add':
								if album_item_client['checked']:
									album_item_client['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],new_process_type+' add')
									album_item_client['process_type'] = new_process_type
									artist_item_client['expanded'] = True
									album_item_client['visible'] = True
									continue	
							
					if b not in album_item_client:
						album_item_client[b] = album_item_serv[b]
				
			
				
				no_albumes = False
				
					
			
			if no_albumes:
				artist_item_client['expanded'] = False
			
					
		return						
	def artist_album_struct_client_server_sinc(self,artist_album_struct_serv,artist_album_struct_client,list_node_key,new_process_type):
		# функция проверяет логическую целостность артистов и их альбомов и сихронизирует клиентскую и серверную структуры в процессе массового сохранения,
		# до самого сохранения.
		# сохранено будет то, что выделено к сохранению в этой структуре. на клиенте активировать кнопку сохранения только после прихода этой структуры
		# любое изменение в этой структура должно блокировать сохранение. если изменили то опять проверка.
		
		# Если артист уже в базе, то он предлагается как невыбранный checked = False, проверка его альбомов происходит всегда
		# проверочная иерархия всегда если есть альбомы на сохранение
		
		# Если артист не в БД и не выделен, то отменить выборку  его альбомом, даже если они выбраны
		self.__logger.debug('in function artist_album_struct_client_server_sinc: [%s] '%(str('')))

		print('in sinc--->',list_node_key,new_process_type)
		for artist_item_serv in artist_album_struct_serv:
			artist_index = artist_album_struct_serv.index(artist_item_serv)
			artist_item_client = artist_album_struct_client[artist_index]
			for a in artist_item_serv:
				if a not in artist_item_client:
					artist_item_client[a] = artist_item_serv[a]
					
			if not artist_item_serv['is_in_db']:
				artist_item_client['expanded'] = True
				if artist_item_client['checked']:
					artist_item_client['process_type'] = new_process_type
					artist_item_client['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],new_process_type)
				
			
			albumL_serv = artist_item_serv[list_node_key]	
			
			albumL_client = artist_item_client[list_node_key]	
			
			
			
			no_albumes = True
			for album_item_serv in albumL_serv:
				album_index = albumL_serv.index(album_item_serv)
				album_item_client = albumL_client[album_index]
				
				
									
				for b in album_item_serv:
					if b not in album_item_client:
						album_item_client[b] = album_item_serv[b]
				
				# пропуск позиций уже наход. в бд или невыбранных
				if album_item_client['is_in_db']:
					album_item_client['checked'] = False
					album_item_client['visible'] = False
					continue	
							
				if not album_item_client['checked']:
					album_item_client['visible'] = False
					continue
				# Если артист не в базе 	
				if not artist_item_client['is_in_db'] and not artist_item_client['checked']:
					album_item_client['checked'] = False
					continue
				
				no_albumes = False
				album_item_client['process_type'] = new_process_type
				album_item_client['visible'] = True
				album_item_client['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],new_process_type)
				if not artist_item_client['expanded']:
					artist_item_client['expanded'] = True
					#album_item_client['visible'] = True	
			
			if no_albumes:
				artist_item_client['expanded'] = False
			
					
		return					
	
	def artist_album_get_categ(self,commandD):
		self.__logger.info('in action artist_album_get_categ: [%s] '%(str(commandD)[:100]))
		categ_id = ''
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		if 'group_list' in commandD:
			categ_id = commandD['group_list']
			
		if 'categ_id' in commandD:
			categ_id = int(commandD['categ_id'])	
		
		print('get albums and artist for categ:',categ_id)
		
		artist_album_categ_data = getArtistAlbum_indexL_viaCategId(dbPath,categ_id,['artist','album'],'general_categ')
		
		self.__modelDic['artist_album_categ_data'] = artist_album_categ_data
		
		artistD = self.map_artist_album_categ_assignment_to_view_json(artist_album_categ_data,'init')
		
		
		vldt_art_key = zlib.crc32(b'art_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		vldt_albNSA_key = zlib.crc32(b'alb_NSA_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		self.__modelDic['artist_album_maintain_proc_buf'] = {
															'artist_view':{'dataD':{'initial':artistD['artistD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
															'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
															'checked_pageL':[1]
															},
															'album_NSA_view':{'dataD':{'initial':artistD['not_single_artist_albumD_list'],'initial_changed':[],'tb_save':[],'saved':[]},
															'proc_state':'initial','validity_key':vldt_albNSA_key,'message_log':'','cur_page':1,
															'checked_pageL':[1]
															},
															'active_view':'artist',
															'proc_type':'data_categ',
															'mode':'update'
															}
		
		
					
		
		return
	
	def artist_album_maintain_check(self,commandD):	
		# фаза проверки должно прийти тип представления, тип состояния процесса, номер странцицы.
		# обно
		# Внимание!!! Эта функция не полностью универсальная, т.к. в зависимости от процесса обработки (начальное сохранение, или категоризация) вызываемая функция
		# синхронизации artist_album_struct_client_server_sinc или ее аналог работает по разному, чтобы вызвать правильную функцию ее надо вызывать в контексте процесса
		# этот контекст передается пока через значение параметра commandD['artists_maintain'] 
		
		
		self.__logger.info('in action artist_album_maintain_check: [%s] '%(str(commandD)[:100]))
		artistDataDL = []
		buf_key = 'nokey'
		if 'artistDataD' in commandD:
			buf_key = 'artist_view'
			sublist_key = 'albumL'
			client_data_key = 'artistDataD'
			vldt_key = zlib.crc32(b'art_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		elif 'album_NSA_DataD'	in commandD:
			buf_key = 'album_NSA_view'
			sublist_key = 'artistL' 
			client_data_key = 'album_NSA_DataD'
			vldt_key = zlib.crc32(b'alb_NSA_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		
		if ('artistDataD' in commandD or 'album_NSA_DataD' in commandD) and 'restore_init_edited' in commandD['action_mode']:
			print('in restore:',commandD['artists_maintain'])
			
			
			client_struct = self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial_changed']
			
						
			struct_initial = self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial']
			
			self.client_struct_restore(client_struct,struct_initial,sublist_key,'initial')
			
			
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial'] =client_struct
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'initial'			
			
		if ('artistDataD' in commandD or 'album_NSA_DataD' in commandD) and 'tb_save' in commandD['action_mode']:
			print('in check',commandD['artists_maintain'])
			
			
			copy_client = []
			for elem in commandD[client_data_key]:
				elem_copy = elem.copy()
				
				for key in elem:
					if key == sublist_key:
						elem_copy[sublist_key] = [item_elem.copy() for item_elem in elem[sublist_key]]
						
				#print 'copy_client:',copy_client		
				copy_client.append(elem_copy)			
						
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial_changed']=copy_client			
			
			
			# Проверить логическую целостность альбомов и артистов и вернуть предложение на сохранение
			# к данным структур надо добавить сессионный ключ уникальности буфера, который вернувшись назад должен быть сверен с серверным если ок. то можно сохранять
			# на клиенте любые изменения сформированной ниже структуры отменяют сохранение пока сверка не пройдет.
			
			# Ниже идет выбор соответствующей процессу функции синхронизации
			if commandD['artists_maintain'] == 'artist_album_maintain_check':
				self.artist_album_struct_client_server_sinc(self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial'],commandD[client_data_key],sublist_key,'tb_save')
			elif commandD['artists_maintain'] == 'artist_album_maintain_categ_check':
				self.__modelDic['artist_album_maintain_proc_buf']['proc_type'] = 'data_categ'
				categ_key =  commandD['group_list']
				if 'mode' not in self.__modelDic['artist_album_maintain_proc_buf']:
					mode =  'add'
					self.__modelDic['artist_album_maintain_proc_buf']['mode'] = mode
				else:
					mode = self.__modelDic['artist_album_maintain_proc_buf']['mode']
					
				
				
				self.artist_album_struct_client_server_sinc_categ(categ_key,self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial'],
				commandD[client_data_key],sublist_key,'tb_save',mode)
			
			# формируем буфер процесса массовой обработки, сохранив в нем пришедшую с клиента реплику по ключу artist_dataD_list_client_copy_init_edited
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save']=commandD[client_data_key]
																
			#self.__modelDic['artist_album_maintain_proc_buf']['artist_dataD_list_client_copy_init_edited']=[a for a in commandD[sublist_key]]
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'tb_save'
			
			self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['validity_key'] = vldt_key
			#print 'after'
			#for item in self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial_changed']:
			#	print item
			
			
				
			return 1
					
				
		return None		
		
	def album_NSA_view_save(self,album_view_dataD,albumD,db):	
		messageL = []
		self.__logger.info('in function album_NSA_view_save')
		success_res = True
		for album_item_serv in album_view_dataD:
			
			if album_item_serv['process_type'] != 'tb_save':
				continue
			
			# Связи сохраняются в любом случае по любым артистам. главное чтобы существовал альбом
			print(list(album_item_serv.keys()))
				
			album_db_id = None
			album_key = int(album_item_serv['key'])
			
			
			
			
			artistL_serv = album_item_serv['artistL']	
			album_saved = False
			create_album = True
			no_albumes = True
			
			for artist_item_serv in artistL_serv:
				#print 'in artist item ',artist_item_serv['key'],artist_item_serv['artist']
				
				artist_key = int(artist_item_serv['key'])
				
				
				# Логика сохранения следующая, тк. альбом логически не может быть без артиста артистов, то вначале надо создать артиста
				# Затем один раз создается альбом если его надо создавать
					
				artistName = artist_item_serv['artist']
				retD = {}
				retD['result'] = ''
				
				#print 'artist is_in_db:%s checked:%s'%(str(artist_item_serv['is_in_db']),str(artist_item_serv['checked']))
				if not artist_item_serv['is_in_db'] and not artist_item_serv['checked']:
					continue
				if not artist_item_serv['is_in_db']:	
					print('in save artist part',artist_item_serv['artist'])
					retD = saveArtistD_intoDB(None,artistName.lower().strip(),'',None,None,[],None,db)
					print('in save artist part OK')
					# Если ошибка сохранения то сменить цвет на ошибочный как для списка
				
					if retD['result'] != None and retD['result']!= -1:
						artist_db_id = retD['id_artist']
						print("%s : Saved Ok"%(str(artist_db_id)))
						
						self.__logger.info("In Artist item mass saving - %s : Saved Ok"%(str(artist_db_id)))
						
						artist_item_serv['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],'saved')
						artist_item_serv['process_type'] = 'saved'
						artist_item_serv['is_in_db'] = True		
						artist_item_serv['checked'] = False
						
					else:
						artist_item_serv['colorcl'] = artist_item_serv['colorcl'].replace(artist_item_serv['process_type'],'error')
						artist_item_serv['process_type'] = 'error'
						artist_item_serv['is_in_db'] = False
						continue
						#create_album = False
					
					
				if not album_saved and not album_item_serv['is_in_db'] and create_album:
						
					print('Creating album:',albumD[album_key]['album'],album_saved)
					# albumD тут из 'album_songD'
					res = saveAlbum_intoDB_via_artistD(None,albumD[album_key],artist_key,album_key,db,'without_artist_relation','album_NSA_view')
					print('Ok',res,album_key)
					# Если ошибка сохранения то сменить цвет на ошибочный как для списка
					if res == -1:
						artist_item_serv['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],'error')
						artist_item_serv['process_type'] = 'error'
						
						messageL.append('Error: album [%s] creation fail'%(str(album_item_serv['album'])))
						
						create_album = False
						success_res = False
						
					else:
						album_saved = True
						db.commit()
						album_item_serv['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],'save')
						album_item_serv['process_type'] = 'save'
						album_item_serv['checked'] = False
						self.__logger.info("In Album mass saving - %s : Saved Ok"%(str(album_item_serv['album'])))

					print(4)
				
				if album_saved:
					# тут сохранить артиста
					#print 'saving artist:',album_item_serv['key'],album_item_serv['artist']
					print('Creating album relation:',albumD[album_key]['album'])
					res = saveAlbum_intoDB_via_artistD(None,albumD[album_key],artist_key,album_key,db,'only_artist_relation_creation','album_NSA_view')
					print('OK',res)
					# Если ошибка сохранения то сменить цвет на ошибочный как для списка
					if res == -1:
						artist_item_serv['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],'error')
						artist_item_serv['process_type'] = 'error'
						messageL.append('Error: album [%s] relation creation to artist[%s]'%(str(album_item_serv['album']),str(artist_item_serv['artist'])))
						success_res = False
					else:
						self.__logger.info("In Album[%s] Artist[%s] relation  mass saving : Saved Ok"%(str(album_item_serv['album']),str(artist_item_serv['artist'])))
						album_item_serv['is_in_db'] = True		
					
		return {'success_res':success_res,'messageL':messageL}				
						
	def artist_view_save(self,artist_view_dataD,artistD,db):	
		self.__logger.info('in function artist_view_save')
		for artist_item_serv in artist_view_dataD:
				#print artist_item_serv.keys()
			#print 	artist_item_serv['artist']
			artist_db_id = None
			if artist_item_serv['process_type'] == 'tb_save':
				# тут сохранить артиста
				#print 'saving artist:',artist_item_serv['key'],artist_item_serv['artist']
				artistName = artist_item_serv['artist']
				retD = saveArtistD_intoDB(None,artistName.lower().strip(),'',None,None,[],None,db)
				
				# Если ошибка сохранения то сменить цвет на ошибочный как для списка
				
				if retD['result'] != None and retD['result']!= -1:
					artist_db_id = retD['id_artist']
					#print "%s : Saved Ok"%(str(artist_db_id))
					artist_item_serv['process_type'] = 'saved'
					artist_item_serv['checked'] = False
					artist_item_serv['is_in_db'] = True
					self.__logger.info("In Artist mass saving - %s : Saved Ok"%(str(artist_db_id)))
				else:
					#print "%s : NOT SAVED!!!"%(str(artist_db_id))
					self.__logger.critical("In Artist mass saving - %s : NOT SAVED!!!"%(str(artist_db_id)))
				
			#print 2
			albumL_serv = artist_item_serv['albumL']	
			
			no_albumes = True
			for album_item_serv in albumL_serv:
				
				# пропуск позиций уже наход. в бд или невыбранных
				if album_item_serv['is_in_db']:
					continue	
							
				if not album_item_serv['checked']:
					continue
				# Если артист не в базе м чекнут	
				if album_item_serv['process_type'] == 'tb_save':
					# тут сохранить аЛьбом
					#print 'saving album:',album_item_serv['key'],album_item_serv['album']
					#print 'saving reference:',artist_item_serv['key'],album_item_serv['key']
					artist_key = int(album_item_serv['artist_key'])
					album_key = int(album_item_serv['key'])
					
					albumD = artistD[artist_key]['albumD'][album_key]
					#print 'albumD:',albumD
					res = saveAlbum_intoDB_via_artistD(None,albumD,artist_key,album_key,db,'artist_view')
					if res == -1:
						album_item_serv['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],'error')
						album_item_serv['process_type'] = 'error'
					else:
						album_item_serv['colorcl'] = album_item_serv['colorcl'].replace(album_item_serv['process_type'],'saved')
						album_item_serv['process_type'] = 'saved'	
						album_item_serv['checked'] = False
						album_item_serv['is_in_db'] = True	

		print('Ok')
						
	def artist_album_maintain_mass(self,commandD):	
		# Функция обертка для сохранения данных в БД (artist_view_save)
		self.__logger.info('in action artist_album_maintain_mass: [%s] '%(str(commandD)))
		artistDataDL = []
		
		if 'artistDataD' in commandD:
			buf_key = 'artist_view'
		elif 'album_NSA_DataD'	in commandD:
			buf_key = 'album_NSA_view'
		
					
		if ('artistDataD' in commandD or 'album_NSA_DataD' in commandD) and 'save' in commandD['action_mode']:
			# Тут нужна серьезная проверка, что посланные шаг назад данные не изменились
			# если проверка прошла то сохранять
			# данные от клиента передавать не надо
			
			
			artist_album_struct_serv = self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save']
			artistD = self.__modelDic['ReportBufD']['artistD']
			#print "Will be saved!!!!",len(artist_album_struct_serv)
			
			db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])	
			if 'artistDataD' in commandD:
				self.artist_view_save(artist_album_struct_serv,artistD,db)
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'saved'	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['saved']   = artist_album_struct_serv	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial'] = artist_album_struct_serv	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save'] = []	
				
			elif 'album_NSA_DataD'	in commandD:
				self.album_NSA_view_save(artist_album_struct_serv,self.__modelDic['ReportBufD']['album_songD'],db)
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'saved'	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['saved']=artist_album_struct_serv		
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial']=artist_album_struct_serv		
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save'] =[]
			
			db.commit()
			db.close()	
			print("saved!!!")
			# тут надо править
			#self.__modelDic['artist_album_maintain_proc_buf']['artist_dataD_list_sync']:artist_album_struct_serv,'action_type':'saved'}		
			return 1
				
					
				
		return None			
		
	def artist_album_categ_maintain_mass(self,commandD):	
		# Функция обертка для сохранения данных в БД (artist_view_save)
		self.__logger.info('in action artist_album_categ_maintain_mass: [%s] '%(str(commandD)))
		artistDataDL = []
		
		if 'artistDataD' in commandD:
			buf_key = 'artist_view'
		elif 'album_NSA_DataD'	in commandD:
			buf_key = 'album_NSA_view'
		
		categ_key = 'UNDEFINED'
		if 'group_list' in commandD:	
			categ_key =  commandD['group_list']	
		
		if 'categ_id' in commandD:	
			categ_id =  int(commandD['categ_id'])
		else:
			categ_id = None
					
		if ('artistDataD' in commandD or 'album_NSA_DataD' in commandD) and 'save' in commandD['action_mode']:
			# Тут нужна серьезная проверка, что посланные шаг назад данные не изменились
			# если проверка прошла то сохранять
			# данные от клиента передавать не надо
			
			artist_album_struct_serv = self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save']
			
			artistD = {} # взять метаданные тут из буферов
			
			artist_dbDD={}	
			album_dbDD={}	
			
			
			categD = {categ_id:categ_key}
			#categ_id = None
			#plGroupD = self.__model_instance.MediaLibPlayProcessDic_viaKey('group2PlayListD','local')['groupD']
			
			#for a in plGroupD:
			#	if a == categ_key:
			#		categ_id = plGroupD[a]['group_id']
			#		categD[categ_id]=categ_key
					
			print(categ_id,categD)
			
			artistL_delete = []
			artistL_append= []
			albumL_delete = []
			albumL_append= []
			dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
			db = sqlite3.connect(dbPath)	
			if 'artistDataD' in commandD:
				
				for artist_item in self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save']:
					if artist_item['process_type'] == 'tb_save':
						artistL_append.append(int(artist_item['key']))
					elif artist_item['process_type'] == 'tb_delete':	
						artistL_delete.append(int(artist_item['key']))
					
					for album_item in artist_item['albumL']:
						if album_item['process_type'] == 'tb_save':
							albumL_append.append(int(album_item['key']))
						elif album_item['process_type'] =='tb_delete':	
							albumL_delete.append(int(album_item['key']))	
							
							
				print(buf_key)
				
				if artistL_append != []:
					#print 'art append l:',artistL_append
					artist_dbDD = getArtistD_fromDB(dbPath,None,artistL_append,'wo_reflist')
					#print len(artist_dbDD)
					
				if 	artistL_delete != []:
					artist_dbDD_del = getArtistD_fromDB(dbPath,None,artistL_delete,'wo_reflist')
					artistL_delete = [artist_dbDD_del[a]['id_artist'] for a in artist_dbDD_del]
					resL = artist_album_categorisation_delete(dbPath,artistL_delete,categ_id,'artist')
					print('art deleted l:',artistL_delete,resL)
					#print len(artistL_delete)
				
				self.__modelDic['artist_dbDD']=artist_dbDD
				
				if albumL_append != []:
					album_dbDD = getAlbumD_fromDB(dbPath,None,None,albumL_append,'wo_reflist')['albumD']
					print('album presel:',len(album_dbDD))
					#print album_dbDD
					
				if 	albumL_delete != []:
					album_dbDD_del = getAlbumD_fromDB(dbPath,None,None,albumL_delete,'wo_reflist')['albumD']
					albumL_delete = [album_dbDD_del[a]['id_album'] for a in album_dbDD_del]
					resL = artist_album_categorisation_delete(dbPath,albumL_delete,categ_id,'album')	
					print('alb deleted l:',albumL_delete,resL)
				
				if artist_dbDD != {}:	
					print('Cat artist add:',len(list(artist_dbDD.keys())))
					print() 
					r = artist_album_categorisation_and_save(dbPath,artist_dbDD,categ_id,categD,'general_categ','artist')
					print('artist added:',r)
				if album_dbDD != {}:	
					print('Cat album add:',len(list(album_dbDD.keys())))
					r = artist_album_categorisation_and_save(dbPath,album_dbDD,categ_id,categD,'general_categ','album')	
					print('album added:',r)
					
				#self.artist_view_save(artist_album_struct_serv,artistD,db)
				
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'saved'	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['saved']   = artist_album_struct_serv	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial'] = artist_album_struct_serv	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save'] = []	
				
			elif 'album_NSA_DataD'	in commandD:
				
				for album_item in self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save']:
					if album_item['process_type'] == 'tb_save':
						albumL_append.append(int(album_item['key']))
					elif album_item['process_type'] =='tb_delete':	
						albumL_delete.append(int(album_item['key']))
					
					for artist_item in album_item['artistL']:
						if artist_item['process_type'] == 'tb_save':
							artistL_append.append(int(artist_item['key']))
						elif artist_item['process_type'] == 'tb_delete':	
							artistL_delete.append(int(artist_item['key']))
				
				print(buf_key)
				
				if artistL_append != []:	
					artist_dbDD = getArtistD_fromDB(dbPath,None,artistL_append)
				if albumL_append != []:
					album_dbDD = getAlbumD_fromDB(dbPath,None,None,albumL_append)['albumD']
				
				if 	artistL_delete != []:
					artist_dbDD_del = getArtistD_fromDB(dbPath,None,artistL_delete,'wo_reflist')
					artistL_delete = [artist_dbDD_del[a]['id_artist'] for a in artist_dbDD_del]
					resL = artist_album_categorisation_delete(dbPath,artistL_delete,categ_id,'artist')
					print('art deleted l:',artistL_delete,resL)
					
				if artist_dbDD != {}:	
					print('Cat artist:',len(list(artist_dbDD.keys())))
					r = artist_album_categorisation_and_save(dbPath,artist_dbDD,categ_id,categD,'general_categ','artist')
					
				if 	albumL_delete != []:
					album_dbDD_del = getAlbumD_fromDB(dbPath,None,None,albumL_delete,'wo_reflist')['albumD']
					albumL_delete = [album_dbDD_del[a]['id_album'] for a in album_dbDD_del]
					resL = artist_album_categorisation_delete(dbPath,albumL_delete,categ_id,'album')	
					print('alb deleted l:',albumL_delete,resL)
					
				if album_dbDD != {}:	
					print('Cat album:',len(list(album_dbDD.keys())))
					
					r = artist_album_categorisation_and_save(dbPath,album_dbDD,categ_id,categD,'general_categ','album')	
				#self.album_NSA_view_save(artist_album_struct_serv,self.__modelDic['ReportBufD']['album_songD'],db)
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state'] = 'saved'	
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['saved']=artist_album_struct_serv		
				self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['initial']=artist_album_struct_serv		
				#ohgdfsa<self.__modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD']['tb_save'] =[]
			
			#db.commit()
			db.close()	
			print("saved!!!")
			# тут надо править
			#self.__modelDic['artist_album_maintain_proc_buf']['artist_dataD_list_sync']:artist_album_struct_serv,'action_type':'saved'}		
			return 1
				
		return None				
		
	def get_tracks_from_cur_plist(self,commandD):	
		
		self.__logger.info('get_tracks_from_cur_plist: [%s] '%(str(commandD)))
		#metaD[a[1]] = {'id_track':a[0],'title':a[2],'artist':a[3],'album':a[4], 'path':a[5], 'cue_num':a[6],'cue_fname':a[7],'format':format,'bitrate':a[8]}
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		#<-----OLD-WINAMP-CODE start
		#l_data = zlib.decompress(self.__player_handler.get_cur_pl_as_list().data)
		#PlayListL = 	pickle.loads(l_data)
		#OLD-WINAMP-CODE end---->
		remote_host = self.__modelDic['REMOTE_ADDR']
		
		
		#self.__PlayListL = PlayControl_CurStatusD['PlayListL']
		#try:
		#	PlayList_asCRC32_L = [zlib.crc32(a.encode(BASE_ENCODING)) for a in PlayListL]	
		#except Exception as e:
		#	self.__logger.critical('Error: in update_model_state %s'%(str(e)))		
		#OLD-WINAMP-CODE end---->
		
		DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')
		media_lib_allcrc32L = DB_metaIndxD.keys()
		
		
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		mpd_socket = mpd_instance['socket']
		mpd_host = mpd_instance['host']
		mpd_host_ip = socket.gethostbyname(host)
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']
				
		client = MPDClient()
		# Not necessary, but should not cause any trouble either
		client.disconnect()
		self.__logger.debug('get_tracks_from_cur_plist 3978: OK ')
		PlayList_asCRC32_L = asyncio.run(get_mpd_playlist_as_crc32L(client,mpd_host_ip, mpd_socket, mpdMusicPathPrefix, media_lib_allcrc32L))	
		self.__logger.debug('get_tracks_from_cur_plist 3980: OK ')
		
		
		
		
		print('r=*********************************',PlayList_asCRC32_L)
		
		db_idL = getDbIDL_via_CRC32L(dbPath,PlayList_asCRC32_L,None)
		db_idL = [a[0]for a in db_idL]
				
		metaD_of_cur_pL = getCurrentMetaData_fromDB_via_DbIdL(db_idL,None)
		
		paramD = {'action':'get_tracks_from_cur_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
		self.__model_instance.setSearchBufD('get_tracks_from_cur_plist',metaD_of_cur_pL,None,None,paramD)
		#print metaD_of_cur_pL[metaD_of_cur_pL.keys()[0]].keys()
		
		self.__logger.debug('in get_tracks_from_cur_plist OK')
		return 1
		
	def get_images_4_cur_album_fromPL(self,commandD):	
		
		self.__logger.debug('3651 get_images_4_cur_album_fromPL: [%s] '%(str(commandD)))
		#metaD[a[1]] = {'id_track':a[0],'title':a[2],'artist':a[3],'album':a[4], 'path':a[5], 'cue_num':a[6],'cue_fname':a[7],'format':format,'bitrate':a[8]}
		file_name = ''
		music_folder = ''
		data_str = ''
		cfgD = readConfigData(mymedialib_cfg)
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		audioFilesPathRoot = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audioFilesPathRoot']
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']
		
		remote_host = self.__modelDic['REMOTE_ADDR']
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		
		mpd_socket = mpd_instance['socket']
		host = mpd_instance['host']
		mpd_client = MPDClient()
		mpd_client.disconnect()
		host = mpd_instance['host']	
		host_ip = socket.gethostbyname(host)
		track_list_num = 0
		
			
		mpd_status = asyncio.run(get_mpd_status(mpd_client,host_ip, mpd_socket))
	
		if 'song' in mpd_status:
			track_list_num = mpd_status['song']
		
		#print(track_list_num)
		
		track_info = asyncio.run(get_mpd_playlistinfo(mpd_client,host_ip, mpd_socket,track_list_num))
		
			
		if track_info == []:
			self.__logger.critical('Error in get_images_4_cur_album_fromPL: MPD list is empty')
			self.__logger.debug('in get_images_4_cur_album_fromPL - Finished with error')
			return 0
			
		if "http://" in track_info[0]['file'] or "https://" in track_info[0]['file']:
			self.__logger.critical('Error in get_images_4_cur_album_fromPL: Radio detected[%s]'%(str(track_info[0]['file'])))	
			self.__logger.debug('in get_images_4_cur_album_fromPL - Finished with error')
			return 0
		
		
		file_name = os.path.relpath(track_info[0]['file'],mpdMusicPathPrefix)
		file_name = os.path.normpath(os.path.join(audioFilesPathRoot,file_name))
		
		print("File Name = ---->",file_name)
		
			
		pos = file_name.rfind("/")
		music_folder = file_name[:pos]
		resDBS = []
		self.__logger.debug('in get_images_4_cur_album_fromPL: path  %s'%(str([music_folder])))	
		
			
		print("test 0")		
		imageD = {}
		imageL = collect_images_for_album(None,music_folder)
		for a in imageL:
			print(a)
			imageD[a['image_crc32']]=a['f_path']
					
		imageLD = {'album_crc32':'99999999999','imageL':imageL,'imageD':imageD}	
		
		self.__logger.debug('3665 get_images_4_cur_album_fromPL: len[%s] '%(str(len(imageL))))
		# Найти срц32 текущего альбома album_crc32 = metaD_of_cur_pL[1989996026]['album_crc32']
		
		paramD = {'action':'get_album_images_from_cur_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
		self.__model_instance.setSearchBufD('get_images_from_cur_album',imageLD,None,None,paramD)
		#print metaD_of_cur_pL[metaD_of_cur_pL.keys()[0]].keys()
		
		self.__logger.debug('in get_images_4_cur_album_fromPL OK')
		return 1	
	
	def get_images_4_selected_album(self,commandD):	
	
		self.__logger.debug('3711 get_images_4_selected_album: [%s] '%(str(commandD)))
		
		album_crc32 = int(commandD['album_crc32'])
		print('albumcrc32:',album_crc32)
		
		imageD = {}
		imageL = collect_images_for_album(album_crc32,None)
		for a in imageL:
			imageD[a['image_crc32']]=a['f_path']
					
		imageLD = {'album_crc32':album_crc32,'imageL':imageL,'imageD':imageD}	
		
		self.__logger.debug('3723 get_images_4_cur_album_fromPL: len[%s] '%(str(len(imageL))))
		# Найти срц32 текущего альбома album_crc32 = metaD_of_cur_pL[1989996026]['album_crc32']
		
		paramD = {'action':'get_album_images_from_cur_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
		self.__model_instance.setSearchBufD('get_images_from_cur_album',imageLD,None,None,paramD)
		#print metaD_of_cur_pL[metaD_of_cur_pL.keys()[0]].keys()
		
		self.__logger.debug('in get_images_4_selected_album OK found[%s]'%str(len(imageL)))
		return 1
		
	def get_tracks_4_selected_folder(self,commandD):	
		# Сбор метаданных для закладки Tracks и упаковка в JSON структуру
		self.__logger.debug('3740 get_tracks_4_selected_folder: [%s] '%(str(commandD)))
		cfgD = readConfigData(mymedialib_cfg)
		audioFilesPathRoot = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audioFilesPathRoot']
		music_folder =''
		res = {}
		resDBS = {}
		creation_time = None
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		DB_PathL = []
		with_db_folder_check = True
		
		album_crc32 = int(commandD['album_crc32'])
		print('albumcrc32:',album_crc32)
		
		autoComplBufD = self.__model_instance.getAutoComplSearch_BufD()
		#sel_dir = os.path.normpath(audioFilesPathRoot)+"\\"+autoComplBufD[album_crc32]
		if os.path.normpath(audioFilesPathRoot) not in autoComplBufD[album_crc32]:
			sel_dir = os.path.normpath(audioFilesPathRoot)+"\\"+autoComplBufD[album_crc32]
		else:
			sel_dir = autoComplBufD[album_crc32]
		
		
		print('selected dir: ',[sel_dir])
		
		update_mode = False	
		update_mode_value = ''
		if 'update_mode' in commandD:
			update_mode_value = commandD['update_mode']
			
			
			
		print('update_mode:',update_mode_value)
		if update_mode_value == 'reload' or update_mode_value == 'reloadsimpl':	
			self.__logger.debug('3836 in get_tracks_4_selected_folder: before identify_music_folder %s '%(str([sel_dir])))
			res = identify_music_folder([sel_dir])
			music_folder = res['music_folderL']
			print('existed music_folderL:',res['music_folderL'])

		# Сравнение по предварительно сохраненному списку дирректорий
		if update_mode_value == 'notindb':
			MLFolderTreeAll_BufD = self.__model_instance.getMLFolderTreeAll_BufD()
			resBuf_ml_folder_tree_buf_path = cfgD['ml_folder_tree_buf_path']
			creation_time = datetime.datetime.fromtimestamp(os.stat(resBuf_ml_folder_tree_buf_path).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
			
			if MLFolderTreeAll_BufD == {}:
				f = open(resBuf_ml_folder_tree_buf_path,'rb')
				Obj = pickle.load(f)
				f.close()
				self.__model_instance.setMLFolderTreeAll_BufD(Obj)
				MLFolderTreeAll_BufD = Obj
			
			if MLFolderTreeAll_BufD != {}:
				print("MLFolderTreeAll_BufD: OK")
				if with_db_folder_check:
					DB_PathL = getFolderPathL_fromDB_viaTermL(dbPath,None,[sel_dir],audioFilesPathRoot)
				
				res = find_new_music_folder([sel_dir], MLFolderTreeAll_BufD['folder_list'],DB_PathL)
				try:
					self.__logger.debug('3952 in get_tracks_4_selected_folder: after find_new_music_folder %s '%(str([res])))	
				except Exception as e:
					self.__logger.critical('4120 Log Error in get_tracks_4_selected_folder: after find_new_music_folder %s '%(str(e)))	
			
				
		if 'music_folderL' in res:
			if res['music_folderL'] != []:
				music_folder = res['music_folderL']
				print('music_folderL:',res['music_folderL'])
			
				#for dir_name in res['music_folderL']:
				#	print 'Loading tracks from:',dir_name.
				
				if update_mode_value == 'reload' or update_mode_value == 'reloadsimpl':	
					resDBS = mediaLib_intoDb_Load_withUpdateCheck(dbPath,res['music_folderL'],audioFilesPathRoot,None,update_mode_value)
					new_allmFD = resDBS['new_allmFD']
				else:
					resDBS = mediaLib_intoDb_Load_withUpdateCheck(dbPath,res['music_folderL'],audioFilesPathRoot,creation_time,'ml_buf_time_with_db_check')
					new_allmFD = resDBS['new_allmFD']
				
				# сохранить выбранную узловую папку, чтобы затем делать апдейт MPD базы от нее
				resDBS['init_selected_node_folder'] = sel_dir
				print()
				#for key in resDBS:
				#	print resDBS[key]['metaD']['pos_num'],resDBS[key]['metaD']['title'].encode(BASE_ENCODING)
				if 'Error' in resDBS or new_allmFD == {}:
					print('print Error 3846')
					self.__logger.critical('Error: 3846 in get_tracks_4_selected_folder after mediaLib_intoDb_Load_withUpdateCheck')		
					self.__modelDic['tracks_preload_proc_buf_db'] = {
																			'tracks_view':{'dataD':{'initial':{'album':'error','artist':'error'}}}}
					return 1
				print('print OK')
				
				
				paramD = {'action':'get_new_album_in folder_node'}
				if 'srch_rep_mode' in commandD:
					paramD['mode']=commandD['srch_rep_mode']
		
				#self.__model_instance.setSearchBufD('tracks_preloaded_from_folder_buf',resDBS,None,None,paramD)
				
				self.__model_instance.setTracksPreloadRes_BufD(resDBS)
				
				print('before map')	
				self.__logger.debug('before map_meta_album_tracks_struct_to_view_json')	
				album_artistD = resDBS['album_artistD']
				albumDL = self.map_meta_album_tracks_struct_to_view_json(new_allmFD,album_artistD)	
				
						# ВНИМАНИЕ! proc_state - является ключем для bufferD													
				vldt_art_key = zlib.crc32(b'art_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
				vldt_albNSA_key = zlib.crc32(b'alb_NSA_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
				print('CRC32')	
				self.__modelDic['tracks_preload_proc_buf_db'] = {
																			'tracks_view':{'dataD':{'initial':albumDL,'initial_changed':[],'tb_save':[],'saved':[]},
																			'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
																			'checked_pageL':[1]
																			},
																			'album_NSA_view':{'dataD':{'initial':[],'initial_changed':[],'tb_save':[],'saved':[]},
																			'proc_state':'initial',
																			'message_log':'','cur_page':1,
																			'checked_pageL':[1]
																			},
																			'active_view':'artist',
																			'proc_type':'data_from_db'
			
																}
																
			else:
				vldt_art_key = zlib.crc32(b'art_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
				vldt_albNSA_key = zlib.crc32(b'alb_NSA_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
				self.__modelDic['tracks_preload_proc_buf_db'] = {
																			'tracks_view':{'dataD':{'initial':[],'initial_changed':[],'tb_save':[],'saved':[]},
																			'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
																			'checked_pageL':[1]
																			},
																			'album_NSA_view':{'dataD':{'initial':[],'initial_changed':[],'tb_save':[],'saved':[]},
																			'proc_state':'initial',
																			'message_log':'','cur_page':1,
																			'checked_pageL':[1]
																			},
																			'active_view':'artist',
																			'proc_type':'data_from_db'
			
																}
				
		print('modeldic ok')	
		
		# Найти срц32 текущего альбома album_crc32 = metaD_of_cur_pL[1989996026]['album_crc32']
		
		paramD = {'action':'get_album_tracks_from_cur_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
		
		self.__logger.debug('in get_tracks_4_selected_folder OK')
		return 1
		
	def get_tracks_4_cur_album_fromPL(self,commandD):
		self.__logger.debug('3878 get_tracks_4_cur_album_fromPL: [%s] - Start '%(str(commandD)))
		file_name = ''
		music_folder = ''
		data_str = ''
		cfgD = readConfigData(mymedialib_cfg)
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		audioFilesPathRoot = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audioFilesPathRoot']
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']
		
		resBuf_ml_folder_tree_buf_path = cfgD['ml_folder_tree_buf_path']
		creation_time = datetime.datetime.fromtimestamp(os.stat(resBuf_ml_folder_tree_buf_path).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
		remote_host = self.__modelDic['REMOTE_ADDR']
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		
		socket = mpd_instance['socket']
		host = mpd_instance['host']
		mpd_client = MPDClient()
		mpd_client.disconnect()
		host = mpd_instance['host']	
		mpd_status = asyncio.run(get_mpd_status(mpd_client,host, socket))
		print("mpd_status=",mpd_status)
		track_list_num = 0
		if 'song' in mpd_status:
			track_list_num = mpd_status['song']
		
		#print(track_list_num)
		track_info = asyncio.run(get_mpd_playlistinfo(mpd_client,host, socket,track_list_num))
			
		if track_info == []:
			self.__logger.critical('Error in get_tracks_4_cur_album_fromPL: MPD list is empty')
			self.__logger.debug('in get_tracks_4_cur_album_fromPL - Finished with error')
			return 0
			
		if "http://" in track_info[0]['file'] or "https://" in track_info[0]['file']:
			self.__logger.critical('Error in get_tracks_4_cur_album_fromPL: Radio detected[%s]'%(str(track_info[0]['file'])))	
			self.__logger.debug('in get_tracks_4_cur_album_fromPL - Finished with error')
			return 0
		
		
		file_name = os.path.relpath(track_info[0]['file'],mpdMusicPathPrefix)
		file_name = os.path.normpath(os.path.join(audioFilesPathRoot,file_name))
		
		print(file_name)
		
			
		pos = file_name.rfind("\\")
		music_folder = file_name[:pos]
		resDBS = []
		self.__logger.debug('in get_tracks_4_cur_album_fromPL: path  %s'%(str([music_folder])))	
		
			
		print("test 0")		
		path_check = False
		try:
			path_check = os.path.exists(music_folder)
		except Exceptio as e:
			self.__logger.critical('Error in get_tracks_4_cur_album_fromPL: path not exist 1 %s'%(str[music_folder]))	
			return 0
		print("test 0 -1",path_check)			
		if not path_check:
			self.__logger.critical('Error in get_tracks_4_cur_album_fromPL: path not exist 2 %s'%(str[music_folder]))	
			return 0
			
		print("test 1")	
		update_mode = False	
		update_mode_value = ''
		if 'text_line' in commandD:
			update_mode_value = commandD['text_line']

		
		
		print("test update mode - 2", update_mode_value)	
		if update_mode_value == 'reload' or update_mode_value == 'reloadsimpl':	
			resDBS = mediaLib_intoDb_Load_withUpdateCheck(dbPath,[music_folder],audioFilesPathRoot,None,update_mode_value)
			new_allmFD = resDBS['new_allmFD']
		elif update_mode_value == 'notindb':
			print("test 3")	
			resDBS = mediaLib_intoDb_Load_withUpdateCheck(dbPath,[music_folder],audioFilesPathRoot,creation_time,'ml_buf_time_with_db_check')
			new_allmFD = resDBS['new_allmFD']
				
				#for key in resDBS:
				#	print resDBS[key]['metaD']['pos_num'],resDBS[key]['metaD']['title'].encode(BASE_ENCODING)
		
			print('print OK')
			
		resDBS['init_selected_node_folder'] = music_folder		
				
		paramD = {'action':'get_new_album_in folder_node'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
				#self.__model_instance.setSearchBufD('tracks_preloaded_from_folder_buf',resDBS,None,None,paramD)
				
		self.__model_instance.setTracksPreloadRes_BufD(resDBS)
				
		print('before map')	
		self.__logger.debug('before map_meta_album_tracks_struct_to_view_json')	
		
		album_artistD = resDBS['album_artistD']
		albumDL = self.map_meta_album_tracks_struct_to_view_json(new_allmFD,album_artistD)	
				
			# ВНИМАНИЕ! proc_state - является ключем для bufferD													
		vldt_art_key = zlib.crc32(b'art_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		vldt_albNSA_key = zlib.crc32(b'alb_NSA_db_buf'+bytes(str(time.time()),encoding = 'utf-8'))
		print('CRC32')	
		self.__modelDic['tracks_preload_proc_buf_db'] = {
														'tracks_view':{'dataD':{'initial':albumDL,'initial_changed':[],'tb_save':[],'saved':[]},
														'proc_state':'initial','validity_key':vldt_art_key, 'message_log':'','cur_page':1,
														'checked_pageL':[1]
														},
														'album_NSA_view':{'dataD':{'initial':[],'initial_changed':[],'tb_save':[],'saved':[]},
														'proc_state':'initial',
														'message_log':'','cur_page':1,
														'checked_pageL':[1]
														},
														'active_view':'artist',
														'proc_type':'data_from_db'
														}
		
		print('modeldic ok')	
		#resDBS = myMediaLib_adm.ri (dbPath,[sel_dir],'save_db')
		
		#self.__logger.debug('3752 get_tracks_4_cur_album_fromPL: len[%s] '%(str(len(imageL))))
		# Найти срц32 текущего альбома album_crc32 = metaD_of_cur_pL[1989996026]['album_crc32']
		
		paramD = {'action':'get_album_tracks_from_cur_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
		
		
		
		self.__logger.debug('in get_tracks_4_cur_album_fromPL OK')
		return 1
		
	def save_tracks_from_preload_scenario(self,commandD):
		#saveLibClast_to_DB(dbPath,allmFD,*args)
		self.__logger.debug('in save_tracks_from_preload_scenario [%s] - Start '%(str(commandD)))
		album_crc32 = int(commandD['text_line'])
		bufD = self.__model_instance.getTracksPreloadRes_BufD()
		trackLD = bufD['new_allmFD']
		album_artistD = bufD['album_artistD']
		tb_saveTracklD = {}
		tb_savealbum_artistD = {}
		
		if album_crc32:
			dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
			print("tuta save")
			for a in trackLD:
				if trackLD[a]['album_crc32'] == album_crc32:
					tb_saveTracklD[a] = trackLD[a]
					
			for a in album_artistD:
				if a == album_crc32:
					tb_savealbum_artistD[a] = album_artistD[a]
			
			print(len(tb_saveTracklD))
			t_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
			resD = saveLibClast_to_DB_unicode(dbPath,tb_saveTracklD,tb_savealbum_artistD,t_date,'save')
			if resD['insL'] != []:
				lenResD = len(resD['insL'])
				print('Correct artist CRC32 for:',lenResD)
			
		self.__logger.debug('in save_tracks_from_preload_scenario Finished')
		return 1
		
		
	def	remove_tracks_from_db(self,commandD):
		#saveLibClast_to_DB(dbPath,allmFD,*args)
		self.__logger.debug('in remove_tracks_from_db [%s] - Start '%(str(commandD)))
		album_crc32 = int(commandD['text_line'])
		album_tobe_remove = False
		resD = {}
		bufD = self.__model_instance.getTracksPreloadRes_BufD()
		
		
		trackLD = bufD['new_allmFD']
		album_artistD = bufD['album_artistD']
		tb_removeTrackL = []
		tb_removeAlbumL = []
		aD = {}
		
		
		if album_crc32:
			aD[album_crc32]= album_artistD[album_crc32]
			dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
			resD = validate_ArtistAlbumLibClast_from_DB(dbPath,aD,'remove_check')
			#check action in general
			if not resD['action']:
				self.__logger.warning('in remove_tracks_from_db - Validate REMOVE FAILED ')
				return 1
			
			if 'ref_track_L' in resD:
				if resD['ref_track_L'] !=[]:
					r = delete_tracks_via_DbIdL(dbPath,resD['ref_track_L'],'remove')
					if r == 1:
						self.__logger.info('in remove_tracks_from_db - Deleted tracks OK [%s]'%(str(resD['ref_track_L'])))
					else:
						self.__logger.critical('in remove_tracks_from_db - Deleted album ERROR [%s]'%(str(resD['ref_track_L'])))
				else:
					self.__logger.critical('in remove_tracks_from_db - Validate 2 artist ERROR [%s]'%(str(resD)))
				
				if resD['del_alb_L'] != []:
					r = delete_album_via_DbIdL(dbPath,resD['del_alb_L'],'remove','with_artist_album_ref_check')
					if r == 1:
						self.__logger.info('in remove_tracks_from_db - Deleted album OK [%s]'%(str(resD['del_alb_L'])))
					else:
						self.__logger.critical('in remove_tracks_from_db - Deleted album ERROR [%s]'%(str(resD['del_alb_L'])))
				else:
					self.__logger.critical('in remove_tracks_from_db - Validate 3 artist ERROR [%s]'%(str(resD)))
					
				if resD['del_art_L'] != []:
					for item in resD['del_art_L']:
						r = delete_Artist(dbPath,item['id_artist'],item['id_album'],None,None,'remove')
						if r == 1:
							self.__logger.info('in remove_tracks_from_db - Deleted artist OK [%s,%s]'%(str(item['id_artist']),str(item['id_album'])))
						else:
							self.__logger.critical('in remove_tracks_from_db - Deleted artist ERROR [%s,%s]'%(str(item['id_artist']),str(item['id_album'])))
				else:
					self.__logger.warning('in remove_tracks_from_db -  artist not deleted [%s] - mb due to existens before'%(str(resD)))			
			else:
				self.__logger.critical('in remove_tracks_from_db - Validate 1 artist ERROR [%s]'%(str(resD)))
			
		self.__logger.debug('in remove_tracks_from_db Finished')
		return 1
		
	def play_album_from_folder(self,commandD):
		#depricated use play_album_or_track_from_folder with album_mode
		self.__logger.info('at play_album_from_folder: [%s] -START '%(str(commandD)))
		self.__logger.info('at play_album_from_folder: Finished ')
		return 
	
	def play_album_or_track_from_folder(self,commandD):
		self.__logger.info('at play_album_or_track_from_folder: [%s] -START '%(str(commandD)))
		album_crc32 = None
		track_crc32 = None
		album_mode = False
		isCue = False	
		if 	commandD['trackpreload'] == 'play_album':
			print('play_album')
			self.__logger.debug('at play_album_or_track_from_folder: album mode')
			album_crc32 = int(commandD['text_line'])
			album_mode = True
		elif commandD['trackpreload'] == 'play_track':
			print('play_track')
			self.__logger.debug('at play_album_or_track_from_folder: track mode')
			try:
				track_crc32 = int(commandD['text_line'])
			except:
				track_crc32 = None
			
		mpdMusicPathPrefix = self.__model_instance.getMediaLibPlayProcessContext()['mpdMusicPathPrefix']	
		audioFilesPathRoot = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audioFilesPathRoot']
		
		mpdMusicPathPrefix_bs = bytes(mpdMusicPathPrefix,encoding = 'utf-8')
		audioFilesPathRoot_bs = bytes(audioFilesPathRoot,encoding = 'utf-8')
		
		#self.__model_instance.setTracksPreloadRes_BufD(resDBS)
		resDBS = self.__model_instance.getTracksPreloadRes_BufD()['new_allmFD']
		selected_init_folder =  self.__model_instance.getTracksPreloadRes_BufD()['init_selected_node_folder']
		selected_init_folder_bs = bytes(selected_init_folder,encoding = 'utf-8')
		
		remote_host = self.__modelDic['REMOTE_ADDR']
		mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
		mpd_socket = mpd_instance['socket']
		host = mpd_instance['host']
		host_ip = socket.gethostbyname(host)
		
		
		# получить метаданные из сохраненного get_tracks_4_selected_folder по album_id
		track_num = 0
		print(resDBS.keys())
		if track_crc32 in resDBS:
			self.__logger.debug('at play_album_or_track_from_folder: track res buf found ')
			album_crc32 = resDBS[track_crc32]['album_crc32']
			track_num = int(resDBS[track_crc32]['metaD']['tracknumber'])-1
		pl = []
		if album_mode:
			print("tuta album")
			
			pl = generate_play_list_from_fileData(resDBS,album_crc32,None,audioFilesPathRoot,mpdMusicPathPrefix)
			
		else:
			print("tuta track")
			pl = generate_play_list_from_fileData(resDBS,None,track_crc32,audioFilesPathRoot,mpdMusicPathPrefix)
			print(resDBS[track_crc32])
			
		self.__logger.info('at play_album_or_track_from_folder: ready to play track[%i] '%track_num)
		
		if pl != []:
			
			client = MPDClient()
			client.disconnect()
			# take for check first file from detected list
			inMPD_DB = False
			for a in resDBS:
				if resDBS[a]['album_crc32'] == album_crc32:
					if 'cue' in resDBS[a]:
						isCue = True	
					#print('--1--')	
					uri_file = os.path.relpath(resDBS[a]['orig_fname'],audioFilesPathRoot_bs).replace(b"\\",b"/")
					#print('--2--')	
					uri_file = os.path.join(mpdMusicPathPrefix_bs,uri_file)
					#convert selected folder to MPD style
					uri_file = uri_file.decode('utf-8')
					#print(uri_file) 
					#print('--3--')	
					selected_init_folder_bs = os.path.relpath(selected_init_folder_bs,audioFilesPathRoot_bs).replace(b"\\",b"/")
					#print('--4--')	
					selected_init_folder_bs = os.path.join(mpdMusicPathPrefix_bs,selected_init_folder_bs)
					#print('--5--')	
					selected_init_folder_conv = selected_init_folder_bs.decode('utf-8')
					#print('--6--')	
					
					#print('selected_init_folder=',selected_init_folder)
					inMPD_DB = asyncio.run(check_update_mpd_db(client,host_ip,mpd_socket,selected_init_folder,uri_file))
					print('--6--',inMPD_DB)
					break
					
			if inMPD_DB:
				resL = asyncio.run(load_mpd_playlist_via_pathL(client,host_ip,mpd_socket,pl, isCue))
				self.__logger.info('at play_album_or_track_from_folder: Finished ')
			return {}
		else:
			self.__logger.critical('Error: at play_album_or_track_from_folder: emply list returned ')
		return 
		
	def get_tracks_from_temp_plist(self,commandD):	
		
		self.__logger.info('get_tracks_from_temp_plist: [%s] '%(str(commandD)))
		#metaD[a[1]] = {'id_track':a[0],'title':a[2],'artist':a[3],'album':a[4], 'path':a[5], 'cue_num':a[6],'cue_fname':a[7],'format':format,'bitrate':a[8]}
		crc32L = self.__model_instance.getMediaLibPlayProcess_State()['Temp_MemCRC32_PlayList']
		print('crc32L:',crc32L)
		DB_metaIndxD = self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')
		
		dbIdL = [DB_metaIndxD[a][0] for a in crc32L if a in DB_metaIndxD]
		print(dbIdL)
		metaD_of_temp_pL = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,None)
		print('metaD_of_temp_pL:',metaD_of_temp_pL)
		
		paramD = {'action':'get_tracks_from_temp_plist'}
		if 'srch_rep_mode' in commandD:
			paramD['mode']=commandD['srch_rep_mode']
			
		self.__model_instance.setSearchBufD('get_tracks_from_temp_plist',metaD_of_temp_pL,None,None,paramD)
		#print metaD_of_cur_pL[metaD_of_cur_pL.keys()[0]].keys()
		print('in get_tracks_from_temp_plist OK')	
		return 1
		
	def	get_album_autocompl_data_db(self,commandD):	
		self.__logger.info('get_album_autocompl_data_db: [%s] '%(str(commandD)))
		#print commandD
		object_data = {}
		search_termD = {}
		dbnew_search_termL =[]
				
		if 'object_data' in commandD:
			object_data = commandD['object_data']
			
			fieldL =['search_term','object']
			for a in fieldL:
				if a not in object_data:
					print("Wrong data params  for artist save",a)
					return 
					
			search_object_key = object_data['object']		
			search_termD[search_object_key] = object_data['search_term']
			dbnew_search_termL = search_termD[search_object_key].split()
			print(dbnew_search_termL)
			
		#dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']			
		#resL = getArtist_Album_list_db_via_search_term(dbPath,search_termD,20)
		DB_meta_Search_IndxD=self.__model_instance.MediaLibPlayProcessDic_viaKey('DB_metaIndxD','local')
		print('DB_meta_Search_IndxD:',len(DB_meta_Search_IndxD))
		resL = getAlbum_list_db_via_AAT_search_term(dbnew_search_termL,[],DB_meta_Search_IndxD)['resultL']
		resL_short = []
		print('getAlbum_list_db_via_AAT_search_term:',len(resL))
		cnt = 0
		tempAlbumL = []
		for a in resL:
			if a['album'] not in tempAlbumL:
				tempAlbumL.append(a['album'])
			else:
				continue
			name = a['artist']+'-'+a['album']+'-'+a['track']
			resL_short.append({"name": name, "key": a['album_crc32'],"album": a['album']})
			if cnt > 21:
				break
			cnt+=1
			
		
		self.__modelDic['object_autocomplL'] = {'autocoml_data':resL_short}
		self.__logger.debug('get_album_autocompl_data_db: --Finished ')
		#print(self.__modelDic['object_autocomplL'])
		return 1	
		
	def	get_album_folder_autocompl_data_db(self,commandD):	
		self.__logger.info('at get_album_folder_autocompl_data_db: [%s] '%(str(commandD)))
		#print commandD
		object_data = {}
		search_termD = {}
		dbnew_search_termL =[]
		check_keyL = []
				
		if 'object_data' in commandD:
			object_data = commandD['object_data']
			
			fieldL =['search_term','object']
			for a in fieldL:
				if a not in object_data:
					print("Wrong data params  for artist save",a)
					return 
					
			search_object_key = object_data['object']		
			search_termD[search_object_key] = object_data['search_term']
			dbnew_search_termL = search_termD[search_object_key].split()
			
			print(dbnew_search_termL)
		
		update_mode = False	
		if 'update_mode' in commandD:
			if commandD['update_mode'] != 'notindb':
				update_mode = True
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']	
		print('update_mode=',update_mode)
		#resL = getArtist_Album_list_db_via_search_term(dbPath,search_termD,20)
		
		termL = []
		for a in dbnew_search_termL:
			termL.append(a.lower())
		resL_short = []
		autoComplBufD={}
		
		path_prefixL = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audio_files_path_list']
		audioFilesPathRoot = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')['audioFilesPathRoot']
		#path_prefixL = os.path.normpath(self.__configDict['audioFilesPathRoot'])
		
		for i in range(len(path_prefixL)):
			path_prefixL[i] = os.path.normpath(path_prefixL[i])
		
		MLFolderTreeNodeL = getFolderAlbumD_fromDB(dbPath,None,None,[],'all')
		print("*****Tut1****",len(MLFolderTreeNodeL))
		extract_dirL = [] # Additional dir list for nodes at higher level
		node_key = 'folder_node'
		node_key = 'path'
		
		tempL = []
		for a in MLFolderTreeNodeL:
			found_term = True	
			for term in termL:
				try:
					path_lower = a[node_key].lower()
				except:
					print("---------------------->>error:", MLFolderTreeAll_List.index(a),a)
					
				if term not in path_lower:
					found_term = False
					break 
			if not found_term:
				continue
			
			path = os.path.normpath(audioFilesPathRoot)+'\\'+a[node_key]
			key = zlib.crc32(path.encode(BASE_ENCODING))
			if key not in check_keyL:
				check_keyL.append(key)
			else:
				continue
			for prefix in path_prefixL:
				item_name = ''
				#print("prefix=",prefix)
				if os.path.normpath(prefix) in path:
					item_name = path[len(prefix):]
					#print('*',path)
					#print('item=',item_name)
					extract_dirL.append(a[node_key])
					break
				else:
					#print('+ PROPUSK')
					continue
					
					
				extract_dirL.append(a[node_key])
			resL_short.append({"name": item_name, "key": key,"album": item_name})
			autoComplBufD[key] = path
		
		stackL = []		
		
		
		if not update_mode:
			print("*****Tut3****",len(extract_dirL))
			for a in extract_dirL:
				
				path = os.path.normpath(audioFilesPathRoot)+'\\'+a
				#print("path=",path)
				#print('path_prefixL=',path_prefixL)
				l = get_parent_folder_stackL(path,path_prefixL)
				#print('l=',l)
				dif_L = list(set(l).difference(set(stackL)))
				stackL += dif_L
			
			print("*****Tut4****",len(extract_dirL))	
			#print('stackL=',len(stackL),stackL)
			for a in stackL:
				found_term = True	
				for term in termL:
					try:
						path_lower = a.lower()
					except:
						print("---------------------->>error:", MLFolderTreeAll_List.index(a),a)
						
					if term not in path_lower:
						found_term = False
						break
				if not found_term:
					continue
				key = zlib.crc32(a.encode(BASE_ENCODING))
				if key not in check_keyL:
					check_keyL.append(key)
				else:
					continue
				for prefix in path_prefixL:
					item_name = ''
					#print("prefix=",prefix)
					if prefix in a:
						item_name = a[len(prefix):]
						#print('*', a)
						break
					else:
						continue
							
				resL_short.append({"name": item_name, "key": key,"album": item_name})
				autoComplBufD[key] = a
				
				if item_name not in tempL:
					tempL.append(item_name)
				else:
					print('dublicate:',a)
			
		resL_short.sort(key=operator.itemgetter('name'))
		resL_short = resL_short[:40]
		#print('2',resL_short)
		
		
		self.__modelDic['object_autocomplL'] = {'autocoml_data':resL_short}
		self.__model_instance.setAutoComplSearch_BufD(autoComplBufD)
		
		self.__logger.info('get_album_folder_autocompl_data_db: FINISHED ')
		return 1		
		
	def	get_artist_album_autocompl_data_db(self,commandD):	
		self.__logger.info('get_artist_album_autocompl_data_db: [%s] '%(str(commandD)))
		#print commandD
		object_data = {}
		search_termD = {}
				
		if 'object_data' in commandD:
			object_data = commandD['object_data']
			
			fieldL =['search_term','object']
			for a in fieldL:
				if a not in object_data:
					print("Wrong data params  for artist save",a)
					return 
					
			search_object_key = object_data['object']		
			search_termD[search_object_key] = object_data['search_term']
			
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']			
		resL = getArtist_Album_list_db_via_search_term(dbPath,search_termD,20)
		self.__modelDic['object_autocomplL'] = {'autocoml_data':resL}
		#print resL
		return 1
		
	def get_artist_live_search_variants(self,commandD):	
		print('get_artist_live_search_variants!!!!:',commandD)	
		self.__logger.debug('in get_artist_live_search_variants: [%s] - Start'%(str(commandD)))
		
		# Если метаданные еще не получены то нижестоящая фукция их соберет, если уже были собраны,то из нее быстрый выход
		
		#ArtistL=self.__model_instance.MediaLibPlayProcessDic_viaKey('Artist_metaBufL','local')
		ArtistL=self.__model_instance.MediaLibPlayProcessDic_viaKey('ArtistL','local')
		#Artist_metaBufL
		input_variantL = []
		for a in ArtistL:
			tmpL = a[0].split()
			for b in tmpL:
				check_clause = False
				
				try:
					check_clause =  b.startswith(commandD['search_term'].lower().strip())
				except:
					check_clause =  b.decode('utf-8').lower().strip().startswith(commandD['search_term'].lower().strip())
					#print [b.decode('utf-8')],check_clause
				if check_clause:
					if a not in input_variantL:
						input_variantL.append(a)
		if 	input_variantL == [] and 'get_artist_live_search_variants_opt'	in 	commandD:
			input_variantL = ArtistL
		
		self.__logger.debug('in get_artist_live_search_variants - Finished')
		return input_variantL				
	def get_artist_meta_buf_live_search_variants(self,commandD):	
		
		self.__logger.debug('get_artist_meta_buf_live_search_variants: [%s] - Start'%(str(commandD)))
		
		# Если метаданные еще не получены то нижестоящая фукция их соберет, если уже были собраны,то из нее быстрый выход
		
		ArtistL=self.__model_instance.MediaLibPlayProcessDic_viaKey('Artist_metaBufL','local')
		#ArtistL=self.__model_instance.MediaLibPlayProcessDic_viaKey('ArtistL','local')
		#Artist_metaBufL
		input_variantL = []
		#print ArtistL
		for a in ArtistL:
			
			tmpL = a.split()
			
			for b in tmpL:
				if b.lower().strip().startswith(commandD['search_term'].lower().strip()):
					if (a,1) not in input_variantL:
						input_variantL.append((a,1))					
			
		
		self.__logger.debug('get_artist_meta_buf_live_search_variants - Finished')
		return input_variantL
	
		
	def do_search(self,commandD):	
		
		self.__logger.info('do_search: [%s] '%(str(commandD)))
		search_term = commandD['search_term']
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		paramD = {}
		if 'tag_maintain' in  commandD or 'search' in  commandD:
			#print '2'
			if 'selL' in commandD:
				#print 'selL=',commandD['selL']
				search_paramL = []
				search_paramL = [a for a in ['artist','album','title']	if a in commandD['selL']]
					
				sD =  searchMediaLib_MetaData(dbPath,search_term,search_paramL,[])
			else:	
				sD =  searchMediaLib_MetaData(dbPath,search_term,[],[])
			#print 'lenSd=',len(sD)
			
			
			if 'tag_maintain' in  commandD:
				paramD['action'] = 'tag_maintain'
			elif 'search' in  commandD:	
				paramD['action'] = 'general_search'
			
			if 'srch_rep_mode' in commandD:
				paramD['mode']=commandD['srch_rep_mode']
			
			
			self.__model_instance.setSearchBufD(search_term,sD,self.__model_instance.getSearchBufD()['tag_id'],self.__model_instance.getSearchBufD()['tag_form_mode'],paramD)
		else:
			paramD['action'] = 'unknown'
			
			if 'srch_rep_mode' in commandD:
				paramD['mode']=commandD['srch_rep_mode']
				
				
			sD =  searchMediaLib_MetaData(dbPath,search_term,[],self.__listsMetaData)
			#print len(sD)
			self.__model_instance.setSearchBufD(search_term,sD,None,None,paramD)
		
		self.__logger.info('in do_search OK')
		return 1
		
	def get_picture(self,commandD):	
		# Загрузка картинки по URL из админ закладки
		self.__logger.info('action get_picture!!!!:%s'%(str(commandD)))
		url = commandD['text_line']
		self.__logger.debug('before dest_dir = self.__model_instance.getCurAlbumDir()')
		
		# Проверить что картинка для РАДИО, проверить есть ли папка для нее по узлу из шаблона. если нет создать е???
		dest_dir = self.__model_instance.getCurAlbumDir()
		
		self.__logger.debug('Pic PrepareOK for %s %s'%(dest_dir,url))
			
		try:
			if getCoverPage(url,dest_dir) == -1:
				self.__logger.critical('Error 4644: in getting pic')
		except Exception as e:
			self.__logger.critical('Exception: Strange exception in picture getting: %s'%e)
		
		self.__logger.info('action get_picture OK')
		return 1	
	
	def get_radio(self,commandD):	
		
		self.__logger.info('action get_radio!!!!:%s'%(str(commandD)))
		url = commandD['radio_URL']
		name = commandD['radio_name']
		existed_station = commandD['existed_stations']
		self.__logger.debug('before dest_dir = self.__model_instance.RADIO')
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']	
		
		self.__logger.debug('RADIO PrepareOK for %s %s existed[%s]'%(str(name),str(url), str(existed_station)))
		
		
		if not existed_station.isdigit():
			existed_station = None
		
		try:
			r = registerRadio(dbPath,url,name,existed_station,128)
				
		except Exception as e:
			self.__logger.critical('Exception: Strange exception in Radio getting: %s'%e)
		
		self.__logger.info('action get_radio OK')
		return 1
		
	def set_mpd_instance(self,commandD):	
		
		self.__logger.info('in action set_mpd_instance Start:%s'%(str(commandD)))
		host = commandD['mpd_instance']
		
		remote_host = self.__modelDic['REMOTE_ADDR']
		self.__logger.debug('before dest_dir = self.__model_instance.MPD')
		#print('before:',self.__model_instance.getPlayerInstanceList()) 		
		for item in self.__model_instance.getPlayerInstanceList():
			if item['host'] == str(host):
				self.__model_instance.setCurPlayerInstance(str(host),item['socket'],remote_host)
				break
		#print('after:',self.__model_instance.getPlayerInstanceList()) 				
				
		self.__logger.debug('MPD SelectOK for [%s]'%(str(self.__model_instance.getCurPlayerInstance(remote_host))))
		
		self.__logger.info('in action get_mpd_instance Finished OK')
		return 1
		
	def do_debug(self,commandD):	
			
		self.__logger.info('in action do_debug: [%s] '%(str(commandD)))
		if 'selL' in commandD:
			
			if len(commandD['selL'])>0:
				self.__modelDic['debugD'] = commandD['selL']
				return None
		self.__modelDic['debugD'] = {}		
		return None		
	
	
	def get_object_edit_data(self,commandD):	
		self.__logger.info('in action get_object_edit_data: [%s] '%(str(commandD)))
		
		stop_list_punct = ['.',';','/','_','&','(',')','%','?','!',]
		stop_list_word = ['the','a']
		
		search_term = ''
		artist_name = ''
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		object_type = ''
		if 'object' in commandD:
			object_type = commandD['object']
		
		
		#print object_type
		
		if object_type == 'artist':
		
			# Референтные списки через фунцию getAll_Related_to_main_Artist_fromDB:
			#1. Список со ссылкой или ссылками на главных (для playtogether их несколько)
			#2. Список со ссылкам от главного (для главного)
			#3. Список всего кластера для неглавног
			artists_from_main_relL = [] 
			artists_main_to_relL = [] 
			artists_all_relL = [] 
			artists_from_main_relLD = [] # для главного список подчиненных
			artists_main_to_relLD = [] # список главных артистов для неглавного или виртуальных для неглавного
			artists_all_relLD = [] # список всего кластера для неглавного
			object_crc32 = int(commandD['key'])
			
			object_dbD=getArtistD_fromDB(dbPath,object_crc32,[])[object_crc32]
			print(object_dbD)
			print(list(object_dbD.keys()))
			
			try:
				search_term = object_dbD['search_term'].strip().lower()
			except:
				search_term = ''
			
			if search_term == '':
				
				frase = object_dbD['artist'].lower()
				for a in stop_list_punct:
					if a in frase:
						frase = frase.replace(a,' ')
				
				fraseL  = 	frase.split()
				rL = []
				for a in fraseL:
					a = a.strip()
					if a not in stop_list_word:
						rL.append(a)
				
				search_term = ' '.join(rL)
				
				object_dbD['search_term'] = search_term
				
				
			object_type = 'general artist'
			
			artist_album_relLD = []
			
			album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,None,[],object_crc32,None)	
			
			#rel_artL = getAll_Related_to_main_Artist_fromDB(artist_crc32)
			
			# Получаем данные по всем артистам они нужны чтобы востановить исходные данные в референтных списках
			artist_dbD_all=getArtistD_fromDB(dbPath,None,[],'wo_reflist')
			
			# Получаем референтные списки фром для главного и ту для обычных
			if (object_dbD['main'] == 'X' or object_dbD['main'] == True):	
				print('this is main!!!!')
				artists_from_main_relLD = getArtist_relation_metaD(dbPath,object_crc32,'main')['artists_from_main_relLD']
				#print 'done'
				pos = 1
				for item in artists_from_main_relLD:
					item['artist'] = artist_dbD_all[item['key'] ]['artist']
					item['object_type'] = artist_dbD_all[item['key'] ]['object_type']
					item['main'] = artist_dbD_all[item['key'] ]['main']
					if (pos % 2):
						even_odd = 'even'
					else:
						even_odd = 'odd'
					pos+=1	
					item['colorcl']	= even_odd
					item['checked'] = True
					
				#print artists_from_main_relLD
			else:
				print('this is NOT main!!!!')
				resD = getArtist_relation_metaD(dbPath,object_crc32,'get_neibor')
				#print resD.keys()
				artists_all_relLD = resD['artists_all_relLD']
				artists_main_to_relLD = resD['artists_main_to_relLD']
				pos = 1
				for item in artists_main_to_relLD:
					item['artist'] = artist_dbD_all[item['key'] ]['artist']
					item['object_type'] = artist_dbD_all[item['key'] ]['object_type']
					item['main'] = artist_dbD_all[item['key'] ]['main']
					if (pos % 2):
						even_odd = 'even'
					else:
						even_odd = 'odd'
					pos+=1	
					item['colorcl']	= even_odd
					item['checked'] = True
					
				for item in artists_all_relLD:
					item['artist'] = artist_dbD_all[item['key'] ]['artist']
					item['object_type'] = artist_dbD_all[item['key'] ]['object_type']
					item['main'] = artist_dbD_all[item['key'] ]['main']
					if (pos % 2):
						even_odd = 'even'
					else:
						even_odd = 'odd'
					pos+=1	
					item['colorcl']	= even_odd
					item['checked'] = True	
				#print resD
				
			self.__modelDic['album_artist_metaD_db'] = album_artist_metaD_db
			
			pos = 1
			
			for rel_item in album_artist_metaD_db['artist_album_refLD']:
								
				album_item = album_artist_metaD_db['albumD'][rel_item['album_key']]
				#album_item['path'] = album_item['path'].replace('\\','/')
				album_item['path'] = "disable"
				keyL =[b for b in album_item if b != 'artistD']
				new_Item = {}
				for b in keyL:
					
					new_Item[b] = album_item[b]
					
				new_Item['key']	= str(rel_item['album_key'])
				new_Item['checked']	= 'X'
				
				# Это надо менять, забирать артистов надо проверяя их связь в ARTIST_ALBUM_REF
				#if rel_item['rel_type'] <> None:
					#continue
				#else:
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
				new_Item['colorcl']	= even_odd
				#print '2',new_Item['object_type'],new_Item['artist']
				artist_album_relLD.append(new_Item)	
				pos+=1	
			
			if object_dbD['object_type']:
				object_type = object_dbD['object_type']
				
			artist = object_dbD['artist']
			
			#print '------>', type(artist),artist
			#print json.dumps(artist)
			self.__modelDic['edit_object_struc'] = {'artist_crc32':object_crc32,
													#'search_term':search_term,'artist_name':artist_name,
													'artist':artist,
													'object_type':object_type,
													'artistD':object_dbD,
													'album_for_artist_relLD':artist_album_relLD,
													'artists_from_main_relLD':artists_from_main_relLD,
													'artists_main_to_relLD':artists_main_to_relLD,
													'artists_all_relLD':artists_all_relLD,
													'main_checked_flag':'','rel_type':'no_selection'	}
		elif object_type == 'album':											
			object_crc32 = int(commandD['key'])
			
			print('album:',object_crc32)
			object_dbD=getAlbumD_fromDB(dbPath,None,object_crc32,[])['albumD'][object_crc32]
			object_dbD['path']= object_dbD['path'].replace('\\',':')
			
			try:
				search_term = object_dbD['search_term'].strip().lower()
			except:
				search_term = ''
			
			if search_term == '':
				
				frase = object_dbD['album'].lower()
				for a in stop_list_punct:
					if a in frase:
						frase = frase.replace(a,' ')
				
				fraseL  = 	frase.lower().split()	
				rL = []
				for a in fraseL:
					a = a.strip()
					if a not in stop_list_word:
						rL.append(a)
				
				search_term = ' '.join(rL)
				object_dbD['search_term'] = search_term
				
				
			
			object_type = 'general album'
			album_type = ''
			if object_dbD['object_type']:
				object_type = object_dbD['object_type']
				
			if object_dbD['album_type'] != 'ONE_ARTIST':
				album_type =  'NSA'
				
			album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,None,[],None,object_crc32)	
			#print 'getArtist_Album_metaD_fromDB OK'
			album_rel_Dic = getAlbum_relation_metaD(dbPath,None,object_crc32,'from','get_neibor')
			
			
			artist_album_relLD = []
			artist_relLD = []
			album_relLD = []
			
			album_from_relLD  = []
			rel_albumD = {}
			
			
			
			tmpL = []
			for item in album_rel_Dic['albums_from_relLD']:
				rel_albumD=getAlbumD_fromDB(dbPath,None,item['key'],[],'wo_reflist')['albumD'][item['key']]
				rel_albumD['key']	= str(item['key'])
				rel_albumD['path']	= "disabled"
				rel_albumD['checked']	= 'X'
				tmpL.append((rel_albumD['album'],rel_albumD))

			
			tmpL.sort()
			pos = 1
			for item in tmpL:
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
				item[1]['colorcl']	= even_odd
				album_from_relLD.append(item[1])
				pos+=1		
			
			
			pos = 1
			tmpL = []
			if object_crc32 in album_artist_metaD_db['albumD']:
				print('in rel AlbumD',object_crc32)
				for item in album_artist_metaD_db['albumD'][object_crc32]['ref_album_crc32L']:
					#print 'item-->:',item
					albumD =getAlbumD_fromDB(dbPath,None,item[1],[],'wo_reflist')['albumD']
					#print albumD.keys(),
					rel_albumD = albumD[item[1]]
					rel_albumD['path']	= "disabled"
					rel_albumD['key']	= str(item[1])
					rel_albumD['checked']	= 'X'
					tmpL.append((rel_albumD['album'],rel_albumD))
					
			
			
			tmpL.sort()
			for item in tmpL:
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
				item[1]['colorcl']	= even_odd
				album_relLD.append(item[1])
				pos+=1				
					
			
			pos = 1
			for rel_item in album_artist_metaD_db['artist_album_refLD']:
								
				artist_item = album_artist_metaD_db['artistD'][rel_item['artist_key']]
				
				keyL =[b for b in artist_item if b != 'albumD']
				new_Item = {}
				for b in keyL:
					new_Item[b] = artist_item[b]
					
				new_Item['key']	= str(rel_item['artist_key'])
				new_Item['checked']	= 'X'
				
				# Это надо менять, забирать артистов надо проверяя их связь в ARTIST_ALBUM_REF
				if rel_item['rel_type'] != None:
					#print '1',new_Item['object_type'],new_Item['artist']
					new_Item['rel_type'] = 	rel_item['rel_type']
					artist_relLD.append(new_Item)
					
				else:
					#print '2',new_Item['object_type'],new_Item['artist']
					artist_album_relLD.append(new_Item)
				
			
			pos = 1	
			for item in artist_album_relLD:
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
					
				item['colorcl']	= even_odd		
				pos+=1	
				
			pos = 1	
			for item in artist_relLD:
				if (pos % 2):
					even_odd = 'even'
				else:
					even_odd = 'odd'
					
				item['colorcl']	= even_odd		
				pos+=1	
				
			
			
			self.__modelDic['edit_object_struc'] = {'album_crc32':object_crc32,
													#'search_term':search_term,'artist_name':artist_name,
													'album':object_dbD['album'],
													'object_type':object_type,
													'album_type': album_type,
													'album_object_type':object_type,
													'albumD':object_dbD,
													'artist_album_relLD':artist_album_relLD,
													'artist_relLD':artist_relLD,
													'album_relLD':album_relLD,
													'album_from_relLD':album_from_relLD,
													'main_checked_flag':'','rel_type':'no_selection'	}
		
		#print commandD
		return 1
		
	def maintain_single_artist_rel(self,commandD):
		# точечная функция обрабработки процесса изменения Альбома или Артиста и всех их связей
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		self.__logger.info('in action maintain_single_artist_rel: [%s] '%(str(commandD)))
		if 'alb_art_relation_struct' in commandD:
			relation_struct = commandD['alb_art_relation_struct']
			ref_artist_crc32 = int(relation_struct['ref_artist_key'])
			artist_crc32 = int(relation_struct['artist_key'])
			relation = relation_struct['relation']
			
			res = 0
			
			if relation_struct['mode'] == 'create':
				rel_type = relation_struct['rel_type']
				print(relation,rel_type)
				
				if relation == "ART_MAIN_TO_REL":
					print("Set Object relation ",rel_type,relation)
					res = set_Artist_relation(dbPath,artist_crc32,ref_artist_crc32,{'rel_type':rel_type})	
				
				print('restore_Object_relation..........>',res)
			elif relation_struct['mode'] == 'delete':
				if relation == "ART_MAIN_TO_REL":
					print("in delete:")
					res = delete_Artist_relation(dbPath,artist_crc32,ref_artist_crc32)
				
				print('delete_Object_relation..........>',res)
				
			if res > 0:
				self.__modelDic['maintain_single_artist_album_res'] = res
			else:
				print(res)
				self.__modelDic['maintain_single_artist_album_res'] = 'error'
		
	
	def check_album2artist_rel(self,commandD):
		self.__logger.info('in action check_album2artist_rel: [%s] '%(str(commandD)))
		res = "error"
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		if 'album_key' in commandD:
			album_key = int(commandD['album_key'])
			print('album will be checked',album_key)
			
			art_albD = getArtist_Album_metaD_fromDB(dbPath,None,[],None,album_key)
			albumD = art_albD['albumD'][album_key]
			relD = art_albD['artist_album_refLD']
			relL = [item['artist_key'] for item in relD]
			#print 'cur artL:',relL
			path = albumD['path']
			DbIdL = getDbIdL_w_folderL_filter(dbPath,[path],None)
			#print 'DbIdL:',DbIdL
			artist_album_relLD = []
			if DbIdL != []:
				resD = getCurrentMetaData_fromDB_via_DbIdL(DbIdL,None,'progress')
				artist_crc32L = list(set([resD[key]['artist_crc32'] for key in resD]))
				
				artistD = getArtistD_fromDB(dbPath,None,artist_crc32L,'wo_reflist')
				#print 'check:',artistD.keys()
				#print 'avalable artist_crc32L:',artist_crc32L
				for key in artist_crc32L:
					#print key,
					if key not in relL:
						#print artistD[key]['artist']
						try:
							artistD[key]['key']	= key
						except :
							print('error',key)
							artist_album_relLD.append({'checked':False,'key':key,'artist_song_num':0,'main':False,'colorcl':'album error','artist':'!!->APPEND INITIALY<-!!'})
							continue	
						artistD[key]['checked']	= False
						artistD[key]['artist_song_num'] = 0
						artistD[key]['colorcl'] = 'newasgn'
						
						
						artist_album_relLD.append(artistD[key])
					#else:
						#print	'ok',
						#print artistD[key].keys()
				
				
				#print resD
			
			
			self.__modelDic['edit_object_struc'] = {'album_crc32':album_key,
													
													'artist_album_relLD':artist_album_relLD,
													}
			
			
			
			if res > 0:
				self.__modelDic['check_album2artist_rel_res'] = res
			else:
				print(res)
				self.__modelDic['check_album2artist_rel_res'] = 'error'		
	
	def maintain_single_album_rel(self,commandD):
		# точечная функция обрабработки процесса изменения Альбома или Артиста и всех их связей
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		self.__logger.info('in action maintain_single_album_rel: [%s] '%(str(commandD)))
		if 'alb_art_relation_struct' in commandD:
			relation_struct = commandD['alb_art_relation_struct']
			ref_album_crc32 = int(relation_struct['ref_album_key'])
			album_crc32 = int(relation_struct['album_key'])
			relation = relation_struct['relation']
			
			res = 0
			
			if relation_struct['mode'] == 'create':
				rel_type = relation_struct['rel_type']
				print(relation,rel_type)
				
				if relation == "ALB_REL_ROLE":
					print("Set Object relation ",rel_type,relation)
					res = set_Albums_relation(dbPath,album_crc32,ref_album_crc32,{'rel_type':rel_type})	
				
				print('restore_Object_relation..........>',res)
			elif relation_struct['mode'] == 'delete':
				if relation == "ALB_REL_ROLE":
					print("in delete:")
					res = delete_Albums_relation(dbPath,album_crc32,ref_album_crc32)
				
				print('delete_Object_relation..........>',res)
				
			if res > 0:
				self.__modelDic['maintain_single_artist_album_res'] = res
			else:
				print(res)
				self.__modelDic['maintain_single_artist_album_res'] = 'error'
				
	def maintain_object_attrs(self,commandD):	
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		self.__logger.info('in action maintain_object_attrs: [%s] '%(str(commandD)))
		res = 'error'
		attrsD = {}
		if 'alb_art_attrs_struct' in  commandD:
			print(commandD['alb_art_attrs_struct'])
			if 'main' in commandD['alb_art_attrs_struct']:
				attrsD['main'] = commandD['alb_art_attrs_struct']['main']
			if 'search_terms' in commandD['alb_art_attrs_struct']:
				attrsD['searchTerms'] = commandD['alb_art_attrs_struct']['search_terms']
				
			if 'artist_key' in  commandD['alb_art_attrs_struct']:
				print("artist---")
				res = modifyArtist_viaCRC32(dbPath,commandD['alb_art_attrs_struct']['artist_key'],attrsD)
			elif 'album_key' in  commandD['alb_art_attrs_struct']:
				print("album---")
				res = modifyAlbum_viaCRC32(dbPath,commandD['alb_art_attrs_struct']['album_key'],attrsD)
				
		if res > 0:
			self.__modelDic['maintain_object_attrs_res'] = res
		else:
			print(res)
			self.__modelDic['maintain_object_attrs_res'] = 'error'		
	def maintain_single_artist_album(self,commandD):
		# точечная функция обрабработки процесса изменения связи Альбома или Артиста
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		self.__logger.info('in action maintain_single_artist_album: [%s] '%(str(commandD)))
		if 'alb_art_relation_struct' in commandD:
			relation_struct = commandD['alb_art_relation_struct']
			artist_crc32 = int(relation_struct['artist_key'])
			album_crc32 = int(relation_struct['album_key'])
			relation = relation_struct['relation']
			rel_type = relation_struct['rel_type']
			res = 0
			print(relation,rel_type)
			if relation_struct['mode'] == 'create':
				if relation == "ART_ALB_REL":
					print("tatata ",rel_type,relation)
					res = restore_Album_Artist_relation(dbPath,artist_crc32,album_crc32,{})	
				elif relation == "ART_ALB_REL_ROLE":	
					print("tuta ",rel_type,relation)
					res = restore_Album_Artist_relation(dbPath,artist_crc32,album_crc32,{'rel_type':rel_type})	
				print('restore_Album_Artist_relation..........>',res)
			elif relation_struct['mode'] == 'delete':
				if relation == "ART_ALB_REL":
					print("in delete:",rel_type,relation)
					res = delete_Album_Artist_relation(dbPath,artist_crc32,album_crc32,{})
				elif relation == "ART_ALB_REL_ROLE":
					print("in delete:",rel_type,relation)
					res = delete_Album_Artist_relation(artist_crc32,album_crc32,{'rel_type':rel_type})
				print('delete_Album_Artist_relation..........>',res)
				
			if res > 0:
				self.__modelDic['maintain_single_artist_album_res'] = res
			else:
				print(res)
				self.__modelDic['maintain_single_artist_album_res'] = 'error'
	
	def do_edit_artist(self,commandD):	
			
		self.__logger.info('in action do_edit_artist: [%s] '%(str(commandD)))
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		
		if 'artist' in commandD:
			stop_list_punct = ['.',';','/','_','&','(',')','%','?','!',]
			stop_list_word = ['the','a']
			search_term = ''
			artist_name = ''
			artist_crc32 = int(commandD['artist'])
			rel_artL = []
			ref_artL = []
			
			if 'edit_artist_struc' in self.__modelDic:
				del(self.__modelDic['edit_artist_struc'])
			
			self.__modelDic['edit_artist_struc'] = {'artist_crc32':artist_crc32,
													'search_term':search_term,'artist_name':artist_name,
													'rel_artL':[],'ref_artL':[],'ref_art_newL':[],'main_checked_flag':'','rel_type':'no_selection'	}
			try:
				artistD = self.__model_instance.getReportBuf_forArtist()['artistD']
				self.__logger.debug('artist_search_res_buf get is OK')
			except Exception as e:	
				self.__logger.critical('%s:at reportbuf in do_edit_artist'%(str(e)))
				artistD = {}
			
			##################
			# Написать функцию берущую тип связи для текущего артиста и его связанных соседей ее использовать при показе страницы в дроп дауне.

			#####################	
			
			if artistD != {}:
				self.__logger.debug('artistD.keys(): %s'%(str(list(artistD.keys()))))
			
			
			artist_dbD=getArtistD_fromDB(dbPath,artist_crc32,[])
			self.__modelDic['edit_artist_struc']['artist_dbD'] = artist_dbD
			
			self.__logger.debug('1')
			
			if artist_dbD != {}:
				self.__logger.debug('Artist already in DB:%s'%(str(artist_dbD[artist_crc32])))
				if artist_crc32 in artist_dbD:
					artist_name = artist_dbD[artist_crc32]['artist']
					search_term = artist_dbD[artist_crc32]['search_term']
					
					if search_term == '':
						frase = artist_name
						for a in stop_list_punct:
							if a in frase:
								frase = frase.replace(a,' ')
						
							
						fraseL  = 	frase.split()	
						rL = []
						for a in fraseL:
							a = a.strip()
							if a not in stop_list_word:
								rL.append(a)
						
						search_term = ' '.join(rL)		
						
					main = artist_dbD[artist_crc32]['main']
					ref_artist_crc32L = artist_dbD[artist_crc32]['ref_artist_crc32L']
					
					rel_artL = []
					if main == 'X':
						self.__modelDic['edit_artist_struc']['main_checked_flag']	= 'CHECKED'
						
						rel_artL = getAll_Related_to_main_Artist_fromDB(dbPath,None,artist_crc32)
					else:
						rel_artL = getAll_Related_to_main_Artist_fromDB(dbPath,None,artist_crc32,'get_neibor')

				else:
					
					self.__logger.error('%s :not in-->:%s'%(str(artist_crc32),str(artist_dbD)))
			else:
				ref_artist_crc32 = []
				
				
				if artist_crc32 in artistD:
					artist_name = artistD[artist_crc32]['artist']
					
					frase = artist_name
					for a in stop_list_punct:
						if a in frase:
							frase = frase.replace(a,' ')
						
							
					fraseL  = 	frase.split()	
					rL = []
					for a in fraseL:
						a = a.strip()
						if a not in stop_list_word:
							rL.append(a)
					
					search_term = ' '.join(rL)		
				
				else:
					self.__logger.error('Error---->HHHren artistD:%s'%(str(list(artistD.keys()))))
				
			self.__logger.debug('2')	
			self.__modelDic['edit_artist_struc']['search_term']	= search_term
			self.__modelDic['edit_artist_struc']['artist_name']	= artist_name
			self.__modelDic['edit_artist_struc']['rel_artL']	= rel_artL
			
			ref_artL = getAll_Main_Artist_fromDB(db)
			
			self.__modelDic['edit_artist_struc']['ref_artL']	= ref_artL
			
			
			self.__logger.debug('3')
			ref_art_newL = []
			# Если новый артист на ввод то у него нет референсивных списков пока. значит пропуск
			if len(artist_dbD) == 1:
				artist_dbD=getArtistD_fromDB(dbPath,None,[])
				self.__modelDic['edit_artist_struc']['artist_dbD'] = artist_dbD
		
			self.__logger.debug('4')
			if artist_crc32 in artist_dbD:
				ref_art_newL = [(a,artist_dbD[a]['artist']) for a in artist_dbD[artist_crc32]['ref_artist_crc32L']]
				if 	ref_art_newL != []:
					rel_type = get_artist_ref_relation_type(dbPath,artist_crc32)
					if rel_type != None:
						self.__modelDic['edit_artist_struc']['rel_type'] = rel_type
			self.__logger.debug('5')	
			self.__modelDic['edit_artist_struc']['ref_art_newL']	= ref_art_newL
			self.__logger.debug('6')
			self.__logger.info(' do_edit_artist is OK ')
		return None	
		
	def do_admin(self,commandD):	
		
		self.__logger.info('in action [%s] - START-OK commandD %s:'%('do_admin',str(commandD)))
		levelD = {'DEBUG':logging.DEBUG,'INFO':logging.INFO,'WARNING':logging.WARNING,'ERROR':logging.ERROR,'CRITICAL':logging.CRITICAL}
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		cfgD = readConfigData(mymedialib_cfg)
		
		if 'set_log_level' in commandD:
			if commandD['set_log_level'] in levelD:
				for a in self.__logger.handlers:
					if isinstance(a,logging.StreamHandler):
						a.setLevel(levelD[commandD['set_log_level']])
						
				self.__logger.info('in action [%s] - set_log_level FINISHED-OK:'%('do_admin'))		
				return 1
		if 'do_admin'	in commandD and 'text_line' in commandD:		
			
			self.__logger.debug('in do_admin do ->%s'%(str(commandD)))			
				
			if 'update_lib' == commandD['text_line']:
				triggerBatchJob_via_event(dbPath,'update_lib',None)
			elif 'update_lib_cur_dir'  == commandD['text_line']:
				print("at update_lib_cur_dir exec")
				current_album_dir = self.__model_instance.getCurAlbumDir()[:-1]
				print("at update_lib_cur_dir exec:",current_album_dir)
				triggerBatchJob_via_event(dbPath,'update_lib_cur_dir',current_album_dir)		
			elif 'del_missing_lib'  == commandD['text_line']:
				triggerBatchJob_via_event(dbPath,'del_missing_lib',None)
			elif 'generate_ml_folder_tree_all'  == commandD['text_line']:
				self.__logger.debug('in do_admin do generate_ml_folder_tree_all ->%s'%(str('start')))
				print("at ml_folder_tree_all:")
				triggerBatchJob_via_event(dbPath,'generate_ml_folder_tree_all',None)	
				
				self.__logger.debug('in do_admin do ->%s'%(str(commandD['text_line'])))			
						
				self.__logger.info('in action [%s] - FINISHED-OK:'%('do_admin'))
				return 1					
			elif 'download_ml_folder_tree_all'  == commandD['text_line']:
				self.__logger.debug('in do_admin do download_ml_folder_tree_all ->%s'%(str('start')))
				print("at ml_folder_tree_all: download")
				
				resBuf_ml_folder_tree_buf_path = cfgD['ml_folder_tree_buf_path']
				
				f = open(resBuf_ml_folder_tree_buf_path,'rb')
				Obj = pickle.load(f)
				f.close()
				self.__model_instance.setMLFolderTreeAll_BufD(Obj)
				print("at ml_folder_tree_all: download",list(Obj.keys()))
				self.__logger.debug('in do_admin do ->%s'%(str(commandD['text_line'])))			
						
				self.__logger.info('in action [%s] - Download FINISHED-OK:'%('do_admin'))
				return 1						
			
		if 'selL' in commandD:
			if len(commandD['selL'])>0:
				for a in commandD['selL']:
					
					self.__logger.debug('in do_admin do->%s'%(str(a)))	
					
					try:
						self.__model_instance.RefreshServerContent(a,'')
					except:
						self.__logger.critical('in action [%s] - Error in refresh server:'%('do_admin'))		
						print("error in :",a)
						
				
				self.__logger.info('in action [%s] - FINISHED-OK:'%('do_admin'))
				return 1		
		
		if 'load_template' in commandD and 'do_admin'	in commandD:
			if 'reload_templ'	in commandD['do_admin']:
				print("!@$#$$%$#^G$#%^$#%&^#$%% hhhhhhhhhhhh -----------------------")
				self.__logger.debug('in action [%s] - reload_template:'%('do_admin'))
				print('do--> reload_templ','load_template',commandD['load_template'])
					
				self.__model_instance.RefreshServerContent('load_templates','',int(commandD['load_template']))
				
		elif 'load_template' in commandD:
			self.__logger.debug('in action [%s] - load_template 4522:'%('do_admin'))
			print('do-->','load_template',commandD['load_template'])
			
			
			self.__model_instance.RefreshServerContent('load_templates','',int(commandD['load_template']))
			
		self.__logger.info('in action [%s] - FINISHED-OK:'%('do_admin'))
		return 1	
		
	def get_track_search_list_for_tag_id(self,commandD):	
		# возвращает список "поискового" типа для выбранного tag_id
		
		self.__logger.debug('in get_track_search_list_for_tag_id: [%s] - Start'%(str(commandD)))
		
		tagId = int(commandD['tag_id'])
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
		dbIdL = getDbIdL_viaTagId(tagId,db)
		#print 'get_tag_tracks dbl_d:',dbIdL
		sD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
			#print sD
			#print sD[sD.keys()[0]].keys()
		db.close()
		search_term = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
		
		
		self.__logger.debug('search_term[%s], len(sD):%s,tagId: [%s]'%(search_term,str(len(sD)),str(tagId)))
		
		self.__model_instance.setSearchBufD(search_term,sD,tagId,'tag_tracks',{})
		self.__logger.debug('in get_track_search_list_for_tag_id: [%s] - Finished'%(str(commandD)))
		return -1	
		
	def get_artist_search_list_for_object_id(self,commandD):	
		# возвращает список "поискового" типа для выбранного tag_id
		
		self.__logger.info('in get_track_search_list_for_tag_id: [%s] '%(str(commandD)))
		
		tagId = int(commandD['tag_id'])
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
		dbIdL = getDbIdL_viaTagId(tagId,db)
		#print 'get_tag_tracks dbl_d:',dbIdL
		sD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
			#print sD
			#print sD[sD.keys()[0]].keys()
		db.close()
		
				
		search_term = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
		
		self.__logger.debug('search_term[%s], len(sD):%s,tagId: [%s]'%(str(search_term),str(len(sD)),str(tagId)))
		self.__model_instance.setSearchBufD(search_term,sD,tagId,'tag_tracks',{})
		return -1		
		
	def check_and_add_missd_song(self,commandD):
		# Недоделанная пока функция автоаматическйо проверк тэга на наличие новой версии песни
		self.__logger.info('check_and_add_missd_song: [%s] '%(str(commandD)))
		paramD['action'] = 'tag_maintain'
		commandD['action_mode'] = 'add'
		tag_id = int(commandD['tag_id'])
		search_term = ''
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		# Получить все трэки этого названия, невзирая на то, что они уже существуют в назначении
		sD =  searchMediaLib_MetaData(dbPath,search_term,['title'],[])
		self.__model_instance.setSearchBufD(search_term,sD,tag_id,tag_form_mode,paramD)

		sD =  searchMediaLib_MetaData(dbPath,search_term,['title'],[])
		# Получить текущие трэки тэга	
		self.__model_instance.setSearch_editable_BufD(sD,tag_id,tag_form_mode,'add')

		if sD_editable != {}:	
			self.__model_instance.setSearchBufD(search_term,sD_cur_tag,tagId,'tag_tracks',{})
			self.__model_instance.setSearch_editable_BufD(sD_editable,tagId,commandD['action_mode'])	
			
			
	def get_artist_search_list_for_tag_id(self,commandD):	
		# возвращает список "поискового" типа для выбранного tag_id
		
		self.__logger.info('in get_artist_search_list_for_tag_id: [%s] '%(str(commandD)))
		
		tagId = commandD['tag_id']
		db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
		#заменить эту функцию на новую для артиста
		dbIdL = getDbIdL_viaTagId(tagId,db)
		#print 'get_tag_tracks dbl_d:',dbIdL
		# тут брать из RepBuffer
		sD = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
			#print sD
			#print sD[sD.keys()[0]].keys()
		db.close()
		
				
		#search_term = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
		
		#self.__logger.debug('search_term[%s], len(sD):%s,tagId: [%s]'%(str(search_term),str(len(sD)),str(tagId)))
		#self.__model_instance.setSearchBufD(search_term,sD,tagId,'tag_tracks',{})
		return -1		

	def artist_tag_assign_update_check(self,commandD):	
		# проверяет список "поискового" типа для выбранного tag_id на предмет изменения тэгоназначения
		
		# Для представления надо подготовить следующие параметры 'change_list':'','change_action':''
		# 'change_list':'' - список измененных позиций. 'change_action' - удалить или добавить
		# вью должен возвратить новый лист с подкрашееными позициями. промежуточно должнен быть сохранет список, по нему после нажатия save будет сделан реальный
		# апдейт
		
		# тут же делать проверку целостности. если действие добавить то список не должен пересекаться с существующим. если удалить, то элементы должны быть в 
		# тэгоназначении
			
		self.__logger.info('in artist_tag_assign_update_check: [%s] '%(str(commandD)))
		#self.__logger.debug('selL = %s '%(str(commandD['selL'])))
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		artistL = []
		albumL = []
		if 'artistDataD' in commandD:
			#print '-->artistDataD:'
			for a in commandD['artistDataD']:
				if not a['checked']:
					continue
				if int(a['key']) not in artistL:	
					artistL.append(int(a['key']))	
				#print a['key'],a['checked']
				#print 'albumL:',
				for b in a['albumL']:
					if b['checked']:
						#print b['key'],b['key']
						if int(b['key']) not in albumL:	
							albumL.append(int(b['key']))	
			
		
		if 'album_NSA_DataD' in commandD:
			#print '-->album_NSA_DataD:'
			for a in commandD['album_NSA_DataD']:
				if not a['checked']:
					continue
				if int(a['key']) not in artistL:	
					albumL.append(int(a['key']))		
					
				#print a['key'],a['checked']
				#print 'artistL:'
				for b in a['artistL']:
					if b['checked']:
						#print b['key'],b['key']
						if int(b['key']) not in albumL:	
							artistL.append(int(b['key']))	
			#artistL = 
		
		
		
		#print 'artistL:',artistL
		sD_editable = {}
		sD_cur_tag = {}
		tagKey = commandD['tag_id']
		
		# временная проверка сохранения в БД
		#if 'ReportBufD' not in self.__modelDic:
		#	self.__modelDic['ReportBufD'] = self.__model_instance.getReportBuf_forArtist()
			
		artist_dbDD={}	
		print('Artist')
		for a in artistL:	
			print(a, end=' ')
			artist_dbDD[a]=getArtistD_fromDB(dbPath,a)[a]
		
		print('Album')	
		album_dbDD={}	
		for a in albumL:	
			album_dbDD[a]=getAlbumD_fromDB(dbPath,None,a,[])['albumD'][a]	
			
		
		self.__modelDic['artist_dbDD']=artist_dbDD
		self.__modelDic['plGroupD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('group2PlayListD','local')['groupD']
		tagD = {}
		tagId = None
		for a in self.__modelDic['plGroupD']:
			if a == tagKey:
				tagId = self.__modelDic['plGroupD'][a]['group_id']
				tagD[tagId]=tagKey
		print(tagD)
		if tagD != {}:	
			if artist_dbDD != {}:	
				print('Cat artist')
				r = artist_album_categorisation_and_save(dbPath,artist_dbDD,tagId,tagD,'general_categ','artist')
			if album_dbDD != {}:	
				print('Cat album')
				r = artist_album_categorisation_and_save(dbPath,album_dbDD,tagId,tagD,'general_categ','album')	
			
		print('Artist assignement saved!')
		return 0
		search_term = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
		self.__model_instance.setSearch_editable_BufD({},None,'')
		
		
		# если 'action_mode' == "delete" то достаточно просто сохранить дельта список ключей, если "add" то надо дополнить поисковый буфер метаданными трэков тэга,
		# на который будут назначаться трэки
		
		if 'action_mode' in commandD and 'selL'  in commandD:
			
			db = sqlite3.connect(dbPath)		
			dbIdL = getDbIdL_viaTagId(tagId,db)
			sD_cur_tag = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
			db.close()
				
			if commandD['action_mode'] == 'add' and len(commandD['selL']) > 0:
				
					
					# список ключей из поискового списка которые выбраны на назначение
				curSelectedKeyL = [a for a in self.__model_instance.getSearchBufD()['sD'] if a in commandD['selL']]
				for a in curSelectedKeyL:
					if a not in sD_cur_tag:
						sD_editable[a] = self.__model_instance.getSearchBufD()['sD'][a]
						
			if commandD['action_mode'] == 'delete':
					
				delKeyL = [a for a in sD_cur_tag if a not in commandD['selL']]
				sD_editable = {}
				
				for a in delKeyL:
					sD_editable[a] = sD_cur_tag[a]
				for a in delKeyL:
					del(sD_cur_tag[a])	
					
				#print "to be deleted:",sD_editable.keys()	
					
			if sD_editable != {}:	
				self.__model_instance.setSearchBufD(search_term,sD_cur_tag,tagId,'tag_tracks',{})
				self.__model_instance.setSearch_editable_BufD(sD_editable,tagId,commandD['action_mode'])
				
		
			# Сохраняем дельта список по которому будет в последствии возможно произведен апдейт
			if sD_editable != {}:
				# тут потом еще сделать проверку на соответствие списка изменений и текущего поискового буфера sD
				# такжедля дельта списка можно хранить таймстемп создания и если на время сохранения прошло допустим больше минуты, то 
				# то отклонять такую транзакцию
				
				cfgD = {'list_type':'edit_hard_tag','action_mode':commandD['action_mode'],'tagId':tagId}
				res = self.__model_instance.set_genKeyL(list(sD_editable.keys()),cfgD)
				return res
		
		return 0	
	def tag_assign_to_categ_check(self,commandD):	
		# проверяет список "поискового" типа для выбранного tag_id на предмет изменения тэгоназначения
		
		# Для представления надо подготовить следующие параметры 'change_list':'','change_action':''
		# 'change_list':'' - список измененных позиций. 'change_action' - удалить или добавить
		# вью должен возвратить новый лист с подкрашееными позициями. промежуточно должнен быть сохранет список, по нему после нажатия save будет сделан реальный
		# апдейт
		
		# тут же делать проверку целостности. если действие добавить то список не должен пересекаться с существующим. если удалить, то элементы должны быть в 
		# тэгоназначении
			
		self.__logger.info('in tag_assign_to_categ_check: [%s] '%(str(commandD)))
		tag_idL = []
		cat_idL = []
		if 'tag_idL' in commandD and 'cat_idL' in commandD :
			tag_idL = commandD['tag_idL']
			cat_idL = commandD['cat_idL']
		for cat_id in cat_idL:
			for tag_id in tag_idL:
				pass
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
		categoryD = getCategoryProfileDic(dbPath)['categoryD']	
		return 0
			
	def tag_assign_update_check(self,commandD):	
		# проверяет список "поискового" типа для выбранного tag_id на предмет изменения тэгоназначения
		
		# Для представления надо подготовить следующие параметры 'change_list':'','change_action':''
		# 'change_list':'' - список измененных позиций. 'change_action' - удалить или добавить
		# вью должен возвратить новый лист с подкрашееными позициями. промежуточно должнен быть сохранет список, по нему после нажатия save будет сделан реальный
		# апдейт
		
		# тут же делать проверку целостности. если действие добавить то список не должен пересекаться с существующим. если удалить, то элементы должны быть в 
		# тэгоназначении
			
		self.__logger.info('in tag_assign_update_check: [%s] '%(str(commandD)))
		sD_editable = {}
		sD_cur_tag = {}
		tagId = int(commandD['tag_id'])
		search_term = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')[tagId]['tag_name']
		self.__model_instance.setSearch_editable_BufD({},None,'')
		crc32L = []
		
		# если 'action_mode' == "delete" то достаточно просто сохранить дельта список ключей, если "add" то надо дополнить поисковый буфер метаданными трэков тэга,
		# на который будут назначаться трэки
		
		if 'action_mode' in commandD and 'selL'  in commandD:
			
			db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
			dbIdL = getDbIdL_viaTagId(tagId,db)
			sD_cur_tag = getCurrentMetaData_fromDB_via_DbIdL(dbIdL,db)
			db.close()
						
			crc32L_str = base64.b64decode(commandD['selL']).decode("utf-8")
			crc32L = [int(a) for a in crc32L_str.split(',')]
				
			if commandD['action_mode'] == 'add' and len(crc32L) > 0:
				
					
					# список ключей из поискового списка которые выбраны на назначение
				curSelectedKeyL = [a for a in self.__model_instance.getSearchBufD()['sD'] if a in crc32L]
				for a in curSelectedKeyL:
					if a not in sD_cur_tag:
						sD_editable[a] = self.__model_instance.getSearchBufD()['sD'][a]
						
			if commandD['action_mode'] == 'delete':
					
				delKeyL = [a for a in sD_cur_tag if a not in crc32L]
				sD_editable = {}
				
				for a in delKeyL:
					sD_editable[a] = sD_cur_tag[a]
				for a in delKeyL:
					del(sD_cur_tag[a])	
					
				#print "to be deleted:",sD_editable.keys()	
					
			if sD_editable != {}:	
				self.__model_instance.setSearchBufD(search_term,sD_cur_tag,tagId,'tag_tracks',{})
				self.__model_instance.setSearch_editable_BufD(sD_editable,tagId,commandD['action_mode'])
				
		
			# Сохраняем дельта список по которому будет в последствии возможно произведен апдейт
			if sD_editable != {}:
				# тут потом еще сделать проверку на соответствие списка изменений и текущего поискового буфера sD
				# такжедля дельта списка можно хранить таймстемп создания и если на время сохранения прошло допустим больше минуты, то 
				# то отклонять такую транзакцию
				
				cfgD = {'list_type':'edit_hard_tag','action_mode':commandD['action_mode'],'tagId':tagId}
				res = self.__model_instance.set_genKeyL(list(sD_editable.keys()),cfgD)
				return res
		
		return 0
		
	def getNavi_Album_Artist_DataSet(self,commandD):	
		self.__logger.info('in getNavi_Album_Artist_DataSet [%s] '%(str(commandD)))
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		categ_id = None
		object = None
		artist_album_DDL_data = {}
		if 'object'	in commandD:
			object = commandD['object']
			if 'cat_id'	in commandD and object == 'genre':
				categ_id = commandD['cat_id']	
				
				# Prepare artist and album DDL (crc32,OBJNAME) for navigation
				artist_index = 1
				even_odd = ''
				self.__modelDic['artist_album_DDL_data'] = getArtistAlbum_indexL_viaCategId(dbPath,categ_id,['artist','album'],'general_categ')
				self.__modelDic['artist_album_DDL_data']['proc'] = commandD['proc']	
				
				
				composL = []
				artL = []
				for item in self.__modelDic['artist_album_DDL_data']['artistL']:
					if item['object_type'] == '1' or item['object_type'] == 'COMPOSITOR':
						item['color'] = "compositor"
						composL.append(item)
					else: 	
						item['color'] = "artist"
						artL.append(item) 
						
				composL.sort(key=operator.itemgetter('value'))
				artL.sort(key=operator.itemgetter('value'))
				self.__modelDic['artist_album_DDL_data']['artistL'] = composL + artL	
				
				for item in self.__modelDic['artist_album_DDL_data']['artistL']:
					#print item
					if ( artist_index % 2 ):
						if item['color'] == "compositor":
							even_odd = 'even-compositor'
						else:	
							even_odd = 'even'
					else:
						if item['color'] == "compositor":
							even_odd = 'odd-compositor'
						else:
							even_odd = 'odd'
					
					item['even_odd'] = even_odd
					#print artist_index
					item['value'] = item['value']
					item['num'] = str(artist_index)
					artist_index+=1
				
					
					
				if 'artist_rel_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_rel_album_DDL_data']
				#print self.__modelDic['artist_album_DDL_data']
			elif 'cat_id'	in commandD and object == 'artist':	
				
				categ_id = int(commandD['cat_id'])
				
				# в данном случае cat_id это артист	
				print('get albums for artist:',categ_id)
				
				self.__logger.debug('in 1. getNavi_Album_Artist_DataSet  cat_id artist [%s] '%(str(categ_id)))
				
				# Получаем всех артистов связанных с этим главным. по идее должны быть только главные
				artistCRC32L = getAll_Related_to_main_Artist_fromDB(dbPath,None,categ_id,'with_parent')
				extendedL = [a[0] for a in artistCRC32L]
				print('extendedL:',artistCRC32L,categ_id)
				
				extendedL.append(categ_id)
				artist_rel_albumD = {}
				for artistcrc32 in extendedL:
					album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,{},[],artistcrc32,None)
					albumD_tmp = album_artist_metaD_db['albumD']
					for a in albumD_tmp:
						if a not in artist_rel_albumD:
							artist_rel_albumD[a] = albumD_tmp[a]
							
				self.__logger.debug('in 2. 4850 getNavi_Album_Artist_DataSet  cat_id artist [%s] artist_rel_albumD [%s] '%(str(categ_id),str(len(artist_rel_albumD))))
				albumL = []
				keyL_sorted = []
				l_mp3 = []
				
				
				for a in artist_rel_albumD:
					try:
						if artist_rel_albumD[a]['format']:
							if 'mp3' in artist_rel_albumD[a]['format'].lower():
								l_mp3.append((artist_rel_albumD[a]['album'],a))
						else:
							print("Virtual Album in (mp3 check) skipped !!! [%s]",artist_rel_albumD[a]['album'],a)
						
					except Exception as e:
						self.__logger.critical('in  4863 Virtual Album skipped !!! [%s] Error %s '%(str(artist_rel_albumD[a]),str(e)))
						
				
				l_mp3.sort()
				
							
				l_losless = []
				for a in artist_rel_albumD:
					try:
						if artist_rel_albumD[a]['format']:
							if 'mp3' not in artist_rel_albumD[a]['format'].lower():
								l_losless.append((artist_rel_albumD[a]['album'],a))
						else:
							print("Virtual Album (lossless check) skipped !!! [%s]",artist_rel_albumD[a]['album'],a)
					except Exception as e:
						self.__logger.critical('in  4887 Virtual Album lossles skipped !!! [%s] Error %s '%(str(artist_rel_albumD[a]),str(e)))
				
				
				l_losless.sort()
				
				for a in artist_rel_albumD:
					if not artist_rel_albumD[a]['format']:
						# Add virtual allbumes at the end
						l_losless.append((artist_rel_albumD[a]['album'],a))
						
								
				# Initially show MP3 than lossless in the list
				keyL_sorted = l_mp3 + l_losless
				keyL_sorted = [a[1] for a in keyL_sorted]
				
				self.__logger.debug('in 3. 4862 getNavi_Album_Artist_DataSet  cat_id artist [%s] '%(str(categ_id)))
				for a in keyL_sorted:
					format = artist_rel_albumD[a]['format']
					if format:
						if 'mp3' in format.lower():
							color = "mp3_color"
						else:
							color = 'losless_color' 
					else:
						color = 'losless_color' 
					albumL.append({'key':a,'album':artist_rel_albumD[a]['album'],
									'format':format,'color':color,
									'album_type':artist_rel_albumD[a]['album_type']})
					
				self.__logger.debug('in 4. 4873 getNavi_Album_Artist_DataSet  cat_id artist [%s] '%(str(categ_id)))	
					
				self.__modelDic['artist_rel_album_DDL_data'] = albumL
				self.__modelDic['artist_rel_albumD'] = artist_rel_albumD
				if 'artist_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_album_DDL_data']
					
				if 'album_rel_artist_DDL_data' in self.__modelDic:
					del self.__modelDic['album_rel_artist_DDL_data']	
				
				print("got artist ready navi OK")	
				
			elif 'cat_id'	in commandD and object == 'album':	
				categ_id = commandD['cat_id']	
				print('get artists for album:',categ_id)
				album_artist_metaD_db = getArtist_Album_metaD_fromDB(dbPath,{},[],None,categ_id)
				#album_rel_artistD = album_artist_metaD_db['artistD']
				artistL = []
				
				for a in album_artist_metaD_db['artistD']:
					artistL.append({'key':a,'value':album_artist_metaD_db['artistD'][a]['artist']})
					
				self.__modelDic['album_rel_artist_DDL_data'] = artistL
				
				if 'artist_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_album_DDL_data']
				if 'artist_rel_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_rel_album_DDL_data']	
					
				print("got album ready navi OK")	
						
			elif 'cat_id'	in commandD and ((object == 'SERIA') or (object == 'BOX') or (object == 'DBL_DISC')):	
				object_crc32 = commandD['cat_id']	
				print('-----------------get albumes for seria:',object_crc32)
				
					
				
				album_rel_Dic = getAlbum_relation_metaD(dbPath,None,object_crc32,'from','get_neibor')
			
				print(album_rel_Dic)	
				artist_album_relLD = []
				artist_relLD = []
				album_relLD = []
				
				album_from_relLD  = []
				rel_albumD = {}
				
				
				
				tmpL = []
				for item in album_rel_Dic['albums_from_relLD']:
					rel_albumD=getAlbumD_fromDB(dbPath,None,item['key'],[],'wo_reflist')['albumD'][item['key']]
					print(list(rel_albumD.keys()))
					format = rel_albumD['format_type']
					color = 'losless_color' 
					if format != None:
						if 'mp3' in format.lower():
							color = "mp3_color"
						else:
							color = 'losless_color' 
					tmpL.append({'key':item['key'],'value':rel_albumD['album'],'format':format,'color':color,'album_type':rel_albumD['album_type']})
					
					
				
				
				print("gogogog 4976")

			#tmpL.sort()
			#pos = 1
			#for item in tmpL:
		#		if (pos % 2):
		#			even_odd = 'even'
		#		else:
		#			even_odd = 'odd'
		#		item[1]['colorcl']	= even_odd
		#		album_from_relLD.append(item[1])
		#		pos+=1		
		
		
			
				
				if 'artist_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_album_DDL_data']
				if 'artist_rel_album_DDL_data' in self.__modelDic:
					del self.__modelDic['artist_rel_album_DDL_data']	
					
				self.__modelDic['artist_album_DDL_data'] = {'albumL':[]}	
				self.__modelDic['artist_album_DDL_data']['albumL'] = tmpL
					
					
				print("got album ready navi OK")		
				
		
		return
		
		
	def get_lib_navi_graf_data(self,commandD):
		self.__logger.info('in get_lib_navi_graf_data [%s], modelDic[%s]'%(str(commandD),str(self.__modelDic)))
		#self.__modelDic = {}
		remote_host_ip_addr = None
		try:
			remote_host = self.__modelDic['REMOTE_ADDR']
			mpd_instance = self.__model_instance.getCurPlayerInstance(remote_host)
			print('mpd_instance:',mpd_instance)
			#remote_host_name = self.__model_instance.getRemHPlayerInstanceD()['remote_host_name']	
			remote_host_ip_addr = mpd_instance['host']
		except Exception as e:
			self.__logger.critical('Exception in get_lib_navi_graf_data for [RemHPlayerInstanceD] in get_modelDic:%s'%e)
			self.__modelDic['RemHPlayerInstanceD'] = {}	
				
				
		try:
			if 'mpd_instanceDL' not in self.__modelDic:
				self.__modelDic['mpd_instanceDL'] = []
			
				cfgD = self.__model_instance.MediaLibPlayProcessDic_viaKey('configDict','local')
				mpdDL = cfgD['mpd_host_list']
				for item in mpdDL:
					if remote_host_ip_addr:
						if item['host'] == remote_host_ip_addr:
							self.__modelDic['mpd_instanceDL'].append({'key':item['host'],'instance_name':item['host'],'socket':item['socket'],'selected':'X'})
						else:
							self.__modelDic['mpd_instanceDL'].append({'key':item['host'],'instance_name':item['host'],'socket':item['socket'],'selected':''})
					else:		
						self.__modelDic['mpd_instanceDL'].append({'key':item['host'],'instance_name':item['host'],'socket':item['socket']})
			else:
				for item in self.__modelDic['mpd_instanceDL']:
					if remote_host_ip_addr:
						if item['key'] == remote_host_ip_addr:
							item['selected']='X'
						else:
							item['selected']=''

						
				
				
		except Exception as e:
			self.__logger.critical('Excepption in admin_page_elements for [radio stations] in get_modelDic:%s'%e)
			self.__modelDic['mpd_instanceDL'] = []
			
		return
	def get_tag_graf_data(self,commandD):
		self.__logger.info('in get_tag_graf_data: [%s] '%(str(commandD)))
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		tag_filter = ''
		if 'graf_param_mode' in commandD:
			self.__modelDic['graf_params'] = {'tag':commandD['graf_param_mode']}
			tag_filter = self.__modelDic['graf_params']['tag']
			
			self.__modelDic['TagD'] = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')
		
			tagL = []
			for a in self.__modelDic['TagD']:
				if self.__modelDic['TagD'][a]['tag_type'] == tag_filter:	
					tagL.append(a)
			
			db = sqlite3.connect(self.__model_instance.getMediaLibPlayProcessContext()['dbPath'])		
			dbIdL = []
			tag2trackD = {}
			tag2artistD = {}
			for a in tagL:
				tag2trackD[a] = getDbIdL_viaTagId(a,db)
				dbIdL = dbIdL + tag2trackD[a]
			
			l = []
			
			
			for a in dbIdL:
				if a not in l:
					l.append(a)
	
			
		#print 'get_tag_tracks dbl_d:',dbIdL
			sD = getCurrentMetaData_fromDB_via_DbIdL(l,db)
			
			self.__modelDic['metaD'] = {}
			
			
			for a in sD:
				self.__modelDic['metaD'][sD[a]['id_track']]=sD[a]
			
			
			
			artist_mainL = getAll_Main_Artist_fromDB(db)
			artist_mainL = [a[0] for a in artist_mainL]
			#print artist_mainL
			artist_AllL = getAll_Main_Artist_fromDB(db,'all')
			
			db.close()
			
			artist_AllL = [a[0] for a in artist_AllL]
			artist_not_mainL =[a for a in artist_AllL if a not in artist_mainL]
			#print 'comrare len:',len(artist_AllL),len(artist_mainL),len(artist_not_mainL)
			unreg_artistD = {}
			self.__modelDic['artistD'] = getArtistD_fromDB(dbPath,None,[])
			
			#for a in self.__modelDic['artistD']:
			#	print self.__modelDic['artistD'][a]
			
			for a in tag2trackD:
				#print 'Now at tag:',a,self.__modelDic['TagD'][a]['tag_name'],len(tag2trackD[a])
				tag2artistD[a]=[]
				
				for b in tag2trackD[a]:
					if b in self.__modelDic['metaD']:
						artist_key = self.__modelDic['metaD'][b]['artist_crc32']
					else:
						print('Dead tag assognement to:',b)
						continue
					try:
						
						# проверяем на регистрацию в базе артистов
						if artist_key not in self.__modelDic['artistD']:
							if artist_key not in tag2artistD[a]:
								tag2artistD[a].append(artist_key)
								unreg_artistD[artist_key] = self.__modelDic['metaD'][b]['artist']
								
								continue 
						#print 'check',b	,artist_key
						# Далее идет обработка только для зарегистрированных артистов		
						if artist_key in artist_mainL:
							#print 'main found!!!!!---------',artist_key
							if artist_key not in tag2artistD[a]:
								tag2artistD[a].append(artist_key)
						elif artist_key in artist_not_mainL:
							#print 'not main found!!!!!---------',artist_key
							# получить референтный главный индекс артиста
							if self.__modelDic['artistD'][artist_key]['ref_artist_crc32L'] != []:
								try:
									main_ref_key = self.__modelDic['artistD'][artist_key]['ref_artist_crc32L'][0]	
								except:
									main_ref_key = artist_key
								if main_ref_key not in tag2artistD[a]:
									tag2artistD[a].append(main_ref_key)
						
						#print 'Ok b=',b	,self.__modelDic['metaD'][b]
						#break
					except:
						print('Tag without ussignement-->tag=%s b=%s'%(str(self.__modelDic['TagD'][a]['tag_name']),str(b)))
						#print self.__modelDic['metaD'][b]
			
			self.__modelDic['tag2artistD'] = tag2artistD
			self.__modelDic['unreg_artistD'] = unreg_artistD
			
			
			#for a in self.__modelDic['metaD']:
			#	print a,self.__modelDic['metaD'][a]
			#	break
			
			
			self.__logger.debug("buffer tag2artistD check")
			for a in tag2artistD:
				self.__logger.debug('tag_key %s len_artlist= %s'%(str(a),str(len(tag2artistD[a]))))
				#print self.__modelDic['TagD'][a]['tag_name']
			#print sD
			#print sD[sD.keys()[0]].keys()
			
		
		#for a in self.__modelDic['artistD']:
		#	if self.__modelDic['artistD'][a]['main'] == '':
		#		print a,self.__modelDic['artistD'][a]
			
		return	
		
	def create_new_tag(self,commandD):
		
		self.__logger.info('in create_new_tag control: [%s] '%(str(commandD)))
		
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath'] 
		newTagName = commandD['tag_name_field']
		TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')	
		TagDescr = ''
		TagDescr = commandD['tag_descr_field']
		TagType = commandD['tag_type']
		print(newTagName,TagType)
					
		res =createNewTag_inDB(dbPath,newTagName,TagDescr,TagType)
		print('creatTagRes=',res)
		if res != -1:
			TagD[res] = {}
			try:
				TagD[res]['tag_name'] = newTagName.decode('utf-8').lower()
				TagD[res]['tag_decr'] = TagDescr.decode('utf-8')
			except:
				
				TagD[res]['tag_name'] = newTagName.lower()
				TagD[res]['tag_decr'] = TagDescr
			TagD[res]['tag_type'] = TagType
		return res	
		
	def delete_empty_tag(self,commandD):	
		print('in delete_tag control',commandD)
		tagId = int(commandD['tag_id'])
		TagD = self.__model_instance.MediaLibPlayProcessDic_viaKey('TagD','local')	
		dbPath = self.__model_instance.getMediaLibPlayProcessContext()['dbPath']
		db = sqlite3.connect(dbPath)		
		dbIdL = getDbIdL_viaTagId(tagId,db)
		db.close()
		
		if dbIdL == []:
			print('will be deleted:',TagD[tagId],len(dbIdL),dbIdL)
			res = delete_Empty_Tag_inDB(dbPath,tagId)
			if res != 0:
				del(TagD[tagId])
			else:
				print("Cann not delete tag from DB!!!!",tagId)
				return 0
		else:
			print("delete assignement first!!!!",len(dbIdL))
			return 0
		print('res=',res)
		return tagId	

def loggerWrapper(descr,value):
	return 'descr%s'%(str(value))		
	
class MediaLib_Application_RPC_server():

	def __init__(self):
		self.__MediaLib_Controller_instance = MediaLib_Controller()
		#print dir(self.__MediaLib_Controller_instance)
		# тут также напрямюу вызываем родительский конструктор, чтобы иметь возможность доступа к функциям старой и новой реализации.
		# затем сервер стартовать в отдельном модуле используя инстанцию контроллера как внешний объект
		
	def get_controller_instance(self):
		return self.__MediaLib_Controller_instance
	
	def runApplServer(self):
	
		
		#print dir(self.__MediaLib_Controller_instance.get_instance())
		port = int(self.__MediaLib_Controller_instance.get_instance().MediaLibPlayProcessDic_viaKey('appl_cntrl_port','local'))
		
		dbl_appl = xmlrpc.client.ServerProxy('http://%s:%s'%(str(socket.gethostname()),str(port)))	
		try:
			res = dbl_appl.appl_status()['dbPath']
			print("Application server already running -> no copy allowed")
			print("Wait 5 sec for exit...[%s]"%(str(res)))
			time.sleep(5)

			return
		except:
			pass
		
		#print self.__MediaLib_Controller_instance.MediaLibPlayProcessDic()
		print('Appla port',port)
		server = SimpleXMLRPCServer((str(socket.gethostname()), port),allow_none = True)
		
		print("Listening on port %s..."%(str(port)))
		self.__logger = logging.getLogger('controller_logger.rfc')
		self.__logger.info('avalable transit methods for player:%s'%(str(self.__MediaLib_Controller_instance.get_instance().MediaLibPlayProcessDic_viaKey('Player_RPC_methods','local'))))
		
		
		server.register_introspection_functions()
		# фукнции старого контроллера в модели (для совместимости) от них надо избавиться и все перенести в новый контроллер
		server.register_function(self.__MediaLib_Controller_instance.get_instance().getMediaLibPlayProcessContext, "appl_status")
		server.register_function(self.__MediaLib_Controller_instance.get_instance().MediaLibPlayProcessDic_viaKey,"processDic_viaKey")
		
		server.register_function(self.__MediaLib_Controller_instance.get_instance().getSearchBufD,"getSearchBufD")
		
		
#		server.register_function(self.__MediaLib_Controller_instance.get_instance().PageGenerator,'page_generator')
		server.register_function(self.__MediaLib_Controller_instance.get_instance().RefreshServerContent,'refresh_content')
		server.register_function(self.__MediaLib_Controller_instance.get_instance().Appl_Controller,'appl_control')
		server.register_function(self.__MediaLib_Controller_instance.get_instance().getCoverPageObj,'get_image')
		server.register_function(self.__MediaLib_Controller_instance.get_instance().get_All_metaD,'get_All_metaD')
		
		
		# фукнция нового контроллера
		server.register_function(self.__MediaLib_Controller_instance.command_dispatcher,'command_dispatcher')
		server.register_function(self.__MediaLib_Controller_instance.get_audio,'get_audio')
		
		server.register_function(self.__MediaLib_Controller_instance.get_instance().getConrolPicD,'get_control_pics')
		server.register_function(self.__MediaLib_Controller_instance.get_instance().debug_get_controllist_for_main,'debug_get_controllist_for_main')
		
		
		
		server.serve_forever()	
