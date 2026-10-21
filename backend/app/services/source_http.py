"""HTTP access to the official sites, shared by the download script and the change watcher.

TLS is verified against the operating system's root store (not certifi). The Consejería server omits its Let's
Encrypt chain (YR2 → ISRG Root YR), so scripts/certs ships those two public certificates as intermediates;
partial-chain trust is disabled, so every connection must still end at ISRG Root X1. Only https URLs and https
redirects are followed, and a response is capped in size.
"""
import ssl
import urllib.request
from pathlib import Path

EXTRA_CHAIN = Path(__file__).resolve().parents[2] / "scripts" / "certs" / "lets-encrypt-yr2-chain.pem"
USER_AGENT = "Avizum source watch (+https://github.com/AlexisVences/abogadazo)"
MAX_PDF_BYTES = 100 * 1024 * 1024  # the largest official PDF is a few MB; anything near this is not a law
MAX_PAGE_BYTES = 5 * 1024 * 1024


def ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_verify_locations(cafile=str(EXTRA_CHAIN))
    return context


class HttpsOnlyRedirects(urllib.request.HTTPRedirectHandler):
    """Follow redirects, but never to plain http: a downgrade would let someone on the path swap the document."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.lower().startswith("https://"):
            raise ValueError(f"redirección a una URL no https rechazada: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url: str, *, max_bytes: int = MAX_PAGE_BYTES, timeout: float = 60, context: ssl.SSLContext | None = None) -> bytes:
    if not url.lower().startswith("https://"):
        raise ValueError(f"la URL debe ser https: {url}")
    opener = urllib.request.build_opener(HttpsOnlyRedirects, urllib.request.HTTPSHandler(context=context or ssl_context()))
    with opener.open(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"la respuesta supera {max_bytes // 2**20} MB: {url}")
    return data
