# -*- coding: utf-8 -*-

### Imports ##########################################################################################################################################
import os                             # [path] abspath, join, dirname
import re                             # split, compile
import time                           # sleep, strftime, localtime
import inspect                        # getfile, currentframe
import time                           # Used to print start time to console
import hashlib                        # md5
import copy                           # deepcopy
from   lxml import etree              #
from   lxml import objectify          #
#from   io   import open    as open    # open

### Functions ########################################################################################################################################
def Dict(var, *arg, **kwarg):
  """ Return the value of an (imbricated) dictionnary, if all fields exist else return "" unless "default=new_value" specified as end argument
      Avoid TypeError: argument of type 'NoneType' is not iterable
      Ex: Dict(variable_dict, 'field1', 'field2', default = 0)
  """
  for key in arg:
    if isinstance(var, dict) and key and key in var:  var = var[key]
    else:  return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var

def SaveDict(value, var, *arg):
  """ Save non empty value to a (nested) Dictionary fields unless value is a list or dict for which it will extend it instead
      # ex: SaveDict(GetXml(ep, 'Rating'), TheTVDB_dict, 'seasons', season, 'episodes', episode, 'rating')
      # ex: SaveDict(Dict(TheTVDB_dict, 'title'), TheTVDB_dict, 'title_sort')
      # ex: SaveDict(genre1,                      TheTVDB_dict, genre) to add    to current list
      # ex: SaveDict([genre1, genre2],            TheTVDB_dict, genre) to extend to current list
  """
  if not value and value!=0:  return ""  # update dict only as string would revert to pre call value being immutable
  if not arg and (isinstance(var, list) or isinstance(var, dict)):
    if not (isinstance(var, list) or isinstance(var, dict)):  var = value
    elif isinstance(value, list) or isinstance(value, dict):  var.extend (value)
    else:                                                     var.append (value)
    return value
    
  for key in arg[:-1]:
    if not isinstance(var, dict):  return ""
    if not key in var:  var[key] = {}
    var = var[key]
  if not arg[-1] in var or not isinstance(var[arg[-1]], list):  var[arg[-1]] = value
  elif isinstance(value, list) or isinstance(value, dict):      var[arg[-1]].extend (value)
  else:                                                         var[arg[-1]].append (value)
  return value

### import var 2 dict into var and returns it
def UpdateDict(var, var2):  var.update(var2);  return var

def natural_sort_key(s):
  '''
    Turn a string into a chunks list like "z23a" -> ["z", 23, "a"] so it is sorted (1, 2, 3...) and not (1, 11, 12, 2, 3...). Usage:
    - In-place list sorting:  list.sort(key=natural_sort_key)
    - Return list copy:    sorted(list, key=natural_sort_key)
  '''
  return [ int(text) if text is not None and text.isdigit() else text for text in re.split( re.compile('([0-9]+)'), str(s).lower() ) ]

def file_extension(file):
  ''' return file extension, and if starting with single dot in filename, equals what's after the dot 
  '''
  return file[1:] if file.count('.') == 1 and file.startswith('.') else file.lower().split('.')[-1] if '.' in os.path.basename(file) else 'jpg'

def xml_from_url_paging_load(URL, key, count, window):
  ''' Load the URL xml page while handling total number of items and paging
  '''
  xml   = XML.ElementFromURL(URL.format(key, count, window), timeout=float(TIMEOUT))
  total = int(xml.get('totalSize', 0))
  Log.Info("# [{:>4}-{:>4} of {:>4}] {}".format(count+1, count+int(xml.get('size', 0)), total, URL.format(key, count, window)))
  return xml, count+window, total

def nfo_load(NFOs, path, field, filenoext=''):
  ''' Load local NFO file into 'NFOs' dict containing the following fields:
      - nfo preference name:
          Dict
          - path:  fullbath including filename to nfo                    Ex: NFOs['artist.nfo']['path' ]
          - xml:   local nfo xml object that will be updated in memory   Ex: NFOs['artist.nfo']['xml'  ]
          - local: copy of local nfo xml object for comparison           Ex: NFOs['artist.nfo']['local']
  '''
  nfo_file = os.path.join(path, Prefs[ field ])
  if '{}' in nfo_file:
    if filenoext=='':  Log.Info('alert - need to add filenoext to nfo_load to replace "{}" in agent setting filename: '+field)
    else:              nfo_file = nfo_file.format(os.path.basename(filenoext))
  Log.Info('nfo_load("{}", "{}", "{}") - nfo_file: "{}"'.format(str(NFOs)[:20]+'...', path, field, nfo_file))
  if Prefs[ field ]=='Ignored' and not DEBUG:  nfo_xml = None
  elif os.path.exists(nfo_file):               nfo_xml = XML.ObjectFromString(Core.storage.load(nfo_file))
  else:                                        nfo_xml = XML.Element(nfo_root_tag[field], xsd="http://www.w3.org/2001/XMLSchema", xsi="http://www.w3.org/2001/XMLSchema-instance", text=None)
  NFOs[nfo_file] = {'path': os.path.join(path, nfo_file), 'xml': nfo_xml, 'local': copy.deepcopy(nfo_xml)}
  return NFOs[nfo_file]['xml']

def xml_import(xml, xml_tags2, root, multi=False, thumb='', tag_multi='', return_value_only=False, nested=False):
  ''' single occurence
      multi single depth
      multi occurence multi depth
      return value
  '''
  xml_tags = copy.deepcopy(xml_tags2)
  for key, value in xml_tags.items() if isinstance(xml_tags, dict) else {xml_tags: {'text':thumb}}.items():  #iterate over a copy otherwise can't change dict while iterating
    nested_tags = { nested_key: value.pop(nested_key) for nested_key, nested_value in value.items() if isinstance(nested_value, dict) }  #.items used to avoid Exception: 'dictionary changed size during iteration'
    if (tag_multi or multi):
      tag = xml.xpath('.//{}[text()="{}"]'.format(tag_multi or key, thumb))  #tag = xml.find('.//'+(tag_multi or key))
      if len(tag): tag=tag[0]
    else:  tag = xml.find('.//'+key)
    
    if return_value_only:
      if not tag:                      return
      elif tag_multi or multi:         return thumb if len(xml.xpath('.//{}[text()="{}"]'.format(tag_multi or key, thumb))) else ""
      elif tag.text:                   return tag.text
    
    if not multi and not isinstance(value, dict):  value = {'text': value}  #if value is not a dict, make it one
    if tag is None or (tag_multi or multi) and xml.xpath('.//{}[text()="{}"]'.format(tag_multi or key, thumb))== []:
      Log.Info('[X] tag: "{}" created with attributes: "{}"'.format(key, value))
      tag = XML.Element(key, **value)  # cannot use 'name' attribute:  Element() got multiple values for keyword argument 'name' 
      xml.append(tag)                  # append new tag single element  #element = ET.Element(key) # program = ET.SubElement(element, nested_key)
    elif not return_value_only:
      Log.Info('[X] tag: "{}" found, updating attributes: "{}"'.format(key, value))
      if isinstance(value, dict) and 'text' in value and value['text']!=tag.text:  setattr(xml, key, value.pop('text', None)) #parent.key=y but all attributes dropped,  x.text = 'newtext' not writable, x._setText('newtext') forbidden by plex due to '_'
      #if isinstance(value, dict) and 'text' in value and tag.text:  delattr(xml, key)  #value['text']  #parent.key=y but all attributes dropped,  x.text = 'newtext' not writable, x._setText('newtext') forbidden by plex due to '_'
      #  if len(tag):  tag[-1].tail = (tag[-1].tail or "") + value['text']
      #  else:         tag.text     = (tag.text     or "") + value['text']
      for x in value:  tag.attrib[x]=value[x]; Log.Info('attribute: "{}", value: "{}"'.format(x, value[x]))  #tag.set(x, value[x]  #xml_tags.update(xml_tags_backup)
      objectify.deannotate(xml, xsi_nil=True)  #remove garbage attributes #tag.set(x, y) #tag.begin = y  #pass  # tag['text'] = y <text xmlns:py="http://codespeak.net/lxml/objectify/pytype" py:pytype="str"> #'tag.text = y' failed: attribute 'text' of 'ObjectifiedElement' objects is not writable
      etree.cleanup_namespaces(xml)
    if nested_tags!={}:  return xml_import(tag, nested_tags, root + '/' + key, multi, thumb, tag_multi, return_value_only, nested=True)  # Nested tags recursive call
      
