# YouTube-Agent.bundle Plex Movie & TV Series library agent 


YouTube IDs
- Playlist id: PL and 16 hexadecimal characters 0-9 and A-F
- Video id: 11 chars long 0-9 and a-z, can have also'_-'

Naming convention for Movie/Home Video library:
- filename without extension named exactly the same as the YouTube video
- filename with youtube video id '[youtube-xxxxxxxxxx]'

Naming convention for TV Series library:
- movies have to be put in identically named folder named exactly the same as the YouTube video or have youtube video id
- series foldername with with youtube playlist id '[youtube-PLxxxxxxxxxxxxxxxx'] in title or inside a youtube.id file at its root
- season folder with youtube playlist id '[youtube-PLxxxxxxxxxxxxxxxx'] in title or inside a youtube.id file at its root

Note:
- The Absolute Series Scanner will support youtube.id file in series folder and pass it to the agent through the series title
- The agent will support the following formats in file or folder names [youtube-xxx], [YouTube-xxx], [Youtube-xxx ] and [xxxxxxxx]

Movie Library Fields supported:
- title
- summary
- poster
- rating
- originally_available_at
- year
- genres (many? to test)
- directors (1)

Forked initially from paulds8 and sander1's 'YouTube-Agent.bundle':

sander1 did the initial movie only agent using a given youtube video id
https://github.com/sander1/YouTube-Agent.bundle
https://forums.plex.tv/discussion/83106/rel-youtube-metadata-agent

paulds8 did the initial title search fork i had to fix
https://github.com/paulds8/YouTube-Agent.bundle/tree/namematch
https://forums.plex.tv/discussion/300800/youtube-agent-matching-on-name

Donation link: PayPal.Me/ZeroQI or https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=S8CUKCX4CWBBG&lc=IE&item_name=Plex%20movies%20and%20TV%20series%20Youtube%20Agent&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
