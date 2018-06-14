# YouTube-Agent.bundle Plex Movie & TV Series library agent 

-Please use the Absolute Series Scanner to scan your media and leave the YouTube id in the series/movie title

YouTube IDs
- Playlist id: PL and 16 hexadecimal characters 0-9 and A-F or 32 chars 0-9 a-Z _ -
- Channel id: PL and 32 hexadecimal characters 0-9 and A-F or 32 chars 0-9 a-Z _ -
- Video id: 11 chars long 0-9 a-Z _ -

Naming convention for Movie/Home Video library:
- filename without extension named exactly the same as the YouTube video
- filename with youtube video id '[xxxxxxxxxx]'or '[youtube-xxxxxxxxxx]'

Naming convention for TV Series library:
- movies have to be put in identically named folder named exactly the same as the YouTube video or have youtube video id
- series foldername with with youtube playlist id '[PLxxxxxxxxxxxxxxxx]' in title or inside a youtube.id file at its root
- series foldername with with youtube channel id '[UCxxxxxxxxxxxxxxxx]' in title or inside a youtube.id file at its root

Note:
- The Absolute Series Scanner will support youtube.id file in series folder and pass it to the agent through the series title
- The agent will support the following formats in file or folder names [xxxxxxxx], [youtube-xxx], [YouTube-xxx], and [Youtube-xxx ]

Movie Library Fields supported:
- title
- summary
- poster
- rating
- originally_available_at
- year
- genres (many? to test)
- directors (1)

Forked initially from paulds8 and sander1's 'YouTube-Agent.bundle' movie only agent initially:

sander1 did the initial movie only agent using a given youtube video id
https://github.com/sander1/YouTube-Agent.bundle
https://forums.plex.tv/discussion/83106/rel-youtube-metadata-agent

paulds8 did the initial title search fork i had to fix
https://github.com/paulds8/YouTube-Agent.bundle/tree/namematch
https://forums.plex.tv/discussion/300800/youtube-agent-matching-on-name

Download playlist:
Take video link: https://www.youtube.com/watch?v=f-wWBGo6a2w&list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat
click on top right on playlist name or remove v=video_id https://www.youtube.com/watch?list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat
.\youtube-dl.exe https://www.youtube.com/watch?list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat

Donation link: PayPal.Me/ZeroQI or https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=S8CUKCX4CWBBG&lc=IE&item_name=Plex%20movies%20and%20TV%20series%20Youtube%20Agent&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
