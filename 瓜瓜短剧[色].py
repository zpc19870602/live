# -*- coding: utf-8 -*-
# 黄瓜短剧 | OK影视/TVBox 通用 | 基于base.spider | 全集解锁版(窗口步进取流)
import sys
import re
import json
import math
import base64
import requests
from urllib.parse import quote
try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    Cipher = algorithms = modes = None
sys.path.append('..')
try:
    from base.spider import Spider
except ImportError:
    Spider = object
class Spider(Spider):
    TAGS = [("tag:dushi", "题材·都市邻里"), ("tag:tag", "题材·甜宠恋爱"), ("tag:nixi", "题材·逆袭"), ("tag:fuchou", "题材·复仇逆袭"), ("tag:xuanhuan", "题材·古装玄幻"), ("tag:tag-06118f", "题材·虐恋情深"), ("tag:xuanyi", "题材·惊悚悬疑"), ("tag:tianchong", "题材·霸总激情"), ("tag:chuanyue", "题材·穿越重生"), ("tag:tag-88650e", "题材·战神归来"), ("tag:zhanshen", "题材·末世生存")]
    def getName(self):
        return "黄瓜短剧"
    def init(self, extend=""):
        self.site_url = "https://hgdju.com"
        self.headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36", "Referer": self.site_url, "Accept-Language": "zh-CN,zh;q=0.9"}
        self.sess = requests.Session()
        requests.packages.urllib3.disable_warnings()
        self.page_size = 20
    def _get(self, url, hdr=None, t=15):
        try:
            hh = self.headers
            if hdr:
                hh = dict(self.headers)
                hh.update(hdr)
            r = self.sess.get(url, headers=hh, timeout=t, verify=False)
            r.encoding = "utf-8"
            return r.text if r.ok else ''
        except Exception:
            return ''
    def _abs(self, u):
        if not u:
            return ''
        if u.startswith('//'):
            return 'https:' + u
        return u if u.startswith('http') else self.site_url + u
    def _cover(self, u):
        """站点封面为 AES-CBC 密文；TVBox 不能直接显示密文，转成 data URL。"""
        u = self._abs(u)
        if not u or u.startswith('data:image/'):
            return u
        if not AES and not Cipher:
            return ''
        try:
            r = self.sess.get(u, headers=self.headers, timeout=15, verify=False)
            raw = r.content
            if len(raw) < 32 or len(raw) % 16:
                return u if raw.startswith((b'\xff\xd8\xff', b'\x89PNG', b'RIFF', b'GIF')) else ''
            # 新旧资源并存：部分 poster 已是明文图片，直接保留 URL。
            if raw.startswith((b'\xff\xd8\xff', b'\x89PNG', b'RIFF', b'GIF')):
                return u
            if AES:
                plain = AES.new(b'f5d965df75336270', AES.MODE_CBC, b'97b60394abc2fbe1').decrypt(raw)
            else:
                decryptor = Cipher(algorithms.AES(b'f5d965df75336270'), modes.CBC(b'97b60394abc2fbe1')).decryptor()
                plain = decryptor.update(raw) + decryptor.finalize()
            pad = plain[-1]
            if not isinstance(pad, int):
                pad = ord(pad)
            if pad < 1 or pad > 16 or plain[-pad:] != bytes([pad]) * pad:
                return ''
            plain = plain[:-pad]
            if plain[:3] == b'\xff\xd8\xff': mime = 'image/jpeg'
            elif plain[:8] == b'\x89PNG\r\n\x1a\n': mime = 'image/png'
            elif plain[:4] == b'RIFF': mime = 'image/webp'
            elif plain[:3] == b'GIF': mime = 'image/gif'
            else: return ''
            return 'data:%s;base64,%s' % (mime, base64.b64encode(plain).decode('ascii'))
        except Exception:
            return ''

    def _cover_candidates(self, *values):
        for value in values:
            if value:
                decoded = self._cover(value)
                if decoded:
                    return decoded
        return ''
    def _pic(self, item_html):
        u = ''
        m = re.search(r'data-cover-fb="([^"]+)"', item_html)
        if m and 'loading' not in m.group(1):
            u = m.group(1)
        if not u:
            m = re.search(r'z-image-loader-url="([^"]+)"', item_html)
            if m and 'loading' not in m.group(1):
                u = m.group(1)
        if not u:
            m = re.search(r'<img[^>]+src="([^"]+)"', item_html)
            if m and 'loading' not in m.group(1):
                u = m.group(1)
        return self._abs(u)
    def _cover_urls(self, html):
        text = (html or '').replace('\\u002F', '/').replace('\\u0026', '&')
        urls = re.findall(r'https?://[^"\'\s<>]+?\.(?:jpe?g|png|webp)(?:\?[^"\'\s<>]*)?', text, re.I)
        out = []
        seen = set()
        for url in urls:
            if url not in seen and '/cover/' in url.lower() and not re.search(r'social-default|logo', url, re.I):
                seen.add(url)
                out.append(url)
        return out
    def _nuxt_items(self, html):
        m = re.search(r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>', html or '', re.S | re.I)
        if not m:
            return []
        try:
            table = json.loads(m.group(1))
            resolving = set()
            def resolve_entry(index):
                if index < 0 or index >= len(table):
                    return index
                if index in resolving:
                    return table[index]
                value = table[index]
                if not isinstance(value, (dict, list)):
                    return value
                resolving.add(index)
                if isinstance(value, list):
                    out = [resolve_entry(x) if isinstance(x, int) and not isinstance(x, bool) and 0 <= x < len(table) else x for x in value]
                else:
                    out = {k: (resolve_entry(v) if isinstance(v, int) and not isinstance(v, bool) and 0 <= v < len(table) else v) for k, v in value.items()}
                resolving.remove(index)
                return out
            root = resolve_entry(0)
            def find_items(value, seen=None):
                if seen is None:
                    seen = set()
                if not isinstance(value, (dict, list)) or id(value) in seen:
                    return []
                seen.add(id(value))
                if isinstance(value, dict):
                    page = value.get('page')
                    if isinstance(page, dict) and isinstance(page.get('items'), list):
                        return page.get('items')
                    for child in value.values():
                        found = find_items(child, seen)
                        if found:
                            return found
                else:
                    for child in value:
                        found = find_items(child, seen)
                        if found:
                            return found
                return []
            return find_items(root)
        except Exception:
            return []

    def _nuxt_drama(self, html, slug):
        m = re.search(r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>', html or '', re.S | re.I)
        if not m:
            return {}
        try:
            table = json.loads(m.group(1)); resolving = set()
            def resolve(i):
                if i < 0 or i >= len(table): return i
                v = table[i]
                if not isinstance(v, (dict, list)) or i in resolving: return v
                resolving.add(i)
                out = ([resolve(x) if isinstance(x, int) and not isinstance(x, bool) and 0 <= x < len(table) else x for x in v]
                       if isinstance(v, list) else {k: resolve(x) if isinstance(x, int) and not isinstance(x, bool) and 0 <= x < len(table) else x for k, x in v.items()})
                resolving.remove(i); return out
            root = resolve(0)
            def walk(v):
                if isinstance(v, dict):
                    if v.get('slug') == slug and isinstance(v.get('cover'), dict): return v
                    for x in v.values():
                        y = walk(x)
                        if y: return y
                elif isinstance(v, list):
                    for x in v:
                        y = walk(x)
                        if y: return y
                return None
            return walk(root) or {}
        except Exception:
            return {}
    def _cards(self, html):
        out, seen = [], set()
        cover_urls = self._cover_urls(html)
        for data in self._nuxt_items(html):
            if not isinstance(data, dict):
                continue
            vid = data.get('primary_route') or data.get('detail_route') or ''
            if vid.startswith('/drama/'):
                vid = vid.replace('/drama/', '/play/', 1) + '/' + str(data.get('latest_episode_number') or 1)
            elif not vid.startswith('/play/') and data.get('slug'):
                vid = '/play/' + data.get('slug') + '/' + str(data.get('latest_episode_number') or 1)
            title = str(data.get('title') or '').strip()
            if not vid or not title or vid in seen:
                continue
            seen.add(vid)
            cover = data.get('cover') or {}
            pic = cover.get('url') or cover.get('fallback_url') or (cover_urls[len(out)] if len(out) < len(cover_urls) else '')
            latest = data.get('latest_episode_number')
            out.append({"vod_id": self._abs(vid), "vod_name": title, "vod_pic": self._cover_candidates(pic, cover.get('fallback_url')), "vod_remarks": ('更新至' + str(latest) + '集') if latest else '', "style": {"type": "rect", "ratio": 0.75}})
        if out:
            return out
        modern_cards = re.findall(r'<article\s+data-xpch=["\']card-drama["\'][^>]*>.*?</article>', html or '', re.S | re.I)
        if modern_cards:
            for item in modern_cards:
                im = re.search(r'<a[^>]+href=["\'](/play/[^"\']+)["\']', item, re.I)
                nm = re.search(r'<div[^>]+class=["\'][^"\']*truncate[^"\']*["\'][^>]*>(.*?)</div>', item, re.S | re.I)
                if not im:
                    continue
                vid = im.group(1)
                title = re.sub(r'<[^>]+>', '', nm.group(1) if nm else '').strip()
                if not title or vid in seen:
                    continue
                seen.add(vid)
                ep = re.search(r'(?:全|更新至)\s*(\d+)\s*集', item, re.I)
                raw_pic = cover_urls[len(out)] if len(out) < len(cover_urls) else self._pic(item)
                out.append({"vod_id": self._abs(vid), "vod_name": title, "vod_pic": self._cover_candidates(raw_pic), "vod_remarks": ('更新至' + ep.group(1) + '集') if ep else '', "style": {"type": "rect", "ratio": 0.75}})
            return out
        for m in re.finditer(r'<div class="card">(.*?)</div>', html, re.S):
            item = m.group(1)
            im = re.search(r'<a class="card-main" href="(/play/[^"]+)"', item)
            nm = re.search(r'<b class="card-title">(.*?)</b>', item)
            if not (im and nm):
                continue
            vid = im.group(1)
            if vid in seen:
                continue
            seen.add(vid)
            em = re.search(r'<i class="card-ep num">(.*?)</i>', item)
            out.append({"vod_id": self._abs(vid), "vod_name": nm.group(1).strip(), "vod_pic": self._cover_candidates(self._pic(item)), "vod_remarks": em.group(1).strip() if em else '', "style": {"type": "rect", "ratio": 0.75}})
        return out
    def homeContent(self, filter):
        cs = [{"type_name": "全部", "type_id": "home"}, {"type_name": "原创", "type_id": "yuanchuang"}, {"type_name": "魔改", "type_id": "mogai"}, {"type_name": "AI漫剧", "type_id": "manju"}, {"type_name": "真人短剧", "type_id": "zhenren"}, {"type_name": "AI短剧", "type_id": "aiduanju"}] + [{"type_name": n, "type_id": t} for t, n in self.TAGS]
        return {"class": cs, "filters": {}}
    def homeVideoContent(self):
        ls = self._list('home', 1)[0]
        return {"list": ls}
    def _list(self, tid, pg, q=''):
        s = str(tid)
        if s in ('home', 'browse'):
            u1, up = f'{self.site_url}/browse', lambda n: f'{self.site_url}/browse?page={n}'
        elif s.startswith('tag:'):
            t = s[4:]
            u1, up = f'{self.site_url}/tag/{t}', lambda n: f'{self.site_url}/tag/{t}?page={n}'
        elif s == 'search':
            qs = quote(q or '')
            u1, up = f'{self.site_url}/search?q={qs}', lambda n: f'{self.site_url}/search?q={qs}&page={n}'
        else:
            u1, up = f'{self.site_url}/{s}', lambda n: f'{self.site_url}/{s}?page={n}'
        if pg <= 1:
            html = self._get(u1)
            if not html:
                return [], 1
            ls = self._cards(html)[:self.page_size]
            tot = re.search(r'共 (\d+) 部', html)
            return ls, math.ceil(int(tot.group(1)) / self.page_size) if tot else 1
        u = up(pg)
        raw = self._get(u + ('&' if '?' in u else '?') + 'partial=1', {'X-Requested-With': 'fetch'})
        d = None
        if raw:
            try:
                d = json.loads(raw)
            except Exception:
                d = None
        if isinstance(d, dict) and d.get('html') is not None:
            ls = self._cards(d.get('html') or '')[:self.page_size]
            return ls, int(d.get('pages') or (pg + 1 if ls else pg))
        html = self._get(u)
        if not html:
            return [], pg
        ls = self._cards(html)
        if len(ls) > self.page_size:
            ls = ls[-self.page_size:]
        return ls, pg + 1 if ls else pg
    def categoryContent(self, tid, pg='1', filter='', extend=''):
        pg = int(pg) if str(pg).isdigit() else 1
        ls, pc = self._list(str(tid), pg)
        return {"list": ls, "page": pg, "pagecount": pc, "limit": self.page_size, "total": len(ls) if ls else 0}
    def _hg(self, url):
        html = self._get(url)
        if not html:
            return None
        m = re.search(r'window\.HG_PLAY\s*=\s*(.*?);\s*</script>', html, re.S)
        if m:
            try:
                return json.loads(m.group(1).replace('\\u0026', '&'))
            except Exception:
                pass
        m = re.search(r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>', html, re.S | re.I)
        if not m:
            return None
        try:
            table = json.loads(m.group(1))
            resolving = set()
            def resolve_entry(index):
                if index < 0 or index >= len(table):
                    return index
                if index in resolving:
                    return table[index]
                value = table[index]
                if not isinstance(value, (dict, list)):
                    return value
                resolving.add(index)
                if isinstance(value, list):
                    out = [resolve_entry(x) if isinstance(x, int) and not isinstance(x, bool) and 0 <= x < len(table) else x for x in value]
                else:
                    out = {k: (resolve_entry(v) if isinstance(v, int) and not isinstance(v, bool) and 0 <= v < len(table) else v) for k, v in value.items()}
                resolving.remove(index)
                return out
            root = resolve_entry(0)
            def find_play(value, seen=None):
                if seen is None:
                    seen = set()
                if not isinstance(value, (dict, list)) or id(value) in seen:
                    return None
                seen.add(id(value))
                if isinstance(value, dict):
                    if value.get('drama') and (value.get('media') or {}).get('source_url'):
                        return value
                    for child in value.values():
                        found = find_play(child, seen)
                        if found:
                            return found
                else:
                    for child in value:
                        found = find_play(child, seen)
                        if found:
                            return found
                return None
            data = find_play(root)
            if not data:
                return None
            drama = data.get('drama') or {}
            return {
                'title': drama.get('title') or '',
                'intro': drama.get('intro') or '',
                'drama': drama,
                'totalEp': int(drama.get('total_episode_count') or 0),
                'line': '',
                'current': data.get('episode') or {},
                'media': data.get('media') or {},
                'episodes': data.get('episodes') or []
            }
        except Exception:
            return None
    def _slug(self, vid):
        m = re.search(r'/(?:play|drama)/([^/?#]+)', str(vid), re.I)
        return m.group(1) if m else (vid.split('/')[-1].split('?')[0] if '/' in vid else vid)
    def _fetch_all(self, slug, total):
        got = {}
        for n in range(1, min(3, total) + 1):
            d = self._hg(f'{self.site_url}/play/{slug}/{n}')
            if d:
                for e in d.get('episodes') or []:
                    u = e.get('hls') or e.get('mp4') or ''
                    if u:
                        got[int(e.get('n'))] = u
        for n in range(3, total + 1, 2):
            d = self._hg(f'{self.site_url}/play/{slug}/{n}')
            if d:
                for e in d.get('episodes') or []:
                    u = e.get('hls') or e.get('mp4') or ''
                    if u:
                        got[int(e.get('n'))] = u
            if len(got) >= total:
                break
        miss = [n for n in range(1, total + 1) if n not in got]
        for n in miss:
            d = self._hg(f'{self.site_url}/play/{slug}/{n}')
            if d:
                for e in d.get('episodes') or []:
                    u = e.get('hls') or e.get('mp4') or ''
                    if u:
                        got[int(e.get('n'))] = u
        return got
    def detailContent(self, ids):
        vid = ids[0] if ids else ''
        if not vid:
            return {"list": []}
        slug = self._slug(vid)
        d = self._hg(f'{self.site_url}/play/{slug}/1')
        title = (d or {}).get('title') or slug
        if not title:
            html = self._get(f'{self.site_url}/drama/{slug}')
            tm = re.search(r'<title>(.*?)\s*[-|]', html or '')
            title = tm.group(1).strip() if tm else slug
        poster = ''
        if d:
            drama_cover = (d.get('drama') or {}).get('cover') or {}
            poster = drama_cover.get('url') or drama_cover.get('fallback_url') or (d.get('media') or {}).get('poster_url') or ''
        detail_html = self._get(f'{self.site_url}/drama/{slug}')
        nuxt_drama = self._nuxt_drama(detail_html, slug)
        cover = nuxt_drama.get('cover') or {}
        poster = cover.get('url') or poster
        if not poster:
            om = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', detail_html or '')
            if om:
                poster = poster or om.group(1)
        total = int((d or {}).get('totalEp') or 0)
        urls = []
        if total > 0:
            for n in range(1, total + 1):
                urls.append(f'第{n}集$' + f'{self.site_url}/play/{slug}/{n}')
        vod = {"vod_id": vid, "vod_name": title, "vod_pic": self._cover_candidates(poster, cover.get('fallback_url')), "vod_remarks": f'更新至 {total} 集' if total else '', "type_name": (d or {}).get('line') or '', "vod_play_from": "主线路", "vod_play_url": '#'.join(urls)}
        return {"list": [vod]}
    def searchContent(self, key, quick, pg='1'):
        if not (key or '').strip():
            return {"list": []}
        pg = int(pg) if str(pg).isdigit() else 1
        ls, pc = self._list('search', pg, str(key).strip())
        return {"list": ls, "page": pg, "pagecount": pc, "limit": self.page_size, "total": len(ls)}
    def playerContent(self, flag, id, vipFlags):
        u = id.split("$")[1] if "$" in id else id
        m = re.search(r'/play/([^/?#]+)/(\d+)(?:[/?#]|$)', u)
        if m and '.m3u8' not in u and '.mp4' not in u:
            d = self._hg(f'{self.site_url}/play/{m.group(1)}/{m.group(2)}')
            if d:
                media = d.get('media') or {}
                u = media.get('source_url') or media.get('mp4_url') or ''
        return {"parse": 0, "url": u, "header": self.headers} if u else {"parse": 1, "url": "", "header": self.headers}
    def localProxy(self, param):
        return None
