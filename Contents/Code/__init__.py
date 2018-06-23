# -*- coding: utf-8 -*-
'''
YouTube Movie and Series Metadata Agent

Movie library  
- movies/movies [video_id].ext

Serie Library
- Name [channel_id ]/file [video_id].ext   #scanner use video id to number, season 1(or year youtube3/4 mode)
- Name [Playlist_id]/file [video_id].ext   #scanner use video id to number, season 1(or year youtube-2)

Collection      | Series   | season | File
----------------|----------|--------|-----------------------
Subject         | Channel  |      1 | loose videos with video_id. year as season?
Subject/channel | Playlist |      1 | loose videos with video_id

IDs not used
- username:     channels.list(part="id", forUsername="username")
- display name: search.list(part="snippet", type="channel", q="display name") #not unique
'''

### Imports ###
import os            # path.abspath, join, dirname
import re            #
import inspect       # getfile, currentframe
from io import open  #

### Return dict value if all fields exists "" otherwise (to allow .isdigit()), avoid key errors
def Dict(var, *arg, **kwarg):  #Avoid TypeError: argument of type 'NoneType' is not iterable
  """ Return the value of an (imbricated) dictionnary, return "" if doesn't exist unless "default=new_value" specified as end argument
      Ex: Dict(variable_dict, 'field1', 'field2', default = 0)
  """
  for key in arg:
    if isinstance(var, dict) and key and key in var or isinstance(var, list) and isinstance(key, int) and 0<=key<len(var):  var = var[key]
    else:  return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var

### natural sort function ### avoid 1 10 11...19 2 20...
def natural_sort_key(s):  return [int(text) if text.isdigit() else text for text in re.split(re.compile('([0-9]+)'), str(s).lower())]  # list.sort(key=natural_sort_key) #sorted(list, key=natural_sort_key) - Turn a string into string list of chunks "z23a" -> ["z", 23, "a"]

### Convert ISO8601 Duration format into seconds ###
def ISO8601DurationToSeconds(duration):
  def js_int(value):  return int(''.join([x for x in list(value or '0') if x.isdigit()]))  # js-like parseInt - https://gist.github.com/douglasmiranda/2174255
  match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
  return 3600 * js_int(match[0]) + 60 * js_int(match[1]) + js_int(match[2])

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
    Log.Info('[!] Library access denied')
    filename = os.path.join(CachePath, '_Logs', '_root_.scanner.log')
    if os.path.isfile(filename):
      Log.Info('[!] ASS root scanner file present: "{}"'.format(filename))
      with open(filename, 'r') as file:  line=file.read()
      for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(dir.count(os.sep)-1, -1, -1)]:
        if "root: '{}'".format(root) in line:
          path = os.path.relpath(dir, root).rstrip('.')
          break
        Log.Info('[!] root not found: "{}"'.format(root))
      else: path, root = '_unknown_folder', '';  
    else:  Log.Info('[!] ASS root scanner file missing: "{}"'.format(filename))
  return library, root, path

### 
def json_load(url):
  iteration = 0
  json_page = {}
  json      = {}
  while not json or Dict(json_page, 'nextPageToken') and Dict(json_page, 'pageInfo', 'resultsPerPage') !=1 and iteration<20:
    #Log.Info('{}'.format(Dict(json_page, 'pageInfo', 'resultsPerPage')))
    try:
      json_page = JSON.ObjectFromURL(url+'&pageToken='+Dict(json_page, 'nextPageToken') if Dict(json_page, 'nextPageToken') else url)
      #Log.Info('items: {}'.format(len(Dict(json_page, 'items'))))
    except Exception as e:
      json = JSON.ObjectFromString(e.content)
      raise ValueError('code: {}, message: {}'.format(Dict(json, 'error', 'code'), Dict(json, 'error', 'message')))
    if json:  json ['items'].extend(json_page['items'])
    else:     json = json_page
    iteration +=1
  #Log.Info('total items: {}'.format(len(Dict(json, 'items'))))
  return json

def Start():
  HTTP.CacheTime                  = CACHE_1MONTH
  HTTP.Headers['User-Agent'     ] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
  HTTP.Headers['Accept-Language'] = 'en-us'

