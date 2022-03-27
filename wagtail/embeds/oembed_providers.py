animoto = {
    "endpoint": "https://animoto.com/services/oembed",
    "urls": [
        r"^https?://animoto\.com/play/.+$",
    ],
}

app_net = {
    "endpoint": "https://alpha-api.app.net/oembed",
    "urls": [
        r"^https?://alpha\.app\.net/[^#?/]+/post/.+$",
        r"^https?://photos\.app\.net/[^#?/]+/.+$",
    ],
}

audioboom = {
    "endpoint": "https://audioboom.com/publishing/oembed.{format}",
    "urls": [
        r"^https?://audioboom\.com/boos/.+$",
        r"^https?://audioboom\.com/posts/.+$",
    ],
}

bambuser = {
    "endpoint": "http://api.bambuser.com/oembed.{format}",
    "urls": [
        r"^http://bambuser\.com/channel/[^#?/]+/broadcast/.+$",
        r"^http://bambuser\.com/channel/.+$",
        r"^http://bambuser\.com/v/.+$",
    ],
}

blip_tv = {
    "endpoint": "http://blip.tv/oembed/",
    "urls": [
        r"^http://[-\w]+\.blip\.tv/.+$",
    ],
}

cacoo = {
    "endpoint": "http://cacoo.com/oembed.{format}",
    "urls": [
        r"^https?://cacoo\.com/.+$",
    ],
}

chirb = {
    "endpoint": "https://chirb.it/oembed.{format}",
    "urls": [
        r"^https?://chirb\.it/.+$",
    ],
}

circuitlab = {
    "endpoint": "https://www.circuitlab.com/circuit/oembed/",
    "urls": [
        r"^https?://(?:www\.)?circuitlab\.com/circuit/.+$",
    ],
}

clickthrough = {
    "endpoint": "http://clikthrough.com/services/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?clikthrough\.com/.+$",
    ],
}

clikthrough = {
    "endpoint": "http://demo.clikthrough.com/services/oembed/",
    "urls": [
        r"^https?://demo\.clikthrough\.com/theater/video/.+$",
    ],
}

collegehumor = {
    "endpoint": "http://www.collegehumor.com/oembed.{format}",
    "urls": [
        r"^http://(?:www\.)?collegehumor\.com/video/.+$",
        r"^http://(?:www\.)?collegehumor\.com/video:.+$",
    ],
}

coub = {
    "endpoint": "http://coub.com/api/oembed.{format}",
    "urls": [
        r"^https?://coub\.com/view/.+$",
        r"^https?://coub\.com/embed/.+$",
    ],
}

crowd_ranking = {
    "endpoint": "http://crowdranking.com/api/oembed.{format}",
    "urls": [
        r"^https?://crowdranking\.com/crowdrankings/.+$",
        r"^https?://crowdranking\.com/rankings/.+$",
        r"^https?://crowdranking\.com/topics/.+$",
        r"^https?://crowdranking\.com/widgets/.+$",
        r"^https?://crowdranking\.com/r/.+$",
    ],
}


dailymile = {
    "endpoint": "http://api.dailymile.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?dailymile\.com/people/[^#?/]+/entries/.+$",
    ],
}


dailymotion = {
    "endpoint": "https://www.dailymotion.com/api/oembed/",
    "urls": [
        r"^https?://[-\w]+\.dailymotion\.com/.+$",
    ],
}

datastudio = {
    "endpoint": "https://datastudio.google.com/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?datastudio\.google\.com/embed/.+$",
    ],
}


deviantart = {
    "endpoint": "https://backend.deviantart.com/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?deviantart\.com/art/.+$",
        r"^https?://fav\.me/.+$",
        r"^https?://sta\.sh/.+$",
        r"^https?://(?:[-\w]+\.)?deviantart\.com/[^#?/]+#/d.+$",
    ],
}


dipdive = {
    "endpoint": "http://api.dipdive.com/oembed.{format}",
    "urls": [
        r"^http://[-\w]+\.dipdive\.com/media/.+$",
    ],
}

dipity = {
    "endpoint": "http://www.dipity.com/oembed/timeline/",
    "urls": [
        r"^https?://(?:www\.)?dipity\.com/timeline/.+$",
        r"^https?://(?:www\.)?dipity\.com/voaweb/.+$",
    ],
}