def SaveFile(thumb, path, field, key="", ratingKey="", dynamic_name="", nfo_xml=None, xml_field='', metadata_field=None, tags={}, multi=False, tag_multi=''):
  ''' Save Metadata to file if different, or restore it to Plex if it doesn't exist anymore
      - thumb:          url to picture or text or list...
      - destination:    path to export file (jpg or nfo)
      - field:          Prefs field name to check if export/importing
      - dynamic_name:   used to replace {} in agent pref filenames
      - nfo_xml:        (nfo) xml dict to update. will be saved if different from backup at the end
      - xml_field:      (nfo) xml tag name
      - xml tags:       (nfo) xml attributes
      - metadata_field: (nfo) metadata field to update
        key:            
      Usage:
      - SaveFile(show.get('theme'), path, 'series_themes')
      - SaveFile(show.get('title'), path, 'series_nfo', nfo_xml=NFOs['series_nfo']['xml'], xml_field='title', metadata_field=metadata.title)
  '''
  Log.Info('SaveFile("{}", "{}", "{}", "{}"...) xml_field: "{}"'.format(thumb, path, field, Prefs[field], xml_field))
  if not thumb or not path or not field or Prefs[field]=='Ignored':  return  #Log.Info('return due to empy field')
  
  ext = file_extension(thumb)
  if ext not in ('jpg', 'jpeg', 'png', 'tbn', 'mp3', 'txt', 'nfo'):  ext='jpg'  #ext=='' or len(ext)>4 or
  filename = Prefs[field].split('¦')[1 if dynamic_name  and '¦' in Prefs[field] else 0] if 'season' in field and '¦' in Prefs[field] else Prefs[field]  #dynamic name for seasons 1+ not specials
  if '{}'   in filename:  filename = filename.format(dynamic_name)
  if '.ext' in filename:  filename = filename.replace('.ext', '.'+ext)
  destination = os.path.join(path, filename)
  ext         = file_extension(destination)
  
  ### plex_value
  try:
    if thumb:
      if ext in ('jpg', 'mp3'):  plex_value = HTTP.Request(PMS+thumb).content #response.headers['content-length']
      else:                      plex_value = thumb #txt, nfo
    else:                        plex_value = ''  
    if DEBUG:             Log.Info('[?]  plex_value: "{}", type: "{}"'.format('binary...' if ext in ('jpg', 'jpeg', 'png', 'tbn', 'mp3') and plex_value!='' else plex_value, type(plex_value)))
  except Exception as e:  Log.Info('plex_value - Exception: "{}"'.format(e));  return
  
  ### local_value
  try:
    local_value=''
    tag=None
    if ext in ('jpg', 'jpeg', 'png', 'tbn', 'mp3', 'txt'): local_value = Core.storage.load(destination) if os.path.exists(destination) else ''
    elif ext=='nfo': 
      if isinstance(xml_field, dict):  local_value = xml_import(nfo_xml, xml_field, nfo_root_tag[field], multi, thumb, tag_multi, return_value_only=True)
      elif multi:  #tag = nfo_xml.find( './/{}'.format(xml_field))  #tags = nfo_xml.xpath('.//{}[text()="{}"]'.format(xml_field, thumb))
        tags = nfo_xml.findall( './/'+xml_field)
        for tag in tags:
          if str(tag)==thumb:  local_value=thumb;  break  #tag[0].text==
        else:  tag = None
      else:
        tag = nfo_xml.find( './/'+xml_field)
        if tag: local_value = tag[0].text
    else:  Log.Info('[!] Unknown extension');  return
    if DEBUG:             Log.Info('[?] local_value: "{}", type: "{}"'.format('binary...' if ext in ('jpg', 'jpeg', 'png', 'tbn', 'mp3') and local_value!='' else local_value, type(local_value)))
  except Exception as e:  Log.Info('local_value - Exception: "{}", {}, {}, {}'.format(e, xml_field, thumb, tag));  return
 
  if   Prefs[field]=='Ignored':  Log.Info('[^] {}: {}'.format(''.format() if xml_field else field, destination))  # Ignored but text output given for checking behaviour without updating 
  elif local_value==plex_value:  Log.Info('[=] No update - {}: {}'.format(field, destination));   # Identical
  
  # Plex update
  elif local_value and (not plex_value or Prefs['metadata_source']=='local'):
    Log.Info('[@] Plex  update {}: {}, ratingKey: {}'.format(field, destination, ratingKey))
    if ext in ('jpg', 'jpeg', 'png', 'tbn', 'mp3'):
      if ratingKey=='':  Log.Info('[!] Source code missing key and ratingKey to allow plex metadata update from local disk information')
      else:              UploadImagesToPlex(destination, ratingKey, 'poster' if 'poster' in field else 'art' if 'fanart' in field else field)
    elif ext=='nfo':
      if metadata_field is not None:  metadata_field = local_value  #setattr(metadata_field, field, tag[0].text)
    elif ext=='txt':
      if DEBUG:  Log.Info("destination: '{}'".format(destination))
      r = HTTP.Request(PLEX_UPLOAD_TEXT.format(key, ratingKey, String.Quote(Core.storage.load(destination))), headers=HEADERS, method='PUT')
      Log.Info('request content: {}, headers: {}, load: {}'.format(r.content, r.headers, r.load))
         
  # Local update
  elif plex_value and (not local_value or Prefs['metadata_source']=='plex'):
    
    if not os.path.exists(os.path.dirname(destination)):
      os.makedirs(os.path.dirname(destination))
      Log.Info('[@] Local update - {}: {}[dir created], ratingKey: {}'.format(field, os.path.basename(destination), ratingKey))
    else:
      Log.Info('[@] Local update {}: {}, ratingKey: {}'.format(field, destination, ratingKey))
    
    if ext in ('jpg', 'mp3', 'txt'):  
      if DEBUG:               Log.Info('[{}] {}: {}'.format('!' if os.path.exists(destination) else '*', field, os.path.basename(destination)))
      try:                    Core.storage.save(destination, plex_value)
      except Exception as e:  Log.Info('Exception: "{}"'.format(e))
    elif ext=='nfo':          xml_import(nfo_xml, xml_field, nfo_root_tag[field], multi, thumb, tag_multi)
  
  else:
    Log.Info("[@] No    update {}: {}, ratingKey: {}, Prefs['metadata_source']: {}".format(field, destination, ratingKey, Prefs['metadata_source']))
    
  return destination
  
def UploadImagesToPlex(url_list, ratingKey, image_type):
  ''' URL uploader for field not in metadata like collections
  
      https://github.com/defract/TMDB-Collection-Data-Retriever/blob/master/collection_updater.py line 211
      - url_list:    url or [url, ...]
      - ratingKey:   #
      - image_type:  poster, fanart, season

      http://127.0.0.1:32400/photo/:/transcode?url=%2Flibrary%2Fmetadata%2F1326%2Ffile%3Furl%3Dupload%253A%252F%252Fposters%252Febe213fdbabb44fe6706c33bec7fa576a50da008%26X-Plex-Token%3Dxxxxxxxx&X-Plex-Token=
      url var decode1: /library/metadata/1326/file?url=upload%3A%2F%2Fposters%2Febe213fdbabb44fe6706c33bec7fa576a50da008&X-Plex-Token=TNmxEi64CzFSnbKhbQnw
      url var decode2: upload://posters/ebe213fdbabb44fe6706c33bec7fa576a50da008
      md5:             8954037BD59365EE7830FCFC3A72EE68
      sha1:            C5DC6B1D5128D3AE2D19A712074C52E992438954
      http://127.0.0.1:32400/library/metadata/1326/posters?X-Plex-Token=xxxxxxxxxxxxxxxx
      
      String.Quote()
      Hash.XXX(data): MD5, SHA1. SHA224, SHA256, SHA384, SHA512, CRC32
      hashlib.md5(data).hexdigest()      
  '''
  for url in url_list if isinstance(url_list, list) else [url_list] if url_list else []:
    r = HTTP.Request(PLEX_UPLOAD_TYPE.format(ratingKey, image_type+'s', ''), headers=HEADERS)
    Log.Info(r.content)
    r = HTTP.Request(PLEX_UPLOAD_TYPE.format(ratingKey, image_type + 's', 'default%3A%2F%2F'), headers=HEADERS, method='PUT')  # upload file  , data=Core.storage.load(url)
    Log.Info(r.content)
    for child in r.iter():
      if child.attrib['selected'] == '1':
        selected_url   = child.attrib['key'] #selected_image_url = selected_url[selected_url.index('?url=')+5:]
        #r = HTTP.Request(PLEX_IMAGES % (ratingKey, image_type + 's', url           ), headers=HEADERS, method='POST')  # upload file
        #r = HTTP.Request(PLEX_IMAGES % (ratingKey, image_type,       selected_image), headers=HEADERS, method='PUT' )  # set    file as selected again
        Log.Info('request content: {}, headers: {}, load: {}'.format(r.content, r.headers, r.load))
        break
    else: continue  #continue if no break occured
    break           #cascade first break to exit both loops

def ValidatePrefs():
  ''' Agent settings shared and accessible in Settings>Tab:Plex Media Server>Sidebar:Agents>Tab:Movies/TV Shows/Albums>Tab:Lambda
      Pre-Defined ValidatePrefs function called when settings changed and output settings choosen (loading json file to get default settings and Prefs var list)
      Last option reset agent to default values in "DefaultPrefs.json" by deleting Prefs settings file 
  '''
  Prefs['reset_to_defaults']  #avoid logs message on first accesslike: 'Loaded preferences from DefaultPrefs.json' + 'Loaded the user preferences for com.plexapp.agents.lambda'
  filename_xml  = os.path.join(PlexRoot, 'Plug-in Support', 'Preferences',   'com.plexapp.agents.Lambda.xml')
  filename_json = os.path.join(PlexRoot, 'Plug-ins',        'Lambda.bundle', 'Contents', 'DefaultPrefs.json')
  Log.Info("".ljust(157, '='))
  Log.Info ("ValidatePrefs() - PlexRoot: '{}'".format(PlexRoot))
  Log.Info ("[?] agent settings json file: '{}'".format(os.path.relpath(filename_json, PlexRoot)))
  Log.Info ("[?] agent settings xml prefs: '{}'".format(os.path.relpath(filename_xml , PlexRoot)))
  if Prefs['reset_to_defaults'] and os.path.isfile(filename_xml):  os.remove(filename_xml)  #delete filename_xml file to reset settings to default
  elif os.path.isfile(filename_json):
    try:
      json = JSON.ObjectFromString(Core.storage.load(filename_json), encoding=None)
      for entry in json or []:  Log.Info("[{active}] Prefs[{key:<{width}}] = {value:<{width2}}, default = {default}".format(active=' ' if Prefs[entry['id']] in ('Ignored', False) else 'X', key="'"+entry['id']+"'", width=max(map(len, [x['id'] for x in json]))+2, value="'"+str(Prefs[entry['id']]).replace('¦','|')+"'", width2=max(map(len, [str(Prefs[x['id']]).replace('¦','|') for x in json]))+2, default="'{}'".format(entry['default'])))
    except Exception as e:  Log.Info("Error :"+str(e)+", filename_json: "+filename_json)
  Log.Info("".ljust(157, '='))
  return MessageContainer('Success', "DefaultPrefs.json valid")

def SetRating(key, rating):
  ''' Called when changing rating in Plex interface
  '''
  pass

def Start():
  ''' Called when starting the agent
  '''
  ValidatePrefs()

def Search(results, media, lang, manual, agent_type):
  ''' Use media ID as unique ID in this agent
  '''
  Log(''.ljust(157, '='))
  Log('search() - lang:"{}", manual="{}", agent_type="{}", media.primary_metadata.id: "{}"'.format(lang, manual, agent_type, media.primary_metadata.id))
  if agent_type=='movie':   results.Append(MetadataSearchResult(id = media.primary_metadata.id, name=media.title,  score = 100))
  if agent_type=='show':    results.Append(MetadataSearchResult(id = media.primary_metadata.id, name=media.show,   score = 100))
  if agent_type=='artist':  results.Append(MetadataSearchResult(id = media.primary_metadata.id, name=media.artist, score = 100))
  if agent_type=='album':   results.Append(MetadataSearchResult(id = media.primary_metadata.id, name=media.title,  score = 100))
  Log(''.ljust(157, '='))
  #metadata = media.primary_metadata  #full metadata object from here with all data, whereas in Update() metadata will be empty...
  
