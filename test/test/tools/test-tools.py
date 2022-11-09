import wave, struct
def make_wav_silent_sample(fname,duration):
	t = time.time()
	sampleRate = 44100.0 # hertz
	d_duration = 1.0*60*60 # seconds
	frequency = 10400.0 # hertz
	channel_num = 2
	obj = wave.open(fname,'w')
	obj.setnchannels(channel_num) # stereo
	obj.setsampwidth(2)
	obj.setframerate(sampleRate)
	for i in range(duration*channel_num):
		if i%(1000000*channel_num) == 0:
			print(int(i/(1000000*channel_num)), end=' ',flush=True)
		data = struct.pack('<h', 120)
		obj.writeframesraw( data )
	print("Done")
	obj.close()
	print("Saved after sec:",time.time()-t)