dotsub = {
    "endpoint": "https://dotsub.com/services/oembed",
    "urls": [
        r"^https?://dotsub\.com/view/.+$",
    ],
}


etsy = {
    "endpoint": "https://openapi.etsy.com/svc/oembed/",
    "urls": [
        r"^https?://(?:www\.)?etsy\.com/listing/.+$",
    ],
}


five_hundred_px = {
    "endpoint": "https://500px.com/photo/{1}/oembed.{format}",
    "urls": [
        r"^https?://500px\.com/photo/([^#?/]+)(?:.+)?$",
    ],
}

five_min = {
    "endpoint": "http://api.5min.com/oembed.{format}",
    "urls": [
        r"^http://www\.5min\.com/video/.+$",
    ],
}

flickr = {
    "endpoint": "https://www.flickr.com/services/oembed/",
    "urls": [
        r"^https?://[-\w]+\.flickr\.com/photos/.+$",
        r"^https?://flic\.kr\.com/.+$",
    ],
}

funny_or_die = {
    "endpoint": "https://www.funnyordie.com/oembed.{format}",
    "urls": [
        r"^https?://www\.funnyordie\.com/videos/.+$",
    ],
}


geograph_gg = {
    "endpoint": "http://www.geograph.org.gg/api/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?geograph\.org\.gg/.+$",
        r"^https?://(?:[-\w]+\.)?geograph\.org\.je/.+$",
        r"^https?://channel-islands\.geograph\.org/.+$",
        r"^https?://channel-islands\.geographs\.org/.+$",
        r"^https?://(?:[-\w]+\.)?channel\.geographs\.org/.+$",
    ],
}

geograph_uk = {
    "endpoint": "http://api.geograph.org.uk/api/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?geograph\.org\.uk/.+$",
        r"^https?://(?:[-\w]+\.)?geograph\.co\.uk/.+$",
        r"^https?://(?:[-\w]+\.)?geograph\.ie/.+$",
    ],
}

github_gist = {
    "endpoint": "https://github.com/api/oembed",
    "urls": [
        r"^https?://gist\.github\.com/.+$",
    ],
}


gmep = {
    "endpoint": "http://gmep.org/oembed.{format}",
    "urls": [
        r"^https?://(?:www\.)?gmep\.org/.+$",
        r"^https?://gmep\.imeducate\.com/.+$",
    ],
}

hlipp = {
    "endpoint": "http://geo.hlipp.de/restapi.php/api/oembed",
    "urls": [
        r"^https?://geo-en\.hlipp\.de/.+$",
        r"^https?://geo\.hlipp\.de/.+$",
        r"^https?://germany\.geograph\.org/.+$",
    ],
}

huffduffer = {
    "endpoint": "https://huffduffer.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?huffduffer\.com/[^#?/]+/.+$",
    ],
}


hulu = {
    "endpoint": "https://www.hulu.com/api/oembed.{format}",
    "urls": [
        r"^https?://www\.hulu\.com/watch/.+$",
    ],
}

ifixit = {
    "endpoint": "https://www.ifixit.com/Embed",
    "urls": [
        r"^https?://www\.ifixit\.com/[^#?/]+/[^#?/]+/.+$",
    ],
}


ifttt = {
    "endpoint": "https://www.ifttt.com/oembed/",
    "urls": [
        r"^https?://ifttt\.com/recipes/.+$",
    ],
}

issuu = {
    "endpoint": "https://issuu.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?issuu\.com/[^#?/]+/docs/.+$",
    ],
}


justin_tv = {
    "endpoint": "http://api.justin.tv/api/embed/from_url.{format}",
    "urls": [
        r"^https?://(?:www\.)?justin\.tv/.+$",
    ],
}

kickstarter = {
    "endpoint": "https://www.kickstarter.com/services/oembed",
    "urls": [
        r"^https?://[-\w]+\.kickstarter\.com/projects/.+$",
    ],
}

kinomap = {
    "endpoint": "https://www.kinomap.com/oembed",
    "urls": [
        r"^https?://[-\w]+\.kinomap\.com/.+$",
    ],
}

