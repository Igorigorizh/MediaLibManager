# -*- coding: utf-8 -*-
import re
import os
import datetime
import chardet
import logging
import zlib
import operator
import collections

from os import curdir, sep, getcwd
import os.path
from pathlib import Path

from mutagen import File
from mutagen.apev2 import APEv2, error
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wavpack import WavPack, error as WavPackError
from mutagen.dsf import DSF
from mutagen.mp4 import MP4
from mutagen.monkeysaudio import MonkeysAudioInfo

from medialib import BASE_ENCODING
from medialib.myMediaLib_fs_util import is_only_one_media_type

logger = logging.getLogger('controller_logger.cue')


def myMusicStr2TimeDelta(strTime):
    l = [int(a) for a in strTime.split(':')]

    return datetime.timedelta(hours=l[0], minutes=l[1], seconds=l[2], milliseconds=(l[3] / 75) * 1000)


def sec2hour(sec):
    return '%02i' % (int(sec / 3600)) + ':' + '%02i' % (int(int(sec % 3600) / 60)) + ':' + '%02i' % (sec % 60) + ':00'


def sec2min(secs):
    if not isinstance(secs, float):
        # raise CodingError('non-float passed to sec2min')
        return ''
    return '%d:%.2d' % (int(secs / 60), secs % 60)


def detect_cue_scenario(album_path, *args):
    """ Detects CUE processing scenario: single image cue, multy tracks image cue, multy tracs album (NO CUE), multy format mix, uncompatible CUE """
    image_cue = ''

    cueD = {}
    cueD = {}
    orig_cue_title_cnt = 0
    f_numb = 0
    real_track_numb = 0
    error_logL = []
    cue_state = {'single_image_CUE': False, 'multy_tracs_CUE': False, 'only_tracks_wo_CUE': False,
                 'media_format_mixture': False}

    if not os.path.exists(album_path):
        print('---!Album path Error:%s - not exists' % album_path)
        error_logL.append('[CUE check]:---!Album path Error:%s - not exists' % album_path)
        return {'RC': -1, 'f_numb': 0, 'orig_cue_title_numb': 0, 'title_numb': 0, cue_state: cue_state,
                'error_logL': error_logL}

    filesL = os.listdir(album_path)

    cue_cnt = 0
    # Валидация CUE через соответствие реальным данным для цели дальнейшей разбивки
    # Либо это нормальный CUE (TITLES > 1 и образ физически есть) -> нужна разбивка на трэки - ОК
    # Либо это любой в тч 'битый' CUE, но есть отдельные трэки -> разбивка не нужна проверить соотв. количества трэков и титлов в #`CUE приоритет tracks и сверка с КУЕ

    normal_trackL = []

    for a in filesL:
        # print(a)
        ext = os.path.splitext(a)[1]

        if ext == b'.cue':
            print('in cue')
            image_cue = a

            normal_trackL = []
            try:
                cueD = simple_parseCue(album_path + image_cue)
            except Exception as e:
                print(e)
                return {'RC': -1, 'f_numb': 0, 'orig_cue_title_numb': 0, 'title_numb': 0, 'errorL': ['cue_corrupted'],
                        cue_state: cue_state}

            cue_cnt += 1
            if cue_cnt > 1:
                print('--!-- Error Critical! several CUE Files! Keep only one CUE!')
                error_logL.append('[CUE state check]:--!-- Error Critical! several CUE Files! Keep only one CUE!')
                return {'RC': -1, 'f_numb': 0, 'orig_cue_title_numb': 0, 'title_numb': 0,
                        'errorL': ['cue', 'cue_error', 'several cue'], cue_state: cue_state, 'error_logL': error_logL}

            if 'orig_file_pathL' in cueD:
                orig_cue_title_cnt = len(cueD['songL'])
                real_track_numb = len(cueD['orig_file_pathL'])
                if real_track_numb == 1:
                    if os.path.exists(cueD['orig_file_pathL'][0]['orig_file_path']):
                        cue_state['single_image_CUE'] = True
                        break
                elif real_track_numb > 1:
                    cue_state['multy_tracs_CUE'] = True
                    for orig_file in cueD['orig_file_pathL']:
                        if not os.path.exists(orig_file['orig_file_path']):
                            print(
                                'Failed CUE albumfile not exists:%s' % str(orig_file['orig_file_path'], BASE_ENCODING))
                            error_logL.append(
                                '[CUE state check]: multy track mode. no real media detected for cue title:%s' % str(
                                    orig_file['orig_file_path'], BASE_ENCODING))
                    break
                else:
                    error_logL.append('[CUE state check]:--!-- Error Critical! - no media detected')
                    return {'RC': -1, 'title_numb': 0, 'errorL': ['cue_corrupted', 'no media detected'],
                            'orig_cue_title_numb': orig_cue_title_cnt, cue_state: cue_state, 'cueD': cueD,
                            'f_numb': real_track_numb, 'error_logL': error_logL}
        else:

            # если до этого найден CUE, то проверка на only tracs не нужно
            if cue_state['single_image_CUE'] or cue_state['multy_tracs_CUE']: continue
            ext = os.path.splitext(a)[1]
            # print('in tracks 1',ext)

            if ext in [b'.ape', b'.mp3', b'.flac', b'.wv', b'.m4a', b'.dsf']:
                # print('in tracks 3')
                normal_trackL.append(a)

    RC = real_track_numb
    if (not cue_state['single_image_CUE'] and not cue_state[
        'multy_tracs_CUE']) and normal_trackL and is_only_one_media_type(filesL):
        cue_state['only_tracks_wo_CUE'] = True
    elif (not cue_state['single_image_CUE'] and not cue_state[
        'multy_tracs_CUE']) and normal_trackL and not is_only_one_media_type(filesL):
        cue_state['media_format_mixture'] = True

    # 1. ОК - single CUE, 1 -original image, several tracks frof cue -> split is possible
    # 2. ОК - several tracks > 1 ape,mp3,flac - no mix of them -> no split
    # 3. OK 2. tracks > 1 + splited CUE files from CUE tracks = cue title - Good cue can me ignored  -> no needed
    # 4.  2. tracks > 1 + cue with no existed 1 image file  - BAD cue can me ignored  -> no needed
    # 5.  2. tracks > 1 + cue with no existed several slitted tracks files - BAD cue can me ignored  -> no needed

    # В этом месте необходимо иметь образ wav и ссылку на него во временном CUE

    return {'RC': RC, 'cue_state': cue_state, 'orig_cue_title_numb': orig_cue_title_cnt, 'title_numb': 0,
            'f_numb': real_track_numb, 'cueD': cueD, 'normal_trackL': normal_trackL, 'error_logL': error_logL}


