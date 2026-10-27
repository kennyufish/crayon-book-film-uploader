# Privacy Policy — crayon-book-film uploader

Last updated: 2026-10-27

crayon-book-film uploader ("the app") is a personal command-line script. It is used only by its owner, the maintainer of this repository, to upload videos they made themselves to their own YouTube channel through the YouTube Data API. It has no other users and no website, server or database.

## What the app accesses

- Only the owner's own YouTube account, after the owner signs in with Google and grants permission (OAuth 2.0, scope `https://www.googleapis.com/auth/youtube.force-ssl`).
- It uploads video files and caption (.srt) files that the owner chooses, sets their title, description, tags, privacy status and "made for kids" setting, and reads the channel name to confirm the sign-in.

## What the app stores and shares

- It does not collect, store, sell or share any personal data, and it accesses no data about anyone other than the owner.
- No YouTube data is stored by the app. The only output is the uploaded video's ID and link, printed on screen for the owner.
- The OAuth client secret and refresh token are kept only in the owner's private environment settings. They are never written to this repository.

## Revoking access

The owner can revoke the app's access at any time at https://myaccount.google.com/permissions, which immediately stops the app from working.

## YouTube API Services

This app uses YouTube API Services. By using it you agree to be bound by the YouTube Terms of Service (https://www.youtube.com/t/terms). See also the Google Privacy Policy (https://policies.google.com/privacy).

## Contact

Open an issue at https://github.com/kennyufish/crayon-book-film-uploader/issues.