major_league_gaming = {
    "endpoint": "http://tv.majorleaguegaming.com/oembed",
    "urls": [
        r"^http://mlg\.tv/.+$",
        r"^http://tv\.majorleaguegaming\.com/.+$",
    ],
}

meetup = {
    "endpoint": "https://api.meetup.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?meetup\.com/.+$",
        r"^https?://(?:www\.)?meetup\.ps/.+$",
    ],
}

minoto = {
    "endpoint": "http://api.minoto-video.com/services/oembed.{format}",
    "urls": [
        r"^http://api\.minoto-video\.com/publishers/[^#?/]+/videos/.+$",
        r"^http://dashboard\.minoto-video\.com/main/video/details/.+$",
        r"^http://embed\.minoto-video\.com/.+$",
    ],
}


mixcloud = {
    "endpoint": "https://www.mixcloud.com/oembed/",
    "urls": [
        r"^https?://(?:www\.)?mixcloud\.com/.+$",
    ],
}

mobypicture = {
    "endpoint": "http://api.mobypicture.com/oEmbed",
    "urls": [
        r"^https?://(?:www\.)?mobypicture\.com/user/[^#?/]+/view/.+$",
        r"^https?://(?:www\.)?moby\.to/.+$",
    ],
}


nfb = {
    "endpoint": "http://www.nfb.ca/remote/services/oembed/",
    "urls": [
        r"^http://(?:[-\w]+\.)?nfb\.ca/film/.+$",
    ],
}


official_fm = {
    "endpoint": "http://official.fm/services/oembed.{format}",
    "urls": [
        r"^https?://official\.fm/.+$",
    ],
}


opera = {
    "endpoint": "http://my.opera.com/service/oembed",
    "urls": [
        r"^http://my\.opera\.com/.+$",
    ],
}


photobucket = {
    "endpoint": "https://photobucket.com/oembed",
    "urls": [
        r"^http://(?:[-\w]+\.)?photobucket\.com/albums/.+$",
        r"^http://(?:[-\w]+\.)?photobucket\.com/groups/.+$",
    ],
}

pinterest = {
    "endpoint": "https://www.pinterest.com/oembed.json",
    "urls": [
        r"^https?://[-\w]+\.pinterest\.com\.?[a-z]*/.+$",
        r"^https?://in\.pinterest\.com/.+$",
        r"^https?://pin\.it/.+$",
    ],
}


polldaddy = {
    "endpoint": "https://polldaddy.com/oembed/",
    "urls": [
        r"^https?://(?:[-\w]+\.)?polldaddy\.com/.+$",
    ],
}


polleverywhere = {
    "endpoint": "https://www.polleverywhere.com/services/oembed/",
    "urls": [
        r"^https?://www\.polleverywhere\.com/polls/.+$",
        r"^https?://www\.polleverywhere\.com/multiple_choice_polls/.+$",
        r"^https?://www\.polleverywhere\.com/free_text_polls/.+$",
    ],
}

qik = {
    "endpoint": "http://qik.com/api/oembed.{format}",
    "urls": [
        r"^http://qik\.com/.+$",
        r"^http://qik\.ly/.+$",
    ],
}


rdio = {
    "endpoint": "http://www.rdio.com/api/oembed",
    "urls": [
        r"^http://(?:wwww\.)?rdio\.com/people/[^#?/]+/playlists/.+$",
        r"^http://[-\w]+\.rdio\.com/artist/[^#?/]+/album/.+$",
    ],
}


reddit = {
    "endpoint": "https://www.reddit.com/oembed",
    "urls": [
        "^https?://(?:www\\.)?reddit\\.com/r/+[^#?/]+/comments/+[^#?/]+[^#?/].+$",
    ],
}


revision3 = {
    "endpoint": "http://revision3.com/api/oembed/",
    "urls": [
        r"^http://[-\w]+\.revision3\.com/.+$",
    ],
}

roomshare = {
    "endpoint": "https://roomshare.jp/oembed.{format}",
    "urls": [
        r"^https?://(?:www\.)?roomshare\.jp/(?:en/)?post/.+$",
    ],
}

sapo = {
    "endpoint": "http://videos.sapo.pt/oembed",
    "urls": [
        r"^https?://videos\.sapo\.pt/.+$",
    ],
}

