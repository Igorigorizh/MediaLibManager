import wave, struct
import time
	
def generate_wav_silent_copy(fname_src,fname_dest):
	""" Generates silent copy of input wav file
		Uses for cue single image tests. File size after recoding to flac, wv, ape etc.. significantly less than original wav

	"""
	with wave.open(fname_src, 'r') as wavefile:
		nchannels, sampwidth, framerate, nframes, _, _ = wavefile.getparams()	
	
	# copy audio properties to output file	
	obj = wave.open(fname_dest,'w')	
	obj.setnchannels(nchannels)
	obj.setsampwidth(sampwidth)
	obj.setframerate(framerate)
	
	# to speedup generation process frames writing by blocs which size=step 
	step = 10000
	t = time.time()
	frames_range = nframes*sampwidth
	for i in range(step,frames_range,step):
		if i%(10000000*sampwidth) == 0:
			print(int(i/(10000000*sampwidth)), end=' ',flush=True)
		data = struct.pack('<%ih'%step, *iter([120]*step))
		obj.writeframesraw( data )
		
	# finaly add tail part = frames_range - i
	data = struct.pack('<%ih'%(frames_range-i), *iter([120]*(frames_range-i)))
	obj.writeframesraw( data )	
	obj.close()	
	print("Done in %i sec"%(time.time()-t))
	
if __name__ == '__main__':
	import argparse	
	parser = argparse.ArgumentParser(description='media lib tools wav silent copy')	
	parser.add_argument('src_wav', metavar='source wave file',
                        help='src_wav')	
	parser.add_argument('dest_wav', metavar='silence copy wave file',
                        help='dest_wav')						
	args = parser.parse_args()
	print(args)	
	generate_wav_silent_copy(args.src_wav,args.dest_wav)