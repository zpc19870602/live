# coding=utf-8
"""
TVBox / CatVod Spider for Yelive live streams.

The original MgRead source uses videoM3u8() to rewrite Mouflon-HLS playlists.
This Spider exposes the public Yelive API and returns an authenticated HLS
variant URL for TVBox.  The source therefore works with TVBox players that
support HLS request headers; browsers can still use the original .js source.
"""
import base64
import hashlib
import json
import re
import urllib.parse
from urllib.parse import urljoin

import sys
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    site_url = "https://zh.yelive.tv"
    front_version = "11.7.45"
    page_size = 24
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/136.0.0.0 Safari/537.36"
    )
    # The web paths are translated labels, but the API now exposes ISO country
    # codes in model.country.  Keep both values for compatibility.
    countries = [
        ("中国", "cn"), ("台湾", "tw"), ("日本", "jp"), ("韩国", "kr"),
        ("美国", "us"), ("英国", "gb"), ("加拿大", "ca"), ("澳大利亚", "au"),
        ("新西兰", "nz"), ("泰国", "th"), ("越南", "vn"), ("菲律宾", "ph"),
        ("马来西亚", "my"), ("印度", "in"), ("印尼", "id"), ("巴西", "br"),
        ("法国", "fr"), ("德国", "de"), ("意大利", "it"), ("西班牙", "es"),
        ("俄罗斯", "ru"), ("南非", "za"), ("墨西哥", "mx"), ("阿根廷", "ar"),
    ]
    primary = [("女主播", "girls"), ("情侣", "couples"),
               ("男主播", "men"), ("跨性别", "trans")]
    tags = [
        ("中文", "tagLanguageChinese"), ("新主播", "autoTagNew"),
        ("VR摄像头", "autoTagVr"), ("团体秀", "groupShow"),
        ("少女18+", "ageTeen"), ("鲜嫩青年22+", "ageYoung"),
        ("熟女", "ageMilf"), ("成熟", "ageMature"),
        ("亚洲人", "ethnicityAsian"), ("白人", "ethnicityWhite"),
        ("拉丁人", "ethnicityLatino"), ("黑人", "ethnicityEbony"),
        ("娇小", "bodyTypePetite"), ("运动型", "bodyTypeAthletic"),
        ("标准体型", "bodyTypeMedium"), ("丰满", "bodyTypeCurvy"),
        ("金发", "hairColorBlonde"), ("棕发", "hairColorBrown"),
        ("黑发", "hairColorBlack"), ("红发", "hairColorRed"),
    ]

    def init(self, extend=""):
        # TVBox passes the configured ``ext`` value to init().  Accept a
        # custom Yelive mirror while retaining the Chinese site by default.
        if isinstance(extend, str) and extend.strip().startswith(("http://", "https://")):
            self.site_url = extend.strip().rstrip("/")
        self.headers = {
            "User-Agent": self.ua,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Front-Version": self.front_version,
            "Referer": self.site_url + "/",
        }
        self.hls_headers = {
            "User-Agent": self.ua,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": self.site_url,
            "Referer": self.site_url + "/",
        }
        self._country_cache = {}

    def _get(self, url, headers=None):
        try:
            try:
                resp = self.fetch(url, headers=headers or self.headers, timeout=15)
            except TypeError:
                resp = self.fetch(url, headers=headers or self.headers)
            if not resp:
                return ""
            text = getattr(resp, "text", None)
            if text is not None and text != "":
                return text
            content = getattr(resp, "content", b"")
            # Some Spider runtimes expose a urllib-like response with only
            # ``read()``; support it in addition to requests-style ``text`` /
            # ``content`` attributes.
            if (content is None or content == b"" or content == "") and hasattr(resp, "read"):
                content = resp.read()
            return content.decode("utf-8", "ignore") if isinstance(content, bytes) else str(content)
        except Exception as exc:
            try:
                self.log("Yelive request failed: " + str(exc))
            except Exception:
                pass
            return ""

    @staticmethod
    def _status(status):
        return {"public": "公开直播", "groupShow": "团体秀", "private": "私密中",
                "p2p": "一对一", "offline": "离线"}.get(str(status or ""), "直播")

    @staticmethod
    def _public(model):
        return str(model.get("status", "")) == "public" and model.get("isOnline", True) is not False

    def _request_models(self, primary, offset, limit, tag=""):
        params = {
            "limit": limit, "offset": offset, "primaryTag": primary,
            "sortBy": "stripRanking",
        }
        if tag:
            params["filterGroupTags"] = json.dumps([[tag]], ensure_ascii=False, separators=(",", ":"))
        url = self.site_url + "/api/front/models?" + urllib.parse.urlencode(params)
        try:
            data = json.loads(self._get(url))
        except Exception:
            data = {}
        raw_models = data.get("models", []) if isinstance(data, dict) else []
        models = [m for m in raw_models if isinstance(m, dict) and self._public(m)]
        total = data.get("filteredCount", 0) if isinstance(data, dict) else 0
        return models, total if isinstance(total, int) else 0, len(raw_models)

    def _country_models(self, primary, country_code, page, tag=""):
        key = (primary, tag)
        state = self._country_cache.setdefault(key, {"models": [], "seen": set(), "offset": 0, "done": False})
        wanted = max(1, int(page or 1)) * self.page_size + 1
        while len([m for m in state["models"] if str(m.get("country", "")).lower() == country_code]) < wanted and not state["done"]:
            models, _, raw_count = self._request_models(primary, state["offset"], 99, tag)
            for model in models:
                marker = str(model.get("id") or model.get("username") or "").lower()
                if marker and marker not in state["seen"]:
                    state["seen"].add(marker)
                    state["models"].append(model)
            state["offset"] += 99
            if raw_count < 99 or state["offset"] >= 1089:
                state["done"] = True
        start = (max(1, int(page or 1)) - 1) * self.page_size
        items = [m for m in state["models"] if str(m.get("country", "")).lower() == country_code]
        pagecount = max(1, int(page or 1) + int(len(items) > start + self.page_size or not state["done"]))
        return items, pagecount

    @staticmethod
    def _extend(value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _room(model):
        values = {
            "u": model.get("username", ""), "h": model.get("hlsPlaylist", ""),
            "c": model.get("previewUrlThumbSmall") or model.get("avatarUrl", ""),
            "s": model.get("status", ""), "v": model.get("viewersCount", ""),
            "g": model.get("gender", "") or model.get("broadcastGender", ""),
            "id": model.get("id", "") or model.get("streamName", ""),
            "ps": ",".join(model.get("presets") or []),
        }
        return "yelive://room?" + urllib.parse.urlencode(values, quote_via=urllib.parse.quote)

    @staticmethod
    def _hls(data, quality="auto"):
        values = {"u": data.get("u", ""), "h": data.get("h", ""),
                  "id": data.get("id", ""), "quality": quality or "auto"}
        return "yelive://hls?" + urllib.parse.urlencode(values, quote_via=urllib.parse.quote)

    @staticmethod
    def _qualities(presets):
        """Return selectable numeric resolutions advertised by the API."""
        values = []
        for item in presets or []:
            value = str(item or "").strip().lower()
            # ``160p_blurred`` is an intentionally blurred fallback and is
            # not useful as a user-facing quality choice.
            if re.match(r"^\d+p(?:60)?$", value):
                values.append(value)
        values = sorted(set(values), key=lambda x: (int(re.match(r"\d+", x).group()), "60" in x), reverse=True)
        # TVBox's quality selector should contain only explicit renditions;
        # putting the highest resolution first makes it the default choice.
        return values

    @staticmethod
    def _auto_source(data):
        """Build a standard-HLS master URL on the model's current CDN edge."""
        ident = str(data.get("id") or "").strip()
        original = str(data.get("h") or "").strip()
        if original:
            # API hlsPlaylist normally points at *_240p.m3u8.  Replacing only
            # the rendition suffix keeps the currently assigned edge (the
            # edge pool changes frequently and a hard-coded host can stall).
            converted = re.sub(
                r"/master/([^/]+?)(?:_\d+p(?:60)?|_auto)?\.m3u8(?:\?.*)?$",
                r"/master/\1_auto.m3u8",
                original,
                flags=re.I,
            )
            if converted != original or "/master/" in original:
                return converted
        if ident:
            return "https://edge-hls.doppiocdn.media/hls/%s/master/%s_auto.m3u8" % (ident, ident)
        return original

    def _book(self, model):
        name = str(model.get("username") or model.get("name") or "直播间")
        viewers = model.get("viewersCount", "")
        status = self._status(model.get("status"))
        room = self._room(model)
        hls = self._hls({"u": name, "h": model.get("hlsPlaylist", ""),
                         "id": model.get("id") or model.get("streamName", ""),
                         "ps": ",".join(model.get("presets") or [])})
        presets = model.get("presets") or []
        qualities = self._qualities(presets)
        if not qualities:
            # A few API responses omit ``presets``.  Keep a usable fixed
            # rendition rather than exposing an ``自动`` item that may cause
            # the player to probe every variant.
            qualities = ["480p"]
        play_items = []
        for quality in qualities:
            play_items.append(quality + "$" + self._hls({"u": name, "h": model.get("hlsPlaylist", ""),
                              "id": model.get("id") or model.get("streamName", ""),
                              "ps": ",".join(presets)}, quality))
        return {
            "vod_id": room, "vod_name": name,
            "vod_pic": model.get("previewUrlThumbSmall") or model.get("avatarUrl", ""),
            "vod_remarks": (str(viewers) + " 人观看") if viewers else status,
            "vod_year": status, "vod_actor": status,
            "vod_content": "Yelive 直播间：" + self.site_url + "/" + urllib.parse.quote(name),
            "vod_play_from": "直播$$$网页",
            "vod_play_url": "#".join(play_items) + "$$$网页观看$" + self.site_url + "/" + urllib.parse.quote(name),
        }

    def homeContent(self, filter):
        classes = []
        for name, key in self.primary:
            classes.append({"type_id": "p:" + key, "type_name": name})
        for name, key in self.countries:
            classes.append({"type_id": "c:" + key, "type_name": name})
        for name, key in self.tags:
            classes.append({"type_id": "t:" + key, "type_name": name})
        models, _, _ = self._request_models("girls", 0, self.page_size)
        result = {"class": classes, "list": [self._book(m) for m in models]}
        if filter:
            result["filters"] = {item["type_id"]: self._filter_rows() for item in classes}
        return result

    def _filter_rows(self):
        return [
            {"key": "tag", "name": "标签", "init": "", "value": [
                {"n": name, "v": key} for name, key in self.tags
            ]},
            {"key": "country", "name": "国家", "init": "", "value": [
                {"n": name, "v": code} for name, code in self.countries
            ]},
        ]

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        tid = str(tid or "")
        page = int(pg or 1)
        extend = self._extend(extend)
        primary, tag = "girls", ""
        country_code = ""
        if tid.startswith("p:"):
            primary = tid[2:] or "girls"
        elif tid.startswith("c:"):
            country_code = tid[2:].lower()
        elif tid.startswith("t:"):
            tag = tid[2:]
        if extend.get("tag") in {key for _, key in self.tags}:
            tag = extend["tag"]
        if extend.get("country") in {code for _, code in self.countries}:
            country_code = extend["country"]
        if country_code:
            models, pagecount = self._country_models(primary, country_code, page, tag)
            total = 0
        else:
            models, total, _ = self._request_models(primary, (page - 1) * self.page_size, self.page_size, tag)
            pagecount = max(1, (total + self.page_size - 1) // self.page_size) if total else max(1, page + int(len(models) == self.page_size))
        result = {"list": [self._book(m) for m in models], "page": page,
                  "pagecount": pagecount, "limit": self.page_size}
        if total:
            result["total"] = total
        return result

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        value = str(ids[0])
        if not value.startswith("yelive://room?"):
            return {"list": [{"vod_id": value, "vod_name": value, "vod_play_from": "网页",
                              "vod_play_url": "网页观看$" + value}]}
        data = self._query(value)
        name = data.get("u", "直播间")
        hls = self._hls(data)
        presets = [x for x in str(data.get("ps", "")).split(",") if x]
        qualities = self._qualities(presets) or ["480p"]
        play_items = [q + "$" + self._hls(data, q) for q in qualities]
        return {"list": [{"vod_id": value, "vod_name": name, "vod_pic": data.get("c", ""),
                          "vod_actor": self._status(data.get("s")),
                          "vod_content": "公开直播，观看人数：" + str(data.get("v", "")),
                          "vod_play_from": "直播$$$网页",
                          "vod_play_url": "#".join(play_items) + "$$$网页观看$" + self.site_url + "/" + urllib.parse.quote(name)}]}

    def searchContent(self, key, quick, pg="1"):
        key = str(key or "").strip()
        if not key:
            return {"list": [], "page": 1, "pagecount": 1}
        found, seen = [], set()
        for _, primary in self.primary:
            url = self.site_url + "/api/front/v4/models/search/group/username?" + urllib.parse.urlencode({
                "query": key, "primaryTag": primary, "limit": 99, "uniq": "1"})
            try:
                data = json.loads(self._get(url))
            except Exception:
                data = {}
            models = data.get("models", []) if isinstance(data, dict) else []
            for model in models:
                username = str(model.get("username", ""))
                marker = username.lower()
                if marker and marker not in seen and self._public(model):
                    seen.add(marker)
                    found.append(self._book(model))
        return {"list": found, "page": int(pg or 1), "pagecount": 1}

    @staticmethod
    def _query(url):
        parsed = urllib.parse.urlparse(url)
        return {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}

    @staticmethod
    def _quality_url(master, quality="auto"):
        pkey_match = re.findall(r"#EXT-X-MOUFLON:PSCH:v2:([^\r\n]+)", master or "")
        pkey = "NTK9aqcLmNFMWrpQ" if pkey_match else ""
        items = []
        lines = (master or "").splitlines()
        pending = False
        for line in lines:
            line = line.strip()
            if line.startswith("#EXT-X-STREAM-INF:"):
                pending = line
            elif pending and line and not line.startswith("#"):
                res = re.search(r"RESOLUTION=\d+x(\d+)", pending, re.I)
                name_match = re.search(r'NAME="([^"]+)"', pending, re.I)
                name = name_match.group(1).lower() if name_match else ""
                # Providers often label the highest rendition as ``source``;
                # expose its numeric resolution so an explicit 720p/1080p
                # request can still select it.
                label = (res.group(1) + "p") if res and (not name or name in ("source", "auto", "原画")) else (name or (res.group(1) + "p" if res else "auto"))
                items.append((label, line))
                pending = False
        target = str(quality or "").lower()
        selected = None
        for label, url in items:
            if target and (target in label or label in target):
                selected = url
                break
        if not selected and items:
            selected = items[0][1]
        if not selected:
            return ""
        if pkey:
            selected += ("&" if "?" in selected else "?") + "psch=v2&pkey=" + pkey
        return selected

    def _proxy_link(self, upstream):
        """Return TVBox's localProxy URL, preserving the upstream URL."""
        try:
            proxy = self.getProxyUrl()
        except Exception:
            return upstream
        if not proxy:
            return upstream
        sep = "&" if "?" in proxy else "?"
        return proxy + sep + "url=" + urllib.parse.quote(str(upstream), safe="")

    @staticmethod
    def _decode_mouflon_uri(uri):
        """Decode the v2 token used in Mouflon media segment paths."""
        match = re.search(r"_(\d+)_([^_]+)_(\d{10})(?=(?:_part\d+)?\.mp4(?:[?#].*)?$)", uri or "")
        if not match:
            return uri
        try:
            token = match.group(2)
            raw = base64.b64decode(token[::-1] + "=" * (-len(token) % 4))
            key = hashlib.sha256(b"tOcYOap4Ty1l9Jzb").digest()
            plain = bytes(value ^ key[index % len(key)] for index, value in enumerate(raw)).decode("utf-8")
            if not re.match(r"^[A-Za-z0-9+/=-]+$", plain):
                return uri
            return uri.replace("_" + token + "_" + match.group(3), "_" + plain + "_" + match.group(3), 1)
        except Exception:
            return uri

    def _rewrite_m3u8(self, text, base_url):
        """Replace Mouflon's placeholder URIs with its decoded media URLs."""
        lines = str(text or "").splitlines()
        pkey = "NTK9aqcLmNFMWrpQ" if "#EXT-X-MOUFLON:PSCH:v2:" in text else ""
        out, pending_stream, pending_mouflon = [], False, ""
        for raw in lines:
            line = raw.strip()
            if line.startswith("#EXT-X-STREAM-INF:"):
                pending_stream = True
                out.append(raw)
                continue
            if pending_stream and line and not line.startswith("#"):
                child = urljoin(base_url, line)
                if pkey and "pkey=" not in child:
                    child += ("&" if "?" in child else "?") + "psch=v2&pkey=" + pkey
                out.append(self._proxy_link(child))
                pending_stream = False
                continue
            pending_stream = False
            if line.startswith("#EXT-X-MOUFLON:URI:"):
                pending_mouflon = self._decode_mouflon_uri(line[len("#EXT-X-MOUFLON:URI:"):].strip())
                continue
            if line.startswith("#EXT-X-PART:") and pending_mouflon:
                line = re.sub(r'URI="[^"]+"', lambda _: 'URI="%s"' % pending_mouflon, line, count=1)
                pending_mouflon = ""
                out.append(line)
                continue
            if line.startswith("#EXT-X-MOUFLON:"):
                continue
            if line.startswith("#EXT-X-MAP:") or line.startswith("#EXT-X-PRELOAD-HINT:"):
                if line.startswith("#EXT-X-PRELOAD-HINT:") and "media.mp4" in line:
                    continue
                line = re.sub(r'URI="([^"]+)"', lambda m: 'URI="%s"' % urljoin(base_url, m.group(1)), line, count=1)
                out.append(line)
                continue
            if line and not line.startswith("#"):
                target = urljoin(base_url, pending_mouflon or line)
                pending_mouflon = ""
                # Child playlists still need proxy rewriting; media segments
                # can be fetched directly by the TVBox player.
                if target.lower().split("?", 1)[0].endswith((".m3u8", ".m3u")):
                    out.append(self._proxy_link(target))
                else:
                    out.append(target)
            else:
                out.append(raw)
        return "\n".join(out) + ("\n" if str(text or "").endswith("\n") else "")

    def localProxy(self, param):
        """Serve and rewrite HLS playlists; pass binary segments through."""
        try:
            upstream = param.get("url", "") if isinstance(param, dict) else ""
            upstream = str(upstream or "").strip()
            if not upstream.startswith(("http://", "https://")):
                return [400, "text/plain; charset=utf-8", b"Bad Request"]
            # Keep a little headroom for live playlist reloads; the base Spider
            # defaults requests to five seconds.
            try:
                response = self.fetch(upstream, headers=self.hls_headers, timeout=12)
            except TypeError:
                response = self.fetch(upstream, headers=self.hls_headers)
            body = getattr(response, "content", b"")
            if (body is None or body == b"" or body == "") and hasattr(response, "read"):
                body = response.read()
            if not isinstance(body, bytes):
                body = str(getattr(response, "text", body)).encode("utf-8")
            content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
            status = int(getattr(response, "status_code", 200) or 200)
            if "#EXTM3U" in body[:128].decode("utf-8", "ignore") or upstream.lower().split("?", 1)[0].endswith((".m3u8", ".m3u")):
                rewritten = self._rewrite_m3u8(body.decode("utf-8", "ignore"), upstream)
                return [status, "application/vnd.apple.mpegurl", rewritten.encode("utf-8"),
                        {"Cache-Control": "no-cache, no-store", "Access-Control-Allow-Origin": "*"}]
            return [status, content_type or "application/octet-stream", body,
                    {"Cache-Control": "no-cache, no-store", "Access-Control-Allow-Origin": "*"}]
        except Exception as exc:
            return [502, "text/plain; charset=utf-8", ("Proxy Error: " + str(exc)).encode("utf-8")]

    def playerContent(self, flag, id, vipFlags):
        value = str(id or "")
        if value.startswith("yelive://hls?"):
            data = self._query(value)
            source = data.get("h", "")
            if data.get("id") or data.get("h"):
                source = self._auto_source(data)
            if source:
                master = self._get(source, self.hls_headers)
                chosen = self._quality_url(master, data.get("quality", ""))
                stream_headers = dict(self.hls_headers)
                stream_headers["Referer"] = self.site_url + "/" + urllib.parse.quote(data.get("u", ""))
                if chosen:
                    return {"parse": 0, "url": self._proxy_link(chosen), "header": stream_headers}
                return {"parse": 0, "url": self._proxy_link(source), "header": stream_headers}
        if value.startswith("yelive://room?"):
            data = self._query(value)
            return self.playerContent(flag, self._hls(data), vipFlags)
        if value.startswith("http"):
            return {"parse": 1, "url": value, "header": self.headers}
        return {"parse": 1, "url": value, "header": self.headers}