screenr = {
    "endpoint": "http://www.screenr.com/api/oembed.{format}",
    "urls": [
        r"^http://www\.screenr\.com/.+$",
    ],
}

scribd = {
    "endpoint": "https://www.scribd.com/services/oembed",
    "urls": [
        r"^https?://[-\w]+\.scribd\.com/.+$",
    ],
}

shoudio = {
    "endpoint": "https://shoudio.com/api/oembed",
    "urls": [
        r"^https?://shoudio\.com/.+$",
        r"^https?://shoud\.io/.+$",
    ],
}

sketchfab = {
    "endpoint": "https://sketchfab.com/oembed",
    "urls": [
        r"^https?://sketchfab\.com/show/.+$",
        r"^https?://sketchfab\.com/models/.+$",
        r"^https?://sketchfab\.com/3d-models/.+$",
    ],
}

skitch = {
    "endpoint": "http://skitch.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?skitch\.com/.+$",
        r"^http://skit\.ch/.+$",
    ],
}

slideshare = {
    "endpoint": "https://www.slideshare.net/api/oembed/2",
    "urls": [
        r"^https?://www\.slideshare\.net/.+$",
    ],
}


smugmug = {
    "endpoint": "https://api.smugmug.com/services/oembed/",
    "urls": [
        r"^https?://(?:www\.)?smugmug\.com/[^#?/]+/.+$",
    ],
}


soundcloud = {
    "endpoint": "https://soundcloud.com/oembed",
    "urls": [
        r"^https://soundcloud\.com/.+$",
    ],
}


speakerdeck = {
    "endpoint": "https://speakerdeck.com/oembed.{format}",
    "urls": [
        r"^https?://speakerdeck\.com/.+$",
    ],
}


spotify = {
    "endpoint": "https://embed.spotify.com/oembed/",
    "urls": [
        r"^https?://open\.spotify\.com/.+$",
        r"^https?://spoti\.fi/.+$",
    ],
}


ted = {
    "endpoint": "https://www.ted.com/talks/oembed.{format}",
    "urls": [
        r"^https?://(?:www\.)?ted\.com/talks/.+$",
        r"^https?://(?:www\.)?ted\.com/talks/lang/[^#?/]+/.+$",
        r"^https?://(?:www\.)?ted\.com/index\.php/talks/.+$",
        r"^https?://(?:www\.)?ted\.com/index\.php/talks/lang/[^#?/]+/.+$",
    ],
}

tidal = {
    "endpoint": "https://oembed.tidal.com/",
    "urls": [r"^https?://(?:www\.)?tidal\.com/.+$"],
}


tumblr = {
    "endpoint": "https://www.tumblr.com/oembed/1.0",
    "urls": [
        r"^https?://.+?\.tumblr\.com/post/.+$",
    ],
}

twenty_three_hq = {
    "endpoint": "http://www.23hq.com/23/oembed",
    "urls": [
        r"^https?://(?:www\.)?23hq\.com/[^#?/]+/photo/.+$",
    ],
}

twitter = {
    "endpoint": "https://api.twitter.com/1/statuses/oembed.{format}",
    "urls": [
        r"^https?://twitter\.com/(?:#!)?[^#?/]+/status/.+$",
    ],
}


urtak = {
    "endpoint": "http://oembed.urtak.com/1/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?urtak\.com/.+$",
    ],
}

ustream = {
    "endpoint": "http://www.ustream.tv/oembed",
    "urls": [
        r"^https?://(?:www\.)?ustream\.tv/.+$",
        r"^https?://(?:www\.)?ustream\.com/.+$",
        r"^http://ustre\.am/.+$",
    ],
}


vhx_tv = {
    "endpoint": "http://vhx.tv/services/oembed.{format}",
    "urls": [
        r"^https?://(?:www\.)?vhx\.tv/.+$",
    ],
}


videojug = {
    "endpoint": "http://www.videojug.com/oembed.{format}",
    "urls": [
        r"^https?://(?:[-\w]+\.)?videojug\.com/film/.+$",
        r"^https?://(?:[-\w]+\.)?videojug\.com/payer/.+$",
        r"^https?://(?:[-\w]+\.)?videojug\.com/interview/.+$",
    ],
}


