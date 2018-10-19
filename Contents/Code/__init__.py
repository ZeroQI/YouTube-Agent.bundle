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
import os                   # path.abspath, join, dirname
import re                   #
import inspect              # getfile, currentframe
import urllib2              #
from   lxml    import etree #
from   io      import open  #

### Return dict value if all fields exists "" otherwise (to allow .isdigit()), avoid key errors
def Dict(var, *arg, **kwarg):  #Avoid TypeError: argument of type 'NoneType' is not iterable
  """ Return the value of an (imbricated) dictionnary, return "" if doesn't exist unless "default=new_value" specified as end argument
      Ex: Dict(variable_dict, 'field1', 'field2', default = 0)
  """
  for key in arg:
    if isinstance(var, dict) and key and key in var or isinstance(var, list) and isinstance(key, int) and 0<=key<len(var):  var = var[key]
    else:  return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var

#Based on an answer by John Machin on Stack Overflow http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
def filterInvalidXMLChars(string):
  def isValidXMLChar(char):  c = ord(char);  return 0x20 <= c <= 0xD7FF or 0xE000 <= c <= 0xFFFD or 0x10000 <= c <= 0x10FFFF or c in (0x9, 0xA, 0xD)
  return filter(isValidXMLChar, string)

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
      line = Core.storage.load(filename)  #with open(filename, 'rb') as file:  line=file.read()
      for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(dir.count(os.sep)-1, -1, -1)]:
        if "root: '{}'".format(root) in line:  path = os.path.relpath(dir, root).rstrip('.');  break  #Log.Info('[!] root not found: "{}"'.format(root))
      else: path, root = '_unknown_folder', ''
    else:  Log.Info('[!] ASS root scanner file missing: "{}"'.format(filename))
  return library, root, path

