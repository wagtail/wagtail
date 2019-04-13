speakerdeck = {
    "endpoint": "https://speakerdeck.com/oembed.{format}",
    "urls": [
        r'^http(?:s)?://speakerdeck\.com/.+$',
    ],
}

app_net = {
    "endpoint": "https://alpha-api.app.net/oembed",
    "urls": [
        r'^http(?:s)?://alpha\.app\.net/[^#?/]+/post/.+$',
        r'^http(?:s)?://photos\.app\.net/[^#?/]+/.+$',
    ],
}

youtube = {
    "endpoint": "http://www.youtube.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/watch.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/v/.+$',
        r'^http(?:s)?://youtu\.be/.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/user/.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/[^#?/]+#[^#?/]+/.+$',
        r'^http(?:s)?://m\.youtube\.com/index.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/profile.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/view_play_list.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?youtube\.com/playlist.+$',
    ],
}

deviantart = {
    "endpoint": "http://backend.deviantart.com/oembed",
    "urls": [
        r'^http://(?:[-\w]+\.)?deviantart\.com/art/.+$',
        r'^http://fav\.me/.+$',
        r'^http://sta\.sh/.+$',
        r'^http://(?:[-\w]+\.)?deviantart\.com/[^#?/]+#/d.+$',
    ],
}

blip_tv = {
    "endpoint": "http://blip.tv/oembed/",
    "urls": [
        r'^http://[-\w]+\.blip\.tv/.+$',
    ],
}

dailymotion = {
    "endpoint": "http://www.dailymotion.com/api/oembed/",
    "urls": [
        r'^http://[-\w]+\.dailymotion\.com/.+$',
    ],
}

flikr = {
    "endpoint": "http://www.flickr.com/services/oembed/",
    "urls": [
        r'^http(?:s)?://[-\w]+\.flickr\.com/photos/.+$',
        r'^http(?:s)?://flic\.kr\.com/.+$',
    ],
}

hulu = {
    "endpoint": "http://www.hulu.com/api/oembed.{format}",
    "urls": [
        r'^http://www\.hulu\.com/watch/.+$',
    ],
}

nfb = {
    "endpoint": "http://www.nfb.ca/remote/services/oembed/",
    "urls": [
        r'^http://(?:[-\w]+\.)?nfb\.ca/film/.+$',
    ],
}

qik = {
    "endpoint": "http://qik.com/api/oembed.{format}",
    "urls": [
        r'^http://qik\.com/.+$',
        r'^http://qik\.ly/.+$',
    ],
}

revision3 = {
    "endpoint": "http://revision3.com/api/oembed/",
    "urls": [
        r'^http://[-\w]+\.revision3\.com/.+$',
    ],
}

scribd = {
    "endpoint": "http://www.scribd.com/services/oembed",
    "urls": [
        r'^http://[-\w]+\.scribd\.com/.+$',
    ],
}

viddler = {
    "endpoint": "http://www.viddler.com/oembed/",
    "urls": [
        r'^http://[-\w]+\.viddler\.com/v/.+$',
        r'^http://[-\w]+\.viddler\.com/explore/.+$',
    ],
}

vimeo = {
    "endpoint": "http://www.vimeo.com/api/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?vimeo\.com/.+$',
        r'^http(?:s)?://player\.vimeo\.com/.+$',
    ],
}

dotsub = {
    "endpoint": "http://dotsub.com/services/oembed",
    "urls": [
        r'^http://dotsub\.com/view/.+$',
    ],
}

yfrog = {
    "endpoint": "http://www.yfrog.com/api/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?yfrog\.com/.+$',
        r'^http(?:s)?://(?:www\.)?yfrog\.us/.+$',
    ],
}

clickthrough = {
    "endpoint": "http://clikthrough.com/services/oembed",
    "urls": [
        r'^http(?:s)?://(?:[-\w]+\.)?clikthrough\.com/.+$',
    ],
}

kinomap = {
    "endpoint": "http://www.kinomap.com/oembed",
    "urls": [
        r'^http://[-\w]+\.kinomap\.com/.+$',
    ],
}