def get_audio_object(fname):
    audio = None
    full_length = bitrate = 0
    if not isinstance(fname, bytes):
        raise Exception('Error: Not Unicode filename')
    file_extL = [b'.flac', b'.mp3', b'.ape', b'.wv', b'.m4a', b'.dsf']
    file_ext = os.path.splitext(fname)[-1]
    
    if file_ext in file_extL:
        if b'ape' in file_ext:
            with open(fname, 'rb') as f:
                try:
                    audio = MonkeysAudioInfo(f)
                except Exception as e:
                    print('probably MonkeysAudioHeaderError_1', fname)
                    return {'Error': e}
            
            if audio.length:
                return {
                    'sample_rate': audio.sample_rate,
                    'full_length': audio.length,
                    'full_time': myMusicStr2TimeDelta(sec2hour(audio.length)),
                    'bitrate': round(os.path.getsize(fname) * 8 / 1000 / audio.length),
                    'bits_per_sample': audio.bits_per_sample
                }
            else: 
                return {
                        'sample_rate': audio.sample_rate, 'full_length': audio.length,
                        'full_time': myMusicStr2TimeDelta(sec2hour(audio.length)), 'bitrate': 0,
                        'bits_per_sample': audio.bits_per_sample
                        }
        try:
            if b'flac' in file_ext: audio = FLAC(fname)
            if b'm4a' in file_ext: audio = MP4(fname)
            if b'dsf' in file_ext: audio = DSF(fname)
            if b'wv' in file_ext: audio = WavPack(fname)
            if b'mp3' in file_ext: audio = MP3(fname, ID3=EasyID3)
        except Exception as e:
            print(f'{file_ext[1:]} mutagen error')
            return {'Error': e}

        full_length = audio.info.length
        tmp_length = sec2hour(full_length)
        full_time = myMusicStr2TimeDelta(tmp_length)
        if b'mp3' in file_ext:
            bits_per_sample = None
        else:
            bits_per_sample = audio.info.bits_per_sample
        if b'flac' in file_ext or  b'dsf' in file_ext or b'mp3' in file_ext:
            bitrate = round(audio.info.bitrate / 1000)
        else:    
            if full_length: 
                # general format case
                bitrate = round(os.path.getsize(fname) * 8 / 1000 / full_length)

        sample_rate = audio.info.sample_rate
        return {'sample_rate': sample_rate, 'full_length': full_length, 'full_time': full_time,
                'bitrate': bitrate,'bits_per_sample':bits_per_sample}


