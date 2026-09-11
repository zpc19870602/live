# -*- coding: utf-8 -*-
import sys
import re
import json
import base64
import requests
from urllib.parse import urlencode, quote

sys.path.append('..')
try:
    from base.spider import Spider
except ImportError:
    class Spider:
        def fetch(self, url, headers=None, **kw):
            import requests as rq
            kw.pop('timeout', None)
            r = rq.get(url, headers=headers, timeout=15, **kw)
            r.encoding = 'utf-8'
            return r

API = ["https://h1cs.i8jajp.com:51111", "https://2gaw.vbjtex.com:52000", "https://d50.l2ukrb.com:51111", "https://96g.l9hmi1.com:25118", "https://d3oi.b0138j.com:51666", "https://gs4i.1unnk5.com:51777", "https://06sw.4k998b.com:52000", "https://17e.ueiqau.com:51666", "https://cn5s.afuuwy.com:51888", "https://wlq.pmjqlw8.com:51888", "https://jvx.i3ubxvj.com:25118", "https://cdz.rkfwzdc.com:52000", "https://esi.vobis8e.com:51111", "https://vqh.z4shq2v.com:51666"]
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
IMG_KEY = b"H0Z%7n#k$H8*M7xSE^N@8xXZPG*RZ&wY"

CATEGORIES = {
    "130": ("黑料", "cate"), "143": ("探花", "cate"), "127": ("SM", "cate"),
    "144": ("乱伦", "cate"), "178": ("颜值", "cate"), "153": ("人妻少妇", "cate"),
    "133": ("自拍", "cate"), "146": ("中文字幕", "cate"), "246": ("多男一女", "cate"),
    "247": ("多女一男", "cate"), "142": ("主播大秀", "cate"),
    "266": ("传媒", "label"), "262": ("国产", "label"), "263": ("日本AV", "label"),
    "264": ("欧美", "label"), "267": ("动漫", "label"), "341": ("三级", "label"),
    "342": ("AI换脸", "label"), "343": ("AV无码", "label"), "358": ("麻豆", "label"),
    "356": ("擦边短剧", "label"),
}

