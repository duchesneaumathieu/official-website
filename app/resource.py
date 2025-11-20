import os, string, functools, markdown2
from pathlib import Path, PurePosixPath
from fastapi import Request
from cachetools import LRUCache
from .config import Settings

html_cache = LRUCache(**Settings.cache.html_cache)
markdown_cache = LRUCache(**Settings.cache.markdown_cache)

class PathTraversalAttack(Exception):
    pass

@functools.lru_cache(**Settings.cache.sanitize_url_path)
def sanitize_url_path(url_path: str) -> PurePosixPath:

    if len(url_path) > Settings.url_rules.max_length:
        raise ValueError("URL is too long")
    
    if any(s in url_path for s in Settings.url_rules.forbidden_strings):
        raise PathTraversalAttack()
    
    # Silently removing not allowed characters
    url_path = "".join(c for c in url_path if c in Settings.url_rules.allowed_characters).lower()
    
    # Silently removing forbidden nodes
    nodes = [node for node in url_path.split('/') if node not in Settings.url_rules.forbidden_nodes]
    
    if len(nodes) > Settings.url_rules.max_depth:
        raise ValueError("URL is too deep")
    
    return PurePosixPath(*nodes)

def secure_resource_resolve(url_path: Path, strict: bool = False) -> Path:
    # Can raise FileNotFoundError when strict=True
    resolved = (Settings.paths.markdown_dir / url_path).resolve(strict=strict)
    
    try:
        relative = resolved.relative_to(Settings.paths.markdown_dir)
    except ValueError:
        raise PathTraversalAttack(url_path)
    
    if Path(url_path) != relative:
        raise PathTraversalAttack(url_path)
    
    return resolved

def get_resource_path(url_path: Path, swp: bool = False) -> Path:
    # First verification before testing if the resource is an index page
    resource = secure_resource_resolve(url_path, strict=False)
    relative_path = url_path / "index.md" if resource.is_dir() else url_path.with_suffix(".md")
    
    if swp:
        # relative_path = f"{relative_path.parent}/.{relative_path.name}.swp"
        relative_path = relative_path.with_name("." + relative_path.name + ".swp")
    
    # Second verification to avoid any abuse of the "{file}.md" and
    # ".{file}.md.swp" modifiers. Can also raise FileNotFoundError.
    return secure_resource_resolve(relative_path, strict=True)

def mtime_lru_cache(cache):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self):
            mtime = os.path.getmtime(self.path)
            if self.path in cache:
                cached_mtime, output = cache[self.path]
                if mtime == cached_mtime:
                    return output
                else:
                    del cache[self.path]
            output = func(self)
            cache[self.path] = (mtime, output)
            return output
        return wrapper
    return decorator

class Resource:
    def __init__(self, url_path: Path):
        self.url_path = sanitize_url_path(str(url_path))
        
        try:
            self.path = get_resource_path(self.url_path)
        except FileNotFoundError:
            self.path = None
    
    def exists(self) -> bool:
        return self.path is not None
    
    @mtime_lru_cache(markdown_cache)
    def markdown(self) -> str:
        if not self.exists:
            raise FileNotFoundError()
        
        with open(self.path, 'r') as f:
            return f.read()
    
    @mtime_lru_cache(html_cache)
    def html(self) -> dict:
        markdown = self.markdown()
        html = markdown2.markdown(markdown, extras=Settings.markdown.extras)
        
        if html.metadata.get("scope") != "public":
            raise PermissionError("Ressource is not publicly available.")
        
        return {"html": html, **html.metadata}
