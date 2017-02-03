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
			json_obj = JSON.ObjectFromString(json)['content']
		except:
			Log('Could not retrieve data from YouTube for: %s' % metadata.id)
			json_obj = None

		if json_obj:

			metadata.title = json_obj['video']['title']
			metadata.duration = json_obj['video']['length_seconds'] * 1000

			thumb = 'https://%s' % (json_obj['video']['thumbnail_for_watch'].split('//')[-1])
			metadata.posters[thumb] = Proxy.Preview(HTTP.Request(thumb).content, sort_order=1)

			metadata.summary = json_obj['video_main_content']['contents'][0]['description']['runs'][0]['text']

			date = Datetime.ParseDate(json_obj['video_main_content']['contents'][0]['date_text']['runs'][0]['text'].split('Published on ')[-1])
			metadata.originally_available_at = date.date()
			metadata.year = date.year

			# Add YouTube user as director
			metadata.directors.clear()

			if Prefs['add_user_as_director']:

				try:
					meta_director = metadata.directors.new()
					meta_director.name = json_obj['video_main_content']['contents'][0]['short_byline_text']['runs'][0]['text']
					meta_director.photo = json_obj['video_main_content']['contents'][0]['thumbnail']['url'].replace('/s88-', '/s512-')
				except:
					pass
