/**
 * 直播源 - 独立健壮版
 * 适配 { "pingtai": [...] } 结构
 */

let siteUrl = 'http://api.hclyz.com:81/mf/';
let platformList = [];

// 通用请求方法（适配影视仓环境）
async function request(url) {
    // 尝试使用全局 req（影视仓标准）
    if (typeof req !== 'undefined') {
        let resp = await req(url, { method: 'get' });
        return resp.content;
    }
    // 降级使用 fetch（如果存在）
    if (typeof fetch !== 'undefined') {
        let resp = await fetch(url);
        return await resp.text();
    }
    throw new Error('No available request method (req/fetch)');
}

async function init(cfg) {
    try {
        if (cfg.ext) siteUrl = cfg.ext;
        console.log('[sebo] init, siteUrl=', siteUrl);
        
        const jsonTxt = await request(siteUrl + 'json.txt');
        console.log('[sebo] json.txt length=', jsonTxt.length);
        
        const data = JSON.parse(jsonTxt);
        platformList = data.pingtai || [];
        console.log('[sebo] 平台数量=', platformList.length);
    } catch (e) {
        console.log('[sebo] init error:', e.message);
        platformList = [];
    }
}

async function home(filter) {
    // 返回一个分类，名为“全部平台”
    return JSON.stringify({
        class: [{ type_id: 'all', type_name: '全部平台' }]
    });
}

async function category(tid, pg, filter, ext) {
    try {
        const videos = platformList.map(item => ({
            vod_id: item.address,
            vod_name: item.title,
            vod_pic: item.xinimg,
            vod_remarks: String(item.Number) + '个频道'
        }));
        console.log('[sebo] category 返回数量=', videos.length);
        return JSON.stringify({
            list: videos,
            page: 1,
            pagecount: 1,
            total: videos.length
        });
    } catch (e) {
        console.log('[sebo] category error:', e);
        return JSON.stringify({ list: [], page: 1, pagecount: 1, total: 0 });
    }
}

async function detail(id) {
    try {
        const detailUrl = siteUrl + id;
        console.log('[sebo] 请求详情:', detailUrl);
        const text = await request(detailUrl);
        const data = JSON.parse(text);
        const zhuboList = data.zhubo || [];
        const playUrls = zhuboList.map(v => v.title + '$' + v.address).join('#');
        return JSON.stringify({
            list: [{
                vod_play_from: '直播线路',
                vod_play_url: playUrls,
                vod_content: '共 ' + zhuboList.length + ' 条线路'
            }]
        });
    } catch (e) {
        console.log('[sebo] detail error:', e);
        return JSON.stringify({ list: [] });
    }
}

async function play(flag, id, flags) {
    return JSON.stringify({ parse: 0, url: id });
}

export function __jsEvalReturn() {
    return { init, home, category, detail, play };
}