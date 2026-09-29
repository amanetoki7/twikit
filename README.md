<h1 align="center">twikit</h1>

<p align="center">
  <b>API キー不要</b>で使える、Python 用の <b>Twitter / X</b> API スクレイピングライブラリ。<br>
  <a href="https://github.com/d60/twikit">d60/twikit</a> をベースに、<a href="https://github.com/PawiX25/twifork">PawiX25/twifork</a> の修正と機能追加（2026 年時点で本家が動かなくなった不具合の修正、X スペース対応など）を取り込んだフォークです。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/github/stars/amanetoki7/twikit?style=flat&color=yellow" alt="Stars">
</p>

<p align="center">
  [日本語] · [<a href="README-en.md">English</a>] · [<a href="README-zh.md">中文</a>]
</p>

> **既存コードはそのまま動きます。** パッケージ名もインポート名も `twikit` のままなので、`from twikit import Client` などのコードを書き換える必要はありません。

---

## インストール

このリポジトリは PyPI には公開していません。git から直接インストールしてください。

```bash
pip install git+https://github.com/amanetoki7/twikit.git
```

> [!WARNING]
> `pip install twikit` で入るのは本家（d60/twikit）の `2.3.3` です。2026 年現在、本家はいくつもの箇所が壊れており、このリポジトリの修正は含まれていません。

オプション機能は extras で指定します。

```bash
# ブラウザの TLS フィンガープリントを偽装して、一部の 403 を回避する（curl_cffi）
pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"

# X スペースの WebRTC 音声（発言 / 聴取）とライブチャットの WebSocket（aiortc + websockets）
pip install "twikit[spaces] @ git+https://github.com/amanetoki7/twikit.git"
```

clone して開発する場合:

```bash
git clone https://github.com/amanetoki7/twikit.git
cd twikit
pip install -e ".[impersonate,spaces]"
```

**Python 3.10 以上**が必要です（`anext()` と辞書の `|` 演算子を使っています）。

## 本家からの修正点

本家の PyPI 版（`twikit==2.3.3`）は 2026 年現在、以下の箇所が壊れています。このリポジトリでは twifork の修正を取り込み、すべて解消しています。各項目は対応する本家の Issue にリンクしています。

