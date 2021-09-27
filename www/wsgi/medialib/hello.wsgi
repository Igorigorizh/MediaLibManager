# # -*- coding: cp1251 -*-
#-*- coding: utf-8 -*-
from pprint import pformat
import xmlrpc.client,socket
import string,cgi,time
from urllib.parse import urlparse, parse_qs
import time
import json
import os, sys
from subprocess import Popen
import base64

sys.path.append('/home/medialib/MediaLibManager')

#import myMediaLib_controller
#from myMediaLib_adm import checkANDkillMLPids
#from myMediaLib_adm import RebootServer
#from myMediaLib_init import readConfigData

mymedialib_cfg = '/home/medialib/MediaLibManager/config/mymedialib.cfg'
logPath = '/home/medialib/MediaLibManager/log/spam.log'
#from myMediaLib_adm import getHardWareInfo

def getHardWareInfo():
	return res


def is_post_request(environ):
	if environ['REQUEST_METHOD'].upper() != 'POST':
		return False
	content_type = environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')
	return (content_type.startswith('application/x-www-form-urlencoded')
		or content_type.startswith('multipart/form-data'))

def application(environ, start_response):
# Òàêèì îáðàçîì îòôèëüòðîâûâàåì çàïðîñû ïî äàííîìó ïðèëîæåíèþ
	if '/medialib' not in environ['REQUEST_URI']:
		exit
	host_name = '127.0.0.1'
	# MEDIALIB_HOST env variable comes through Docker-compose indicating separated wsgi and rpc hosts;
	# medialib is default rpc host name in separate scenario
	if 'MEDIALIB_HOST' in os.environ:
	    host_name = os.environ['MEDIALIB_HOST']
	p_appl = xmlrpc.client.ServerProxy('http://'+str(socket.gethostname())+':9000')	
	#s_appl = xmlrpc.client.ServerProxy('http://'+str(socket.gethostname())+':9001')
	s_appl = xmlrpc.client.ServerProxy('http://'+host_name+':9001')
	try:
		request_body_size = int(environ.get('CONTENT_LENGTH', 0))
	except (ValueError):
		request_body_size = 0	
	output = [b'']
	commandD = {}
	
	http_params = {}
	if 'REMOTE_ADDR' in environ:
		http_params = {'REMOTE_ADDR':environ['REMOTE_ADDR'],'HTTP_HOST':environ['HTTP_HOST'],'SERVER_ADDR':environ['SERVER_ADDR'],'SERVER_NAME':environ['SERVER_NAME']}
		
	if 'HTTP_USER_AGENT' in environ:
		http_params['HTTP_USER_AGENT'] = environ['HTTP_USER_AGENT']
	
	
	
	command_routingD = {'/main':{'page_load':'main_page'},
						'/cast':{'page_load':'cast_page'},
						'/admin':{'page_load':'admin_page'},
						'/info':{'page_load':'info_page'},
						'/tagadmin':{'page_load':'tagAdmin_page'},
						'/search':{'page_load':'search_page'},
						'/trackpreload':{'page_load':'track_preload_page'},
						'/image':{'page_load':'image_page'},
						'/debug':{'page_load':'debug_page'},
						'/graf':{'page_load':'graf_page'},
						'/reports':{'page_load':'report_artist_page'},
						'/edit_artist':{'page_load':'edit_artist_page','artist':''}
						}
	
	if environ['REQUEST_METHOD'] == 'GET':	
	
		if '/main' in environ['REQUEST_URI']:
			commandD = command_routingD['/main']	
		elif '/admin' in environ['REQUEST_URI']:
			commandD = command_routingD['/admin']
		elif '/cast' in environ['REQUEST_URI']:
			commandD = command_routingD['/cast']	
		elif '/info' in environ['REQUEST_URI']:
			commandD = command_routingD['/info']
		elif '/search' in environ['REQUEST_URI']:
			commandD = command_routingD['/search']	
		elif '/image' in environ['REQUEST_URI']:
			commandD = command_routingD['/image']				
		elif '/trackpreload' in environ['REQUEST_URI']:
			commandD = command_routingD['/trackpreload']					
		elif '/graf' in environ['REQUEST_URI']:
			commandD = command_routingD['/graf']		
		elif '/debug' in environ['REQUEST_URI']:
			commandD = command_routingD['/debug']
		elif '/log' in environ['REQUEST_URI']:
			output.append(b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> \n <html> \n <head> <meta http-equiv="Content-Type" content="text/html; charset=utf8"> </head> \n <body> \n')
			res = str(time.strftime('%X %x %Z'))+' <BR>   apache wsgi appl, player rpc, appl rpc to be tested.......... <BR> <BR> <BR>'
			if 'SERVER_ADDR' in environ:
				res += '1. apache wsgi-helloappl is OK: <BR>' + str('--------SERVER_ADDR') + '-->'+str(environ['SERVER_ADDR'])+"<BR>"
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			
			
						
			res = '<BR> 2. apache wsgi-player: <BR>'
			try:		
				res = res + str(p_appl.get_status())
				res = res + '<BR> player is OK <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except:
				res = res + 'player application failed!!! <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
				
			# output_len = sum(len(line) for line in output)
			# start_response('200 OK', [('Content-type', 'text/html'),
									  # ('Content-Length', str(output_len))])	
			# return output
			
			
			res = '<BR> 3. apache wsgi-appl: <BR>'
			try:		
				res = res + str(s_appl.appl_status())
				res = res + '<BR> application instance is OK  <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except Exception as e:
				res = res + ' <BR> application controller instance failed!!!'
				res = res + 'Error:'+str(e)
				res = bytes(res,encoding = "utf-8")
				output.append(res)
				

			line_num = 200
			log_pos = environ['REQUEST_URI'].find('/log/')
			if log_pos>0:
				req_tail = environ['REQUEST_URI'][log_pos+5:]
				if req_tail.isdigit(): 
					line_num = int(req_tail)
					if line_num > 10000:
						line_num = 10000
							
					if line_num < 10:
						line_num = 10
			res = '<BR> 4. apache wsgi appl log of [%i] last lines (log/->linesNum for more lines in output): <BR>'%line_num
			Tmpl_D = {}
			#configDict = {}
			#configDict = readConfigData(mymedialib_cfg)
			#logPath='---no Path---'
			
			#try:
				#logPath=configDict['logPath']
				#res = res + ' <BR>'
			#except Exception as e:
				#res = b'wsgi error: 132 '+str(e).encode('utf-8')

			#res = res+str(logPath)
			#res = str(configDict)

			color_template_red = "<span style='color:Red;background-color:Yellow'> %s '</span>'"	
			color_template_green = "<span style='color:Black;background-color:Cyan'> %s '</span>'"	
			color_template_orange = "<span style='color:Black;background-color:Orange'> %s '</span>'"	
			color_template_grey = "<span style='color:Black;background-color:Grey'> %s '</span>'"
			try:	
				logf = open(logPath,"r",encoding = "utf-8")
				lines = logf.readlines()
				logf.close()
				log_l_len = len(lines)
				output.append(b'log lines read: %i'%log_l_len)
				for i, a in enumerate(lines):
					if 'CRITICAL' in a:
						lines[i]= a.replace('CRITICAL', color_template_red%('CRITICAL'))
					elif 'DEBUG' in a:
						lines[i]= a.replace('DEBUG', color_template_green%('DEBUG'))			
					elif 'INFO' in a:
						lines[i]= a.replace('INFO', color_template_orange%('INFO'))			
					elif 'WARNING' in a:
						lines[i]= a.replace('WARNING', color_template_grey%('WARNING'))			

				lines.reverse()
				
			except Exception as e:
				res = b'wsgi error: 265 '+str(e).encode('utf-8')
				output.append(res)
			
			try:		
				for a in lines[:line_num]:
					res = res + '<BR>'+a
				res = bytes(res,encoding = "utf-8")	
				output.append(res)
			except:
				res = res + str('error: wsgi 274 logging failed!!!').encode('utf-8')
				#res = bytes(res,encoding = "utf-8")
				output.append(res)
				
			
			# except xmlrpclib.Fault, err:	
				# output.append("A fault occurred in status returning %s \n"%(str(''))
				# output.append("Fault code: %d \n" % err.faultCode)
				# output.append("Fault string: %s \n" % err.faultString)
			
			
			
			output.append(b'\n </body> \n </html>')
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
									  ('Content-Length', str(output_len))])
			return output					  
		
		elif '/mstat' in environ['REQUEST_URI']:
			
			res = str(time.strftime('%X %x %Z'))+' <BR>   apache wsgi appl, player rpc, appl rpc to be tested.......... <BR> <BR> <BR>'
			if 'SERVER_ADDR' in environ:
				res += '1. apache wsgi-helloappl is OK: <BR>' + str('--------SERVER_ADDR') + '-->'+str(environ['SERVER_ADDR'])+"<BR>"
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			
			
						
			res = '<BR> 2. apache wsgi-player: <BR>'
			try:		
				res = res + str(p_appl.get_status())
				res = res + '<BR> player is OK <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except:
				res = res + 'player application failed!!! <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
				
			# output_len = sum(len(line) for line in output)
			# start_response('200 OK', [('Content-type', 'text/html'),
									  # ('Content-Length', str(output_len))])	
			# return output
			
			
			res = '<BR> 3. apache wsgi-appl: <BR>'
			try:		
				res = res + str(s_appl.appl_status())
				res = res + '<BR> application instance is OK  <BR>'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except:
				res = res + ' <BR> application controller instance failed!!!'
				res = bytes(res,encoding = "utf-8")
				output.append(res)
					
				
					
			
			# except xmlrpclib.Fault, err:	
				# output.append("A fault occurred in status returning %s \n"%(str(''))
				# output.append("Fault code: %d \n" % err.faultCode)
				# output.append("Fault string: %s \n" % err.faultString)
			
			
			res = '<BR> 4. System hardware status: <BR>'
			try:
				res+= getHardWareInfo()
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except :
				res = bytes(res,encoding = "utf-8")
				output.append("error in getHardWareInfo:")
				
			res = '<BR> 5. ML services ranning: <BR>'	
			try:
				res+= str(checkANDkillMLPids())
				res = bytes(res,encoding = "utf-8")
				output.append(res)
			except :
				res = bytes(res,encoding = "utf-8")
				output.append("error in checkANDkillMLPids:")	
			
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
									  ('Content-Length', str(output_len))])
			return output					  
					
			
			
			
					
		elif '/tagadmin' in environ['REQUEST_URI']:
			commandD = command_routingD['/tagadmin']	
		elif '/reports' in environ['REQUEST_URI']:
			commandD = command_routingD['/reports']	
		elif '/edit_artist' in environ['REQUEST_URI']:	
			dic = cgi.parse_qs(urlparse(environ['REQUEST_URI'])[4])
			if 'q' in dic:
				command_routingD['/edit_artist']['artist'] = dic['q'][0]
			commandD = command_routingD['/edit_artist']		
		
		#elif '/medialib' in environ['REQUEST_URI'] and 'search' not in environ['REQUEST_URI'] and '/environ' not in environ['REQUEST_URI']:
		#	commandD = command_routingD['/main']	
				
		elif '/environ' in environ['REQUEST_URI']:
			res = ''
			for a in environ:
				res = res + str(a) + '-->'+str(environ[a])+"<BR>"
			
			output.append(bytes(res,encoding = "UTF-8"))	
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
					
			return output
			
		elif '/medialib' in environ['REQUEST_URI']:
			res = 'Empty medialib command <BR>'
			
			try:		
				res = res + str(p_appl.get_status())+'<BR>'
				
			except:
				res = res + 'player application failed!!! <BR>'
				
			try:		
				res = res + str(s_appl.appl_status())
			except:
				res = res + 'medialib application failed!!! <BR>'
				
				
			try:
				w=winamp.Winamp()
				pr_id = str(w._Winamp__processID)
				w_ver = str(w.getVersion())
				res = res +'<BR> Winamp live status:' + "<BR>"+'-->'+pr_id+ '<--'+ w_ver+"<BR>"
			except:
				res = res + '<BR> Winamp  failed!!! <BR>'	
			res = bytes(res,encoding = "utf-8")	
			output.append(res)
			
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
					
			return output	
			
			
		if commandD != {}:	
			# àêòóàëüíûé îáðàáîò÷èê
			try:
				
				res = s_appl.command_dispatcher(commandD, http_params).data
				print('Test 427 command_routingD='+str(command_routingD))
				print(str(type(res)))
			#output.append('Test page')
				if res != 0:
					output.append(res)
				else:
					output.append(b'')
					
				output_len = sum(len(line) for line in output)
				start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
					
				return output
				
			except xmlrpc.client.Fault as err:	
				output.append("A fault occurred in new %s full page\n"%(str(list(commandD.values())[0])))
				output.append("Fault code: %d \n" % err.faultCode)
				output.append("Fault string: %s \n" % err.faultString)
				
			except socket.error as e:	
				output.append('Medialib Application Error:'+str(e)+'<BR>')
				output.append('*****************************************************<BR>')
				output.append('PLEASE CHECK IF MEDIALIB SERVICE IS RUNNING! <BR>')
				output.append('*****************************************************<BR>')
				
			except :
				output.append("A fault occurred new  FULL PAGE last--->\n %s"%(str(list(commandD.values())[0])))
				output.append("Unknown error" )
				
				
		commandD = {}		
		
        	
 #  ÃËÀÂÍÛÉ WSGI îáðàáîò÷èê POST çàïðîñîâ ÷åðåç JSON
	if environ['REQUEST_METHOD'] == 'POST':
		if '/main' in environ['REQUEST_URI'] or '/edit_artist' in environ['REQUEST_URI'] or '/tagadmin' in environ['REQUEST_URI']  or '/admin' in environ['REQUEST_URI'] or '/search' in environ['REQUEST_URI'] or '/report' in environ['REQUEST_URI'] or '/graf' in environ['REQUEST_URI'] or '/cast' in environ['REQUEST_URI'] or '/debug' in environ['REQUEST_URI'] or '/image' in environ['REQUEST_URI'] or '/trackpreload' in environ['REQUEST_URI'] or '/start_ml' in environ['REQUEST_URI']:
			try:
				fs = get_post_form(environ)
			except :	
				output.append(b'A fault occurred form parsing--->\n ')
				return output
			res = ''
			try:
				json_params = {}
				#print('json_params='+str(type(json_params)))
				#json_params = bytes(json.loads(fs),encoding = "UTF-8")
				json_params = json.loads(fs)
				#print('json_params='+str(type(json_params)))
			except :
				output.append(b'A fault occurred new main params parsing--->\n ')
				return output	
				
			# Îáðàáîòàòü áåç çàïðîñîâ ê ñåðâåðàì çàäà÷ó íà ïåðåçàãðóçêó èëè ôèçè÷åñêóþ îñòàíîâêó ñåðâåðà	
			if 'do_admin' in json_params:
				if json_params['do_admin'] == 'restart_srv' or json_params['do_admin'] == 'shutdown_srv' or json_params['do_admin'] == 'remove_srv':
					if json_params['restart_pswrd'] == 'brumbul':
						
						if json_params['do_admin'] == 'restart_srv':
							reply = {"action_name": "do_admin", "action_result": 1,"message":'Rebooting'}
							output.append(json.dumps(reply))
							RebootServer() 
						if json_params['do_admin'] == 'shutdown_srv':	
							reply = {"action_name": "do_admin", "action_result": 1,"message":'Shutdowning... Take AC plug off and reloacate server'}
							output.append(json.dumps(reply))
							RebootServer(message='Shutdown', bReboot=0) 
						if json_params['do_admin'] == 'remove_srv':	
							reply = {"action_name": "do_admin", "action_result": 1,"message":'Removing ml services and Winamp... Restart services again'}
							output.append(json.dumps(reply))
							res = res + str(checkANDkillMLPids('kill')) 	
							output.append(res)
					else:
						reply = {"action_name": "do_admin", "action_result": 0,"message":'wrong password'}
						output.append(json.dumps(reply))
						
						
						
					output_len = sum(len(line) for line in output)
					start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
					return output
				else:
					json_params['remote_host'] = environ['REMOTE_ADDR']
					
			elif 'start_medialib'	in json_params:
			
				if json_params['start_medialib'] == 'start_player_controller':
					reply = {"action_name": "start_medialib", "action_result": 1,"message":'Starting...  please wait'}
					
					r = os.spawnve(os.P_WAIT, 'c:\Python27\python.exe', ['c:\Python27\python.exe','C:\My_projects\MyMediaLib\_player_server.py'], os.environ)
					
					output.append(json.dumps(reply))
				
				elif json_params['start_medialib'] == 'start_appl_controller':
					reply = {"action_name": "start_medialib", "action_result": 1,"message":'Starting...  please wait'}
					r = os.spawnve(os.P_WAIT, 'c:\Python27\python.exe', ['c:\Python27\python.exe','C:\My_projects\MyMediaLib\_appl_server.py'], os.environ)
					output.append(json.dumps(reply))	
					
				elif json_params['start_medialib'] == 'start_task_dispatcher':
					reply = {"action_name": "start_medialib", "action_result": 1,"message":'Starting...  please wait'}
					r = os.spawnve(os.P_WAIT, 'c:\Python27\python.exe', ['c:\Python27\python.exe','C:\My_projects\MyMediaLib\_task_dispatcher.py'], os.environ)
					output.append(json.dumps(reply))		
				
					
				
				output_len = sum(len(line) for line in output)
				start_response('200 OK', [('Content-type', 'text/html'),('Content-Length', str(output_len))])
				return output
				
			# Main processing	
			try:
				res = s_appl.command_dispatcher(json_params, http_params)
				res = bytes(res,encoding = "UTF-8")
				#output.append('Test page')
				if res != 0:
					output.append(res)
				elif res == {}:
					output.append(b'Empty Status')
				else:
					output.append(b'')
				
				output_len = sum(len(line) for line in output)
				start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
				return output
				
			except xmlrpc.client.Fault as err:	
				output.append(b"A fault occurred in new WSGI MAIN\n")
				output.append(b"Fault code: %d \n" % err.faultCode)
				output.append(bytes("Fault string: %s \n" % str(err.faultString),encoding = "utf-8"))
			except Exception as err:
				output.append(bytes("A fault occurred new main last--->\n %s\n"%str(fs),encoding = "utf-8"))
				output.append(bytes("Unknown error: %s"%str(err),encoding = "utf-8"))
				
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
                              ('Content-Length', str(output_len))])	
			return output
		elif  '/async' in environ['REQUEST_URI']:	
			fs = get_post_form(environ)
			res = ''
			try:
				# òåêóùèé êëèåíòñêèé ñòàòóñ
				cur_status = json.loads(fs)
			except :
				output.append("A fault occurred new main params parsing--->\n %s")
				return output	
			try:
				respond =  {}
				cnt_sec = 0 
				while cnt_sec < 60:
					cnt_sec+=1	
					res = p_appl.get_status()
					
										
					
					if cur_status['playBack_Mode'] !=  res['playBack_Mode']:
						respond['playBack_Mode'] = res['playBack_Mode']
						
					if cur_status['pL_CRC32'] !=  res['pL_CRC32']:
						respond['pL_CRC32']= res['pL_CRC32']
					elif cur_status['pl_pos'] !=  res['pl_pos']:	
						respond['pl_pos'] =res['pl_pos']
					
					#print abs(int(cur_status['playingTrack_pos']/1000) - int(res['playingTrack_pos']/1000)),
					#print int(cur_status['playingTrack_pos']/1000), int(res['playingTrack_pos']/1000)
					
					if abs(int(cur_status['playingTrack_pos']/1000) - int(res['playingTrack_pos']/1000)) >	3:
						#pass
						#print abs(int(cur_status['playingTrack_pos']/1000) - int(res['playingTrack_pos']/1000)),
						respond['playingTrack_pos'] =res['playingTrack_pos']
					if respond != {}:
						respond['playingTrack_pos'] = res['playingTrack_pos']
						dum = s_appl.refresh_content('play_list_sync',res)	
						output.append(bytes(json.dumps({'async_respond':respond}),encoding = "UTF-8"))
						output_len = sum(len(line) for line in output)
						start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
						return output
						
						
					time.sleep(1)	
					
					if cur_status['playBack_Mode'] == 1:
						cur_status['playingTrack_pos']+=1000
				#print 'okkk->',respond
				
				#output.append('Test page')
				
				output.append(bytes(json.dumps({'async_respond':'endoflive'}),encoding = "UTF-8"))
				
				
				output_len = sum(len(line) for line in output)
				start_response('200 OK', [('Content-type', 'text/html'),
								  ('Content-Length', str(output_len))])
				return output
				
			except xmlrpc.client.Fault as err:	
				output.append(b"A fault occurred in ASYNC\n")
				output.append(b"Fault code: %d \n" % err.faultCode)
				output.append(b"Fault string: %s \n" % err.faultString)
			except :
				output.append(b"A fault occurred new ASYNC --->\n %s"%str(fs))
				output.append(b"Unknown error" )
				
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),
                              ('Content-Length', str(output_len))])	
			return output
			
	return output
	
	
def get_post_form(environ):
	assert is_post_request(environ)
	post_form = environ.get('wsgi.post_form')
	input = environ['wsgi.input']
	#f = open('ajax.txt','w')
	#res = input.read()
	#f.write(res)
	#f.close()
	post_form = environ.get('wsgi.post_form')
	if (post_form is not None
		and post_form[0] is input):
		#f = open('ajax.txt','w+')
		#res = post_form[2].read()
		#f.write(res)
		#f.close()
		return post_form[2]
	# This must be done to avoid a bug in cgi.FieldStorage
	environ.setdefault('QUERY_STRING', '')
	try:
		fs = cgi.FieldStorage(fp=input,
							environ=environ,
							keep_blank_values=1)
	except:
		res = input.read()
		return res
    #new_input = InputProcessed('')
    #post_form = (new_input, input, fs)
    #environ['wsgi.post_form'] = post_form
   # environ['wsgi.input'] = new_input
	return fs

class InputProcessed(object):
	def read(self, *args):
		raise EOFError('The wsgi.input stream has already been consumed')
	readline = readlines = __iter__ = read	
