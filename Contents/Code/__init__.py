# -*- coding: utf-8 -*-

### Imports ###
import sys                  # getdefaultencoding, getfilesystemencoding, platform, argv
import fnmatch              # filter
import os                   # path.abspath, join, dirname
import re                   #
import inspect              # getfile, currentframe
import urllib2              #
from   lxml    import etree #
from   io      import open  # open

###Mini Functions ###
def natural_sort_key     (s):  return [int(text) if text.isdigit() else text for text in re.split(re.compile('([0-9]+)'), str(s).lower())]  ### Avoid 1, 10, 2, 20... #Usage: list.sort(key=natural_sort_key), sorted(list, key=natural_sort_key)
def sanitize_path        (p):  return p if isinstance(p, unicode) else p.decode(sys.getfilesystemencoding()) ### Make sure the path is unicode, if it is not, decode using OS filesystem's encoding ###
def js_int               (i):  return int(''.join([x for x in list(i or '0') if x.isdigit()]))  # js-like parseInt - https://gist.github.com/douglasmiranda/2174255
  
### Return dict value if all fields exists "" otherwise (to allow .isdigit()), avoid key errors
def Dict(var, *arg, **kwarg):  #Avoid TypeError: argument of type 'NoneType' is not iterable
  """ Return the value of an (imbricated) dictionnary, return "" if doesn't exist unless "default=new_value" specified as end argument
      Ex: Dict(variable_dict, 'field1', 'field2', default = 0)
  """
  for key in arg:
    if isinstance(var, dict) and key and key in var or isinstance(var, list) and isinstance(key, int) and 0<=key<len(var):  var = var[key]
    else:  return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var

### Convert ISO8601 Duration format into seconds ###
def ISO8601DurationToSeconds(duration):
  try:     match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
  except:  return 0
  else:    return 3600 * js_int(match[0]) + 60 * js_int(match[1]) + js_int(match[2])

### Get media directory ###
def GetMediaDir (media, movie, file=False):
  if movie:  return os.path.dirname(media.items[0].parts[0].file)
  else:
    for s in media.seasons if media else []: # TV_Show:
      for e in media.seasons[s].episodes:
        Log.Info(media.seasons[s].episodes[e].items[0].parts[0].file)
        return media.seasons[s].episodes[e].items[0].parts[0].file if file else os.path.dirname(media.seasons[s].episodes[e].items[0].parts[0].file)

### Get media root folder ###
def GetLibraryRootPath(dir):
  library, root, path = '', '', ''
  for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(0, dir.count(os.sep))]:
    if root in PLEX_LIBRARY:
      library = PLEX_LIBRARY[root]
      path    = os.path.relpath(dir, root)
      break
  else:  #401 no right to list libraries (windows)
    Log.Info(u'[!] Library access denied')
    filename = os.path.join(CachePath, '_Logs', '_root_.scanner.log')
    if os.path.isfile(filename):
      Log.Info(u'[!] ASS root scanner file present: "{}"'.format(filename))
      line = Core.storage.load(filename)  #with open(filename, 'rb') as file:  line=file.read()
      for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(dir.count(os.sep)-1, -1, -1)]:
        if "root: '{}'".format(root) in line:  path = os.path.relpath(dir, root).rstrip('.');  break  #Log.Info(u'[!] root not found: "{}"'.format(root))
      else: path, root = '_unknown_folder', ''
    else:  Log.Info(u'[!] ASS root scanner file missing: "{}"'.format(filename))
  return library, root, path

###
def json_load(template, *args):
  url = template.format(*args + tuple([Prefs['YouTube-Agent_youtube_api_key']]))
  url = sanitize_path(url)
  iteration = 0
  json_page = {}
  json      = {}
  while not json or Dict(json_page, 'nextPageToken') and Dict(json_page, 'pageInfo', 'resultsPerPage') !=1 and iteration<50:
    #Log.Info(u'{}'.format(Dict(json_page, 'pageInfo', 'resultsPerPage')))
    try:                    json_page = JSON.ObjectFromURL(url+'&pageToken='+Dict(json_page, 'nextPageToken') if Dict(json_page, 'nextPageToken') else url)  #Log.Info(u'items: {}'.format(len(Dict(json_page, 'items'))))
    except Exception as e:  json = JSON.ObjectFromString(e.content);  raise ValueError('code: {}, message: {}'.format(Dict(json, 'error', 'code'), Dict(json, 'error', 'message')))
    if json:  json ['items'].extend(json_page['items'])
    else:     json = json_page
    iteration +=1
  #Log.Info(u'total items: {}'.format(len(Dict(json, 'items'))))
  return json

### load image if present in local dir
def img_load(series_root_folder, filename):
  Log(u'img_load() - series_root_folder: {}, filename: {}'.format(series_root_folder, filename))
  for ext in ['jpg', 'jpeg', 'png', 'tiff', 'gif', 'jp2']:
    filename = os.path.join(series_root_folder, filename.rsplit('.', 1)[0]+"."+ext)
    if os.path.isfile(filename):  Log(u'local thumbnail found for file %s', filename);  return filename, Core.storage.load(filename)
  return "", None

def Start():
  HTTP.CacheTime                  = CACHE_1MONTH
  HTTP.Headers['User-Agent'     ] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
  HTTP.Headers['Accept-Language'] = 'en-us'

