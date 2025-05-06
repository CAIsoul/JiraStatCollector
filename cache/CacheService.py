import redis
import json
from functools import wraps
from datetime import timedelta

class CacheService:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    def get(self, key):
        data = self.redis.get(key)  
        if data:
            return json.loads(data)
        return None

    def set(self, key, value, ttl=3600):
        self.redis.set(key, json.dumps(value), ex=ttl)

    def delete(self, key):
        self.redis.delete(key)

    def cache(self, ttl=3600):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{args}:{kwargs}"

                cached_data = self.get(cache_key)
                if cached_data:
                    return cached_data
                
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator

cache_service = CacheService()