def parseCue(fName, *args):
    # Чтобы не перегружать функцию parseCue, перед ee вызовом обязательно проверить на
    # существование файла!
    # Т.е. тут мы уже предполагаем, что с именем файла и его существованием все ОК
    # Возможны разные сценании UTF-8. utf- в имени, проверка пред вызовом. UTF- в данных
    # самого файла.
    # Для единообразия требуем имя файла всегда в unicode byte string!
    # Два реежима потрэковый и однообраз сильно отличаются по сценариям извлечения данных
    # 1. Время можно вычислить из INDEX разности для Cue - однообраз, для трэкового - из
    # физических файлов
    # индексы в image CUE могут быть с pregap и его надо игнорировать, беря только вторые
    # индексы для вычисления времени  в режиме only_file в single image возвращает количество
    # cue_tracks_number = 0 =>  чтобы узнать реальное количество трэков надо вызывать без параметров
    #
    # Имена файлов необходимо возвращать в абсолютном формате, т.к. затем абсолютные имена будут\
    # использоваться для извлечения других данных
    if not isinstance(fName, bytes):
        logger.critical('Exception at in parseCue: only unicode byte string allowed')
        return {'Error': 'Not Unicode filename'}
    try:
        logger.debug('in parseCue - start')
    except:
        print('No logger attached at local execution')
        pass
    char_codec = line_album_codec = line_file_codec = line_track_codec = line_perform_main_codec = line_perform_track_codec = {}
    cue_crc32 = 0

    # since it not known how data encoded inside we provide both scenariouus with/without UTF
    try:
        f = open(fName, 'r', encoding=BASE_ENCODING)
    except Exception as e:
        print('File not found:', fName, char_codec)
        logger.critical('Exception at 57[%s] in parseCue' % (str(e)))
        return {'Error': e}

    cue_f_name_abs = fName

    nonUnicode = False

    try:
        l = f.readlines()
    except UnicodeDecodeError as e:
        print('Exception at 71[%s] in parseCue switch to non Unicode' % (str(e)))
        logger.info('Exception at 71[%s] in parseCue switch to non Unicode' % (str(e)))
        f.close()

        nonUnicode = True

    if nonUnicode:
        f = open(fName, 'r')
        try:
            l = f.readlines()
            f.close()
        except Exception as e:
            logger.critical('Exception at 84[%s] in parseCue' % (str(e)))
            f.close()
            return {'Error': e}
    track_flag = False
    album = ''
    full_time = ''
    orig_file = ''
    orig_file_path = ''
    orig_file_pathL = []
    perform_main = ''
    track_num = 0
    next_frame = 0
    trackD = {}
    bitrate = 0
    first_track_offset = 150
    pregap = 0
    total_track_sectors = 0
    offsetL = []

    # для смещений медиафайлов ape, flac,wv etc, если мультитрэк
    offset_mediaL = []
    lead_out_track_offset = 0
    sample_rate = 0
    got_file_info = False
    orig_file_path_exist = False
    is_cue_multy_tracks = False
    is_non_compliant_eac_cue = False
    check_fileL = []
    exists_track_stackL = []
    temp_track_stackL = []
    delta = 0
    bitrateL = []

    try:
        # cue_crc32 = zlib.crc32(fNameRel.encode(BASE_ENCODING))
        if isinstance(fName, str):
            cue_crc32 = zlib.crc32(fName.encode(BASE_ENCODING))
        elif isinstance(fName, bytes):
            cue_crc32 = zlib.crc32(fName)
    except Exception as e:
        print('Error crc32 generate')
        logger.critical('Exception [%s] in parseCue  [cue crc32 generation]' % (str(e)))
        return {'Error': e}

    # define most possible coding schema
    cue_termsL = ['file ', 'title ', 'performer ']
    codec_freqL = []
    tobe_suppressed_codecL = ['MacCyrillic', 'ascii', 'TIS-620']
    for a in l:
        for term in cue_termsL:
            if a.lower().strip().find(term) == 0:
                codec_freqL.append(chardet.detect(bytes(a, encoding=BASE_ENCODING))['encoding'])
    counter = collections.Counter(codec_freqL)
    most_codec = str(counter.most_common(1)[0][0])

    # below is heuristical aproach for codec change when 'ascii' is a major but also local specific is met so ignor ascii!
    # better aproach 1. Предотвратить появление копии потрэковой альбома если это CUE
    # 2. выбирать кодек файла на втором проходе, если при первомо происходит неправильный выбор кодировки файла CUE
    # 3. надо делать несколько проходный прелоад сценарий
    if len(counter) > 1 and most_codec in tobe_suppressed_codecL:
        most_codec = str(counter.most_common(2)[1][0])
        # print 'codec changed:',most_codec,counter.most_common(1)[0][0]
        logger.warning('in parseCue - codec changed from:%s to %s ' % (
            str(counter.most_common(1)[0][0]), str(counter.most_common(2)[1][0])))

    logger.debug('in parseCue - codec statistic:%s' % (str(counter)))
    # most_codec = 'cp1251'

    print("----------------^^^^ParseCue-stamp^^^^^^^^^^^^^^^^^^----------")
    print([most_codec], counter.most_common(1))
    track_offset_cnt = 0
    for a in l:
        if a.lower().strip().find('pregap ') == 0:
            lst = a.split()

            # convert MSF to frames: 1 sec = 75 frames, MM(min):SS(sec):FF(frame) -> MM*60*75+SS*75+FF
            MSF_l = lst[1].split(':')
            pregap = int(MSF_l[0]) * 60 * 75 + int(MSF_l[1]) * 75 + int(MSF_l[2])
            print(pregap)
        if a.lower().strip().find('file ') == 0:

            # print chardet.detect(a)
            orig_file_path = orig_file = b""

            if track_flag:
                track_flag = False
            lst = re.split('([^"]*")(.*)("[^"]*)', a)
            line_file_codec = chardet.detect(bytes(lst[2], encoding=BASE_ENCODING))

            if not isinstance(lst[2], bytes):
                orig_file = bytes(lst[2], encoding=BASE_ENCODING)
            else:
                orig_file = lst[2]

            orig_file_path = os.path.join(os.path.dirname(fName) + b'/', orig_file)
            # print(os.path.dirname(fName),orig_file)

            fType = os.path.splitext(orig_file)[-1][1:].decode()

            orig_file_path_exist = False
            if os.path.exists(orig_file_path):
                orig_file_path_exist = True
                if orig_file_path not in exists_track_stackL:
                    exists_track_stackL.append(orig_file_path)
            else:
                print('Check CUE:', [orig_file_path])
                logger.warning('in parseCue - incomplient orig file not found  [%s]' % (orig_file_path))

            if len(exists_track_stackL) > 1:
                is_cue_multy_tracks = True

            if orig_file_path_exist and 'with_bitrate' in args:
                audio = get_audio_object(orig_file_path)

                full_length = audio['full_length']
                full_time = audio['full_time']
                bitrate = audio['bitrate']
                sample_rate = audio['sample_rate']
                bits_per_sample = audio['bits_per_sample']
                # For all formats  keep the same approach of TOC data calculation. Only for multy tracks cue
                lead_out_track_offset = int(full_length * 75) + first_track_offset

                total_track_sectors = total_track_sectors + int(full_length * 75) + 1
                if track_num == 0:
                    offset_mediaL.append(first_track_offset + pregap)
                    next_frame = total_track_sectors - track_offset_cnt - pregap + first_track_offset - 1
                else:
                    offset_mediaL.append(next_frame)
                next_frame = total_track_sectors - track_offset_cnt - pregap + first_track_offset - 1
                track_offset_cnt += 1

            if orig_file_path != '' and orig_file_path != b"":

                if isinstance(orig_file_path, str):
                    orig_file_path_crc32 = zlib.crc32(orig_file_path.encode(BASE_ENCODING))
                elif isinstance(orig_file_path, bytes):
                    orig_file_path_crc32 = zlib.crc32(orig_file_path)

                orig_file_pathL.append(
                    {'orig_file_path': orig_file_path, 'file_exists': orig_file_path_exist, 'BitRate': bitrate,
                     'SampleRate': sample_rate, 'Time': full_time, 'file_crc32': orig_file_path_crc32})

            continue

        if 'only_file' in args:
            continue

        if a.lower().strip().find('track ') == 0:
            track_flag = True
            tracL = a.split()

            # Находимся в секции TRACK	и получаем новый номер трэка
            if tracL[0].lower() == 'track' and tracL[2].lower() == 'audio':
                track_num = int(tracL[1])
                trackD[track_num] = {'Title': '', 'Album': '', 'BitRate': 0, 'OrigFile': '', 'Time': '00:00',
                                     'Performer': '', 'SampleRate': 0, 'start_in_sec': 0, 'total_in_sec': 0}

                # Делаем проверку для multytrack, что к этому моменту для трэка > 1
                if track_num > 1:
                    orig_file_path_number = len(orig_file_pathL)
                    if (orig_file_path_number > 1 and orig_file_path_number == track_num) or orig_file_path_number == 1:
                        pass
                    else:
                        is_non_compliant_eac_cue = True
                        print("non_compliant_eac_cue 331", orig_file_path_number, track_num)
                continue

        if a.lower().strip().find('title ') == 0 and not track_flag and orig_file_pathL == []:
            lst = re.split('([^"]*")(.*)("[^"]*)', a)
            album = lst[2].strip()

            line_album_codec = chardet.detect(bytes(lst[2], encoding=BASE_ENCODING))
            continue

        elif a.lower().strip().find('performer ') == 0 and not track_flag:
            lst = re.split('([^"]*")(.*)("[^"]*)', a)
            try:
                line_perform_main_codec = chardet.detect(bytes(lst[2], encoding=BASE_ENCODING))
                perform_main = lst[2].strip()
            except UnicodeDecodeError as e:
                perform_main = lst[2].strip().decode(BASE_ENCODING)
            except Exception as e:
                perform_main = "decode_utf8_Error perform_main".decode(BASE_ENCODING)
                print('error:', lst, l[0], l[1], l[2], l[3], l[4], l[5])
            continue

        if a.lower().strip().find('title') == 0 and track_flag and track_num > 0:
            #			print 'title here!!!',track_num
            lst = re.split('([^"]*")(.*)("[^"]*)', a)
            try:
                line_track_codec = chardet.detect(bytes(lst[2], encoding=BASE_ENCODING))
            except Exception as e:
                logger.critical('Exception [%s] in parseCue  [at title chardet]' % (str(e)))
                logger.critical('Exception [%s] in parseCue  [at title chardet-2]' % (str([a, track_num])))
                print('parseCue Error: line', track_num)
                return {'Error': str(e), 'ErrorData': [lst, a, track_num]}

            try:

                trackD[track_num]['Title'] = lst[2].strip()
            except UnicodeDecodeError as e:
                trackD[track_num]['Title'] = lst[2].strip().decode(BASE_ENCODING)
            except Exception as e:
                trackD[track_num]['Title'] = 'decode_utf8_Error'.decode(BASE_ENCODING)
                trackD[track_num]['TitleUndecode'] = lst[2]

            try:
                trackD[track_num]['Album'] = album
            except UnicodeDecodeError as e:
                trackD[track_num]['Album'] = album.decode(BASE_ENCODING)
            except Exception as e:
                trackD[track_num]['Album'] = 'decode_utf8_Error'.decode(BASE_ENCODING)


        #
        elif a.lower().strip().find('performer ') == 0 and track_flag and track_num > 0:
            #			print 'rerformer here!!!',track_num
            lst = re.split('([^"]*")(.*)("[^"]*)', a)
            line_perform_track_codec = chardet.detect(bytes(lst[2], encoding=BASE_ENCODING))
            try:
                trackD[track_num]['Performer'] = lst[2].strip()
            except Exception as e:
                logger.critical('Exception [%s] in parseCue  [at performer]' % (str(e)))
                pass
            try:
                trackD[track_num]['Performer_CRC32'] = zlib.crc32(
                    trackD[track_num]['Performer'].lower().encode(BASE_ENCODING))
            except Exception as e:
                logger.critical('Exception [%s] in parseCue  [at performer crc32]' % (str(e)))
                pass

        elif a.lower().strip().find('index ') == 0 and track_flag and track_num > 0:
            #			print 'indx here!!!',track_num
            lst = a.split()
            index = lst[1]

            # Calculate track Frame offset for  final TOC
            index_time = '00:' + lst[2]

            if int(index) == 0:
                trackD[track_num]['index'] = [index_time, 0]
            elif int(index) == 1:
                # Поддержка нескольких индексов INDEX 1 и INDEX 0
                if 'index' in trackD[track_num]:
                    # один INDEX уже есть, заводим второй индекс
                    trackD[track_num]['index'] = [trackD[track_num]['index'][0], index_time]
                else:
                    # регистрирует первый индекс
                    trackD[track_num]['index'] = [index_time, index_time]

                cur_delta = myMusicStr2TimeDelta(trackD[track_num]['index'][1]) - myMusicStr2TimeDelta(
                    trackD[track_num]['index'][0])

                # Только для single IMAGE вычисляем длину трэка в секундах как разница между соседнмини трэками, только однофайлового CUE
                if track_num > 1 and not is_cue_multy_tracks:
                    try:
                        # delta = myMusicStr2TimeDelta(trackD[track_num]['index'][1])-myMusicStr2TimeDelta(trackD[track_num-1]['index'][1])-cur_delta
                        delta = myMusicStr2TimeDelta(trackD[track_num]['index'][1]) - myMusicStr2TimeDelta(
                            trackD[track_num - 1]['index'][1])
                    except Exception as e:
                        print('Exception [%s] in parseCue  [at myMusicStr2TimeDelta], check time', e)
                        logger.critical('Exception [%s] in parseCue  [at myMusicStr2TimeDelta]' % (str(e)))
                        delta = datetime.timedelta(0)

                    trackD[track_num]['start_in_sec'] = myMusicStr2TimeDelta(
                        trackD[track_num]['index'][1]).total_seconds()
                    trackD[track_num - 1]['total_in_sec'] = delta.total_seconds()
                    trackD[track_num - 1]['Time'] = str(delta)[2:7]

                if track_num == 1:
                    # 1-st Frame offset = 150
                    offsetL.append(first_track_offset + pregap)
                if track_num > 1 and not is_cue_multy_tracks:
                    # только для single image cue формируем список смещений таким образом. для multy tracks формирование на физическом уровне
                    # convert MSF to frames: 1 sec = 75 frames, MM(min):SS(sec):FF(frame) -> MM*60*75+SS*75+FF
                    MSF_l = lst[2].split(':')
                    offsetL.append(
                        pregap + first_track_offset + int(MSF_l[0]) * 60 * 75 + int(MSF_l[1]) * 75 + int(MSF_l[2]))
    # print(track_num,index,lst[2],int(MSF_l[0])*60*75 + int(MSF_l[1])*75+int(MSF_l[2]))

    if is_cue_multy_tracks:
        # если мультитрэк то заменяем список смещений
        print("---------Multytracks-----------")
        offsetL = offset_mediaL
        lead_out_track_offset = next_frame
        if len(exists_track_stackL) != len(orig_file_pathL):
            is_non_compliant_eac_cue = True
            print("non_compliant_eac_cue 456")

    if 'only_file' in args:
        pass
        if track_num == 0 and len(orig_file_pathL) > 1:
            track_num = len(orig_file_pathL)
    else:

        for a in trackD:
            if trackD[a]['Performer'] == '':
                trackD[a]['Performer'] = perform_main
                try:
                    trackD[a]['Performer_CRC32'] = zlib.crc32(perform_main.encode(BASE_ENCODING))
                except Exception as e:
                    logger.critical('Exception [%s] in parseCue  [at performer main crc32]' % (str(e)))
                    pass
            if trackD[a]['Album'] == '':
                trackD[a]['Album'] = album

            # For image cue restore OrigFile from 1st track
            if not is_cue_multy_tracks:
                trackD[a]['OrigFile'] = orig_file_pathL[0]['orig_file_path']
                if 'with_bitrate' in args:
                    trackD[a]['BitRate'] = orig_file_pathL[0]['BitRate']
                    trackD[a]['SampleRate'] = orig_file_pathL[0]['SampleRate']
            # for Multy track replicate from orig_file_pathL
            elif is_cue_multy_tracks:
                orig_file = orig_file_pathL[a - 1]['orig_file_path']
                try:
                    trackD[a]['OrigFile'] = orig_file
                except UnicodeDecodeError as e:
                    trackD[a]['OrigFile'] = orig_file.decode(BASE_ENCODING)
                except Exception as e:
                    trackD[a]['OrigFile'] = 'decode_utf8_Error'.decode(BASE_ENCODING)

                if 'with_bitrate' in args:
                    trackD[a]['BitRate'] = orig_file_pathL[a - 1]['BitRate']
                    trackD[a]['SampleRate'] = orig_file_pathL[a - 1]['SampleRate']
                    time = str(orig_file_pathL[a - 1]['Time'])
                    if time[:2] == '0:':
                        time = time[2:7]
                    trackD[a]['Time'] = time

        if 'with_bitrate' in args and not is_cue_multy_tracks:
            # для вычисления времени последнего трэка нужна длина всего файла, это только с with_bitrate
            trackD[track_num]['total_in_sec'] = full_length - myMusicStr2TimeDelta(
                trackD[track_num]['index'][1]).total_seconds()
            # trackD[track_num]['start_in_sec']	= myMusicStr2TimeDelta(trackD[track_num]['index'][1]).total_seconds()
            try:
                delta = str(full_time - myMusicStr2TimeDelta(trackD[track_num]['index'][1]))
            except Exception as e:
                print(e)
                print('Error in parseCue-> myMusicStr2TimeDelta', trackD[track_num], track_num)
                logger.critical('Exception at 331 [%s] in parseCue  [myMusicStr2TimeDelta]' % (str(e)))
                logger.critical('Exception at 331 [%s] in parseCue  [myMusicStr2TimeDelta]-2' % (fName))
                logger.critical('Exception at 331 [%s] [%s] in parseCue  [myMusicStr2TimeDelta]-3' % (
                    str(full_time), str(myMusicStr2TimeDelta(trackD[track_num]['index'][1]))))

            if delta[:2] == '0:':
                delta = delta[2:7]

            trackD[track_num]['Time'] = delta
        elif 'with_bitrate' not in args and not is_cue_multy_tracks:
            # без длины всего образа нельзя вычислить последний трэк
            trackD[track_num]['Time'] = '00:00'

    #	print 'in parseCue - finished with [%s %s]'%(str(len(exists_track_stackL)),str(len(orig_file_pathL)))

    #	for a in exists_track_stackL:
    #		print a
    logger.debug('in parseCue - finished with [%s %s]' % (str(len(exists_track_stackL)), str(len(orig_file_pathL))))
    return {'trackD': trackD, 'is_non_compliant_eac_cue': is_non_compliant_eac_cue,
            'is_cue_multy_tracks': is_cue_multy_tracks, 'orig_file_pathL': orig_file_pathL, 'fType': fType,
            'cue_tracks_number': track_num, 'cue_crc32': cue_crc32, 'cue_f_name': fName,
            'lead_out_track_offset': lead_out_track_offset, 'offsetL': offsetL}


def simple_parseCue(fName, *args):
    """
        Gets track list from cue with relative file path
    """
    # Collect only filenames from CUE
    if not isinstance(fName, bytes):
        logger.critical('Exception at in simple_parseCue: Not Unicode filename')
        return {'Error': 'Not Unicode filename'}
    try:
        logger.debug('in simple_parseCue - start')
    except:
        print('No logger attached at local execution')
        pass

    char_codec = line_album_codec = line_file_codec = line_track_codec = line_perform_main_codec = line_perform_track_codec = {}
    fType = ''

    try:
        f = open(fName, 'r', encoding=BASE_ENCODING)
    except Exception as e:
        print('File not found:', fName, char_codec)
        logger.critical('Exception at 472[%s] in parseCue' % (str(e)))
        return {'Error': e, 'cue_file_name': fName}

    nonUnicode = False

    try:
        l = f.readlines()
    except UnicodeDecodeError as e:
        print('Exception at 482[%s] in parseCue switch to non Unicode' % (str(e)))
        logger.info('Exception at 482[%s] in parseCue switch to non Unicode' % (str(e)))
        f.close()

        nonUnicode = True

    if nonUnicode:
        f = open(fName, 'r')
        try:
            l = f.readlines()
            f.close()
        except Exception as e:
            logger.critical('Exception at 494[%s] in parseCue' % (str(e)))
            f.close()
            return {'Error': e, 'cue_file_name': fName}

    track_flag = False
    album = ''
    full_time = ''
    orig_file = ''
    orig_file_path = b""
    perform_main = ''
    orig_file_pathL = []
    track_num = 0
    trackD = {}
    got_file_info = False
    # внутри цикла надо разделить сценарий CUE single image и cue tracks
    for a in l:

        if a.lower().strip().find('track ') == 0:
            track_flag = True
            tracL = a.split()

            if tracL[0].lower() == 'track' and tracL[2].lower() == 'audio':
                track_num = int(tracL[1])
                continue

        if a.lower().strip().find('file ') == 0:

            lst = re.split('([^"]*")(.*)("[^"]*)', a)

            if not isinstance(lst[2], bytes):
                orig_file = bytes(lst[2], encoding=BASE_ENCODING)
            else:
                orig_file = lst[2]

            fType = os.path.splitext(orig_file)[-1][1:].decode()
            if fType == '':
                logger.critical('Critical error in simple_parseCue: file ext retrieve failed for:', a)
            orig_file_pathL.append(
                {'orig_file_path': os.path.join(os.path.dirname(fName) + b'/', orig_file), 'orig_file': orig_file,
                 'fType': fType})

    cue_songL = []
    for i in range(1, track_num + 1):
        # generate cue file name based tracklist for db storage and player processing
        cue_songL.append(fName + b"," + bytes(str(i), encoding=BASE_ENCODING))
    if fType == '':
        print('Error in fType:', orig_file_path)
    return {'orig_file_pathL': orig_file_pathL, 'songL': cue_songL, 'cue_tracks_number': track_num,
            'cue_file_name': fName}


