YOUTUBE_VIDEO_DETAILS = 'https://m.youtube.com/watch?ajax=1&v=%s'
RE_YT_ID = Regex('[a-z0-9\-_]{11}', Regex.IGNORECASE)

def Start():

	HTTP.CacheTime = CACHE_1MONTH
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.54'
	HTTP.Headers['Accept-Language'] = 'en-us'

class YouTubeAgent(Agent.Movies):

	name = 'YouTube'
	languages = [Locale.Language.NoLanguage]
	primary_provider = True
	accepts_from = ['com.plexapp.agents.localmedia']

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
			json = HTTP.Request(YOUTUBE_VIDEO_DETAILS % metadata.id).content[4:]
			json_obj = JSON.ObjectFromString(json)['content']['video']
		except:
			Log('Could not retrieve data from YouTube for: %s' % metadata.id)
			json_obj = None

		if json_obj:
			metadata.title = json_obj['title']
			metadata.studio = json_obj['public_name']
			metadata.summary = json_obj['description']
			metadata.duration = json_obj['length_seconds'] * 1000

			date = Datetime.ParseDate(json_obj['time_created_text'])
			metadata.originally_available_at = date.date()
			metadata.year = date.year

			thumb = json_obj['thumbnail_for_watch']
			metadata.posters[thumb] = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)