### Assign unique ID ###
def Search(results, media, lang, manual, movie):
  filename = media.title if movie else media.show #os.path.splitext(os.path.basename(media.filename))[0]
  Log(''.ljust(157, '='))
  Log('search()')
  
  try:
    regex  = 'YOUTUBE_REGEX_PLAYLIST'
    result = YOUTUBE_REGEX_PLAYLIST.search(filename)
    if result: guid = result.group('id')
    else: 
      regex  = 'YOUTUBE_REGEX_VIDEO'
      result = YOUTUBE_REGEX_VIDEO.search(filename)
      if result: guid = result.group('id')
      else:      guid = None
  except Exception as e:  guid = None;  Log('search() - filename: "{}" Regex failed to find YouTube id: "{}", error: "{}"'.format(filename, regex, e))
  if guid:
    Log('search() - filename: "{}", found youtube ID: "{}"'.format(filename, guid))
    results.Append( MetadataSearchResult( id='youtube-'+guid,  name=filename, year=None, score=100, lang=lang ) )
  else:
    if not movie: 
      s = media.seasons.keys()[0] if media.seasons.keys()[0]!='0' else media.seasons.keys()[1] if len(media.seasons.keys()) >1 else None
      if s:
        e          = media.seasons[s].episodes.keys()[0]
        dir        = os.path.dirname(media.seasons[s].episodes[e].items[0].parts[0].file)
        result = YOUTUBE_REGEX_PLAYLIST.search(os.path.basename(dir))
        guid   = result.group('id') if result else ''
        if result or os.path.exists(os.path.join(dir, 'youtube.id')):
          Log('search() - filename: "{}", found season YouTube playlist id, result.group("id"): {}'.format(filename, result.group('id')))
          results.Append( MetadataSearchResult( id='youtube-'+guid, name=filename, year=None, score=100, lang=lang ) )
          Log(''.ljust(157, '='))
          return
        Log('search() - id not found')
    try:
      video_details = json_load(YOUTUBE_VIDEO_SEARCH % (String.Quote(filename, usePlus=False)))
      if Dict(video_details, 'pageInfo', 'totalResults'):
        Log.Info('filename: "{}", title:        "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'title')))
        Log.Info('filename: "{}", channelTitle: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle')))
        if filename == Dict(video_details, 'items', 0, 'snippet', 'channelTitle'):   
          Log.Info('filename: "{}", found exact matching YouTube title: "{}", description: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(video_details, 'items', 0, 'snippet', 'description')))
          results.Append( MetadataSearchResult( id='youtube-'+Dict(video_details, 'items', 0, 'id', 'channelId'), name=filename, year=None, score=100, lang=lang ) )
        else:  Log.Info('search() - no id in title nor matching YouTube title: "{}", closest match: "{}", description: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(video_details, 'items', 0, 'snippet', 'description')))
      elif 'error' in video_details:  Log.Info('search() - code: "{}", message: "{}"'.format(Dict(video_details, 'error', 'code'), Dict(video_details, 'error', 'message')))
    except Exception as e:  Log('search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(filename, e))
    
    ###
    if not results:
      dir                 = GetMediaDir(media, movie)
      library, root, path = GetLibraryRootPath(dir)
      Log('Putting folder name "{}" as guid since no assign channel id or playlist id was assigned'.format(path.split(os.sep)[-1]))
      results.Append( MetadataSearchResult( id='youtube-'+path.split(os.sep)[-1], name=filename, year=None, score=80, lang=lang ) )
    Log(''.ljust(157, '='))
  Log(''.ljust(157, '='))

### Download metadata using unique ID ###
def Update(metadata, media, lang, force, movie):
  guid       = metadata.id.replace("youtube-", "") if metadata.id.startswith('youtube-') else metadata.id
  season_map = {}
  channelId  = None
  
  result = YOUTUBE_REGEX_VIDEO.search(guid)
  if not guid.startswith('PL') and not guid.startswith('UC') and not result:
    metadata.title = guid  #no id mode, update title so ep gets updated
      
  ### Movie library and video tag ###
  Log(''.ljust(157, '='))
  Log('update() - metadata,id: "{}"'.format(guid))
  if movie:

    # YouTube video id given
    if guid and not guid.startswith('PL'):
      try:     video_details = json_load(YOUTUBE_VIDEO_DETAILS % (guid))['items'][0]
      except:  Log('video_details - Could not retrieve data from YouTube for: %s' % guid)
      else:
        Log('video_details - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS % (guid)))
        date                             = Datetime.ParseDate(video_details['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
        metadata.originally_available_at = date.date()
        metadata.title                   = video_details['snippet']['title'];                                           Log('series title:       "{}"'.format(video_details['snippet']['title'])) 
        metadata.summary                 = video_details['snippet']['description'];                                     Log('series description: '+video_details['snippet']['description'].replace('\n', '. '))
        thumb                            = video_details['snippet']['thumbnails']['default']['url'];                    Log('thumb: "{}"'.format(thumb))
        poster                           = video_details['snippet']['thumbnails']['standard']['url'];                   Log('poster: "{}"'.format(thumb))
        metadata.posters[thumb]          = Proxy.Media(HTTP.Request(poster).content, sort_order=1)
        metadata.duration                = ISO8601DurationToSeconds(video_details['contentDetails']['duration'])*1000;  Log('series duration:    "{}"->"{}"'.format(video_details['contentDetails']['duration'], metadata.duration))
        metadata.rating                  = float(10*int(video_details['statistics']['likeCount'])/(int(video_details['statistics']['dislikeCount'])+int(video_details['statistics']['likeCount'])));  Log('rating: {}'.format(metadata.rating))
        metadata.genres                  = [ YOUTUBE_CATEGORY_ID[id] for id in video_details['snippet']['categoryId'].split(',') ];  Log('genres: '+str([x for x in metadata.genres]))
        metadata.year                    = date.year  #test avoid:  AttributeError: 'TV_Show' object has no attribute named 'year'
      
        # Add YouTube user as director
        if Prefs['add_user_as_director']:
          metadata.directors.clear()
          try:
            meta_director       = metadata.directors.new()
            meta_director.name  = video_details['snippet']['channelTitle']
            Log('director: '+video_details['snippet']['channelTitle'])
          except:  pass
        #metadata.extras.add(TrailerObject(title = 'Trailer', url = 'https://www.youtube.com/watch?v=D9joM600LKA'))  #'https://www.youtube.com/watch?v='+metadata.id))
        
  ### TV series Library ###
  else: 
    
    ### Collection tag for grouping folders ###
    Local_dict          = {}
    dir                 = GetMediaDir(media, movie)
    library, root, path = GetLibraryRootPath(dir)
    Log.Info('[ ] dir:        "{}"'.format(dir    ))
    Log.Info('[ ] library:    "{}"'.format(library))
    Log.Info('[ ] root:       "{}"'.format(root   ))
    Log.Info('[ ] path:       "{}"'.format(path   ))
    if not path in ('_unknown_folder', '.'):
    
      series_root_folder  = os.path.join(root, path.split(os.sep, 1)[0])
      subfolder_count     = len([file for file in os.listdir(series_root_folder) if os.path.isdir(os.path.join(series_root_folder, file))])
      Log.Info('[ ] series_root_folder: "{}"'.format(series_root_folder))
      Log.Info('[ ] subfolder_count:    "{}"'.format(subfolder_count   ))
      
      ### Extract season and transparent folder to reduce complexity and use folder as serie name ###
      reverse_path, season_folder_first = list(reversed(path.split(os.sep))), False
      SEASON_RX = [ 'Specials',                                                                                                                                           # Specials (season 0)
                    '(Season|Series|Book|Saison|Livre|S)[ _\-]*(?P<season>[0-9]{1,2}).*',                                                                                 # Season ##, Series #Book ## Saison ##, Livre ##, S##, S ##
                    '(?P<show>.*?)[\._\- ]+[sS](?P<season>[0-9]{2})',                                                                                                     # (title) S01
                    '(?P<season>[0-9]{1,2})a? Stagione.*',                                                                                                                # ##a Stagione
                    '(?P<season>[0-9]{1,2}).*',	                                                                                                                          # ##
                    '^.*([Ss]aga]|([Ss]tory )?[Aa][Rr][KkCc]).*$'                                                                                                         # Last entry in array, folder name droped but files kept: Story, Arc, Ark, Video
                  ]                                                                                                                                                       #
      for folder in reverse_path[:-1]:                 # remove root folder from test, [:-1] Doesn't thow errors but gives an empty list if items don't exist, might not be what you want in other cases
        for rx in SEASON_RX :                          # in anime, more specials folders than season folders, so doing it first
          if re.match(rx, folder, re.IGNORECASE):      # get season number but Skip last entry in seasons (skipped folders)
            reverse_path.remove(folder)                # Since iterating slice [:] or [:-1] doesn't hinder iteration. All ways to remove: reverse_path.pop(-1), reverse_path.remove(thing|array[0])
            if rx!=SEASON_RX[-1] and len(reverse_path)>=2 and folder==reverse_path[-2]:  season_folder_first = True
            break
     
      if len(reverse_path)>1 and not season_folder_first and subfolder_count>1:  ### grouping folders only ###
        Log.Info("Grouping folder found, root: {}, path: {}, Grouping folder: {}, subdirs: {}, reverse_path: {}".format(root, path, os.path.basename(series_root_folder), subfolder_count, reverse_path))
        Log.Info('[ ] collections:        "{}"'.format(reverse_path[-1]))
        if reverse_path[-1] not in metadata.collections:  metadata.collections=[reverse_path[-1]]
          
      else:  Log.Info("Grouping folder not found or single folder, root: {}, path: {}, Grouping folder: {}, subdirs: {}, reverse_path: {}".format(root, path, os.path.basename(series_root_folder), subfolder_count, reverse_path))
    
    #
    channel_id           = guid if guid.startswith('UC') else ''
    json                 = {}
    json_playlist_items  = {}
    json_channel_items   = {}
    json_channel_details = {}
    metadata.studio      = 'YouTube'
    
    # Loading Playlist
    if guid.startswith('PL'):

      Log.Info('[?] json_playlist_details')
      try:                    json_playlist_details = json_load(YOUTUBE_PLAYLIST_DETAILS.format(guid))['items'][0] #Choosen per id hence one single result
      except Exception as e:  Log('[!] json_playlist_details exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_DETAILS.format(guid)))
      else:
        Log.Info('[?] json_playlist_details: {}'.format(json_playlist_details.keys()))
        channel_id       = Dict(json_playlist_details, 'snippet', 'channelId');  Log.Info('[ ] channel_id: "{}"'.format(channel_id))
        metadata.title   = Dict(json_playlist_details, 'snippet', 'title'    );  Log.Info('[ ] title:      "{}"'.format(metadata.title))
        if Dict(json_playlist_details, 'snippet', 'description'):  metadata.summary = Dict(json_playlist_details, 'snippet', 'description');  
        Log.Info('[ ] summary:     "{}"'.format((Dict(json_playlist_details, 'snippet', 'description') or '').replace('\n', '. ')))  #
        metadata.originally_available_at = Datetime.ParseDate(Dict(json_playlist_details, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_playlist_details, 'snippet', 'publishedAt' )))
        thumb            = Dict(json_playlist_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'default', 'url')
        if thumb and thumb not in metadata.posters:  Log('[ ] posters:   {}'.format(thumb));  metadata.posters [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
        else:                                        Log('[X] posters:   {}'.format(thumb))
        
      Log.Info('[?] json_playlist_items')
      try:                    json_playlist_items = json_load(YOUTUBE_PLAYLIST_ITEMS.format(guid)) #Choosen per id hence one single result
      except Exception as e:  Log.Info('[!] json_playlist_items exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_ITEMS.format(guid)))
      else:                   Log.Info('[?] json_playlist_items: {}'.format(json_playlist_items.keys()))
        
    else:  Log.Info('after')
    
    # Loading Channel Details for summary, country, background and role image
    if channel_id.startswith('UC'):
      try:                    json_channel_details = json_load(YOUTUBE_CHANNEL_DETAILS.format(channel_id))['items'][0]  #Choosen per id hence one single result
      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        Log.Info('[?] json_channel_details: {}'.format(json_channel_details.keys()))
        Log.Info('[ ] title:       "{}"'.format(Dict(json_channel_details, 'snippet', 'title'      )))
        if not Dict(json_playlist_details, 'snippet', 'description'):
          if Dict(json_channel_details, 'snippet', 'description'):  metadata.summary =  Dict(json_channel_details, 'snippet', 'description'); 
          elif guid.startswith('PL'):  metadata.summary = 'No Playlist nor Channel summary'
          else:                        metadata.summary = 'No Channel summary'
          Log.Info('[ ] summary:     "{}"'.format(Dict(json_channel_details, 'snippet', 'description').replace('\n', '. ')))  #
        if Dict(json_channel_details,'snippet','country') and Dict(json_channel_details,'snippet','country') not in metadata.countries:
          metadata.countries.add(Dict(json_channel_details,'snippet','country'));  Log.Info('[ ] country: {}'.format(Dict(json_channel_details,'snippet','country') ))
        metadata.roles.clear()
        role       = metadata.roles.new()
        role.role  = Dict(json_channel_details, 'snippet', 'title')
        role.name  = Dict(json_channel_details, 'snippet', 'title')
        role.photo = Dict(json_channel_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_channel_details, 'snippet', 'thumbnails', 'high', 'url')   or Dict(json_channel_details, 'snippet', 'thumbnails', 'default', 'url')  
        Log.Info('[ ] role:        {}'.format(Dict(json_channel_details,'snippet','title')))
        #thumb = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvLowImageUrl' ) or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvMediumImageUrl') \
        #     or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvHighImageUrl') or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvImageUrl'      )
        thumb = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerImageUrl' )
        if thumb and thumb not in metadata.art:  Log('[ ] art:       {}'.format(thumb));  metadata.art [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
        else:                                    Log('[X] art:       {}'.format(thumb))

    # Loading Channel
    if guid.startswith('UC'):
      try:                    json_channel_items = json_load(YOUTUBE_CHANNEL_ITEMS.format(guid))  #Choosen per id hence one single result
      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        Log.Info('json_channel_items: {}'.format(len(Dict(json_channel_items, 'items'))))
        thumb                            = Dict(json_channel_items, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_channel_items, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_channel_items, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_channel_items, 'snippet', 'thumbnails', 'default', 'url')
        if not Dict(json_playlist_details, 'snippet', 'publishedAt'):  metadata.originally_available_at = Datetime.ParseDate(Dict(json_channel_items, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_channel_items, 'snippet', 'publishedAt' )))
        if thumb:                                                      metadata.posters[thumb]          = Proxy.Media(HTTP.Request( thumb ).content, sort_order=1);         Log.Info('[ ] thumb:       '+ thumb)
     
    ### Season + Episode loop ###
    genre_array = {}
    episodes    = 0
    for s in sorted(media.seasons, key=natural_sort_key):
      season = metadata.seasons[s]
      Log.Info("".ljust(157, '='))
      Log.Info('Season: {:>2}'.format(s))
      #season.summary        = 'test'; #                             Log('[ ] summary:   {}'.format(summary.replace('\n', '. ')))
      #season.posters[thumb] = Proxy.Media(poster, sort_order=1);  Log('[ ] thumbnail: {}'.format(thumb))
      
      for e in sorted(media.seasons[s].episodes, key=natural_sort_key):
        filename  = os.path.basename(media.seasons[s].episodes[e].items[0].parts[0].file)
        episode   = metadata.seasons[s].episodes[e]
        episodes += 1
        Log.Info('metadata.seasons[{:>2}].episodes[{:>3}] "{}"'.format(s, e, filename))
        json = Dict(json_playlist_items, 'items') or Dict(json_channel_items, 'items') or {}
        
        for video in Dict(json_playlist_items, 'items') or Dict(json_channel_items, 'items') or {}:
          videoId = Dict(video, 'id', 'videoId') or Dict(video, 'snippet', 'resourceId', 'videoId')
          if videoId and videoId in filename:
            
            # videoId not in Playlist/channel
            thumb = Dict(video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video, 'snippet', 'thumbnails', 'high', 'url') or Dict(video, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video, 'snippet', 'thumbnails', 'default', 'url')
            episode.title                   = Dict(video, 'snippet', 'title'       );                            Log.Info('[ ] title:        {}'.format(Dict(video, 'snippet', 'title'       )))
            episode.summary                 = Dict(video, 'snippet', 'description' );                            Log.Info('[ ] description:  {}'.format(Dict(video, 'snippet', 'description' ).replace('\n', '. ')))
            episode.originally_available_at = Datetime.ParseDate(Dict(video, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(video, 'snippet', 'publishedAt' )))
            episode.thumbs[thumb]           = Proxy.Media(HTTP.Request(thumb).content, sort_order=1);            Log.Info('[ ] thumbnail:    {}'.format(thumb))
            Log.Info('[ ] channelTitle: {}'.format(Dict(video, 'snippet', 'channelTitle')))
            break
        else:

          # videoId not in Playlist/channel item list so loading video_details
          Log.Info('# videoId not in Playlist/channel item list so loading video_details')
          result = YOUTUBE_REGEX_VIDEO.search(filename)
          if result:
            videoId = result.group('id')
            Log.Info(videoId)
            url = YOUTUBE_VIDEO_DETAILS % (videoId)
            try:                    video_details = json_load(url)['items'][0]
            except Exception as e:  Log('Error: "{}"'.format(e))
            else:
              #Log.Info('[?] link:     "https://www.youtube.com/watch?v={}"'.format(videoId))
              rating                          = float(10*int(video_details['statistics']['likeCount'])/(int(video_details['statistics']['dislikeCount'])+int(video_details['statistics']['likeCount'])))
              thumb                           = Dict(video_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'default', 'url')
              poster                          = Dict(video_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'default', 'url')
              episode.title                   = video_details['snippet']['title'];                                                        Log.Info('[ ] title:    "{}"'.format(video_details['snippet']['title'])) 
              episode.summary                 = video_details['snippet']['description'];                                                  Log.Info('[ ] summary:  "{}"'.format(video_details['snippet']['description'].replace('\n', '. ')))
              episode.originally_available_at = Datetime.ParseDate(video_details['snippet']['publishedAt']).date();                       Log.Info('[ ] date:     "{}"'.format(video_details['snippet']['publishedAt']))
              episode.rating                  = rating;                                                                                   Log.Info('[ ] rating:   "{}"'.format(rating))
              episode.thumbs[thumb]           = Proxy.Media(HTTP.Request(poster).content, sort_order=1);                                  Log.Info('[ ] thumbs:   "{}"->"{}"'.format(thumb, poster))
              episode.duration                = ISO8601DurationToSeconds(video_details['contentDetails']['duration'])*1000;               Log.Info('[ ] duration: "{}"->"{}"'.format(video_details['contentDetails']['duration'], metadata.duration))
              #videoId = Dict(video, 'contentDetails', 'videoId')
              if Dict(video_details, 'snippet',  'channelTitle') and Dict(video_details, 'snippet',  'channelTitle') not in [role_obj.name for role_obj in episode.directors]:
                meta_director       = episode.directors.new()
                meta_director.name  = Dict(video_details, 'snippet',  'channelTitle')
              Log.Info('[ ] director: "{}"'.format(Dict(video_details, 'snippet',  'channelTitle')))
              for id  in Dict(video_details, 'snippet', 'categoryId').split(',') or []:  genre_array[YOUTUBE_CATEGORY_ID[id]] = genre_array[YOUTUBE_CATEGORY_ID[id]]+1 if YOUTUBE_CATEGORY_ID[id] in genre_array else 1
              for tag in Dict(video_details, 'snippet', 'tags')                  or []:  genre_array[tag                    ] = genre_array[tag                    ]+1 if tag                     in genre_array else 1
              
            Log.Info('[ ] genres:   "{}"'.format([x for x in metadata.genres]))  #metadata.genres.clear()
            genre_array_cleansed = [id for id in genre_array if genre_array[id]>episodes/2 and id not in metadata.genres]  #Log.Info('[ ] genre_list: {}'.format(genre_list))
            for id in genre_array_cleansed:  metadata.genres.add(id)
          else:
            Log.Info('videoId not found in filename')

  Log(''.ljust(157, '='))

### Agent declaration ##################################################################################################################################################
class YouTubeSeriesAgent(Agent.TV_Shows):
  name, primary_provider, fallback_agent, contributes_to, accepts_from, languages = 'YouTube', True, None, None, ['com.plexapp.agents.localmedia'], [Locale.Language.NoLanguage]
  def search (self, results,  media, lang, manual):  Search (results,  media, lang, manual, False)
  def update (self, metadata, media, lang, force ):  Update (metadata, media, lang, force,  False)

class YouTubeMovieAgentAgent(Agent.Movies):
  name, primary_provider, fallback_agent, contributes_to, accepts_from, languages = 'YouTube', True, None, None, ['com.plexapp.agents.localmedia'], [Locale.Language.NoLanguage]
  def search (self, results,  media, lang, manual):  Search (results,  media, lang, manual, True)
  def update (self, metadata, media, lang, force ):  Update (metadata, media, lang, force,  True)

### Variables ###
YOUTUBE_API_KEY          = 'AIzaSyC2q8yjciNdlYRNdvwbb7NEcDxBkv1Cass'
YOUTUBE_API_KEY2         = Prefs['YouTube-Agent_youtube_api_key']
YOUTUBE_VIDEO_SEARCH     = 'https://content.googleapis.com/youtube/v3/search?q=%s&maxResults=1&part=snippet&key='                                    + YOUTUBE_API_KEY
YOUTUBE_VIDEO_DETAILS    = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key='                          + YOUTUBE_API_KEY
YOUTUBE_PLAYLIST_DETAILS = 'https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id={}&key='                                  + YOUTUBE_API_KEY
YOUTUBE_PLAYLIST_ITEMS   = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={}&key='                       + YOUTUBE_API_KEY
YOUTUBE_CHANNEL_DETAILS  = 'https://www.googleapis.com/youtube/v3/channels?part=snippet%2CcontentDetails%2Cstatistics%2CbrandingSettings&id={}&key=' + YOUTUBE_API_KEY
YOUTUBE_CHANNEL_ITEMS   = 'https://www.googleapis.com/youtube/v3/search?order=date&part=snippet&type=video&channelId={}&maxResults=50&key='          + YOUTUBE_API_KEY
YOUTUBE_REGEX_VIDEO      = Regex('(\\[(youtube-)?|-)(?P<id>[a-z0-9\-_]{11})\\]?',                   Regex.IGNORECASE)
YOUTUBE_REGEX_PLAYLIST   = Regex('\\[(youtube-)?(?P<id>(PL[a-z0-9]{16}|PL[a-z0-9\-_]{32}|UC[a-z0-9\-_]{22}))\\]',  Regex.IGNORECASE)  #.*\[([Yy]ou[Tt]ube-)?PL[a-z0-9\-_]{11}
YOUTUBE_CATEGORY_ID      = {  '1': 'Film & Animation'     ,  '2': 'Autos & Vehicles'     , '10': 'Music'                , '15': 'Pets & Animals',
                             '17': 'Sports',                '18': 'Short Movies',          '19': 'Travel & Events',       '20': 'Gaming',
                             '21': 'Videoblogging',         '22': 'People & Blogs',        '23': 'Comedy',                '24': 'Entertainment',
                             '25': 'News & Politics',       '26': 'Howto & Style',         '27': 'Education',             '28': 'Science & Technology',
                             '29': 'Nonprofits & Activism', '30': 'Movies',                '31': 'Anime/Animation',       '32': 'Action/Adventure',
                             '33': 'Classics',              '34': 'Comedy',                '35': 'Documentary',           '36': 'Drama',
                             '37': 'Family',                '38': 'Foreign',               '39': 'Horror',                '40': 'Sci-Fi/Fantasy',
                             '41': 'Thriller',              '42': 'Shorts',                '43': 'Shows',                 '44': 'Trailers'
                           }
PlexRoot                 = os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "..", "..", "..", ".."))
CachePath                = os.path.join(PlexRoot, "Plug-in Support", "Data", "com.plexapp.agents.hama", "DataItems")
PLEX_LIBRARY_URL         = "http://127.0.0.1:32400/library/sections/"    # Allow to get the library name to get a log per library https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token
PLEX_LIBRARY             = {}

### Plex Library XML ###
Log.Info("Library: "+PlexRoot)  #Log.Info(file)
Log.Info('[YouTube-Agent] API Key: {}'.format(YOUTUBE_API_KEY2)
if os.path.isfile(os.path.join(PlexRoot, "X-Plex-Token.id")):
  Log.Info("'X-Plex-Token.id' file present")
  token_file=Data.Load(os.path.join(PlexRoot, "X-Plex-Token.id"))
  if token_file:  PLEX_LIBRARY_URL += "?X-Plex-Token=" + token_file.strip()  #Log.Info(PLEX_LIBRARY_URL) ##security risk if posting logs with token displayed
try:
  library_xml = etree.fromstring(urllib2.urlopen(PLEX_LIBRARY_URL).read())
  for library in library_xml.iterchildren('Directory'):
    for path in library.iterchildren('Location'):
      PLEX_LIBRARY[path.get("path")] = library.get("title")
      Log.Info( path.get("path") + " = " + library.get("title") )
except Exception as e:  Log.Info("Place correct Plex token in X-Plex-Token.id file in logs folder or in PLEX_LIBRARY_URL variable to have a log per library - https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token" + str(e))
