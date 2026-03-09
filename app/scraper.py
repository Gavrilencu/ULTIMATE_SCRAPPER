# -*- coding: utf-8 -*-
"""
Extragere date: suport pentru mai multe biblioteci.
- parsel: XPath + CSS, rapid, HTML static
- beautifulsoup: CSS (XPath prin parsel pe același HTML)
- selenium: descărcare pagină cu JavaScript, apoi extragere cu parsel
"""
import re
import requests
from parsel import Selector
from app.models import JobVariable


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

LIBRARIES = {
    "parsel": "Parsel (XPath + CSS, rapid)",
    "beautifulsoup": "BeautifulSoup (CSS, parser alternativ)",
    "selenium": "Selenium (pagini cu JavaScript)",
}


def format_value(value: str, format_type: str) -> str:
    if not value or not format_type or format_type == "none":
        return (value or "").strip()
    value = value.strip()
    if format_type == "strip_percent":
        return re.sub(r"%\s*$", "", value).strip()
    if format_type == "strip_currency":
        return re.sub(r"[^\d.,\-]", "", value).strip().replace(",", ".")
    if format_type == "strip_spaces":
        return re.sub(r"\s+", " ", value).strip()
    if format_type == "integer":
        return re.sub(r"[^\d\-]", "", value) or "0"
    if format_type == "decimal":
        return re.sub(r"[^\d.\-]", "", value).replace(",", ".") or "0"
    if format_type == "date_iso":
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", value)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = re.search(r"(\d{2})[./](\d{2})[./](\d{4})", value)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return value
    if format_type == "datetime_iso":
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})[\sT](\d{1,2}):(\d{2})", value)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4).zfill(2)}:{m.group(5)}:00"
        return value
    return value


def _fetch_requests(url: str, timeout: int = 30, proxy: str | None = None) -> tuple[str, str | None]:
    try:
        kwargs = {"headers": {"User-Agent": USER_AGENT}, "timeout": timeout}
        if proxy and (proxy := proxy.strip()):
            kwargs["proxies"] = {"http": proxy, "https": proxy}
        r = requests.get(url, **kwargs)
        r.raise_for_status()
        return r.text, None
    except requests.RequestException as e:
        return "", str(e)


def _fetch_selenium(url: str, timeout: int = 30, proxy: str | None = None) -> tuple[str, str | None]:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        return "", "Instalați selenium: pip install selenium (și ChromeDriver)"
    # Opțiuni compatibile Windows + Linux (headless)
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"user-agent={USER_AGENT}")
    if proxy and (proxy := proxy.strip()):
        host, port = _proxy_host(proxy), _proxy_port(proxy)
        if host:
            server = f"{host}:{port or 8080}"
            opts.add_argument(f"--proxy-server={server}")
    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        html = driver.page_source
        return html, None
    except Exception as e:
        # Fallback: Firefox (util pe Linux când Chrome/ChromeDriver lipsește)
        try:
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            opts_ff = FirefoxOptions()
            opts_ff.add_argument("--headless")
            if proxy and proxy.strip():
                opts_ff.set_preference("network.proxy.type", 1)
                opts_ff.set_preference("network.proxy.http", _proxy_host(proxy))
                opts_ff.set_preference("network.proxy.http_port", _proxy_port(proxy) or 80)
                opts_ff.set_preference("network.proxy.ssl", _proxy_host(proxy))
                opts_ff.set_preference("network.proxy.ssl_port", _proxy_port(proxy) or 443)
            driver_ff = webdriver.Firefox(options=opts_ff)
            driver_ff.set_page_load_timeout(timeout)
            driver_ff.get(url)
            html = driver_ff.page_source
            driver_ff.quit()
            return html, None
        except Exception:
            pass
        return "", str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def _proxy_host(proxy_url: str) -> str:
    """Extrage host din URL proxy (http://host:port sau http://user:pass@host:port)."""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(proxy_url if "://" in proxy_url else "http://" + proxy_url)
        return parsed.hostname or ""
    except Exception:
        return ""


def _proxy_port(proxy_url: str) -> int | None:
    """Extrage port din URL proxy."""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(proxy_url if "://" in proxy_url else "http://" + proxy_url)
        return parsed.port
    except Exception:
        return None


def fetch_page(url: str, library: str = "parsel", timeout: int = 30, proxy: str | None = None) -> tuple[str, str | None]:
    if library == "selenium":
        return _fetch_selenium(url, timeout, proxy=proxy)
    return _fetch_requests(url, timeout, proxy=proxy)


def _extract_parsel(html: str, variables: list) -> dict:
    selector = Selector(html)
    result = {}
    for v in variables:
        name = v.name
        if v.extract_type == "constant":
            result[name] = format_value(v.constant_value or "", v.format_type or "none")
            continue
        sel = (v.selector or "").strip()
        if not sel:
            result[name] = ""
            continue
        try:
            if v.extract_type == "xpath":
                nodes = selector.xpath(sel)
            else:
                nodes = selector.css(sel)
            text = " ".join(nodes.xpath("string()").getall()).strip() if nodes else ""
            result[name] = format_value(text, v.format_type or "none")
        except Exception:
            result[name] = ""
    return result


def _extract_beautifulsoup(html: str, variables: list) -> dict:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return _extract_parsel(html, variables)
    soup = BeautifulSoup(html, "lxml")
    result = {}
    for v in variables:
        name = v.name
        if v.extract_type == "constant":
            result[name] = format_value(v.constant_value or "", v.format_type or "none")
            continue
        sel = (v.selector or "").strip()
        if not sel:
            result[name] = ""
            continue
        try:
            if v.extract_type == "xpath":
                selector = Selector(html)
                nodes = selector.xpath(sel)
                text = " ".join(nodes.xpath("string()").getall()).strip() if nodes else ""
            else:
                elements = soup.select(sel)
                text = " ".join(e.get_text(strip=True) for e in elements) if elements else ""
            result[name] = format_value(text, v.format_type or "none")
        except Exception:
            result[name] = ""
    return result


def extract_from_page(html: str, variables: list, library: str = "parsel") -> dict:
    if library == "beautifulsoup":
        return _extract_beautifulsoup(html, variables)
    return _extract_parsel(html, variables)


def test_extract(url: str, library: str, selector_type: str, selector: str, timeout: int = 30) -> tuple[list[str], str | None]:
    """
    Extrage valorile pentru un singur selector (test).
    Returnează (lista de texte extrase, eroare sau None).
    """
    html, err = fetch_page(url, library=library, timeout=timeout)
    if err:
        return [], err
    selector = (selector or "").strip()
    if not selector:
        return [], "Introduceți un XPath sau selector CSS."
    try:
        if library == "beautifulsoup":
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                sel = Selector(html)
                if selector_type == "xpath":
                    nodes = sel.xpath(selector)
                else:
                    nodes = sel.css(selector)
                return [(" ".join(nodes.xpath("string()").getall()).strip()) if nodes else ""], None
            soup = BeautifulSoup(html, "lxml")
            if selector_type == "xpath":
                sel = Selector(html)
                nodes = sel.xpath(selector)
                texts = nodes.xpath("string()").getall() if nodes else [""]
            else:
                elements = soup.select(selector)
                texts = [e.get_text(strip=True) for e in elements] if elements else [""]
            return [t.strip() for t in texts if t] or [""], None
        else:
            sel = Selector(html)
            if selector_type == "xpath":
                nodes = sel.xpath(selector)
            else:
                nodes = sel.css(selector)
            texts = nodes.xpath("string()").getall() if nodes else [""]
            return [t.strip() for t in texts if t] or [""], None
    except Exception as e:
        return [], str(e)