photobucket = {
    "endpoint": "https://photobucket.com/oembed",
    "urls": [
        r'^http://(?:[-\w]+\.)?photobucket\.com/albums/.+$',
        r'^http://(?:[-\w]+\.)?photobucket\.com/groups/.+$',
    ],
}

instagram = {
    "endpoint": "http://api.instagram.com/oembed",
    "urls": [
        r'^http://instagr\.am/p/.+$',
        r'^http[s]?://(?:www\.)?instagram\.com/p/.+$',
    ],
}

facebook_video = {
    "endpoint": "https://www.facebook.com/plugins/video/oembed.{format}",
    "urls": [
        r'^https://(?:www\.)?facebook\.com/.+?/videos/.+$',
        r'^https://(?:www\.)?facebook\.com/video\.php\?(?:v|id)=.+$',
    ],
}

facebook_post = {
    "endpoint": "https://www.facebook.com/plugins/post/oembed.{format}",
    "urls": [
        r'^https://(?:www\.)?facebook\.com/.+?/(?:posts|activity)/.+$',
        r'^https://(?:www\.)?facebook\.com/photo\.php\?fbid=.+$',
        r'^https://(?:www\.)?facebook\.com/(?:photos|questions)/.+$',
        r'^https://(?:www\.)?facebook\.com/permalink\.php\?story_fbid=.+$',
        r'^https://(?:www\.)?facebook\.com/media/set/?\?set=.+$',
        r'^https://(?:www\.)?facebook\.com/notes/.+?/.+?/.+$',

        # At the moment, not documented on https://developers.facebook.com/docs/plugins/oembed-endpoints
        # Works for posts with a single photo
        r'^https://(?:www\.)?facebook\.com/.+?/photos/.+$',
    ],
}

slideshare = {
    "endpoint": "https://www.slideshare.net/api/oembed/2",
    "urls": [
        r'^http://www\.slideshare\.net/.+$',
    ],
}

major_league_gaming = {
    "endpoint": "http://tv.majorleaguegaming.com/oembed",
    "urls": [
        r'^http://mlg\.tv/.+$',
        r'^http://tv\.majorleaguegaming\.com/.+$',
    ],
}

opera = {
    "endpoint": "http://my.opera.com/service/oembed",
    "urls": [
        r'^http://my\.opera\.com/.+$',
    ],
}

skitch = {
    "endpoint": "http://skitch.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?skitch\.com/.+$',
        r'^http://skit\.ch/.+$',
    ],
}

twitter = {
    "endpoint": "https://api.twitter.com/1/statuses/oembed.{format}",
    "urls": [
        r'^http(?:s)?://twitter\.com/(?:#!)?[^#?/]+/status/.+$',
    ],
}

soundcloud = {
    "endpoint": "https://soundcloud.com/oembed",
    "urls": [
        r'^https://soundcloud\.com/[^#?/]+/.+$',
    ],
}

collegehumor = {
    "endpoint": "http://www.collegehumor.com/oembed.{format}",
    "urls": [
        r'^http://(?:www\.)?collegehumor\.com/video/.+$',
        r'^http://(?:www\.)?collegehumor\.com/video:.+$',
    ],
}

polleverywhere = {
    "endpoint": "http://www.polleverywhere.com/services/oembed/",
    "urls": [
        r'^http://www\.polleverywhere\.com/polls/.+$',
        r'^http://www\.polleverywhere\.com/multiple_choice_polls/.+$',
        r'^http://www\.polleverywhere\.com/free_text_polls/.+$',
    ],
}

ifixit = {
    "endpoint": "http://www.ifixit.com/Embed",
    "urls": [
        r'^http://www\.ifixit\.com/[^#?/]+/[^#?/]+/.+$',
    ],
}

smugmug = {
    "endpoint": "http://api.smugmug.com/services/oembed/",
    "urls": [
        r'^http(?:s)?://(?:www\.)?smugmug\.com/[^#?/]+/.+$',
    ],
}

github_gist = {
    "endpoint": "https://github.com/api/oembed",
    "urls": [
        r'^http(?:s)?://gist\.github\.com/.+$',
    ],
}

animoto = {
    "endpoint": "http://animoto.com/services/oembed",
    "urls": [
        r'^http://animoto\.com/play/.+$',
    ],
}

