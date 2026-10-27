# crayon-book-film uploader

A small personal script (Python standard library only) that uploads the owner's own crayon picture-book films to the owner's own YouTube channel with the YouTube Data API v3, together with Chinese and English captions.

**This app uses YouTube API Services.** By using it you agree to the [YouTube Terms of Service](https://www.youtube.com/t/terms). See the [Google Privacy Policy](https://policies.google.com/privacy).

- [Privacy Policy](PRIVACY.md)
- [Terms of Service](TERMS.md)

## What it does

1. Exchanges the owner's OAuth refresh token for an access token (scope `youtube.force-ssl`).
2. Uploads one video with `videos.insert` (resumable upload, resumes after network errors), setting title, description, tags, category, privacy status, language and "made for kids" = no.
3. Adds caption tracks with `captions.insert` (Chinese `zh-Hans` and English `en` .srt files).
4. Prints the video link.

It only ever acts on the signed-in owner's own channel. It has no users other than the owner, and stores no data.

## API methods used

| Method | Purpose | Quota per film |
|---|---|---|
| `channels.list` (mine=true) | confirm which channel is signed in (`--check`) | 1 |
| `videos.insert` | upload the film | ~1,600 |
| `captions.insert` ×2 | add Chinese and English captions | ~800 |

About one film per week; the default 10,000 units/day is enough.

## Usage

Set three environment variables (never committed): `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

```
python3 yt_upload.py --check        # prints the channel name

python3 yt_upload.py the-nail-crayon_hq.mp4 \
  --title "The Nail | 一颗钉子 · Crayon Picture Book" \
  --description-file desc.txt \
  --tag "fairy tale" --tag "Grimm" --tag "crayon" --tag "picture book" \
  --privacy public \
  --caption the-nail-crayon.zh.srt:zh-Hans:中文 \
  --caption the-nail-crayon.en.srt:en:English
```

Example of an uploaded film: https://youtu.be/BnSf-i8aeS0
