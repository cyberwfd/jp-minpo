# 电视直播订阅（每日自动更新）

飞牛影视里订阅一次即可，每天自动刷新。

## 订阅地址

| 列表 | 地址 | 台数 | 刷新时间 |
|------|------|------|----------|
| 日本 | https://raw.githubusercontent.com/cyberwfd/jp-minpo/main/jp.m3u | 16 | 每天 06:00 |
| 中国 | https://raw.githubusercontent.com/cyberwfd/jp-minpo/main/cn.m3u | 60 | 每天 07:00 |
| 英美 | https://raw.githubusercontent.com/cyberwfd/jp-minpo/main/en.m3u | 16 | 每天 07:00 |

## 日本 (jp.m3u)

### EPG（飞牛里和订阅地址一起填，两个都加）

- https://epgshare01.online/epgshare01/epg_ripper_JP1.xml.gz
- https://epgshare01.online/epgshare01/epg_ripper_JP2.xml.gz
- https 拉不到就换 http

### 包含的台（16）

地上波：日本テレビ / テレビ朝日 / TBSテレビ / テレビ東京 / フジテレビ / TOKYO MX1
BS：BS朝日 / BS-TBS / BSフジ / BSテレ東 / BS10スターチャンネル / NHK BS / WOWOWプライム
其他：NHK World-Japan / NHK World Premium / Weathernews

（BS日テレ暂无可用源，找到后会加回来）

## 中国 (cn.m3u)

- 来源：best-fan/iptv-sources，每台只留最高清（同清晰度取响应最快）
- 央视 1-17 + 卫视 + 凤凰等，共 60 台
- 每天 07:00 自动重建（`scripts/rebuild.py`）

## 英美 (en.m3u)

- 美国娱乐（HBO、Cinemax、Starz、AMC 等）+ 新闻（CNN、Fox News、MSNBC 等），英国 BBC News 等，共 16 台
- 每天 07:00 自动重建（`scripts/rebuild.py`）

## 自动维护

- `.github/workflows/daily-check.yml`：日本，每天北京时间 06:00 运行
- `.github/workflows/refresh-cn-en.yml`：中国 + 英美，每天北京时间 07:00 运行
- 日本：`refresh.sh` 重抓所有带 `# tvivu: <slug>` 标记的当日签名链（验活通过才写入）；没有标记的静态源跳过
- 日本：`check.sh` 逐台验活，挂了的台会在 Actions 日志里标 DEAD

某台长期挂掉：在 Actions 日志里看到 DEAD 台名，按 `refresh.sh` 的 tvivu 模式手动重抓一条换上即可。
netgenx 源（BSフジ/BSテレ東）的台标映射若再次错乱，以实际播出台标为准重标即可。
