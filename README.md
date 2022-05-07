# YouTube-Agent.bundle Plex Movie & TV Series library agent 

Please respect Youtube Terms and conditions: https://www.youtube.com/t/terms

Download playlist:
Take video link: https://www.youtube.com/watch?v=f-wWBGo6a2w&list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat
click on top right on playlist name or remove v=video_id https://www.youtube.com/watch?list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat
.\youtube-dl.exe https://www.youtube.com/watch?list=PL22J3VaeABQD_IZs7y60I3lUrrFTzkpat

--restrict-filenames
Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames, makes the filenames slightly messy but no crash due to unsupported character

My_Plex_Pass@forums.plex.com script for both channels and playlists in format channel [chanid]\title [videoid].ext:
- youtube-dl -v --dateafter 20081004 --download-archive /volume1/Youtube/.Downloaded -i -o "/volume1/Youtube/%(uploader)s [%(channel_id)s]/%(playlist_index)s - %(title)s [%(id)s].%(ext)s" -f bestvideo+bestaudio -ci --batch-file=/volume1/Youtube/Channels_to_DL.txt
- Format generated: "Youtube\Errant Signal [UCm4JnxTxtvItQecKUc4zRhQ]\001 - Thanksgiving Leftovers - Battlefield V [Qgdr8xdqGDE]"