def GetTrackInfoVia_ext(filename, ftype):
    logger.debug('in GetTrackInfoVia_ext - start [%s]' % str(ftype))
    # logger.debug('in GetTrackInfoVia_ext, file= %s'%(str([filename])))
    # print 'filename:',[filename],type(filename)
    # 'pL_info':pL_info
    audio = None
    bitrate = 0
    sample_rate = 0
    time = '00:00'
    time_sec = 0
    infoD = {}
    if ftype.lower() == 'flac':
        try:

            audio = FLAC(filename)
            full_length = audio.info.length
            # print('full_length',full_length)
            if full_length != 0:
                bitrate = int(round(float(audio.info.bitrate) / 1000))
                sample_rate = audio.info.sample_rate
                tmp_length = sec2hour(full_length)
                full_time = myMusicStr2TimeDelta(tmp_length)
                time_sec = int(full_length)
                time = full_time

        except IOError as e:
            logger.critical(' 713 Exception in GetTrackInfoVia_ext: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'time': '00:00', 'ftype': ftype}
        except Exception as e:
            logger.critical(' 711 Exception in GetTrackInfoVia_ext: %s' % (str(e)))
        except:
            logger.critical(' 716 Exception in GetTrackInfoVia_ext: %s' % (str('unknown mutagen error')))

    elif ftype.lower() == 'wv':
        try:
            audio = WavPack(filename)
        except Exception as e:
            print('WavPack data error reading', filename)
            logger.critical('GetTrackInfoVia_ext: WavPack data error reading %s' % (str(filename)))
            logger.critical('919 Exception in GetTrackInfoVia_ext: WavPack %s' % (str(e)))
        #	return {'Error':e,'error path':filename}
        if audio:
            try:
                full_length = audio.info.length
                if full_length != 0:
                    bitrate = int(round(os.path.getsize(filename) * 8 / 1000 / full_length))
                    sample_rate = audio.info.sample_rate
                    tmp_length = sec2hour(full_length)
                    full_time = myMusicStr2TimeDelta(tmp_length)
                    time_sec = int(full_length)
                    time = full_time

            except Exception as e:
                logger.critical(' 846 Exception in GetTrackInfoVia_ext wv: %s' % (str(e)))
            except IOError as e:
                logger.critical(' 848 Exception in GetTrackInfoVia_ext wv: %s' % (str(e)))
                return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)],
                        "artist": b"No Artist",
                        "album": b"No Album",
                        "bitrate": 0,
                        'sample_rate': 0,
                        'time': '00:00',
                        'ftype': ftype
                        }
            except:
                logger.critical(' 851 Exception in GetTrackInfoVia_ext wv: %s' % (str('unknown mutagen error')))

    elif ftype.lower() == 'm4a':
        try:

            audio = MP4(filename)
            full_length = audio.info.length
            if full_length != 0:
                bitrate = int(round(os.path.getsize(filename) * 8 / 1000 / full_length))
                sample_rate = audio.info.sample_rate
                tmp_length = sec2hour(full_length)
                full_time = myMusicStr2TimeDelta(tmp_length)
                time_sec = int(full_length)
                time = full_time

        except IOError as e:
            logger.critical(' 889 Exception in GetTrackInfoVia_ext mp4: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}
        except Exception as e:
            logger.critical(' 887 Exception in GetTrackInfoVia_ext mp4: %s' % (str(e)))

        except:
            logger.critical(' 851 Exception in GetTrackInfoVia_ext mp4: %s' % (str('unknown mutagen error')))

        try:

            audio = File(filename)
            infoD['title'] = audio['\xa9nam'][0]
            infoD['artist'] = audio['\xa9ART'][0]
            infoD['album'] = audio['\xa9alb'][0]
            infoD['tracknumber'] = audio['TRCK'][0][0]
            infoD['date'] = audio['\xa9day'][0]
            infoD['genre'] = audio['\xa9gen'][0]

        except IOError as e:
            logger.critical(' 907 Exception in GetTrackInfoVia_ext MP4 meta: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}
        except Exception as e:
            logger.critical(' 905 Exception in GetTrackInfoVia_ext MP4 meta: %s' % (str(e)))
        except:
            logger.critical(' 891 Exception in GetTrackInfoVia_ext dsf meta: %s' % (str('unknown mutagen error')))

    elif ftype.lower() == 'dsf':
        try:

            audio = DSF(filename)
            full_length = audio.info.length

            if full_length != 0:
                bitrate = int(round(os.path.getsize(filename) * 8 / 1000 / full_length))
                sample_rate = audio.info.sample_rate
                tmp_length = sec2hour(full_length)
                full_time = myMusicStr2TimeDelta(tmp_length)
                time_sec = int(full_length)
                time = full_time

        except Exception as e:
            logger.critical(' 869 Exception in GetTrackInfoVia_ext dsf: %s' % (str(e)))
        except IOError as e:
            logger.critical(' 871 Exception in GetTrackInfoVia_ext dsf: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}
        except:
            logger.critical(' 874 Exception in GetTrackInfoVia_ext dsf: %s' % (str('unknown mutagen error')))

        try:

            audio = File(filename)
            infoD['title'] = audio['TIT2'].text[0]
            infoD['artist'] = audio['TPE1'].text[0]
            infoD['album'] = audio['TALB'].text[0]
            infoD['tracknumber'] = audio['TRCK'].text[0]
            infoD['date'] = audio['TDRC'].text[0].text
            infoD['genre'] = audio['TCON'].text[0]

        except IOError as e:
            logger.critical(' 888 Exception in GetTrackInfoVia_ext dsf meta: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}
        except Exception as e:
            logger.critical(' 886 Exception in GetTrackInfoVia_ext dsf meta: %s' % (str(e)))
        except:
            logger.critical(' 891 Exception in GetTrackInfoVia_ext dsf meta: %s' % (str('unknown mutagen error')))
    elif ftype.lower() == 'mp3':
        try:
            audio = MP3(filename, ID3=EasyID3)
        except IOError as e:
            logger.critical('723 Exception in GetTrackInfoVia_ext: %s' % (str(e)))
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}
        except:
            logger.critical('Strange mp3 error at 639 myMediaLib_cue:')
            print('Strange mp3 error at 1524 myMediaLib:', filename)
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                    "album": 'No Album', "bitrate": 0, 'sample_rate': 0, 'time': '00:00', 'ftype': ftype}

        try:
            bitrate = audio.info.bitrate / 1000
        except:
            print('audio=:', audio)
        full_length = audio.info.length
        sample_rate = audio.info.sample_rate

    elif ftype == 'ape' or ftype == 'apl':
        m_audio = None
        try:
            f = open(filename, 'rb')
            m_audio = MonkeysAudioInfo(f)
            f.close()
            full_length = m_audio.length
            if full_length != 0:
                bitrate = int(os.path.getsize(filename) * 8 / 1000 / full_length)
                sample_rate = m_audio.sample_rate
            time_sec = int(full_length)
        except IOError:
            print('m_audio.error', filename, ' ---> time and avrg bitrate and sample_rate will not be availble')
            pass

        try:
            audio = APEv2(filename)

        except IOError:
            return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": b"No Artist",
                    "album": b"No Album", "bitrate": bitrate, 'sample_rate': sample_rate, 'time': "00:00",
                    'time_sec': 0, 'ftype': ftype}

    if audio == None:
        print(filename[filename.rfind('/') + 1:-(len(ftype) + 1)])
        return {"title": filename[filename.rfind('/') + 1:-(len(ftype) + 1)], "artist": 'No Artist',
                "album": 'No Album', "bitrate": bitrate, 'sample_rate': sample_rate, 'time': '00:00', 'time_sec': 0,
                'ftype': ftype}

    audio_keys = ['title', 'artist', 'album', 'tracknumber', 'date', 'genre']
    if ftype == 'ape' or ftype == 'apl':
        audio_keys = ['title', 'artist', 'album', 'track', 'date', 'genre']
        try:
            time = '%6s' % sec2min(m_audio.length)
            time_sec = int(m_audio.length)
        # print 'timeOk!   ',time
        except Exception as e:
            logger.critical('Error in GetTrackInfoVia_ext ape:[%s]' % str(e))

    elif ftype == 'mp3':
        try:
            time = '%6s' % sec2min(audio.info.length)
            time_sec = int(audio.info.length)
        # print 'timeOk!   ',time
        except Exception as e:
            logger.critical('Error in GetTrackInfoVia_ext mp3:[%s]' % str(e))

            time_sec = 0
    for c in audio_keys:
        if ftype == 'dsf':
            break
        if c not in audio:
            infoD[c] = 'NA ' + c
            continue
        if c in audio:
            # print audio[c]
            if ftype != 'ape':
                infoD[c] = audio[c][0].strip()
            else:

                if audio[c].value[-1] == '\x00':
                    infoD[c] = audio[c].value[:-1]
                else:
                    infoD[c] = audio[c].value
                if c == 'track':
                    infoD['tracknumber'] = infoD[c]
        else:
            if c == 'title':
                infoD[c] = filename[filename.rfind('/') + 1:-(len(ftype) + 1)]
            elif c == 'tracknumber':
                infoD[c] = 0
            else:
                infoD[c] = 'NA ' + c

    infoD['bitrate'] = bitrate
    infoD['sample_rate'] = sample_rate

    time = str(time)
    if time[:2] == '0:':
        time = time[2:7]

    infoD['time'] = time
    infoD['time_sec'] = time_sec
    infoD['ftype'] = ftype
    infoD['full_length'] = full_length
    logger.debug('in GetTrackInfoVia_ext - [%s]' % str(infoD))
    logger.debug('in GetTrackInfoVia_ext - finished')

    return infoD


def generate_play_list_from_fileData(trackLD, album_crc32, track_crc32, audioFilesPathRoot, mpdMusicPathPrefix):
    logger.debug(
        'in generate_play_list_from_fileData album[%s] track[%s]  - start' % (str(album_crc32), str(track_crc32)))
    is_cue = False
    is_image = False
    trackL = []
    temp_trackL = []
    # конвертируем если надо в bytes для работы с os.path, где требуются только байт строки
    if not isinstance(audioFilesPathRoot, bytes):
        audioFilesPathRoot = bytes(audioFilesPathRoot, encoding='utf-8')
    if not isinstance(mpdMusicPathPrefix, bytes):
        mpdMusicPathPrefix = bytes(mpdMusicPathPrefix, encoding='utf-8')

    logger.debug('in generate_play_list_from_fileData  trackLD.keys:[%s]' % (str(trackLD.keys())))
    for a in trackLD:
        if track_crc32 != None and a != track_crc32:
            continue
        elif album_crc32 == None:
            # define album_crc32 when only track modus
            album_crc32 = trackLD[a]['album_crc32']

        if trackLD[a]['album_crc32'] == album_crc32:

            if 'cue' in trackLD[a]:
                is_cue = True
                print("CUE", trackLD[a])
            if trackLD[a]['file'] not in trackL:
                # в конце замена уже замена по unicode строке
                # returning data is tuple (track_file_name, number) for "not cue" number is 0
                print('mpdMusicPathPrefix:', mpdMusicPathPrefix)
                print('file:', trackLD[a]['file'])

                # if os.path.normpath(audioFilesPathRoot) in trackLD[a]['file']:

                #	print(mpd_file)
                #	trackL.append((os.path.join(mpdMusicPathPrefix,mpd_file).decode('utf-8'),0))

                if is_cue:
                    try:

                        if audioFilesPathRoot in trackLD[a]['cue_f_name_abs']:
                            print('before2:==========')
                            # в конце замена замена по байт строке, т.к. следующая операция с os.path
                            cue_item = os.path.relpath(trackLD[a]['cue_f_name_abs'], audioFilesPathRoot).replace(b"\\",
                                                                                                                 b"/")
                            print('before3:==========', cue_item)
                            trackL.append((os.path.join(mpdMusicPathPrefix, cue_item).decode('utf-8'),
                                           int(trackLD[a]['cueNameIndx']) - 1))
                    except Exception as e:
                        logger.critical('Error: in generate_play_list_from_fileData [%s]' % str(e))
                        logger.critical('Error: in generate_play_list_from_fileData skipped [%s]' % str(a))
                        logger.critical(
                            'Error: in generate_play_list_from_fileData skipped [%s]' % (trackLD[a]['file']))
                        logger.critical(
                            'Error: in generate_play_list_from_fileData skipped keys [%s]' % (str(trackLD[a].keys())))
                        continue
                else:
                    if audioFilesPathRoot in trackLD[a]['file']:
                        mpd_file = os.path.relpath(trackLD[a]['file'], audioFilesPathRoot).replace(b"\\", b"/")
                        print(mpd_file)
                        trackL.append((os.path.join(mpdMusicPathPrefix, mpd_file).decode('utf-8'), 0))

    if is_cue and len(trackL) > 0:
        # pos = trackL[0].rfind(',')
        # cue_file = trackL[0][:pos]
        # print cue_file
        trackL.sort(key=operator.itemgetter(1))
        logger.debug('in generate_play_list_from_fileData - cue Finished [%s]' % (str(len(trackL))))
        return trackL

    if not is_cue and len(trackL) > 0:
        trackL.sort(key=operator.itemgetter(0))
        logger.debug('in generate_play_list_from_fileData - not cue Finished')
        return trackL

    logger.critical('in generate_play_list_from_fileData - Error Finished')
    return []
