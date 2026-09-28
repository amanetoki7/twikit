import asyncio
from typing import NoReturn

from twikit import Client, Tweet

client = Client()

USER_ID = '44196397'      # 監視するユーザーの ID
CHECK_INTERVAL = 60 * 5   # 確認する間隔（秒）


def callback(tweet: Tweet) -> None:
    print(f'新しいツイートが投稿されました : {tweet.text}')


async def get_latest_tweet() -> Tweet:
    return (await client.get_user_tweets(USER_ID, 'Replies'))[0]


async def main() -> NoReturn:
    # 保存しておいた Cookie を読み込む（README の「使い方」を参照）
    client.load_cookies('cookies.json')

    before_tweet = await get_latest_tweet()

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        latest_tweet = await get_latest_tweet()
        if (
            before_tweet != latest_tweet and
            before_tweet.created_at_datetime < latest_tweet.created_at_datetime
        ):
            callback(latest_tweet)
        before_tweet = latest_tweet

asyncio.run(main())
