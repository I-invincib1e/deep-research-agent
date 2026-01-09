"""File-based caching layer for the Research Agent."""

import os
import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("Cache")

CACHE_DIR = Path(__file__).parent / ".cache"
DEFAULT_TTL = 3600  # 1 hour


def _get_cache_path(key: str) -> Path:
    """Generate cache file path from key."""
    key_hash = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{key_hash}.json"


def get_cached(key: str) -> Optional[Any]:
    """Retrieve cached data if it exists and hasn't expired."""
    cache_path = _get_cache_path(key)
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        if time.time() > cached.get('expires_at', 0):
            logger.debug(f"Cache expired for key: {key[:50]}...")
            cache_path.unlink(missing_ok=True)
            return None
        
        logger.info(f"📦 Cache HIT for: {key[:50]}...")
        return cached.get('data')
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


def set_cached(key: str, data: Any, ttl_seconds: int = DEFAULT_TTL) -> None:
    """Store data in cache with expiration time."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _get_cache_path(key)
    
    try:
        cached = {
            'key': key,
            'data': data,
            'created_at': time.time(),
            'expires_at': time.time() + ttl_seconds
        }
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cached, f, ensure_ascii=False)
        logger.debug(f"📥 Cached: {key[:50]}...")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


def clear_expired() -> int:
    """Remove all expired cache entries. Returns count of removed files."""
    if not CACHE_DIR.exists():
        return 0
    
    removed = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            if time.time() > cached.get('expires_at', 0):
                cache_file.unlink()
                removed += 1
        except:
            pass
    
    if removed:
        logger.info(f"🗑️ Cleared {removed} expired cache entries")
    return removed


def clear_all() -> int:
    """Remove all cache entries. Returns count of removed files."""
    if not CACHE_DIR.exists():
        return 0
    
    removed = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            cache_file.unlink()
            removed += 1
        except:
            pass
    
    logger.info(f"🗑️ Cleared all {removed} cache entries")
    return removed
