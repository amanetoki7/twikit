<h1 align="center">twikit</h1>

<p align="center">
  A <b>Twitter / X</b> API scraper for Python — <b>no API key required</b>.<br>
  A fork of <a href="https://github.com/d60/twikit">d60/twikit</a> that carries the fixes and additions from <a href="https://github.com/PawiX25/twifork">PawiX25/twifork</a> (the 2026 breakages that make the upstream release unusable, X Spaces support, and more).
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/github/stars/amanetoki7/twikit?style=flat&color=yellow" alt="Stars">
</p>

<p align="center">
  [<a href="README.md">日本語</a>] · [English] · [<a href="README-zh.md">中文</a>]
</p>

> **Drop-in replacement** — the package and the import are still `twikit`, so existing code (`from twikit import Client`) keeps working unchanged.

---

## Install

This repository is not published on PyPI. Install it straight from git:

```bash
pip install git+https://github.com/amanetoki7/twikit.git
```

> [!WARNING]
> `pip install twikit` gives you the upstream (d60/twikit) release `2.3.3`, which is broken in several ways as of 2026 and contains none of the fixes in this repository.

Optional features are extras:

```bash
# Browser TLS impersonation (gets past some 403 walls; curl_cffi)
pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"

# X Spaces WebRTC voice (speak / listen) and the live chat WebSocket (aiortc + websockets)
pip install "twikit[spaces] @ git+https://github.com/amanetoki7/twikit.git"
```

For development from a clone:

```bash
git clone https://github.com/amanetoki7/twikit.git
cd twikit
pip install -e ".[impersonate,spaces]"
```

**Python 3.10 or newer** is required (the code uses `anext()` and the dict `|` operator).

## What is fixed compared to upstream

The upstream PyPI release (`twikit==2.3.3`) is broken in several ways as of 2026. This repository carries the twifork fixes, so all of them are resolved — each item links to the upstream issue it resolves:

- **ClientTransaction / `Couldn't get KEY_BYTE indices`** — updated `ondemand.s.js` parsing for the new X webpack bundle, so GraphQL requests work again. ([#408](https://github.com/d60/twikit/issues/408), [#409](https://github.com/d60/twikit/issues/409), [#304](https://github.com/d60/twikit/issues/304))
- **Intermittent / sticky `404` on `SearchTimeline` and `friends/list`** — the `x-client-transaction-id` animation key was missing X's `frame_time` rounding step, so on some `Client` sessions every strict request 404'd until the client was recreated. Restored, so the semi-random 404s are gone. ([#357](https://github.com/d60/twikit/issues/357), [#397](https://github.com/d60/twikit/issues/397))
- **`KeyError` on missing optional fields** in `User.__init__` and `Client.request` — defensive `.get()` parsing. ([#417](https://github.com/d60/twikit/issues/417))
- **Empty user `name` / `screen_name`** (e.g. in search results) — X moved `name`, `screen_name`, `created_at`, avatar, location, and more out of `legacy` into new sub-objects; these are now read with a legacy fallback.
- **`get_tweet_by_id` `KeyError: 'itemContent'`** — handles both the legacy and the new trailing-cursor shapes. ([#332](https://github.com/d60/twikit/issues/332), [#363](https://github.com/d60/twikit/issues/363))
- **`KeyError: 'entries'` / `IndexError` on `get_user_tweets`** for accounts with no visible tweets — empty / cursor-less timelines return an empty result instead of crashing. ([#361](https://github.com/d60/twikit/issues/361), [#216](https://github.com/d60/twikit/issues/216))
- **`get_trends` deprecated / returns nothing** — rebuilt on top of `GenericTimelineById`; also adds `get_explore_page()`. ([#389](https://github.com/d60/twikit/issues/389))
- **`RecursionError` on rate-limit** — the 429 recovery path no longer recurses.
- **`GuestClient` does not work, and no fix here changes that.** The `User-Agent` header and the defensive user parsing are in place ([#402](https://github.com/d60/twikit/issues/402), [#385](https://github.com/d60/twikit/issues/385)), but `activate()` does not even get that far. Verified against live X: every call goes through the `x-client-transaction-id` handshake first, and a logged-out request only ever gets a ~34 KB page shell with no webpack manifest, so the handshake cannot complete — `activate()` itself raises `InvalidSession`. The `/1.1/guest/activate.json` endpoint is alive; reaching it is not. Guest access is closed on X's side; use cookies. ([#192](https://github.com/d60/twikit/issues/192))
- **`get_latest_friends` 404** — routed through the GraphQL `Following` endpoint after the v1.1 endpoint was retired. ([#397](https://github.com/d60/twikit/issues/397))
- **`'Client' object has no attribute '_ui_metrix'`** — fixed the captcha unlock path. ([#333](https://github.com/d60/twikit/issues/333))
- **`get_bookmark_folders().next()` infinite loop** — fixed malformed pagination variables. ([#334](https://github.com/d60/twikit/issues/334), [#335](https://github.com/d60/twikit/issues/335))
- **`get_latest_timeline` / `get_list_tweets` dropping conversation entries** — home- and list-conversation entries are now unpacked. ([#336](https://github.com/d60/twikit/issues/336), [#337](https://github.com/d60/twikit/issues/337), [#340](https://github.com/d60/twikit/issues/340))
- **`Media.source_url`** for the full-resolution image ([#376](https://github.com/d60/twikit/issues/376)), and **`Tweet.quoted_status_id`** for the quoted tweet id ([#222](https://github.com/d60/twikit/issues/222)).

### Other fixes

Beyond the list above, the following fixes from the twifork history are included:

- **`import twikit` no longer reconfigures the whole process** — on Windows it used to swap the event loop policy, which broke every importer that also needed subprocesses (playwright and friends) with `NotImplementedError`. Opt in with `TWIKIT_WINDOWS_SELECTOR_LOOP=1` if you really want the old behaviour.
- **Pagination** — `next()` / `previous()` no longer re-request the same page when X omits the cursor, and `get_lists` keeps paginating past a page with no lists on it. `count` is honoured; the surplus X over-delivers is handed back through `next()`.
- **Requests under `impersonate=`** — the `json=` body and `files=` (media chunks) were dropped, so GraphQL POSTs (timelines, `create_tweet`) answered 422 and `upload_media` failed. Also fixed: cookies sent to unrelated hosts, a stale `auth_token` surviving under another domain, and the `twitter.com` csrf cookie vanishing after the first response.
- **Replies tab and DMs** — `get_user_tweets(..., 'Replies')` returned the other party's tweet instead of the user's own reply; pinned tweets were dropped or duplicated; `send_dm` reported the wrong sender.
- **X's refusals are raised, not hidden** — permission errors (code 37 and friends) no longer come back as an empty result, `create_tweet` surfaces X's daily-limit message verbatim, and unresolvable lists / users raise `NotFound` / `UserNotFound` instead of returning an empty object.
- **Notifications** — `get_notifications('Mentions')` handles the new payload without a `notifications` key.
- **`get_trends`** — no more unbounded retries, and the news / sports / entertainment categories are no longer empty.
- **Fields X moved out of `legacy`** — User / Community / multi-photo `Tweet.media` / retweet full text / open polls are read from their new homes. `Poll.vote` now accepts the choice ordinal too (breaking change).
- **New properties** — `Tweet.url`, `Tweet.article` (`Article`), `Tweet.source`, `Tweet.conversation_ids`, `User.verified_type`, the parody / automated labels, `Conversation`, `Message.reply_data` and more. `Tweet.urls` always returns a list.
- **Login** — challenges are consumed in any order and `code_callback` replaces the blocking `input()` prompt. Password login itself is retired on X's side and raises `LoginRetired` (see below).
- **`x-client-transaction-id` handshake** — serialised, retried on failure, and dropped when the cookies change. Long-running processes can call `client.refresh_transaction()`.
- **Endpoints** — GraphQL query ids and feature flags refreshed to their 2026 values; the profile lookups keep the document that still returns `listed_count` and the other legacy counters.
- **Packaging** — the real Python floor (3.10) is declared, `py.typed` ships with the package, and `httpx>=0.26` is pinned. The `twikit.errors` module docstring records the X error codes seen in practice and the cause of intermittent 404s.

Issues that stem from X-side restrictions (account suspension, Cloudflare/IP blocks, captcha, automation limits) aren't fixable in the library and are out of scope.

### Browser TLS impersonation (optional)

Some X endpoints reject the default `httpx` TLS fingerprint with a `403` (HTML) response even when the request is valid. Installing the optional `curl_cffi` backend and passing `impersonate=` routes requests through a real browser TLS fingerprint, which avoids those 403s:

```python
client = Client('en-US', impersonate='chrome124')
```

## Quick start

> [!IMPORTANT]
> **Log in with cookies, not with a password.**
> X has retired the onboarding flow that `Client.login()` drives — it answers `code 366, "flow name LoginFlow is currently not accessible"`. Verified against live x.com on 2026-07-29: `/i/flow/login` now redirects to `/i/jf/onboarding/web`, and the site posts to `/i/jfapi/onboarding/web/actions/begin_login`, which requires a ~5 KB `$castle_token` generated by obfuscated in-page JavaScript and offers passkey/WebAuthn as a first factor. None of that is reachable from a plain HTTP client, so **password login cannot be made to work** — no library fix will change it. Export your cookies from a browser session instead.

**Getting the cookies**: log in to x.com in a browser, open the developer tools (Application / Storage → Cookies) and copy the values of `auth_token` and `ct0`. Those two are enough.

**Define a client and load cookies.**

```python
import asyncio
from twikit import Client

# impersonate= needs the extra: pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"
# Without it the v1.1 endpoints may answer 403 with a Cloudflare page.
client = Client('en-US', impersonate='chrome124')

async def main():
    # auth_token and ct0 are enough
    client.set_cookies({'auth_token': '...', 'ct0': '...'})
    # or: client.load_cookies('cookies.json')

    if not await client.is_logged_in():
        raise SystemExit('Cookies are stale - export them again.')

    # keep them for next time
    client.save_cookies('cookies.json')

asyncio.run(main())
```

`set_cookies` also accepts the list format exported by browser extensions or Playwright (a list of dicts with `name` and `value`).

**Post a tweet with media attached.**

```python
media_ids = [
    await client.upload_media('media1.jpg'),
    await client.upload_media('media2.jpg'),
]
await client.create_tweet(text='Example Tweet', media_ids=media_ids)
```

**Search the latest tweets for a keyword.**

```python
tweets = await client.search_tweet('python', 'Latest')
for tweet in tweets:
    print(tweet.user.name, tweet.text, tweet.created_at)
```

**A few more common calls.**

```python
await client.get_user_tweets('123456', 'Tweets')   # a user's tweets
await client.send_dm('123456789', 'Hello')          # send a DM
await client.get_trends('trending')                 # trending topics
```

More examples: [examples](examples)

## Features

- **No API key** — works by scraping the web client.
- **Free & open source** (MIT).
- **Drop-in `twikit` replacement** — same import, your code doesn't change.
- Tweets, search, timelines, trends, users, DMs, media, bookmarks, and more.
- **X Spaces** — read, search, create, publish, moderate and end audio Spaces, HLS stream urls, chat history and live chat. No extra packages for the core flow (`twikit[spaces]` adds WebRTC voice + the live chat WebSocket). See [docs/spaces.rst](docs/spaces.rst) and [examples/spaces.py](examples/spaces.py):

  ```python
  space = await client.spaces.get_space('1DXGydznBYWKM')
  stream = await client.spaces.get_stream(space.media_key)   # HLS url
  chat = await client.spaces.chat(space)                     # history
  created = await client.spaces.create_space(title='hi')     # go live
  await client.spaces.end_space(created['broadcast']['id'])
  ```

### API added on top of upstream

- `Client(impersonate=...)` — browser TLS impersonation via curl_cffi.
- `Client.is_logged_in()` — checks whether the cookies still authenticate.
- `Client.rate_limit_remaining` / `Client.rate_limit_reset` — the rate-limit budget reported by the last response.
- `Client.refresh_transaction()` — redo the `x-client-transaction-id` handshake.
- `Client.get_dm_inbox()`, `create_group()`, `delete_dm_conversation()` — the DM inbox, group creation and conversation deletion.
- `Client.update_profile()`, `get_about_account()`, `get_user_spotlights()`, `get_user_lists()`, `get_muted_users()`, `get_blocked_users()`.
- `Client.get_user_mentions()`, `search_tweets_by_date()`, `get_thread()`, `get_tweet_by_url()`, `get_explore_page()`.
- `twikit.SearchOptions` / `twikit.build_query` — search query building.
- `twikit.Article`, `twikit.Conversation` — long-form articles and DM conversations.
- `twikit.spaces` — the Spaces classes (`Spaces`, `Space`, `SpaceChat`, `SpaceVoiceSession`, ...).
- Exceptions: `ClientTransactionError`, `InvalidSession` (cookies rejected), `LoginRetired` (password login is gone).

## Documentation

The documentation in this repository is written in Japanese.

- API reference (Sphinx): [docs/twikit.rst](docs/twikit.rst) — build it with `make html` inside `docs/` (`pip install -r docs/requirements.txt`).
- Spaces guide: [docs/spaces.rst](docs/spaces.rst)
- Rate limits: [ratelimits.md](ratelimits.md)
- Protecting your account: [ToProtectYourAccount.md](ToProtectYourAccount.md)
- Upstream API reference (English; this repository is a superset of it): https://twikit.readthedocs.io/en/latest/twikit.html

## Community

Upstream twikit Discord: [![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)

## Contributing

Found a bug or have a fix? Open an issue or pull request on [amanetoki7/twikit](https://github.com/amanetoki7/twikit/issues).

If this saved you a headache, consider leaving a ⭐.

## Credits

- **[d60/twikit](https://github.com/d60/twikit)** by [@d60](https://github.com/d60) — the original implementation; all upstream credit goes to the original authors.
- **[PawiX25/twifork](https://github.com/PawiX25/twifork)** by [@PawiX25](https://github.com/PawiX25) and contributors — the 2026 fixes and the X Spaces support this repository builds on.

Both are licensed under the **MIT License**.

## Disclaimer

This is an independent, unofficial project. It is **not affiliated with, endorsed by, or sponsored by X Corp.** "X" and "Twitter" are trademarks of X Corp. Use it in accordance with applicable terms and laws.
