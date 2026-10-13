#!/usr/bin/env python3
"""Rebuild cn.m3u and en.m3u from upstream sources.

CN: best-fan/iptv-sources cn_all_status + cn_pay_status, deduped to
    one entry per channel (highest resolution, tie-break lowest response-time).
EN: 16 user-curated US/UK channels. 15 from hacks.tools eng.m3u (matched by
    tvg-id), BBC News from the official BBC CDN URL. If a channel is missing
    from the fresh upstream, keep the old URL from the current file.
"""
import re
import sys
import urllib.request
from collections import defaultdict

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

def parse_m3u(text):
    """Parse m3u, handling #EXTVLCOPT lines between EXTINF and URL."""
    lines = text.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("#EXTINF"):
            name = l.rsplit(",", 1)[-1].strip()
            tvg = re.search(r'tvg-name="([^"]*)"', l)
            logo = re.search(r'tvg-logo="([^"]*)"', l)
            grp = re.search(r'group-title="([^"]*)"', l)
            rt = re.search(r'response-time="([^"]*)"', l)
            tvgid = re.search(r'tvg-id="([^"]*)"', l)
            url = ""
            j = i + 1
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                j += 1
            if j < len(lines) and lines[j].startswith("http"):
                url = lines[j]
            entries.append({
                "name": name,
                "tvg": tvg.group(1) if tvg else "",
                "logo": logo.group(1) if logo else "",
                "grp": grp.group(1) if grp else "",
                "rt": rt.group(1) if rt else "",
                "tvgid": tvgid.group(1) if tvgid else "",
                "url": url,
            })
            i = j + 1
        else:
            i += 1
    return entries

# ---------------- CN ----------------

def cn_canonical(e):
    base = re.sub(r"\[\d+\]\[[A-Za-z]+\]", "", e["tvg"]).strip()
    if base:
        return base
    n = e["name"]
    n = re.sub(r"\s*\(\d+p\)", "", n)
    n = re.sub(r"(综合|中文国际|纪录|财经|体育|少儿|电影|电视剧|新闻|综艺|科教|戏曲|社会与法|农业农村|国防军事|奥林匹克|4K|8K)$", "", n)
    return n.replace("-", "").replace(" ", "")

def cn_resolution(e):
    m = re.search(r"\[(\d+)\]", e["tvg"])
    if m:
        return int(m.group(1))
    m = re.search(r"\((\d+)p\)", e["name"])
    if m:
        return int(m.group(1))
    return 0

def cn_resp_ms(e):
    m = re.search(r"(\d+)", e["rt"])
    return int(m.group(1)) if m else 99999

def cn_display(canon):
    if canon.startswith("CCTV"):
        num = re.sub(r"\D", "", canon)
        plus = "+" if "+" in canon else ""
        return f"CCTV-{num}{plus}"
    return canon

def rebuild_cn():
    all_entries = []
    for fname in ("cn_all_status", "cn_pay_status"):
        text = fetch(f"https://raw.githubusercontent.com/best-fan/iptv-sources/main/{fname}.m3u8")
        all_entries.extend(parse_m3u(text))
    groups = defaultdict(list)
    for e in all_entries:
        groups[cn_canonical(e)].append(e)
    out = ["#EXTM3U",
           "# 来源: best-fan/iptv-sources cn_all_status.m3u8 + cn_pay_status.m3u8 (自动刷新)",
           "# 去重: 每台只留最高清 (同清晰度取响应最快)"]
    for canon, cands in sorted(groups.items()):
        best = sorted(cands, key=lambda x: (-cn_resolution(x), cn_resp_ms(x)))[0]
        out.append(f'#EXTINF:-1 tvg-name="{cn_display(canon)}" tvg-logo="{best["logo"]}" group-title="{best["grp"]}",{cn_display(canon)}')
        out.append(best["url"])
    return "\n".join(out) + "\n"

# ---------------- EN ----------------

# (display name, group, eng.m3u tvg-id to match, fallback URL)
EN_ENG = [
    ("HBO", "美国娱乐", "HBO.us@East"),
    ("HBO Hits", "美国娱乐", "HBOHits.us@East"),
    ("Cinemax", "美国娱乐", "Cinemax.us@West"),
    ("MoreMax", "美国娱乐", "CinemaxHits.us@East"),
    ("Starz", "美国娱乐", "Starz.us@West"),
    ("Starz Comedy", "美国娱乐", "StarzComedy.us@East"),
    ("AMC", "美国娱乐", "AMC.us@EastHD"),
    ("BBC America", "美国娱乐", "BBCAmerica.us@East"),
    ("IFC", "美国娱乐", "IFC.us@East"),
    ("CNN", "美国新闻", "CNN.us@SD"),
    ("CNN International", "美国新闻", "CNNInternational.us@Europe"),
    ("Fox News", "美国新闻", "FoxNewsChannel.us@SD"),
    ("Bloomberg", "美国新闻", "BloombergTV.us@US"),
    ("HLN", "美国新闻", "HLN.us@SD"),
    ("Newsmax", "美国新闻", "NewsmaxTV.us@SD"),
]
BBC_NEWS_URL = "https://vs-hls-push-ww-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_news_channel_hd/t=3840/v=pv14/b=5070016/main.m3u8"

def read_old_urls(path):
    urls = {}
    try:
        lines = open(path).read().splitlines()
        for i, l in enumerate(lines):
            if l.startswith("#EXTINF"):
                name = l.rsplit(",", 1)[-1].strip()
                if i + 1 < len(lines) and lines[i + 1].startswith("http"):
                    urls[name] = lines[i + 1]
    except FileNotFoundError:
        pass
    return urls

def rebuild_en():
    text = fetch("https://live.hacks.tools/iptv/languages/eng.m3u")
    eng = parse_m3u(text)
    by_tvgid = {e["tvgid"]: e for e in eng}
    old = read_old_urls("en.m3u")
    out = ["#EXTM3U",
           "# 美英经典频道 - 用户筛选版 (自动刷新)",
           "# 16 个台, 来源: hacks.tools eng.m3u + Free-TV (BBC News)"]
    for name, grp, tvgid in EN_ENG:
        e = by_tvgid.get(tvgid)
        url = e["url"] if e and e["url"] else old.get(name, "")
        if not url:
            print(f"WARN: no URL for {name}, skipping", file=sys.stderr)
            continue
        out.append(f'#EXTINF:-1 tvg-name="{name}" group-title="{grp}",{name}')
        out.append(url)
    out.append('#EXTINF:-1 tvg-name="BBC News" group-title="英国新闻",BBC News')
    out.append(BBC_NEWS_URL)
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    cn = rebuild_cn()
    open("cn.m3u", "w").write(cn)
    print(f"cn.m3u: {cn.count('#EXTINF')} channels")
    en = rebuild_en()
    open("en.m3u", "w").write(en)
    print(f"en.m3u: {en.count('#EXTINF')} channels")
