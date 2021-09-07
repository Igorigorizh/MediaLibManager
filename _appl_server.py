import xmlrpc.client
import myMediaLib_adm
import myMediaLib_controller
from myMediaLib_CONST import mymedialib_cfg
import time
import sys
#import myMediaLib_model
#from medialib_pages import *

if __name__ == '__main__':
	
#	PlayerContr_serv = PlayerController()
#	PlayerContr_serv.runPlayerServer()
	cfgD = myMediaLib_adm.readConfigData(mymedialib_cfg)
	
	port = cfgD['appl_cntrl_port']
	dbl_appl = xmlrpc.client.ServerProxy('http://%s:%s'%(str(socket.gethostname()),str(port)))		
	
	try:
		dbl_appl.appl_status()['stop_flag']
		print("Application server already running -> no copy allowed")
		print("Wait 5 sec for exit...")
		time.sleep(5)
		
	except Exception as e:
		#print e

		ApplContr_serv = myMediaLib_controller.MediaLib_Application_RPC_server()
#	ApplContr_serv = myMediaLib_model.MediaLibPlayProcess()



#	commandD = {'search_entry': ['-394885814', '-1530884522', 
#		'1702136245', '-105095107', '529265438', '-1961472358',
#		 '-1509026889', '1998299829', '-1458783151', '189998416',
#		'1910909115', '-359689642', '1096565497', '650674108',
#		 '1700196659'], 'play_selected': 'PlaySelected','page_mode':''}
#	ApplContr_serv.Appl_Controller('main',{'page_mode':'do_search','search_term':'granada'})
#	ApplContr_serv.Appl_Controller('main',{'page_mode':''})
#	print ApplContr_serv.get_controller_instance().get_instance().PageGenerator('main',{'page_mode':''})
#	ApplContr_serv.Appl_Controller('search',commandD) 
#''.encode('utf8')
#	print 'ststus:',ApplContr_serv.getMediaLibPlayProcessContext()
		ApplContr_serv.runApplServer()
	
