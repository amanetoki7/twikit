"""
ゲストクライアント（ログイン無し）の例。

注意: 2026 年現在、X はゲストアクセスを閉じています。未ログインのリクエストには
webpack マニフェストを含まないページの殻しか返ってこないため、
x-client-transaction-id のハンドシェイクが完了できず、`activate()` は
`InvalidSession` を送出します。これはライブラリ側では直せません。
ログイン済みの Cookie を使う `twikit.Client` を利用してください。
"""

import asyncio

from twikit.guest import GuestClient

client = GuestClient()


async def main():
    # ゲストトークンを生成してクライアントを有効化する
    await client.activate()

    # スクリーンネームからユーザーを取得
    user = await client.get_user_by_screen_name('elonmusk')
    print(user)
    # ID からユーザーを取得
    user = await client.get_user_by_id('44196397')
    print(user)


    user_tweets = await client.get_user_tweets('44196397')
    print(user_tweets)

    tweet = await client.get_tweet_by_id('1519480761749016577')
    print(tweet)

asyncio.run(main())