- **ClientTransaction / `Couldn't get KEY_BYTE indices`** — X の新しい webpack バンドルに合わせて `ondemand.s.js` の解析を更新し、GraphQL リクエストが再び通るようにしました。([#408](https://github.com/d60/twikit/issues/408), [#409](https://github.com/d60/twikit/issues/409), [#304](https://github.com/d60/twikit/issues/304))
- **`SearchTimeline` や `friends/list` で散発的に出て、そのまま居座る `404`** — `x-client-transaction-id` のアニメーションキー計算で X 側の `frame_time` の丸め処理が抜けており、一部の `Client` では作り直すまで厳格なリクエストがすべて 404 になっていました。丸め処理を復元し、ランダムな 404 は解消されています。([#357](https://github.com/d60/twikit/issues/357), [#397](https://github.com/d60/twikit/issues/397))
- **任意フィールド欠落時の `KeyError`**（`User.__init__` と `Client.request`）— `.get()` で安全に読むようにしました。([#417](https://github.com/d60/twikit/issues/417))
- **ユーザーの `name` / `screen_name` が空になる**（検索結果などで発生）— X が `name`・`screen_name`・`created_at`・アイコン・場所などを `legacy` から新しいサブオブジェクトへ移したため、新しい場所を読みつつ `legacy` にもフォールバックするようにしました。
- **`get_tweet_by_id` の `KeyError: 'itemContent'`** — 旧形式と新しい末尾カーソル形式の両方に対応しました。([#332](https://github.com/d60/twikit/issues/332), [#363](https://github.com/d60/twikit/issues/363))
- **ツイートが無いアカウントでの `get_user_tweets` の `KeyError: 'entries'` / `IndexError`** — 空・カーソル無しのタイムラインでも落ちずに空の結果を返します。([#361](https://github.com/d60/twikit/issues/361), [#216](https://github.com/d60/twikit/issues/216))
- **`get_trends` が非推奨で何も返さない** — `GenericTimelineById` ベースに作り直し、あわせて `get_explore_page()` を追加しました。([#389](https://github.com/d60/twikit/issues/389))
- **レート制限時の `RecursionError`** — 429 のリカバリ処理が再帰しないようにしました。
- **`GuestClient` は動作しません。これはライブラリ側では直せません。** `User-Agent` ヘッダーの送信とユーザー情報の安全な解析は入っていますが（[#402](https://github.com/d60/twikit/issues/402), [#385](https://github.com/d60/twikit/issues/385)）、`activate()` はそこまで到達しません。実際の X に対して確認したところ、すべてのリクエストは先に `x-client-transaction-id` のハンドシェイクを通りますが、未ログインのリクエストには webpack マニフェストを含まない約 34 KB のページの殻しか返ってこないため、ハンドシェイクを完了できず、`activate()` 自体が `InvalidSession` を送出します。`/1.1/guest/activate.json` エンドポイントは生きていますが、そこに辿り着けません。ゲストアクセスは X 側で閉じられているため、Cookie を使ってください。([#192](https://github.com/d60/twikit/issues/192))
- **`get_latest_friends` の 404** — v1.1 エンドポイントが廃止されたため、GraphQL の `Following` エンドポイント経由にしました。([#397](https://github.com/d60/twikit/issues/397))
- **`'Client' object has no attribute '_ui_metrix'`** — captcha 解除の処理を修正しました。([#333](https://github.com/d60/twikit/issues/333))
- **`get_bookmark_folders().next()` が無限ループ** — 壊れていたページネーション用パラメータを修正しました。([#334](https://github.com/d60/twikit/issues/334), [#335](https://github.com/d60/twikit/issues/335))
- **`get_latest_timeline` / `get_list_tweets` が会話ツイートを取りこぼす** — home / list の会話エントリも展開するようにしました。([#336](https://github.com/d60/twikit/issues/336), [#337](https://github.com/d60/twikit/issues/337), [#340](https://github.com/d60/twikit/issues/340))
- フル解像度の画像 URL を返す **`Media.source_url`**（[#376](https://github.com/d60/twikit/issues/376)）と、引用元ツイートの ID を返す **`Tweet.quoted_status_id`**（[#222](https://github.com/d60/twikit/issues/222)）を追加しました。

### その他の修正

上記のほかにも、twifork のコミット履歴から次の修正を取り込んでいます。

- **`import twikit` がプロセス全体を書き換えない** — Windows でイベントループポリシーを勝手に差し替えていたため、playwright などサブプロセスを使うライブラリと併用すると `NotImplementedError` になっていました。従来の動作が必要な場合だけ、環境変数 `TWIKIT_WINDOWS_SELECTOR_LOOP=1` を設定してください。
- **ページネーション** — カーソルの無いページで `next()` / `previous()` が同じページを取り直し続ける問題、`get_lists` がリストの無いページで打ち切られる問題を修正しました。`count` は指定どおりに切り詰め、余剰分は `next()` で取れます。
- **`impersonate=` 使用時の送信内容** — `json=` ボディと `files=`（メディアのチャンク）が送られず、GraphQL の POST（タイムライン取得や `create_tweet`）が 422 になったり `upload_media` が失敗したりする問題を修正しました。Cookie が無関係なホストに送られる問題、古い `auth_token` が残る問題、`twitter.com` 向けの csrf Cookie が最初のレスポンス以降で消える問題も修正しています。
- **`Replies` タブと DM** — `get_user_tweets(..., 'Replies')` で本人の返信ではなく相手のツイートが返っていた問題、固定ツイートの取りこぼし・重複、`send_dm` の送信者の誤りを修正しました。
- **X の拒否を隠さない** — 権限エラー（コード 37 など）を空の結果として握りつぶさず例外を送出します。`create_tweet` の日次上限のメッセージもそのまま表示します。存在しないリスト・ユーザーは空のオブジェクトではなく `NotFound` / `UserNotFound` になります。
- **通知** — `get_notifications('Mentions')` で `notifications` キーが無い新形式のレスポンスに対応しました。
- **`get_trends`** — 無限リトライを修正し、news / sports / entertainment のカテゴリが空で返る問題を修正しました。
- **X が `legacy` から移動したフィールド** — User / Community / Tweet.media（複数枚の添付）/ リツイートの全文 / 開催中の投票などを新しい場所から読みます。`Poll.vote` は選択肢の番号も受け付けるようになりました（破壊的変更）。
- **新しいプロパティ** — `Tweet.url`、`Tweet.article`（`Article`）、`Tweet.source`、`Tweet.conversation_ids`、`User.verified_type`、パロディ / 自動化ラベル、`Conversation`、`Message.reply_data` など。`Tweet.urls` は常にリストを返します。
- **ログイン** — ログインチャレンジをどの順序で来ても処理し、`code_callback` でコードの入力方法を差し替えられるようにしました。ただしパスワードログイン自体は X 側で廃止されており、`LoginRetired` を送出します（後述）。
- **`x-client-transaction-id` のハンドシェイク** — 直列化して失敗時にリトライし、Cookie を更新したあとは古いハンドシェイクを捨てます。長時間動かすプロセスでは `client.refresh_transaction()` で手動更新もできます。
- **エンドポイント** — GraphQL の query id と features フラグを 2026 年時点のものへ更新しました。プロフィール取得は `listed_count` などの統計を返す旧ドキュメントを維持しています。
- **パッケージ** — Python の下限を実態（3.10）に合わせ、`py.typed` を同梱し、`httpx>=0.26` の下限を宣言しました。`twikit.errors` のモジュール docstring に、実際に観測した X のエラーコード一覧と散発的な 404 の原因をまとめています。

X 側の制限（アカウント凍結、Cloudflare / IP ブロック、captcha、自動化の制約）が原因の問題は、ライブラリ側では直しようがないため対象外です。

### ブラウザ TLS の偽装（任意）

X の一部のエンドポイントは、リクエスト自体が正しくても `httpx` 既定の TLS フィンガープリントを `403`（HTML）で弾いてきます。オプションの `curl_cffi` を入れて `impersonate=` を渡すと、実際のブラウザの TLS フィンガープリントで通信し、この種の 403 を避けられます。

```python
client = Client('ja', impersonate='chrome124')
```

## 使い方

> [!IMPORTANT]
> **パスワードではなく Cookie でログインしてください。**
> X は `Client.login()` が使うオンボーディングフローを廃止しており、`code 366, "flow name LoginFlow is currently not accessible"` を返します。2026-07-29 に実際の x.com で確認したところ、`/i/flow/login` は `/i/jf/onboarding/web` にリダイレクトされ、サイトは `/i/jfapi/onboarding/web/actions/begin_login` に POST します。この POST には難読化されたページ内 JavaScript が生成する約 5 KB の `$castle_token` が必要で、第一要素としてパスキー / WebAuthn も提示されます。いずれも素の HTTP クライアントからは到達できないため、**パスワードログインは動作させられません**（ライブラリ側の修正では直りません）。代わりに、ブラウザでログインしたセッションの Cookie を取り出して使ってください。

**Cookie の取り出し方**: ブラウザで x.com にログインし、開発者ツール（Application / Storage → Cookies）から `auth_token` と `ct0` の値をコピーします。この 2 つだけで十分です。

**クライアントを用意して Cookie をセットする。**

```python
import asyncio
from twikit import Client

# impersonate= には extras が必要: pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"
# 無いと v1.1 のエンドポイントが Cloudflare のページとともに 403 を返すことがあります。
client = Client('ja', impersonate='chrome124')

async def main():
    # auth_token と ct0 だけで十分です
    client.set_cookies({'auth_token': '...', 'ct0': '...'})
    # または: client.load_cookies('cookies.json')

    if not await client.is_logged_in():
        raise SystemExit('Cookie が無効です。ブラウザから取り直してください。')

    # 次回以降のために保存しておく
    client.save_cookies('cookies.json')

asyncio.run(main())
```

`set_cookies` には、ブラウザの拡張機能や Playwright が書き出す形式（`name` と `value` を持つ辞書のリスト）もそのまま渡せます。

**メディア付きツイートを投稿する。**

```python
media_ids = [
    await client.upload_media('media1.jpg'),
    await client.upload_media('media2.jpg'),
]
await client.create_tweet(text='Example Tweet', media_ids=media_ids)
```

**キーワードで最新のツイートを検索する。**

```python
tweets = await client.search_tweet('python', 'Latest')
for tweet in tweets:
    print(tweet.user.name, tweet.text, tweet.created_at)
```

**その他、よく使う呼び出し。**

```python
await client.get_user_tweets('123456', 'Tweets')   # ユーザーのツイート
await client.send_dm('123456789', 'Hello')          # DM を送る
await client.get_trends('trending')                 # トレンド
```

さらに詳しい例は [examples](examples) にあります。

## 主な機能

- **API キー不要** — Web 版をスクレイピングして動作します。
- **無料・オープンソース**（MIT）。
- **`twikit` の置き換え** — インポート名は同じなので、コードはそのままで構いません。
- ツイート、検索、タイムライン、トレンド、ユーザー、DM、メディア、ブックマークなど。
- **X スペース（Spaces）** — 読み取り・検索・作成・公開・モデレーション・終了、HLS ストリーム URL、チャット履歴・ライブチャットに対応。コア機能に追加パッケージは不要です（WebRTC 音声とライブチャットの WebSocket は `twikit[spaces]`）。詳しくは [docs/spaces.rst](docs/spaces.rst) と [examples/spaces.py](examples/spaces.py) を参照してください。

  ```python
  space = await client.spaces.get_space('1DXGydznBYWKM')
  stream = await client.spaces.get_stream(space.media_key)   # HLS URL
  chat = await client.spaces.chat(space)                     # 履歴
  created = await client.spaces.create_space(title='こんにちは')  # ライブ開始
  await client.spaces.end_space(created['broadcast']['id'])
  ```

### 本家に無い追加 API

- `Client(impersonate=...)` — curl_cffi によるブラウザ TLS の偽装。
- `Client.is_logged_in()` — Cookie がまだ有効かを確認します。
- `Client.rate_limit_remaining` / `Client.rate_limit_reset` — 直近のレスポンスに含まれるレート制限の残りとリセット時刻。
- `Client.refresh_transaction()` — `x-client-transaction-id` のハンドシェイクをやり直します。
- `Client.get_dm_inbox()`、`create_group()`、`delete_dm_conversation()` — DM の受信箱一覧、グループ作成、会話の削除。
- `Client.update_profile()`、`get_about_account()`、`get_user_spotlights()`、`get_user_lists()`、`get_muted_users()`、`get_blocked_users()`。
- `Client.get_user_mentions()`、`search_tweets_by_date()`、`get_thread()`、`get_tweet_by_url()`、`get_explore_page()`。
- `twikit.SearchOptions` / `twikit.build_query` — 検索クエリの組み立て。
- `twikit.Article`、`twikit.Conversation` — 長文記事と DM の会話。
- `twikit.spaces` — スペース関連のクラス群（`Spaces`、`Space`、`SpaceChat`、`SpaceVoiceSession` など）。
- 例外: `ClientTransactionError`、`InvalidSession`（Cookie が無効）、`LoginRetired`（パスワードログインは廃止）。

## ドキュメント

- API リファレンス（Sphinx、日本語）: [docs/twikit.rst](docs/twikit.rst)。`docs/` で `make html` するとビルドできます（`pip install -r docs/requirements.txt`）。
- X スペースのガイド: [docs/spaces.rst](docs/spaces.rst)
- レート制限: [ratelimits.md](ratelimits.md)
- アカウントを守るために: [ToProtectYourAccount.md](ToProtectYourAccount.md)
- 本家の API リファレンス（英語。このリポジトリはその上位互換です）: https://twikit.readthedocs.io/en/latest/twikit.html

## アカウントを守るために

このライブラリは非公式 API を使うため、使い方を誤るとアカウントが凍結される可能性があります。リクエストを送りすぎない、Cookie を使い回す、といった対策を [ToProtectYourAccount.md](ToProtectYourAccount.md) にまとめています。

## コミュニティ

本家 twikit の Discord: [![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)

## コントリビュート

不具合を見つけたとき、修正があるときは、[Issues](https://github.com/amanetoki7/twikit/issues) に Issue や Pull Request をお願いします。

役に立ったら、すたー を付けてもらえると励みになります。

## クレジット

- **[d60/twikit](https://github.com/d60/twikit)**（[@d60](https://github.com/d60)）— 元になる実装。功績はすべて原作者に帰属します。
- **[PawiX25/twifork](https://github.com/PawiX25/twifork)**（[@PawiX25](https://github.com/PawiX25) とコントリビューターの皆さん）— 2026 年時点の不具合修正と X スペース対応。このリポジトリはその成果を取り込んでいます。
- すきくん **[八雲ゆかり](https://x.com/yukari_557fd8) さま** ([@yukari-557fd8](https://github.com/yukari-557fd8)) - 公式APIしか使ったことないわたしを救ってくれた。このリポジトリがうまれるきっかけにもなりました。

GitHubリポジトリは、いずれも **MIT ライセンス**で公開されています。

## 免責事項

このリポジトリは独立した非公式プロジェクトであり、**X Corp. とは一切の提携・承認・スポンサー関係はありません。**「X」および「Twitter」は X Corp. の商標です。利用にあたっては、適用される規約および法令を守ってください。
