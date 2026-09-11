# -*- coding: utf-8 -*-
# 黄瓜短剧 | OK影视/TVBox 通用 | 基于base.spider | 全集解锁版(窗口步进取流)
import sys
import re
import json
import math
import requests
from urllib.parse import quote
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
    def _cards(self, html):
        out, seen = [], set()
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
            out.append({"vod_id": self._abs(vid), "vod_name": nm.group(1).strip(), "vod_pic": self._pic(item), "vod_remarks": em.group(1).strip() if em else '', "style": {"type": "rect", "ratio": 0.75}})
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
            u1, up = f'{self.site_url}/tag/{t}', lambda n: f'{self.site_url}/tag/{t}/page/{n}'
        elif s == 'search':
            qs = quote(q or '')
            u1, up = f'{self.site_url}/search?q={qs}', lambda n: f'{self.site_url}/search?q={qs}&page={n}'
        else:
            u1, up = f'{self.site_url}/{s}', lambda n: f'{self.site_url}/{s}/page/{n}'
        if pg <= 1:
            html = self._get(u1)
            if not html:
                return [], 1
            i = html.find('foot-grid')
            seg = html[:i] if i > 0 else html
            ls = self._cards(seg)[:self.page_size]
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
        i = html.find('foot-grid')
        seg = html[:i] if i > 0 else html
        ls = self._cards(seg)
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
        if not m:
            return None
        try:
            return json.loads(m.group(1).replace('\\u0026', '&'))
        except Exception:
            return None
    def _slug(self, vid):
        return vid.split('/')[-1].split('?')[0] if '/' in vid else vid
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
        d = self._hg(f'{self.site_url}/play/{slug}')
        title = (d or {}).get('title') or slug
        if not title:
            html = self._get(f'{self.site_url}/play/{slug}')
            tm = re.search(r'<title>(.*?)\s*[-|]', html or '')
            title = tm.group(1).strip() if tm else slug
        poster = ''
        if d:
            eps0 = (d.get('episodes') or [{}])[0]
            poster = eps0.get('poster') or ''
        if not poster:
            html = self._get(f'{self.site_url}/play/{slug}')
            om = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html or '')
            if om:
                poster = om.group(1)
        total = int((d or {}).get('totalEp') or 0)
        urls = []
        if total > 0:
            got = self._fetch_all(slug, total)
            for n in sorted(got):
                urls.append(f'第{n}集${got[n]}')
        vod = {"vod_id": vid, "vod_name": title, "vod_pic": self._abs(poster), "vod_remarks": f'更新至 {total} 集' if total else '', "type_name": (d or {}).get('line') or '', "vod_play_from": "主线路", "vod_play_url": '#'.join(urls)}
        return {"list": [vod]}
    def searchContent(self, key, quick, pg='1'):
        if not (key or '').strip():
            return {"list": []}
        pg = int(pg) if str(pg).isdigit() else 1
        ls, pc = self._list('search', pg, str(key).strip())
        return {"list": ls, "page": pg, "pagecount": pc, "limit": self.page_size, "total": len(ls)}
    def playerContent(self, flag, id, vipFlags):
        u = id.split("$")[1] if "$" in id else id
        return {"parse": 0, "url": u, "header": self.headers} if u else {"parse": 1, "url": "", "header": self.headers}
    def localProxy(self, param):
        return None