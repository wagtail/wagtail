
app_net = {
    "endpoint": "https://alpha-api.app.net/oembed",
    "urls": [
        r"^https?://alpha\.app\.net/[^#?/]+/post/.+$",
        r"^https?://photos\.app\.net/[^#?/]+/.+$",
    ],
}





clickthrough = {
    "endpoint": "http://clikthrough.com/services/oembed",
    "urls": [
        r"^https?://(?:[-\w]+\.)?clikthrough\.com/.+$",
    ],
}


collegehumor = {
    "endpoint": "http://www.collegehumor.com/oembed.{format}",
    "urls": [
        r"^http://(?:www\.)?collegehumor\.com/video/.+$",
        r"^http://(?:www\.)?collegehumor\.com/video:.+$",
    ],
}

five_hundred_px = {
    "endpoint": "https://500px.com/photo/{1}/oembed.{format}",
    "urls": [
        r"^https?://500px\.com/photo/([^#?/]+)(?:.+)?$",
    ],
}

mobypicture = {
    "endpoint": "http://api.mobypicture.com/oEmbed",
    "urls": [
        r"^https?://(?:www\.)?mobypicture\.com/user/[^#?/]+/view/.+$",
        r"^https?://(?:www\.)?moby\.to/.+$",
    ],
}

official_fm = {
    "endpoint": "http://official.fm/services/oembed.{format}",
    "urls": [
        r"^https?://official\.fm/.+$",
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

shoudio = {
    "endpoint": "https://shoudio.com/api/oembed",
    "urls": [
        r"^https?://shoudio\.com/.+$",
        r"^https?://shoud\.io/.+$",
    ],
}


skitch = {
    "endpoint": "http://skitch.com/oembed",
    "urls": [
        r"^https?://(?:www\.)?skitch\.com/.+$",
        r"^http://skit\.ch/.+$",
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


yandex = {
    "endpoint": "https://video.yandex.ru/oembed.{format}",
    "urls": [
        r"^https?://video\.yandex\.ru/users/[^#?/]+/view/.+$",
    ],
}






all_providers = [
    app_net,
    clickthrough,
    collegehumor,
    five_hundred_px,
    mobypicture,
    official_fm,
    photobucket,
    pinterest,
    shoudio,
    skitch,
    videojug,
    vzaar,
    yandex,
]
