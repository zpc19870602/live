import { Crypto, load, _ } from '../../cat.js';
/**
 * 直播源（修正版）
 * 适配平台数组结构：每个平台为一个分类，点击后直接进入播放详情
 */

let siteUrl = 'http://api.hclyz.com:81/mf/';
let siteKey = '';
let siteType = 0;
let platformList = [];      // 存储平台数组

async function request(reqUrl, postData, post) {
    let res = await req(reqUrl, {
        method: post ? 'post' : 'get',
        data: postData || {},
        postType: post ? 'form' : '',
    });
    return res.content;
}

async function init(cfg) {
    siteKey = cfg.skey;
    siteType = cfg.stype;
    if (cfg.ext) {
        siteUrl = cfg.ext;
    }
    const jsonTxt = await request(siteUrl + 'json.txt');
    const data = JSON.parse(jsonTxt);
    // 原始数据是 { "pingtai": [...] } 结构
    platformList = data.pingtai || [];
}

async function home(filter) {
    // 将所有平台归为一个分类（也可按需拆分为多个分类，但通常直播源列表直接展示即可）
    const classes = [{
        type_id: 'all',
        type_name: '全部平台'
    }];
    return JSON.stringify({ class: classes });
}

async function category(tid, pg, filter, ext) {
    // 不分页，直接返回所有平台作为视频列表
    const videos = platformList.map(item => {
        return {
            vod_id: item.address,          // 详情文件的地址，如 jsonweishizhibo.txt
            vod_name: item.title,
            vod_pic: item.xinimg,
            vod_remarks: item.Number       // 显示视频数量或直播状态
        };
    });
    return JSON.stringify({
        list: videos,
        page: pg,
        pagecount: 1,
        total: videos.length
    });
}

async function detail(id) {
    try {
        const detailUrl = siteUrl + id;
        const resText = await request(detailUrl);
        const resJson = JSON.parse(resText);
        const zhuboList = resJson.zhubo || [];
        const playUrls = zhuboList.map(vod => {
            return vod.title + '$' + vod.address;
        }).join('#');
        const video = {
            vod_play_from: '直播源',
            vod_play_url: playUrls,
            vod_content: '请选择播放线路'
        };
        return JSON.stringify({ list: [video] });
    } catch (e) {
        console.log('detail error', e);
        return null;
    }
}

async function play(flag, id, flags) {
    return JSON.stringify({
        parse: 0,
        url: id,
    });
}

export function __jsEvalReturn() {
    return {
        init: init,
        home: home,
        category: category,
        detail: detail,
        play: play,
    };
}