class Spider(Spider):
    def init(self, extend=""):
        self._doms = list(API)
        self._di = 0
        self._cats = {}
        self.header = {"User-Agent": UA, "Accept": "application/json"}

    def _api(self, path, params=None):
        qs = "?" + urlencode(params) if params else ""
        for _ in range(len(self._doms)):
            dom = self._doms[self._di % len(self._doms)]
            self._di += 1
            try:
                r = self.fetch(dom + path + qs, headers=self.header, timeout=12000)
                j = json.loads(r.text)
                if j.get("code") == 200 and j.get("data") and j.get("key"):
                    return json.loads(self._dec(j["data"], j["key"]))
            except Exception:
                pass
        return None

    def _dec(self, data, key):
        s = data.replace("-", "+").replace("_", "/")
        s += "=" * (-len(s) % 4)
        raw = base64.b64decode(s)
        kb = key.encode()
        return bytes(raw[i] ^ kb[i % len(kb)] for i in range(len(raw))).decode("utf-8", "replace")

    def _pic(self, it):
        p = it.get("upload_thumb") or it.get("thumb") or ""
        if not p:
            return ""
        if p.startswith("http"):
            url = p
        else:
            up = it.get("upload_thumb") or ""
            m = re.search(r"(https?://[^/]+)", up)
            base = m.group(1) if m else "https://spfm.xn--49sx5y1jln6s.cn"
            url = base + p
        return self.getProxyUrl() + "&url=" + quote(url, safe="")

    def homeContent(self, filter=False):
        d = self._api("/api/old_v3/video/nav")
        if isinstance(d, list):
            self._cats = {str(n.get("id")): (n.get("name") or "", n.get("type") or "cate") for n in d if n.get("id") and n.get("type") not in ("home", "hot")}
        cats = self._cats or CATEGORIES
        r = {"class": [], "list": []}
        for k, v in cats.items():
            r["class"].append({"type_id": str(k), "type_name": v[0] if isinstance(v, tuple) else v})
        return r

    def homeVideoContent(self):
        d = self._api("/api/old_v3/video/home")
        out = []
        if isinstance(d, list):
            for sec in d:
                if isinstance(sec, dict) and sec.get("list"):
                    out += self._items(sec["list"])
        return {"list": out}

    def categoryContent(self, tid, pg=1, filter=False, extend=""):
        try:
            pn = max(int(str(pg)), 1)
        except Exception:
            pn = 1
        t = "cate"
        if self._cats and str(tid) in self._cats:
            t = self._cats[str(tid)][1]
        elif str(tid) in CATEGORIES:
            t = CATEGORIES[str(tid)][1]
        d = self._api("/api/old_v3/video/getList", {"id": str(tid), "type": t, "page": pn, "size": 30})
        if not d:
            return {"page": pn, "pagecount": 1, "limit": 30, "total": 0, "list": []}
        try:
            total = int(d.get("total") or 0)
        except Exception:
            total = 0
        return {"page": pn, "pagecount": (total + 29) // 30 if total else 1, "limit": 30, "total": total, "list": self._items(d.get("list") or [])}

    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else str(ids or "")
        m = re.search(r"(\d+)", str(vid))
        vid = m.group(1) if m else ""
        if not vid:
            return {"list": []}
        d = self._api("/api/v3/home/public/video/long/detail", {"id": vid})
        if not d:
            return {"list": []}
        url = d.get("play_hls_url") or ""
        if url:
            url = re.sub(r"cdnId=\d+", "cdnId=2", url)
        if not url and d.get("href"):
            url = d["href"] if str(d["href"]).startswith("http") else ""
        if not url:
            return {"list": []}
        vod = {
            "vod_id": vid,
            "vod_name": str(d.get("title") or "")[:60],
            "vod_pic": self._pic(d),
            "vod_year": str(d.get("years") or ""),
            "vod_area": str(d.get("region") or ""),
            "vod_class": str(d.get("label") or ""),
            "vod_director": "",
            "vod_actor": str(d.get("actor") or ""),
            "vod_content": re.sub(r"<[^>]+>", "", str(d.get("desc") or "")).strip()[:500],
            "vod_remarks": str(d.get("label") or ""),
            "vod_play_from": "默认",
            "vod_play_url": "正片$" + url,
        }
        vl = d.get("video_list") or []
        if isinstance(vl, list) and vl:
            eps = []
            for i, e in enumerate(vl):
                if not isinstance(e, dict):
                    continue
                eu = e.get("play_hls_url") or ""
                if eu:
                    eu = re.sub(r"cdnId=\d+", "cdnId=2", eu)
                if not eu and e.get("href"):
                    eu = e["href"] if str(e["href"]).startswith("http") else ""
                if eu:
                    eps.append("%s$%s" % (str(e.get("title") or ("第%d集" % (i + 1))).replace("$", "").replace("#", ""), eu))
            if eps:
                vod["vod_play_url"] = "#".join(eps)
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        d = self._api("/api/old_v3/video/search", {"keyword": key, "page": 1, "size": 30})
        if not d:
            return {"list": []}
        return {"list": self._items(d.get("data") or [])}

    def playerContent(self, flag, id, vipFlags=None):
        return {"parse": 0, "url": str(id)}

    def localProxy(self, param):
        try:
            from Crypto.Cipher import AES
        except ImportError:
            return [500, "text/plain", b"no crypto"]
        if not isinstance(param, dict):
            return [400, "text/plain", b"bad param"]
        url = param.get("url", "")
        if not isinstance(url, str) or not url.startswith("http"):
            return [400, "text/plain", b"bad url"]
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
            if r.status_code != 200:
                return [502, "text/plain", b"fetch fail"]
            raw = r.content
            if not raw or len(raw) <= 16:
                return [502, "text/plain", b"bad enc"]
            plain = AES.new(IMG_KEY, AES.MODE_CBC, raw[:16]).decrypt(raw[16:])
            if plain[:3] == b"\xff\xd8\xff":
                return [200, "image/jpeg", plain]
            if plain[:4] == b"\x89PNG":
                return [200, "image/png", plain]
            if plain[:3] in (b"GIF87a", b"GIF89a"):
                return [200, "image/gif", plain]
            return [502, "text/plain", b"bad image"]
        except Exception:
            return [502, "text/plain", b"proxy err"]

    def _items(self, arr):
        out = []
        for it in arr or []:
            if not isinstance(it, dict) or not it.get("id"):
                continue
            out.append({
                "vod_id": str(it["id"]),
                "vod_name": str(it.get("title") or "")[:60],
                "vod_pic": self._pic(it),
                "vod_remarks": str(it.get("label") or ""),
            })
        return out
