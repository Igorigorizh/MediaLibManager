import os
import time
import functools
import base64

from celery import Celery
from myMediaLib_scheduler import music_folders_generation_scheduler
from myMediaLib_tools import get_FP_and_discID_for_album
app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379")
app.conf.imports = 'medialib'
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['application/json', 'application/x-python-serialize']

@app.task(name="hello")
def hello():
	time.sleep(10)
	print("Hello there")
	return True
	

def base64_convert(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		val = func(*args, **kwargs)
		if type(val) == list:
			val = [base64.b64encode(a) for a in val]
		elif type(val) == bytes:
			val = base64.b64encode(val)
		elif type(val) == dict:
			val = [base64.b64encode(val[a]) for a in val]
		return val
	return wrapper	
	

	
#music_folders_generation_scheduler = app.task(name='music_folders_generation_scheduler-new_recogn_name',serializer='json',bind=True)(base64_convert(music_folders_generation_scheduler))
music_folders_generation_scheduler = app.task(name='music_folders_generation_scheduler-new_recogn_name',serializer='json',bind=True)(music_folders_generation_scheduler)	


@app.task(name="worker.callback")
def callback(result):
	print('Tuta')
	folderL = result
	for folder_name in folderL:
		task_fp_res = app.send_task('get_FP_and_discID_for_album',(folder_name, 0, 'multy', 'FP', 'ACOUSTID_FP_REQ', 'MB_DISCID_REQ'))
		
	print(result)
	

get_FP_and_discID_for_album = app.task(name='get_FP_and_discID_for_album',bind=True)(get_FP_and_discID_for_album)	

def fp_multy_scheduler(app, path):
	task_list = []
	task_first_res = app.send_task('music_folders_generation_scheduler-new_recogn_name',(p2,[],[]))
	

if __name__ == '__main__':
	app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://192.168.1.65:6379")
	app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://192.168.1.65:6379")
	
	task_list = []
	p3 = '/home/medialib/MediaLibManager/music/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar'
	p2 = '/home/medialib/MediaLibManager/music/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/Vivaldi/Antonio Vivaldi - 19 Sinfonias and Concertos for Strings and Continuo/'
	task_first_res = app.send_task('music_folders_generation_scheduler-new_recogn_name',(p2,[],[]),link=callback.s())
	
			
	#print(task_first_res.result)
	folderL = task_first_res.result
	for folder_name in folderL:
		#task_fp_res = app.send_task('get_FP_and_discID_for_album',(folder_name, 0, 'multy', 'FP', 'ACOUSTID_FP_REQ', 'MB_DISCID_REQ'))
		pass
	
	