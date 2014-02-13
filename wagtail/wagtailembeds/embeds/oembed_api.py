import os, re
import urllib2, urllib
from datetime import datetime
import json

class NotImplementedOembedException(Exception):
    pass

ENDPOINTS = {}

def get_embed_oembed(url, max_width=None):
    provider = None
    for endpoint in ENDPOINTS.keys():
        for pattern in ENDPOINTS[endpoint]:
            if re.match(pattern, url):
                provider = endpoint
                break
    if not provider:
        raise NotImplementedOembedException
    params = {'url': url, 'format': 'json',  }
    if max_width:
        params['maxwidth'] = max_width
    req = provider+'?' +urllib.urlencode(params)
    request = urllib2.Request(req)
    opener = urllib2.build_opener()         
    # Some provicers were not working without a user agent
    request.add_header('User-Agent','Mozilla/5.0')
    return json.loads(opener.open(request).read())
    
        
# Uses the public domain collection of oembed endpoints by Mathias Panzenbpeck (panzi)
# at https://github.com/panzi/oembedendpoints/blob/master/endpoints-regexp.json        

def load_oembed_endpoints():
    module_dir = os.path.dirname(__file__)  
    endpoints_path  = os.path.join(module_dir, 'endpoints.json')
    with open( endpoints_path) as f:
        endpoints = json.loads(f.read())
        
        for endpoint in endpoints.keys():
            endpoint_key = endpoint.replace('{format}', 'json')

            ENDPOINTS[endpoint_key]=[]
            for pattern in endpoints[endpoint]:
                ENDPOINTS[endpoint_key].append(re.compile(pattern))
    
                
        
load_oembed_endpoints()

        
                