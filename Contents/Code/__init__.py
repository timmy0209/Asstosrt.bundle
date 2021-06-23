#将本地ASS字幕转换为STR字幕的plex插件
#更多PLEX中文插件请访问plexmedia.cn

import io
import os
import hashlib
import json
import urllib
import urllib2
from urllib2 import HTTPError
import httplib
import re
import sys
import chardet


def Start():
  HTTP.CacheTime = 0
  Log.Debug("Shooter Agent Start")
  
'''提取路径中的文件名、后缀等'''
def filename_find(filepath, return_type=0):
    basename = os.path.basename(filepath)
    extension = '.%s' % basename.split(".")[-1]
    extension_lang = '.%s.%s' % (basename.split(".")[-2],basename.split(".")[-1])
    #if not basename.__contains__('.'):
    #    extension = ''
    #    extension_lang = ''
    
    filename_without_extension = basename[0:len(basename)-len(extension)]
    if return_type is 0:    # 文件名
        return basename
    if return_type is 1:    # 后缀名
        return extension
    if return_type is 2:    # 无后缀文件名
        return filename_without_extension
    if return_type is 3:    # 后缀名加字幕语言名
        return extension_lang
      
'''转换ass为srt'''

def get_codetype(ass_name): #获取字幕编码格式
    f = io.open(ass_name,'rb')  # 先用二进制打开
    data = f.read()  # 读取文件内容
    file_encoding = chardet.detect(data).get('encoding')  # 得到文件的编码格式
    f.close
    Log(file_encoding)
    return file_encoding
  
def read_ass_file(ass_name,codetype):
    # function: read the ass file into python
    # input: filename
    # output: 
    f_ass = io.open(ass_name,'r',encoding=codetype)
    subtitle = f_ass.readlines()
    f_ass.close()
    return subtitle

def find_event(subtitle):
    # function: find the beginning of the [Event]
    # input: subtitle
    # output: event
    new_subtitle = []
    for i in range(len(subtitle)):
        if "[Events]" in subtitle[i]:
            Log("[Events]:from {}th line".format(i+1))
            new_subtitle = subtitle[i:]
            break
    return new_subtitle

def get_format(new_subtitle):
    # function: get the structure of the event
    #exzample: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text  
    # input: new_subtitle
    # output: text_num, i.e. the index of Text in the format
    text_num = -9999
    if "Format" in new_subtitle[1]:
        subtitle_format = new_subtitle[1].split(":")[1].split(",")
        # strip the space and "\n"
        for i in range(len(subtitle_format)):
            subtitle_format[i] = subtitle_format[i].strip()
        if "Text" in subtitle_format:
            text_num = subtitle_format.index("Text")
        Log("The subtitle structure is {}".format(subtitle_format))
    else:
        Log("the structrue of the subtitle can not be processed by this py file")
    return text_num

def get_time_and_text(new_subtitle, text_num):
    time_text = []
    for i in range(2, len(new_subtitle)-1):
        #if "".join(new_subtitle[i].split(",")[text_num:])[0] != "{":
            start = new_subtitle[i].split(",")[1]
            end = new_subtitle[i].split(",")[2]
            text = "".join(new_subtitle[i].split(",")[text_num:])
            # the information out of the {} is what we need
            p = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", text)
            #print('p:{}'.format(p))
            # whether the subtitle is bi-languange
            if "\\N" in p:
                language_a = p.split("\\N")[0]
                language_b = p.split("\\N")[1]
            else:
                language_a = p
                language_b = ""
            #if type(language_a) is str and type(language_b) is str:
            #    pass
            #else:
                #Log('第{}句字幕不是str格式'.format(i))
                #Log('a:{}'.format(language_a))
                #Log('b:{}'.format(language_b))
            time_text.append([str(i), "{} --> {}".format(start, end), language_a, language_b, "\n"])
    return time_text

def get_srt_subtitle(time_text):
    srt_subtitle = []
    Log("Preparing the srt subtitle...")
    #for i in trange(len(time_text)):
    #print(time_text)
    for item in (time_text):
        srt_subtitle.append("\n".join(item))
    #print("\n")
    #print(srt_subtitle)
    return srt_subtitle
    
