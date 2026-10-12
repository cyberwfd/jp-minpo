# 日本电视每日自动更新订阅

飞牛影视里订阅一次即可，每天早上 6 点自动刷新（日テレ签名链每日重抓，其余台验活）。

## 订阅地址

```
https://raw.githubusercontent.com/cyberwfd/jp-minpo/main/jp.m3u
```

## EPG（飞牛里和订阅地址一起填，两个都加）

- https://epgshare01.online/epgshare01/epg_ripper_JP1.xml.gz
- https://epgshare01.online/epgshare01/epg_ripper_JP2.xml.gz
- https 拉不到就换 http

## 包含的台（16）

地上波：日本テレビ / テレビ朝日 / TBSテレビ / テレビ東京 / フジテレビ / TOKYO MX1
BS：BS日テレ / BS朝日 / BS-TBS / BSテレ東 / BSフジ / WOWOWプライム / BS10スターチャンネル
其他：NHK World-Japan / NHK World Premium / Weathernews

## 自动维护

- `.github/workflows/daily-check.yml`：每天北京时间 06:00 运行
- `refresh.sh`：重抓日テレ当日签名链（验活通过才写入）
- `check.sh`：逐台验活，挂了的台会在 Actions 日志里标 DEAD

某台长期挂掉：在 Actions 日志里看到 DEAD 台名，按 `refresh.sh` 的 tvivu 模式手动重抓一条换上即可。