rdio = {
    "endpoint": "http://www.rdio.com/api/oembed",
    "urls": [
        r'^http://(?:wwww\.)?rdio\.com/people/[^#?/]+/playlists/.+$',
        r'^http://[-\w]+\.rdio\.com/artist/[^#?/]+/album/.+$',
    ],
}

five_min = {
    "endpoint": "http://api.5min.com/oembed.{format}",
    "urls": [
        r'^http://www\.5min\.com/video/.+$',
    ],
}

five_hundred_px = {
    "endpoint": "http://500px.com/photo/{1}/oembed.{format}",
    "urls": [
        r'^http://500px\.com/photo/([^#?/]+)(?:.+)?$',
    ],
}

dipdive = {
    "endpoint": "http://api.dipdive.com/oembed.{format}",
    "urls": [
        r'^http://[-\w]+\.dipdive\.com/media/.+$',
    ],
}

yandex = {
    "endpoint": "http://video.yandex.ru/oembed.{format}",
    "urls": [
        r'^http://video\.yandex\.ru/users/[^#?/]+/view/.+$',
    ],
}

mixcloud = {
    "endpoint": "https://www.mixcloud.com/oembed/",
    "urls": [
        r'^https?://(?:www\.)?mixcloud\.com/.+$',
    ],
}

kickstarter = {
    "endpoint": "http://www.kickstarter.com/services/oembed",
    "urls": [
        r'^http(?:s)://[-\w]+\.kickstarter\.com/projects/.+$',
    ],
}

coub = {
    "endpoint": "http://coub.com/api/oembed.{format}",
    "urls": [
        r'^http(?:s)?://coub\.com/view/.+$',
        r'^http(?:s)?://coub\.com/embed/.+$',
    ],
}

screenr = {
    "endpoint": "http://www.screenr.com/api/oembed.{format}",
    "urls": [
        r'^http://www\.screenr\.com/.+$',
    ],
}

funny_or_die = {
    "endpoint": "http://www.funnyordie.com/oembed.{format}",
    "urls": [
        r'^http://www\.funnyordie\.com/videos/.+$',
    ],
}

wistia = {
    "endpoint": "http://fast.wistia.com/oembed.{format}",
    "urls": [
        r'^https?://([^/]+\.)?(wistia.com|wi.st)/(medias|embed)/.+$',
    ],
}

ustream = {
    "endpoint": "http://www.ustream.tv/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?ustream\.tv/.+$',
        r'^http(?:s)?://(?:www\.)?ustream\.com/.+$',
        r'^http://ustre\.am/.+$',
    ],
}

wordpress = {
    "endpoint": "http://wordpress.tv/oembed/",
    "urls": [
        r'^http://wordpress\.tv/.+$',
    ],
}

polldaddy = {
    "endpoint": "http://polldaddy.com/oembed/",
    "urls": [
        r'^http(?:s)?://(?:[-\w]+\.)?polldaddy\.com/.+$',
    ],
}

bambuser = {
    "endpoint": "http://api.bambuser.com/oembed.{format}",
    "urls": [
        r'^http://bambuser\.com/channel/[^#?/]+/broadcast/.+$',
        r'^http://bambuser\.com/channel/.+$',
        r'^http://bambuser\.com/v/.+$',
    ],
}

ted = {
    "endpoint": "http://www.ted.com/talks/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?ted\.com/talks/.+$',
        r'^http(?:s)?://(?:www\.)?ted\.com/talks/lang/[^#?/]+/.+$',
        r'^http(?:s)?://(?:www\.)?ted\.com/index\.php/talks/.+$',
        r'^http(?:s)?://(?:www\.)?ted\.com/index\.php/talks/lang/[^#?/]+/.+$',
    ],
}

chirb = {
    "endpoint": "http://chirb.it/oembed.{format}",
    "urls": [
        r'^http://chirb\.it/.+$',
    ],
}

circuitlab = {
    "endpoint": "https://www.circuitlab.com/circuit/oembed/",
    "urls": [
        r'^http(?:s)?://(?:www\.)?circuitlab\.com/circuit/.+$',
    ],
}

