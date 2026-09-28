import asyncio
import time

from twikit import Client

client = Client('ja')


async def main():
    started_time = time.time()

    # 保存しておいた Cookie を読み込む（README の「使い方」を参照）
    client.load_cookies('cookies.json')
    client_user = await client.user()

    # すべての投稿を取得
    all_tweets = []
    tweets = await client_user.get_tweets('Replies')
    all_tweets += tweets

    while len(tweets) != 0:
        tweets = await tweets.next()
        all_tweets += tweets

    tasks = []
    for tweet in all_tweets:
        tasks.append(tweet.delete())

    gather = asyncio.gather(*tasks)
    await gather

    print(
        f'{len(all_tweets)} 件のツイートを削除しました\n'
        f'所要時間: {time.time() - started_time}'
    )

asyncio.run(main())