def write_srt(srt_name, srt_subtitle):
    #using gbk for srt

    f_srt = io.open(srt_name,'w',encoding="gbk",errors='ignore')
    f_srt.writelines(srt_subtitle)
    f_srt.close()


def ass_to_srt(ass_fullpath):
    #ass_name = "Iron.Man.2008.2160p.BluRay.HEVC.DTS-HD.MA.5.1-BB.ass"
    (filepath, tempfilename) = os.path.split(ass_fullpath)
    (filename, extension) = os.path.splitext(tempfilename)
    srt_name = filepath + '/' + filename + ".srt"
    codetype = get_codetype(ass_fullpath)
    subtitle = read_ass_file(ass_fullpath,codetype)
    new_subtitle = find_event(subtitle)
    
    if new_subtitle == []:
        Log("Attention!!!!!!")
        Log("There is no Event in ass file, please check the file")
        
    text_num = get_format(new_subtitle)
    Log("Text is the {}th of the event".format(text_num+1))
    if text_num == -9999:
        Log("Attention!!!!")
        Log("There is no format in event!")
  
    time_text = get_time_and_text(new_subtitle, text_num)        
    srt_subtitle = get_srt_subtitle(time_text)
    Log("The content of srt is finished")
    
    write_srt(srt_name, srt_subtitle)
    Log("Done! You can find {}".format(srt_name))


class AssToSrtMovies(Agent.Movies):
  name = 'AssToSrt'
  languages = [Locale.Language.Chinese]  
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb','com.plexapp.agents.douban']

  def search(self, results, media, lang):
    Log.Debug("AssrtAgentMovies.search")
    results.Append(MetadataSearchResult(
      id    = media.primary_metadata.id,    
      score = 100
    ))
    
    
  def update(self, metadata, media, lang):
    Log.Debug("AssrtAgentMovies.update")
    for i in media.items:
      for part in i.parts:
          file = part.file
          Log(file)
          folder_path = os.path.dirname(file)
          file_list = os.listdir(folder_path) #提取目录下文件名
          Log(file_list)
          for files in file_list:  #转换srt
            Log(files)
            if filename_find(files,1) == '.ass' or filename_find(files,1) == '.ssa':
              Log(os.path.exists( folder_path + '/' + filename_find(files,2) + '.srt'))
              if os.path.exists( folder_path + '/' + filename_find(files,2) + '.srt'):
                Log( folder_path + '/' + filename_find(files,2) + '.srt' + '存在')
              else:
                Log( folder_path + '/' + filename_find(files,2) + '.srt' + '不存在')
                ass_to_srt(folder_path + '/' + files)
          break
      break

    

class AssToSrtTVShows(Agent.TV_Shows):
  name = 'AssToSrt'
  languages = [Locale.Language.Chinese]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb','com.plexapp.agents.douban']

  def search(self, results, media, lang, manual):
    Log.Debug("AssrtAgentTVShows.search")
    results.Append(MetadataSearchResult(
      id    = "null",    
      score = 100
    ))
    

  def update(self, metadata, media, lang, force):
    Log.Debug("AssrtAgentTVShows.update")
    for s in media.seasons:
      # just like in the Local Media Agent, if we have a date-based season skip for now.
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            for part in i.parts:
              file = part.file
              Log(file)
              folder_path = os.path.dirname(file)
              file_list = os.listdir(folder_path) #提取目录下文件名
              Log(file_list)
              for files in file_list:  #转换srt
                Log(files)
                if filename_find(files,1) == '.ass' or filename_find(files,1) == '.ssa':
                  Log(os.path.exists( folder_path + '/' + filename_find(files,2) + '.srt'))
                  if os.path.exists( folder_path + '/' + filename_find(files,2) + '.srt'):
                    Log( folder_path + '/' + filename_find(files,2) + '.srt' + '存在')
                  else:
                    Log( folder_path + '/' + filename_find(files,2) + '.srt' + '不存在')
                    ass_to_srt(folder_path + '/' + files)
          break