YouTube IDs
- Playlist id: PL and 16 hexadecimal characters 0-9 and A-F or 32 chars 0-9 a-Z _ - (EX: https://www.youtube.com/watch?v=aCl4SD7SkLE&list=PLMBYlcH3smRxxcXT7G-HHAj5czGS0sZsB)
- Channel id: PL and 32 hexadecimal characters 0-9 and A-F or 32 chars 0-9 a-Z _ - (EX: (https://www.youtube.com/channel/UCYzPXprvl5Y-Sf0g4vX-m6g)
- Video id: 11 chars long 0-9 a-Z _ -

Requirements
- Do create your own YouTube API key and replace in ASS code and agent settings
- Please use the Absolute Series Scanner to scan your media and leave the YouTube id in the series/movie title
- leave the YouTube video ID on every file
- Playlist (preffered) id OR Channel id on series foldername (as Search() need to assign an id to the series)

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
- [!] register your own API key and also replace API_KEY='AIzaSyC2q8yjciNdlYRNdvwbb7NEcDxBkv1Cass' in ass code and the agent setting [Agent_youtube_api_key] OR you will deplete the quota of requests in MY account and metadata will stop for ALL users using default settings. 
- You can use grouping folders and a collection field will be created. If the logs complain about 'INFO (__init__:527) - Place correct Plex token in X-Plex-Token.id file in logs folder or in PLEX_LIBRARY_URL variable to have a log per library - https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token', then create a "Plex Media Server/X-Plex-Token.id" containing the Plex token id by logging on plex.tv/desktop, then https://plex.tv/devices.xml, it will be MediaContainer/Device ... token="xxxxxxxxxxxxxx".


Movie Library Fields supported:
- title
- summary
- poster
- rating
- originally_available_at
- year
- genres (many? to test)
- directors (1)

Example
=======

CaRtOoNz [UCdQWs2nw6w77Rw0t-37a4OA]/
- Ben and Ed/
  - Ben and Ed _ 'My Zombie Best Friend!' (I Didn't Need Those Legs Anyway!) [fRFr7L_qgEo].mkv
  - Ben and Ed _ 'Clownin Around!' (F_ck You Neck-Beard!) [Nh9eILgD5N4].mkv
- Golf With Your Friends/
  - Golf With Friends _ HOLE IN ONE...THOUSAND! (w_ H2O Delirious, Bryce, & Ohmwrecker) [81er8CP24h8].mkv
  - Golf With Friends _ GOLF LIKE AN EGYPTIAN! (w_ H2O Delirious, Bryce, & Ohmwrecker) [gKYid-SjDiE].mkv

H2ODelirious [UCClNRixXlagwAd--5MwJKCw]/
- Ben and Ed/
  - Ben And Ed Ep.1 (MUST SAVE BEN) BRAINNNNNSSSS [9YeXl28l9Yg].mkv
  - Ben And Ed - Blood Party - ANGRYLIRIOUS!!!!! (I CAN DO THIS!) [BEDE2z3G3hY].mkv
- Golf With Your Friends/
  - Golf With Your Friends - 1st Time Playing! 'Professionals' [wxS52xI_W_Y].mkv
  - Golf With Your Friends - Hitting Balls, Stroking Out! [GdLon0CCEXE].mkv

History
=======

Forked initially from paulds8 and sander1's 'YouTube-Agent.bundle' movie only agent:

sander1 did the initial movie only agent using a given youtube video id
https://github.com/sander1/YouTube-Agent.bundle
https://forums.plex.tv/discussion/83106/rel-youtube-metadata-agent

paulds8 did the initial title search fork i had to fix
https://github.com/paulds8/YouTube-Agent.bundle/tree/namematch
https://forums.plex.tv/discussion/300800/youtube-agent-matching-on-name

Made it into a series agent straight away...

Installation
============

Here is how to find the plug-in folder location:
https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-

Plex main folder location:

    * '%LOCALAPPDATA%\Plex Media Server\'                                        # Windows Vista/7/8
    * '%USERPROFILE%\Local Settings\Application Data\Plex Media Server\'         # Windows XP, 2003, Home Server
    * '$HOME/Library/Application Support/Plex Media Server/'                     # Mac OS
    * '$PLEX_HOME/Library/Application Support/Plex Media Server/',               # Linux
    * '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/', # Debian,Fedora,CentOS,Ubuntu
    * '/usr/local/plexdata/Plex Media Server/',                                  # FreeBSD
    * '/usr/pbi/plexmediaserver-amd64/plexdata/Plex Media Server/',              # FreeNAS
    * '${JAIL_ROOT}/var/db/plexdata/Plex Media Server/',                         # FreeNAS
    * '/c/.plex/Library/Application Support/Plex Media Server/',                 # ReadyNAS
    * '/share/MD0_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/',        # QNAP
    * '/volume1/Plex/Library/Application Support/Plex Media Server/',            # Synology, Asustor
    * '/raid0/data/module/Plex/sys/Plex Media Server/',                          # Thecus
    * '/raid0/data/PLEX_CONFIG/Plex Media Server/'                               # Thecus Plex community    

Get the latest source zip in github release for hama https://github.com/ZeroQI/Youtube-Agent.bundle > "Clone or download > Download Zip
Folders Youtube-Agent.bundle-master.zip and copy inside folder Youtube-Agent.bundle-master in plug-ins folders but rename to "Youtube-Agent.bundle" (remove -master) :

Troubleshooting:
================
If you ask for something already answered in the readme, or post scanner issues on the agent page or vice-versa, please donate (will be refered to as the RTFM tax)

If files and series are showing in Plex GUI with the right season, the scanner did its job
If you miss metadata (serie title wrong, no posters, summary, wrong episode title or summaries, ep screenshot, etc...), that is the Agent doing.

To avoid already solved issues, and make sure you do include all relevant logs in one go, please do the following:
- Update to the latest Absolute Series Scanner, Youtube-Agent
- deleting all Plex logs leaving folders intact
- restart Plex
- Update the series Metadata
- including all the following logs: (location: https://support.plex.tv/hc/en-us/articles/200250417-Plex-Media-Server-Log-Files)
   - [...]/Plex Media Server/Logs/PMS Plugin Logs/com.plexapp.agents.Youtube-Agent.log (Agent logs)
   - [...]/Plex Media Server/Logs/PMS Plugin Logs/com.plexapp.system.log (show why the agent cannot launch)
   - Screen capture to illustrate if needed. Above logs are still mandatory

Support thread for agent:
- https://github.com/ZeroQI/YouTube-Agent.bundle/issues (proven or confident enough it's a bug. Include the symptoms, the logs mentionned above)
- https://forums.plex.tv/discussion/83106/rel-youtube-metadata-agent/p5 (not sure if bug, if bug will create a gihub issue ticket)

Donation link:
==============
PayPal.Me/ZeroQI or https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=S8CUKCX4CWBBG&lc=IE&item_name=Plex%20movies%20and%20TV%20series%20Youtube%20Agent&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted
