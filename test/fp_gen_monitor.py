import sys
#windows path trick
sys.path.insert(0,'./medialib')
import pickle
from flask import Flask
import os

dump_path = b'//192.168.1.66/OMVNasUsb/MUSIC/ORIGINAL_MUSIC/ORIGINAL_EASY/Los Incas - El Condor Pasa (1985)/fpgen_1652531874.dump'
with open(dump_path, 'rb') as f:
	sD = pickle.load(f)

app = Flask(__name__)

@app.route('/')
def index():
	return 'FP and discId generation routine with Musicbrainz and acoustId response check'

@app.route('/dump/<num>')
def dump(num):
	
	res = '---------------<BR>'    
	cnt = 1
	for item in sD['fpDL'][int(num)]['convDL']:
		try:
			res += '<BR><BR>%i------[%s]<BR>'%(cnt,str(sD['fpDL'][int(num)]['album_path'],'utf-8'))
		except:
			pass 
		res += str(item['response'])
		cnt+=1        
	return res
if __name__ == '__main__':
	app.run()