import os
import re

YOUTUBE_VIDEO_DETAILS = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key=%s'
YOUTUBE_VIDEO_SEARCH  = 'https://content.googleapis.com/youtube/v3/search?q=%s&maxResults=1&part=snippet&key=%s'
RE_YT_ID              = Regex('[a-z0-9\-_]{11}', Regex.IGNORECASE)
API_KEY               = 'AIzaSyC2q8yjciNdlYRNdvwbb7NEcDxBkv1Cass'
YOUTUBE_CATEGORY_ID   = {  '1': 'Film & Animation'     ,  '2': 'Autos & Vehicles'     , '10': 'Music'                , '15': 'Pets & Animals',
                          '17': 'Sports',                '18': 'Short Movies',          '19': 'Travel & Events',       '20': 'Gaming',
                          '21': 'Videoblogging',         '22': 'People & Blogs',        '23': 'Comedy',                '24': 'Entertainment',
                          '25': 'News & Politics',       '26': 'Howto & Style',         '27': 'Education',             '28': 'Science & Technology',
                          '29': 'Nonprofits & Activism', '30': 'Movies',                '31': 'Anime/Animation',       '32': 'Action/Adventure',
                          '33': 'Classics',              '34': 'Comedy',                '35': 'Documentary',           '36': 'Drama',
                          '37': 'Family',                '38': 'Foreign',               '39': 'Horror',                '40': 'Sci-Fi/Fantasy',
                          '41': 'Thriller',              '42': 'Shorts',                '43': 'Shows',                 '44': 'Trailers'
}

def ISO8601DurationToSeconds(duration):
  def js_int(value):  return int(''.join([x for x in list(value or '0') if x.isdigit()]))  # js-like parseInt - https://gist.github.com/douglasmiranda/2174255
  match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
  return 3600 * js_int(match[0]) + 60 * js_int(match[1]) + js_int(match[2])
  
def Start():
  HTTP.CacheTime                  = CACHE_1MONTH
  HTTP.Headers['User-Agent'     ] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
  HTTP.Headers['Accept-Language'] = 'en-us'

class YouTubeAgent(Agent.Movies):
  name             = 'YouTube'
  languages        = [Locale.Language.NoLanguage]
  primary_provider = True
  accepts_from     = ['com.plexapp.agents.localmedia']

  def search(self, results, media, lang):
    filename = os.path.splitext(os.path.basename(String.Unquote(media.filename)))[0]
    Log(''.ljust(157, '='))
    Log('search() - filename: "{}"'.format(filename))
    if Prefs['yt_pattern']:
      try:     yt_id = Regex(Prefs['yt_pattern']).search(filename).group('id')
      except:  yt_id = None;  Log('search() - Regex failed: "{}", Filename: "{}"'.format(Prefs['yt_pattern'], filename))

      if yt_id and RE_YT_ID.search(yt_id):
        Log('search() - found youtube ID in title: "{}"'.format(yt_id))
        results.Append( MetadataSearchResult( id=yt_id,  name=media.name, year=None, score=100, lang=lang ) )
      else:
        try:
          json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_SEARCH % (String.Quote(media.name, usePlus=False), API_KEY))  #Prefs['yt_apikey']
          if json_obj['pageInfo']['totalResults']:
            if filename == json_obj['items'][0]['snippet']['title']:   
              Log('search() - found matching title: "{}", description: "{}"'.format(json_obj['items'][0]['snippet']['title'], json_obj['items'][0]['snippet']['description']))
              results.Append( MetadataSearchResult( id=json_obj['items'][0]['id']['videoId'], name=filename, year=None, score=100, lang=lang ) )
            else:  Log('search() - found unmatching title: "{}", description: "{}"'.format(json_obj['items'][0]['snippet']['title'], json_obj['items'][0]['snippet']['description']))
          elif 'error' in json_obj:  Log('search() - code: "{}", message: "{}"'.format(json_obj['error']['code'], json_obj['error']['message']))
        except Exception as e:  Log('search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(filename, e))
    Log(''.ljust(157, '='))
  
  def update(self, metadata, media, lang):
    Log(''.ljust(157, '='))
    Log('update() - metadata,id: "{}"'.format(metadata.id))
    
    try:     json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS % (metadata.id, API_KEY))['items'][0]
    except:  json_obj = None;  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
    
    if json_obj:
      Log('update() - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS % (metadata.id, API_KEY)))
      #Log('update() - json_obj: "{}"'.format(str(json_obj).replace(', ', '\n')))
      thumb                            = json_obj['snippet']['thumbnails']['default']['url'];     Log('thumb: "{}"'.format(thumb))
      date                             = Datetime.ParseDate(json_obj['snippet']['publishedAt']);  Log('date:  "{}"'.format(date))
      metadata.originally_available_at = date.date()
      metadata.year                    = date.year
      metadata.title                   = json_obj['snippet']['title'];                                           Log('title: "{}"'.format(json_obj['snippet']['title'])) 
      metadata.summary                 = json_obj['snippet']['description'];                                     Log('description: '+json_obj['snippet']['description'].replace('\n', '. '))
      metadata.duration                = ISO8601DurationToSeconds(json_obj['contentDetails']['duration'])*1000;  Log('duration: "{}"->"{}"'.format(json_obj['contentDetails']['duration'], metadata.duration))
      metadata.posters[thumb]          = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)
      metadata.rating                  = float(10*int(json_obj['statistics']['likeCount'])/(int(json_obj['statistics']['dislikeCount'])+int(json_obj['statistics']['likeCount'])));  Log('rating: {}'.format(metadata.rating))
      metadata.genres                  = [ YOUTUBE_CATEGORY_ID[id] for id in json_obj['snippet']['categoryId'].split(',') ];  Log('genres: '+str([x for x in metadata.genres]))

      
      # Add YouTube user as director
      metadata.directors.clear()
      if Prefs['add_user_as_director']:
        try:
          meta_director       = metadata.directors.new()
          meta_director.name  = json_obj['snippet']['channelTitle']
          #meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
          Log('director: '+json_obj['snippet']['channelTitle'])
        except:  pass
    Log(''.ljust(157, '='))
