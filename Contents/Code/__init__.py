# -*- coding: utf-8 -*-
#
# To Do
# - series agent code

### Imports ###
import os
import re

YOUTUBE_VIDEO_SEARCH     = 'https://content.googleapis.com/youtube/v3/search?q=%s&maxResults=1&part=snippet&key=%s'
YOUTUBE_VIDEO_DETAILS    = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key=%s'
YOUTUBE_PLAYLIST_DETAILS = 'https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id=%s&key=%s'
YOUTUBE_PLAYLIST_ITEMS   = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&maxResults=50&playlistId=%s&key=%s'
YOUTUBE_API_KEY          = 'AIzaSyC2q8yjciNdlYRNdvwbb7NEcDxBkv1Cass'
YOUTUBE_REGEX_VIDEO      = Regex('\\[(youtube-)?(?P<id>[a-z0-9\-_]{11})\\]', Regex.IGNORECASE)
YOUTUBE_REGEX_PLAYLIST   = Regex('\\[(youtube-)?(?P<id>PL([a-z0-9]{16}|[a-z0-9\-_]{32}))\\]',  Regex.IGNORECASE)  #.*\[([Yy]ou[Tt]ube-)?PL[a-z0-9\-_]{11}
YOUTUBE_CATEGORY_ID      = {  '1': 'Film & Animation'     ,  '2': 'Autos & Vehicles'     , '10': 'Music'                , '15': 'Pets & Animals',
                             '17': 'Sports',                '18': 'Short Movies',          '19': 'Travel & Events',       '20': 'Gaming',
                             '21': 'Videoblogging',         '22': 'People & Blogs',        '23': 'Comedy',                '24': 'Entertainment',
                             '25': 'News & Politics',       '26': 'Howto & Style',         '27': 'Education',             '28': 'Science & Technology',
                             '29': 'Nonprofits & Activism', '30': 'Movies',                '31': 'Anime/Animation',       '32': 'Action/Adventure',
                             '33': 'Classics',              '34': 'Comedy',                '35': 'Documentary',           '36': 'Drama',
                             '37': 'Family',                '38': 'Foreign',               '39': 'Horror',                '40': 'Sci-Fi/Fantasy',
                             '41': 'Thriller',              '42': 'Shorts',                '43': 'Shows',                 '44': 'Trailers'
                           }

### Return dict value if all fields exists "" otherwise (to allow .isdigit()), avoid key errors
def Dict(var, *arg, **kwarg):  #Avoid TypeError: argument of type 'NoneType' is not iterable
  """ Return the value of an (imbricated) dictionnary, return "" if doesn't exist unless "default=new_value" specified as end argument
      Ex: Dict(variable_dict, 'field1', 'field2', default = 0)
  """
  for key in arg:
    if isinstance(var, dict) and key and key in var:  var = var[key]
    else:  return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var

### natural sort function ### avoid 1 10 11...19 2 20...
def natural_sort_key(s):  return [int(text) if text.isdigit() else text for text in re.split(re.compile('([0-9]+)'), str(s).lower())]  # list.sort(key=natural_sort_key) #sorted(list, key=natural_sort_key) - Turn a string into string list of chunks "z23a" -> ["z", 23, "a"]

### Convert ISO8601 Duration format into seconds ###
def ISO8601DurationToSeconds(duration):
  def js_int(value):  return int(''.join([x for x in list(value or '0') if x.isdigit()]))  # js-like parseInt - https://gist.github.com/douglasmiranda/2174255
  match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
  return 3600 * js_int(match[0]) + 60 * js_int(match[1]) + js_int(match[2])
  
def Start():
  HTTP.CacheTime                  = CACHE_1MONTH
  HTTP.Headers['User-Agent'     ] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
  HTTP.Headers['Accept-Language'] = 'en-us'

