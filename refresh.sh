#!/bin/bash
# 每日刷新日テレ签名链：调 tvivu XHR API 抓新链，验活通过才写入 jp.m3u
# 用法：bash refresh.sh [jp.m3u] ; 退出码 0=已刷新，1=失败（保留旧链）
set -u
M3U="${1:-jp.m3u}"
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

json="$(curl -s --max-time 25 -A "$UA" \
  -H 'Accept: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Referer: https://tvivu.com/watch/jp-2' \
  'https://tvivu.com/api/channels/jp-2/streams' 2>/dev/null)"

new_url="$(printf '%s' "$json" | python3 -c "
import json, sys, base64
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for s in d.get('streams', []):
    u = s.get('url', '')
    b = u[1:] if u.startswith('~') else u
    b += '=' * (-len(b) % 4)
    try:
        url = base64.b64decode(b).decode()
    except Exception:
        continue
    if 'pxfy.dev' in url and 'exp=' in url:
        print(url)
        break
")"

if [ -z "$new_url" ]; then
  echo "REFRESH_FAIL: no url from tvivu api"
  exit 1
fi

pl="$(curl -s --max-time 20 -A "$UA" "$new_url" 2>/dev/null)"
printf '%s' "$pl" | grep -q '#EXTM3U' || { echo "REFRESH_FAIL: bad playlist"; exit 1; }
printf '%s' "$pl" | grep -q 'EXT-X-MEDIA-SEQUENCE' || { echo "REFRESH_FAIL: not a live playlist"; exit 1; }

python3 - "$M3U" "$new_url" << 'PYEOF'
import sys
m3u_path, new_url = sys.argv[1], sys.argv[2].strip()
with open(m3u_path) as f:
    lines = f.readlines()
out, i, done = [], 0, False
while i < len(lines):
    out.append(lines[i])
    if not done and lines[i].startswith('#EXTINF:') and '日本テレビ' in lines[i]:
        i += 1
        if i < len(lines) and lines[i].startswith('http'):
            out.append(new_url + '\n')
            done = True
        else:
            out.append(lines[i])
    i += 1
if done:
    open(m3u_path, 'w').writelines(out)
    print("NTV chain refreshed")
else:
    print("NTV entry not found, no change")
    sys.exit(1)
PYEOF
