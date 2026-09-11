#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, gzip, hashlib, hmac, json, os, time, uuid
from urllib.parse import unquote
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

HOSTS = ['eyeonneb.cc', 'psfxhhox.top', 'sxqirtho.top', 'qicuknlj.top', 'hvthtcpa.top']
SIGN_SECRET = 'bRfAdi04WvugJKF1b6f0XLu0WUTZeg7c'
BODY_SECRET = b'c10ca2986a31fb46d4481ce8631c2725'
TOKEN = 'D_109c4564a704e012ba252bbb576c9d8f_10928741'
DEVICE_ID = 'aid.69e1ec93bd099d90'
PAGE_SIZE = 18

NAV_FILTERS = {
    'yuandou': [('推荐', {})],
    'aiman': [
        ('漫剧精选', {'cat_id': '1050902', 'order': 'new'}),
        ('恐怖怪谈', {'cat_id': '327401', 'tag_id': '500001', 'order': 'new'}),
        ('恐怖故事', {'cat_id': '327401', 'tag_id': '500002', 'order': 'new'})],
    'erciyuan': [
        ('里番动漫', {'cat_id': '817201', 'order': 'new'}),
        ('日漫', {'cat_id': '1050906', 'order': 'new'}),
        ('原神', {'cat_id': '900010', 'order': 'new'}),
        ('动画同人', {'cat_id': '481301', 'order': 'new'}),
        ('游戏同人', {'cat_id': '900002', 'order': 'new'}),
        ('鬼畜混剪', {'cat_id': '900004', 'order': 'new'}),
        ('国漫女神', {'cat_id': '451201', 'order': 'new'})],
    'caibian': [
        ('最新', {'cat_id': '246505', 'order': 'new'}),
        ('推荐', {'cat_id': '246505', 'order': 'hot'}),
        ('全部', {'cat_id': '246505'})],
    'zhenren': [
        ('现代都市', {'cat_id': '817202', 'order': 'new'}),
        ('古装国风', {'cat_id': '900006', 'order': 'new'}),
        ('校园职场', {'cat_id': '1039301', 'order': 'new'}),
        ('民国', {'cat_id': '1050901', 'order': 'new'}),
        ('重生穿越', {'cat_id': '900007', 'order': 'new'}),
        ('系统异能', {'cat_id': '900008', 'order': 'new'}),
        ('荒岛', {'cat_id': '1050903', 'order': 'new'})],
    'mod': [('最新', {'cat_id': '900011', 'order': 'new'})],
    'zongyi': [
        ('最新', {'cat_id': '1050905', 'order': 'new'}),
        ('推荐', {'cat_id': '1050905', 'order': 'hot'})],
    'heiliao': [
        ('最新', {'cat_id': '900012', 'order': 'new'}),
        ('推荐', {'cat_id': '900012', 'order': 'hot'})],
    'chuanmei': [
        ('糖心vlog', {'cat_id': '1050904', 'order': 'new'})]
}

CLASSES = [
    {'type_id': 'all', 'type_name': '全部'},
    {'type_id': 'yuandou', 'type_name': '黄豆原创'},
    {'type_id': 'aiman', 'type_name': 'AI漫剧'},
    {'type_id': 'erciyuan', 'type_name': '二次元'},
    {'type_id': 'caibian', 'type_name': '擦边短剧'},
    {'type_id': 'zhenren', 'type_name': '真人短剧'},
    {'type_id': 'mod', 'type_name': '魔改短剧'},
    {'type_id': 'zongyi', 'type_name': '综艺'},
    {'type_id': 'heiliao', 'type_name': '黑料'},
    {'type_id': 'chuanmei', 'type_name': '国产传媒'},
    {'type_id': 'rank', 'type_name': '排行榜'},
    {'type_id': 'topic', 'type_name': '专题'}
]

