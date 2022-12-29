import datetime
from medialib.myMediaLib_fp_tools import guess_TOC_from_tracks_list
from medialib.myMediaLib_fp_tools import FpGenerator

path_list = [b"./test/test_audio_data/test_flac_cue/",\
                b"./test/test_audio_data/test_ape_cue_tracks/",\
                b"./test/test_audio_data/test_mp3/"]
                
def test_FpGenerator_build_fp_task_param_single_image_cue():

    flac_image_cue_expected = [(b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 181.947 -ss 0.000 "./test/test_audio_data/test_flac_cue/temp1.wav"', b'./test/test_audio_data/test_flac_cue/temp1.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 71.987 -ss 181.947 "./test/test_audio_data/test_flac_cue/temp2.wav"', b'./test/test_audio_data/test_flac_cue/temp2.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 119.507 -ss 253.933 "./test/test_audio_data/test_flac_cue/temp3.wav"', b'./test/test_audio_data/test_flac_cue/temp3.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 289.520 -ss 373.440 "./test/test_audio_data/test_flac_cue/temp4.wav"', b'./test/test_audio_data/test_flac_cue/temp4.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 186.213 -ss 662.960 "./test/test_audio_data/test_flac_cue/temp5.wav"', b'./test/test_audio_data/test_flac_cue/temp5.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 177.080 -ss 849.173 "./test/test_audio_data/test_flac_cue/temp6.wav"', b'./test/test_audio_data/test_flac_cue/temp6.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 212.653 -ss 1026.253 "./test/test_audio_data/test_flac_cue/temp7.wav"', b'./test/test_audio_data/test_flac_cue/temp7.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 260.027 -ss 1238.907 "./test/test_audio_data/test_flac_cue/temp8.wav"', b'./test/test_audio_data/test_flac_cue/temp8.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 123.373 -ss 1498.933 "./test/test_audio_data/test_flac_cue/temp9.wav"', b'./test/test_audio_data/test_flac_cue/temp9.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 176.080 -ss 1622.307 "./test/test_audio_data/test_flac_cue/temp10.wav"', b'./test/test_audio_data/test_flac_cue/temp10.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 188.360 -ss 1798.387 "./test/test_audio_data/test_flac_cue/temp11.wav"', b'./test/test_audio_data/test_flac_cue/temp11.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 182.627 -ss 1986.747 "./test/test_audio_data/test_flac_cue/temp12.wav"', b'./test/test_audio_data/test_flac_cue/temp12.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 138.427 -ss 2169.373 "./test/test_audio_data/test_flac_cue/temp13.wav"', b'./test/test_audio_data/test_flac_cue/temp13.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 142.680 -ss 2307.800 "./test/test_audio_data/test_flac_cue/temp14.wav"', b'./test/test_audio_data/test_flac_cue/temp14.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 136.907 -ss 2450.480 "./test/test_audio_data/test_flac_cue/temp15.wav"', b'./test/test_audio_data/test_flac_cue/temp15.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 195.040 -ss 2587.387 "./test/test_audio_data/test_flac_cue/temp16.wav"', b'./test/test_audio_data/test_flac_cue/temp16.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 116.440 -ss 2782.427 "./test/test_audio_data/test_flac_cue/temp17.wav"', b'./test/test_audio_data/test_flac_cue/temp17.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 156.720 -ss 2898.867 "./test/test_audio_data/test_flac_cue/temp18.wav"', b'./test/test_audio_data/test_flac_cue/temp18.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 220.747 -ss 3055.587 "./test/test_audio_data/test_flac_cue/temp19.wav"', b'./test/test_audio_data/test_flac_cue/temp19.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 179.147 -ss 3276.333 "./test/test_audio_data/test_flac_cue/temp20.wav"', b'./test/test_audio_data/test_flac_cue/temp20.wav'), (b'ffmpeg -y -i "./test/test_audio_data/test_flac_cue/test.flac" -t 160.747 -ss 3455.480 "./test/test_audio_data/test_flac_cue/temp21.wav"', b'./test/test_audio_data/test_flac_cue/temp21.wav')]
    result_expected = {'scenario':'single_image_CUE','params': flac_image_cue_expected}
    path = b"./test/test_audio_data/test_flac_cue/" 
    fp = FpGenerator()
    assert fp.cue_folder_check_scenario_processing(path) == result_expected

def test_FpGenerator_build_fp_task_param_multy_tracks_cue():
    result_expected = {'scenario': 'multy_tracs_CUE', 'params': [b'./test/test_audio_data/test_ape_cue_tracks/01 - test_s.ape', b'./test/test_audio_data/test_ape_cue_tracks/02 - test_s.ape', b'./test/test_audio_data/test_ape_cue_tracks/03 - test_s.ape']}
    path =  b"./test/test_audio_data/test_ape_cue_tracks/"
    fp = FpGenerator()
    assert fp.cue_folder_check_scenario_processing(path) == result_expected

def test_FpGenerator_build_fp_task_param_multy_tracks():
    result_expected = {'scenario': 'only_tracks_wo_CUE', 'params': ['./test/test_audio_data/test_mp3/01 - test_s.mp3', './test/test_audio_data/test_mp3/02 - test_s.mp3', './test/test_audio_data/test_mp3/03 - test_s.mp3']}
    path = b"./test/test_audio_data/test_mp3/"
    fp = FpGenerator()
    assert fp.build_fp_task_param(path) == result_expected	
	

def test_guess_TOC_from_tracks_list():
    trackL = [
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/01. Der Sionitin Wiegenlied - Nun, ich singe! Gott, ich knie.flac',
        b"V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/02. Lamento - Ach, dass ich Wassers g'nug h\xc3\xa4tte.flac",
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/03. Ich suchte des Nachts in meinem Bette.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/04. Gott, hilf mir.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/05. O amantissime sponse.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/06. Chiaccona a 4 in C Major.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/07. Von Gott will ich nicht lassen, SWV 366.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/08. Kommt, ihr Stunden, macht mich frei.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/09. Aria. Ein kleines Kindelein.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/10. Bleib bei uns, denn es will Abend werden.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/11. Sonata a 6 in E Minor.flac',
        b'V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/12. Erbarm Dich mein, o Herre Gott, SWV 447.flac',
        b"V:/MUSIC/ORIGINAL_MUSIC/ORIGINAL_CLASSICAL/LArpeggiata - Christina Pluhar/_HI-RES/Christina Pluhar - Himmelsmusik (2018) [24-96]/13. Komm, s\xc3\xbcsser Tod, komm, sel'ge Ruh, BWV 478.flac"
    ]

    result_expected = {'discidInput': {'First_Track': 1, 'Last_Track': 13,
                                       'offsetL': [150, 33280, 64858, 90568, 118249, 165074, 185318, 211068, 248665,
                                                   261297, 286245, 309951, 328834],
                                       'total_lead_off': 339935},
                       'toc_string': '1 13 339935 150 33280 64858 90568 118249 165074 185318 211068 248665 261297 286245 309951 328834',
                       'trackDL': [{'sample_rate': 96000, 'full_length': 441.73333333333335,
                                    'full_time': datetime.timedelta(seconds=441), 'bitrate': 2468,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 421.04,
                                    'full_time': datetime.timedelta(seconds=421), 'bitrate': 2464,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 342.8,
                                    'full_time': datetime.timedelta(seconds=342), 'bitrate': 2495,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 369.0933333333333,
                                    'full_time': datetime.timedelta(seconds=369), 'bitrate': 2429,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 624.3333333333334,
                                    'full_time': datetime.timedelta(seconds=624), 'bitrate': 2408,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 269.92,
                                    'full_time': datetime.timedelta(seconds=269), 'bitrate': 2549,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 343.3333333333333,
                                    'full_time': datetime.timedelta(seconds=343), 'bitrate': 2465,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 501.29333333333335,
                                    'full_time': datetime.timedelta(seconds=501), 'bitrate': 2413,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 168.42666666666668,
                                    'full_time': datetime.timedelta(seconds=168), 'bitrate': 2380,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 332.64,
                                    'full_time': datetime.timedelta(seconds=332), 'bitrate': 2376,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 316.0933333333333,
                                    'full_time': datetime.timedelta(seconds=316), 'bitrate': 2564,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 251.77333333333334,
                                    'full_time': datetime.timedelta(seconds=251), 'bitrate': 2423,
                                    'bits_per_sample': 24},
                                   {'sample_rate': 96000, 'full_length': 148.01333333333332,
                                    'full_time': datetime.timedelta(seconds=148), 'bitrate': 2264,
                                    'bits_per_sample': 24}]
                       }
    assert guess_TOC_from_tracks_list(trackL) == result_expected

def test_CdTocGenerator_cue_folder_check_scenario_processing_cue_image():

    toc_expected = {}
    result_expected = {'scenario':'single_image_CUE','params': flac_image_cue_expected}
    path = b"./test/test_audio_data/test_flac_cue/" 
    cdtoc = CdTocGenerator()
    assert cdtoc.cue_folder_check_scenario_processing(path) == result_expected