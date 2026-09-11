// ==UserScript==
// @name 18J今天
// @namespace https://ozzc.18jtoday8m4.buzz
// @version 1.0.0
// ==/UserScript==
// {"name":"18J今天","type":"js","url":"https://ozzc.18jtoday8m4.buzz"}
import cheerio from 'assets://js/lib/cheerio.min.js';

const appConfig = {
    siteName: "18J今天",
    siteUrl: "https://ozzc.18jtoday8m4.buzz"
};

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

async function init(ext) {
    console.log("初始化爬虫:", appConfig.siteName);
}

// ============ 分类列表 ============
const classList = [
    { type_id: "424", type_name: "麻豆视频" },
    { type_id: "425", type_name: "91制片厂" },
    { type_id: "426", type_name: "天美传媒" },
    { type_id: "427", type_name: "蜜桃传媒" },
    { type_id: "428", type_name: "皇家华人" },
    { type_id: "429", type_name: "星空传媒" },
    { type_id: "430", type_name: "精东影业" },
    { type_id: "431", type_name: "大象传媒" },
    { type_id: "432", type_name: "91茄子" },
    { type_id: "433", type_name: "性视界传媒" },
    { type_id: "434", type_name: "兔子先生" },
    { type_id: "435", type_name: "杏吧原创" },
    { type_id: "436", type_name: "玩偶姐姐" },
    { type_id: "437", type_name: "香蕉传媒" },
    { type_id: "438", type_name: "SA国际传媒" },
    { type_id: "439", type_name: "EDmosaic" },
    { type_id: "440", type_name: "PsychoPorn" },
    { type_id: "441", type_name: "糖心Vlog" },
    { type_id: "442", type_name: "葫芦影业" },
    { type_id: "443", type_name: "果冻传媒" },
    { type_id: "2", type_name: "国产视频" },
    { type_id: "3", type_name: "国产主播" },
    { type_id: "4", type_name: "91大神" },
    { type_id: "5", type_name: "热门事件" },
    { type_id: "6", type_name: "传媒自拍" },
    { type_id: "7", type_name: "日本有码" },
    { type_id: "8", type_name: "日本无码" },
    { type_id: "9", type_name: "日韩主播" },
    { type_id: "10", type_name: "动漫肉番" },
    { type_id: "11", type_name: "女同性恋" },
    { type_id: "12", type_name: "中文字幕" },
    { type_id: "15", type_name: "制服诱惑" },
    { type_id: "16", type_name: "AV解说" },
    { type_id: "19", type_name: "日韩无码" },
    { type_id: "21", type_name: "欧美精品" },
    { type_id: "24", type_name: "动漫精品" },
    { type_id: "25", type_name: "日韩精品" },
    { type_id: "28", type_name: "自拍偷拍" },
    { type_id: "30", type_name: "AV明星" },
    { type_id: "31", type_name: "巨乳系列" },
    { type_id: "33", type_name: "口交视频" },
    { type_id: "35", type_name: "国产精品" },
    { type_id: "36", type_name: "SM重味" },
    { type_id: "49", type_name: "国产精品2" },
    { type_id: "51", type_name: "黑料吃瓜" },
    { type_id: "52", type_name: "欧美" },
    { type_id: "54", type_name: "学生" },
    { type_id: "71", type_name: "萝莉少女" },
    { type_id: "74", type_name: "成人动漫" },
    { type_id: "79", type_name: "Cosplay" },
    { type_id: "155", type_name: "国产自拍" },
    { type_id: "165", type_name: "映画传媒" },
    { type_id: "274", type_name: "国产自拍2" },
    { type_id: "275", type_name: "主播诱惑" },
    { type_id: "276", type_name: "探花约炮" },
    { type_id: "278", type_name: "网曝吃瓜" },
    { type_id: "279", type_name: "抖阴短片" },
    { type_id: "280", type_name: "传媒剧情" },
    { type_id: "297", type_name: "国产视频2" },
    { type_id: "348", type_name: "亚洲情色" },
    { type_id: "387", type_name: "网红主播" },
    { type_id: "388", type_name: "国产传媒" },
    { type_id: "389", type_name: "探花系列" },
    { type_id: "419", type_name: "3D动漫" },
    { type_id: "422", type_name: "OnlyFans" }
];