class HuangDouAPI:
    def __init__(self, host=None, session_id=None, token=TOKEN, device_id=DEVICE_ID, timeout=12, retries=1):
        self.hosts = ([host] if host else []) + [x for x in HOSTS if x != host]
        self.session_id = session_id or uuid.uuid4().hex
        self.token, self.device_id = token, device_id
        self.timeout, self.retries = int(timeout), max(1, int(retries))
        self.http = requests.Session()

    @staticmethod
    def key(request_id):
        return hmac.new(BODY_SECRET, bytes.fromhex(request_id.replace('-', '')), hashlib.sha256).digest()

    def sign(self, host, path, timestamp, request_id):
        raw = '|'.join((SIGN_SECRET, self.session_id, request_id, str(timestamp), host + path))
        return hashlib.md5(raw.encode()).hexdigest() + '-' + str(timestamp)

    def encode(self, data, request_id):
        obj = {'token': self.token, 'deviceId': self.device_id, 'data': data or {}}
        raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()
        packed, iv = gzip.compress(raw, compresslevel=6, mtime=0), os.urandom(16)
        return iv + AES.new(self.key(request_id), AES.MODE_CBC, iv).encrypt(pad(packed, 16))

    def decode(self, body, request_id):
        if not isinstance(body, bytes) or len(body) < 32 or len(body) % 16:
            raise ValueError('响应密文长度异常')
        packed = unpad(AES.new(self.key(request_id), AES.MODE_CBC, body[:16]).decrypt(body[16:]), 16)
        return json.loads(gzip.decompress(packed).decode('utf-8'))

    def request(self, path, data=None):
        errors = []
        for host in self.hosts:
            for attempt in range(1, self.retries + 1):
                rid, now = str(uuid.uuid4()), int(time.time())
                body = self.encode(data or {}, rid)
                headers = {'user-agent': 'Dart/3.7 (dart:io)', 'time': str(now),
                    'accept-encoding': 'gzip', 'systemname': 'Android',
                    'content-type': 'application/x-www-form-urlencoded', 'devicebrand': 'google',
                    'systemversion': '11', 'sign': self.sign(host, path, now, rid),
                    'devicetype': 'android', 'version': '1.1.1', 'devicemodel': 'Pixel 4',
                    'requestid': rid, 'sessionid': self.session_id, 'content-length': str(len(body))}
                try:
                    res = self.http.post('https://' + host + path, data=body, headers=headers, timeout=self.timeout)
                    if res.status_code != 200: raise RuntimeError('HTTP %s' % res.status_code)
                    obj = self.decode(res.content, rid)
                    if not isinstance(obj, dict): raise ValueError('响应类型异常')
                    return obj
                except Exception as e:
                    errors.append('%s#%d %s' % (host, attempt, e))
        raise RuntimeError('所有 Host 请求失败：' + ' | '.join(errors))

    def drama_list(self, page=1, **filters):
        data = {'page': str(page), 'page_size': str(PAGE_SIZE)}
        for key in ('order', 'cat_id', 'tag_id', 'source', 'canvas', 'keywords', 'update_status'):
            if filters.get(key) not in (None, ''): data[key] = str(filters[key])
        return self.request('/api/drama/list', data)

    def detail(self, drama_id): return self.request('/api/drama/detail', {'id': str(drama_id), 'type': 'drama'})
    def play(self, drama_id, seq): return self.request('/api/drama/play', {'id': str(drama_id), 'type': 'drama', 'seq': str(seq)})
    def rank(self, page=1): return self.request('/api/drama/rank', {'page': str(page)})
    def topic_list(self, page=1): return self.request('/api/drama/topicList', {'page': str(page)})
    def topic_detail(self, topic_id): return self.request('/api/drama/topicDetail', {'id': str(topic_id), 'page': '1'})

