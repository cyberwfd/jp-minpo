#!/bin/bash
# 通用刷新：jp.m3u 里所有 "# tvivu: <slug>" 标记的下一行签名链，逐个重抓并验活后替换
# 没有标记的行（如 netgenx 静态源）会被跳过，由 check.sh 负责验活
# 用法：bash refresh.sh [jp.m3u] ; 退出码 0=至少刷新一条或无需刷新，1=全部失败
set -u
M3U="${1:-jp.m3u}"
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
API='https://tvivu.com/api/channels'
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT

slugs="$(grep '^# tvivu:' "$M3U" | sed 's/# tvivu: *//' | sort -u)"
[ -z "$slugs" ] && { echo "no tvivu marks in $M3U"; exit 1; }

for slug in $slugs; do
  json="$(curl -s --max-time 25 -A "$UA" \
    -H 'Accept: application/json' \
    -H 'X-Requested-With: XMLHttpRequest' \
    -H "Referer: https://tvivu.com/watch/$slug" \
    "$API/$slug/streams" 2>/dev/null)"
  url="$(printf '%s' "$json" | python3 -c "
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
  if [ -z "$url" ]; then echo "FAIL(grab) $slug"; continue; fi
  pl="$(curl -s --max-time 20 -A "$UA" "$url" 2>/dev/null)"
  if printf '%s' "$pl" | grep -q '#EXTM3U' && \
     printf '%s' "$pl" | grep -qE 'EXT-X-MEDIA-SEQUENCE|EXT-X-STREAM-INF'; then
    printf '%s' "$url" > "$TMPD/$slug.url"
    echo "OK $slug"
  else
    echo "FAIL(verify) $slug"
  fi
done

python3 - "$M3U" "$TMPD" << 'PYEOF'
import sys, os
m3u, tmpd = sys.argv[1], sys.argv[2]
fresh = {}
for f in os.listdir(tmpd):
    if f.endswith('.url'):
        fresh[f[:-4]] = open(os.path.join(tmpd, f)).read().strip()
lines = open(m3u).read().splitlines(keepends=True)
out, i, n = [], 0, 0
while i < len(lines):
    out.append(lines[i])
    if lines[i].startswith('# tvivu:') and i + 1 < len(lines):
        slug = lines[i].split(':', 1)[1].strip()
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            out.append(lines[j]); j += 1
        if j < len(lines) and lines[j].startswith('http') and slug in fresh:
            out.append(fresh[slug] + '\n'); n += 1
        elif j < len(lines):
            out.append(lines[j])
        i = j
    i += 1
open(m3u, 'w').writelines(out)
print(f"refreshed {n} chains")
PYEOF
