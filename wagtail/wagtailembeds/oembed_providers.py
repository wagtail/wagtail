OEMBED_ENDPOINTS = {
    "https://speakerdeck.com/oembed.{format}": [
        "^http(?:s)?://speakerdeck\\.com/.+$"
    ],
    "https://alpha-api.app.net/oembed": [
        "^http(?:s)?://alpha\\.app\\.net/[^#?/]+/post/.+$",
        "^http(?:s)?://photos\\.app\\.net/[^#?/]+/.+$"
    ],
    "http://www.youtube.com/oembed": [
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/watch.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/v/.+$",
        "^http(?:s)?://youtu\\.be/.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/user/.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/[^#?/]+#[^#?/]+/.+$",
        "^http(?:s)?://m\\.youtube\\.com/index.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/profile.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/view_play_list.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?youtube\\.com/playlist.+$"
    ],
    "http://backend.deviantart.com/oembed": [
        "^http://(?:[-\\w]+\\.)?deviantart\\.com/art/.+$",
        "^http://fav\\.me/.+$",
        "^http://sta\\.sh/.+$",
        "^http://(?:[-\\w]+\\.)?deviantart\\.com/[^#?/]+#/d.+$"
    ],
    "http://blip.tv/oembed/": [
        "^http://[-\\w]+\\.blip\\.tv/.+$"
    ],
    "http://www.dailymotion.com/api/oembed/": [
        "^http://[-\\w]+\\.dailymotion\\.com/.+$"
    ],
    "http://www.flickr.com/services/oembed/": [
        "^http://[-\\w]+\\.flickr\\.com/photos/.+$",
        "^http://flic\\.kr\\.com/.+$"
    ],
    "http://www.hulu.com/api/oembed.{format}": [
        "^http://www\\.hulu\\.com/watch/.+$"
    ],
    "http://www.nfb.ca/remote/services/oembed/": [
        "^http://(?:[-\\w]+\\.)?nfb\\.ca/film/.+$"
    ],
    "http://qik.com/api/oembed.{format}": [
        "^http://qik\\.com/.+$",
        "^http://qik\\.ly/.+$"
    ],
    "http://revision3.com/api/oembed/": [
        "^http://[-\\w]+\\.revision3\\.com/.+$"
    ],
    "http://www.scribd.com/services/oembed": [
        "^http://[-\\w]+\\.scribd\\.com/.+$"
    ],
    "http://www.viddler.com/oembed/": [
        "^http://[-\\w]+\\.viddler\\.com/v/.+$",
        "^http://[-\\w]+\\.viddler\\.com/explore/.+$"
    ],
    "http://www.vimeo.com/api/oembed.{format}": [
        "^http(?:s)?://(?:www\\.)?vimeo\\.com/.+$",
        "^http(?:s)?://player\\.vimeo\\.com/.+$"
    ],
    "http://dotsub.com/services/oembed": [
        "^http://dotsub\\.com/view/.+$"
    ],
    "http://www.yfrog.com/api/oembed": [
        "^http(?:s)?://(?:www\\.)?yfrog\\.com/.+$",
        "^http(?:s)?://(?:www\\.)?yfrog\\.us/.+$"
    ],
    "http://clikthrough.com/services/oembed": [
        "^http(?:s)?://(?:[-\\w]+\\.)?clikthrough\\.com/.+$"
    ],
    "http://www.kinomap.com/oembed": [
        "^http://[-\\w]+\\.kinomap\\.com/.+$"
    ],
    "https://photobucket.com/oembed": [
        "^http://(?:[-\\w]+\\.)?photobucket\\.com/albums/.+$",
        "^http://(?:[-\\w]+\\.)?photobucket\\.com/groups/.+$"
    ],
    "http://api.instagram.com/oembed": [
        "^http://instagr\\.am/p/.+$",
        "^http[s]?://instagram\\.com/p/.+$"
    ],
    "https://www.slideshare.net/api/oembed/2": [
        "^http://www\\.slideshare\\.net/.+$"
    ],
    "http://tv.majorleaguegaming.com/oembed": [
        "^http://mlg\\.tv/.+$",
        "^http://tv\\.majorleaguegaming\\.com/.+$"
    ],
    "http://my.opera.com/service/oembed": [
        "^http://my\\.opera\\.com/.+$"
    ],
    "http://skitch.com/oembed": [
        "^http(?:s)?://(?:www\\.)?skitch\\.com/.+$",
        "^http://skit\\.ch/.+$"
    ],
    "https://api.twitter.com/1/statuses/oembed.{format}": [
        "^http(?:s)?://twitter\\.com/(?:#!)?[^#?/]+/status/.+$"
    ],
    "https://soundcloud.com/oembed": [
        "^https://soundcloud\\.com/[^#?/]+/.+$"
    ],
    "http://www.collegehumor.com/oembed.{format}": [
        "^http://(?:www\\.)?collegehumor\\.com/video/.+$",
        "^http://(?:www\\.)?collegehumor\\.com/video:.+$"
    ],
    "http://www.polleverywhere.com/services/oembed/": [
        "^http://www\\.polleverywhere\\.com/polls/.+$",
        "^http://www\\.polleverywhere\\.com/multiple_choice_polls/.+$",
        "^http://www\\.polleverywhere\\.com/free_text_polls/.+$"
    ],
    "http://www.ifixit.com/Embed": [
        "^http://www\\.ifixit\\.com/[^#?/]+/[^#?/]+/.+$"
    ],
    "http://api.smugmug.com/services/oembed/": [
        "^http(?:s)?://(?:www\\.)?smugmug\\.com/[^#?/]+/.+$"
    ],
    "https://github.com/api/oembed": [
        "^http(?:s)?://gist\\.github\\.com/.+$"
    ],
    "http://animoto.com/services/oembed": [
        "^http://animoto\\.com/play/.+$"
    ],
    "http://www.rdio.com/api/oembed": [
        "^http://(?:wwww\\.)?rdio\\.com/people/[^#?/]+/playlists/.+$",
        "^http://[-\\w]+\\.rdio\\.com/artist/[^#?/]+/album/.+$"
    ],
    "http://api.5min.com/oembed.{format}": [
        "^http://www\\.5min\\.com/video/.+$"
    ],
    "http://500px.com/photo/{1}/oembed.{format}": [
        "^http://500px\\.com/photo/([^#?/]+)(?:.+)?$"
    ],
    "http://api.dipdive.com/oembed.{format}": [
        "^http://[-\\w]+\\.dipdive\\.com/media/.+$"
    ],
    "http://video.yandex.ru/oembed.{format}": [
        "^http://video\\.yandex\\.ru/users/[^#?/]+/view/.+$"
    ],
    "http://www.mixcloud.com/oembed/": [
        "^http://www\\.mixcloud\\.com/oembed/[^#?/]+/.+$"
    ],
    "http://www.kickstarter.com/services/oembed": [
        "^http(?:s)://[-\\w]+\\.kickstarter\\.com/projects/.+$"
    ],
    "http://coub.com/api/oembed.{format}": [
        "^http(?:s)?://coub\\.com/view/.+$",
        "^http(?:s)?://coub\\.com/embed/.+$"
    ],
    "http://www.screenr.com/api/oembed.{format}": [
        "^http://www\\.screenr\\.com/.+$"
    ],
    "http://www.funnyordie.com/oembed.{format}": [
        "^http://www\\.funnyordie\\.com/videos/.+$"
    ],
    "http://fast.wistia.com/oembed.{format}": [
        "^http://[-\\w]+\\.wista\\.com/medias/.+$"
    ],
    "http://www.ustream.tv/oembed": [
        "^http(?:s)?://(?:www\\.)?ustream\\.tv/.+$",
        "^http(?:s)?://(?:www\\.)?ustream\\.com/.+$",
        "^http://ustre\\.am/.+$"
    ],
    "http://wordpress.tv/oembed/": [
        "^http://wordpress\\.tv/.+$"
    ],
    "http://polldaddy.com/oembed/": [
        "^http(?:s)?://(?:[-\\w]+\\.)?polldaddy\\.com/.+$"
    ],
    "http://api.bambuser.com/oembed.{format}": [
        "^http://bambuser\\.com/channel/[^#?/]+/broadcast/.+$",
        "^http://bambuser\\.com/channel/.+$",
        "^http://bambuser\\.com/v/.+$"
    ],
    "http://www.ted.com/talks/oembed.{format}": [
        "^http(?:s)?://(?:www\\.)?ted\\.com/talks/.+$",
        "^http(?:s)?://(?:www\\.)?ted\\.com/talks/lang/[^#?/]+/.+$",
        "^http(?:s)?://(?:www\\.)?ted\\.com/index\\.php/talks/.+$",
        "^http(?:s)?://(?:www\\.)?ted\\.com/index\\.php/talks/lang/[^#?/]+/.+$"
    ],
    "http://chirb.it/oembed.{format}": [
        "^http://chirb\\.it/.+$"
    ],
    "https://www.circuitlab.com/circuit/oembed/": [
        "^http(?:s)?://(?:www\\.)?circuitlab\\.com/circuit/.+$"
    ],
    "http://api.geograph.org.uk/api/oembed": [
        "^http://(?:[-\\w]+\\.)?geograph\\.org\\.uk/.+$",
        "^http://(?:[-\\w]+\\.)?geograph\\.co\\.uk/.+$",
        "^http://(?:[-\\w]+\\.)?geograph\\.ie/.+$"
    ],
    "http://geo.hlipp.de/restapi.php/api/oembed": [
        "^http://geo-en\\.hlipp\\.de/.+$",
        "^http://geo\\.hlipp\\.de/.+$",
        "^http://germany\\.geograph\\.org/.+$"
    ],
    "http://www.geograph.org.gg/api/oembed": [
        "^http://(?:[-\\w]+\\.)?geograph\\.org\\.gg/.+$",
        "^http://(?:[-\\w]+\\.)?geograph\\.org\\.je/.+$",
        "^http://channel-islands\\.geograph\\.org/.+$",
        "^http://channel-islands\\.geographs\\.org/.+$",
        "^http://(?:[-\\w]+\\.)?channel\\.geographs\\.org/.+$"
    ],
    "http://vzaar.com/api/videos/{1}.{format}": [
        "^http://(?:www\\.)?vzaar\\.com/videos/([^#?/]+)(?:.+)?$",
        "^http://www\\.vzaar\\.tv/([^#?/]+)(?:.+)?$",
        "^http://vzaar\\.tv/([^#?/]+)(?:.+)?$",
        "^http://vzaar\\.me/([^#?/]+)(?:.+)?$",
        "^http://[-\\w]+\\.vzaar\\.me/([^#?/]+)(?:.+)?$"
    ],
    "http://api.minoto-video.com/services/oembed.{format}": [
        "^http://api\\.minoto-video\\.com/publishers/[^#?/]+/videos/.+$",
        "^http://dashboard\\.minoto-video\\.com/main/video/details/.+$",
        "^http://embed\\.minoto-video\\.com/.+$"
    ],
    "http://www.videojug.com/oembed.{format}": [
        "^http(?:s)?://(?:[-\\w]+\\.)?videojug\\.com/film/.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?videojug\\.com/payer/.+$",
        "^http(?:s)?://(?:[-\\w]+\\.)?videojug\\.com/interview/.+$"
    ],
    "http://videos.sapo.pt/oembed": [
        "^http(?:s)?://videos\\.sapo\\.pt/.+$"
    ],
    "http://vhx.tv/services/oembed.{format}": [
        "^http(?:s)?://(?:www\\.)?vhx\\.tv/.+$"
    ],
    "http://api.justin.tv/api/embed/from_url.{format}": [
        "^http(?:s)?://(?:www\\.)?justin\\.tv/.+$"
    ],
    "http://official.fm/services/oembed.{format}": [
        "^http(?:s)?://official\\.fm/.+$"
    ],
    "http://huffduffer.com/oembed": [
        "^http(?:s)?://(?:www\\.)?huffduffer\\.com/[^#?/]+/.+$"
    ],
    "https://embed.spotify.com/oembed/": [
        "^http(?:s)?://open\\.spotify\\.com/.+$",
        "^http(?:s)?://spoti\\.fi/.+$"
    ],
    "http://shoudio.com/api/oembed": [
        "^http://shoudio\\.com/.+$",
        "^http://shoud\\.io/.+$"
    ],
    "http://api.mobypicture.com/oEmbed": [
        "^http(?:s)?://(?:www\\.)?mobypicture\\.com/user/[^#?/]+/view/.+$",
        "^http(?:s)?://(?:www\\.)?moby\\.to/.+$"
    ],
    "http://www.23hq.com/23/oembed": [
        "^http(?:s)?://(?:www\\.)?23hq\\.com/[^#?/]+/photo/.+$"
    ],
    "http://gmep.org/oembed.{format}": [
        "^http(?:s)?://(?:www\\.)?gmep\\.org/.+$",
        "^http(?:s)?://gmep\\.imeducate\\.com/.+$"
    ],
    "http://oembed.urtak.com/1/oembed": [
        "^http(?:s)?://(?:[-\\w]+\\.)?urtak\\.com/.+$"
    ],
    "http://cacoo.com/oembed.{format}": [
        "^http(?:s)?://cacoo\\.com/.+$"
    ],
    "http://api.dailymile.com/oembed": [
        "^http(?:s)?://(?:www\\.)?dailymile\\.com/people/[^#?/]+/entries/.+$"
    ],
    "http://www.dipity.com/oembed/timeline/": [
        "^http(?:s)?://(?:www\\.)?dipity\\.com/timeline/.+$",
        "^http(?:s)?://(?:www\\.)?dipity\\.com/voaweb/.+$"
    ],
    "https://sketchfab.com/oembed": [
        "^http(?:s)?://sketchfab\\.com/show/.+$"
    ],
    "https://api.meetup.com/oembed": [
        "^http(?:s)?://(?:www\\.)?meetup\\.com/.+$",
        "^http(?:s)?://(?:www\\.)?meetup\\.ps/.+$"
    ],
    "https://roomshare.jp/oembed.{format}": [
        "^http(?:s)?://(?:www\\.)?roomshare\\.jp/(?:en/)?post/.+$"
    ],
    "http://crowdranking.com/api/oembed.{format}": [
        "^http(?:s)?://crowdranking\\.com/crowdrankings/.+$",
        "^http(?:s)?://crowdranking\\.com/rankings/.+$",
        "^http(?:s)?://crowdranking\\.com/topics/.+$",
        "^http(?:s)?://crowdranking\\.com/widgets/.+$",
        "^http(?:s)?://crowdranking\\.com/r/.+$"
    ],
    "http://openapi.etsy.com/svc/oembed/": [
        "^http(?:s)?://(?:www\\.)?etsy\\.com/listing/.+$"
    ],
    "https://audioboo.fm/publishing/oembed.{format}": [
        "^http(?:s)?://audioboo\\.fm/boos/.+$"
    ],
    "http://demo.clikthrough.com/services/oembed/": [
        "^http(?:s)?://demo\\.clikthrough\\.com/theater/video/.+$"
    ],
    "http://www.ifttt.com/oembed/": [
        "^http(?:s)?://ifttt\\.com/recipes/.+$"
    ],

    # Added 11th December 2014 - http://developers.issuu.com/api/oembed.html
    "http://issuu.com/oembed": [
        "^http(?:s)?://(?:www\\.)?issuu\\.com/[^#?/]+/docs/.+$"
    ],
}


# Compile endpoints into regular expression objects
import re


def compile_endpoints():
    endpoints = {}
    for endpoint in OEMBED_ENDPOINTS.keys():
        endpoint_key = endpoint.replace('{format}', 'json')

        endpoints[endpoint_key] = []
        for pattern in OEMBED_ENDPOINTS[endpoint]:
            endpoints[endpoint_key].append(re.compile(pattern))

    return endpoints

OEMBED_ENDPOINTS_COMPILED = compile_endpoints()


def get_oembed_provider(url):
    for endpoint in OEMBED_ENDPOINTS_COMPILED.keys():
        for pattern in OEMBED_ENDPOINTS_COMPILED[endpoint]:
            if re.match(pattern, url):
                return endpoint

    return
