import asyncio
from twikit import Client

client = Client('ja')


async def main():
    # 保存しておいた Cookie を読み込む（README の「使い方」を参照）
    client.load_cookies('cookies.json')

    tweet = await client.get_tweet_by_id('...')

    # 添付メディアを種類ごとにダウンロードする
    for i, media in enumerate(tweet.media):
        if media.type == 'photo':
            await media.download(f'media_{i}.jpg')
        if media.type == 'animated_gif':
            await media.streams[-1].download(f'media_{i}.mp4')
        if media.type == 'video':
            await media.streams[-1].download(f'media_{i}.mp4')

asyncio.run(main())