// ============ 子分类筛选 ============
const SORT_FILTER = [
    { n: "全部", v: "" },
    { n: "最新", v: "time" },
    { n: "热门", v: "hits" }
];

const myFilters = {};
classList.forEach(function(c) {
    myFilters[c.type_id] = [
        { key: "sort", name: "排序", value: SORT_FILTER }
    ];
});

// ============ 工具函数 ============
function fixUrl(u) {
    if (!u) return '';
    if (u.startsWith('http')) return u;
    if (u.startsWith('//')) return 'https:' + u;
    if (u.startsWith('/')) return appConfig.siteUrl + u;
    return u;
}

function fixPic(u) {
    if (!u) return '';
    if (u.startsWith('http')) return u;
    if (u.startsWith('//')) return 'https:' + u;
    if (u.startsWith('/')) return appConfig.siteUrl + u;
    return u;
}

// ============ 列表解析 ============
function parseListHtml(html) {
    const $ = cheerio.load(html);
    let list = [];
    let vodIds = {};

    $("section.item-box").each(function() {
        let img = $(this).find("img.lazy-image");
        let pic = img.attr("data-src") || img.attr("src") || "";
        let a = $(this).find("a.img-box").first();
        let href = a.attr("href") || "";
        let title = a.attr("title") || $(this).find("h2 a").text().trim() || "";

        let remarks = $(this).find("span.item-auxiliary small").last().text().trim() || "";

        let vod_id = "";
        let m = href.match(/\/voddetail\/(\d+)\//);
        if (m) {
            vod_id = m[1];
        } else if (href.startsWith('/voddetail/')) {
            vod_id = href.replace(/\/voddetail\//, '').replace(/\/$/, '');
        }

        if (!vod_id || vodIds[vod_id]) return;
        vodIds[vod_id] = true;

        list.push({
            vod_id: vod_id,
            vod_name: title,
            vod_pic: fixPic(pic),
            vod_remarks: remarks
        });
    });

    return list;
}

// ============ 分页解析 ============
function extractPageCount(html) {
    let m = html.match(/共\d+条数据.*?当前\d+\/(\d+)页/);
    if (m) return parseInt(m[1]);
    m = html.match(/\/vodtype\/\d+-(\d+)\/.*?laypage_next/);
    if (m) return parseInt(m[1]);
    return 1;
}

function extractSearchPageCount(html) {
    let m = html.match(/共\d+条数据.*?当前\d+\/(\d+)页/);
    if (m) return parseInt(m[1]);
    m = html.match(/\/vodsearch\/[^"]+-(\d+)---\/.*?laypage_next/);
    if (m) return parseInt(m[1]);
    return 1;
}

// ============ 分类URL构造 ============
function buildCategoryUrl(tid, pg, extend) {
    pg = pg || 1;
    let sort = (extend && extend.sort) || '';

    // 统一使用 vodtype 路由（vodshow 排序路由该站数据量不稳定）
    if (pg > 1) {
        return appConfig.siteUrl + '/vodtype/' + tid + '-' + pg + '/';
    }
    return appConfig.siteUrl + '/vodtype/' + tid + '/';
}

// ============ 搜索URL构造 ============
function buildSearchUrl(wd, pg) {
    pg = pg || 1;
    let keyword = encodeURIComponent(wd);
    // 14段路由: /vodsearch/{keyword}----------{pg}---/
    return appConfig.siteUrl + '/vodsearch/' + keyword + '----------' + pg + '---/';
}

// ============ 首页 ============
async function home(filter) {
    let list = [];
    try {
        let resp = await req(appConfig.siteUrl + '/luckily/', {
            method: "GET",
            headers: {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        });
        let html = resp.content || '';
        list = parseListHtml(html);
    } catch (e) {
        console.error("首页推荐获取失败:", e.message);
    }

    return JSON.stringify({
        class: classList,
        filters: myFilters,
        list: list.slice(0, 30)
    });
}

// ============ 分类列表 ============
async function category(tid, pg, filter, extend) {
    pg = pg || 1;
    extend = extend || {};
    let url = buildCategoryUrl(tid, pg, extend);

    let list = [];
    let pageCount = 1;

    try {
        let resp = await req(url, {
            method: "GET",
            headers: {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",
                "Referer": appConfig.siteUrl + '/vodtype/' + tid + '/'
            }
        });
        let html = resp.content || '';
        list = parseListHtml(html);

        if (extend.sort) {
            // vodshow 排序时尝试提取页数，失败则用 vodtype 页数
            let cat2 = await req(appConfig.siteUrl + '/vodtype/' + tid + '/', {
                method: "GET",
                headers: { "User-Agent": UA, "Accept-Encoding": "identity" }
            });
            pageCount = extractPageCount(cat2.content || '');
        } else {
            pageCount = extractPageCount(html);
        }
    } catch (e) {
        console.error("分类列表获取失败:", e.message);
    }

    return JSON.stringify({
        list: list,
        page: pg,
        pageCount: pageCount,
        limit: 20
    });
}

// ============ 从播放页 HTML 提取 m3u8 直链 ============
function extractM3u8FromPlayHtml(html) {
    let m = html.match(/var\s+player_data\s*=\s*(\{[\s\S]+?\})\s*;?\s*<\/script>/);
    if (m) {
        let urlMatch = m[1].match(/"url"\s*:\s*"([^"]+)"/);
        if (urlMatch) return urlMatch[1].replace(/\\\//g, '/');
    }
    m = html.match(/var\s+player_aaaa\s*=\s*(\{[\s\S]+?\})\s*;?\s*<\/script>/);
    if (m) {
        let urlMatch = m[1].match(/"url"\s*:\s*"([^"]+)"/);
        if (urlMatch) return urlMatch[1].replace(/\\\//g, '/');
    }
    m = html.match(/(https?:\\?\/\\?\/[^\s"']+\.m3u8[^\s"']*)/);
    if (m) return m[1].replace(/\\\//g, '/');
    return "";
}

// ============ 详情 ============
async function detail(id) {
    let list = [];
    let detailUrl = appConfig.siteUrl + '/voddetail/' + id + '/';

    try {
        let resp = await req(detailUrl, {
            method: "GET",
            headers: {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",
                "Referer": appConfig.siteUrl
            }
        });
        let html = resp.content || '';
        const $ = cheerio.load(html);

        let title = $(".detail-info-wrapper h1.f-20").text().trim() ||
                    $(".detail-info-wrapper h1").first().text().trim() || "";
        let pic = $(".detail-image-wrapper img.lazy-image").attr("data-src") ||
                  $(".detail-image-wrapper img").attr("src") || "";
        let date = $(".detail-info-wrapper h6").first().text().trim() || "";
        let content = $(".detail-info-wrapper .tx-text p").first().text().trim() || title;
        let typeName = $(".detail-info-type a").attr("title") || "";

        let tags = [];
        $(".info-auxiliary-txt a[href*='/vodshow/']").each(function() {
            let tag = $(this).text().trim();
            if (tag) tags.push(tag);
        });
        if (tags.length > 0) {
            content += " 标签: " + tags.join(" ");
        }

        // 提取播放链接路径
        let playUrl = $(".detail-info-wrapper a[href*='/vodplay/']").attr("href") || "";
        if (!playUrl) {
            playUrl = $("a[href*='/vodplay/']").first().attr("href") || "";
        }
        if (playUrl && !playUrl.startsWith('/') && !playUrl.startsWith('http')) {
            playUrl = '/' + playUrl;
        }

        // 预解析 m3u8 直链（与萝莉模板一致：detail 里提取，play 直接返回）
        let m3u8Url = "";
        if (playUrl) {
            try {
                let playPageUrl = appConfig.siteUrl + playUrl;
                let playResp = await req(playPageUrl, {
                    method: "GET",
                    headers: {
                        "User-Agent": UA,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Referer": detailUrl
                    }
                });
                let playHtml = playResp.content || '';
                m3u8Url = extractM3u8FromPlayHtml(playHtml);
            } catch (e) {
                console.error("预解析m3u8失败:", e.message);
            }
        }

        // 预解析成功: 传完整 m3u8 URL 给 play; 失败: 传播放页路径
        let vodPlayUrl = "";
        if (m3u8Url) {
            vodPlayUrl = "在线播放$" + m3u8Url;
        } else if (playUrl) {
            vodPlayUrl = "在线播放$" + playUrl;
        }

        list.push({
            vod_id: String(id),
            vod_name: title,
            vod_pic: fixPic(pic),
            vod_year: date.substring(0, 4) || "",
            vod_area: typeName || "",
            vod_remarks: date,
            vod_content: content,
            vod_play_from: "18J今天",
            vod_play_url: vodPlayUrl
        });
    } catch (e) {
        console.error("详情获取失败:", e.message, "id:", id);
    }

    return JSON.stringify({ list: list });
}

// ============ 搜索 ============
async function search(wd, quick, page) {
    wd = wd || "";
    page = page || 1;

    if (!wd) {
        return JSON.stringify({ list: [], page: 1, pageCount: 1 });
    }

    let url = buildSearchUrl(wd, page);
    let list = [];
    let pageCount = 1;

    try {
        let resp = await req(url, {
            method: "GET",
            headers: {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",
                "Referer": appConfig.siteUrl + '/luckily/'
            }
        });
        let html = resp.content || '';
        list = parseListHtml(html);
        pageCount = extractSearchPageCount(html);
    } catch (e) {
        console.error("搜索失败:", e.message);
    }

    return JSON.stringify({
        list: list,
        page: page,
        pageCount: pageCount
    });
}

// ============ 播放 ============
async function play(flag, id, flags) {
    try {
        // detail 预解析成功时 id 是完整 m3u8 URL，直接返回
        if (id && id.startsWith("http")) {
            return JSON.stringify({
                parse: 0,
                Header: { "User-Agent": UA, "Referer": appConfig.siteUrl },
                url: id
            });
        }

        // 兜底: detail 预解析失败时 id 是 /vodplay/ 路径，这里再请求播放页提取
        const playPageUrl = id.startsWith('/') ? appConfig.siteUrl + id : appConfig.siteUrl + '/' + id;
        const html = (await req(playPageUrl, {
            method: "GET",
            headers: {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": appConfig.siteUrl
            }
        })).content;

        let m3u8Url = extractM3u8FromPlayHtml(html);
        if (m3u8Url) {
            return JSON.stringify({
                parse: 0,
                Header: { "User-Agent": UA, "Referer": appConfig.siteUrl },
                url: m3u8Url
            });
        }

        const $ = cheerio.load(html);
        let iframeSrc = $("iframe").attr("src");
        if (iframeSrc) {
            return JSON.stringify({
                parse: 1,
                Header: { "User-Agent": UA, "Referer": appConfig.siteUrl },
                url: fixUrl(iframeSrc)
            });
        }

        return JSON.stringify({
            parse: 1,
            Header: { "User-Agent": UA, "Referer": appConfig.siteUrl },
            url: playPageUrl
        });
    } catch (e) {
        console.error("播放失败:", e);
        return JSON.stringify({ parse: 0, url: "" });
    }
}

export default { init, home, category, detail, search, play };
