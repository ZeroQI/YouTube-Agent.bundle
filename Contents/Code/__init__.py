YOUTUBE_VIDEO_DETAILS = 'http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc'
RE_YT_ID = Regex('[a-z0-9\-_]{11}', Regex.IGNORECASE)

def Start():
	HTTP.CacheTime = CACHE_1MONTH
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36'

class YouTubeAgent(Agent.Movies):
	name = 'YouTube'
	languages = [Locale.Language.NoLanguage]
	primary_provider = True

	def search(self, results, media, lang):
		filename = String.Unquote(media.filename)

		if Prefs['yt_pattern'] != '':
			try:
				yt_id = Regex(Prefs['yt_pattern']).search(filename).group('id')
			except:
				Log('Regex failed: %s\nFilename: %s' % (Prefs['yt_pattern'], filename))
				yt_id = None

			if yt_id and RE_YT_ID.search(yt_id):
				results.Append(
					MetadataSearchResult(
						id = yt_id,
						name = media.name,
						year = None,
						score = 99,
						lang = lang
					)
				)

	def update(self, metadata, media, lang):
		try:
			json_obj = JSON.ObjectFromURL(YOUTUBE_VIDEO_DETAILS % metadata.id)['data']
		except:
			Log('Could not retrieve data from YouTube API for: %s' % metadata.id)
			json_obj = None

		if json_obj:
			metadata.title = json_obj['title']
			metadata.studio = json_obj['uploader']
                        metadata.rating = json_obj['rating'] * 2
			metadata.summary = json_obj['description']
			metadata.duration = json_obj['duration'] * 1000
			metadata.originally_available_at = Datetime.ParseDate(json_obj['uploaded']).date()

			thumb = None
			if 'hqDefault' in json_obj['thumbnail']:
				thumb = json_obj['thumbnail']['hqDefault']
			elif 'sqDefault' in json_obj['thumbnail']:
				thumb = json_obj['thumbnail']['sqDefault']

			if thumb:
				poster = HTTP.Request(thumb)
				metadata.posters[thumb] = Proxy.Preview(poster, sort_order=1)
