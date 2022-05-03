import logging
import os
import json
logger = logging.getLogger('controller_logger.init')

def loadCommandRouting(fname):
	
	#f = open(getcwd()+fname,'r')
	f = open(fname,'r')
	r = f.read()
	f.close()
	command_routingD = {}	
	try:
		command_routingD = json.loads(r.replace('\'','\"'))
	except Exception as e:
		print("Error in json command parsing, check:",fname)
		logger.critical("Error at load command routing [%s]"%(str(e)))
		#print(r)
	
	return command_routingD	

def readConfigData(fname):
	f = open(fname,'r', encoding="utf-8")
	l = f.readlines()
	f.close()
	configDict = {'mpdMusicPathPrefix':'','audioFilesPathRoot':'','logPath':'','mediaPath':'','templatesPath':'','lossless_path':'','winampext':'','player_cntrl_port':0,'appl_cntrl_port':0,'commandRouting':'','dbPath':'','audio_files_path_list':[],'applicationPath':'','radioNodePath':'','imageNodePath':'','preprocessAlb4libPath':'','ml_folder_tree_buf_path':'','mpd_host_list':[]}	
	configDictCmlx = {'templatesPath':'','audio_files_path_list':[],'mpd_host_list':[]}	

	for a in l:
		
		if a == '\n': continue

		try:
			if a.strip()[0] == '#': continue
		except:
			logger.critical("Error in config. Check line [%i],[%s]"%(l.index(a),a))
			continue
		key_found = False
# 		simple config parameters processing
		for key in configDict:
			pos = a.find(key)
			if pos >=0:
				
				if key in configDictCmlx:
					key_found = True
					break
				else:	
					configDict[key] = a.split('=')[1].strip()
					key_found = True
				break
		if not key_found:
			logger.critical("Error at readConfigData: undefined key=[%s]"%(a.split('=')[0].strip()))
			continue
# 		nested config parameters processing			
		if key == 'audio_files_path_list':
			configDict[key] = []
			try:
				path_strL = a.split('=')[1].strip().split(';')
				chkL = [b.strip() for b in  path_strL if b != '']
				for path in chkL:
					if not os.path.exists(path):
						print('Wrong  path! 3294:',[path], "-->Check in config:'audio_files_path_list='")
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
				host_name = "undefined"
				host_s = a.split('=')[1].strip().replace('\'','\"')
				chkD = json.loads(host_s)
				for host_name in chkD:
					#print(chkD[host_name])
					hostL = chkD[host_name].split(':')
					configDict[key].append({'host_name':host_name,'host':hostL[0],'socket':hostL[1]})
				continue		
						
			except Exception as e:
				logger.critical("Error at mpd host list load [%s] [%s]"%(str(e),str(host_name)))
				continue		
				
			
		if key == 'templatesPath':	 
		
			if 'templatesD' not in configDict:
				configDict['templatesD'] = {l.index(a):{key:a.split('=')[1].strip(),'active':True}}
			else:
				configDict['templatesD'][l.index(a)] = {key:a.split('=')[1].strip(),'active':False}
				
			continue	

	return 	configDict	

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
		# 	
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