class Spider:
    def __init__(self): self.api = HuangDouAPI()
    def getName(self): return '黄豆短剧'
    def getDependence(self): return []
    def setContext(self, context): self.context = context
    def getKey(self): return 'huangdou'
    def getDesc(self): return '黄豆短剧APP Python源'

    def init(self, extend=''):
        if not extend: return
        try:
            c = json.loads(extend) if isinstance(extend, str) else extend
            if isinstance(c, dict):
                self.api = HuangDouAPI(c.get('host'), c.get('sessionId'), c.get('token', TOKEN),
                    c.get('deviceId', DEVICE_ID), c.get('timeout', 12), c.get('retries', 1))
        except Exception as e: print('[黄豆短剧][配置异常]', e)

    @staticmethod
    def _data(obj):
        d = obj.get('data', {}) if isinstance(obj, dict) else {}
        return d if isinstance(d, dict) else {}

    @classmethod
    def _items(cls, obj):
        if isinstance(obj, list): return obj
        d = cls._data(obj) or (obj if isinstance(obj, dict) else {})
        fallback = []
        for key in ('list', 'items', 'rows', 'data'):
            if isinstance(d.get(key), list):
                if d[key]: return d[key]
                fallback = d[key]
        return fallback

    @staticmethod
    def _id(x): return str(x.get('drama_id') or x.get('id') or x.get('vod_id') or '')
    @staticmethod
    def _name(x): return x.get('name') or x.get('title') or x.get('drama_name') or '未知短剧'
    @staticmethod
    def _pic(x): return x.get('img') or x.get('img_y') or x.get('img_x') or x.get('cover') or x.get('image') or ''

    def _vod(self, x):
        count = x.get('episode_count') or x.get('episodes_count') or x.get('drama_count') or ''
        remark = x.get('remark') or x.get('update_label') or (str(count) + '集' if count else '')
        return {'vod_id': self._id(x), 'vod_name': self._name(x), 'vod_pic': self._pic(x), 'vod_remarks': str(remark)}

    @staticmethod
    def _pack(obj, prefix):
        raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()
        return prefix + base64.urlsafe_b64encode(raw).decode().rstrip('=')

    @staticmethod
    def _unpack(value, prefix):
        try:
            value = str(value)
            if not value.startswith(prefix): return {}
            text = value[len(prefix):] + '=' * (-len(value[len(prefix):]) % 4)
            obj = json.loads(base64.urlsafe_b64decode(text).decode())
            return obj if isinstance(obj, dict) else {}
        except Exception: return {}

    @staticmethod
    def _route(tid):
        if isinstance(tid, dict): return str(tid.get('id') or '')
        text = unquote(str(tid or '')).strip()
        try:
            obj = json.loads(text)
            if isinstance(obj, dict): return str(obj.get('id') or text)
        except Exception: pass
        return text

    def _filters(self):
        return {code: [{'key': 'tab', 'name': '子分类', 'value': [
            {'n': name, 'v': self._pack(params, 'f_')} for name, params in entries]}]
            for code, entries in NAV_FILTERS.items()}

    @staticmethod
    def _page(page, videos, size=PAGE_SIZE, total=None):
        more = len(videos) >= size
        return {'page': page, 'pagecount': page + (1 if more else 0), 'limit': len(videos),
            'total': total if total is not None else (999999 if more else len(videos)), 'list': videos}

    def homeContent(self, filter=False): return {'class': list(CLASSES), 'filters': self._filters()}

    def homeVideoContent(self):
        try: videos = [self._vod(x) for x in self._items(self.api.drama_list(1)) if self._id(x)]
        except Exception as e: print('[黄豆短剧][首页异常]', e); videos = []
        return {'list': videos}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        page = max(1, int(pg or 1))
        try:
            tid = self._route(tid) or 'all'
            ext = {}
            if extend:
                if isinstance(extend, str):
                    try: ext = json.loads(extend) if extend else {}
                    except Exception: ext = {}
                elif isinstance(extend, dict):
                    ext = extend

            if tid == 'rank':
                videos = [self._vod(x) for x in self._items(self.api.rank(page)) if self._id(x)]
                return self._page(page, videos, len(videos) or PAGE_SIZE)
            if tid == 'topic':
                videos = [{'vod_id': 'topic_' + str(x.get('id') or ''),
                    'vod_name': x.get('title') or x.get('name') or '专题', 'vod_pic': self._pic(x),
                    'vod_remarks': str(x.get('sub_title') or x.get('drama_count') or ''),
                    'vod_tag': 'folder'}
                    for x in self._items(self.api.topic_list(page)) if x.get('id')]
                return self._page(page, videos, len(videos) or PAGE_SIZE)
            if tid.startswith('topic_'):
                items = self._items(self.api.topic_detail(tid.split('_', 1)[1]))
                start = (page - 1) * 24
                videos = [self._vod(x) for x in items[start:start + 24] if self._id(x)]
                total = len(items)
                return {'page': page, 'pagecount': max(1, (total + 23) // 24),
                    'limit': len(videos), 'total': total, 'list': videos}
            if tid in NAV_FILTERS:
                tab_value = ext.get('tab') if isinstance(ext, dict) else None
                params = self._unpack(tab_value or '', 'f_') or dict(NAV_FILTERS[tid][0][1])
            else:
                params = {}
            videos = [self._vod(x) for x in self._items(self.api.drama_list(page, **params)) if self._id(x)]
            return self._page(page, videos)
        except Exception as e:
            print('[黄豆短剧][分类异常]', e)
            return {'page': page, 'pagecount': 1, 'limit': 0, 'total': 0, 'list': []}

    def _plain_category(self, name):
        return str(name or '').strip()

    def _episodes(self, drama_id, eps, total):
        by_seq = {}
        for index, ep in enumerate(eps or [], 1):
            if isinstance(ep, dict):
                seq = int(ep.get('seq') or ep.get('episode') or ep.get('sort') or index)
                by_seq[seq] = ep
        try: total = int(total or 0)
        except Exception: total = 0
        if by_seq: total = max(total, max(by_seq))
        if total <= 0: total = len(by_seq)
        play, free_count, unlocked = [], 0, 0
        for seq in range(1, total + 1):
            ep = by_seq.get(seq) or {}
            typ, bought, price = str(ep.get('type') or '').lower(), bool(ep.get('is_buy')), ep.get('price') or 0
            if not ep: label = '补全'
            elif typ == 'free': label = '免费'; free_count += 1; unlocked += 1
            elif bought: label = '已购'; unlocked += 1
            elif typ == 'coin': label = '金币%s' % price
            elif typ == 'vip': label = 'VIP'
            else: label = typ.upper() if typ else '播放'
            raw_name = ep.get('name') or ep.get('title') or ''
            name = raw_name if '集' in str(raw_name) else '第%s集' % seq
            direct = (not bool(ep)) or (typ in ('coin', 'vip') and not bought)
            token = self._pack({'id': drama_id, 'seq': str(seq), 'direct': direct}, 'p_')
            play.append('[%s]%s$%s' % (label, name, token))
        return play, free_count, unlocked, total

    def detailContent(self, ids):
        drama_id = str(ids[0] if isinstance(ids, (list, tuple)) else ids)
        try:
            if drama_id.startswith('topic@@'):
                videos = [self._vod(x) for x in self._items(self.api.topic_detail(drama_id.split('@@', 1)[1])) if self._id(x)]
                return {'list': videos}
            data = self._data(self.api.detail(drama_id))
            eps = data.get('episodes') or []
            play, free_count, unlocked, total = self._episodes(drama_id, eps, data.get('episode_count') or len(eps))
            category = str(data.get('category') or '')
            content = str(data.get('description') or '')
            if category:
                content = '分类：' + self._plain_category(category) + ('\n' + content if content else '')
            remark = '免费%s集/共%s集' % (free_count, total) if total else ''
            if unlocked > free_count: remark += ' 已解锁%s集' % unlocked
            if total and len(eps) < total: remark += ' 已补全%s集' % total
            vod = self._vod(data)
            vod.update({'vod_id': drama_id, 'vod_remarks': remark or vod.get('vod_remarks', ''),
                'vod_content': content, 'vod_play_from': '黄豆短剧', 'vod_play_url': '#'.join(play)})
            return {'list': [vod]}
        except Exception as e: print('[黄豆短剧][详情异常]', e); return {'list': []}

    def searchContent(self, key, quick=False, pg=1):
        page = max(1, int(pg or 1))
        try:
            videos = [self._vod(x) for x in self._items(
                self.api.drama_list(page, keywords=str(key or '').strip())) if self._id(x)]
            return self._page(page, videos)
        except Exception as e:
            print('[黄豆短剧][搜索异常]', e)
            return {'page': page, 'pagecount': 1, 'limit': 0, 'total': 0, 'list': []}

    def recommendContent(self, ids, pg):
        """相关推荐 - 基于当前视频ID获取同分类推荐"""
        try:
            drama_id = str(ids[0] if isinstance(ids, (list, tuple)) else ids)
            drama_id = drama_id.replace('rp_', '').strip()
            if not drama_id:
                return {'list': []}
            
            detail_data = self._data(self.api.detail(drama_id))
            category = detail_data.get('category', '')
            
            page = max(1, int(pg or 1))
            params = {'page': page, 'page_size': str(PAGE_SIZE)}
            
            if category:
                params['keywords'] = str(category)
            else:
                params['order'] = 'hot'
            
            resp = self.api.drama_list(**params)
            items = self._items(resp)
            
            videos = []
            for x in items:
                vid = self._id(x)
                if vid and vid != drama_id and vid != 'rp_' + drama_id:
                    videos.append(self._vod(x))
                    if len(videos) >= 18:
                        break
            
            return {'list': videos}
        except Exception as e:
            print('[黄豆短剧][推荐异常]', e)
            return {'list': []}

    def playerContent(self, flag, id, vipFlags=None):
        header = {'User-Agent': 'Dart/3.7 (dart:io)'}
        try:
            token = self._unpack(id, 'p_')
            drama_id = str(token.get('id') or '')
            seq = str(token.get('seq') or '1')
            direct = bool(token.get('direct'))
            if not drama_id:
                raise ValueError('播放 ID 无效')

            if not direct:
                try:
                    response = self.api.play(drama_id, seq)
                    if response.get('status') == 'y':
                        data = self._data(response)
                        url = (data.get('m3u8') or data.get('url') or data.get('play_url')
                               or data.get('preview_m3u8') or '')
                        if url:
                            return {'parse': 0, 'url': url, 'header': header, 'msg': ''}
                except Exception as e:
                    print('[黄豆短剧][官方播放回退]', e)

            url = 'https://xqjzvcvt.top/api/drama/hls/%s/%s/play.m3u8?line=free' % (
                drama_id, seq
            )
            return {'parse': 0, 'url': url, 'header': header, 'msg': ''}
        except Exception as e:
            print('[黄豆短剧][播放异常]', e)
            return {'parse': 1, 'url': '', 'header': header}

    def localProxy(self, param): return [404, 'text/plain', 'not found']
    def isVideoFormat(self, url): return bool(url and ('.m3u8' in url or '.mp4' in url))
    def manualVideoCheck(self): return False
    def destroy(self): pass