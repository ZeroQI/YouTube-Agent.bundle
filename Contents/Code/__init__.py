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
YOUTUBE_CHANNEL_DETAILS  = 'https://www.googleapis.com/youtube/v3/channels?part=snippet%2CcontentDetails%2Cstatistics&id={}&key={}'
YOUTUBE_API_KEY          = 'AIzaSyC2q8yjciNdlYRNdvwbb7NEcDxBkv1Cass'
YOUTUBE_REGEX_VIDEO      = Regex('\\[(youtube-)?(?P<id>[a-z0-9\-_]{11})\\]',                   Regex.IGNORECASE)
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
        result = YOUTUBE_REGEX_PLAYLIST.search(os.path.basename(dir))
        guid   = result.group('id') if result else ''
        if result or os.path.exists(os.path.join(dir, 'youtube.id')):
          Log('search() - filename: "{}", found season YouTube playlist id, result.group("id"): {}'.format(filename, result.group('id')))
          results.Append( MetadataSearchResult( id='youtube-'+guid, name=filename, year=None, score=100, lang=lang ) )
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
  season_map = {}
  channelId  = None
    
  ### Movie library and video tag ###
  if movie:

    # YouTube video id given
    if guid and not guid.startswith('PL'):
      try:     json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS % (guid, YOUTUBE_API_KEY))['items'][0]
      except:  Log('update() - Could not retrieve data from YouTube for: %s' % guid)
      else:
        Log('update() - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS % (guid, YOUTUBE_API_KEY)))
        date                             = Datetime.ParseDate(json_obj['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
        metadata.originally_available_at = date.date()
        metadata.title                   = json_obj['snippet']['title'];                                           Log('series title:       "{}"'.format(json_obj['snippet']['title'])) 
        metadata.summary                 = json_obj['snippet']['description'];                                     Log('series description: '+json_obj['snippet']['description'].replace('\n', '. '))
        thumb                            = json_obj['snippet']['thumbnails']['default']['url'];                    Log('thumb: "{}"'.format(thumb))
        poster                           = json_obj['snippet']['thumbnails']['standard']['url'];                   Log('poster: "{}"'.format(thumb))
        metadata.posters[thumb]          = Proxy.Preview(HTTP.Request(poster).content, sort_order=1)
        metadata.duration                = ISO8601DurationToSeconds(json_obj['contentDetails']['duration'])*1000;  Log('series duration:    "{}"->"{}"'.format(json_obj['contentDetails']['duration'], metadata.duration))
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
              Log('director: '+json_obj['snippet']['channelTitle'])
            except:  pass
  
  ### TV series Library ###
  else: 
    
    # Building season map to playlist id
    if guid:  # Youtube ID given on Series so single season playlist
      season_map ['1'] = guid
      try:                    json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_DETAILS % (guid, YOUTUBE_API_KEY))['items'][0]  #Choosen per id hence one single result
      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        
        ### Series info if PL id in series folder name
        #Log('update() - json obj: {}'.format(json_obj))
        image = HTTP.Request( json_obj['snippet']['thumbnails']['standard']['url'] ).content
        metadata.posters[json_obj['snippet']['thumbnails']['standard']['url']] = Proxy.Preview(image, sort_order=1)
        metadata.title                   =                    json_obj['snippet']['title'      ].rstrip(' Playlist');  Log('update() - series - title:       '+ json_obj['snippet']['title'])
        metadata.summary                 =                    json_obj['snippet']['description'];                      Log('update() - series - summary:     '+json_obj['snippet']['description'].replace('\n', '. '))
        metadata.originally_available_at = Datetime.ParseDate(json_obj['snippet']['publishedAt']).date();              Log('update() - series - publishedAt: '+ json_obj['snippet']['publishedAt'])
        metadata.studio                  = 'YouTube';                                                                  Log('update() - series - studio:      YouTube')

        # Adding as role to show channel in series page with pic
        try:                    json_obj2 = JSON.ObjectFromURL(YOUTUBE_CHANNEL_DETAILS.format(Dict(json_obj, 'snippet', 'channelId'), YOUTUBE_API_KEY))['items'][0]  #Choosen per id hence one single result
        except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
        else:
          metadata.roles.clear()
          role       = metadata.roles.new()
          role.role  = Dict(json_obj,'snippet','channelTitle')
          role.name  = Dict(json_obj,'snippet','channelTitle')
          role.photo = Dict(json_obj2,'snippet', 'thumbnails', 'medium', 'url')  
          Log.Info('[ ] role: {}'.format(Dict(json_obj,'snippet','channelTitle')))
          if Dict(json_obj,'snippet','country') and Dict(json_obj,'snippet','country') not in metadata.countries:  metadata.countries.add(Dict(json_obj,'snippet','country'));  Log.Info('[ ] country: {}'.format(Dict(json_obj,'snippet','country') ))
                
      #Season playlist mode:
      for season in sorted(media.seasons, key=natural_sort_key):
        for episode in sorted(media.seasons[season].episodes, key=natural_sort_key):
          full_dir = os.path.dirname(media.seasons[season].episodes[episode].items[0].parts[0].file)
          dir      = os.path.basename(full_dir)
          result   = YOUTUBE_REGEX_PLAYLIST.search(dir)
          if result: season_map [season] = result.group('id')
          elif os.path.isfile(os.path.join(dir, 'youtube.id')):
            with open(os.path.join(full_dir, 'youtube.id'), 'r') as guid_file:  
              season_map [season] = guid_file.read().strip()
              Log.Info('Forced ID file: youtube.id for season {:>2} with id {} in seasons folder'.format(season, season_map[season]))
          break
    
    ### Seasons loop ###
    for season in season_map:
      guid = season_map [season]
      if not guid.startswith('PL'):  continue
      
      ### Seasons ###
      genre_array  = {}
      try:                    json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_DETAILS % (guid, YOUTUBE_API_KEY))['items'][0]  #Choosen per id hence one single result
      except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
      else:
        json_test = JSON.ObjectFromURL('https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&id={}&key={}'.format(guid, YOUTUBE_API_KEY))
        if Dict(json_test, 'url'):  Log(json_test['url'])
        else:                       Log('no custom banner')
        title   = json_obj['snippet']['title'      ]
        summary = json_obj['snippet']['description']
        thumb   = Dict(json_obj, 'snippet', 'thumbnails', 'standard', 'url') or Dict(json_obj, 'snippet', 'thumbnails', 'high', 'url') or Dict(json_obj, 'snippet', 'thumbnails', 'medium', 'url') or Dict(json_obj, 'snippet', 'thumbnails', 'default', 'url')
        poster  = HTTP.Request( thumb ).content
        #metadata.seasons[season].art
        #channelTitle = json_obj['snippet']['channelTitle']
        
        ### Episodes ###
        try:                    json_obj = JSON.ObjectFromURL(YOUTUBE_PLAYLIST_ITEMS % (guid, YOUTUBE_API_KEY))
        except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
        else:
          
          # Do a list of all episodes present on disk only, allow to count them and group all access in logs
          playlist, playlist_details, playlist_thumbs, rank = {}, {}, {}, 0
          for video in json_obj['items']:
            rank+=1
            if str(rank) in media.seasons[season].episodes:
              playlist[str(rank)]=video
              try:                    playlist_details[str(rank)] = Dict(JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS % (Dict(video, 'contentDetails', 'videoId'), YOUTUBE_API_KEY)), 'items')[0]
              except Exception as e:  Log('exception: {}, url: {}'.format(e, guid))
              else:
                link = Dict(video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video, 'snippet', 'thumbnails', 'high', 'url') or Dict(video, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video, 'snippet', 'thumbnails', 'default', 'url')
                playlist_thumbs[str(rank)] = (link, Proxy.Preview(HTTP.Request(link).content)) 
            
          # Loop through list
          Log.Info("".ljust(157, '='))
          Log.Info('Season: {:>2} - totalResults:   {}, resultsPerPage: {}, Json: {}'.format(season, json_obj['pageInfo']['totalResults'], json_obj['pageInfo']['resultsPerPage'], YOUTUBE_PLAYLIST_DETAILS % (guid, YOUTUBE_API_KEY)))
          metadata.seasons[season].title          = title;                                Log('[ ] title:     {}'.format(title))
          metadata.seasons[season].summary        = summary;                              Log('[ ] summary:   {}'.format(summary.replace('\n', '. ')))
          metadata.seasons[season].posters[thumb] = Proxy.Preview(poster, sort_order=1);  Log('[ ] thumbnail: {}'.format(thumb))
          for rank in sorted(playlist, key=natural_sort_key):
            episode = metadata.seasons[season].episodes[rank]
            video   = playlist[rank]
            videoId = Dict(video, 'contentDetails', 'videoId')
            thumb   = Dict(video, 'snippet', 'thumbnails', 'standard', 'url') or Dict(video, 'snippet', 'thumbnails', 'high', 'url') or Dict(video, 'snippet', 'thumbnails', 'medium', 'url') or Dict(video, 'snippet', 'thumbnails', 'default', 'url')
            Log.Info("".ljust(157, '-'))
            Log('Seasons[{:>2}].episodes[{:>3}] Video: https://www.youtube.com/watch?v={}, Json: {}'.format(season, rank, videoId, YOUTUBE_VIDEO_DETAILS % (Dict(video, 'contentDetails', 'videoId'), YOUTUBE_API_KEY)))
            #episode.originally_available_at = Datetime.ParseDate(video['contentDetails']['videoPublishedAt']).date();  Log('update() - publishedAt:      '+video['contentDetails']['videoPublishedAt'])
            episode.title                            = video['snippet']['title'      ];                             Log('[ ] title:       {}'.format(video['snippet'       ]['title'      ]))
            episode.summary                          = video['snippet']['description'];                             Log('[ ] summary:     {}'.format(video['snippet'       ]['description'].replace('\n', '. ').replace('\r', '. ')))
            episode.originally_available_at          = Datetime.ParseDate(video['snippet']['publishedAt']).date();  Log('[ ] publishedAt: {}'.format(video['snippet'       ]['publishedAt']))
            episode.thumbs[playlist_thumbs[rank][0]] = Proxy.Preview(playlist_thumbs[rank][1], sort_order=1);       Log('[ ] thumbnail:   {}'.format(playlist_thumbs[rank][0]))
            
            if Dict(playlist_details, rank):
              #Log.Info('playlist_details: {}'.format(playlist_details[rank]))
              episode.duration = ISO8601DurationToSeconds(playlist_details[rank]['contentDetails']['duration'])*1000
              Log('[ ] duration:    "{}"->"{}"'.format(playlist_details[rank]['contentDetails']['duration'], episode.duration))
              episode.rating   = float(10*int(playlist_details[rank]['statistics']['likeCount'])/(int(playlist_details[rank]['statistics']['dislikeCount'])+int(playlist_details[rank]['statistics']['likeCount'])))
              Log('[ ] rating:      {}'.format(episode.rating))
              Log.Info('[ ] director:    {}'.format(Dict(playlist_details, rank, 'snippet',  'channelTitle')))
              #channel = Dict(playlist_details, rank, 'snippet',  'channelTitle')
              if Dict(playlist_details, rank, 'snippet',  'channelTitle') and Dict(playlist_details, rank, 'snippet',  'channelTitle') not in episode.directors:
                meta_director       = episode.directors.new()
                meta_director.name  = Dict(playlist_details, rank, 'snippet',  'channelTitle')
                #meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
              for id  in Dict(playlist_details, rank, 'snippet', 'categoryId').split(',') or []:  genre_array[YOUTUBE_CATEGORY_ID[id]] = genre_array[YOUTUBE_CATEGORY_ID[id]]+1 if YOUTUBE_CATEGORY_ID[id] in genre_array else 1
              for tag in Dict(playlist_details, rank, 'snippet', 'tags')                  or []:  genre_array[tag                    ] = genre_array[tag                    ]+1 if tag                     in genre_array else 1
              #Log.Info('[ ] genre_array: {}'.format(genre_array))
              
          genre_list = [id for id in genre_array if genre_array[id]>len(playlist)/2 and id not in metadata.genres]
          #Log.Info('[ ] genre_list: {}'.format(genre_list))
          if genre_list:
            metadata.genres.clear()
            for id in genre_array:
              if genre_array[id]>len(playlist)/2 and id not in metadata.genres:  metadata.genres.add(id)
              
          channel = Dict(json_obj, 'snippet', 'channelTitle')
          if channel:
            Log('director: '+Dict(json_obj, 'snippet', 'channelTitle'))
            meta_director       = metadata.directors.new()
            meta_director.name  = json_obj['snippet']['channelTitle']
            #meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
            
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