viddler = {
    "endpoint": "https://www.viddler.com/oembed/",
    "urls": [
        r"^https?://[-\w]+\.viddler\.com/v/.+$",
        r"^https?://[-\w]+\.viddler\.com/explore/.+$",
    ],
}

vidyard = {
    "endpoint": "https://api.vidyard.com/dashboard/v1.1/oembed",
    "urls": [
        r"^https?://play\.vidyard\.com/.+$",
        r"^https?://embed\.vidyard\.com/.+$",
        r"^https?://share\.vidyard\.com/.+$",
        r"^https?://.+?\.hubs\.vidyard\.com/.+$",
    ],
}

vimeo = {
    "endpoint": "https://www.vimeo.com/api/oembed.{format}",
    "urls": [
        r"^https?://(?:www\.)?vimeo\.com/.+$",
        r"^https?://player\.vimeo\.com/.+$",
    ],
}

vzaar = {
    "endpoint": "http://vzaar.com/api/videos/{1}.{format}",
    "urls": [
        r"^http://(?:www\.)?vzaar\.com/videos/([^#?/]+)(?:.+)?$",
        r"^http://www\.vzaar\.tv/([^#?/]+)(?:.+)?$",
        r"^http://vzaar\.tv/([^#?/]+)(?:.+)?$",
        r"^http://vzaar\.me/([^#?/]+)(?:.+)?$",
        r"^http://[-\w]+\.vzaar\.me/([^#?/]+)(?:.+)?$",
    ],
}


wistia = {
    "endpoint": "http://fast.wistia.com/oembed.{format}",
    "urls": [
        r"^https?://([^/]+\.)?(wistia.com|wi.st)/(medias|embed)/.+$",
    ],
}

wordpress = {
    "endpoint": "https://wordpress.tv/oembed/",
    "urls": [
        r"^https?://wordpress\.tv/.+$",
    ],
}

yandex = {
    "endpoint": "https://video.yandex.ru/oembed.{format}",
    "urls": [
        r"^https?://video\.yandex\.ru/users/[^#?/]+/view/.+$",
    ],
}


yfrog = {
    "endpoint": "http://www.yfrog.com/api/oembed",
    "urls": [
        r"^https?://(?:www\.)?yfrog\.com/.+$",
        r"^https?://(?:www\.)?yfrog\.us/.+$",
    ],
}

youtube = {
    "endpoint": "https://www.youtube.com/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?youtube\.com/watch.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/v/.+$",
        r"^https?://youtu\.be/.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/user/.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/[^#?/]+#[^#?/]+/.+$",
        r"^https?://m\.youtube\.com/index.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/profile.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/view_play_list.+$",
        r"^https?://(?:[-\w]+\.)?youtube\.com/playlist.+$",
    ],
}


all_providers = [
    animoto,
    app_net,
    audioboom,
    bambuser,
    blip_tv,
    cacoo,
    chirb,
    circuitlab,
    clickthrough,
    clikthrough,
    collegehumor,
    coub,
    crowd_ranking,
    dailymile,
    dailymotion,
    datastudio,
    deviantart,
    dipdive,
    dipity,
    dotsub,
    etsy,
    five_hundred_px,
    five_min,
    flickr,
    funny_or_die,
    geograph_gg,
    geograph_uk,
    github_gist,
    gmep,
    hlipp,
    huffduffer,
    hulu,
    ifixit,
    ifttt,
    issuu,
    justin_tv,
    kickstarter,
    kinomap,
    major_league_gaming,
    meetup,
    minoto,
    mixcloud,
    mobypicture,
    nfb,
    official_fm,
    opera,
    photobucket,
    pinterest,
    polldaddy,
    polleverywhere,
    qik,
    rdio,
    reddit,
    revision3,
    roomshare,
    sapo,
    screenr,
    scribd,
    shoudio,
    sketchfab,
    skitch,
    slideshare,
    smugmug,
    soundcloud,
    speakerdeck,
    spotify,
    ted,
    tidal,
    tumblr,
    twenty_three_hq,
    twitter,
    urtak,
    ustream,
    vhx_tv,
    viddler,
    videojug,
    vidyard,
    vimeo,
    vzaar,
    wistia,
    wordpress,
    yandex,
    yfrog,
    youtube,
]
