# # -*- coding: cp1251 -*-
#-*- coding: utf-8 -*-
#import  wx

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import socket
import json
import pickle
import logging
import operator
import os
import chardet
from string import Template

import myMediaLib_model
#from myMediaLib_adm import searchMediaLib_MetaData
#from myMediaLib_adm import get_all_artists_in_metaD
#from myMediaLib_adm import getArtistD_fromDB
#from myMediaLib_adm import getAll_Main_Artist_fromDB
#from myMediaLib_adm import getAll_Related_to_main_Artist_fromDB
from myMediaLib_adm import split_2_fix_lines

from myMediaLib_model import MediaLibPlayProcess_singletone_Wrapper
from myMediaLib_model import str2_RusLine

# forward':{'model_update_method':'forward','view_method':'ajax_main_page_update','view_elem_id_Dic':{'refresh_time':0}},
#'revind':{'model_update_method':'forward',	'view_method':'ajax_main_page_update','view_elem_id_Dic':{'refresh_time':0}},	
#'play':{'model_update_method':'play', 'view_method':'ajax_main_page_update', 'view_elem_id_Dic':{'play_status':''}},
#'stop':{'model_update_method':'stop', 'view_method':'ajax_main_page_update','view_elem_id_Dic':{'play_status':''}},
#'pause':{'model_update_method':'pause','view_method':'ajax_main_page_update','view_elem_id_Dic':{'play_status':''}},

main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = image_sel = track_preload_sel = ''  
menu_selD = {'host_name':'','main_sel':'','search_sel':'','image_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':'','track_preload_sel':''}
#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
html_title = 'Удаленная смотрелка-управлялка играющей музыки'


