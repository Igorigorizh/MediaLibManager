import os
import xmlrpc.client
from pprint import pformat
import json
import pickle
import base64

def application(environ, start_response):
	output = [b'<pre>']
	output.append(b'If you see this - it is strange')
	output.append(b'/<pre>')

	output_len = sum(len(line) for line in output)
	response_headers = [('Content-type', 'text/plain'),
                    ('Content-Length', str(output_len))]

	host_name = '127.0.0.1'
	# MEDIALIB_HOST env variable comes through Docker-compose indicating separated wsgi and rpc hosts;
	# medialib is default rpc host name in separate scenario
	if 'MEDIALIB_HOST' in os.environ:
	    host_name = os.environ['MEDIALIB_HOST']
	#p_appl = xmlrpc.client.ServerProxy('http://'+str(socket.gethostname())+':9000')
	#s_appl = xmlrpc.client.ServerProxy('http://'+str(socket.gethostname())+':9001')
	s_appl = xmlrpc.client.ServerProxy('http://'+host_name+':9001')
#	output = ['<pre>']
#	output.append(pformat(environ))
#	output.append('</pre>')
	
#	return output
	path = ''
	data = ''
	if '/cover' in environ['REQUEST_URI'] or 'no-image-availabl' in environ['REQUEST_URI']:
		pos = environ['REQUEST_URI'].find('/cover')+7	
		id= environ['REQUEST_URI'][pos:]
		#data = s_appl.get_image(id).data
		d = s_appl.get_image(id).data
		dmp = pickle.loads(os.path.normpath(d))
		path = str(base64.b64decode(dmp).decode('utf-8'))
		
	elif '/album_images' in environ['REQUEST_URI']:
		pos = environ['REQUEST_URI'].find('/album_images')+14	
		pos_2 = environ['REQUEST_URI'].rfind('/')
						
		album_crc32= environ['REQUEST_URI'][pos:pos_2]
		image_crc32= environ['REQUEST_URI'][pos_2+1:]
		#data = s_appl.get_image("album_images",{'album_crc32':album_crc32,'image_crc32':image_crc32}).data
		d = s_appl.get_image("album_images",{'album_crc32':album_crc32,'image_crc32':image_crc32}).data
		dmp = pickle.loads(d)
		#os.path.normpath(d)
		try:
			path = str(base64.b64decode(dmp).decode('utf-8'))
			path = os.path.normpath(path)
		except Exception as err:
			print('Error in image.wsgi 45 with image path:',[dmp])
			output.append(dmp)
			output.append(bytes("\nUnknown error in album images: %s"%str(err),encoding = "utf-8"))
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),('Content-Length', str(output_len))])
			return output

	elif '/100_cover' in environ['REQUEST_URI'] or 'no-image-availabl' in environ['REQUEST_URI']:
		if '/100_cover' in environ['REQUEST_URI']:
			pos = environ['REQUEST_URI'].find('/100_cover')+11	
			id= environ['REQUEST_URI'][pos:]

		#data = s_appl.get_image('search_icon',id).data
		
		d = s_appl.get_image('search_icon',id).data
		dmp = pickle.loads(d)
		
		try:
			path = str(base64.b64decode(dmp).decode('utf-8'))
			path = os.path.normpath(path)
		except Exception as err:
			#output.append(bytes("Unknown error: %s"%str(err),encoding = "utf-8"))
			print([dmp]) 
			output.append(dmp)
			output.append(bytes("\nUnknown error: %s"%str(err),encoding = "utf-8"))
			output_len = sum(len(line) for line in output)
			start_response('200 OK', [('Content-type', 'text/html'),('Content-Length', str(output_len))])
			return output
		
	# Conditions above are true	
	print('path='+str([path]),len(path))
	if path != '':

		if os.path.exists(bytes(path,encoding = "UTF-8")):
			fileObj = open(path,'rb')
			image = fileObj.read()
			fileObj.close()
			
			if '.pdf' in environ['REQUEST_URI'] and '.pdf' in path:
				response_headers = [('Content-type', 'application/pdf'),
					('Content-Length', str(len(image)))]
			else:
				response_headers = [('Content-type', 'image/jpeg'),
					('Content-Length', str(len(image)))]
			
			start_response('200 OK', response_headers)
			return [image]
		else:
			print('Error in image.wsgi 100 with image path:',[path])
			res = bytes('Wrong path returned in image.wsgi 100:'+str([path])+',len='+str(len(path)),encoding = "UTF-8")
			#output.append(res)
			
			#output_len = sum(len(line) for line in output)
			output_len = len(res)
			
			response_headers = [('Content-type', 'text/plain'),
                    ('Content-Length', str(output_len))]
			
			start_response('400 Bad data', response_headers)
			print(str([res]))
			return [res]
	
	controlL = ['play','stop','next','prev','pause']
	
	for command_name in controlL:
		if '/'+command_name+'.jpg' in environ['REQUEST_URI']:
			image = s_appl.get_control_pics(command_name).data
			response_headers = [('Content-type', 'image/jpeg'),
	        	('Content-Length', str(len(data))),
			('Cache-Control','private')]				
			start_response('200 OK', response_headers)
			return [image]
##		response_headers = [('Content-type', 'image/jpeg'),
##	        	('Content-Length', str(len(data))),
##			('Cache-Control','private')]
	
	start_response('400 OK', response_headers)
	
	return [data]
##	return output
