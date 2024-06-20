import requests

all_providers = [
    {
        "endpoint": "https://animoto.com/services/oembed",
        "urls": [r"^https?://animoto\.com/play/.+$"],
    },
    {
        "endpoint": "https://alpha-api.app.net/oembed",
        "urls": [r"^https?://alpha\.app\.net/[^#?/]+/post/.+$", r"^https?://photos\.app\.net/[^#?/]+/.+$"],
    },
    {
        "endpoint": "https://audioboom.com/publishing/oembed.{format}",
        "urls": [r"^https?://audioboom\.com/boos/.+$", r"^https?://audioboom\.com/posts/.+$"],
    },
    {
        "endpoint": "http://api.bambuser.com/oembed.{format}",
        "urls": [r"^http://bambuser\.com/channel/[^#?/]+/broadcast/.+$", r"^http://bambuser\.com/channel/.+$", r"^http://bambuser\.com/v/.+$"],
    },
    {
        "endpoint": "http://blip.tv/oembed/",
        "urls": [r"^http://[-\w]+\.blip\.tv/.+$"],
    },
    {
        "endpoint": "http://vzaar.com/api/videos/{1}.{format}",
        "urls": [
            r"^http://(?:www\.)?vzaar\.com/videos/([^#?/]+)(?:.+)?$",
            r"^http://www\.vzaar\.tv/([^#?/]+)(?:.+)?$",
            r"^http://vzaar\.tv/([^#?/]+)(?:.+)?$",
            r"^http://vzaar\.me/([^#?/]+)(?:.+)?$",
            r"^http://[-\w]+\.vzaar\.me/([^#?/]+)(?:.+)?$",
        ],
    },
    {
        "endpoint": "http://fast.wistia.com/oembed.{format}",
        "urls": [r"^https?://([^/]+\.)?(wistia.com|wi.st)/(medias|embed)/.+$"],
    },
    {
        "endpoint": "https://wordpress.tv/oembed/",
        "urls": [r"^https?://wordpress\.tv/.+$"],
    },
    {
        "endpoint": "https://video.yandex.ru/oembed.{format}",
        "urls": [r"^https?://video\.yandex\.ru/users/[^#?/]+/view/.+$"],
    },
    {
        "endpoint": "http://www.yfrog.com/api/oembed",
        "urls": [r"^https?://(?:www\.)?yfrog\.com/.+$", r"^https?://(?:www\.)?yfrog\.us/.+$"],
    },
    
]

def check_providers(providers):
    dead_providers = []

    for provider in providers:
        endpoint = provider['endpoint']
        if '{format}' in endpoint:
            endpoint = endpoint.replace("{format}", "json")
        if '{1}' in endpoint:
            endpoint = endpoint.replace("{1}", "1")
        
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code != 200:
                dead_providers.append(provider)
        except requests.exceptions.RequestException:
            dead_providers.append(provider)
    
    return dead_providers

dead_providers = check_providers(all_providers)
print("Providers with endpoints not opening or dead:")
for provider in dead_providers:
    print(provider)
