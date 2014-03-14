import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

session = CacheControl(
    requests.Session(),
    cache=FileCache(".web_cache")
)