###
def json_load(url):
  iteration = 0
  json_page = {}
  json      = {}
  while not json or Dict(json_page, 'nextPageToken') and Dict(json_page, 'pageInfo', 'resultsPerPage') !=1 and iteration<50:
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

  YOUTUBE_API_KEY   = Prefs['YouTube-Agent_youtube_api_key']
  displayname = os.path.basename(media.items[0].parts[0].file) if movie else media.show
  filename = os.path.basename(media.items[0].parts[0].file) if movie else os.path.splitext(os.path.basename(media.filename))[0]
  dir      = GetMediaDir(media, movie)
  Log(''.ljust(157, '='))
  Log('search() - dir: {}, filename: {}'.format(dir, filename))
  
  array = [('YOUTUBE_REGEX_PLAYLIST', YOUTUBE_REGEX_PLAYLIST), ('YOUTUBE_REGEX_CHANNEL', YOUTUBE_REGEX_CHANNEL), ('YOUTUBE_REGEX_VIDEO', YOUTUBE_REGEX_VIDEO)]
  try:
    for regex, url in array:
      result = url.search(filename)
      if result:
        guid = result.group('id')
        Log.Info('search() - YouTube ID found - regex: {}, youtube ID: "{}"'.format(regex, guid))
        results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(guid,os.path.basename(dir)), name=displayname, year=None, score=100, lang=lang ) )
        return
      else: Log.Info('search() - YouTube ID not found - regex: "{}"'.format(regex))  
    else:        guid = None
  except Exception as e:  guid = None;  Log('search() - filename: "{}" Regex failed to find YouTube id: "{}", error: "{}"'.format(filename, regex, e))
  if not guid:
    Log.Info('no guid found')
    if movie:
      Log.Info(filename)
    else:    
      s = media.seasons.keys()[0] if media.seasons.keys()[0]!='0' else media.seasons.keys()[1] if len(media.seasons.keys()) >1 else None
      if s:
        e      = media.seasons[s].episodes.keys()[0]
        result = YOUTUBE_REGEX_PLAYLIST.search(os.path.basename(os.path.dirname(dir)))
        guid   = result.group('id') if result else ''
        if result or os.path.exists(os.path.join(dir, 'youtube.id')):
          Log('search() - filename: "{}", found season YouTube playlist id, result.group("id"): {}'.format(filename, result.group('id')))
          results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(guid,dir), name=filename, year=None, score=100, lang=lang ) )
          Log(''.ljust(157, '='))
          return
        Log('search() - id not found')
    
    try:
      URL_VIDEO_SEARCH = '{}&q={}&key={}'.format(YOUTUBE_VIDEO_SEARCH, String.Quote(filename, usePlus=False), YOUTUBE_API_KEY)
      video_details = json_load(URL_VIDEO_SEARCH)

      if Dict(video_details, 'pageInfo', 'totalResults'):
        Log.Info('filename: "{}", title:        "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'title')))
        Log.Info('filename: "{}", channelTitle: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle')))
        if filename == Dict(video_details, 'items', 0, 'snippet', 'channelTitle'):
          Log.Info('filename: "{}", found exact matching YouTube title: "{}", description: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(video_details, 'items', 0, 'snippet', 'description')))
          results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(Dict(video_details, 'items', 0, 'id', 'channelId'),dir), name=filename, year=None, score=100, lang=lang ) )
        else:  Log.Info('search() - no id in title nor matching YouTube title: "{}", closest match: "{}", description: "{}"'.format(filename, Dict(video_details, 'items', 0, 'snippet', 'channelTitle'), Dict(video_details, 'items', 0, 'snippet', 'description')))
      elif 'error' in video_details:  Log.Info('search() - code: "{}", message: "{}"'.format(Dict(video_details, 'error', 'code'), Dict(video_details, 'error', 'message')))
    except Exception as e:  Log('search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(filename, e))

    ###
    if not results:
      library, root, path = GetLibraryRootPath(dir)
      Log('Putting folder name "{}" as guid since no assign channel id or playlist id was assigned'.format(path.split(os.sep)[-1]))
      results.Append( MetadataSearchResult( id='youtube|{}|{}'.format(path.split(os.sep)[-2] if os.sep in path else '', dir), name=os.path.basename(filename), year=None, score=80, lang=lang ) )
    Log(''.ljust(157, '='))
  Log(''.ljust(157, '='))

### Download metadata using unique ID ###
def Update(metadata, media, lang, force, movie):

  YOUTUBE_API_KEY   = Prefs['YouTube-Agent_youtube_api_key']

  temp, guid, dir = metadata.id.split("|")
  season_map      = {}
  channelId       = None
  
  if not (len(guid)>2 and guid[0:2] in ('PL', 'UU', 'FL', 'LP', 'RD')):  metadata.title = re.sub(r'\[.*\]', '', dir).strip()  #no id mode, update title so ep gets updated

  ### Movie library and video tag ###
  Log(''.ljust(157, '='))
  Log('update() - guid: {}, dir: {}, metadata.id: {}'.format(guid, dir, metadata.id))
  if movie:

    # YouTube video id given
    if guid and not (len(guid)>2 and guid[0:2] in ('PL', 'UU', 'FL', 'LP', 'RD')):
      try:

        URL_VIDEO_DETAILS = '{}&id={}&key={}'.format(YOUTUBE_VIDEO_DETAILS, guid, YOUTUBE_API_KEY)
        video_details = json_load(URL_VIDEO_DETAILS)['items'][0]

      except:  Log('video_details - Could not retrieve data from YouTube for: '+guid)
      else:
        Log.Info('Movie mode3')
        Log('video_details - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS))
        date                             = Datetime.ParseDate(video_details['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
        metadata.originally_available_at = date.date()
        metadata.title                   = video_details['snippet']['title'];                                           Log('series title:       "{}"'.format(video_details['snippet']['title']))
        metadata.summary                 = video_details['snippet']['description'];                                     Log('series description: '+video_details['snippet']['description'].replace('\n', '. '))
        thumb                            = video_details['snippet']['thumbnails']['default']['url'];                    Log('thumb: "{}"'.format(thumb))
        poster                           = video_details['snippet']['thumbnails']['standard']['url'];                   Log('poster: "{}"'.format(thumb))
        metadata.posters[thumb]          = Proxy.Media(HTTP.Request(poster).content, sort_order=1)
        metadata.duration                = ISO8601DurationToSeconds(video_details['contentDetails']['duration'])*1000;  Log('series duration:    "{}"->"{}"'.format(video_details['contentDetails']['duration'], metadata.duration))
        if Dict(video_details, 'statistics', 'likeCount'):
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
        collection = re.sub(r'\[.*\]', '', reverse_path[-1]).strip()
        Log.Info('[ ] collections:        "{}"'.format(collection))
        if collection not in metadata.collections:  metadata.collections=[collection]
      else:  Log.Info("Grouping folder not found or single folder, root: {}, path: {}, Grouping folder: {}, subdirs: {}, reverse_path: {}".format(root, path, os.path.basename(series_root_folder), subfolder_count, reverse_path))

    #
    channel_id            = guid if guid.startswith('UC') or guid.startswith('HC') else ''
    json                  = {}
    json_playlist_details = {}
    json_playlist_items   = {}
    json_channel_items    = {}
    json_channel_details  = {}
    metadata.studio       = 'YouTube'
    
    # Loading Playlist
    if len(guid)>2 and guid[0:2] in ('PL', 'UU', 'FL', 'LP', 'RD'):

      Log.Info('[?] json_playlist_details')
      try:

        URL_PLAYLIST_DETAILS  = '{}&id={}&key={}'.format(YOUTUBE_PLAYLIST_DETAILS, guid, YOUTUBE_API_KEY)
        json_playlist_details = json_load(URL_PLAYLIST_DETAILS)['items'][0]

      except Exception as e:  Log('[!] json_playlist_details exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_DETAILS.format(guid)))
      else:
        Log.Info('[?] json_playlist_details: {}'.format(json_playlist_details.keys()))
        channel_id       = Dict(json_playlist_details, 'snippet', 'channelId');  Log.Info('[ ] channel_id: "{}"'.format(channel_id))
        metadata.title   = filterInvalidXMLChars(Dict(json_playlist_details, 'snippet', 'title'));  Log.Info('[ ] title:      "{}"'.format(metadata.title))
        if Dict(json_playlist_details, 'snippet', 'description'):  metadata.summary = Dict(json_playlist_details, 'snippet', 'description');
        Log.Info('[ ] summary:     "{}"'.format((Dict(json_playlist_details, 'snippet', 'description') or '').replace('\n', '. ')))  #
        metadata.originally_available_at = Datetime.ParseDate(Dict(json_playlist_details, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_playlist_details, 'snippet', 'publishedAt' )))
        thumb            = Dict(json_playlist_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_playlist_details, 'snippet', 'thumbnails', 'default', 'url')
        if thumb and thumb not in metadata.posters:  Log('[ ] posters:   {}'.format(thumb));  metadata.posters [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1 if Prefs['media_poster_source']=='Episode' else 2)
        else:                                        Log('[X] posters:   {}'.format(thumb))

      Log.Info('[?] json_playlist_items')
      try:

        URL_PLAYLIST_ITEMS  = '{}&playlistId={}&key={}'.format(YOUTUBE_PLAYLIST_ITEMS, guid, YOUTUBE_API_KEY)
        json_playlist_items = json_load(URL_PLAYLIST_ITEMS)

      except Exception as e:  Log.Info('[!] json_playlist_items exception: {}, url: {}'.format(e, YOUTUBE_PLAYLIST_ITEMS.format(guid)))
      else:                   Log.Info('[?] json_playlist_items: {}'.format(json_playlist_items.keys()))

    else:  Log.Info('after')

    # Loading Channel Details for summary, country, background and role image
    if channel_id.startswith('UC') or channel_id.startswith('HC'):
      try:

        URL_CHANNEL_DETAILS   = '{}&id={}&key={}'.format(YOUTUBE_CHANNEL_DETAILS,channel_id, YOUTUBE_API_KEY)
        json_channel_details  = json_load(URL_CHANNEL_DETAILS)['items'][0]

      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        Log.Info('[?] json_channel_details: {}'.format(json_channel_details.keys()))
        Log.Info('[ ] title:       "{}"'.format(Dict(json_channel_details, 'snippet', 'title'      )))
        if not Dict(json_playlist_details, 'snippet', 'description'):
          if Dict(json_channel_details, 'snippet', 'description'):  metadata.summary =  Dict(json_channel_details, 'snippet', 'description');
          #elif guid.startswith('PL'):  metadata.summary = 'No Playlist nor Channel summary'
          else:
            summary  = 'Channel with {} videos, '.format(Dict(json_channel_details, 'statistics', 'videoCount'     ))
            summary += '{} subscribers, '.format(Dict(json_channel_details, 'statistics', 'subscriberCount'))
            summary += '{} views'.format(Dict(json_channel_details, 'statistics', 'viewCount'      ))
            metadata.summary = filterInvalidXMLChars(summary) #or 'No Channel summary'
            Log.Info('[ ] summary:     "{}"'.format(Dict(json_channel_details, 'snippet', 'description').replace('\n', '. ')))  #
        if Dict(json_channel_details,'snippet','country') and Dict(json_channel_details,'snippet','country') not in metadata.countries:
          metadata.countries.add(Dict(json_channel_details,'snippet','country'));  Log.Info('[ ] country: {}'.format(Dict(json_channel_details,'snippet','country') ))
        thumb_channel = Dict(json_channel_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_channel_details, 'snippet', 'thumbnails', 'high', 'url')   or Dict(json_channel_details, 'snippet', 'thumbnails', 'default', 'url')
        metadata.roles.clear()
        role       = metadata.roles.new()
        role.role  = filterInvalidXMLChars(Dict(json_channel_details, 'snippet', 'title'))
        role.name  = filterInvalidXMLChars(Dict(json_channel_details, 'snippet', 'title'))
        role.photo = thumb_channel
        Log.Info('[ ] role:        {}'.format(Dict(json_channel_details,'snippet','title')))
        thumb = Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvLowImageUrl' ) or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvMediumImageUrl') \
             or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvHighImageUrl') or Dict(json_channel_details, 'brandingSettings', 'image', 'bannerTvImageUrl'      )
        if thumb and thumb not in metadata.art:  Log('[X] art:       {}'.format(thumb));  metadata.art [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
        else:                                    Log('[ ] art:       {}'.format(thumb))

        if thumb and thumb not in metadata.banners:  Log('[X] banners:   {}'.format(thumb));  metadata.banners [thumb] = Proxy.Media(HTTP.Request(thumb).content, sort_order=1)
        else:                                        Log('[ ] banners:   {}'.format(thumb))

        if thumb_channel and thumb_channel not in metadata.posters:
          Log('[X] posters:   {}'.format(thumb_channel))
          metadata.posters [thumb_channel] = Proxy.Media(HTTP.Request(thumb_channel).content, sort_order=1 if Prefs['media_poster_source']=='Channel' else 2)
          #metadata.posters.validate_keys([thumb_channel])
        else:                                                        Log('[ ] posters:   {}'.format(thumb_channel))

        #if not Dict(json_playlist_details, 'snippet', 'publishedAt'):  metadata.originally_available_at = Datetime.ParseDate(Dict(json_channel_items, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(json_channel_items, 'snippet', 'publishedAt' )))
    
    ### Season + Episode loop ###
    genre_array = {}
    episodes    = 0
    first       = True
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

        for video in Dict(json_playlist_items, 'items') or {}:
          videoId = Dict(video, 'id', 'videoId') or Dict(video, 'snippet', 'resourceId', 'videoId')
          if videoId and videoId in filename:

            # videoId not in Playlist/channel
            thumb                           = Dict(video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video, 'snippet', 'thumbnails', 'high', 'url') or Dict(video, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video, 'snippet', 'thumbnails', 'default', 'url')
            picture                         = HTTP.Request(thumb).content 
            episode.title                   = filterInvalidXMLChars(Dict(video, 'snippet', 'title'       ));     Log.Info('[ ] title:        {}'.format(Dict(video, 'snippet', 'title'       )))
            episode.summary                 = filterInvalidXMLChars(Dict(video, 'snippet', 'description' ));     Log.Info('[ ] description:  {}'.format(Dict(video, 'snippet', 'description' ).replace('\n', '. ')))
            episode.originally_available_at = Datetime.ParseDate(Dict(video, 'snippet', 'publishedAt')).date();  Log.Info('[ ] publishedAt:  {}'.format(Dict(video, 'snippet', 'publishedAt' )))
            episode.thumbs[thumb]           = Proxy.Media(picture, sort_order=1);                                Log.Info('[ ] thumbnail:    {}'.format(thumb))
            Log.Info('[ ] channelTitle: {}'.format(Dict(video, 'snippet', 'channelTitle')))
            break
        else:

          # videoId not in Playlist/channel item list so loading video_details
          
          result = YOUTUBE_REGEX_VIDEO.search(filename)
          if result:
            videoId = result.group('id')
            Log.Info('# videoId [{}] not in Playlist/channel item list so loading video_details'.format(videoId))
            try:

              url = '{}&id={}&key={}'.format(YOUTUBE_VIDEO_DETAILS, videoId, YOUTUBE_API_KEY)
              video_details = json_load(url)['items'][0]

            except Exception as e:  Log('Error: "{}"'.format(e))
            else:
              #Log.Info('[?] link:     "https://www.youtube.com/watch?v={}"'.format(videoId))
              thumb                           = Dict(video_details, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'high', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video_details, 'snippet', 'thumbnails', 'default', 'url')
              picture                         = HTTP.Request(thumb).content
              if Dict(video_details, 'statistics', 'likeCount'):
                rating                          = float(10*int(video_details['statistics']['likeCount'])/(int(video_details['statistics']['dislikeCount'])+int(video_details['statistics']['likeCount'])))
              episode.title                   = filterInvalidXMLChars(video_details['snippet']['title']);                                 Log.Info('[ ] title:    "{}"'.format(video_details['snippet']['title']))
              episode.summary                 = filterInvalidXMLChars(video_details['snippet']['description']);                           Log.Info('[ ] summary:  "{}"'.format(video_details['snippet']['description'].replace('\n', '. ')))
              episode.originally_available_at = Datetime.ParseDate(video_details['snippet']['publishedAt']).date();                       Log.Info('[ ] date:     "{}"'.format(video_details['snippet']['publishedAt']))
              episode.rating                  = rating;                                                                                   Log.Info('[ ] rating:   "{}"'.format(rating))
              episode.thumbs[thumb]           = Proxy.Media(picture, sort_order=1);                                  Log.Info('[ ] thumbs:   "{}"'.format(thumb))
              episode.thumbs.validate_keys([thumb])
              episode.duration                = ISO8601DurationToSeconds(video_details['contentDetails']['duration'])*1000;               Log.Info('[ ] duration: "{}"->"{}"'.format(video_details['contentDetails']['duration'], metadata.duration))
              #videoId = Dict(video, 'contentDetails', 'videoId')
              if Dict(video_details, 'snippet',  'channelTitle') and Dict(video_details, 'snippet',  'channelTitle') not in [role_obj.name for role_obj in episode.directors]:
                meta_director       = episode.directors.new()
                meta_director.name  = filterInvalidXMLChars(Dict(video_details, 'snippet',  'channelTitle'))
              Log.Info('[ ] director: "{}"'.format(Dict(video_details, 'snippet',  'channelTitle')))
              for id  in Dict(video_details, 'snippet', 'categoryId').split(',') or []:  genre_array[YOUTUBE_CATEGORY_ID[id]] = genre_array[YOUTUBE_CATEGORY_ID[id]]+1 if YOUTUBE_CATEGORY_ID[id] in genre_array else 1
              for tag in Dict(video_details, 'snippet', 'tags')                  or []:  genre_array[tag                    ] = genre_array[tag                    ]+1 if tag                     in genre_array else 1
              if first: 
                first = False
                metadata.posters[thumb] = Proxy.Media(picture, sort_order=1)
                Log.Info('[ ] posters: {}'.format(thumb))
                
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

YOUTUBE_API_BASE_URL        = 'https://www.googleapis.com/youtube/v3/'

YOUTUBE_VIDEO_SEARCH     = YOUTUBE_API_BASE_URL + 'search?&maxResults=1&part=snippet'                                        # &q=string             &key=apikey
YOUTUBE_VIDEO_DETAILS    = YOUTUBE_API_BASE_URL + 'videos?part=snippet,contentDetails,statistics'                            # &id=string            &key=apikey
YOUTUBE_PLAYLIST_DETAILS = YOUTUBE_API_BASE_URL + 'playlists?part=snippet,contentDetails'                                    # &id=string            &key=apikey
YOUTUBE_PLAYLIST_ITEMS   = YOUTUBE_API_BASE_URL + 'playlistItems?part=snippet&maxResults=50'                                 # &playlistId=string    &key=apikey
YOUTUBE_CHANNEL_DETAILS  = YOUTUBE_API_BASE_URL + 'channels?part=snippet%2CcontentDetails%2Cstatistics%2CbrandingSettings'   # &id=string            &key=apikey
YOUTUBE_CHANNEL_ITEMS    = YOUTUBE_API_BASE_URL + 'search?order=date&part=snippet&type=video&maxResults=50'                  # &channelId=string     &key=apikey

YOUTUBE_REGEX_VIDEO      = Regex('\[(?:youtube\-)?(?P<id>[a-z0-9\-_]{11})\]', Regex.IGNORECASE) # https://regex101.com/r/BFKkGc/3/
YOUTUBE_REGEX_PLAYLIST   = Regex('\[(?:youtube\-)?(?P<id>PL[^\[\]]{16}|PL[^\[\]]{32}|UU[^\[\]]{22}|FL[^\[\]]{22}|LP[^\[\]]{22}|RD[^\[\]]{22}|UC[^\[\]]{22}|HC[^\[\]]{22})\]',  Regex.IGNORECASE)  # https://regex101.com/r/37x8wI/2
YOUTUBE_REGEX_CHANNEL    = Regex('\[(?:youtube\-)?(?P<id>UC[a-zA-Z0-9\-_]{22}|HC[a-zA-Z0-9\-_]{22})\]')  # https://regex101.com/r/IKysEd/1
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