### Assign unique ID ###
def Search(results, media, lang, manual, movie):
  Log(''.ljust(157, '='))
  filename = media.title if movie else media.show #os.path.splitext(os.path.basename(media.filename))[0]
  
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
        Log(dir)
        Log(os.path.basename(dir))
        if YOUTUBE_REGEX_PLAYLIST.search(os.path.basename(dir)) or os.path.exists(os.path.join(dir, 'youtube.id')):
          Log('search() - filename: "{}", found season YouTube playlist id'.format(filename))
          results.Append( MetadataSearchResult( id=filename, name=filename, year=None, score=100, lang=lang ) )
          Log(''.ljust(157, '='))
          return
    try:
      json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_SEARCH % (String.Quote(filename, usePlus=False), YOUTUBE_API_KEY))  #Prefs['yt_apikey']
      if json_obj['pageInfo']['totalResults']:
        if filename == json_obj['items'][0]['snippet']['title']:   
          Log('search() - filename: "{}", found exact matching YouTube title: "{}", description: "{}"'.format(filename, json_obj['items'][0]['snippet']['description']))
          results.Append( MetadataSearchResult( id='youtube-'+json_obj['items'][0]['id']['videoId'], name=filename, year=None, score=100, lang=lang ) )
        else:  Log('search() - no id in title nor matching YouTube title: "{}", closest match: "{}", description: "{}"'.format(filename, json_obj['items'][0]['snippet']['title'], json_obj['items'][0]['snippet']['description']))
      elif 'error' in json_obj:  Log('search() - code: "{}", message: "{}"'.format(json_obj['error']['code'], json_obj['error']['message']))
    except Exception as e:  Log('search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(filename, e))
Log(''.ljust(157, '='))

### Download metadata using unique ID ###
def Update(metadata, media, lang, force, movie):
  Log(''.ljust(157, '='))
  Log('update() - metadata,id: "{}"'.format(metadata.id))
  guid = metadata.id.replace("youtube-", "") if metadata.id.startswith('youtube-') else ''
  
  json_obj = None
  if guid:
    try:     json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS % (metadata.id, YOUTUBE_API_KEY))['items'][0]
    except:  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
  
  if json_obj:
    Log('update() - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS % (metadata.id, YOUTUBE_API_KEY)))
    #Log('update() - json_obj: "{}"'.format(str(json_obj).replace(', ', '\n')))
    thumb                            = json_obj['snippet']['thumbnails']['default']['url'];     Log('thumb: "{}"'.format(thumb))
    date                             = Datetime.ParseDate(json_obj['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
    metadata.originally_available_at = date.date()
    metadata.title                   = json_obj['snippet']['title'];                                           Log('title: "{}"'.format(json_obj['snippet']['title'])) 
    metadata.summary                 = json_obj['snippet']['description'];                                     Log('description: '+json_obj['snippet']['description'].replace('\n', '. '))
    metadata.duration                = ISO8601DurationToSeconds(json_obj['contentDetails']['duration'])*1000;  Log('duration: "{}"->"{}"'.format(json_obj['contentDetails']['duration'], metadata.duration))
    metadata.posters[thumb]          = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)
    metadata.rating                  = float(10*int(json_obj['statistics']['likeCount'])/(int(json_obj['statistics']['dislikeCount'])+int(json_obj['statistics']['likeCount'])));  Log('rating: {}'.format(metadata.rating))
    metadata.genres                  = [ YOUTUBE_CATEGORY_ID[id] for id in json_obj['snippet']['categoryId'].split(',') ];  Log('genres: '+str([x for x in metadata.genres]))

    #metadata.extras.add(TrailerObject(title = 'Trailer', url = 'https://www.youtube.com/watch?v=D9joM600LKA'))  #'https://www.youtube.com/watch?v='+metadata.id))
    
    if movie:
      metadata.year                    = date.year  #test avoid:  AttributeError: 'TV_Show' object has no attribute named 'year'
    
      # Add YouTube user as director
      if Prefs['add_user_as_director']:
        metadata.directors.clear()
        try:
          meta_director       = metadata.directors.new()
          meta_director.name  = json_obj['snippet']['channelTitle']
          #meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
          #https://www.googleapis.com/youtube/v3/channels?part=snippet&id='+commaSeperatedList+'&fields=items(id%2Csnippet%2Fthumbnails)
          #https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}
          Log('director: '+json_obj['snippet']['channelTitle'])
        except:  pass
  
  if not movie:  #TV series Library
    
    # Building season map to playlist id
    season_map={}
    if guid:  # Youtube ID given on Series so single season playlist
      season_map ['1'] = guid
      try:     json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_DETAILS % (guid, YOUTUBE_API_KEY))['items'][0]  #Choosen per id hence one single result
      except:  json_obj = None;  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
      if json_obj:
        #Log('update() - json obj: {}'.format(json_obj))
        metadata.title                   =                    json_obj['snippet']['title'      ].rstrip(' Playlist');  Log('update() - series - title:       '+ json_obj['snippet']['title'])
        metadata.summary                 =                    json_obj['snippet']['description'];                      Log('update() - series - summary:     '+json_obj['snippet']['description'].replace('\n', '. '))
        metadata.originally_available_at = Datetime.ParseDate(json_obj['snippet']['publishedAt']).date();              Log('update() - series - publishedAt: '+ json_obj['snippet']['publishedAt'])
        metadata.posters[json_obj['snippet']['thumbnails']['default']['url']] = Proxy.Preview(HTTP.Request( json_obj['snippet']['thumbnails']['standard']['url'] ).content, sort_order=1)
        #metadata.duration                = ISO8601DurationToSeconds(json_obj['contentDetails']['duration'])*1000;  Log('duration: "{}"->"{}"'.format(json_obj['contentDetails']['duration'], metadata.duration))
        #metadata.rating                  = float(10*int(json_obj['statistics']['likeCount'])/(int(json_obj['statistics']['dislikeCount'])+int(json_obj['statistics']['likeCount'])));  Log('rating: {}'.format(metadata.rating))
        #metadata.genres                  = [ YOUTUBE_CATEGORY_ID[id] for id in json_obj['snippet']['categoryId'].split(',') ];  Log('genres: '+str([x for x in metadata.genres]))

    else:  #Season playlist mode
      metadata.title = metadata.id
      for season in sorted(media.seasons, key=natural_sort_key):
        for episode in sorted(media.seasons[season].episodes, key=natural_sort_key):
          full_dir = os.path.dirname(media.seasons[season].episodes[episode].items[0].parts[0].file)
          dir      = os.path.basename(full_dir)
          result = YOUTUBE_REGEX_PLAYLIST.search(dir)
          if result: season_map [season] = result.group('id')
          elif os.path.isfile(os.path.join(dir, 'youtube.id')):
            with open(os.path.join(full_dir, 'youtube.id'), 'r') as guid_file:
              season_map [season] = guid_file.read().strip()
              Log.info('Forced ID file: "youtube.id" for season {:>2} with id "{}" in seasons folder'.format(season, season_map[season]))
          break
    
    ### Seasons loop ###
    for season in season_map:
      guid = season_map [season]
      if not guid.startswith('PL'):  continue
      
      ### Seasons ###
      try:     json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_DETAILS % (guid, YOUTUBE_API_KEY))['items'][0]  #Choosen per id hence one single result
      except:  json_obj = None;  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
      if json_obj:
        #Log('update() - json obj: {}'.format(json_obj))
        Log('update() - series - Season {} summary: '.format(season, json_obj['snippet']['description'].replace('\n', '. ')))
        metadata.seasons[season].summary                                                      = json_obj['snippet']['description']
        metadata.seasons[season].posters[json_obj['snippet']['thumbnails']['standard']['url']] = Proxy.Preview(HTTP.Request( json_obj['snippet']['thumbnails']['standard']['url'] ).content, sort_order=1)
        #metadata.seasons[season].art
        #channelTitle = json_obj['snippet']['channelTitle']
        
      ### Episodes ###
      try:     json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_ITEMS % (guid, YOUTUBE_API_KEY))
      except:  json_obj = None;  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
      if json_obj:
        #Log('update() - json obj: {}'.format(json_obj))
        Log('update() - totalResults:   {}'.format(json_obj['pageInfo']['totalResults']))
        Log('update() - resultsPerPage: {}'.format(+json_obj['pageInfo']['resultsPerPage']))
        
        playlist = json_obj['items']
        rank     = 0
        for video in playlist:
          rank=rank+1
          if '1' not in media.seasons or str(rank) not in media.seasons['1'].episodes:  Log('episode not present: '+str(rank));  continue
          episode = metadata.seasons[season].episodes[str(rank)]
         
          Log('update() - Episode: {:>3} videoId: https://www.youtube.com/watch?v={}'.format(rank, video['contentDetails']['videoId']))
          #episode.originally_available_at = Datetime.ParseDate(video['contentDetails']['videoPublishedAt']).date();  Log('update() - publishedAt:      '+video['contentDetails']['videoPublishedAt'])
          episode.originally_available_at = Datetime.ParseDate(video['snippet']['publishedAt']).date();  Log('update() - publishedAt: '+video['snippet'       ]['publishedAt'])
          episode.title                   = video['snippet'       ]['title'      ];  Log('update() - title:       '.format(video['snippet'       ]['title'      ]))
          episode.summary                 = video['snippet'       ]['description'];  Log('update() - summary:     '.format(video['snippet'       ]['description'].replace('\n', '. ')))
          episode.thumbs [ video['snippet']['thumbnails' ]['standard' ]['url'] ] = Proxy.Preview(video['snippet']['thumbnails' ]['standard']['url'], sort_order=1) 
          Log('update() - summary:     '+video['snippet']['thumbnails' ]['default' ]['url'])
          Log('update() - summary:     '+video['snippet']['thumbnails' ]['standard' ]['url'])
          
          if Prefs['add_user_as_director']:
            episode.directors.clear()
            try:
              meta_director       = metadata.directors.new()
              meta_director.name  = json_obj['snippet']['channelTitle'];  Log('director: '+json_obj['snippet']['channelTitle'])
              #meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
              #https://www.googleapis.com/youtube/v3/channels?part=snippet&id='+commaSeperatedList+'&fields=items(id%2Csnippet%2Fthumbnails)
              #https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}
            except:  pass
          
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
