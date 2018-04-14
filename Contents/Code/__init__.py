import os

YOUTUBE_VIDEO_DETAILS = 'https://m.youtube.com/watch?ajax=1&v=%s'
YOUTUBE_VIDEO_SEARCH  = 'https://content.googleapis.com/youtube/v3/search?q=%s&maxResults=1&part=snippet&key=%s'
RE_YT_ID              = Regex('[a-z0-9\-_]{11}', Regex.IGNORECASE)

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
    if Prefs['yt_pattern'] != '':
      try:     yt_id = Regex(Prefs['yt_pattern']).search(filename).group('id')
      except:  yt_id = None;  Log('search() - Regex failed: "{}", Filename: "{}"'.format(Prefs['yt_pattern'], filename))

      if yt_id and RE_YT_ID.search(yt_id):
        Log('search() - found youtube ID in title: "{}"'.format(yt_id))
        results.Append( MetadataSearchResult( id=yt_id,  name=media.name, year=None, score=99, lang=lang ) )
      else:
        try:
          json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_SEARCH % (String.Quote(media.name, usePlus=False), Prefs['yt_apikey']))
          if json_obj['pageInfo']['totalResults']:
            if filename == json_obj['items'][0]['snippet']['title']:   
              Log('search() - found matching title: "{}", description: "{}"'.format(json_obj['items'][0]['snippet']['title'], json_obj['items'][0]['snippet']['description']))
              results.Append( MetadataSearchResult( id=json_obj['items'][0]['id']['videoId'], name=media.name, year=None, score=99, lang=lang ) )
            else:  Log('search() - found unmatching title: "{}", description: "{}"'.format(json_obj['items'][0]['snippet']['title'], json_obj['items'][0]['snippet']['description']))
          elif 'error' in json_obj:  Log('search() - code: "{}", message: "{}"'.format(json_obj['error']['code'], json_obj['error']['message']))
        except Exception as e:  Log('search() - Could not retrieve data from YouTube for: "{}", Exception: "{}"'.format(String.Unquote(media.filename), e))
    Log(''.ljust(157, '='))
  
  def update(self, metadata, media, lang):
    Log(''.ljust(157, '='))
    Log('update() - metadata,id: "{}"'.format(metadata.id))
  
    try:     json_obj = JSON.ObjectFromString( HTTP.Request(YOUTUBE_VIDEO_DETAILS % metadata.id).content[4:] )['content']
    except:  json_obj = None;  Log('update() - Could not retrieve data from YouTube for: %s' % metadata.id)
    
    if json_obj:
      Log('update() - Loaded video details from: "{}"'.format(YOUTUBE_VIDEO_DETAILS % metadata.id))
      #Log('update() - json_obj: "{}"'.format(str(json_obj).replace(', ', '\n')))
      date                             = Datetime.ParseDate(json_obj['video_main_content']['contents'][0]['date_text']['runs'][0]['text'].split('on ')[-1])
      thumb                            = 'https://%s' % (json_obj['video']['thumbnail_for_watch'].split('//')[-1])
      metadata.originally_available_at = date.date()
      metadata.year                    = date.year
      metadata.title                   = json_obj['video']['title']
      metadata.duration                = json_obj['video']['length_seconds'] * 1000
      metadata.posters[thumb]          = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)
      #if not json_obj['video']['channelTitle'] in metadata.collection:  metadata.collection.append(json_obj['video']['channelTitle'])
      #keywords, view_count, is_watched
      #ArianaGrandeVevo: runs author public_name
      # Summary
      try:                metadata.summary = json_obj['video_main_content']['contents'][0]['description']['runs'][0]['text']
      except IndexError:  Log('update() - No Summary for: "{}"'.format(metadata.id))
      
      # Add YouTube user as director
      metadata.directors.clear()
      if Prefs['add_user_as_director']:
        try:
          meta_director       = metadata.directors.new()
          meta_director.name  = json_obj['video_main_content']['contents'][0]['short_byline_text']['runs'][0]['text']
          meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail'        ]['url' ].replace('/s88-', '/s512-')
        except:  pass
    Log(''.ljust(157, '='))
