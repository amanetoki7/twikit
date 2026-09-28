import asyncio
import os

from twikit import Client
from twikit.streaming import Topic

# ブラウザでログインした状態の Cookie（auth_token と ct0）。
# パスワードによるログイン（client.login）は X 側で廃止されています。
AUTH_TOKEN = ''
CT0 = ''

client = Client()


async def main():
    if os.path.exists('cookies.json'):
        # 2 回目以降は保存した Cookie を読み込む
        client.load_cookies('cookies.json')
    else:
        # 初回はブラウザから取り出した Cookie をセットして保存する
        client.set_cookies({'auth_token': AUTH_TOKEN, 'ct0': CT0})
        client.save_cookies('cookies.json')


    user_id = '1752362966203469824'  # DM を監視する相手のユーザー ID
    reply_message = 'Hello'

    topics = {
        Topic.dm_update(f'{await client.user_id()}-{user_id}')
    }
    streaming_session = await client.get_streaming_session(topics)

    async for topic, payload in streaming_session:
        if payload.dm_update:
            # 自分が送ったメッセージには反応しない
            if await client.user_id() == payload.dm_update.user_id:
                continue
            await client.send_dm(payload.dm_update.user_id, reply_message)

asyncio.run(main())
