import xmlrpc.client
import myMediaLib_adm
import myMediaLib_model
import subprocess
if __name__ == '__main__':
	
#	PlayerContr_serv = PlayerController()
#	PlayerContr_serv.runPlayerServer()
	cfgD = myMediaLib_adm.readConfigData(myMediaLib_adm.mymedialib_cfg)
	
	port = cfgD['player_cntrl_port']
	dbl_appl = xmlrpc.client.ServerProxy('http://127.0.0.1:%s'%(str(port)))	
	try:
		dbl_appl.get_status()['playBack_Mode']
		print("Player server already running -> no copy allowed")
		print("Wait 5 sec for exit...")
		time.sleep(5)
	except Exception as e:
		#print e
		PlayerContr_serv = myMediaLib_model.PlayerController()
		PlayerContr_serv.runPlayerServer()

#process = subprocess.Popen(['c:\Python26\python2.exe',  'C:\My_projects\MyMediaLib\_appl_server.py'])