geograph_uk = {
    "endpoint": "http://api.geograph.org.uk/api/oembed",
    "urls": [
        r'^http://(?:[-\w]+\.)?geograph\.org\.uk/.+$',
        r'^http://(?:[-\w]+\.)?geograph\.co\.uk/.+$',
        r'^http://(?:[-\w]+\.)?geograph\.ie/.+$',
    ],
}

hlipp = {
    "endpoint": "http://geo.hlipp.de/restapi.php/api/oembed",
    "urls": [
        r'^http://geo-en\.hlipp\.de/.+$',
        r'^http://geo\.hlipp\.de/.+$',
        r'^http://germany\.geograph\.org/.+$',
    ],
}

geograph_gg = {
    "endpoint": "http://www.geograph.org.gg/api/oembed",
    "urls": [
        r'^http://(?:[-\w]+\.)?geograph\.org\.gg/.+$',
        r'^http://(?:[-\w]+\.)?geograph\.org\.je/.+$',
        r'^http://channel-islands\.geograph\.org/.+$',
        r'^http://channel-islands\.geographs\.org/.+$',
        r'^http://(?:[-\w]+\.)?channel\.geographs\.org/.+$',
    ],
}

vzaar = {
    "endpoint": "http://vzaar.com/api/videos/{1}.{format}",
    "urls": [
        r'^http://(?:www\.)?vzaar\.com/videos/([^#?/]+)(?:.+)?$',
        r'^http://www\.vzaar\.tv/([^#?/]+)(?:.+)?$',
        r'^http://vzaar\.tv/([^#?/]+)(?:.+)?$',
        r'^http://vzaar\.me/([^#?/]+)(?:.+)?$',
        r'^http://[-\w]+\.vzaar\.me/([^#?/]+)(?:.+)?$',
    ],
}

minoto = {
    "endpoint": "http://api.minoto-video.com/services/oembed.{format}",
    "urls": [
        r'^http://api\.minoto-video\.com/publishers/[^#?/]+/videos/.+$',
        r'^http://dashboard\.minoto-video\.com/main/video/details/.+$',
        r'^http://embed\.minoto-video\.com/.+$',
    ],
}

videojug = {
    "endpoint": "http://www.videojug.com/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:[-\w]+\.)?videojug\.com/film/.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?videojug\.com/payer/.+$',
        r'^http(?:s)?://(?:[-\w]+\.)?videojug\.com/interview/.+$',
    ],
}

sapo = {
    "endpoint": "http://videos.sapo.pt/oembed",
    "urls": [
        r'^http(?:s)?://videos\.sapo\.pt/.+$',
    ],
}

vhx_tv = {
    "endpoint": "http://vhx.tv/services/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?vhx\.tv/.+$',
    ],
}

justin_tv = {
    "endpoint": "http://api.justin.tv/api/embed/from_url.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?justin\.tv/.+$',
    ],
}

official_fm = {
    "endpoint": "http://official.fm/services/oembed.{format}",
    "urls": [
        r'^http(?:s)?://official\.fm/.+$',
    ],
}

huffduffer = {
    "endpoint": "http://huffduffer.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?huffduffer\.com/[^#?/]+/.+$',
    ],
}

spotify = {
    "endpoint": "https://embed.spotify.com/oembed/",
    "urls": [
        r'^http(?:s)?://open\.spotify\.com/.+$',
        r'^http(?:s)?://spoti\.fi/.+$',
    ],
}

shoudio = {
    "endpoint": "http://shoudio.com/api/oembed",
    "urls": [
        r'^http://shoudio\.com/.+$',
        r'^http://shoud\.io/.+$',
    ],
}

mobypicture = {
    "endpoint": "http://api.mobypicture.com/oEmbed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?mobypicture\.com/user/[^#?/]+/view/.+$',
        r'^http(?:s)?://(?:www\.)?moby\.to/.+$',
    ],
}

twenty_three_hq = {
    "endpoint": "http://www.23hq.com/23/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?23hq\.com/[^#?/]+/photo/.+$',
    ],
}

gmep = {
    "endpoint": "http://gmep.org/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?gmep\.org/.+$',
        r'^http(?:s)?://gmep\.imeducate\.com/.+$',
    ],
}

urtak = {
    "endpoint": "http://oembed.urtak.com/1/oembed",
    "urls": [
        r'^http(?:s)?://(?:[-\w]+\.)?urtak\.com/.+$',
    ],
}