### Assign unique ID ###
def Search(results, media, lang, manual, movie):
  
  displayname = sanitize_path(os.path.basename(media.name if movie else media.show))
  filename    = media.items[0].parts[0].file if movie else media.filename or media.show
  dir         = GetMediaDir(media, movie)
  try:                    filename = sanitize_path(filename)
  except Exception as e:  Log('search() - Exception1: filename: "{}", e: "{}"'.format(filename, e))
  try:                    filename = os.path.basename(filename)
  except Exception as e:  Log('search() - Exception2: filename: "{}", e: "{}"'.format(filename, e))
  try:                    filename = urllib2.unquote(filename)
  except Exception as e:  Log('search() - Exception3: filename: "{}", e: "{}"'.format(filename, e))
  Log(u''.ljust(157, '='))
  Log(u"Search() - dir: {}, filename: {}, displayname: {}".format(dir, filename, displayname))
    
  ### Try loading local JSON file if present
  json_filename = os.path.splitext(filename)[0]+ ".info.json" #filename.rsplit('.', 1)[0] + ".info.json"
  if os.path.exists(json_filename):
    Log(u'searching for info file - dir: {}, json_filename: {}'.format(dir, json_filename))
    try:     json_video_details = JSON.ObjectFromString(Core.storage.load(json_filename))  #with open(json_filename) as f:  json_video_details = JSON.ObjectFromString(f.read())
    except:  pass
    else:
      results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(Dict(json_video_details, 'id'), os.path.basename(dir)), name=displayname, year=Datetime.ParseDate(Dict(json_video_details, 'upload_date')).year, score=100, lang=lang ) )
      Log(u''.ljust(157, '='))
      return
  
  try:
    for regex, url in [('PLAYLIST', YOUTUBE_PLAYLIST_REGEX), ('CHANNEL', YOUTUBE_CHANNEL_REGEX), ('VIDEO', YOUTUBE_VIDEO_REGEX)]:
      result = url.search(filename)
      if result:
        guid = result.group('id')
        Log.Info(u'search() - YouTube ID found - regex: {}, youtube ID: "{}"'.format(regex, guid))
        results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(guid,os.path.basename(dir)), name=displayname, year=None, score=100, lang=lang ) )
        Log(u''.ljust(157, '='))
        return
      else: Log.Info('search() - YouTube ID not found - regex: "{}"'.format(regex))  
  except Exception as e:  Log('search() - filename: "{}" Regex failed to find YouTube id, error: "{}"'.format(filename, e))
  
  if movie:  Log.Info(filename)
  else:    
    s = media.seasons.keys()[0] if media.seasons.keys()[0]!='0' else media.seasons.keys()[1] if len(media.seasons.keys()) >1 else None
    if s:
      e      = media.seasons[s].episodes.keys()[0]
      result = YOUTUBE_PLAYLIST_REGEX.search(os.path.basename(os.path.dirname(dir)))
      guid   = result.group('id') if result else ''
      if result or os.path.exists(os.path.join(dir, 'youtube.id')):
        Log(u'search() - filename: "{}", found season YouTube playlist id, result.group("id"): {}'.format(filename, result.group('id')))
        results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(guid,dir), name=filename, year=None, score=100, lang=lang ) )
        Log(u''.ljust(157, '='))
        return
      else:  Log('search() - id not found')
  
  try:
    json_video_details = json_load(YOUTUBE_VIDEO_SEARCH, String.Quote(filename, usePlus=False))
    if Dict(json_video_details, 'pageInfo', 'totalResults'):
      Log.Info(u'filename: "{}", title:        "{}"'.format(filename, Dict(json_video_details, 'items', 0, 'snippet', 'title')))
      Log.Info(u'filename: "{}", channelTitle: "{}"'.format(filename, Dict(json_video_details, 'items', 0, 'snippet', 'channelTitle')))
      if filename == Dict(json_video_details, 'items', 0, 'snippet', 'channelTitle'):
        Log.Info(u'filename: "{}", found exact matching YouTube title: "{}", description: "{}"'.format(filename, Dict(json_video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(json_video_details, 'items', 0, 'snippet', 'description')))
        results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(Dict(json_video_details, 'items', 0, 'id', 'channelId'),dir), name=filename, year=None, score=100, lang=lang ) )
        Log(u''.ljust(157, '='))
        return
      else:  Log.Info(u'search() - no id in title nor matching YouTube title: "{}", closest match: "{}", description: "{}"'.format(filename, Dict(json_video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(json_video_details, 'items', 0, 'snippet', 'description')))
    elif 'error' in json_video_details:  Log.Info(u'search() - code: "{}", message: "{}"'.format(Dict(json_video_details, 'error', 'code'), Dict(json_video_details, 'error', 'message')))
  except Exception as e:  Log(u'search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(filename, e))

  library, root, path = GetLibraryRootPath(dir)
  Log(u'Putting folder name "{}" as guid since no assign channel id or playlist id was assigned'.format(path.split(os.sep)[-1]))
  results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(path.split(os.sep)[-2] if os.sep in path else '', dir), name=os.path.basename(filename), year=None, score=80, lang=lang ) )
  Log(''.ljust(157, '='))

### Download metadata using unique ID ###
def Update(metadata, media, lang, force, movie):
  Log(u'=== update(lang={}, force={}, movie={}) ==='.format(lang, force, movie))
  temp1, guid, series_folder = metadata.id.split("|")
  dir                        = sanitize_path(GetMediaDir(media, movie))
  channel_id                 = guid if guid.startswith('UC') or guid.startswith('HC') else ''
  channel_title              = ""
  json                       = {}
  json_playlist_details      = {}
  json_playlist_items        = {}
  json_channel_items         = {}
  json_channel_details       = {}
  json_video_details         = {}
  series_folder              = sanitize_path(series_folder)
  if not (len(guid)>2 and guid[0:2] in ('PL', 'UU', 'FL', 'LP', 'RD')):  metadata.title = re.sub(r'\[.*\]', '', dir).strip()  #no id mode, update title so ep gets updated
  Log(u''.ljust(157, '='))
    
  ### Movie Library ###
  if movie:

    ### Movie - JSON call ###############################################################################################################
    json_filename = GetMediaDir(media, movie, True).rsplit('.', 1)[0] + ".info.json"
    if os.path.exists(json_filename):
      Log(u'Update using present json file - json_filename: {}'.format(json_filename))
      try:             json_video_details = JSON.ObjectFromString(Core.storage.load(json_filename))
      except IOError:  guid = None
      else:    
        guid          = Dict(json_video_details, 'id')
        channel_id    = Dict(json_video_details, 'channel_id')
        
        ### Movie - Local JSON
        Log.Info(u'update() using json file json_video_details - Loaded video details from: "{}"'.format(json_filename))
        metadata.title                   = Dict(json_video_details, 'title');                                  Log(u'series title:       "{}"'.format(Dict(json_video_details, 'title')))
        metadata.summary                 = Dict(json_video_details, 'description');                            Log(u'series description: '+Dict(json_video_details, 'description').replace('\n', '. '))
        metadata.duration                = Dict(json_video_details, 'duration');                               Log(u'series duration:    "{}"->"{}"'.format(Dict(json_video_details, 'duration'), metadata.duration))
        metadata.genres                  = Dict(json_video_details, 'categories');                             Log(u'genres: '+str([x for x in metadata.genres]))
        date                             = Datetime.ParseDate(Dict(json_video_details, 'upload_date'));        Log(u'date:  "{}"'.format(date))
        metadata.originally_available_at = date.date()
        metadata.year                    = date.year  #test avoid:  AttributeError: 'TV_Show' object has no attribute named 'year'
        thumb                            = Dict(json_video_details, 'thumbnails', 3, 'url') or Dict(json_video_details, 'thumbnails', 2, 'url') or Dict(json_video_details, 'thumbnails', 1, 'url') or Dict(json_video_details, 'thumbnails', 0, 'url')
        if thumb and thumb not in metadata.posters:
          Log(u'poster: "{}" added'.format(thumb))
          metadata.posters[thumb]        = Proxy.Media(HTTP.Request(Dict(json_video_details, 'thumbnails', '0', 'url')).content, sort_order=1)
        else:  Log(u'thumb: "{}" already present'.format(thumb))
        if Dict(json_video_details, 'statistics', 'likeCount') and int(Dict(json_video_details, 'like_count')) > 0 and Dict(json_video_details, 'dislike_count') and int(Dict(json_video_details, 'dislike_count')) > 0:
          metadata.rating                = float(10*int(Dict(json_video_details, 'like_count'))/(int(Dict(json_video_details, 'dislike_count'))+int(Dict(json_video_details, 'like_count'))));  Log(u'rating: {}'.format(metadata.rating))
        if Prefs['add_user_as_director']:
          metadata.directors.clear()
          try:
            meta_director       = metadata.directors.new()
            meta_director.name  = channel_title
            Log('director: '+ channel_title)
          except:  pass
        return

    ### Movie - API call ################################################################################################################
    Log(u'update() using api - guid: {}, dir: {}, metadata.id: {}'.format(guid, dir, metadata.id))
    try:     json_video_details = json_load(YOUTUBE_json_video_details, guid)['items'][0]
    except:  Log(u'json_video_details - Could not retrieve data from YouTube for: ' + guid)
    else:
      Log('Movie mode - json_video_details - Loaded video details from: "{}"'.format(YOUTUBE_json_video_details, 'personal_key'))
      date                             = Datetime.ParseDate(json_video_details['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
      metadata.originally_available_at = date.date()
      metadata.title                   = json_video_details['snippet']['title'];                                                      Log(u'series title:       "{}"'.format(json_video_details['snippet']['title']))
      metadata.summary                 = json_video_details['snippet']['description'];                                                Log(u'series description: '+json_video_details['snippet']['description'].replace('\n', '. '))
      metadata.duration                = ISO8601DurationToSeconds(json_video_details['contentDetails']['duration'])*1000;             Log(u'series duration:    "{}"->"{}"'.format(json_video_details['contentDetails']['duration'], metadata.duration))
      metadata.genres                  = [YOUTUBE_CATEGORY_ID[id] for id in json_video_details['snippet']['categoryId'].split(',')];  Log(u'genres: '+str([x for x in metadata.genres]))
      metadata.year                    = date.year;                                                                              Log(u'movie year: {}'.format(date.year))
      thumb                            = json_video_details['snippet']['thumbnails']['default']['url'];                               Log(u'thumb: "{}"'.format(thumb))
      if thumb and thumb not in metadata.posters:
        Log(u'poster: "{}"'.format(thumb))
        metadata.posters[thumb]        = Proxy.Media(HTTP.Request(Dict(json_video_details, 'snippet', 'thumbnails', 'maxres', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'default', 'url')).content, sort_order=1)
      if Dict(json_video_details, 'statistics', 'likeCount') and int(json_video_details['statistics']['likeCount']) > 0 and Dict(json_video_details, 'statistics', 'dislikeCount') and int(Dict(json_video_details, 'statistics', 'dislikeCount')) > 0:
        metadata.rating                = float(10*int(json_video_details['statistics']['likeCount'])/(int(json_video_details['statistics']['dislikeCount'])+int(json_video_details['statistics']['likeCount'])));  Log('rating: {}'.format(metadata.rating))
      if Prefs['add_user_as_director']:
        metadata.directors.clear()
        try:
          meta_director       = metadata.directors.new()
          meta_director.name  = json_video_details['snippet']['channelTitle']
          Log(u'director: '+json_video_details['snippet']['channelTitle'])
        except Exception as e:  Log.Info(u'[!] add_user_as_director exception: {}'.format(e))
      return
  
  ### TV series Library ###
  else:
    title=""
    ### Collection tag for grouping folders ###
    library, root, path = GetLibraryRootPath(dir)
    series_root_folder=''
    Log.Info(u'[ ] library:    "{}"'.format(library))
    Log.Info(u'[ ] root:       "{}"'.format(root   ))
    Log.Info(u'[ ] path:       "{}"'.format(path   ))
    Log.Info(u'[ ] dir:        "{}"'.format(dir    ))
    metadata.studio = 'YouTube'
    if not path in ('_unknown_folder', '.'):
      #Log.Info('[ ] series root folder:        "{}"'.format(os.path.join(root, path.split(os.sep, 1)[0])))
      series_root_folder  = os.path.join(root, path.split(os.sep, 1)[0] if os.sep in path else path) 
      Log.Info(u'[ ] series_root_folder: "{}"'.format(series_root_folder))
      list_files      = os.listdir(series_root_folder) if os.path.exists(series_root_folder) else []
      subfolder_count = len([file for file in list_files if os.path.isdir(os.path.join(series_root_folder, file))])
      Log.Info(u'[ ] subfolder_count:    "{}"'.format(subfolder_count   ))

      ### Extract season and transparent folder to reduce complexity and use folder as serie name ###
      reverse_path, season_folder_first = list(reversed(path.split(os.sep))), False
      SEASON_RX = [ '^Specials',                                                                                                                                           # Specials (season 0)
                    '^(?P<show>.*)?[\._\-\— ]*?(Season|Series|Book|Saison|Livre|Temporada|[Ss])[\._\—\- ]*?(?P<season>\d{1,4}).*?',                                        # (title) S01
                    '^(?P<show>.*)?[\._\-\— ]*?Volume[\._\-\— ]*?(?P<season>(?=[MDCLXVI])M*D?C{0,4}L?X{0,4}V?I{0,4}).*?',                                                  # (title) S01
                    '^(Saga|(Story )?Ar[kc])']                                                                                                                             # Last entry, folder name droped but files kept: Saga / Story Ar[kc] / Ar[kc]
      for folder in reverse_path[:-1]:                 # remove root folder from test, [:-1] Doesn't thow errors but gives an empty list if items don't exist, might not be what you want in other cases
        for rx in SEASON_RX[:-1]:                      # in anime, more specials folders than season folders, so doing it first
          if re.match(rx, folder, re.IGNORECASE):      # get season number but Skip last entry in seasons (skipped folders)
            reverse_path.remove(folder)                # Since iterating slice [:] or [:-1] doesn't hinder iteration. All ways to remove: reverse_path.pop(-1), reverse_path.remove(thing|array[0])
            if rx!=SEASON_RX[-1] and len(reverse_path)>=2 and folder==reverse_path[-2]:  season_folder_first = True
            break

      if len(reverse_path)>1 and not season_folder_first and subfolder_count>1:  ### grouping folders only ###
        Log.Info("Grouping folder found, root: {}, path: {}, Grouping folder: {}, subdirs: {}, reverse_path: {}".format(root, path, os.path.basename(series_root_folder), subfolder_count, reverse_path))
        collection = re.sub(r'\[.*\]', '', reverse_path[-1]).strip()
        Log.Info('[ ] collections:        "{}"'.format(collection))
        if collection not in metadata.collections:  metadata.collections=[collection]
      else:  Log.Info("Grouping folder not found or single folder, root: {}, path: {}, Grouping folder: {}, subdirs: {}, reverse_path: {}".format(root, path, os.path.basename(series_root_folder), subfolder_count, reverse_path))

    ### Series - Playlist ###############################################################################################################
    if len(guid)>2 and guid[0:2] in ('PL', 'UU', 'FL', 'LP', 'RD'):
      Log.Info('[?] json_playlist_details')
      try:                    json_playlist_details = json_load(YOUTUBE_PLAYLIST_DETAILS, guid)['items'][0]
      except Exception as e:  Log('[!] json_playlist_details exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_DETAILS.format(guid, 'personal_key')))
      else:
        Log.Info('[?] json_playlist_details: {}'.format(json_playlist_details.keys()))
        channel_id                       = Dict(json_playlist_details, 'snippet', 'channelId');                               Log.Info('[ ] channel_id: "{}"'.format(channel_id))
        title                            = sanitize_path(Dict(json_playlist_details, 'snippet', 'title'));                    Log.Info('[ ] title:      "{}"'.format(metadata.title))
        if title: metadata.title = title
        metadata.originally_available_at = Datetime.ParseDate(Dict(json_playlist_details, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_playlist_details, 'snippet', 'publishedAt' )))
        metadata.summary                 = Dict(json_playlist_details, 'snippet', 'description');                             Log.Info('[ ] summary:     "{}"'.format((Dict(json_playlist_details, 'snippet', 'description').replace('\n', '. '))))
        
      Log.Info('[?] json_playlist_items')
      try:                    json_playlist_items = json_load(YOUTUBE_PLAYLIST_ITEMS, guid)
      except Exception as e:  Log.Info('[!] json_playlist_items exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_ITEMS.format(guid, 'personal_key')))
      else:
        Log.Info('[?] json_playlist_items: {}'.format(json_playlist_items.keys()))
        first_video = sorted(Dict(json_playlist_items, 'items'), key=lambda i: Dict(i, 'contentDetails', 'videoPublishedAt'))[0]
        thumb = Dict(first_video, 'snippet', 'thumbnails', 'maxres', 'url') or Dict(first_video, 'snippet', 'thumbnails', 'medium', 'url') or Dict(first_video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(first_video, 'snippet', 'thumbnails', 'high', 'url') or Dict(first_video, 'snippet', 'thumbnails', 'default', 'url')
        if thumb and thumb not in metadata.posters:  Log('[ ] posters:   {}'.format(thumb));  metadata.posters [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1 if Prefs['media_poster_source']=='Episode' else 2)
        else:                                        Log('[X] posters:   {}'.format(thumb))
    
    ### Series - Channel ###############################################################################################################
    if channel_id.startswith('UC') or channel_id.startswith('HC'):
      try:                    json_channel_details  = json_load(YOUTUBE_CHANNEL_DETAILS, channel_id)['items'][0]
      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        
        if not title:
          title          = re.sub( "\s*\[.*?\]\s*"," ",series_folder)  #instead of path use series foldername
          metadata.title = title
        Log.Info('[ ] title:        "{}", metadata.title: "{}"'.format(title, metadata.title))
        if not Dict(json_playlist_details, 'snippet', 'description'):
          if Dict(json_channel_details, 'snippet', 'description'):  metadata.summary = sanitize_path(Dict(json_channel_details, 'snippet', 'description'))
          else:
            summary  = u'Channel with {} videos, '.format(Dict(json_channel_details, 'statistics', 'videoCount'))
            summary += u'{} subscribers, '.format(Dict(json_channel_details, 'statistics', 'subscriberCount'))
            summary += u'{} views'.format(Dict(json_channel_details, 'statistics', 'viewCount'))
            metadata.summary = sanitize_path(summary);  Log.Info(u'[ ] summary:     "{}"'.format(summary))  #
        
        if Dict(json_channel_details,'snippet','country') and Dict(json_channel_details,'snippet','country') not in metadata.countries:
          metadata.countries.add(Dict(json_channel_details,'snippet','country'));  Log.Info('[ ] country: {}'.format(Dict(json_channel_details,'snippet','country') ))

        ### Playlist with cast coming from multiple chan entries in youtube.id file ###############################################################################################################
        if os.path.exists(os.path.join(dir, 'youtube.id')):
          with open(os.path.join(dir, 'youtube.id')) as f:
            metadata.roles.clear()
            for line in f.readlines():
              try:                    json_channel_details = json_load(YOUTUBE_CHANNEL_DETAILS, line.rstrip())['items'][0]
              except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
              else:
                Log.Info('[?] json_channel_details: {}'.format(json_channel_details.keys()))
                Log.Info('[ ] title:       "{}"'.format(Dict(json_channel_details, 'snippet', 'title'      )))
                if not Dict(json_playlist_details, 'snippet', 'description'):
                  if Dict(json_channel_details, 'snippet', 'description'):  metadata.summary =  sanitize_path(Dict(json_channel_details, 'snippet', 'description'))
                  #elif guid.startswith('PL'):  metadata.summary = 'No Playlist nor Channel summary'
                  else:
                    summary  = u'Channel with {} videos, '.format(Dict(json_channel_details, 'statistics', 'videoCount'     ))
                    summary += u'{} subscribers, '.format(Dict(json_channel_details, 'statistics', 'subscriberCount'))
                    summary += u'{} views'.format(Dict(json_channel_details, 'statistics', 'viewCount'      ))
                    metadata.summary = sanitize_path(summary) #or 'No Channel summary'
                    Log.Info(u'[ ] summary:     "{}"'.format(Dict(json_channel_details, 'snippet', 'description').replace('\n', '. ')))  #
                
                if Dict(json_channel_details,'snippet','country') and Dict(json_channel_details,'snippet','country') not in metadata.countries:
                  metadata.countries.add(Dict(json_channel_details,'snippet','country'));  Log.Info('[ ] country: {}'.format(Dict(json_channel_details,'snippet','country') ))
                
                thumb_channel = Dict(json_channel_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_channel_details, 'snippet', 'thumbnails', 'high', 'url')   or Dict(json_channel_details, 'snippet', 'thumbnails', 'default', 'url')
                role       = metadata.roles.new()
                role.role  = sanitize_path(Dict(json_channel_details, 'snippet', 'title'))
                role.name  = sanitize_path(Dict(json_channel_details, 'snippet', 'title'))
                role.photo = thumb_channel
                Log.Info('[ ] role:        {}'.format(Dict(json_channel_details,'snippet','title')))
                
                thumb = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvLowImageUrl' ) or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvMediumImageUrl') \
                  or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvHighImageUrl') or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvImageUrl'      )
                external_banner_url = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerExternalUrl')
                if not thumb and external_banner_url: thumb = '{}=s1920'.format(external_banner_url)
                if thumb and thumb not in metadata.art:      Log('[X] art:       {}'.format(thumb));  metadata.art [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
                else:                                        Log('[ ] art:       {}'.format(thumb))
                if thumb and thumb not in metadata.banners:  Log('[X] banners:   {}'.format(thumb));  metadata.banners [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
                else:                                        Log('[ ] banners:   {}'.format(thumb))
                if thumb_channel and thumb_channel not in metadata.posters:
                  Log('[X] posters:   {}'.format(thumb_channel))
                  metadata.posters [thumb_channel] = Proxy.Media(HTTP.Request(thumb_channel).content, sort_order=1 if Prefs['media_poster_source']=='Channel' else 2)
                  #metadata.posters.validate_keys([thumb_channel])
                else:                                                        Log('[ ] posters:   {}'.format(thumb_channel))
        
        ### Cast comes from channel
        else:    
          thumb         = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvLowImageUrl' ) or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvMediumImageUrl') \
                       or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvHighImageUrl') or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvImageUrl'      )
          external_banner_url = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerExternalUrl')
          if not thumb and external_banner_url: thumb = '{}=s1920'.format(external_banner_url)
          if thumb and thumb not in metadata.art:      Log(u'[X] art:       {}'.format(thumb));  metadata.art [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
          else:                                        Log(u'[ ] art:       {}'.format(thumb))
          if thumb and thumb not in metadata.banners:  Log(u'[X] banners:   {}'.format(thumb));  metadata.banners [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
          else:                                        Log(u'[ ] banners:   {}'.format(thumb))
          thumb_channel = Dict(json_channel_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_channel_details, 'snippet', 'thumbnails', 'high', 'url')   or Dict(json_channel_details, 'snippet', 'thumbnails', 'default', 'url')
          if thumb_channel and thumb_channel not in metadata.posters:
            #thumb_channel = sanitize_path(thumb_channel)
            Log(u'[X] posters:   {}'.format(thumb_channel))
            metadata.posters [thumb_channel] = Proxy.Media(HTTP.Request(thumb_channel).content, sort_order=1 if Prefs['media_poster_source']=='Channel' else 2)
            #metadata.posters.validate_keys([thumb_channel])
          else:                                        Log('[ ] posters:   {}'.format(thumb_channel))
          metadata.roles.clear()
          role       = metadata.roles.new()
          role.role  = sanitize_path(Dict(json_channel_details, 'snippet', 'title'))
          role.name  = sanitize_path(Dict(json_channel_details, 'snippet', 'title'))
          role.photo = thumb_channel
          Log.Info(u'[ ] role:        {}'.format(Dict(json_channel_details,'snippet','title')))
          #if not Dict(json_playlist_details, 'snippet', 'publishedAt'):  metadata.originally_available_at = Datetime.ParseDate(Dict(json_channel_items, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_channel_items, 'snippet', 'publishedAt' )))
           
    #NOT PLAYLIST NOR CHANNEL GUID
    else:  
      Log.Info('No GUID so random folder')
      metadata.title = series_folder  #instead of path use series foldername
 
    ### Season + Episode loop ###
    genre_array = {}
    episodes    = 0
    first       = True
    
    for s in sorted(media.seasons, key=natural_sort_key):
      season = metadata.seasons[s]
      Log.Info(u"".ljust(157, '='))
      Log.Info(u"Season: {:>2}".format(s))
    
      for e in sorted(media.seasons[s].episodes, key=natural_sort_key):
        filename  = os.path.basename(media.seasons[s].episodes[e].items[0].parts[0].file)
        episode   = metadata.seasons[s].episodes[e]
        episodes += 1
        Log.Info('metadata.seasons[{:>2}].episodes[{:>3}] "{}"'.format(s, e, filename))
        
        for video in Dict(json_playlist_items, 'items') or Dict(json_channel_items, 'items') or {}:
          
          # videoId in Playlist/channel
          videoId = Dict(video, 'id', 'videoId') or Dict(video, 'snippet', 'resourceId', 'videoId')
          if videoId and videoId in filename:
            episode.title                   = sanitize_path(Dict(video, 'snippet', 'title'       ));             Log.Info(u'[ ] title:        {}'.format(Dict(video, 'snippet', 'title'       )))
            episode.summary                 = sanitize_path(Dict(video, 'snippet', 'description' ));             Log.Info(u'[ ] description:  {}'.format(Dict(video, 'snippet', 'description' ).replace('\n', '. ')))
            episode.originally_available_at = Datetime.ParseDate(Dict(video, 'contentDetails', 'videoPublishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(video, 'contentDetails', 'videoPublishedAt' )))
            thumb                           = Dict(video, 'snippet', 'thumbnails', 'maxres', 'url') or Dict(video, 'snippet', 'thumbnails', 'medium', 'url')or Dict(video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video, 'snippet', 'thumbnails', 'high', 'url') or Dict(video, 'snippet', 'thumbnails', 'default', 'url')
            if thumb and thumb not in episode.thumbs:  episode.thumbs[thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1);                                Log.Info('[ ] thumbnail:    {}'.format(thumb))
            Log.Info(u'[ ] channelTitle: {}'.format(Dict(video, 'snippet', 'channelTitle')))
            break
        
        else:  # videoId not in Playlist/channel item list

          #Loading json file if available
          json_filename = filename.rsplit('.', 1)[0] + ".info.json"
          Log.Info(u'populate_episode_metadata_from_info_json() - series_root_folder: {}, filename: {}'.format(series_root_folder, filename))
          Log.Info(u'Searching for "{}". Searching in "{}".'.format(json_filename, series_root_folder))
          for root, dirnames, filenames in os.walk(series_root_folder):
            Log.Info(u'Directory {} contains {} files'.format(root, len(filenames)))  #for filename in filenames: Log.Info('File: {}'.format(filename))
            if json_filename in filenames :
              json_file = os.path.join(root, json_filename)
              try:  json_video_details = JSON.ObjectFromString(Core.storage.load(json_file))  #"JSONDecodeError: Unexpected end of input" if empty
              except: json_video_details = None
              if json_video_details:
                Log.Info('Attempting to read metadata from {}'.format(os.path.join(root, json_filename)))
                videoId = Dict(json_video_details, 'id')
                Log.Info('# videoId [{}] not in Playlist/channel item list so loading json_video_details'.format(videoId))
                Log.Info('[?] link:     "https://www.youtube.com/watch?v={}"'.format(videoId))
                thumb, picture = img_load(series_root_folder, filename)  #Load locally
                if thumb is None:
                  thumb = Dict(json_video_details, 'thumbnails', 3, 'url') or Dict(json_video_details, 'thumbnails', 2, 'url') or Dict(json_video_details, 'thumbnails', 1, 'url') or Dict(json_video_details, 'thumbnails', 0, 'url')
                  if thumb not in episode.thumbs: picture = HTTP.Request(thumb).content  
                if thumb and thumb not in episode.thumbs:
                  Log.Info(u'[ ] thumbs:   "{}"'.format(thumb))
                  episode.thumbs[thumb] = Proxy.Media(picture, sort_order=1)
                  episode.thumbs.validate_keys([thumb])
                  
                episode.title                   = sanitize_path(Dict(json_video_details, 'title'));            Log.Info(u'[ ] title:    "{}"'.format(Dict(json_video_details, 'title')))
                episode.summary                 = sanitize_path(Dict(json_video_details, 'description'));      Log.Info(u'[ ] summary:  "{}"'.format(Dict(json_video_details, 'description').replace('\n', '. ')))
                if len(e)>3: episode.originally_available_at = Datetime.ParseDate(Dict(json_video_details, 'upload_date')).date();  Log.Info(u'[ ] date:     "{}"'.format(Dict(json_video_details, 'upload_date')))
                episode.duration                = int(Dict(json_video_details, 'duration'));                           Log.Info(u'[ ] duration: "{}"'.format(episode.duration))
                if Dict(json_video_details, 'likeCount') and int(Dict(json_video_details, 'like_count')) > 0 and Dict(json_video_details, 'dislike_count') and int(Dict(json_video_details, 'dislike_count')) > 0:
                  episode.rating                = float(10*int(Dict(json_video_details, 'like_count'))/(int(Dict(json_video_details, 'dislike_count'))+int(Dict(json_video_details, 'like_count'))));  Log('[ ] rating:   "{}"'.format(episode.rating))
                if channel_title and channel_title not in [role_obj.name for role_obj in episode.directors]:
                  meta_director      = episode.directors.new()
                  meta_director.name = sanitize_path(channel_title)
                  Log.Info(u'[ ] director: "{}"'.format(channel_title))

                for category  in Dict(json_video_details, 'categories') or []:  genre_array[category] = genre_array[category]+1 if category in genre_array else 1
                for tag       in Dict(json_video_details, 'tags')       or []:  genre_array[tag     ] = genre_array[tag     ]+1 if tag      in genre_array else 1
                
                Log.Info(u'[ ] genres:   "{}"'.format([x for x in metadata.genres]))  #metadata.genres.clear()
                for id in [id for id in genre_array if genre_array[id]>episodes/2 and id not in metadata.genres]:  metadata.genres.add(id)
                break
          
          #Loading from API
          else:
            Log(u'populate_episode_metadata_from_api() - filename: {}'.format(filename))
            result = YOUTUBE_VIDEO_REGEX.search(filename)
            if result:
              videoId = result.group('id')
              Log.Info(u'# videoId [{}] not in Playlist/channel item list so loading json_video_details'.format(videoId))
              try:                    json_video_details = json_load(YOUTUBE_json_video_details, videoId)['items'][0]
              except Exception as e:  Log('Error: "{}"'.format(e))
              else:
                Log.Info('[?] link:     "https://www.youtube.com/watch?v={}"'.format(videoId))
                thumb                           = Dict(json_video_details, 'snippet', 'thumbnails', 'maxres', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_video_details, 'snippet', 'thumbnails', 'default', 'url')
                episode.title                   = sanitize_path(json_video_details['snippet']['title']);                                 Log.Info('[ ] title:    "{}"'.format(json_video_details['snippet']['title']))
                episode.summary                 = sanitize_path(json_video_details['snippet']['description']);                           Log.Info('[ ] summary:  "{}"'.format(json_video_details['snippet']['description'].replace('\n', '. ')))
                if len(e)>3:  episode.originally_available_at = Datetime.ParseDate(json_video_details['snippet']['publishedAt']).date();                       Log.Info('[ ] date:     "{}"'.format(json_video_details['snippet']['publishedAt']))
                episode.duration                = ISO8601DurationToSeconds(json_video_details['contentDetails']['duration'])*1000;               Log.Info('[ ] duration: "{}"->"{}"'.format(json_video_details['contentDetails']['duration'], episode.duration))
                if Dict(json_video_details, 'statistics', 'likeCount') and int(json_video_details['statistics']['likeCount']) > 0 and Dict(json_video_details, 'statistics', 'dislikeCount') and int(Dict(json_video_details, 'statistics', 'dislikeCount')) > 0:
                  episode.rating                = 10*float(json_video_details['statistics']['likeCount'])/(float(json_video_details['statistics']['dislikeCount'])+float(json_video_details['statistics']['likeCount']));  Log('[ ] rating:   "{}"'.format(episode.rating))
                if thumb and thumb not in episode.thumbs:
                  picture = HTTP.Request(thumb).content
                  episode.thumbs[thumb]         = Proxy.Media(picture, sort_order=1);                                                     Log.Info('[ ] thumbs:   "{}"'.format(thumb))
                  episode.thumbs.validate_keys([thumb])
                  Log.Info(u'[ ] Thumb: {}'.format(thumb))
                if Dict(json_video_details, 'snippet',  'channelTitle') and Dict(json_video_details, 'snippet',  'channelTitle') not in [role_obj.name for role_obj in episode.directors]:
                  meta_director       = episode.directors.new()
                  meta_director.name  = sanitize_path(Dict(json_video_details, 'snippet',  'channelTitle'))
                  Log.Info('[ ] director: "{}"'.format(Dict(json_video_details, 'snippet',  'channelTitle')))
                
                for id  in Dict(json_video_details, 'snippet', 'categoryId').split(',') or []:  genre_array[YOUTUBE_CATEGORY_ID[id]] = genre_array[YOUTUBE_CATEGORY_ID[id]]+1 if YOUTUBE_CATEGORY_ID[id] in genre_array else 1
                for tag in Dict(json_video_details, 'snippet', 'tags')                  or []:  genre_array[tag                    ] = genre_array[tag                    ]+1 if tag                     in genre_array else 1

              Log.Info(u'[ ] genres:   "{}"'.format([x for x in metadata.genres]))  #metadata.genres.clear()
              genre_array_cleansed = [id for id in genre_array if genre_array[id]>episodes/2 and id not in metadata.genres]  #Log.Info('[ ] genre_list: {}'.format(genre_list))
              for id in genre_array_cleansed:  metadata.genres.add(id)
            else:  Log.Info(u'videoId not found in filename')

  Log('=== End Of Agent Call, errors after that are Plex related ==='.ljust(157, '='))

### Agent declaration ##################################################################################################################################################
class YouTubeSeriesAgent(Agent.TV_Shows):
  name, primary_provider, fallback_agent, contributes_to, accepts_from, languages = 'YouTubeSeries', True, None, None, ['com.plexapp.agents.localmedia'], [Locale.Language.NoLanguage]
  def search (self, results,  media, lang, manual):  Search (results,  media, lang, manual, False)
  def update (self, metadata, media, lang, force ):  Update (metadata, media, lang, force,  False)

class YouTubeMovieAgent(Agent.Movies):
  name, primary_provider, fallback_agent, contributes_to, accepts_from, languages = 'YouTubeMovie', True, None, None, ['com.plexapp.agents.localmedia'], [Locale.Language.NoLanguage]
  def search (self, results,  media, lang, manual):  Search (results,  media, lang, manual, True)
  def update (self, metadata, media, lang, force ):  Update (metadata, media, lang, force,  True)

### Variables ###
PlexRoot                 = os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "..", "..", "..", ".."))
CachePath                = os.path.join(PlexRoot, "Plug-in Support", "Data", "com.plexapp.agents.hama", "DataItems")
PLEX_LIBRARY             = {}
PLEX_LIBRARY_URL         = "http://127.0.0.1:32400/library/sections/"    # Allow to get the library name to get a log per library https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token
YOUTUBE_API_BASE_URL     = "https://www.googleapis.com/youtube/v3/"
YOUTUBE_CHANNEL_ITEMS    = YOUTUBE_API_BASE_URL + 'search?order=date&part=snippet&type=video&maxResults=50&channelId={}&key={}' #NOT_USED
YOUTUBE_CHANNEL_DETAILS  = YOUTUBE_API_BASE_URL + 'channels?part=snippet%2CcontentDetails%2Cstatistics%2CbrandingSettings&id={}&key={}'
YOUTUBE_CHANNEL_REGEX    = Regex('\[(?:youtube(|2)\-)?(?P<id>UC[a-zA-Z0-9\-_]{22}|HC[a-zA-Z0-9\-_]{22})\]')
YOUTUBE_PLAYLIST_ITEMS   = YOUTUBE_API_BASE_URL + 'playlistItems?part=snippet,contentDetails&maxResults=50&playlistId={}&key={}'
YOUTUBE_PLAYLIST_DETAILS = YOUTUBE_API_BASE_URL + 'playlists?part=snippet,contentDetails&id={}&key={}'
YOUTUBE_PLAYLIST_REGEX   = Regex('\[(?:youtube(|3)\-)?(?P<id>PL[^\[\]]{16}|PL[^\[\]]{32}|UU[^\[\]]{22}|FL[^\[\]]{22}|LP[^\[\]]{22}|RD[^\[\]]{22}|UC[^\[\]]{22}|HC[^\[\]]{22})\]',  Regex.IGNORECASE)  # https://regex101.com/r/37x8wI/2
YOUTUBE_VIDEO_SEARCH     = YOUTUBE_API_BASE_URL + 'search?&maxResults=1&part=snippet&q={}&key={}'
YOUTUBE_json_video_details    = YOUTUBE_API_BASE_URL + 'videos?part=snippet,contentDetails,statistics&id={}&key={}'
YOUTUBE_VIDEO_REGEX      = Regex('\[(?:youtube\-)?(?P<id>[a-z0-9\-_]{11})\]', Regex.IGNORECASE) # https://regex101.com/r/BFKkGc/3/
YOUTUBE_CATEGORY_ID      = {  '1': 'Film & Animation',  '2': 'Autos & Vehicles',  '10': 'Music',          '15': 'Pets & Animals',        '17': 'Sports',                 '18': 'Short Movies',
                             '19': 'Travel & Events',  '20': 'Gaming',            '21': 'Videoblogging',  '22': 'People & Blogs',        '23': 'Comedy',                 '24': 'Entertainment',
                             '25': 'News & Politics',  '26': 'Howto & Style',     '27': 'Education',      '28': 'Science & Technology',  '29': 'Nonprofits & Activism',  '30': 'Movies',
                             '31': 'Anime/Animation',  '32': 'Action/Adventure',  '33': 'Classics',       '34': 'Comedy',                '35': 'Documentary',            '36': 'Drama', 
                             '37': 'Family',           '38': 'Foreign',           '39': 'Horror',         '40': 'Sci-Fi/Fantasy',        '41': 'Thriller',               '42': 'Shorts',
                             '43': 'Shows',            '44': 'Trailers'}
### Plex Library XML ###
Log.Info(u"Library: "+PlexRoot)  #Log.Info(file)
token_file_path = os.path.join(PlexRoot, "X-Plex-Token.id")
if os.path.isfile(token_file_path):
  Log.Info(u"'X-Plex-Token.id' file present")
  token_file=Data.Load(token_file_path)
  if token_file:  PLEX_LIBRARY_URL += "?X-Plex-Token=" + token_file.strip()
  #Log.Info(PLEX_LIBRARY_URL) ##security risk if posting logs with token displayed
try:
  library_xml = etree.fromstring(urllib2.urlopen(PLEX_LIBRARY_URL).read())
  for library in library_xml.iterchildren('Directory'):
    for path in library.iterchildren('Location'):
      PLEX_LIBRARY[path.get("path")] = library.get("title")
      Log.Info(u"{} = {}".format(path.get("path"), library.get("title")))
except Exception as e:  Log.Info(u"Place correct Plex token in {} file or in PLEX_LIBRARY_URL variable in Code/__init__.py to have a log per library - https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token, Error: {}".format(token_file_path, str(e)))
