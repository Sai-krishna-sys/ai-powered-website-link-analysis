import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse, urlunparse

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "169.254.169.254",
}


class URLValidationError(ValueError):
    pass


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        return False
    if addr.is_multicast or addr.is_reserved or addr.is_unspecified:
        return False
    # cloud metadata
    if str(addr) == "169.254.169.254":
        return False
    return True


def validate_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise URLValidationError("URL is required")
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise URLValidationError("Only HTTP and HTTPS URLs are allowed")
    if not parsed.hostname:
        raise URLValidationError("URL must include a hostname")
    if parsed.port not in ALLOWED_PORTS:
        raise URLValidationError("Unsupported port")
    host = parsed.hostname.lower()
    if host in BLOCKED_HOSTS:
        raise URLValidationError("Internal or metadata endpoint is not allowed")
    # resolve DNS
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise URLValidationError("DNS resolution failed") from exc
    if not infos:
        raise URLValidationError("DNS resolution failed")
    for info in infos:
        ip = info[4][0]
        if not _is_public_ip(ip):
            raise URLValidationError("Resolved address is not publicly accessible")
    # normalize
    return urlunparse(parsed)


# aliases
def validate_http_url(url: str) -> str:
    return validate_url(url)


def is_safe_url(url: str) -> bool:
    try:
        validate_url(url)
        return True
    except URLValidationError:
        return False