logger = logging.getLogger('controller_logger.View')
class MediaLib_ViewGen(MediaLibPlayProcess_singletone_Wrapper):
	def __init__(self):
	
		# вызываем явно конструктор родителя, чтобы в этом классе иметь доступ к атрибутам родителя
		# таким образом инстанция контролера является одновременно инстанцией модели, зачем это???? 
		# это сделано на начальном этапе чтобы минимально изменять старый код, когда в модели был реализовани контроллер 
		# напрямую. в будущем сделать в модели методы, которые выдавали бы соответсвущие объекты модели 
		#super(MediaLib_Controller, self).__init__()
		MediaLibPlayProcess_singletone_Wrapper.__init__(self)
		
		logger.info('View logger check Ok')
		#print self.get_instance().getMediaLibPlayProcess_State()
		
	def ajax_gen_action_confirmed(self,res,view_elem_id_Dic,dummy_2,modelDic):	
		
		logger.info(' we are in ajax_gen_action_confirmed:%s res=%s'%(str(view_elem_id_Dic),str(res)))
		json_reply = {}
		if 'action_name' in view_elem_id_Dic:
			view_elem_id_Dic['action_result'] = res
			
			json_reply = json.dumps(view_elem_id_Dic)
			print('ajax_gen_action_confirmed = OK')
		return json_reply
		
	def do_nothing(self,dummy_0,dummy_1,dummy_2,dummy_3):
	
		logger.info("Do nothing veiw result")
		return 0	
		
	def	ajax_tag_admin_page_update(self,res,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('we are in ajax_tag_admin_page_update %s res=%s:'%(str(view_elem_id_Dic),str(res)))
		json_reply = {}
		if 'action_name' in view_elem_id_Dic:
			if res > 0:
				view_elem_id_Dic['action_result'] = 1
				
				if view_elem_id_Dic['action_name'] == 'create_new_tag':
					view_elem_id_Dic['tag_id'] = res
					view_elem_id_Dic['tag_name'] = modelDic['tag_name']
				elif view_elem_id_Dic['action_name'] == 'delete_empty_tag':
					view_elem_id_Dic['tag_id'] = res
			else:
				view_elem_id_Dic['action_result'] = 0
			json_reply = json.dumps(view_elem_id_Dic)
			
		elif 'tag_init_data' in view_elem_id_Dic:
			view_elem_id_Dic['action_result'] = 1
			view_elem_id_Dic['tag_data'] = {}
			
			tagD =  modelDic['TagD']
			tagCatD = {'ALL_GRP':[]}
			tagCatLD = []
			catL = []
			for a in tagD:
				if tagD[a]['tag_type'] not in tagCatD:
					item = tagD[a]
					item['key'] = a
					tagCatD[tagD[a]['tag_type']]=[item]
					
				else:
					item = tagD[a]
					item['key'] = a
					tagCatD[tagD[a]['tag_type']].append(item)
					
				tagCatD['ALL_GRP'].append(item)	
					
			
			for a in tagCatD:
				tagCatLD.append({'cat_name':a, 'tagL':tagCatD[a]})
				catL.append(a)
				tagCatD[a].sort(key=operator.itemgetter('tag_name'),reverse=False)
					
			catL.sort()
			tagL = []
			try:
				tagL=[(tagD[a]['tag_name'],a) for a in tagD if 'tag_name' in tagD[a]]
				tagL.sort() 
				
				tagL = [a[1] for a in tagL]
			except:
				tagL = []
				print('Error in tagL rendering of send_HtmlPage_tagAdmin_new')
				
				
			TagResL = []
			
			#print 	'tagAdmin geneta 3'	
			
			form_mode =  ''
			
			js_tag_group_list = ''
			# получаем все группы тэгов
			tagGroupL = []
			for a in tagL:
				if tagD[a]['tag_type'] not in tagGroupL:
					if 'tag_type' in tagD[a]:
						tagGroupL.append(tagD[a]['tag_type'])
			
			for a in tagL:
				try:
					opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a,'selected':'','text':tagD[a]['tag_name']})
					#print tagD[a]['tag_name']
				except:
					print("""Erorr in tagD[a]['tag_name'] index:""",a)	
					continue
				
				#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
				TagResL.append(opt_elem)
			tag_list_content = '\n'.join(TagResL)
			
			for a in tagGroupL:

				sel_option_js_contentL = []
				for b in tagL:
					try:
						if tagD[b]['tag_type'] == a:
							sel_option_js_contentL.append({'tag_name':tagD[b]['tag_name'],'group':b})
						else:
							continue
					except:
						print("""Erorr in tagD[b]['tag_name'] index:""",b)	
						continue
			print('html_title-1')
			
			
			if 'style_claster_groupL' in view_elem_id_Dic:
			
				if 	'cat_profD' in 	modelDic:	
					view_elem_id_Dic['style_claster_groupL'] = modelDic['cat_profD']

		
			
			
			view_elem_id_Dic['tag_data'] = tag_list_content
			view_elem_id_Dic['tagCatLD'] = tagCatD
			view_elem_id_Dic['catL'] = catL	
			view_elem_id_Dic['tag_group'] = sel_option_js_contentL
			view_elem_id_Dic['html_title'] = html_title
			
			
			json_reply = json.dumps(view_elem_id_Dic)
		
		logger.debug('ajax_tag_admin_page_update: Finished!')
		
		return json_reply
		
	def	ajax_tracks_preload_page_update(self,res,view_elem_id_Dic,dummy_2,modelDic):
		logger.info('at are in ajax_tracks_preload_page_update %s res=%s:'%(str(view_elem_id_Dic),str(res)))
		json_reply = {}
		
		view_elem_id_Dic['action_result'] = 0
		json_reply = json.dumps(modelDic['tracks_preload_proc_buf_db'])
		print(3)	
		logger.debug('ajax_tracks_preload_page_update - Finished')
		return json_reply
		
	def	ajax_artist_search_like_page_update(self,res,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('And now!!! we are in ajax_artist_search_like_page_update %s res=%s:'%(str(view_elem_id_Dic),str(res)))
		data_reply  = {}
		json_reply = {}
		
		if 'artist_search_buf_data' in view_elem_id_Dic or 'artist_search_buf_data_db' in view_elem_id_Dic or 'artist_album_categ_buf_data' in view_elem_id_Dic:
			for buf_key in ['artist_view','album_NSA_view']:
				logger.debug('in ajax_artist_search_like_page_update check:%s'%buf_key)
				#print buf_key
				if buf_key in modelDic['artist_album_maintain_proc_buf']:
					if 'proc_state' in modelDic['artist_album_maintain_proc_buf'][buf_key]:
						proc_state = modelDic['artist_album_maintain_proc_buf'][buf_key]['proc_state']
						proc_type = modelDic['artist_album_maintain_proc_buf']['proc_type']
						
						active_view = modelDic['artist_album_maintain_proc_buf']['active_view']
						#print modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD'][proc_state]
						#print 'ok',buf_key,proc_state
						data_reply[buf_key] = {'dataD':json.dumps(modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD'][proc_state]),
												'proc_state':proc_state,
												'validity_key':modelDic['artist_album_maintain_proc_buf'][buf_key]['validity_key'],
												'cur_page':modelDic['artist_album_maintain_proc_buf'][buf_key]['cur_page'],
												
												}
						# Ресетим переключатель представления						
									
			logger.debug('in ajax_artist_search_like_page_update check:1')								
			data_reply['active_view']=active_view
			data_reply['proc_type']=proc_type
			json_reply = json.dumps(data_reply)
			modelDic['artist_album_maintain_proc_buf']['active_view'] = ''
			logger.debug('in ajax_artist_search_like_page_update check:1+')	

		if 'get_albumes_cmpl_clast'	 in view_elem_id_Dic:	
			
			data_reply['albumes_cmpl_clast_view'] = {'dataD':json.dumps(modelDic['albumes_cmpl_maintain_buf']).encode('base64')}
			data_reply['proc_type']='albumes_cmpl'
			json_reply = json.dumps(data_reply)
			del modelDic['albumes_cmpl_maintain_buf'] 
			
		
		if 'maintain_album_component'	 in view_elem_id_Dic:	
			
			data_reply['maintain_album_component'] = modelDic['maintain_album_component']
			data_reply['proc_type']='albumes_cmpl'
			json_reply = json.dumps(data_reply)
			del modelDic['maintain_album_component'] 
			
			
		if 'artist_search_res_buf' in view_elem_id_Dic:
			search_res_list = ''
			search_part_tmpl = ''
			art_stat_D = modelDic['ReportBufD']
			
			#print 'search_res_list-1 ',	art_stat_D.keys()
			
						
			
			search_res_list  = search_res_list + prepareArtistOveralReport(art_stat_D['statL'],art_stat_D['artistD'],art_stat_D['ref_artL'],modelDic)
			
			album_cnt = 0
			albumL = []
			for a in art_stat_D['statL']:
				if 'albumD' in art_stat_D['artistD'][a[3]]:
					#print a[3],art_stat_D['artistD'][a[3]]['albumD'].keys()
					for b in art_stat_D['artistD'][a[3]]['albumD']:
						if b not in albumL:
							albumL.append(art_stat_D['artistD'][a[3]]['albumD'][b]['album'])	
			album_cnt = len(albumL)			
			del(albumL)
			logger.debug("Album num:%d"%album_cnt)
			
			
			#print 'template =',modelDic['Tmpl']['report_part_tmpl']['TMPL']
			#print modelDic['Tmpl']['report_part_tmpl'].keys(),'search_part_tmpl',search_part_tmpl,'len(art_stat_D[])=',len(art_stat_D['artistD'])
			try:
				notFoundL = [a for a in art_stat_D['search_termL'] if a not in art_stat_D['foundL']]
				stat_str = str(len(notFoundL))+'/'+str(len(art_stat_D['search_termL']))
			except Exception as e:
				print('Error in ajax_artist_search_like_page_update:',list(art_stat_D.keys()))
				logger.critical('Exception in ajax_artist_search_like_page_update:%s -->%s'%(e,str(list(art_stat_D.keys()))))
				notFoundL = stat_str = ''
				
			
			# Вызываем шаблонизатор	
			variableD =	{'res_lenth':len(art_stat_D['artistD']),'album_num':album_cnt,'info_str':'not found %s:'%(stat_str)+str(notFoundL),
																											'search_res_list':search_res_list}
			search_part_tmpl = template_process(modelDic,'report_part_tmpl',variableD)
			
			view_elem_id_Dic['search_result_frm'] = search_part_tmpl.encode('base64')
			
			
			try:
				# так как перед вызовом метода представления идет динамический вызов метода контроллра, который возвращает значение,
				# то в res = этому возвращаемому значению_ это неявное присваивание, в дальнейшем продумать как это делать явно
				# возможно стоит это делать через modelDic
				view_elem_id_Dic['action_key'] = res
				json_reply = json.dumps(view_elem_id_Dic)
				
			except:
				try:
					view_elem_id_Dic['search_result_frm'] = view_elem_id_Dic['search_result_frm'].decode('cp1251')
					json_reply = json.dumps(view_elem_id_Dic)
				except:
					d = pickle.dumps(view_elem_id_Dic)
					f = open('c:\debug.dat','w')
					f.write(d)
					f.close()
					print("http_Reply--> Error",len(search_part_tmpl))
					view_elem_id_Dic['search_result_frm'] ='error'
					json_reply = json.dumps(view_elem_id_Dic)
		print() 
		logger.debug('artist search_res_list-4 ready')
		return json_reply
		
	def	ajax_artist_update(self,res,view_elem_id_Dic,dummy_2,modelDic):
		logger.info('in ajax_artist_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))	
		json_reply = {}	
		folderD_list = []
		cat_profD = []
		folder_filter_key = ''
		selected_index = -1
		keyL = ['color_set','descr','ref_folderL']
		
		if 	'cat_profD' in 	modelDic:	
			cat_profD = modelDic['cat_profD']
		
		if 'plGroupD' in modelDic:
		
			folder_filter_key = ''
			selected_index = -1
			if 'folder_filter_key' in modelDic:
				folder_filter_key = modelDic['folder_filter_key']
		
		
			logger.debug('plGroupD is OK')
			plGroupD = modelDic['plGroupD']
			plGroupL = [(plGroupD[a]['num'],a) for a in plGroupD]
			plGroupL.sort()
			
			plGroupL = [a[1] for a in plGroupL]
			
			for key in plGroupL:
				itemD = {}
				for a in plGroupD[key]:
					if a not in keyL:
						continue
					if a == 'descr':
						try:
							node_name=plGroupD[key]['descr']
						except Exception as e:
							logger.critical(""""Exception during the dd 1 template plGroupD[key]['descr']:%s"""%(str(e)))
							print("""Erorr at plGroupD[key]['descr']""", a)
							continue
							node_name = str(key)
							
						
						itemD[a] = node_name
						
					elif a == 'color_set':
						try:				
							colorD = json.loads(plGroupD[key]['color_set'])
							itemD['bk_color'] = str(colorD['background-color'])	
							itemD['color'] = str(colorD['color'])	
						except Exception as e:
							print("Error at group color set:%s"%str(key),e)
							itemD['bk_color'] = "White"	
							itemD['color'] = "Black"	
					else:	
						itemD[a] = plGroupD[key][a]
				itemD['key'] = key	
				if key == folder_filter_key:
					itemD['selected'] = True
					selected_index = plGroupL.index(key)
				else:
					itemD['selected'] = False
				folderD_list.append(itemD)
				logger.debug('Check plGroupL:%s'%(str(a)))
				
				#del modelDic['plGroupD']
				
		if 'maintain_single_artist_album' in view_elem_id_Dic:
			json_reply = {'maintain_single_artist_album':modelDic['maintain_single_artist_album_res']}
			
			del modelDic['maintain_single_artist_album_res']
			
		if 'maintain_object_attrs' in view_elem_id_Dic:
			json_reply = {'maintain_object_attrs':modelDic['maintain_object_attrs_res']}
			
			del modelDic['maintain_object_attrs_res']	
				
				
		if 'get_object_edit_data' in view_elem_id_Dic:
			
			if 'edit_object_struc' in modelDic:
				try:
					json_reply = {'object_edit_data':modelDic['edit_object_struc']}
					#'dataD':json.dumps(modelDic['artist_album_maintain_proc_buf'][buf_key]['dataD'][proc_state]).encode('base64')
					#print json_reply
				except Exception as e:
					logger.critical('Exception in ajax_artist_update:%s -->%s'%(e,str('')))	
				
		
		
		
		if 'folder_data' in view_elem_id_Dic:
			
			if 	'cat_profD' in 	modelDic:	
				cat_profD_data = json.dumps(cat_profD)	
				
			
			try:	
				json_reply = {'folder_data':json.dumps(folderD_list),'category_data':cat_profD_data,'folder_filter_keyD':{'folder_filter_key':folder_filter_key,'selected_index':selected_index}}
			except Exception as e:
				logger.critical('Exception in ajax_artist_update:%s -->%s'%(e,str('')))
		
		#print "ajax_artist_update before return is OK",json_reply	
		return json.dumps(json_reply)
		
		
	def ajax_nav_cat_data_update(self,res,view_elem_id_Dic,dummy_2,modelDic):	
		logger.info('in ajax_nav_cat_data_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))
		navi_cat_data = {}	
		
		if 'artist_album_DDL_data' in modelDic:
			
			logger.debug('at 308 artist_album_DDL_data:%s -->'%(str(modelDic['artist_album_DDL_data'])))
			if 'proc' not in modelDic['artist_album_DDL_data']:
				navi_cat_data['proc'] = "navi"
			else:	
				navi_cat_data['proc'] = modelDic['artist_album_DDL_data']['proc']
			if 'artistL' in modelDic['artist_album_DDL_data']:
				navi_cat_data['artistL'] = modelDic['artist_album_DDL_data']['artistL']
			if 'albumL' in modelDic['artist_album_DDL_data']:
				navi_cat_data['albumL'] = modelDic['artist_album_DDL_data']['albumL']
			if 'tag_DDL_data' in modelDic:	
				navi_cat_data['tagL'] = modelDic['tag_DDL_data']['tagL']
			logger.debug('chek point 5')
			try:	
				json_reply = {'navi_cat_data_general':json.dumps(navi_cat_data)}
			except:
				print("error at json reply:",navi_cat_data)
		elif 'artist_rel_album_DDL_data' in modelDic:		
			
			logger.debug('319 at artist_album_DDL_data:%s -->'%(str(modelDic['artist_rel_album_DDL_data'])))
			navi_cat_data = {}	
			navi_cat_data['albumL'] = modelDic['artist_rel_album_DDL_data']
			try:	
				json_reply = {'navi_cat_data_artist':json.dumps(navi_cat_data)}
			except:
				print("error at json reply:",navi_cat_data)
		elif 'album_rel_artist_DDL_data' in modelDic:		
			
			logger.debug('327 at artist_album_DDL_data:%s -->'%(str(modelDic['album_rel_artist_DDL_data'])))
			navi_cat_data = {}	
			navi_cat_data['artistL'] = modelDic['album_rel_artist_DDL_data']
			try:	
				json_reply = {'navi_cat_data_album':json.dumps(navi_cat_data)}
			except:
				print("error at json reply:",navi_cat_data)		
				
				
			
		logger.debug('At point 3')
		#print 'graf data-4 ready',	json_reply
		return json.dumps(json_reply)		

		
	def	ajax_player_prc_update(self,PlayControl_CurStatusD,view_elem_id_Dic,dummy_2,modelDic):	
		logger.info('in ajax_player_prc_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(PlayControl_CurStatusD),str(list(modelDic.keys()))))
		json_reply = {'player_process_info':{}}	
		
		#print 0
		PlayControl_CurStatusD['album_CRC32'] = modelDic['metaD_of_cur_pL'][PlayControl_CurStatusD['track_CRC32']]['album_crc32']
		if 'list_type_flat'	 in modelDic:
			PlayControl_CurStatusD['list_type_flat'] = modelDic['list_type_flat']
			
		cur_album_pos = 0
		cur_track_in_album_pos = 0
		#print 1
		
		if 'cur_track_in_album_pos' in modelDic:
			
			try:
				
				print('OK cur_track_in_album_pos----->:',modelDic['cur_track_in_album_pos'])
				cur_track_in_album_pos = modelDic['cur_track_in_album_pos']
				PlayControl_CurStatusD['cur_track_in_album_pos'] = cur_track_in_album_pos
			except Exception as e:	
				print("Error in ajax_player_prc_update: cur_track_in_album_pos",e)
		else:
			if 'cur_track_in_album_pos' not in PlayControl_CurStatusD:
				PlayControl_CurStatusD['cur_track_in_album_pos'] = 0
				
		#print 'in view pc cur_track_in_album_pos:',PlayControl_CurStatusD['cur_track_in_album_pos']
		
		if 'current_Album_order_Indx' in modelDic:
			# Данный способ вычисления порядкового номера альбома в листе не корректен ибо зависит от динамического albumDL. т.к. при перезагрузке сервера он отсутсвует
			try:
				#cur_album_pos = [modelDic['albumDL'].index(item) for item in modelDic['albumDL'] if item['album_key'] == PlayControl_CurStatusD['album_CRC32']][0]
				cur_album_pos = modelDic['current_Album_order_Indx']
				PlayControl_CurStatusD['cur_album_pos']	= cur_album_pos
			except Exception as e:	
				print("Error: cur_album_pos",e)
		else:
			print('!!! NO cur_album_pos')
		
		#PlayControl_CurStatusD['cur_track_in_album_pos']	= cur_track_in_album_pos
		#print 2
				
		if 'tagsDL' in modelDic:
			try:	
				json_reply['player_process_info']['tagsDL']=json.dumps(modelDic['tagsDL'])
				del modelDic['tagsDL']
			except:
				print("error at json reply tagsDL:",modelDic['tagsDL'])
		
		if 'tplgDL' in modelDic:
			try:	
				json_reply['player_process_info']['tplgDL']=json.dumps(modelDic['tplgDL'])
				del modelDic['tplgDL']
			except:
				print("error at json reply tagsDL:",modelDic['tplgDL'])		
				
		if 'obj_categDL' in modelDic:
			try:	
				json_reply['player_process_info']['obj_categDL']=json.dumps(modelDic['obj_categDL'])
				del modelDic['obj_categDL']
			except:
				print("error at json reply tagsDL:",modelDic['obj_categDL'])				
		
		if 'curState'in view_elem_id_Dic:
			try:	
				json_reply['player_process_info']['player_State']=json.dumps(PlayControl_CurStatusD)
				if 'current_Album_order_Indx' in modelDic:
					#print 'deleting current_Album_order_Indx'
					del modelDic['current_Album_order_Indx']
				if 'cur_track_in_album_pos' in modelDic:	
					#print 'deleting cur_track_in_album_pos'
					del modelDic['cur_track_in_album_pos']
			except:
				print("error at json reply curState")
		#print 3		
		if 'albumDL' in modelDic:
			try:	
				json_reply['player_process_info']['albumD']=json.dumps(modelDic['albumDL'])
				del modelDic['albumDL']
			except:
				print("error at json reply albumDL:",modelDic['albumDL'])
				
		if 'trackDL' in modelDic:
			try:	
				json_reply['player_process_info']['trackD']=json.dumps(modelDic['trackDL'])
				del modelDic['trackDL']
			except:
				print("error at json reply trackDL:",modelDic['trackDL'])		
		
		#print 4
			
		return json.dumps(json_reply)	
		
	def	ajax_graf_update(self,res,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('in ajax_graf_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))
		tagD = {}
		
		tag_filter = ''
		if 'graf_params' in modelDic:
			logger.debug('graf_params:%s'%(str(modelDic['graf_params'])))
			
			tag_filter = modelDic['graf_params']['tag']
		
		
		json_reply = {}		
		nodeD ={}
		edgeD ={}
		
		
			
		
		
		if 'graf_input_data_navi' in view_elem_id_Dic  and 'plGroupD' in modelDic and 'cat_profD' in modelDic:
			plGroupD = modelDic['plGroupD']
			colorL = ["Black","DarkGray"," LightGrey","White","Aquamarine","Blue","Navy","Purple","DeepPink",
						"Violet","Pink","DarkGreen","Green","YellowGreen","Yellow",
						"Orange","Red","Brown","BurlyWood","Beige"]
						
						
			colorL = [{"background-color": "Black","color": "#FFFFFF"},{"background-color": "DarkGray","color": "#FFFFFF"},{"background-color": "LightGrey","color":"Black"},
						{"background-color":"White","color": "Black"},{"background-color":"Aquamarine","color": "Black"},{"background-color":"Blue","color":"#FFFFFF"},
						{"background-color":"Navy","color":"#FFFFFF"},{"background-color":"Purple","color":"#FFFFFF"},{"background-color":"DeepPink","color":"#FFFFFF"},
						{"background-color":"Violet","color":"#FFFFFF"},{"background-color":"Pink","color":"Black"},{"background-color":"DarkGreen","color":"#FFFFFF"},
						{"background-color":"Green","color":"#FFFFFF"},{"background-color":"YellowGreen","color":"#FFFFFF"},{"background-color":"Yellow","color":"Black"},
						{"background-color":"Orange","color":"#FFFFFF"},{"background-color":"Red","color":"#FFFFFF"},{"background-color":"Brown","color":"#FFFFFF"},
						{"background-color":"BurlyWood","color":"#FFFFFF"},{"background-color":"Beige","color":"Black"}]			
			colorL = colorL + colorL 
			
			nodeD["center"] ={"color":"#95cde5","font_color":"white","w":100,"shape":"box","label":"Music Library $% Enjoy the listening!","alpha":1,'node_type':'center',"link":"#"}
			edgeD["center"] = {}
			
			
			logger.debug('chek point 1')
			plGroupL = [(plGroupD[a]['num'],a) for a in plGroupD]
			plGroupL.sort()
			
			plGroupL = [a[1] for a in plGroupL]
			
			#print 'chek point 2',
			for a in plGroupL:
				#print a
				try:
					node_name=plGroupD[a]['descr']
					node_name_2=plGroupD[a]['descr']
					l = split_2_fix_lines(node_name,15)
					max_len = l['max_len']
					node_name = '$%'.join(l['strL'])
					node_name_2=node_name_2.decode('cp1251')
					node_name=node_name.decode('cp1251')
					mult_line = 'X'
				except:
					max_len = 20
					node_name = a
					mult_line = ''
				#colorL[plGroupL.index(a)]
				try:
					colorD = json.loads(plGroupD[a]['color_set'])
				except:
					colorD = {"background-color":"White","color": "Black"}
					
				nodeD[a] = {"color":colorD['background-color'],"font_color":colorD['color'],"w":max_len+2,"shape":"dot","label":node_name,
																'node_id':a,'mult_line':mult_line,'node_type':'leaf_navi',
																'play_tag':plGroupD[a]['play_tag'],'node_descr':node_name_2}
				edgeD["center"][a] = {"length":.8}	
				#print 'chek point 4'
			graf_data = {"nodes": nodeD,	"edges": edgeD, 'cat_profD': modelDic['cat_profD'], 'mpdHostDL':modelDic['mpd_instanceDL']}	
			
			logger.debug('chek point 5')
			try:	
				json_reply = {'graf_data':json.dumps(graf_data)}
			except:
				print("error at json reply:",graf_data)
			#	pass	
		#
		if 'graf_input_data_tag' in  view_elem_id_Dic and 'tag' in modelDic['graf_params']:
			tag2artistD = modelDic['tag2artistD']
			artistD = modelDic['artistD']
			unreg_artistD  = modelDic['unreg_artistD']
			graf_stat_info = ''
			tagD = modelDic['TagD']
			colorD = {'SONG': "#95cde5",'COMPOSITOR':'#db8e3c','BOXSET':"orange",'VOLUMESET':"#922E00",'THEMATIC':'red','STYLE':'blue'}
			tag_node_cnt = 0
			artist_node_cnt = 0
			unreg_artist_node_cnt =0
			connections_cnt = 0
			for a in tagD:
				
				if tagD[a]['tag_type'] != 'ALL_GRP' and tag_filter in colorD and tagD[a]['tag_type'] == tag_filter:
					pass
				elif tagD[a]['tag_type'] != 'ALL_GRP' and tagD[a]['tag_type'] != tag_filter:	
					continue
					
				#print 	'tag_filter',tag_filter,a	
				try:
					nodeD[a] = {"color":colorD[tagD[a]['tag_type']],"font_color":"white","w":0,"shape":"box","label":tagD[a]['tag_name'],'tag_id':a}
					tag_node_cnt+=1
				except:
					print('err')
					#nodeL.append({"name": tagD[a]['tag_name'],"data":{"color":"#95cde5","w":20,"shape":"box","label":tagD[a]['tag_name'],'tag_id':a}})
			
				logger.debug('at point 1')
			for a in tag2artistD:
				edgeD[a] = {}
				
				for b in tag2artistD[a]:
										
					if b not in nodeD:	
						if b in artistD:
							color = "green"
							label = artistD[b]['artist']
							#print label
						else:
							color = "red"
							unreg_artist_node_cnt+=1
							if b in unreg_artistD:
								try:
									label = unreg_artistD[b].decode('utf8')
								except:
									print('enc error: ',b)
									label = str(b)
									
							else:	
								label = str(b)
						nodeD[b] = {"color":"white","font_color":color,"w":0,"shape":"non","label":label,'artist_id':b}
						artist_node_cnt+=1
						
					edgeD[a][b] = {"length":.8}
					connections_cnt+=1
					
			logger.debug('at point 2')	
			#print 'edgeD:', nodeD
			graf_data = {"nodes": nodeD,	"edges": edgeD}
			
			
			graf_stat_info = "Nodes number: %d, tag nodes:%d, artist noded:%d, unreg_artist:%d, ---> connections:%d <-----"%(len(nodeD),tag_node_cnt,																												artist_node_cnt,unreg_artist_node_cnt,connections_cnt)	
			try:	
				json_reply = {'graf_data':json.dumps(graf_data),'graf_stat_info':graf_stat_info}
			except:
				pass
			
		#modelDic['graf_data'] = nodeD
		
		logger.debug('At point 3')
		#print 'graf data-4 ready',	json_reply
		return json.dumps(json_reply)		
		
	
	def ajax_search_like_page_update(self,res,view_elem_id_Dic,dummy_2,modelDic):	
		
		logger.info('in ajax_search_like_page_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))
		json_reply = {}
		artist_search_vars = ''
		artist_search_varsL = []
		table_header = ""
		if 'artist_search_vars' in view_elem_id_Dic:
			if view_elem_id_Dic['artist_search_vars']==[]:
				artist_search_varsL.append('no suggestion')
			else:
				
				for a in view_elem_id_Dic['artist_search_vars']:
					# !!! Первый индекс неправильный надо его исправить потом
					#artist_search_varsL.append("""<div class><a href="#" onclick="navigation_control_send('goto_artist_tagL',%s);">%s</a><BR></div>"""%(a[1],a[0]))
					auto_suggest_elem = modelDic['Tmpl']['auto_suggest_href_elem']['TMPL']%({'value':a[1],'text':a[0]})
					#artist_search_varsL.append("""<div class><a href="#" onclick="navigation_control_send('goto_artist_tagL',%s);">%s</a></div>"""%(a[1],a[0]))
					artist_search_varsL.append(auto_suggest_elem)
			view_elem_id_Dic['artist_search_vars']	= '\n'.join(artist_search_varsL)				
			#print view_elem_id_Dic['artist_search_vars']
			json_reply = json.dumps(view_elem_id_Dic)
			
			logger.debug('AT----------> artist_search_vars OK')
		
		if 'artist_album_autocompl_data' in view_elem_id_Dic:
			if 'object_autocomplL' in modelDic:
				for a in  modelDic['object_autocomplL']["autocoml_data"]:
					if 'key' in a:
						a['key'] = str(a['key'])
				json_reply = json.dumps(modelDic['object_autocomplL'])
				logger.debug('AT----------> artist_album_autocompl_data OK')
				del modelDic['object_autocomplL']
				
		
		if 'artist_search_vars_opt' in view_elem_id_Dic:
			if view_elem_id_Dic['artist_search_vars_opt']==[]:
				artist_search_varsL.append('no suggestion')
			else:
				
				for a in view_elem_id_Dic['artist_search_vars_opt']:
					#print a
					# !!! Первый индекс неправильный надо его исправить потом
					#artist_search_varsL.append("""<div class><a href="#" onclick="navigation_control_send('goto_artist_tagL',%s);">%s</a><BR></div>"""%(a[1],a[0]))
					auto_suggest_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','selected':'','value':a[1],'text':a[0]})
					#artist_search_varsL.append("""<div class><a href="#" onclick="navigation_control_send('goto_artist_tagL',%s);">%s</a></div>"""%(a[1],a[0]))
					artist_search_varsL.append(auto_suggest_elem)
			view_elem_id_Dic['artist_search_vars_opt']	= '\n'.join(artist_search_varsL)				
			
			json_reply = json.dumps(view_elem_id_Dic)	
			
			logger.debug('AT----------> artist_search_vars_opt OK')
		
		if 'action_result'  in view_elem_id_Dic:	
		# Полная херня, исправить этот неявный кусок надо!!!! использовать как результаты явные слова а не числа.
		# Как вариант action result передавать через modeldic
			#print 'AT----------> Action result ',view_elem_id_Dic.keys()
			view_elem_id_Dic['action_result'] = 1
			if modelDic['SearchBufD']['sD'] == {}:
				view_elem_id_Dic['action_result'] = 0
				
			json_reply = json.dumps(view_elem_id_Dic)
			#print 'AT----------> Action result OK'
			#return json_reply
			
		
		if 'tag_adm_search_res_buf' in view_elem_id_Dic or 'search_res_buf' in view_elem_id_Dic or 'search_res_buf_image' in view_elem_id_Dic:
			print('at search_res_buf-------->1')
			logger.debug('at search_res_buf-------->1')
			search_res_list = ''
			sD = modelDic['SearchBufD']['sD']
			sBufparamD = modelDic['SearchBufD']['paramD']
			sD_editable = {}
			
			if 'change_delta_list' in view_elem_id_Dic:
				
				sD_editable = modelDic['Search_Editable_BufD']['sD']
				#print "in change_delta_list area",modelDic['Search_Editable_BufD'].keys(),sD_editable.keys()
				if modelDic['Search_Editable_BufD']['action_mode'] == "add": 
					colorL = ['#FFE5B4','#FFCC99']
				else:
					colorL = ['#00BFFF','#1E90FF']
				#print 'colorL=',colorL
				search_res_list  = search_res_list + generic_search_res_track_list(sD_editable,colorL,modelDic,'simple')
				
				# Если есть измененная часть то сообщаем клиенту, что это так 
				if sD_editable != {}:
					view_elem_id_Dic['action_result'] = 2
					view_elem_id_Dic['action_key'] = res
				
			if 'tag_adm_search_res_buf' in view_elem_id_Dic:
				search_res_list  = search_res_list + generic_search_res_track_list(sD,['#FFFFCC','#CCFFFF'],modelDic,'simple')
				
			elif 'search_res_buf' in view_elem_id_Dic:	
				
				if 'mode' in sBufparamD:
					if sBufparamD['mode'] == 'tags_navi':
						search_res_list  = search_res_list + generic_search_res_track_list(sD,['#FFFFCC','#CCFFFF'],modelDic,'with_a_t_a_href')
					elif sBufparamD['mode'] == 'text_only':	
						search_res_list  = search_res_list + generic_search_res_track_list(sD,['#FFFFCC','#CCFFFF'],modelDic,'simple')
					elif sBufparamD['mode'] == 'with_pic':	
						search_res_list  = search_res_list + generic_search_res_track_list(sD,['#FFFFCC','#CCFFFF'],modelDic,'with_pic')	
					
			if 'search_res_buf_image' in view_elem_id_Dic:				
				logger.debug('AT--701-----search_res_buf_image---> serch res OK')
				if 'mode' in sBufparamD:
					if sBufparamD['mode'] == 'images':	
						search_res_list  = search_res_list + images_search_res_album_list(sD,['#FFFFCC','#CCFFFF'],modelDic,'images')	
						
					search_part_tmpl = modelDic['Tmpl']['search_part_image_tmpl']['TMPL']%({'res_lenth':len(sD)+len(sD_editable),'search_res_list':search_res_list,'table_header':table_header})	
			else:			
				table_header = modelDic['Tmpl']['table_header_elem']['TMPL']
				print('search_res_list-3.1')
				search_part_tmpl = modelDic['Tmpl']['search_part_new_tmpl']['TMPL']%({'res_lenth':len(sD)+len(sD_editable),'search_res_list':search_res_list,'table_header':table_header})
				print('search_res_list-3.2')
				
			
			try:
				view_elem_id_Dic['search_result_frm'] = search_part_tmpl
			except Exception as e:
				logger.critical('AT ajax_search_like_page_update base64 covertion failed: line 727')
				d = pickle.dumps({'Dump_Data':search_part_tmpl,'Error':str(e),'ErrorContext':'AT ajax_search_like_page_update base64 convertion failed:line 727'})
				
				logger.info('727 Dump saved at debug.dat in [%s]'%(str(os.getcwd())))
				f = open('debug.dat','w')
				f.write(d)
				f.close()
				
			print('search_res_list-4')
			#print view_elem_id_Dic['search_result_frm']
			#print 'search_res_list-3 before dumps'
			try:
				# так как перед вызовом метода представления идет динамический вызов метода контроллра, который возвращает значение,
				# то в res = этому возвращаемому значению_ это неявное присваивание, в дальнейшем продумать как это делать явно
				# возможно стоит это делать через modelDic
				
				if 	'Search_Editable_BufD' in modelDic:
					if modelDic['Search_Editable_BufD']['sD'] != {}:
						pass
				elif modelDic['SearchBufD']['sD'] == {}:
					
					view_elem_id_Dic['action_result'] = 0
				elif modelDic['SearchBufD']['sD'] != {}:
						view_elem_id_Dic['action_result'] = res		
				
				json_reply = json.dumps(view_elem_id_Dic)
				logger.debug('AT--844-----search_res_buf_image---> search res OK')
			except:
				try:
					view_elem_id_Dic['search_result_frm'] = view_elem_id_Dic['search_result_frm'] #.decode('cp1251')
					if 	'Search_Editable_BufD' in modelDic:
						if modelDic['Search_Editable_BufD']['sD'] != {}:
							pass
							#view_elem_id_Dic['action_result'] = res
					elif modelDic['SearchBufD']['sD'] == {}:
						
						view_elem_id_Dic['action_result'] = 0
					elif modelDic['SearchBufD']['sD'] != {}:
						view_elem_id_Dic['action_result'] = res	
						
					json_reply = json.dumps(view_elem_id_Dic)
					logger.critical('AT--859-----search_res_buf_image---> search res ERROE')
				except:
					d = pickle.dumps(view_elem_id_Dic)
					f = open('debug.dat','w')
					f.write(d)
					f.close()
					
					view_elem_id_Dic['search_result_frm'] ='error'
					json_reply = json.dumps(view_elem_id_Dic)
			
			logger.debug('AT----------> serch res OK%s'%(str(res)))
		#print 'search_res_list-4 ready',res
		logger.debug('AT----------> ajax_search_like_page_update OK-Finished%s'%(str(res)))
		#print(json_reply)
		return json_reply

	def ajax_main_page_update(self,PlayControl_CurStatusD,view_elem_id_Dic,modelStateDic,modelDic,*args):
		# PlayControl_CurStatusD - отражение текущего состояния медиаплеера в модели в целях минимизации количества обращений
		# к контроллеру плеера этот словарь передается от контроллера MVC, где он формируется почти непосредственно перед вызовом
		# генерации представления
		#
		# view_elem_id_Dic cловарь требуемых в представлении данных
		
		# генерация представления происходит из того предположения, что модель уже находиться в актуальном состоянии вызовы контроллера
		# плеера не нужны
		
		# Необходимые постоянно переменные состоянния
		
		albumResL = []
		trackResL = []
		groupResL = []
		plistResL = []
		PListQueueResL = []
		
		
		curList_crc32 = PlayControl_CurStatusD['pL_CRC32']
		songNum = PlayControl_CurStatusD['pl_pos']
		albumNum = modelStateDic['albumNum']
		
		
		
		logger.info('in ajax_main_page_update %s PlayControl_CurStatusD=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(PlayControl_CurStatusD),str(list(modelDic.keys()))))
		#print 'view_elem_id_Dic:',view_elem_id_Dic
		
		# определим	общие данные необходимы для всех вариантов
		if 'refresh_time' in view_elem_id_Dic:
			view_elem_id_Dic['refresh_time'] = PlayControl_CurStatusD['rest_sec'] 
			view_elem_id_Dic['duration'] = PlayControl_CurStatusD['duration_sec'] 
			
		if 'cover' in view_elem_id_Dic:
			try:
				view_elem_id_Dic['image_crc32'] = str(modelDic['metaD_of_cur_pL'][PlayControl_CurStatusD['track_CRC32']]['album_crc32']) 	
			except Exception as e:
				logger.critical('Exception:',e)
			
		if 'play_status' in view_elem_id_Dic:
			if  PlayControl_CurStatusD['playBack_Mode'] == 1:
				view_elem_id_Dic['play_status_txt'] = 'Playing.'
				view_elem_id_Dic['play_status'] = 1
			elif  PlayControl_CurStatusD['playBack_Mode'] == 3:	
				view_elem_id_Dic['play_status_txt'] = 'Paused.'
				view_elem_id_Dic['play_status'] = 3
			elif  PlayControl_CurStatusD['playBack_Mode'] == 0:		
				view_elem_id_Dic['play_status_txt'] = 'Stopped.'
				view_elem_id_Dic['play_status'] = 0
				
		if 'tagsL' in view_elem_id_Dic:		
			TagD = modelDic['TagD']
			
			#print "Main 3 Ok"	
			tagsL = modelDic['tagsL']		
			
			hard_tags = ''
			
			
			for a in tagsL:
				
				if a in TagD:
					if TagD[a]['tag_type'] == 'SONG' or TagD[a]['tag_type'] == 'SYSTEM':
						continue
					#print 'tagsL',tagsL
					#print TagD[a]
					
					hard_tags = hard_tags + modelDic['Tmpl']['title_tag_navi_href_elem_w_td']['TMPL']%(
						{'class':'hard_tags','value':str(a),'selected':'','text':TagD[a]['tag_name'].encode('utf8')})
					
					
					
				else:	
					
					logger.error(' %s not found in TagD.keys():%s'%(str(a),str(list(TagD.keys()))))
					
			
					
			view_elem_id_Dic['tagsL'] =  hard_tags
			
			logger.info('tagsL - OK')
			
		if 'tagsAllL' in view_elem_id_Dic:
			TagD = modelDic['TagD']
			#print 'TagD:',TagD
			tagL = []
			try:
				tagL=[(TagD[a]['tag_name'],a) for a in TagD if 'tag_name' in TagD[a]]
				tagL.sort() 
				tagL = [a[1] for a in tagL]
				#print 'tagAllL--4'
			except Exception as e:
				tagL = []
				logger.critical(' %s not found in TagD.keys():%s'%(str(a),str(list(TagD.keys()))))
				
			TagResL = []
			form_mode =  ''
			
			tags_num = len(tagL)	
			tag_ancor = ''
			for a in tagL:
				try:
					opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a),'selected':'','text':TagD[a]['tag_name']})
				except:
					print("""Erorr in TagD[a]['tag_name'] index:""",a)	
					continue
					
					
					
				#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
				TagResL.append(opt_elem)
			#print TagResL
			view_elem_id_Dic['tagsAllL'] = '\n'.join(TagResL)				
			
			logger.info("tagsAllL - OK")
			
		# ВНИМАНИЕ!!! При генерации списков первый и последний элементы это опредение списка, это определение не нужно,
		# но по причине бага в Хроме и невозможности сделать замету по DIV мы вынуждены делать замену по ID SELECT
		
		# Общаая подготовка данных для списка альбомов и списка треков	
		if 'trackL'	 in view_elem_id_Dic or 'albumL' in view_elem_id_Dic:
			albumD = modelDic['albumD']
			playerStatus = {'curAlbumIndx':0,'curTrackIndx':0,'curPlayListIndx':0}
			playerStatus['curTrackIndx'] = songNum

			albumL = [(albumD[b]['firstFileIndex'],b,albumD[b]['format']) for b in albumD]
			albumL.sort()

			tL = [b[0] for b in albumL if playerStatus['curTrackIndx'] >= b[0]]
			if tL == []:
				playerStatus['curAlbumIndx'] = 0
			else:
				playerStatus['curAlbumIndx'] = [b[0] for b in albumL if playerStatus['curTrackIndx'] >= b[0]][-1]

			l = [a for a in albumD if albumD[a]['firstFileIndex'] ==playerStatus['curAlbumIndx']]
			if l != []:
				albumKey = l[0]
			else:	
				albumKey = 0
				
				
			logger.info("trackL - OK")
			
		if 'albumL' in view_elem_id_Dic:	
			# Генерируем данные для списка альбомов
			
			#albumResL.append("""  <SELECT NAME="getAlbum" id="getAlbum">""")
			for a in albumL:
				r_line = str2_RusLine(a[1],60)	

				if 'mp3' in a[2].lower():
					class_color_ddl = "mp3_color"
				else:
					class_color_ddl = "losless_color"	
				
				if a[0] == playerStatus['curAlbumIndx']:
					selected = 'selected'
				else:
					selected = ''
				try:	
					opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':class_color_ddl,'value':a[0],'selected':selected,
																			'text':r_line.decode('cp1251').encode('utf8')})
				except Exception as e:
					
					logger.critical(' %s Error in templating AlbumL in mainview:%s'%(str(a),str(list(modelDic.keys()))))
					opt_elem = "Error in templating AlbumL in mainview",list(modelDic.keys())
					
				albumResL.append(opt_elem)
			
			view_elem_id_Dic['albumL'] =  '\n'.join(albumResL)	
			
			logger.info("albumL - OK")
		
		if 'trackL' in view_elem_id_Dic:	
			# Генерируем данные для списка треков
			
			if albumKey in albumD:
				for a in albumD[albumKey]['albumL']:
					opt_elem = ''
					r_line = str2_RusLine(a[0],90)
			
					if 'cue' not in albumD[albumKey]:
						if a[1] == playerStatus['curTrackIndx']:
							selected = 'selected'	
						else:
							selected = ''
							
						try:	
							opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':r_line.decode('cp1251').encode('utf8')})
						except:
							opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':r_line})

					else:
						if a[1] == playerStatus['curTrackIndx']:
							selected = 'selected'	
						else:
							selected = ''	
						opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':r_line})	
						
					#print 	'opt_elem=',opt_elem
					trackResL.append(opt_elem)	
						
			else:
				trackResL = []
			view_elem_id_Dic['trackL'] =  '\n'.join(trackResL)
			
			logger.info("trackL - OK")
		
		if 'jscript_tag_typeL'	 in view_elem_id_Dic:
			tagD = modelDic['TagD']
			scrpt_2_main = ''
			scrpt_2_main_tagL = []	
			
			#print 	'js geneta 1'	
			sel_option_js_contentL = []
			for a in tagL:
				#scrpt_2_main =  scrpt_2_main + """ selbox.options[selbox.options.length] = new Option("%s","%s");\n"""%(modelDic['pD'][a]['title'].encode('utf8'),str(a))
				try:
					elem = modelDic['Tmpl']['gen_if_js_inside_elem']['TMPL']%({'text':tagD[a]['tag_name'],'value':str(a)})
				except:
					elem = 'Error in tmpl rendering',a
				sel_option_js_contentL.append(elem)
			
			#print 	'js geneta 2'		
			# Вначале заполняем явно первую группу	
			sel_option_js_content_list  = '\n'.join(sel_option_js_contentL)	
			if_chosen_elem = modelDic['Tmpl']['gen_if_js_elem']['TMPL']%({'group':'ALL_GRP','cnt':tags_num,'sel_option_js_content_list':sel_option_js_content_list}) 
			scrpt_2_main_tagL.append(if_chosen_elem)
			#print 	'js geneta 3'
			
			# получаем все группы тэгов
			tagGroupL = []
			for a in tagD:
				if tagD[a]['tag_type'] not in tagGroupL:
					if 'tag_type' in tagD[a]:
						tagGroupL.append(tagD[a]['tag_type'])
						
			for a in tagGroupL:
				#print 'GR=',a
				sel_option_js_contentL = []
				for b in tagL:
				#scrpt_2_main =  scrpt_2_main + """ selbox.options[selbox.options.length] = new Option("%s","%s");\n"""%(modelDic['pD'][a]['title'].encode('utf8'),str(a))
					if tagD[b]['tag_type'] == a:
						elem = modelDic['Tmpl']['gen_if_js_inside_elem']['TMPL']%({'text':tagD[b]['tag_name'],'value':str(b)})
						sel_option_js_contentL.append(elem)
					else:
						continue
				sel_option_js_content_list  = '\n'.join(sel_option_js_contentL)	
				if_chosen_elem = modelDic['Tmpl']['gen_if_js_elem']['TMPL']%({'group':str(a),'cnt':len(sel_option_js_contentL),'sel_option_js_content_list':sel_option_js_content_list}) 
				scrpt_2_main_tagL.append(if_chosen_elem)	
			
			scrpt_2_main =  '\n'.join(scrpt_2_main_tagL)
			view_elem_id_Dic['jscript_tag_typeL'] =  '\n'.join(scrpt_2_main_tagL)
		
		if 'jscript_plist_groupL' in view_elem_id_Dic and 'group2PlayListD'  in modelDic and 'pD'  in modelDic:
		#********************************	Данные для скрипта выбора групп листов	
			group2PlayListD = modelDic['group2PlayListD']['group2PlistD']
			scrpt_2_main = ''
			scrpt_2_mainL = []
			
			sortL = [(modelDic['pD'][a]['title'],a) for a in modelDic['pD']]
			sortL.sort()
			sortL = [a[1] for a in sortL]
			
			sel_option_js_contentL = []
			for a in sortL:
				#scrpt_2_main =  scrpt_2_main + """ selbox.options[selbox.options.length] = new Option("%s","%s");\n"""%(modelDic['pD'][a]['title'].encode('utf8'),str(a))
				elem = modelDic['Tmpl']['gen_if_js_inside_elem']['TMPL']%({'text':modelDic['pD'][a]['title'].encode('utf8'),'value':str(a)})
				sel_option_js_contentL.append(elem)
			
			# Вна	
			sel_option_js_content_list  = '\n'.join(sel_option_js_contentL)	
			if_chosen_elem = modelDic['Tmpl']['gen_if_js_elem']['TMPL']%({'group':'ALL_GRP','cnt':len(sortL),'sel_option_js_content_list':sel_option_js_content_list}) 
			scrpt_2_mainL.append(if_chosen_elem)
			
			# Теперь идем по каждой группе
			#print group2PlayListD
			for a in group2PlayListD:
				sel_option_js_content_list = ''
				sel_option_js_contentL = []
				if_chosen_elem = ''
				#scrpt_2_main =  scrpt_2_main + """ if (chosen == "%s") { \n"""%(a)
				
				#print 'a=',a
				sortL = [(modelDic['pD'][b]['title'],b) for b in group2PlayListD[a] if b in modelDic['pD'] ]
				sortL.sort()
				sortL = [b[1] for b in sortL]
				#for b in group2PlayListD['group2PlistD'][a]:
				for b in sortL:
					if b not in modelDic['pD']:
						print('CategoryDB Inconsistens with PlayListDB:',b,'is missing in plalistDB')
						continue
					try:
						elem = modelDic['Tmpl']['gen_if_js_inside_elem']['TMPL']%({'text':modelDic['pD'][b]['title'].encode('utf8'),'value':str(b)}) 
						#print '2ok=',pD[b]['title'].encode('cp1251'),type(pD[b]['title'].encode('cp1251')),type(b)
					except:
						print('issue')
						print('Error=',modelDic['pD'][b]['title'].encode('utf8'),type(modelDic['pD'][b]['title'].encode('utf8')),b,type(b))
						continue	
						
					sel_option_js_contentL.append(elem)
					
				sel_option_js_content_list  = '\n'.join(sel_option_js_contentL)
				if_chosen_elem = modelDic['Tmpl']['gen_if_js_elem']['TMPL']%({'group':a,'cnt':len(sel_option_js_contentL),'sel_option_js_content_list':sel_option_js_content_list}) 
				scrpt_2_mainL.append(if_chosen_elem)
				
	
			
			view_elem_id_Dic['jscript_plist_groupL'] =  '\n'.join(scrpt_2_mainL)
			
			logger.info("jscript main if   - OK")
		
		
		if 'plist_groupL' in view_elem_id_Dic and 'group2PlayListD'  in modelDic:
			# Генерируем данные для групп плейлистов
			
			playlistGroup = ''
			#print '1'
			if playlistGroup == 'ALL_GRP':
				try:
					groupResL.append("""<option value="ALL_GRP" selected > All - Все плейлисты без группировок </option>\n""".encode('utf8'))
				except:
					groupResL.append("""<option value="ALL_GRP" selected > All - ----- </option>\n""")
			else:	
				try:
					groupResL.append("""<option value="ALL_GRP" > All - Все плейлисты без группировок </option>\n""".encode('utf8'))
				except:
					groupResL.append("""<option value="ALL_GRP" > All - ---------- </option>\n""")
			#print '2'
			
			# Сортируем список групп по номеру порядка представления на экране	
			grKeysL = [(modelDic['group2PlayListD']['groupD'][a]['num'] ,a)for a in modelDic['group2PlayListD']['groupD']]
			grKeysL.sort()
			grKeysL = [a[1] for a in grKeysL]
					
			
			colorL = ["background-color: Black;color: #FFFFFF;","background-color: DarkGray;","background-color: LightGrey;",
						"background-color: White;","background-color: Aquamarine;","background-color: Blue;color: #FFFFFF;",
						"background-color: Navy;color: #FFFFFF;","background-color: Purple;color: #FFFFFF;","background-color: DeepPink;",
						"background-color: Violet;","background-color: Pink;","background-color: DarkGreen;color: #FFFFFF;",
						"background-color: Green;color: #FFFFFF;","background-color: YellowGreen;","background-color: Yellow;",
						"background-color: Orange;","background-color: Red;","background-color: Brown;","background-color: BurlyWood;",
						"background-color: Beige;"]
			colorL = colorL + colorL 			
					
					
					
			for a in grKeysL :	
				if 	a == playlistGroup:
					groupResL.append("""<option style="%s" value="%s" selected > %s </option>\n"""%(colorL[grKeysL.index(a)],a,modelDic['group2PlayListD']['groupD'][a]['descr']))
				else:
					groupResL.append("""<option style="%s" value="%s" > %s </option>\n"""%(colorL[grKeysL.index(a)],a,modelDic['group2PlayListD']['groupD'][a]['descr']))
			#print '3'
			view_elem_id_Dic['plist_groupL'] =  '\n'.join(groupResL)
			#print '4'
			logger.info("plist_groupL   - OK")
			
		if 'lib_plistL' in view_elem_id_Dic and 'pD' in modelDic and 'plist_groupL' in view_elem_id_Dic:	
		
			
			# Генерируем данные для списка плейлистов	
			curList_fName =	''
			playlistGroup = ''
			
			sortL = [(modelDic['pD'][a]['title'],a) for a in modelDic['pD']]
			try:
				sortL.sort()
			except:
				print('Strange error at _cntrl.py:1669')
					
			sortL = [a[1] for a in sortL]
			#print 	'playlistGroup=',playlistGroup
			
			for a in sortL:
				if playlistGroup != 'ALL_GRP':
					#if a not in  modelDic['group2PlayListD']['group2PlistD'][playlistGroup]:
					#	continue
					pass
				if a == curList_fName:
					plistResL.append("""<OPTION VALUE= "%s" selected > %s </option>\n"""%(a,modelDic['pD'][a]['title'].encode('utf8')))
				else:	
					plistResL.append("""<OPTION VALUE= "%s" > %s </option>\n"""%(a,modelDic['pD'][a]['title'].encode('utf8')))
					
			view_elem_id_Dic['lib_plistL'] =  '\n'.join(plistResL)

			
		
		if 'queueL' in view_elem_id_Dic:
			#PListQueueResL.append("""<SELECT NAME="getPlistQueue" id="getPlistQueue">""")
			for a in modelDic['PlayListQueue']:
				if curList_crc32 == a:
					PListQueueResL.append("""<OPTION VALUE= "%s" selected > %s  </option>\n"""%(a,str(modelDic['PlayListQueue'].index(a)+1)+'.'+modelDic['PlayListQueueD'][a]['listType']+' *'+modelDic['PlayListQueueD'][a]['listDescr'].encode('utf8')))			
				else:
					PListQueueResL.append("""<OPTION VALUE= "%s" > %s </option>\n"""%(a,str(modelDic['PlayListQueue'].index(a)+1)+'.'+modelDic['PlayListQueueD'][a]['listType']+' *'+modelDic['PlayListQueueD'][a]['listDescr'].encode('utf8')))			
			#PListQueueResL.append("""</SELECT> """)	
			
			view_elem_id_Dic['queueL'] =  '\n'.join(PListQueueResL)	
			
	
		#********************************	Данные для таблицы фрейма 3х песен	frame_table_content	
		if 'frame3' in view_elem_id_Dic:
			
			logger.debug('frame3 generation-1')
			
			view_elem_id_Dic['frame3'] = {}
			
			
			stop_flag = PlayControl_CurStatusD['playBack_Mode']
			
			logger.debug('frame3 generation-2')
			
				
			# Получить метаданные для трех текущих композиций
			max_indx = len(modelDic['PlayList_asCRC32_L'])-1
			if songNum == 0:
				frame_l = [modelDic['PlayList_asCRC32_L'][max_indx]]+modelDic['PlayList_asCRC32_L'][0:2]
			elif songNum == max_indx:
				frame_l = modelDic['PlayList_asCRC32_L'][max_indx-1:max_indx+1]+[modelDic['PlayList_asCRC32_L'][0]]
			else:
				frame_l = modelDic['PlayList_asCRC32_L'][songNum-1:songNum+2]
			logger.debug('frame3 generation-3')
			
			#Сохраняем изначальную длину фрейма для проверки что в нем не менее трех элементов
			len_frame = len(frame_l)
			if len(frame_l) == 1:
				frame_l.insert(0,0)
				modelDic['metaD_of_cur_pL'][0]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
				frame_l.append(2)
				modelDic['metaD_of_cur_pL'][2]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
			elif len(frame_l) == 2:
				frame_l[0] = 0
				modelDic['metaD_of_cur_pL'][0]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
				frame_l.append(2)
				modelDic['metaD_of_cur_pL'][2]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
			
			#print metaL
			logger.debug('frame3 generation-4')
			frame_table_content = ''
			# так как словать метаданных имеет ключами порядковый номер композиции в списке то сделаем список позиций а не срц32
				
			for a in  frame_l:
				#print 'frame3 generation-2',a	
				frame_table_content = ''
				
				#frame_table_content = frame_table_content + '<TR>\n'
				if frame_l.index(a)==1:	
					frame_table_content = frame_table_content + ' <tr style="background-color:#CCFFCC" id="frame3-row-%s" height="60" >'%(str(frame_l.index(a)))
				else:
					frame_table_content = frame_table_content + '<tr height="60" id="frame3-row-%s" >'	%(str(frame_l.index(a)))
				
				elem_id = "frame3-row-%s"%(str(frame_l.index(a)))	
					
				if a not in modelDic['metaD_of_cur_pL']:
					
					print('Logical error! Key ',a, type(a),' missing in __metaD_of_cur_pL',len(modelDic['metaD_of_cur_pL']))
					continue
					
				frame_table_content = frame_table_content + '\n'
				
				for c in ['title','artist','album','time_str','bitrate','format']:			
					#print 'frame3 generation-2-2',c
					frame_table_content = frame_table_content + ' <td>'
					frame_table_content = frame_table_content + '<br>'
					try:
						if c in modelDic['metaD_of_cur_pL'][a]:
							if frame_l.index(a)==1 :
								if   c == 'album' and 'NA_' not in modelDic['metaD_of_cur_pL'][a][c]:
									#print "############## album begin"
									album_tag_navi_href_elem = modelDic['Tmpl']['album_tag_navi_href_elem']['TMPL']%(
										{'value':modelDic['metaD_of_cur_pL'][a]['album_crc32'],'text':modelDic['metaD_of_cur_pL'][a][c]})
									frame_table_content = frame_table_content + album_tag_navi_href_elem
									view_elem_id_Dic['image_crc32'] = str(modelDic['metaD_of_cur_pL'][a]['album_crc32'])
									#print "##############album OK"
								elif c == 'artist'  and 'NA_' not in modelDic['metaD_of_cur_pL'][a][c]:	
									artist_tag_navi_href_elem = modelDic['Tmpl']['artist_tag_navi_href_elem']['TMPL']%(
										{'value':modelDic['metaD_of_cur_pL'][a]['artist_crc32'],'text':modelDic['metaD_of_cur_pL'][a][c]})
									frame_table_content = frame_table_content + artist_tag_navi_href_elem
									
								elif c == 'title'  and 'NA_' not in modelDic['metaD_of_cur_pL'][a][c]:	

									title_tag_navi_href_elem = ''		
									for tag in tagsL:
										if tag in TagD:
											if TagD[tag]['tag_type'] == 'SONG':
												#print TagD[tag]
																								
												title_tag_navi_href_elem = modelDic['Tmpl']['title_tag_navi_href_elem']['TMPL']%(
													{'value':str(tag),'class':"",'text':modelDic['metaD_of_cur_pL'][a][c]})	
												break
												
									if title_tag_navi_href_elem == '':				
										title_tag_navi_href_elem = str(modelDic['metaD_of_cur_pL'][a][c])
										
									frame_table_content = frame_table_content + title_tag_navi_href_elem	
									
								else:		
									frame_table_content = frame_table_content + str(modelDic['metaD_of_cur_pL'][a][c])
							else: 
								frame_table_content = frame_table_content + str(modelDic['metaD_of_cur_pL'][a][c])
						#print '1-ok','-->',mp3L.index(a)
					except UnicodeEncodeError:	
						try:
							s = ''.join([chr(ord(b)) for b in modelDic['metaD_of_cur_pL'][a][c]])
							frame_table_content = frame_table_content +s.decode('cp1251').encode('utf8')
							#print '2-ok','-->',mp3L.index(a)
						except ValueError:
							try:
								#print 'b=',b,mp3L.index(a),a
								frame_table_content = frame_table_content + modelDic['metaD_of_cur_pL'][a][c].encode('utf8')
							except:
								frame_table_content = frame_table_content +"N/A"+c 
								
			
					frame_table_content = frame_table_content + '</td>\n'
				
				frame_table_content = frame_table_content + '</tr>\n'
				view_elem_id_Dic['frame3'][elem_id] = frame_table_content.encode('base64')
				#print "frame3 - OK"
				
			logger.info('frame3 -- OK')	
#******************************************									
	
	# Current Album CRC32
		if 'curState' in view_elem_id_Dic:
			print('Cur_state')
			view_elem_id_Dic['curState']={'curList_crc32':curList_crc32,'curAlbum':albumNum,'curTrack':songNum}
		
		print('------ Pol Ok ---------')
	# Current Track CRC32
		if 'local' in args:
			return view_elem_id_Dic
		print('------ Pol Ok 2------------------')	
		json_reply = json.dumps(view_elem_id_Dic)
		print('------ Pol Ok 3------------------')
		logger.debug('json_reply -- OK')
		#if 'frame3' in view_elem_id_Dic:
		#	for a in view_elem_id_Dic['frame3']:
		#		del view_elem_id_Dic['frame3'][a]
		#	view_elem_id_Dic['frame3'] = ''
		return json_reply
	
	def ajax_debug_update(self,res,view_elem_id_Dic,dummy_2,modelDic,*args):	
		logger.info('in ajax_debug_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))
		ignorL = ['Tmpl','debugD']
		
		debug_data = ""
		
		for a in modelDic:
			if a in ignorL:
				continue
			if a not in modelDic['debugD']:
				continue
			
			debug_data = debug_data + "----------------------------------------------------------<BR>"	
			debug_data = debug_data + 'Getting '+ str(a)  + '<BR>'
			try:
				debug_data = debug_data + ' Object len:  '+str(len(modelDic[a])) + '<BR>'
				if len(modelDic[a]) < 10 and type(modelDic[a]) == dict:
					debug_data = debug_data + ' Object keys:  '+str(list(modelDic[a].keys())) + '<BR>'
				elif len(modelDic[a]) > 10 and type(modelDic[a]) == dict:
					if type(modelDic[a][list(modelDic[a].keys())[0]]) == dict:
						key = list(modelDic[a].keys())[0]
						debug_data = debug_data + ' Object keys of the first key modelDic[%s] key=%s:  '%(str(a),str(key))+'<BR>'
						debug_data = debug_data + 'keys():--->'+str(list(modelDic[a][key].keys())) + '<BR>'	
						debug_data = debug_data + '1st Entry for the keys:--->'+ '<BR>'+str(modelDic[a][key]) + '<BR>'	
			except Exception as e:
				logger.critical('Exception:%s'%(str(e)))
				debug_data = debug_data + 'Error at obj len:' + str(a) + '<BR>'
				
			debug_data = debug_data + "----------------------------------------------------------<BR>"	
			
				
			try:
				#print view_elem_id_Dic[a]
				debug_data = debug_data + str(modelDic[a]) + '<BR>'
			except Exception as e:
				logger.critical('Exception:%s'%(str(e)))
				#print 'Error at:' + str(a)
				debug_data = debug_data + 'Error at:' + str(a) + '<BR>'
		view_elem_id_Dic['debug_data'] = debug_data		
		json_reply = json.dumps(view_elem_id_Dic)
		return json_reply
		
	def ajax_cast_page_update(self,res,view_elem_id_Dic,dummy_2,modelDic,*args):
		
		logger.info('in ajax_cast_page_update %s res=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(res),str(list(modelDic.keys()))))
		# PlayControl_CurStatusD - отражение текущего состояния медиаплеера в модели в целях минимизации количества обращений
		# к контроллеру плеера этот словарь передается от контроллера MVC, где он формируется почти непосредственно перед вызовом
		# генерации представления
		#
		# view_elem_id_Dic cловарь требуемых в представлении данных
		
		# генерация представления происходит из того предположения, что модель уже находиться в актуальном состоянии вызовы контроллера
		# плеера не нужны
		
		# Необходимые постоянно переменные состоянния
		
		albumResL = []
		trackResL = []
		groupResL = []
		plistResL = []
		PListQueueResL = []
		TagD =  {}
		castL = []
		json_reply = {}
		songNum = 0
		
		tagsL = []
		
		
		
		#print 'view_elem_id_Dic:',view_elem_id_Dic
		
			
			
		logger.debug('before castL generation')		
		if 'castL' in view_elem_id_Dic and 'castL' in modelDic:		
			castL = modelDic['castL']
			
			logger.debug("castL - OK")		
			view_elem_id_Dic['cast_data'] = json.dumps(castL)	
			#json_reply = {'cast_data':json.dumps(castL)}	
			
		logger.debug('before tagsL generation')		
		
		if 'tagsL' in view_elem_id_Dic:		
			TagD = modelDic['TagD']
			
			#print "Main 3 Ok"	
			tagsL = modelDic['tagsL']		
			
			hard_tags = ''
			for a in tagsL:
				
				if a in TagD:
					if TagD[a]['tag_type'] == 'SONG':
						continue
					
					logger.debug('tagsL = %s'%(str(tagsL)))
					#print TagD[a]
					hard_tags = hard_tags + modelDic['Tmpl']['title_tag_navi_href_elem_w_td']['TMPL']%(
						{'class':'hard_tags','value':str(a),'selected':'','text':TagD[a]['tag_name'].encode('utf8')})
				else :	
					logger.error(' %s not found in TagD.keys():%s'%(str(a),str(list(TagD.keys()))))
						
			view_elem_id_Dic['tagsL'] =  hard_tags
			
			logger.debug("tagsL - OK")				
		
		if 'cast_frame3' in view_elem_id_Dic:
			view_elem_id_Dic['cast_frame3'] = {}
			
			logger.debug('frame3 generation-1')
			# Тут нужна срц32 текущей песни и ее позиция в списке воспроизведения songNum.
			cur_crc32 = modelDic['cur_crc32']
			castL = modelDic['CastPlayListD']['castL']
			songNum = modelDic['CastPlayListD']['castL'].index(modelDic['CastPlayListD']['cur_track_id'])
			view_elem_id_Dic['frame3'] = {}
			
			
			#stop_flag = PlayControl_CurStatusD['playBack_Mode']
			
				
			# Получить метаданные для трех текущих композиций
			max_indx = len(modelDic['CastPlayListD']['crc32L'])-1
			
			
			if songNum == 0:
				frame_l = [modelDic['CastPlayListD']['crc32L'][max_indx]]+modelDic['CastPlayListD']['crc32L'][0:2]
			elif songNum == max_indx:
				frame_l = modelDic['CastPlayListD']['crc32L'][max_indx-1:max_indx+1]+modelDic['CastPlayListD']['crc32L'][0]
			else:
				frame_l = modelDic['CastPlayListD']['crc32L'][songNum-1:songNum+2]
			
			
			#Сохраняем изначальную длину фрейма для проверки что в нем не менее трех элементов
			len_frame = len(frame_l)
			
			
			logger.debug('frame3 generation-1 - OK')
			#Сохраняем изначальную длину фрейма для проверки что в нем не менее трех элементов
			len_frame = len(frame_l)
			if len(frame_l) == 1:
				frame_l.insert(0,0)
				modelDic['CastPlayListD']['metaD'][0]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
				frame_l.append(2)
				modelDic['CastPlayListD']['metaD'][2]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
			elif len(frame_l) == 2:
				frame_l[0] = 0
				modelDic['CastPlayListD']['metaD'][0]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
				frame_l.append(2)
				modelDic['CastPlayListD']['metaD'][2]={'album':'------','artist':'------','title':'------','time':'------','bitrate':'------','format':'------'}
			
			#print metaL
			
			frame_table_content = ''
			# так как словать метаданных имеет ключами порядковый номер композиции в списке то сделаем список позиций а не срц32
			logger.debug('frame3 generation-2 OK')
			for a in  frame_l:
				#print 'frame3 generation-2',a	
				frame_table_content = ''
				
				#frame_table_content = frame_table_content + '<TR>\n'
				if frame_l.index(a)==1:	
					frame_table_content = frame_table_content + ' <tr style="background-color:#CCFFCC" id="frame3-row-%s" height="60" >'%(str(frame_l.index(a)))
				else:
					frame_table_content = frame_table_content + '<tr height="60" id="frame3-row-%s" >'	%(str(frame_l.index(a)))
				
				elem_id = "frame3-row-%s"%(str(frame_l.index(a)))	
					
				if a not in modelDic['CastPlayListD']['metaD']:
					
					logger.error( 'Logical error! Key %s  missing in __metaD_of_cur_pL %s'%(str(a),str(len(modelDic['CastPlayListD']['metaD']))))
					continue
					
				frame_table_content = frame_table_content + '\n'
				
				for c in ['title','artist','album','time_str','bitrate','format']:			
					#print 'frame3 generation-2-2',c
					frame_table_content = frame_table_content + ' <td>'
					frame_table_content = frame_table_content + '<br>'
					try:
						if c in modelDic ['CastPlayListD']['metaD'][a]:
							if frame_l.index(a)==1 :
								if   c == 'album' and 'NA_' not in modelDic['CastPlayListD']['metaD'][a][c]:
									#print "############## album begin"
									album_tag_navi_href_elem = modelDic['Tmpl']['album_tag_navi_href_elem']['TMPL']%(
										{'value':modelDic['CastPlayListD']['metaD'][a]['album_crc32'],'text':modelDic['CastPlayListD']['metaD'][a][c]})
									frame_table_content = frame_table_content + album_tag_navi_href_elem
									view_elem_id_Dic['image_crc32'] = str(modelDic['CastPlayListD']['metaD'][a]['album_crc32'])
									#print "##############album OK"
								elif c == 'artist'  and 'NA_' not in modelDic['CastPlayListD']['metaD'][a][c]:	
									artist_tag_navi_href_elem = modelDic['Tmpl']['artist_tag_navi_href_elem']['TMPL']%(
										{'value':modelDic['CastPlayListD']['metaD'][a]['artist_crc32'],'text':modelDic['CastPlayListD']['metaD'][a][c]})
									frame_table_content = frame_table_content + artist_tag_navi_href_elem
									
								elif c == 'title'  and 'NA_' not in modelDic['CastPlayListD']['metaD'][a][c]:	

									title_tag_navi_href_elem = ''		
									for tag in tagsL:
										if tag in TagD:
											if TagD[tag]['tag_type'] == 'SONG':
												#print TagD[tag]
																								
												title_tag_navi_href_elem = modelDic['Tmpl']['title_tag_navi_href_elem']['TMPL']%(
													{'value':str(tag),'class':"",'text':modelDic['CastPlayListD']['metaD'][a][c]})	
												break
												
									if title_tag_navi_href_elem == '':				
										title_tag_navi_href_elem = str(modelDic['CastPlayListD']['metaD'][a][c])
										
									frame_table_content = frame_table_content + title_tag_navi_href_elem	
									
								else:		
									frame_table_content = frame_table_content + str(modelDic['CastPlayListD']['metaD'][a][c])
							else: 
								frame_table_content = frame_table_content + str(modelDic['CastPlayListD']['metaD'][a][c])
						#print '1-ok','-->',mp3L.index(a)
					except UnicodeEncodeError:	
						try:
							s = ''.join([chr(ord(b)) for b in modelDic['CastPlayListD']['metaD'][a][c]])
							frame_table_content = frame_table_content +s.decode('cp1251').encode('utf8')
							#print '2-ok','-->',mp3L.index(a)
						except ValueError:
							try:
								#print 'b=',b,mp3L.index(a),a
								frame_table_content = frame_table_content + modelDic['CastPlayListD']['metaD'][a][c].encode('utf8')
							except Exception as e:
								frame_table_content = frame_table_content +"N/A"+c 
								logger.critical('Encoding exception:%s'%str(e))
								
			
					frame_table_content = frame_table_content + '</td>\n'
				
				frame_table_content = frame_table_content + '</tr>\n'
				
				logger.debug("frame3 - 3 OK %s"%str(elem_id))
				view_elem_id_Dic['cast_frame3'][elem_id] = frame_table_content.encode('base64')
				logger.debug("frame3 - 3  OK final")
			
		if 'tagsAllL' in view_elem_id_Dic:
			TagD = modelDic['TagD']
			#print 'TagD:',TagD
			tagL = []
			try:
				#print 'tagAllL--2'
				tagL=[(TagD[a]['tag_name'],a) for a in TagD if 'tag_name' in TagD[a]]
				#print 'tagAllL--2'
				tagL.sort() 
				#print 'tagAllL--3'
				tagL = [a[1] for a in tagL]
				#print 'tagAllL--4'
			except Exception as e:
				tagL = []
				
				logger.critical('Error in tagL rendering of ajax_main_page_update:%s'%str(e))
			TagResL = []
			
			#print 	'tagAllL geneta 1'	
			
			form_mode =  ''
			
			tags_num = len(tagL)	
			tag_ancor = ''
			
			
			for a in tagL:
				opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a),'selected':'','text':TagD[a]['tag_name'].encode('utf8')})
				#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
				TagResL.append(opt_elem)
			
			view_elem_id_Dic['tagsAllL'] = '\n'.join(TagResL)				
			
			logger.debug("tagsAllL - OK")
		


		
		
		# ВНИМАНИЕ!!! При генерации списков первый и последний элементы это опредение списка, это определение не нужно,
		# но по причине бага в Хроме и невозможности сделать замету по DIV мы вынуждены делать замену по ID SELECT
		
		# Общаая подготовка данных для списка альбомов и списка треков	
		if 'trackL'	 in view_elem_id_Dic or 'albumL' in view_elem_id_Dic:
			albumD = modelDic['cast_albumD']
			playerStatus = {'curAlbumIndx':0,'curTrackIndx':0,'curPlayListIndx':0}
			playerStatus['curTrackIndx'] = songNum

			albumL = [(albumD[b]['firstFileIndex'],albumD[b]['album']) for b in albumD]
			albumL.sort()

			tL = [b[0] for b in albumL if playerStatus['curTrackIndx'] >= b[0]]
			if tL == []:
				playerStatus['curAlbumIndx'] = 0
			else:
				playerStatus['curAlbumIndx'] = [b[0] for b in albumL if playerStatus['curTrackIndx'] >= b[0]][-1]

			l = [a for a in albumD if albumD[a]['firstFileIndex'] ==playerStatus['curAlbumIndx']]
			if l != []:
				albumKey = l[0]
			else:	
				albumKey = 0
				
			
			logger.debug("trackL albumL - OK")
			
			
		if 'albumL' in view_elem_id_Dic:	
			# Генерируем данные для списка альбомов
			
			#albumResL.append("""  <SELECT NAME="getAlbum" id="getAlbum">""")
			for a in albumL:
				#r_line = str2_RusLine(a[1],60)	

				
				class_color_ddl = "mp3_color"
				
				
				if a[0] == playerStatus['curAlbumIndx']:
					selected = 'selected'
				else:
					selected = ''
				try:	
					opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':class_color_ddl,'value':a[0],'selected':selected,
																			'text':a[1]})
				except Exception as e:
					
					logger.critical('Error in templating AlbumL in mainview:%s%s'%(str(e),str(list(modelDic.keys()))))
					opt_elem = "Error in templating AlbumL in mainview",list(modelDic.keys())
					
					
				albumResL.append(opt_elem)
			
			view_elem_id_Dic['albumL'] =  '\n'.join(albumResL).encode('base64')	
			
			logger.debug("albumL - OK")
			
			
			
			
			
			
			
		
		if 'trackL' in view_elem_id_Dic:	
			# Генерируем данные для списка треков
			
			if albumKey in albumD:
				for a in albumD[albumKey]['albumL']:
					index = albumD[albumKey]['albumL'].index(a)+1
					opt_elem = ''
					#r_line = str2_RusLine(a[0],90)
					title = str(index)+'.'+a[0]
			
					if 'cue' not in albumD[albumKey]:
						if a[1] == playerStatus['curTrackIndx']:
							selected = 'selected'	
						else:
							selected = ''
							
						try:	
							opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':title})
						except:
							opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':title})

					else:
						if a[1] == playerStatus['curTrackIndx']:
							selected = 'selected'	
						else:
							selected = ''	
						opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':a[1],'selected':selected,'text':title})	
						
					#print 	'opt_elem=',opt_elem
					trackResL.append(opt_elem)	
						
			else:
				trackResL = []
			view_elem_id_Dic['trackL'] =  '\n'.join(trackResL).encode('base64')	
			
			logger.debug("trackL  - OK")
		
		
		
		
	# Current Track CRC32
		if 'local' in args:
			
			logger.debug("in local modus part")
			return view_elem_id_Dic
		try:	
			json_reply = json.dumps(view_elem_id_Dic)
		except Exception as e:
			logger.critical('Exception at json_reply = json.dumps(view_elem_id_Dic):%s'%str(e))
			logger.critical('Exception at json_reply = json.dumps(view_elem_id_Dic):%s'%str(list(view_elem_id_Dic.keys())))
			json_reply = json.dumps(view_elem_id_Dic)
		#if 'frame3' in view_elem_id_Dic:
		#	for a in view_elem_id_Dic['frame3']:
		#		del view_elem_id_Dic['frame3'][a]
		#	view_elem_id_Dic['frame3'] = ''
		
		logger.debug("ajax_cast_page_update  - OK")
		return json_reply	
		
	def send_HtmlPage_info(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):		
		
		logger.info('And now!!! we are in send_HtmlPage_info')
		bookmark_part = ''
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		#print('info geneta 2')
		menu_selD['info_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		#print('info geneta 3')
		info_tmpl = modelDic['Tmpl']['info_tmpl']['TMPL']
		
		#print('info geneta 4')
		page = modelDic['Tmpl']['info_page']['TMPL']%({'bookmark_tmpl':bookmark_part,
														'info_tmpl':info_tmpl,
														'host_name':modelDic['host_name'],
														'html_title':html_title,
														'host':modelDic['host']
														})		
		
		#print('info geneta 6'+str(type(page)))	
		page = bytes(page,encoding = "utf-8")
		logger.debug("info page generation finished - OK")
		return xmlrpc.client.Binary(page)
		
	def send_HtmlPage_graf(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):		
		
		logger.info('in send_HtmlPage_graf %s  modeldic.keys: %s'%(str(view_elem_id_Dic),str(list(modelDic.keys()))))
		
		bookmark_part = ''
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		
		logger.debug('graf geneta 2')
		menu_selD['graf_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		
		#graf_tmpl = modelDic['Tmpl']['graf_tmpl']['TMPL'].decode('cp1251').encode('utf8')
		
		#print 	'graf geneta 4:',modelDic['Tmpl']['graf_page'].keys()
		page = modelDic['Tmpl']['graf_page']['TMPL']%({'bookmark_tmpl':bookmark_part,
														#'graf_tmpl':graf_tmpl,
														'host_name':modelDic['host_name'],
														'html_title':html_title,
														'host':modelDic['host']
														})		
		
		logger.debug('graf geneta OK')	
		page = bytes(page,encoding = "utf-8")
		logger.debug("graf page generation finished - OK")
		return xmlrpc.client.Binary(page)	
		
	def send_HtmlPage_admin(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):		
		logger.info('And now!!! we are in send_HtmlPage_admin')
		
		bookmark_part = ''
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		page = 'admin page  '
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary

		
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		

		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		print('admin geneta 2')
		menu_selD['admin_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		print('admin geneta 3')
		
		pic_get_text = 'Если картинки нет, введите урл картинки, например с амазона'
		template_list_content = ''
		radio_stat_lst = ''
		templ_selL = []
		for a in modelDic['templatesD']:
			if modelDic['templatesD'][a]['active'] == True:
				templ_selL.append("""<OPTION  VALUE= "%s" selected> %s </option>\n"""%(a,modelDic['templatesD'][a]['templatesPath']))		
			else:
				templ_selL.append("""<OPTION  VALUE= "%s" > %s </option>\n"""%(a,modelDic['templatesD'][a]['templatesPath']))		
				
		print('admin geneta 4')
		template_list_content =  '\n'.join(templ_selL)	
		
		
		StatResL = []
		for a in modelDic['radio_statDL']:
			try:
				opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a['key']),'selected':'','text':a['station_name']})
			except:
				print("""Erorr in radio_statL[a]['tag_name'] index:""",a)	
				continue
				
			StatResL.append(opt_elem)
		radio_stat_lst = '\n'.join(StatResL)		
		
		mpd_instance_lst = ""
		MPDResL = []
		for a in modelDic['mpd_instanceDL']:
			try:
				opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a['key']),'selected':'','text':a['instance_name']})
			except:
				print("""Error in mpd_instanceL[a] index:""",a)	
				continue
				
			MPDResL.append(opt_elem)	
		mpd_instance_lst = '\n'.join(MPDResL)		
		
		print('admin geneta 5')
		template_encoded = ''
		#try:
		#	code_schema = chardet.detect(modelDic['Tmpl']['admin_page']['TMPL'])['encoding']
		#except Exception, e:
		#	page = err_msg = 'Error: in send_HtmlPage_admin template encoding 1 [%s]'%(str(e))
		#	logger.critical(err_msg)
			
		#print code_schema
		
		#try:
		#	template_encoded = modelDic['Tmpl']['admin_page']['TMPL'].decode(code_schema)
		#except Exception, e:
		#	page = err_msg = 'Error: in send_HtmlPage_admin template encoding [%s]'%(str(e))
		#	logger.critical(err_msg)
		
		try:
			radio_stat_lst = radio_stat_lst.encode('utf8')
		except Exception as e:
			page = err_msg = 'Error: in send_HtmlPage_admin template encoding [%s]'%(str(e))
			
		try:
			page = Template(modelDic['Tmpl']['admin_page']['TMPL']).substitute({'bookmark_tmpl':bookmark_part,
														'host_name':modelDic['host_name'],
														'html_title':html_title,
														'pic_get_text':pic_get_text,
														'radio_stations_exist_l':radio_stat_lst,
														'mpd_instance_l':mpd_instance_lst,
														'host':modelDic['host'],
														'template_select_list':template_list_content })		
		except Exception as e:
			err_msg = 'Error: in send_HtmlPage_admin [%s]'%(str(e))
			logger.critical(err_msg)
			d = pickle.dumps(view_elem_id_Dic)
			f = open('debug.dat','w')
			f.write(d)
			f.close()
			page += err_msg+str([radio_stat_lst])
		
		print('admin geneta 6')	
		page = bytes(page,encoding = "utf-8")
		logger.debug("admin page generation finished - OK")
		return xmlrpc.client.Binary(page)	
		
	def send_HtmlPage_debug(self,PlayControl_CurStatusD,view_elem_id_Dic,dummy_2,modelDic):		
		logger.info('And now!!! we are in send_HtmlPage_debug')
		
		bookmark_part = ''
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		

		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		#print 	'debug geneta 2'
		menu_selD['admin_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		debug_data = ''
		#print 	'debug geneta 3'
		debug_data = debug_data + "#################### <BR>"
		debug_data = debug_data +'<BR>' + 'modelDic.keys(): ' + str(list(modelDic.keys())) + '<BR>'
		debug_data = debug_data + "#################### <BR>"
		debug_data = debug_data + 'view_elem_id_Dic.keys():' + str(list(view_elem_id_Dic.keys())) + '<BR>'
		debug_data = debug_data + "#################### <BR>"
		debug_data = debug_data + "### TEMPLATES:  ##### :" +str(list(modelDic['Tmpl'].keys())) + '<BR>'
		debug_data = debug_data + "#################### <BR>"
		#if 'curState' in view_elem_id_Dic:
		#	debug_data = debug_data +'<BR>' + 'current player status: ' + str(view_elem_id_Dic['curState']) + '<BR>'
		#if 'play_status' in view_elem_id_Dic:
		debug_data = debug_data +'<BR>' + 'current player status: ' + str(PlayControl_CurStatusD) + '<BR>'	
		debug_data = debug_data + "#################### <BR>"
		ignorL = ['Tmpl','debugD']
		
		for a in modelDic:
			if a in ignorL:
				continue
			debug_data = debug_data + "%s <input height='27' width='36' class='debug_check' type='checkbox' name='%s' value='%s'> <BR>"%(str(a),str(a),str(a))
		#for a in modelDic:
		#	if a in ignorL:
		#		continue
		#	debug_data = debug_data + "#################### <BR>"	
		#	debug_data = debug_data + 'Getting '+ str(a)  + '<BR>'
		#	debug_data = debug_data + "#################### <BR>"	
		#	try:
				#print view_elem_id_Dic[a]
				#debug_data = debug_data + str(modelDic[a]) + '<BR>'
		#		pass
		#	except:
				#print 'Error at:' + str(a)
		#		debug_data = debug_data + 'Error at:' + str(a) + '<BR>'
		logger.debug('debug geneta 4')
		template_list_content = ''
		
		
		page = modelDic['Tmpl']['debug_page']['TMPL']%({'bookmark_tmpl':bookmark_part,
														'host_name':modelDic['host_name'],
														'html_title':'Media Lib tag admin',
														'pic_get_text':'',
														'host':modelDic['host'],
														'debug_data':debug_data})		
		
		logger.debug('debug geneta OK')
		page = bytes(page,encoding = "utf-8")
		logger.debug("info page generation finished - OK")
		return xmlrpc.client.Binary(page)
	def send_HtmlPage_tagAdmin_new(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('in send_HtmlPage_tagAdmin_new - Start')
		

		search_term = 'Search_text'
		if_chosen_elem = ''
		search_part_tmpl = ''
		sel_option_js_content_list = ''
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		
		#print 	'tagAdmin geneta 1'	
		
		
		#bookmark_part = pageConfigD['bookmark_part']
		bookmark_part = '<BR>'
		#print 	'tagAdmin geneta 1'	
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		menu_selD['tag_admin_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		print('tagAdmin geneta 2')			
			
		tagD =  modelDic['TagD']
		
		tagL = []
		try:
			tagL=[(tagD[a]['tag_name'],a) for a in tagD if 'tag_name' in tagD[a]]
			tagL.sort() 
			
			tagL = [a[1] for a in tagL]
		except:
			tagL = []
			print('Error in tagL rendering of send_HtmlPage_tagAdmin_new')
			
		tagGrD = {}

			
		TagResL = []
		
		print('tagAdmin geneta 3')
		
		form_mode =  ''
		
		tags_num = len(tagL)
		
		tag_ancor = ''
		
		js_tag_group_list = ''
		# получаем все группы тэгов
		tagGroupL = []
		for a in tagL:
			if tagD[a]['tag_type'] not in tagGroupL:
				if 'tag_type' in tagD[a]:
					tagGroupL.append(tagD[a]['tag_type'])

		
		page = ''
			
		print('tagAdmin geneta 4')
		
		# При начальной загрузке результаты поиска пустые
		try:
			search_part_tmpl = modelDic['Tmpl']['tag_adm_part_tmpl']['TMPL']%({'res_lenth':'0','search_res_list':''})	
		except:
			print("""Erorr in modelDic['Tmpl']['tag_adm_part_tmpl']""")
			search_part_tmpl = ''
		
		#html_title = u'Удаленная смотрелка-управлялка играющей музыки'
		
		variableD =	{'bookmark_tmpl':bookmark_part,
													'host_name':modelDic['host_name'],
													'html_title':html_title,
													'search_part_tmpl':search_part_tmpl,
													'search_text':'Search_text',
													'host':modelDic['host'],
													'tag_list_content':'',
													'tags_num':tags_num,
													'tag_ancor':tag_ancor,
													'form_mode':form_mode}
													
		#page = template_process(modelDic,'tag_adm_page',variableD)	
		print('tagAdmin geneta 5') 
		#codec = chardet.detect(modelDic['Tmpl']['tag_adm_page']['TMPL'])	
		#print(codec)
		tag_adm_template = modelDic['Tmpl']['tag_adm_page']['TMPL']
		print('Geneta 6.1')
		try:
			page = tag_adm_template%variableD
		except Exception as e :	
			logger.critical('Error: in send_HtmlPage_tagAdmin_new - %s'%(str(e)))	
		
		print('tagAdmin geneta 7')	
		page = bytes(page,encoding = "utf-8")
		logger.debug("tag admin page generation finished - OK")
		logger.info('in send_HtmlPage_tagAdmin_new - Finished')
		return xmlrpc.client.Binary(page)
		

	def send_HtmlPage_track_preload(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('And now!!! we are in send_HtmlPage_track_preload')

		
		for a in menu_selD:
			menu_selD[a]=''
			
		menu_selD['host_name']=modelDic['host_name']
		
		
		
		
		bookmark_part = ''
		logger.debug('image geneta 1')
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		
		
		menu_selD['track_preload_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		logger.debug('image geneta 2')			
			
		tagD =  modelDic['TagD']
		
		tagL = []
		try:
			tagL=[(tagD[a]['tag_name'],a) for a in tagD if 'tag_name' in tagD[a]]
			tagL.sort() 
			tagL = [a[1] for a in tagL]
		except:
			tagL = []
			print('Error in tagL rendering of send_HtmlPage_tagAdmin_new')
		TagResL = []
		
		logger.debug('image geneta 3')			
		
		form_mode =  ''
		
		tags_num = len(tagL)
		
		tag_ancor = ''
		
		js_tag_group_list = ''
		# получаем все группы тэгов
		tagGroupL = []
		for a in tagD:
			if tagD[a]['tag_type'] not in tagGroupL:
				if 'tag_type' in tagD[a]:
					tagGroupL.append(tagD[a]['tag_type'])
		#for a in tagGroupL:
			
		
		#for a in tagL:
		#	opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a),'selected':'','text':tagD[a]['tag_name'].encode('utf8')})
			#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
		#	TagResL.append(opt_elem)
		#tag_list_content = '\n'.join(TagResL)	
		page = ''
			
		logger.debug('image geneta 4')				
		
		# При начальной загрузке результаты поиска пустые
		try:
			
			search_part_tmpl = modelDic['Tmpl']['search_part_new_tmpl']['TMPL']%({'res_lenth':'0','search_res_list':'','table_header':''})	
		except:
			print("""Erorr in modelDic['Tmpl']['search_part_new_tmpl']""")
			search_part_tmpl = ''
			
		scrpt_2_main = ''
		scrpt_2_mainL = []	
		
		logger.debug('image geneta 6')		
		
		page = modelDic['Tmpl']['track_preload_page']['TMPL']%({'bookmark_tmpl':bookmark_part,
													'host_name':modelDic['host_name'],
													'html_title':html_title,
													'search_part_new_tmpl':search_part_tmpl,
													'search_text':'Search_text',
													'host':modelDic['host'],
													
													'form_mode':form_mode})		
			
		page = bytes(page,encoding = "utf-8")
		logger.debug('track_preseltrack_presel geneta OK')			
		return xmlrpc.client.Binary(page)	
		
	def send_HtmlPage_image(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('And now!!! we are in send_HtmlPage_image')

		
		for a in menu_selD:
			menu_selD[a]=''
			
		menu_selD['host_name']=modelDic['host_name']
		
		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		#bookmark_part = pageConfigD['bookmark_part']
		bookmark_part = ''
		logger.debug('image geneta 1')
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		
		
		menu_selD['image_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		logger.debug('image geneta 2')			
			
		tagD =  modelDic['TagD']
		
		tagL = []
		try:
			tagL=[(tagD[a]['tag_name'],a) for a in tagD if 'tag_name' in tagD[a]]
			tagL.sort() 
			tagL = [a[1] for a in tagL]
		except:
			tagL = []
			print('Error in tagL rendering of send_HtmlPage_tagAdmin_new')
		TagResL = []
		
		logger.debug('image geneta 3')			
		
		form_mode =  ''
		
		tags_num = len(tagL)
		
		tag_ancor = ''
		
		js_tag_group_list = ''
		# получаем все группы тэгов
		tagGroupL = []
		for a in tagD:
			if tagD[a]['tag_type'] not in tagGroupL:
				if 'tag_type' in tagD[a]:
					tagGroupL.append(tagD[a]['tag_type'])
		#for a in tagGroupL:
			
		
		#for a in tagL:
		#	opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a),'selected':'','text':tagD[a]['tag_name'].encode('utf8')})
			#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
		#	TagResL.append(opt_elem)
		#tag_list_content = '\n'.join(TagResL)	
		page = ''
			
		logger.debug('image geneta 4')				
		
		# При начальной загрузке результаты поиска пустые
		try:
			
			search_part_tmpl = modelDic['Tmpl']['search_part_new_tmpl']['TMPL']%({'res_lenth':'0','search_res_list':'','table_header':''})	
		except:
			print("""Erorr in modelDic['Tmpl']['search_part_new_tmpl']""")
			search_part_tmpl = ''
			
		scrpt_2_main = ''
		scrpt_2_mainL = []	
		
		logger.debug('image geneta 6')		
		
		page = modelDic['Tmpl']['image_page']['TMPL']%({'bookmark_tmpl':bookmark_part,
													'host_name':modelDic['host_name'],
													'html_title':html_title,
													'search_part_new_tmpl':search_part_tmpl,
													'search_text':'Search_text',
													'host':modelDic['host'],
													
													'form_mode':form_mode})		
			
		
		logger.debug('image geneta OK')		
		page = bytes(page,encoding = "utf-8")
		logger.debug("image page generation finished - OK")	
		return xmlrpc.client.Binary(page)	
	def send_HtmlPage_search_new(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):
		
		logger.info('And now!!! we are in send_HtmlPage_search_new')

		search_term = 'Search_text'.encode('utf8')
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		
		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		#bookmark_part = pageConfigD['bookmark_part']
		bookmark_part = ''
		logger.debug('search geneta 1')
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
		
		menu_selD['search_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		logger.debug('search geneta 2')			
			
		tagD =  modelDic['TagD']
		
		tagL = []
		try:
			tagL=[(tagD[a]['tag_name'],a) for a in tagD if 'tag_name' in tagD[a]]
			tagL.sort() 
			tagL = [a[1] for a in tagL]
		except:
			tagL = []
			print('Error in tagL rendering of send_HtmlPage_tagAdmin_new')
		TagResL = []
		
		logger.debug('search geneta 3')			
		
		form_mode =  ''
		
		tags_num = len(tagL)
		
		tag_ancor = ''
		
		js_tag_group_list = ''
		# получаем все группы тэгов
		tagGroupL = []
		for a in tagD:
			if tagD[a]['tag_type'] not in tagGroupL:
				if 'tag_type' in tagD[a]:
					tagGroupL.append(tagD[a]['tag_type'])
		#for a in tagGroupL:
			
		
		#for a in tagL:
		#	opt_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a),'selected':'','text':tagD[a]['tag_name'].encode('utf8')})
			#TagResL.append("""<OPTION VALUE="%s" > %s"""%(str(a),tagD[a]['tag_name'].encode('utf8')))
		#	TagResL.append(opt_elem)
		#tag_list_content = '\n'.join(TagResL)	
		page = ''
			
		logger.debug('search geneta 4')				
		
		# При начальной загрузке результаты поиска пустые
		try:
			
			search_part_tmpl = modelDic['Tmpl']['search_part_new_tmpl']['TMPL']%({'res_lenth':'0','search_res_list':'','table_header':''})	
		except:
			print("""Erorr in modelDic['Tmpl']['search_part_new_tmpl']""")
			search_part_tmpl = ''
			
		scrpt_2_main = ''
		scrpt_2_mainL = []	
		
		logger.debug('search geneta 6')		
		
		page = modelDic['Tmpl']['search_page_new']['TMPL']%({'bookmark_tmpl':bookmark_part,
													'host_name':modelDic['host_name'],
													'html_title':html_title,
													'search_part_new_tmpl':search_part_tmpl,
													'search_text':'Search_text',
													'host':modelDic['host'],
													
													'form_mode':form_mode})		
			
		
		logger.debug('search geneta OK')
		page = bytes(page,encoding = "utf-8")
		logger.debug("search new page generation finished - OK")
		return xmlrpc.client.Binary(page)
		
	def send_HtmlPage_reports(self,dummy_1,view_elemD,dumy_2,modelDic):

		logger.info('in send_HtmlPage_reports: %s  modeldic.keys: %s'%(str(view_elemD),str(list(modelDic.keys()))))
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']

		#html_title = 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
			
		menu_selD['reports_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		
		
		#logger.info('report 1.2')			
		TmplD = modelDic['Tmpl']
		#logger.info('report 2')
		
		
		page = ''
		report_part_tmpl = ''
		
		report_part_tmpl = ''
		search_term = 'Search_text'
			
		#logger.info('report 4')
			
		
		if 'runReport' in view_elemD:
		
			if 'search_term' in ReportBufD:
				search_term = myMediaLib_model.str2_RusLine(ReportBufD['search_term'],0)
				search_term = search_term.encode('utf8')
			else:
				search_term = ''
				
			#print view_elemD['page_mode'],view_elemD['runReport']
			if  'ArtistStat' in view_elemD['runReport'] and ReportBufD != {}:
				print('report 5','ReportBufD:',len(ReportBufD),list(view_elemD.keys()))
				art_stat_D = {}
				art_stat_D = ReportBufD
					
		#		print 'report 5'
				report_res_list = ''
				report_part_tmpl = ''
								
			
				res_lenth = len(art_stat_D['statL'])
				album_cnt = 0
				albumL = []
				for a in art_stat_D['statL']:
					if 'albumD' in art_stat_D['artistD'][a[3]]:
						alb_crc32 = art_stat_D['artistD'][a[3]]['albumD']['album_crc32']
						if alb_crc32 not in albumL:
							albumL.append(alb_crc32)	
				album_cnt = len(albumL)			
				del(albumL)
			
			
		#		print 'res_lenth',res_lenth
				if res_lenth == 0:
					report_res_list = ''
					report_part_tmpl = ''
				else:
					 
					report_res_list = prepareArtistOveralReport(art_stat_D['statL'],art_stat_D['artistD'],art_stat_D['ref_artL'],modelDic)	
					#print 'report_res_list='

							
			#			search_res_list = ''
				#print "Album num:",album_cnt
				notFoundL = [a for a in ReportBufD['search_termL'] if a not in ReportBufD['foundL']]
				
				report_part_tmpl = TmplD['report_part_tmpl']['TMPL']%({'res_lenth':res_lenth,'album_num':album_cnt,'info_str':'not found:'+str(notFoundL),'report_res_list':report_res_list})		
				#search_part_tmpl = ''
				
		
				
		# Вызываем шаблонизатор	
		#json.dumps(folderD)
		variableD =	{'bookmark_tmpl':bookmark_part,	'host_name':modelDic['host_name'],'html_title':html_title,'report_part_tmpl':report_part_tmpl,
					'search_text':search_term,'host':modelDic['host']}
		page = template_process(modelDic,'reports_page',variableD)		

		page = bytes(page,encoding = "utf-8")
		logger.debug("reports page generation finished - OK")		
		return xmlrpc.client.Binary(page)					
		
	def send_HtmlPage_main(self,PlayControl_CurStatusD,view_elem_id_Dic,modelStateDic,modelDic):	
		for a in menu_selD:
			menu_selD[a]=''
		menu_selD['host_name']=modelDic['host_name']
		logger.info('in send_HtmlPage_main: %s PlayControl_CurStatusD=%s modeldic.keys: %s'%(str(view_elem_id_Dic),str(PlayControl_CurStatusD),str(list(modelDic.keys()))))
		try:
			view_elem_id_Dic = self.ajax_main_page_update(PlayControl_CurStatusD,view_elem_id_Dic,modelStateDic,modelDic,'local')
		except Exception as e:
	
			logger.critical("Exception in ajax_main_page_update:%s"%str(e))
			return 0
			
		
		bookmark_part = ''
		buttons_part = ''
		hard_tags = ''
		html_title = ''
		refresh_time = ''
		frame_table_content = ''
		cntrl_lists_part = ''
		cur_list_name = ''
		scrpt_2_main = ''
		scrpt_1_line = ''
		tagsAllL_content = ''
		scrpt_2_main_tag = ''
		time_stamp = [0,0]
		
		album_list_content = ''
		track_list_content = ''
		group_list_content = ''
		pl_list_content = ''
		plist_queue_content = ''
		
		
		
		# 01---> html_title 
		if  PlayControl_CurStatusD['playBack_Mode'] == 1:
			play_status = 'Playing.'
		elif  PlayControl_CurStatusD['playBack_Mode'] == 3:	
			play_status = 'Paused.'
		elif  PlayControl_CurStatusD['playBack_Mode'] == 0:		
			play_status = 'Stopped.'
		else:
			play_status = 'Undef'
		#html_title = play_status + 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		html_title =  'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		# 02---> frame3 
		if 'frame3' in view_elem_id_Dic:
			l = [a for a in view_elem_id_Dic['frame3']]
			l.sort()
			for a in l:
				frame_table_content = frame_table_content + view_elem_id_Dic['frame3'][a].decode('base64')+'\n'
		

		# 03---> Формирование управляющих списков
		list_grp2_title =  'Выбор плейлиста с сервера. Плейлистов:'.decode('cp1251').encode('utf8')
		list_grp1_title =  'Управление текущим плейлистом на сервере. Альбомов:'.decode('cp1251').encode('utf8')
			
		
		if 'albumL' in view_elem_id_Dic:	
			album_list_content = view_elem_id_Dic['albumL']
		
		if 'trackL' in view_elem_id_Dic:		
			track_list_content = view_elem_id_Dic['trackL']
			
		if 'queueL' in view_elem_id_Dic:		
			plist_queue_content	= view_elem_id_Dic['queueL']
		
		if 'plist_groupL' in view_elem_id_Dic:		
			group_list_content	= view_elem_id_Dic['plist_groupL']
			
		if 'lib_plistL'	in view_elem_id_Dic:		
			pl_list_content	= view_elem_id_Dic['lib_plistL']
			
		if 'jscript_plist_groupL'	in view_elem_id_Dic:		
			scrpt_2_main_plist = view_elem_id_Dic['jscript_plist_groupL']
		
		if 'jscript_tag_typeL'	in view_elem_id_Dic:		
			scrpt_2_main_tag = view_elem_id_Dic['jscript_tag_typeL']	
		if 'tagsAllL'	in view_elem_id_Dic:	
			tagsAllL_content = view_elem_id_Dic['tagsAllL']	
			#print 'tagsAllL_content:',tagsAllL_content
			
		#group_list_content = '\n'.join(listContentD['groupResL'])
		#pl_list_content = '\n'.join(listContentD['plistResL'])
		
		album_num = """<SPAN id="album_numb"> %s </SPAN>"""%(str(0))
		
		try:
			cntrl_lists_part = modelDic['Tmpl']['cntrl_lists_tmpl']['TMPL']%({'list_grp1_title':list_grp1_title,
																			'list_grp2_title':list_grp2_title,
																			'album_list_content':album_list_content,
																			'track_list_content':track_list_content,
																			'group_list_content':group_list_content,
																			'pl_list_content':pl_list_content,
																			'plist_queue_content':plist_queue_content,
																			'album_num':album_num,
																			'tagsAllL_content':tagsAllL_content})	
		except Exception as e:
			logger.critical('Error in cntrl_lists_tmpl:%s'%str(e))
			
			
		
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		#main_sel = search_sel = admin_sel = info_sel = reports_sel =  tag_admin_sel = graf_sel = ''  
		#menu_selD = {'host_name':modelDic['host_name'],'main_sel':'','search_sel':'','admin_sel': '','info_sel':'','reports_sel':'','tag_admin_sel':'','graf_sel':''}
			
		print('main geneta 2')
		menu_selD['main_sel'] = """ class="selected" """
		bookmark_part = modelDic['Tmpl']['bookmark_tmpl']['TMPL']%(menu_selD)
		
		print('main geneta 3')
		if 'tagsL' in view_elem_id_Dic:
			
			logger.debug('hard_tags OK')
			hard_tags = view_elem_id_Dic['tagsL']
			
		# Заполняем значение для имени плейлиста
		if PlayControl_CurStatusD['pL_CRC32'] in modelDic['pD_crc32']:
			#print PlayControl_CurStatusD['pL_CRC32'],self.__pD_crc32
			cur_list_name = modelDic['pD_crc32'][PlayControl_CurStatusD['pL_CRC32']]['title'].encode('utf8')
		else:
			cur_list_name = """PlayList << Неизвестный  >>""".decode('cp1251').encode('utf8')

				
		buttons_part = modelDic['Tmpl']['player_buttons_tmpl']['TMPL']%({'hard_tags':hard_tags})
		
		main_script = ''
		
		try:
			main_script = modelDic['Tmpl']['scrpt_main']['TMPL']%({'my_sec':str(int(time_stamp[1])),
													'my_min':time_stamp[0],
													'host':modelDic['host'],
													'html_title':html_title,
													'scrpt_2_main_plist':scrpt_2_main_plist,
													'scrpt_2_main_tag':scrpt_2_main_tag
													})
		except:
			#print modelDic['Tmpl']['scrpt_main']['TMPL']
			print(modelDic['Tmpl']['scrpt_main']['TMPL'][:modelDic['Tmpl']['scrpt_main']['TMPL'].find('scrpt_1_line')+100])
			print('Erororor!!!!!!!!!!!!!!!!!',modelDic['Tmpl']['scrpt_main']['TMPL'].find('scrpt_1_line'),scrpt_1_line)
		
		if 'image_crc32' in view_elem_id_Dic:
			image_name = str(view_elem_id_Dic['image_crc32'])+'.jpg',
		else:
			image_name = 'noname.jpg'
		
		
		
		logger.debug('main geneta 4')
		
		tmplContentD = {'scrpt_main':main_script,
								'bookmark_tmpl':bookmark_part, # OK
								'cur_list_name':cur_list_name, # OK
								'player_buttons_tmpl':buttons_part, # OK
								'refresh_time':refresh_time, # OK
								'host_name':modelDic['host_name'], # OK
								'host':modelDic['host'], # OK
								'host_image_name':modelDic['host_image_name'], # OK
								'html_title':html_title, # OK
								't_song':""" Композиция""".decode('cp1251').encode('utf8'),
								't_actor':""" Исполнитель """.decode('cp1251').encode('utf8'),
								't_album':""" Альбом """.decode('cp1251').encode('utf8'),
								't_time':""" Время """.decode('cp1251').encode('utf8'),
								't_bitrate':""" Битрейт """.decode('cp1251').encode('utf8'),
								't_format':""" Формат """.decode('cp1251').encode('utf8'),
								'frame_table_content':frame_table_content, # OK
								'image_crc32':image_name,
								'cntrl_lists_tmpl':cntrl_lists_part} # OK
		
		print('main geneta 5')
		page = modelDic['Tmpl']['main_page']['TMPL']%(tmplContentD)
		#print 	'main geneta 6'	
		return xmlrpc.client.Binary(page)
		
	def send_HtmlPage_cast(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):	
		
		logger.info('in send_HtmlPage_cast %s  modeldic.keys: %s'%(str(view_elem_id_Dic),str(list(modelDic.keys()))))
		try:
			view_elem_id_Dic = self.ajax_cast_page_update(dummy_1,view_elem_id_Dic,dummy_2,modelDic,'local')
			
		except Exception as e:
			logger.critical('Error in ajax_cast_page_update:%s'%str(e))
			
			return 0
			
		
		bookmark_part = ''
		buttons_part = ''
		hard_tags = ''
		html_title = ''
		refresh_time = ''
		frame_table_content = ''
		cntrl_lists_part = ''
		cur_list_name = ''
		scrpt_2_main = ''
		scrpt_1_line = ''
		tagsAllL_content = ''
		scrpt_2_main_tag = ''
		time_stamp = [0,0]
		
		album_list_content = ''
		track_list_content = ''
		group_list_content = ''
		pl_list_content = ''
		plist_queue_content = ''
		
		#print 	'main geneta 1'	
		
		# 01---> html_title 
	
		#html_title = play_status + 'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		html_title =  'Удаленная смотрелка-управлялка играющей музыки'.decode('cp1251').encode('utf8')
		
		# 02---> frame3 
		if 'frame3' in view_elem_id_Dic:
			l = [a for a in view_elem_id_Dic['frame3']]
			l.sort()
			for a in l:
				frame_table_content = frame_table_content + view_elem_id_Dic['cast_frame3'][a].decode('base64')+'\n'
		

		# 03---> Формирование управляющих списков
		list_grp2_title =  'Выбор плейлиста с сервера. Плейлистов:'.decode('cp1251').encode('utf8')
		list_grp1_title =  'Управление текущим плейлистом на сервере. Альбомов:'.decode('cp1251').encode('utf8')
			
		
		if 'albumL' in view_elem_id_Dic:	
			album_list_content = view_elem_id_Dic['albumL']
		
		if 'trackL' in view_elem_id_Dic:		
			track_list_content = view_elem_id_Dic['trackL']
			
		if 'queueL' in view_elem_id_Dic:		
			plist_queue_content	= view_elem_id_Dic['queueL']
		
		if 'plist_groupL' in view_elem_id_Dic:		
			group_list_content	= view_elem_id_Dic['plist_groupL']
			
		if 'lib_plistL'	in view_elem_id_Dic:		
			pl_list_content	= view_elem_id_Dic['lib_plistL']
			
		if 'jscript_plist_groupL'	in view_elem_id_Dic:		
			scrpt_2_main_plist = view_elem_id_Dic['jscript_plist_groupL']
		
		if 'jscript_tag_typeL'	in view_elem_id_Dic:		
			scrpt_2_main_tag = view_elem_id_Dic['jscript_tag_typeL']	
		if 'tagsAllL'	in view_elem_id_Dic:	
			tagsAllL_content = view_elem_id_Dic['tagsAllL']	
			#print 'tagsAllL_content:',tagsAllL_content
			
		#group_list_content = '\n'.join(listContentD['groupResL'])
		#pl_list_content = '\n'.join(listContentD['plistResL'])
		
		album_num = """<SPAN id="album_numb"> %s </SPAN>"""%(str(0))
			#print "Main 6 Ok"
		
			
		
		# 00 ---> Menue Definition: for the new page add here the new bookmarks and menue dictionary
		
			
		#print 	'main geneta 2'
		
		
		#print 	'main geneta 3'
		if 'tagsL' in view_elem_id_Dic:
			
			logger.info( 'hard_tags OK')
			hard_tags = view_elem_id_Dic['tagsL']
			
		# Заполняем значение для имени плейлиста
		
		
		main_script = ''
		
		
		
		if 'image_crc32' in view_elem_id_Dic:
			image_name = str(view_elem_id_Dic['image_crc32'])+'.jpg',
		else:
			image_name = 'noname.jpg'
		
		
		logger.info('send_HtmlPage_cast 4 ')
		tmplContentD = {
								
								
								'host_name':modelDic['host_name'], # OK
								'host':modelDic['host'], # OK
								'host_image_name':modelDic['host_image_name'], # OK
								'html_title':html_title, # OK
								't_song':""" Композиция""".decode('cp1251').encode('utf8'),
								't_actor':""" Исполнитель """.decode('cp1251').encode('utf8'),
								't_album':""" Альбом """.decode('cp1251').encode('utf8'),
								't_time':""" Время """.decode('cp1251').encode('utf8'),
								't_bitrate':""" Битрейт """.decode('cp1251').encode('utf8'),
								't_format':""" Формат """.decode('cp1251').encode('utf8'),
								'hard_tags':hard_tags,
								'image_crc32':"image_name",
								
								'tagsAllL_content':tagsAllL_content}

								# OK
		
		logger.info('send_HtmlPage_cast 5 ')
		try:
			page = modelDic['Tmpl']['cast_page']['TMPL']%(tmplContentD)
		except KeyError as e:
			print('KeyError',e)
		except:
			page = str(tmplContentD)
			
		
		logger.info('send_HtmlPage_cast OK ')
		return xmlrpc.client.Binary(page)
	
	def send_ArtistEdit_form_new(self,dummy_1,view_elem_id_Dic,dummy_2,modelDic):
		logger.info('And now!!! we are in send_ArtistEdit_form_new %s view_elem_id_Dic:%s'%(str(list(modelDic.keys())),str(view_elem_id_Dic)))
		stop_list_punct = ['.',';','/','_','&','(',')','%','?','!',]
		stop_list_word = ['the','a']
		
		TmplD = modelDic['Tmpl']
		
		search_term = ''
		artist_name = ''
		ref_artist_list = ''
		rel_artist_list = ''
		main_checked_flag = modelDic['edit_artist_struc']['main_checked_flag']
		rel_artist_num = '0'
		
		host_name = modelDic['host_name']
		host = modelDic['host']
		html_title = modelDic['html_title']

		artist_name = modelDic['edit_artist_struc']['artist_name']
		search_term = modelDic['edit_artist_struc']['search_term']
			
		rel_artL = modelDic['edit_artist_struc']['rel_artL']
		ref_art_newL =  modelDic['edit_artist_struc']['ref_art_newL']			
		rel_artist_num = str(len(rel_artL))
		rel_artist_list = ''
		for a in rel_artL:
			variablD  = {'class':'no','value':str(a[0]),'selected':'','text':str(a[1])}
			rel_artist_list = rel_artist_list +  template_process(modelDic,'gen_dd_list_option_elem',variablD)		
			#rel_artist_list = rel_artist_list +  modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'no','value':str(a[0]),'selected':'','text':str(a[1])})
		
		
		ref_artL = modelDic['edit_artist_struc']['ref_artL']
		main_artist_num = str(len(ref_artL))
		ref_artist_avlbl_list = ''
		for a in ref_artL:
			variablD  = {'class':'','value':str(a[0]),'selected':'','text':str(a[1])}
			ref_artist_avlbl_list = ref_artist_avlbl_list +  template_process(modelDic,'gen_dd_list_option_elem',variablD)		
			#ref_artist_avlbl_list = ref_artist_avlbl_list +   modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'','value':str(a[0]),'selected':'','text':str(a[1])})	
			
		rel_type = modelDic['edit_artist_struc']['rel_type']
		rel_type_list = ''
		rel_typeL = [('no_selection','NO Selection'),('same_artist','SAME ARTIST'),('play_together','PLAY TOGETHER')]
		for a in rel_typeL:
			selected = ''
			if rel_type == a[0]:
				selected = 'SELECTED'
			variablD  = {'class':'no','value':str(a[0]),'selected':selected,'text':str(a[1])}	
			rel_type_list = rel_type_list +  template_process(modelDic,'gen_dd_list_option_elem',variablD)		
			#rel_type_list = rel_type_list +  modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'no','value':str(a[0]),'selected':selected,'text':str(a[1])})	
			
		# Если новый артист на ввод то у него нет референсивных списков пока. значит пропуск
		ref_artist_list = ''
		logger.debug('ref_list_generation')
		for a in ref_art_newL:
			
			ref_artist_list = ref_artist_list +    modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'no','value':str(a[0]),'selected':'','text':str(a[1])})	
		logger.debug ('send_ArtistEdit_form_new -> Generated OK')	
			
		
		variablD =	{'host_name':host_name,'html_title':html_title,'host':host,'artist_name':artist_name,
					'search_term':search_term,'ref_artist_list':ref_artist_list,'checked_flag':main_checked_flag,
					'ref_artist_avlbl_list':ref_artist_avlbl_list,'rel_artist_list':rel_artist_list,
					'rel_artist_num':rel_artist_num,'main_artist_num':main_artist_num,'rel_type_list':rel_type_list}
					
		page = template_process(modelDic,'artist_edit_form',variablD)		
		
		#try:
		#	page = TmplD['artist_edit_form']['TMPL']%({'host_name':host_name,'html_title':html_title,'host':host,'artist_name':artist_name,
		#												'search_term':search_term,'ref_artist_list':ref_artist_list,'checked_flag':main_checked_flag,
		#												'ref_artist_avlbl_list':ref_artist_avlbl_list,'rel_artist_list':rel_artist_list,
		#												'rel_artist_num':rel_artist_num,'main_artist_num':main_artist_num,'rel_type_list':rel_type_list})	
		#except Exception,e:
			
		#	page = "Hren",str(TmplD['artist_edit_form']['TMPL'])
		#	logger.critical('Exception at send_ArtistEdit_form_new:%s'%(str(e)))	
		logger.info('send_ArtistEdit_form_new -> Generated OK')	
		return xmlrpc.client.Binary(page)
	
def prepareArtistOveralReport(statL,artistD,ref_artL,modelDic,*args):
	logger.info('And now!!! we are in prepareArtistOveralReport %s'%(str(list(modelDic.keys()))))
	s = ''
	colorL = ['#FFFFCC','#CCFFFF']
	color = colorL[0]
	
	song_num = 0
	album_num = 0
	
	search_res_list = ''
	
	gr_L = []
	if "grouping" in args:
		pass
	
	for a in statL[:1000]:
		
		if (statL.index(a) % 2) == 0:
			color =  colorL[1]
		else:
			color =  colorL[0]
		tr_crc32 = str(a[3])
		
		try:
			artist_name = "%-3s. %s"%(str(statL.index(a)+1),artistD[a[3]]['artist'])
		except Exception as e:
			artist_name = 'error'
			logger.critical('Exception during the report generation:%s %s %s'%(str(e),str(a[3]),str(artistD[a[3]]['artist'])))
		
		if artistD[a[3]]['main'] == True:
			main_checked = 'CHECKED'
		else:
			main_checked = ''
			
			
		if artistD[a[3]]['is_in_db'] == True:
			in_db_checked = 'CHECKED'
		else:
			in_db_checked = ''
	
		song_num = 	"%-4s"%(str(len(artistD[a[3]]['id_trackL'])))
		
		album_stat_dd = ''
		
		
		if 'albumD' in artistD[a[3]]:
			album_num = str(len(artistD[a[3]]['albumD']))	
			
			l_mp3 = []
			l_losless = []
			for b in artistD[a[3]]['albumD']:
				#print b
				album = artistD[a[3]]['albumD'][b]['album']
				#print album
				if 'mp3' in artistD[a[3]]['albumD'][b]['format'].lower():
					l_mp3.append((b,album))
				else:
					l_losless.append((b,album))
			l = l_losless + l_mp3 		
			
			for b in l:
				if 'mp3' in artistD[a[3]]['albumD'][b[0]]['format'].lower():
					class_color_ddl = "mp3_color"
				else:
					class_color_ddl = "losless_color"
		
				option_text = """  %-100s -->%-3s: %-4s\n"""%(b[1],str(artistD[a[3]]['albumD'][b[0]]['song_num']),str(artistD[a[3]]['albumD'][b[0]]['format']))
				album_crc32 = str(artistD[a[3]]['albumD'][b[0]]['album_crc32'])
				try:
					album_stat_dd = album_stat_dd+modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':class_color_ddl,'value':album_crc32,
																									'selected':'',	'text':option_text})
				except Exception as e:
					logger.critical('Exception during the dd template:%s'%(str(e)))
					search_res_list = "error"
				

		try:
			search_res_list = search_res_list + modelDic['Tmpl']['search_res_table_row_artist']['TMPL']%({'color':color,'tr_crc32':tr_crc32 ,
																'artist_name':artist_name,
																'main_checked':main_checked,'in_db_checked':in_db_checked,
																'song_num':song_num,'album_num':album_num,'album_stat_dd':album_stat_dd
																
																})	
		except Exception as e:
			logger.critical('Exception during the template:%s'%(str(e)))
			search_res_list = "error"
			
	
	return search_res_list	
	
	

	
	
def generic_search_res_track_list(sD,color_zebraL,modelDic,mode):	
	logger.debug('AT----------> generic_search_res_track_list: START')	
	resL = []
	sortedL = []
	#print 'search 4.1',sD.keys()
	albumD = {}
	
	for a in sD:
		if sD[a]['album_crc32'] in albumD:
			albumD[sD[a]['album_crc32']]+=1
		else:
			albumD[sD[a]['album_crc32']] = 1
		try:
			if sD[a]['cue_num']==None:
				resL.append((sD[a]['path'],a))
			else:
				resL.append((sD[a]['cue_fname']+','+str(sD[a]['cue_num']),a))
		except:
			print('Error in search page generation 1')
	#print albumD
	
	resL.sort()
	sortedL = [a[1] for a in resL]
	#print 'search 4.2'
	#colorL = ['#FFFFCC','#CCFFFF']
	colorL = color_zebraL
	#print colorL
	color = colorL[0]

	search_res_list = ''		
	#print 'search 4.3'		
	
	if mode == 'with_a_t_a_href':
		TagD = modelDic['TagD']
		tagsLDic = modelDic['tagsLDic']	
	
	
	for a in sortedL:
		#print 'search 4.4',a			
		if (sortedL.index(a) % 2) == 0:
			color =  colorL[1]
		else:
			color =  colorL[0]
		
		#'search_res_table_row'
		try:
			if mode == 'simple':
				#print "in simple 1"
				search_res_list = search_res_list + modelDic['Tmpl']['search_res_table_row']['TMPL']%({'color':color,'tr_crc32':str(a),'track':sD[a]['title'],'artist':sD[a]['artist'],
																'album':sD[a]['album'],'format':sD[a]['format'],'bitrate':sD[a]['bitrate'],'ddl_part':''})
				#print "in simple 1"												
			elif mode == 'with_pic':
				logger.debug('AT----------1> generic_search_res_track_list: mode:'+mode)	
				image_name = sD[a]['album_crc32']
				num_tracks = albumD[sD[a]['album_crc32']]
				if num_tracks == 0:
					search_res_list = search_res_list + modelDic['Tmpl']['search_res_table_row']['TMPL']%({'color':color,'tr_crc32':str(a),'track':sD[a]['title'],
																'artist':sD[a]['artist'],'album':sD[a]['album'],'format':sD[a]['format'],
																'bitrate':sD[a]['bitrate'],'ddl_part':''})
				else:
					search_res_list = search_res_list + modelDic['Tmpl']['search_res_table_row_album']['TMPL']%({'color':color,'tr_crc32':str(a),'track':sD[a]['title'],
																'artist':sD[a]['artist'],'album':sD[a]['album'],'format':sD[a]['format'],
																'bitrate':sD[a]['bitrate'],'ddl_part':'','image_name':image_name,'num_tracks':num_tracks,
																'value':sD[a]['album_crc32'],'value2':str(a)})
																
				albumD[sD[a]['album_crc32']] = 0
				logger.debug('AT----------> generic_search_res_track_list: end 1')	
				
			elif mode == 'with_a_t_a_href':	
				
				#print 'check 1'
				artist_tag_navi_href_elem = ''
				if 'NA_' not in sD[a]['artist'] and 'NA ar' not in sD[a]['artist']:
					artist_tag_navi_href_elem = modelDic['Tmpl']['artist_tag_navi_search_href_elem']['TMPL']%({'value':sD[a]['artist_crc32'],'value2':str(a),'text':sD[a]['artist']})				
				else:
					artist_tag_navi_href_elem = str(sD[a]['artist'])
				#print 'check 2'
				album_tag_navi_href_elem = ''	
				if 'NA_' not in sD[a]['album'] and 'NA al' not in sD[a]['album']:
					album_tag_navi_href_elem = modelDic['Tmpl']['album_tag_navi_search_href_elem']['TMPL']%({'value':sD[a]['album_crc32'],'value2':str(a),'text':sD[a]['album']})		
				else:
					album_tag_navi_href_elem = str(sD[a]['album'])
				#print 'check 3'
				title_tag_navi_href_elem = ''
				# Проверяем есть ли тэги связанные с данным трэком	
				try:
					tagsL = tagsLDic[a]
				except:
					tagsL = []
					
				ddl_navi_part = ''	
				ddl_navi_L = []
				
				check_cnt = 0
				for tag in tagsL:
					if tag in TagD:
						if TagD[tag]['tag_type'] == 'SONG':
				#			print TagD[tag]
																								
							title_tag_navi_href_elem = modelDic['Tmpl']['title_tag_navi_search_href_elem']['TMPL']%({'value':str(tag),'value2':str(a),'class':"",'text':str(sD[a]['title'])})	
							continue
						#print TagD[tag]['tag_type']+':'+TagD[tag]['tag_name'].encode('utf8')	
						option_elem = ''
						#if a == -1846070030:
						#	print sD[a]['title'],TagD[tag]['tag_name'],sD[a]['album'],sD[a]['artist']
						#else:
						check_cnt = 1
						option_text = TagD[tag]['tag_type']+':'+TagD[tag]['tag_name']
						
						#text_navi = modelDic['Tmpl']['title_tag_navi_search_href_elem']['TMPL']%({'value':tag,'value2':str(a),'class':"",'text':str(option_text)})	
						
						option_elem = modelDic['Tmpl']['gen_dd_list_option_elem']['TMPL']%({'class':'mp3_color','value':str(tag),'selected':'',
																			'text':option_text})	
						#print option_elem													
																			
						check_cnt = 2
						ddl_navi_L.append(option_elem.encode('utf8'))
						check_cnt = 3
						
				if ddl_navi_L != []:		
					ddl_navi_part = """<SELECT NAME="getPL">""" + '\n'.join(ddl_navi_L) + "</SELECT>"									
					check_cnt = 4
				#print ddl_navi_part
				
				#print 'check 4'
				if title_tag_navi_href_elem == '':				
					title_tag_navi_href_elem = str(sD[a]['title'])			
				#print 'check 5'
				search_res_list = search_res_list + modelDic['Tmpl']['search_res_table_row']['TMPL']%({'color':color,'tr_crc32':str(a),'track':title_tag_navi_href_elem,
								'artist':artist_tag_navi_href_elem,'album':album_tag_navi_href_elem,'format':sD[a]['format'],'bitrate':sD[a]['bitrate'],
								'ddl_part':str(ddl_navi_part)})	
				check_cnt = 5				
					
																
		except:
			print('Error in generic_search_res_track_list ',a,list(sD[a].keys()),list(modelDic.keys()))
			print()
			print(ddl_navi_part)
			search_res_list = search_res_list + str(sortedL.index(a)) +'error in template search_res_table_row rendering   check pos:%s  <BR>---> %s'%(str(check_cnt),str(ddl_navi_part)) + '<BR>' 
			
	logger.debug('AT<----------- generic_search_res_track_list: Finished')		
	return search_res_list	

def images_search_res_album_list(sD,color_zebraL,modelDic,mode):	
	logger.debug('AT----------> images_search_res_album_list: START')	
	resL = []
	sortedL = []
	#print 'search 4.1',sD.keys()
	albumD = {}
	imageL = sD['imageL']
	album_crc32 = sD['album_crc32']
	
	#print 'search 4.2'
	#colorL = ['#FFFFCC','#CCFFFF']
	colorL = color_zebraL
	#print colorL
	color = colorL[0]

	search_res_list = ''		
	#print 'search 4.3'		
	class_value = ''
	
	for a in imageL:
		#print 'search 4.4',a			
		if (imageL.index(a) % 2) == 0:
			color =  colorL[1]
		else:
			color =  colorL[0]
		
		#'search_res_table_row'
		class_value = "cover_srch"
		if ".pdf" in a['f_name'].lower():
			class_value = "embed"
		else:
			class_value = "cover_srch"
		try:
			if mode == 'simple':
				#print "in simple 1"
				pass
				#print "in simple 1"												
			elif mode == 'images':
				logger.debug('AT---2980-----> images_search_res_album_list: mode:'+mode)	
				if imageL.index(a)==0:
					print('2975 JPG-Header')
					search_res_list = search_res_list + modelDic['Tmpl']['search_album_image_table_row_first']['TMPL']%({'color':color,'album_crc32':str(album_crc32),'images_num':str(len(imageL)),'value2':str(a['image_crc32']),'f_name':a['f_name'],'class_value':class_value})
					print('2975 JPG-Header - OK')
				else:
					embed_elem = ''
					if class_value == "embed":
						#print '2978 PDF'
						image_name = str(a['image_crc32'])+".pdf"
						embed_elem = modelDic['Tmpl']['pdf_embed_elem']['TMPL']%({'obj_crc32':str(a['image_crc32']),'obj_crc32_pdf':str(image_name),'album_crc32':str(album_crc32)})
						#print '2978 PDF - OK'
					else:
						print('2984 JPG')
						image_name = a['image_crc32']
						embed_elem = modelDic['Tmpl']['image_embed_elem_fotorama']['TMPL']%({'obj_crc32':str(image_name),'album_crc32':str(album_crc32),'f_name':a['f_name'],'class_value':class_value})
						print('2984 JPG -OK')
					
					 
					
					search_res_list = search_res_list + modelDic['Tmpl']['search_album_image_table_row']['TMPL']%({'color':color,'embed_elem':embed_elem})
				
																
		except:
			print('Error in images_search_res_album_list ',imageL.index(a),list(modelDic.keys()))
			print()
			
			search_res_list = search_res_list + str(sortedL.index(a)) +'error in template search_res_table_row rendering   check   <BR>---> %s'%(str('---')) + '<BR>' 
			
	return search_res_list		
	
def get_templ_vars(template_str):
	variableD = {}
	varL = []
	while(1):
		try:
			res = template_str%variableD
		except KeyError as e:
			missed_var = e.args[0]
			if missed_var not in variableD:
				variableD[missed_var] = ''
				varL.append(missed_var)
				continue
		return 	varL
	return 	varL
	
def template_process(modelDic,template_name,variableD):
	cnt =0
	res = ''
	#modelDic['Tmpl'][template_name]['TMPL']
	while(1):
		try:
			res = modelDic['Tmpl'][template_name]['TMPL']%variableD
		except KeyError as e:
			missed_var = e.args[0]
			logger.critical('Exception during template processing [%s]:%s'%(str(template_name),str(e)))
			if missed_var not in variableD:
				
				variableD[missed_var] = """<-- var:[%s] is missed at at template [%s] processing-->"""%(missed_var,str(template_name))
				continue
		except Exception as e:
			logger.critical('Exception general during template processing [%s]:%s'%(str(template_name),str(e)))
			return res
		return res
	return res		
		