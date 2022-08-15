import os
import time
import functools
import base64

from celery import Celery
from myMediaLib_scheduler import music_folders_generation_scheduler

app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379")
app.conf.imports = 'medialib'

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
	

	
music_folders_generation_scheduler = app.task(name='music_folders_generation_scheduler-new_recogn_name',serializer='json',bind=True)(base64_convert(music_folders_generation_scheduler))
										