def Update(metadata, media, lang, force, agent_type):
  ''' Download metadata using unique ID, but 'title' needs updating so metadata changes are saved
  '''
  Log.Info(''.ljust(157, '='))
  Log.Info('Update(metadata, media="{}", lang="{}", force={}, agent_type={})'.format(media.title, lang, force, agent_type))
  
  ### Media folder retrieval: path folder and media item filename ###
  if   agent_type=='movie':  path, item = os.path.split(media.items[0].parts[0].file)
  elif agent_type=='show':
    dirs=[]
    for s in media.seasons if media else []: # TV_Show:
      for e in media.seasons[s].episodes:
        path, item =  os.path.split(media.seasons[s].episodes[e].items[0].parts[0].file)
        break
      else: continue  #loop if no break
      break           #cascade break
  elif agent_type=='album':
    for track in media.tracks:
      path, item = os.path.split(media.tracks[track].items[0].parts[0].file)
      break
  
  ### Plex library variables: library_key, library_path, library_name ###
  library_key, library_path, library_name = '', '', ''
  series_root_folder                      = ""
  try:
    PLEX_LIBRARY_XML = XML.ElementFromURL(PMSSEC, timeout=float(TIMEOUT))
    Log.Info('Libraries: ')
    for directory in PLEX_LIBRARY_XML.iterchildren('Directory'):
      for location in directory:
        Log.Info('[{}] id: {:>2}, type: {:>6}, library: {:<24}, path: {}'.format('*' if location.get('path') in path else ' ', directory.get("key"), directory.get('type'), directory.get('title'), location.get("path")))
        if ('artist' if agent_type=='album' else agent_type)==directory.get('type') and location.get('path') in path:
          library_key, library_path, library_name = directory.get("key"), location.get("path"), directory.get('title')
  except Exception as e:  Log.Info("PMSSEC - Exception: '{}'".format(e));  
  else:
    
    ### Extract season and transparent folder to reduce complexity and use folder as serie name ###
    rel_path            = os.path.relpath(path, library_path).lstrip('.')
    series_root_folder  = os.path.join   (library_path, rel_path.split(os.sep, 1)[0]).rstrip('\\')
    rel_reverse_path    = list(reversed(rel_path.split(os.sep))) if rel_path!='' else []
    #subfolder_count     = len([file for file in os.listdir(series_root_folder) if os.path.isdir(os.path.join(series_root_folder, file))] or [])
    SEASON_RX           = [ 'Specials',                                                                                                                                           # Specials (season 0)
                            '(Season|Series|Book|Saison|Livre|Temporada|S)[ _\-]*(?P<season>[0-9]{1,2}).*',  # Season ##, Series #Book ## Saison ##, Livre ##, S##, S ##
                            '(?P<show>.*?)[\._\- ]+[sS](?P<season>[0-9]{2})',                      # (title) S01
                            '(?P<season>[0-9]{1,2})a? Stagione.*',                                 # ##a Stagione
                            #'(?P<season>[0-9]{1,2}).*',	                                           # ##
                            '^.*([Ss]aga]|([Ss]tory )?[Aa][Rr][KkCc]).*$'                          # Last entry in array, folder name droped but files kept: Story, Arc, Ark, Video
                          ]                                                                                                                                                       #
    for folder in rel_reverse_path if agent_type=='show' else []:
      for rx in SEASON_RX:
        if re.match(rx, folder, re.IGNORECASE):
          Log.Info('rx: {}'.format(rx))
          if rx!=SEASON_RX[-1]:  rel_reverse_path.remove(folder) # get season number but Skip last entry in seasons (skipped folders) #  iterating slice [:] or [:-1] doesn't hinder iteration. All ways to remove: reverse_path.pop(-1), reverse_path.remove(thing|array[0])
          break
    path = os.path.join(library_path, rel_path.split(rel_reverse_path[0])[0], rel_reverse_path[0]) if rel_reverse_path else library_path
    Log.Info('series_root_folder: "{}", rel_path: "{}", rel_reverse_path: "{}"'.format(series_root_folder, rel_path, rel_reverse_path))
    Log.Info('library_key: {}, library_path: {}, library_name: {}'.format(library_key, library_path, library_name))
    Log.Info("series folder detected: {}".format(path))
    Log.Info('')
    
  ### Variables initialization ###
  roles           = []
  genres          = []
  collections     = []
  NFOs            = {}
  ratingKey       = ""
  source          = ''
  guid            = ''
  if '-' in metadata.id:  source, id = metadata.id.split('-', 1)
  else:                   source, id = '', metadata.id 
    
  ### Movies (PLEX_URL_MOVIES) ################################################################################################################################
  if agent_type=='movie':
    
    count, total = 0, 0
    while count==0 or count<total:  #int(PLEX_TVSHOWS_XML.get('size')) == WINDOW_SIZE[agent_type] and
      try:
        PLEX_XML_MOVIES, count, total = xml_from_url_paging_load(PLEX_URL_MOVIES, library_key, count, WINDOW_SIZE[agent_type])
        for video in PLEX_XML_MOVIES.iterchildren('Video'):
          ratingKey = video.get('ratingKey')
          if media.id == ratingKey:
            Log.Info(XML.StringFromElement(video))
            Log.Info('title:                 {}'.format(video.get('title')))
            
            #NFO
            filenoext   = '.'.join(media.items[0].parts[0].file.split('.')[:-1])
            nfo_xml     = nfo_load(NFOs, path, 'movies_nfo', filenoext=filenoext)
            duration    = str(int(video.get('duration'))/ (1000 * 60)) if video.get('duration') is not None and video.get('duration').isdigit() else "0" # in minutes in nfo in ms in Plex
            rated       = ('Rated '+video.get('contentRating')) if video.get('contentRating') else ''
            date_added  = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(video.get('addedAt')))) if video.get('addedAt') else None
            SaveFile(id                                , path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field={'uniqueid': {'type': source or 'unknown', 'default': 'true', 'text': id}})
            SaveFile(video.get('title'                ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='title',          metadata_field=metadata.title                           )
            SaveFile(video.get('originalTitle'        ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='originaltitle',  metadata_field=metadata.original_title                  )
            SaveFile(video.get('titleSort'            ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='sorttitle'                                                               )
            SaveFile(video.get('tagline'              ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='tagline',        metadata_field=metadata.tagline                         )
            SaveFile(video.get('rating'               ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='rating',         metadata_field=metadata.rating                          )
            SaveFile(video.get('studio'               ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='studio',         metadata_field=metadata.studio                          )
            SaveFile(video.get('summary'              ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='plot',           metadata_field=metadata.summary                         )
            SaveFile(video.get('year'                 ), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='year',           metadata_field=metadata.year                            )
            SaveFile(video.get('originallyAvailableAt'), path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='aired',          metadata_field=metadata.originally_available_at         )
            SaveFile(duration                          , path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='runtime',        metadata_field=metadata.duration                        )
            SaveFile(rated                             , path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='mpaa',           metadata_field=metadata.content_rating                  )
            SaveFile(date_added                        , path, 'movies_nfo', nfo_xml=nfo_xml, dynamic_name=filenoext, xml_field='dateadded'                                                               )
            
            #Pictures
            destination = SaveFile(video.get('thumb'), path, 'movies_poster', dynamic_name=filenoext);  SaveFile(destination, path, 'movies_nfo', nfo_xml=nfo_xml, xml_field={'art': {'poster': {'text': destination }}})
            destination = SaveFile(video.get('art'  ), path, 'movies_fanart', dynamic_name=filenoext);  SaveFile(destination, path, 'movies_nfo', nfo_xml=nfo_xml, xml_field={'art': {'fanart': {'text': destination }}})
            
            xml = XML.ElementFromURL(PMSMETA.format(ratingKey), timeout=float(TIMEOUT))
            if xml is not None:
              Log.Info(XML.StringFromElement(xml  ))
              roles, genres = [], []
              for tag in xml.iterdescendants('Genre'     ):  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field='genre',      metadata_field=metadata.genres,      multi=True, tag_multi='genre');  genres.append(tag.get('tag'))
              for tag in xml.iterdescendants('Collection'):  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field='collection', metadata_field=metadata.collections, multi=True                   );  collections.append(tag.get('tag'))
              for tag in xml.iterdescendants('Role'      ):
                for tag in xml.iterdescendants('Role' ):
                  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field={'actor': {'role': {'text': tag.get('role')}, 'name': {'text': tag.get('tag')}, 'thumb': {'text': tag.get('thumb', '')}}}, multi='actor', tag_multi='role'); roles.append(tag.get('tag'))
                  roles.append(tag.get('tag'))
              Log.Info("Genres:      {}".format(genres     ))
              Log.Info("Collections: {}".format(collections))
              Log.Info("Roles:       {}".format(roles      ))
              
            #Multi tags [if missing after 2, move in code above loading from 'xml' instead of 'video']
            for tag in video.iterchildren('Director'  ):  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field='director', metadata_field=metadata.directors, dynamic_name=filenoext, multi=True)
            for tag in video.iterchildren('Writer'    ):  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field='credits',  metadata_field=metadata.writers,   dynamic_name=filenoext, multi=True)
            for tag in video.iterchildren('Country'   ):  SaveFile(tag.get('tag'), path, 'movies_nfo', nfo_xml=nfo_xml, xml_field='country',  metadata_field=metadata.countries, dynamic_name=filenoext, multi=True)
            
            break
        else:  continue
        break      
      except Exception as e:  Log.Info('PLEX_URL_MOVIES - Exception: "{}", e.message: {}, e.args: {}'.format(e, e.message, e.args)); count+=1
    Log.Info('')
  
  ##### TV Shows (PLEX_URL_TVSHOWS) ###########################################################################################################################
  if agent_type=='show':

    ### PLEX_URL_TVSHOWS
    count, total = 0, 0
    while count==0 or count<total:  #int(PLEX_TVSHOWS_XML.get('size')) == WINDOW_SIZE[agent_type] and
      try:
        PLEX_TVSHOWS_XML, count, total = xml_from_url_paging_load(PLEX_URL_TVSHOWS, library_key, count, WINDOW_SIZE[agent_type])
        for show in PLEX_TVSHOWS_XML.iterchildren('Directory'):
          if media.title==show.get('title'):   
            Log.Info(XML.StringFromElement(show))

            #NFOs
            nfo_xml   = nfo_load(NFOs, path,  'series_nfo')
            ratingKey  = show.get('ratingKey')                                  #Used in season and ep sections below
            roles      = [tag.get('tag') for tag in show.iterchildren('Role')]  #Used in Advance information: viewedLeafCount, Location, Roles
            duration   = str(int(show.get('duration'))/ (1000 * 60)) if show.get('duration') and show.get('duration').isdigit() else "0" # in minutes in nfo in ms in Plex
            rated      = ('Rated '+show.get('contentRating')) if show.get('contentRating') else ''
            date_added = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(show.get('addedAt')))) if show.get('addedAt') else None
            SaveFile(id                               , path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'uniqueid': {'type': source or 'unknown', 'default': 'true', 'text': id}}, metadata_field=None)
            SaveFile(show.get('title'                ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='title'        , metadata_field=metadata.title                  )
            SaveFile(show.get('originalTitle'        ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='originaltitle', metadata_field=metadata.title                  )
            SaveFile(show.get('summary'              ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='plot'         , metadata_field=metadata.original_title         )
            SaveFile(show.get('studio'               ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='studio'       , metadata_field=metadata.studio                 )
            SaveFile(show.get('year'                 ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='year'         , metadata_field=metadata.rating                 )
            SaveFile(show.get('originallyAvailableAt'), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='aired'        , metadata_field=metadata.originally_available_at)
            SaveFile(show.get('tagline'              ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='tagline'      , metadata_field=None                            )
            SaveFile(show.get('rating'               ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'ratings': {'rating': {'Name': "", 'max': "10", 'default': "", 'value': {'text': show.get('rating')}}}}, metadata_field=metadata.rating)
            SaveFile(rated                            , path, 'series_nfo', nfo_xml=nfo_xml, xml_field='mpaa'         , metadata_field=metadata.summary                )
            SaveFile(duration                         , path, 'series_nfo', nfo_xml=nfo_xml, xml_field='runtime'      , metadata_field=metadata.duration               )
            SaveFile(date_added                       , path, 'series_nfo', nfo_xml=nfo_xml, xml_field='dateadded'    , metadata_field=None                            )
            
            #Pictures, theme song
            SaveFile(show.get('theme'                ), path, 'series_themes')
            if ratingKey in (show.get('thumb' ) or []):  destination = SaveFile(show.get('thumb' ), path, 'series_poster');  SaveFile(destination, path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'art': {'poster': {'text': destination}}})
            if ratingKey in (show.get('art'   ) or []):  destination = SaveFile(show.get('art'   ), path, 'series_fanart');  SaveFile(destination, path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'art': {'fanart': {'text': destination}}})
            if ratingKey in (show.get('banner') or []):  destination = SaveFile(show.get('banner'), path, 'series_banner');  SaveFile(destination, path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'art': {'banner': {'text': destination}}})
                       
            #Advance information: viewedLeafCount, Location, Roles
            xml = XML.ElementFromURL(PMSMETA.format(ratingKey), timeout=float(TIMEOUT))
            if xml is not None:
              Log.Info(XML.StringFromElement(xml))

              #Multi tags
              for tag in xml.iterdescendants('Genre'     ):  SaveFile(tag.get('tag'), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='genre',      metadata_field=metadata.genres,      multi=True, tag_multi='genre');       genres.append(tag.get('tag'))
              for tag in xml.iterdescendants('Collection'):  SaveFile(tag.get('tag'), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='collection', metadata_field=metadata.collections, multi=True                   );  collections.append(tag.get('tag')) 
              for directory in xml.xpath('//MediaContainer/Directory'):
                SaveFile(path,                             path, 'series_nfo', nfo_xml=nfo_xml, xml_field='path'     )
                SaveFile(path,                             path, 'series_nfo', nfo_xml=nfo_xml, xml_field='basepath' )
                SaveFile(directory.get('viewedLeafCount'), path, 'series_nfo', nfo_xml=nfo_xml, xml_field='playcount')
                for tag in directory.iterchildren('Role'):  SaveFile(tag.get('tag'), path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'actor': {'role': {'text': tag.get('role', '')}, 'name': {'text': tag.get('tag', '')}, 'thumb': {'text': tag.get('thumb', '')}}}, multi='actor', tag_multi='role'); roles.append(tag.get('tag'))
              Log.Info("Roles:       {}".format(roles      ))
              Log.Info("Genres:      {}".format(genres     ))
              Log.Info("Collections: {}".format(collections))
            break
        else:  continue
        break      
      except Exception as e:  Log.Info("PLEX_URL_TVSHOWS - Exception: '{}'".format(e));  count=total+1
    Log.Info('')
  
    ### PLEX_URL_SEASONS  - TV Shows seasons ###
    count, total = 0, 0
    while count==0 or count<total and int(PLEX_XML_SEASONS.get('size')) == WINDOW_SIZE[agent_type]:
      try:
        PLEX_XML_SEASONS, count, total = xml_from_url_paging_load(PLEX_URL_SEASONS, library_key, count, WINDOW_SIZE[agent_type])
        for show in PLEX_XML_SEASONS.iterchildren('Directory') or []:
          if ratingKey == show.get('parentRatingKey'):
            if show.get('title'):  Log.Info('[ ] title:               {}'.format(show.get('title')))
            season = show.get('title')[6:].strip() if show.get('title') and show.get('title').startswith('Season') else '0'
            for episode in media.seasons[season].episodes:
              season_folder = os.path.split(media.seasons[season].episodes[episode].items[0].parts[0].file)[0]
              
              #Season NFO
              if not ratingKey in show.get('thumb'):  
                destination = SaveFile(show.get('thumb'), season_folder, 'season_poster', dynamic_name='' if show.get('title')=='Specials' else season.zfill(2) if show.get('title') else '') #SeasonXX
                SaveFile(destination, path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'art':{'season': {'num': season, 'poster': {'text': destination}}}}, metadata_field=None)
              if not ratingKey in show.get('art'  ):
                destination = SaveFile(show.get('art'   ), season_folder, 'season_fanart', dynamic_name='' if show.get('title')=='Specials' else season.zfill(2) if show.get('title') else '') #SeasonXX)
                SaveFile(destination, path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'art':{'season': {'num': season, 'fanart': {'text': destination}}}}, metadata_field=None)
              break
            
            #Debug output
            if DEBUG:  Log.Info(XML.StringFromElement(show))
      except Exception as e:  Log.Info("PLEX_URL_SEASONS - Exception: '{}'".format(e));  #raise
      
    ### Episode thumbs list
    if Prefs['episode_thumbs']!='Ignore':
      
      count, total = 0, 0
      while count==0 or count<total:
        try:
          PLEX_XML_EPISODE, count, total = xml_from_url_paging_load(PLEX_URL_EPISODE, library_key, count, WINDOW_SIZE[agent_type])
          for video in PLEX_XML_EPISODE.iterchildren('Video'):
            if ratingKey == video.get('grandparentRatingKey'):
              season,  episode  = video.get('parentIndex'), video.get('index')
              Log.Info('[ ] serie ratingKey: {}, season: {}, episode: {}'.format(video.get('grandparentRatingKey'), season,  episode))
              
              #Media Folder and file names
              for part in video.iterdescendants('Part'):
                dirname, filename = os.path.split(part.get('file'))
                filenoext         = '.'.join(filename.split('.')[:-1])
                Log.Info('[ ] filenoext: "{}"'.format(filenoext))
                break
              
              #Episode NFO
              nfo_xml           = nfo_load(NFOs, dirname, 'episode_nfo', filenoext)
              SaveFile(video.get('thumb'                ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='thumb',           metadata_field=metadata.seasons[season].episodes[episode].thumbs,                   dynamic_name=filenoext)
              SaveFile(video.get('title'                ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='title',           metadata_field=metadata.seasons[season].episodes[episode].title,                    dynamic_name=filenoext)
              SaveFile(video.get('summary'              ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='plot',            metadata_field=metadata.seasons[season].episodes[episode].summary,                  dynamic_name=filenoext)
              SaveFile(video.get('originallyAvailableAt'), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='aired',           metadata_field=metadata.seasons[season].episodes[episode].originally_available_at,  dynamic_name=filenoext)
              SaveFile(video.get('grandparentTitle'     ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='showtitle',     )
              SaveFile(video.get('year'                 ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='year',          )
              SaveFile(video.get('addedAt'              ), dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='dateadded',     )
              SaveFile(season                            , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='season',        )
              SaveFile(episode                           , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='episode',       )
              SaveFile(filename                          , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='file',          )
              SaveFile(dirname                           , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='path',          )
              SaveFile(part.get('file')                  , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='filenameandpath')
              SaveFile(path                              , dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='basepath',      )
              SaveFile(video.get('rating'               ), path, 'series_nfo', nfo_xml=nfo_xml, xml_field={'test': {'rating': {'Name': "", 'max': "10", 'default': "", 'value':{'text': video.get('rating')}}}}, metadata_field=metadata.seasons[season].episodes[episode].rating)  #if 'name': 'Element() got multiple values for keyword argument 'name''
              for tag in video.iterdescendants('Director'):  SaveFile(tag.get('tag'),  dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='director', metadata_field=metadata.seasons[season].episodes[episode].directors,  dynamic_name=filenoext);  break
              for tag in video.iterdescendants('Writer'  ):  SaveFile(tag.get('tag'),  dirname, 'episode_nfo', nfo_xml=nfo_xml, xml_field='credits',  metadata_field=metadata.seasons[season].episodes[episode].writers,    dynamic_name=filenoext)
              
              #Episode thumb
              SaveFile(video.get('thumb'                ), dirname,                           'episode_thumbs', dynamic_name=filenoext)
              
              #Debug + end of episode output
              if DEBUG:  Log.Info(XML.StringFromElement(video))
              Log.Info(''.ljust(157, '-'))
                  
        except Exception as e:  Log.Info("PLEX_URL_EPISODE - Exception: '{}', count: {}, total: {}".format(e, count, total));  
    Log.Info('')
  
  ### Music ###################################################################################################################################################
  if agent_type=='album':

    #Load nfo file if present
    nfo_load(NFOs, path, 'album_nfo')
    nfo_load(NFOs, path, 'artist_nfo')
    
    ### PLEX_URL_ARTISTS ###
    '''count = 0
    while count==0 or count<total:  #int(PLEX_TVSHOWS_XML.get('size')) == WINDOW_SIZE[agent_type] and
      try:
        #Log.Info(library_key)
        PLEX_ARTIST_XML, count, total = xml_from_url_paging_load(PLEX_URL_ARTISTS, library_key, count, WINDOW_SIZE[agent_type])
        Log.Debug("PLEX_URL_ARTISTS [{}-{} of {}]".format(count+1, count+int(PLEX_ARTIST_XML.get('size')) ,total))
        for directory in PLEX_ARTIST_XML.iterchildren('Directory'):
          if media.parentTitle==directory.get('title'):
            Log.Info(XML.StringFromElement(directory))  #Un-comment for XML code displayed in logs
            #Log.Info("media.title: {}, media.parentTitle: {}, media.id: {}, directory.get('title'): {}".format(media.title, media.parentTitle, media.id, directory.get('title')))
            SaveFile(directory.get('title'           ), path, 'artist_nfo', nfo_xml=nfo_xml, xml_field='name',      metadata_field=metadata.title  )
            SaveFile(directory.get('summary'         ), path, 'artist_nfo', nfo_xml=nfo_xml, xml_field='biography', metadata_field=metadata.summary)
            for genre in directory.iterdescendants('Genre'):
              Log.Info(  '[ ] genre: {}'.format(genre.get('tag')))
              SaveFile(genre.get('tag'               ), path, 'artist_nfo', nfo_xml=nfo_xml, xml_field='style',      metadata_field=metadata.genres)
              
      except Exception as e:  Log.Info("Exception: '{}'".format(e))    
    '''
    
    ### ALBUM ###
    '''count = 0
    while count==0 or count<total:  #int(PLEX_TVSHOWS_XML.get('size')) == WINDOW_SIZE[agent_type] and
      try:
        PLEX_ALBUM_XML = xml_from_url_paging_load(PLEX_URL_ALBUM, library_key, count, WINDOW_SIZE[agent_type])
        Log.Info("media.title: {}, media.parentTitle: {}, media.id: {}".format(media.title, media.parentTitle, media.id))
        for directory in PLEX_ALBUM_XML.iterchildren('Directory'):
          Log.Info("directory.get('title'): {}, directory.get('parentTitle'): {}".format(directory.get('title'), directory.get('parentTitle')))
          if media.title==directory.get('title'):   
            if directory.get('summary'              ):  Log.Info('summary:               {}'.format(directory.get('summary')))
            if directory.get('parentTitle'          ):  Log.Info('parentTitle:           {}'.format(directory.get('parentTitle')))
            if directory.get('title'                ):  Log.Info('title:                 {}'.format(directory.get('title')))
            if Prefs['album_poster' ] and directory.get('thumb'):
              Log.Info('thumb:                 {}'.format(directory.get('thumb')))
              SaveFile(PMS+directory.get('thumb' ), os.path.join(path, 'cover.jpg'     ), 'poster')
            if Prefs['artist_poster'] and directory.get('parentThumb') not in ('', directory.get('thumb')):  
              Log.Info('parentThumb:                 {}'.format(directory.get('parentThumb')))
              SaveFile(PMS+directory.get('thumb' ), os.path.join(path, 'artist-poster.jpg'), 'poster')
            for collection in directory.iterchildren('Collection'):  Log.Info('collection:            {}'.format(collection.get('tag')));  collections.append(collection.get('tag'))
            found = True
            break
        else:  continue
        break      
      except Exception as e:  Log.Info("Exception: '{}'".format(e))
    '''
    
    ### PLEX_URL_TRACK ###
    count = 0
    Log.Info("media.title: {}, media.parentTitle: {}, media.id: {}".format(media.title, media.parentTitle, media.id))
    while count==0 or count<total:  #int(PLEX_TVSHOWS_XML.get('size')) == WINDOW_SIZE[agent_type] and
      try:
        
        # Paging load of PLEX_URL_TRACK
        PLEX_XML_TRACK, count, total = xml_from_url_paging_load(PLEX_URL_TRACK, library_key, count, WINDOW_SIZE[agent_type])
        Log.Debug("PLEX_URL_TRACK [{}-{} of {}]".format(count+1, count+int(PLEX_XML_TRACK.get('size')) ,total))
        #if DEBUG: Log.Info(XML.StringFromElement(PLEX_XML_TRACK))  #Un-comment for XML code displayed in logs
        
        for track in PLEX_XML_TRACK.iterchildren('Track'):
          if DEBUG:  Log.Info(XML.StringFromElement(track))
          for part in track.iterdescendants('Part'):
            if os.path.basename(part.get('file'))==item:
              Log.Info("[*] {}".format(item))              
              if os.path.exists(os.path.join(library_path, item)):
                Log.Info('[!] Skipping since on root folder')
                break
              
              # Artist poster, fanart
              if track.get('grandparentThumb') not in ('', track.get('parentThumb')):  SaveFile(track.get('grandparentThumb'), path, 'artist_poster')
              else:                                                                    Log.Info('[!] artist_poster not present or same as album')
              if track.get('grandparentArt'  ) not in ('', track.get('art')):          SaveFile(track.get('grandparentThumb'), path, 'artist_fanart')
              else:                                                                    Log.Info('[!] artist_fanart not present or same as album')
              SaveFile(track.get('parentThumb'), path, 'album_poster')
              SaveFile(track.get('art'        ), path, 'album_fanart')
              # SaveFile(track.get('thumb'), os.path.join(path, 'track.jpg'), 'album_track_poster')
              # Log.Info(XML.StringFromElement(track))
              # Log.Info(XML.StringFromElement(part))
              
              #Can extract posters and LRC from MP3 and m4a files
              break
          else:  continue
          count=total
          break
      except Exception as e:  Log.Info("Exception: '{}'".format(e))
    
  ### Collection loop for collection poster, fanart, summary ##################################################################################################
  Log.Info('-'*157)
  Log.Info('Collections {} - PLEX_URL_COLLECT paging load'.format(collections))
  count, total, collection_list = 0, 0, []
  while collections and (count==0 or count<total):
    try:
      PLEX_COLLECT_XML, count, total = xml_from_url_paging_load(PLEX_URL_COLLECT, library_key, count, WINDOW_SIZE[agent_type])
      Log.Info("count: {}, total: {}".format(count, total))
      if DEBUG:  Log.Info(XML.StringFromElement(PLEX_COLLECT_XML))
      
      for directory in PLEX_COLLECT_XML.iterchildren('Directory'):
        title = directory.get('title')
        if title in collections or title.replace(' Collection', '') in collections:
          collections.remove(title)
          dirname    = os.path.join(library_path if Prefs['collection_folder']=='root' else AgentDataFolder, '_Collections', title)
          rated      = ('Rated '+directory.get('contentRating')) if directory.get('contentRating') else ''
          dest_thumb = SaveFile(directory.get('thumb'     ), dirname, 'collection_poster', library_key, directory.get('ratingKey'), dynamic_name=lang)
          dest_art   = SaveFile(directory.get('art'       ), dirname, 'collection_fanart', library_key, directory.get('ratingKey'), dynamic_name=lang)
          
          Log.Info('-'*157)
          Log.Info('[ ] Collection: "{}", path: "{}"'.format(title, dirname))
          
          #Collection NFO
          nfo_xml = nfo_load(NFOs, dirname, 'collection_nfo')
          SaveFile(title                      , dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='title',      metadata_field=None)
          SaveFile(directory.get('addedAt'   ), dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='dateadded',  metadata_field=None)
          SaveFile(directory.get('childCount'), dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='childcount', metadata_field=None)
          SaveFile(directory.get('minYear'   ), dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='minyear',    metadata_field=None)
          SaveFile(directory.get('maxYear'   ), dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='maxyear',    metadata_field=None)
          SaveFile(directory.get('summary'   ), dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field={'plot': {lang:{'text':directory.get('summary')}}} )
          SaveFile(media.title                , dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field={'items': {'item': {'id':metadata.id, 'text':media.title}}}, multi='item', tag_multi='item')
          SaveFile(rated                      , dirname, 'collection_nfo',    nfo_xml=nfo_xml, xml_field='mpaa')
          SaveFile(dest_thumb, dirname, 'collection_nfo', nfo_xml=nfo_xml, xml_field={'art': {'poster': {'text': dest_thumb}}} )
          SaveFile(dest_art  , dirname, 'collection_nfo', nfo_xml=nfo_xml, xml_field={'art': {'fanart': {'text': dest_art  }}} )
          
          if DEBUG:  Log.Info(XML.StringFromElement(directory))
        else:  collection_list.append(title)
    except Exception as e:  Log.Info("Exception: '{}'".format(e))
  Log.Info('-'*157)
  for collection in collections:  #Collection warning if unlinked/was renammed
    Log.Info('[!] collection "{}" renamed in of the following: "{}". Please remove old collection tag and add new one'.format(collection, collection_list))
    Log.Info('-'*157)
  
  ### Save NFOs if different from local copy or file didn't exist #############################################################################################
  Log.Info('NFO files')
  for nfo in sorted(NFOs, key=natural_sort_key):
    nfo_string_xml     = XML.StringFromElement(NFOs[nfo]['xml'  ], encoding='utf-8')
    if nfo_string_xml == XML.StringFromElement(NFOs[nfo]['local'], encoding='utf-8'):  Log.Info('[=] {:<12} path: "{}"'.format(nfo, NFOs[nfo]['path']))
    elif NFOs[nfo]['path'].endswith('Ignored'):                                        Log.Info('[ ] {:<12} path: "{}"'.format(nfo, NFOs[nfo]['path']))
    else:                    Core.storage.save(NFOs[nfo]['path' ], nfo_string_xml);    Log.Info('[X] {:<12} path: "{}"'.format(nfo, NFOs[nfo]['path']))  #NFOs[nfo]['xml'].write(NFOs[nfo]['path' ])
    
### Agent declaration ################################################################################################################################
class LambdaTV(Agent.TV_Shows):
  name, primary_provider, fallback_agent, languages = 'Lambda', False, False, [Locale.Language.English, 'fr', 'zh', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'cs', 'ko', 'sl', 'hr']
  persist_stored_files = False
  contributes_to       = ['com.plexapp.agents.hama', 'com.plexapp.agents.thetvdb', 'com.plexapp.agents.themoviedb', 'com.plexapp.agents.none']
  def search (self, results,  media, lang, manual):  Search(results,  media, lang, manual, 'show')
  def update (self, metadata, media, lang, force ):  Update(metadata, media, lang, force,  'show')

class LambdaMovie(Agent.Movies):
  name, primary_provider, fallback_agent, languages = 'Lambda', False, False, [Locale.Language.English, 'fr', 'zh', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'cs', 'ko', 'sl', 'hr']
  persist_stored_files = False
  contributes_to       = ['com.plexapp.agents.hama', 'tv.plex.agents.movie', 'com.plexapp.agents.imdb', 'com.plexapp.agents.none', 'com.plexapp.agents.themoviedb', 'com.plexapp.agents.phoenixadult']
  def search (self, results,  media, lang, manual):  Search(results,  media, lang, manual, 'movie')
  def update (self, metadata, media, lang, force ):  Update(metadata, media, lang, force,  'movie')

class LambdaAlbum(Agent.Album):
  name, primary_provider, fallback_agent, languages = 'Lambda', False, False, [Locale.Language.English, 'fr', 'zh', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'cs', 'ko', 'sl', 'hr']
  persist_stored_files = False
  contributes_to       = ['com.plexapp.agents.discogs', 'com.plexapp.agents.lastfm', 'com.plexapp.agents.plexmusic', 'com.plexapp.agents.none']
  def search(self, results,  media, lang, manual):  Search(results,  media, lang, manual, 'album')
  def update(self, metadata, media, lang, force ):  Update(metadata, media, lang, force,  'album')

### Variables ########################################################################################################################################
DEBUG                           = True
PlexRoot                        = Core.app_support_path
AgentDataFolder                 = os.path.join(PlexRoot, "Plug-in Support", "Data", "com.plexapp.agents.lambda", "DataItems")
PMS                             = 'http://127.0.0.1:32400'  # Since PMS is hardcoded to listen on 127.0.0.1:32400, that's all we need
PMSLIB                          = PMS + '/library'
PMSSEC                          = PMSLIB + '/sections'
PMSMETA                         = PMSLIB + '/metadata/{}'
PAGING                          = '&X-Plex-Container-Start={}&X-Plex-Container-Size={}'
PLEX_URL_MOVIES                 = PMSSEC + '/{}/all?type=1'  + PAGING #How to load XML info: https://support.plex.tv/articles/201638786-plex-media-server-url-commands/
PLEX_URL_TVSHOWS                = PMSSEC + '/{}/all?type=2'  + PAGING
PLEX_URL_SEASONS                = PMSSEC + '/{}/all?type=3'  + PAGING
PLEX_URL_EPISODE                = PMSSEC + '/{}/all?type=4'  + PAGING
PLEX_URL_ARTISTS                = PMSSEC + '/{}/all?type=8'  + PAGING
PLEX_URL_ALBUM                  = PMSSEC + '/{}/all?type=9'  + PAGING
PLEX_URL_TRACK                  = PMSSEC + '/{}/all?type=10' + PAGING
PLEX_URL_COLLECT                = PMSSEC + '/{}/all?type=18' + PAGING
PLEX_URL_COITEMS                = PMSSEC + '/{}/children'    + PAGING
PLEX_UPLOAD_TEXT                = PMSSEC + '/{}/all?type=18&id={}&summary.value={}'
PLEX_UPLOAD_TYPE                = PMSLIB + '/metadata/{}/{}?url={}'
WINDOW_SIZE                     = {'movie': 30, 'show': 20, 'artist': 10, 'album': 10}
TIMEOUT                         = 30
HTTP.CacheTime                  = 0
HEADERS                         = {}
nfo_root_tag                    = {'movies_nfo': 'movie', 'series_nfo': 'tvshow', 'album_nfo': 'album', 'artist_nfo':'artist_nfo', 'episode_nfo':'episodedetails', 'collection_nfo':'collection'} #top level parent tag
HTTP.Headers['User-Agent'     ] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
HTTP.Headers['Accept-Language'] = 'en-us'
