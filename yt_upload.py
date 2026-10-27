#!/usr/bin/env python3
"""把成片传到 YouTube（YouTube Data API v3，只用标准库）。

授权来自环境变量：YT_CLIENT_ID、YT_CLIENT_SECRET、YT_REFRESH_TOKEN（see README.md）。

  python3 yt_upload.py --check
  python3 yt_upload.py VIDEO.mp4 --title "..." [--description-file d.txt] [--tag x ...]
                       [--privacy private|unlisted|public] [--kids yes|no]
                       [--caption FILE.srt:LANG:NAME ...]

默认 private。成功后打印视频链接，并写一行 JSON 到 stdout 最后一行。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
CHUNK = 16 * 1024 * 1024  # 必须是 256 KiB 的整数倍


def env(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"缺环境变量 {name}（see README.md）")
    return v


def access_token():
    data = urllib.parse.urlencode({
        "client_id": env("YT_CLIENT_ID"),
        "client_secret": env("YT_CLIENT_SECRET"),
        "refresh_token": env("YT_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=60) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        # invalid_grant 多半是 refresh token 失效：OAuth 应用还在 Testing 状态时 7 天就过期
        sys.exit(f"换 access token 失败：{e.code} {e.read().decode(errors='replace')}")


def call(method, url, token, body=None, headers=None, timeout=120):
    h = {"Authorization": f"Bearer {token}"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    return urllib.request.urlopen(req, timeout=timeout)


def check(token):
    with call("GET", f"{API}/channels?part=snippet&mine=true", token) as r:
        items = json.load(r).get("items", [])
    if not items:
        sys.exit("授权有效，但这个 Google 账号下没有 YouTube 频道")
    for c in items:
        print(f"频道：{c['snippet']['title']}  https://www.youtube.com/channel/{c['id']}")


def upload_video(token, path, meta):
    size = os.path.getsize(path)
    with call("POST", f"{UPLOAD}/videos?uploadType=resumable&part=snippet,status", token,
              body=json.dumps(meta).encode(),
              headers={"Content-Type": "application/json; charset=UTF-8",
                       "X-Upload-Content-Type": "video/mp4",
                       "X-Upload-Content-Length": str(size)}) as r:
        session = r.headers["Location"]

    offset, tries = 0, 0
    with open(path, "rb") as f:
        while True:
            f.seek(offset)
            chunk = f.read(CHUNK)
            end = offset + len(chunk) - 1
            try:
                with call("PUT", session, token, body=chunk, timeout=600,
                          headers={"Content-Range": f"bytes {offset}-{end}/{size}"}) as r:
                    return json.load(r)  # 200/201：传完了
            except urllib.error.HTTPError as e:
                if e.code == 308:  # 这块收到了，接着传
                    rng = e.headers.get("Range")
                    offset = int(rng.split("-")[1]) + 1 if rng else 0
                    tries = 0
                    print(f"  {offset * 100 // size}%", file=sys.stderr)
                    continue
                if e.code not in (500, 502, 503, 504):
                    sys.exit(f"上传失败：{e.code} {e.read().decode(errors='replace')}")
                err = f"{e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                err = repr(e)
            tries += 1
            if tries > 6:
                sys.exit(f"上传多次失败，放弃：{err}")
            time.sleep(2 ** tries)
            # 问服务器实际收到了多少再续传
            try:
                with call("PUT", session, token, body=b"",
                          headers={"Content-Range": f"bytes */{size}"}) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code != 308:
                    sys.exit(f"续传查询失败：{e.code} {e.read().decode(errors='replace')}")
                rng = e.headers.get("Range")
                offset = int(rng.split("-")[1]) + 1 if rng else 0


def upload_caption(token, video_id, path, lang, name):
    boundary = uuid.uuid4().hex
    meta = {"snippet": {"videoId": video_id, "language": lang, "name": name}}
    with open(path, "rb") as f:
        srt = f.read()
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(meta)}\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
            ).encode() + srt + f"\r\n--{boundary}--\r\n".encode()
    try:
        with call("POST", f"{UPLOAD}/captions?uploadType=multipart&part=snippet", token, body=body,
                  headers={"Content-Type": f"multipart/related; boundary={boundary}"}) as r:
            json.load(r)
        print(f"字幕已加：{lang} {name}")
    except urllib.error.HTTPError as e:
        # 字幕失败不影响视频本身，报出来让人补传
        print(f"字幕 {path} 上传失败：{e.code} {e.read().decode(errors='replace')}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video", nargs="?")
    p.add_argument("--check", action="store_true", help="只验证授权，打印频道名")
    p.add_argument("--title")
    p.add_argument("--description-file")
    p.add_argument("--tag", action="append", default=[])
    p.add_argument("--category", default="1", help="1 = Film & Animation")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    p.add_argument("--kids", default="no", choices=["yes", "no"], help="是否“为儿童打造”")
    p.add_argument("--lang", default="en", help="视频的语言（配音语言）")
    p.add_argument("--caption", action="append", default=[], help="FILE.srt:LANG:NAME")
    a = p.parse_args()

    token = access_token()
    if a.check:
        check(token)
        return
    if not a.video or not a.title:
        p.error("要给 VIDEO 和 --title")

    desc = open(a.description_file, encoding="utf-8").read() if a.description_file else ""
    meta = {
        "snippet": {"title": a.title, "description": desc, "tags": a.tag,
                    "categoryId": a.category, "defaultLanguage": a.lang,
                    "defaultAudioLanguage": a.lang},
        "status": {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": a.kids == "yes",
                   "embeddable": True},
    }
    video = upload_video(token, a.video, meta)
    vid = video["id"]
    for c in a.caption:
        path, lang, name = c.split(":", 2)
        upload_caption(token, vid, path, lang, name)
    url = f"https://youtu.be/{vid}"
    print(f"已上传：{url}（{video['status']['privacyStatus']}）")
    print(json.dumps({"id": vid, "url": url, "privacy": video["status"]["privacyStatus"]}))


if __name__ == "__main__":
    main()
