#!/bin/bash
# 每日验活：逐个请求 m3u 中的每个源，检查 HTTP 200 且 playlist 看起来是直播流
# 直播判定：playlist 里有 .ts/.m3u8 段，或有 #EXT-X-MEDIA-SEQUENCE（pxfy 签名源的段 URL 无扩展名）
# 用法：./check.sh jp.m3u ; 退出码 0=全活，非0=有挂的台（会打印台名+URL）
set -u
M3U="${1:-jp.m3u}"
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
dead=0
name=""
while IFS= read -r line; do
  case "$line" in
    '#EXTINF:'*) name="${line##*,}" ;;
    '# tvivu:'*) : ;;
    'http'*)
      body="$(curl -s --max-time 15 -A "$UA" "$line" 2>/dev/null)"
      if printf '%s' "$body" | grep -qE '\.(ts|m3u8)(\?|$)|#EXT-X-MEDIA-SEQUENCE'; then
        echo "OK   $name"
      else
        echo "DEAD $name  -> $line"
        dead=$((dead+1))
      fi
      ;;
  esac
done < "$M3U"
echo "--- $dead dead ---"
exit "$dead"