cacoo = {
    "endpoint": "http://cacoo.com/oembed.{format}",
    "urls": [
        r'^http(?:s)?://cacoo\.com/.+$',
    ],
}

dailymile = {
    "endpoint": "http://api.dailymile.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?dailymile\.com/people/[^#?/]+/entries/.+$',
    ],
}

dipity = {
    "endpoint": "http://www.dipity.com/oembed/timeline/",
    "urls": [
        r'^http(?:s)?://(?:www\.)?dipity\.com/timeline/.+$',
        r'^http(?:s)?://(?:www\.)?dipity\.com/voaweb/.+$',
    ],
}

sketchfab = {
    "endpoint": "https://sketchfab.com/oembed",
    "urls": [
        r'^http(?:s)?://sketchfab\.com/show/.+$',
    ],
}

meetup = {
    "endpoint": "https://api.meetup.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?meetup\.com/.+$',
        r'^http(?:s)?://(?:www\.)?meetup\.ps/.+$',
    ],
}

roomshare = {
    "endpoint": "https://roomshare.jp/oembed.{format}",
    "urls": [
        r'^http(?:s)?://(?:www\.)?roomshare\.jp/(?:en/)?post/.+$',
    ],
}

crowd_ranking = {
    "endpoint": "http://crowdranking.com/api/oembed.{format}",
    "urls": [
        r'^http(?:s)?://crowdranking\.com/crowdrankings/.+$',
        r'^http(?:s)?://crowdranking\.com/rankings/.+$',
        r'^http(?:s)?://crowdranking\.com/topics/.+$',
        r'^http(?:s)?://crowdranking\.com/widgets/.+$',
        r'^http(?:s)?://crowdranking\.com/r/.+$',
    ],
}

etsy = {
    "endpoint": "http://openapi.etsy.com/svc/oembed/",
    "urls": [
        r'^http(?:s)?://(?:www\.)?etsy\.com/listing/.+$',
    ],
}

audioboom = {
    "endpoint": "https://audioboom.com/publishing/oembed.{format}",
    "urls": [
        r'^http(?:s)?://audioboom\.com/boos/.+$',
        r'^https?://audioboom\.com/posts/.+$',
    ],
}

clikthrough = {
    "endpoint": "http://demo.clikthrough.com/services/oembed/",
    "urls": [
        r'^http(?:s)?://demo\.clikthrough\.com/theater/video/.+$',
    ],
}

ifttt = {
    "endpoint": "http://www.ifttt.com/oembed/",
    "urls": [
        r'^http(?:s)?://ifttt\.com/recipes/.+$',
    ],
}

issuu = {
    "endpoint": "http://issuu.com/oembed",
    "urls": [
        r'^http(?:s)?://(?:www\.)?issuu\.com/[^#?/]+/docs/.+$',
    ],
}

tumblr = {
    "endpoint": "https://www.tumblr.com/oembed/1.0",
    "urls": [
        r'^http(?:s)?://.+?\.tumblr\.com/post/.+$',
    ]
}

all_providers = [
    speakerdeck, app_net, youtube, deviantart, blip_tv, dailymotion, flikr,
    hulu, nfb, qik, revision3, scribd, viddler, vimeo, dotsub, yfrog,
    clickthrough, kinomap, photobucket, instagram, facebook_video,
    facebook_post, slideshare,
    major_league_gaming, opera, skitch, twitter, soundcloud, collegehumor,
    polleverywhere, ifixit, smugmug, github_gist, animoto, rdio, five_min,
    five_hundred_px, dipdive, yandex, mixcloud, kickstarter, coub, screenr,
    funny_or_die, wistia, ustream, wordpress, polldaddy, bambuser, ted, chirb,
    circuitlab, geograph_uk, hlipp, geograph_gg, vzaar, minoto, videojug, sapo,
    vhx_tv, justin_tv, official_fm, huffduffer, spotify, shoudio, mobypicture,
    twenty_three_hq, gmep, urtak, cacoo, dailymile, dipity, sketchfab, meetup,
    roomshare, crowd_ranking, etsy, audioboom, clikthrough, ifttt, issuu, tumblr
]
