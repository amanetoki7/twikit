"""
twikit の X スペース（Spaces）デモ。

ライブラリの他の機能と同じく、ログイン済みの Client（auth_token と ct0 の
Cookie）が必要です。

読み取り系の操作（get_space、search、ストリーム URL、チャット履歴）に追加
パッケージは不要です。スペースの作成 / 終了も追加パッケージ無しで動作します
（Web クライアントと同じ proxsee + Janus の HTTP フローを実行します）。
オプションの依存パッケージが必要なのは、WebRTC の音声経路（speak / listen）
だけです:

    pip install "twikit[spaces] @ git+https://github.com/amanetoki7/twikit.git"

実行:

    AUTH_TOKEN=... CT0=... python examples/spaces.py

このデモは、
  1. ID でスペースを取得します（配信中のスペースの検索も行います）。
  2. ストリーム URL（HLS）と最新のチャットメッセージを表示します。
  3. SPACES_CREATE=1 のとき: ライブのスペースを作成し、Running になったことを
     確認してから終了します（数秒間だけ公開されます）。
"""

import asyncio
import os

import twikit

# 任意の公開スペースの ID（13 文字の ID、または URL 全体）。
SPACE_ID = os.environ.get('SPACE_ID', '1DXGydznBYWKM')


async def main() -> None:
    client = twikit.Client(language='ja')
    # ブラウザの Cookie（auth_token と ct0）をセットします。
    # 取得方法は README を参照してください。
    client.set_cookies({
        'auth_token': os.environ['AUTH_TOKEN'],
        'ct0': os.environ['CT0'],
    })
    user_id = await client.user_id()
    print(f'ログイン中のユーザー ID: {user_id}')

    # 1. メタデータ
    space = await client.spaces.get_space(SPACE_ID)
    print(f'space: {space.state} | {space.title!r}')
    print(f'  host: {space.host_user_id} | speakers: {len(space.speaker_ids)}')

    # 2. 配信中のスペースを検索
    live = await client.spaces.search('music', filter='Live')
    print(f'配信中のスペースの検索結果: {len(live)} 件')
    for s in live[:3]:
        print('  -', s.id)

    # 3. HLS ストリーム URL（ffmpeg で聴取: ffmpeg -i <url> out.m4a）
    if space.media_key:
        stream = await client.spaces.get_stream(space.media_key)
        print(f'HLS url: {stream.hls_url}')

    # 4. チャット履歴（ライブ中でもリプレイでも取得可能）
    try:
        chat = await client.spaces.chat(space)
        print(f'chat read_only={chat.read_only} ws={chat._ws is not None}')
        for msg in (await chat.history(limit=5))[:3]:
            print('  msg:', (msg.body or '')[:60])
    except Exception as e:
        print('チャットは利用できません:', e)

    # 5. 作成 -> ライブ確認 -> 終了（明示的に有効化したときだけ。外から見える操作です）
    if os.environ.get('SPACES_CREATE'):
        created = await client.spaces.create_space(
            title='twikit spaces demo',
            conversation_controls=2,
        )
        space_id = (created.get('broadcast') or {}).get('id')
        print(f'作成しました: {space_id}')
        await asyncio.sleep(3)
        live_space = await client.spaces.get_space(space_id)
        print(f'state: {live_space.state} (Running のはず)')
        await client.spaces.end_space(space_id)
        print(f'終了しました: {space_id}')

    # 6. 発言（明示的に有効化したときだけ。外から見える操作です）: 承認済みの
    #    発言者として、ペース制御した正弦波をライブのスペースに流します。
    #    ホストの場合は代わりに
    #    `await client.spaces.host(created, audio_track=...)` を使います。
    #    `pip install "twikit[spaces] @ git+https://github.com/amanetoki7/twikit.git"` が必要です。
    if os.environ.get('SPACES_SPEAK'):
        space_id = os.environ.get('SPACES_SPEAK')
        import math
        import struct

        from aiortc.mediastreams import AudioFrame, AudioStreamTrack

        class PacedSineTrack(AudioStreamTrack):
            kind = 'audio'

            def __init__(self, freq: int = 440):
                super().__init__()
                self._n = 0
                self._pts = 0
                self._next = None

            async def recv(self):
                # aiortc は RTP のペース制御をしません。recv() がフレームを
                # 返す速さでそのまま送信されます。20ms のフレームごとに 20ms
                # スリープしないと、音声が約 15 倍速で再生されてしまいます。
                now = asyncio.get_event_loop().time()
                if self._next is None:
                    self._next = now
                delay = self._next - now
                if delay > 0:
                    await asyncio.sleep(delay)
                self._next += 0.02
                from fractions import Fraction
                n = 960
                buf = bytearray(n * 2)
                for i in range(n):
                    v = int(8000 * math.sin(2 * math.pi * 440 * (self._n + i) / 48000))
                    struct.pack_into('<h', buf, i * 2, v)
                self._n += n
                frame = AudioFrame(format='s16', layout='mono', samples=n)
                frame.sample_rate = 48000
                frame.pts = self._pts
                frame.time_base = Fraction(1, 48000)
                self._pts += n
                frame.planes[0].update(bytes(buf))
                return frame

        session = await client.spaces.speak(
            space_id,
            audio_track=PacedSineTrack(),
        )
        print(f'{space_id} で発言中（publisher id {session.publisher_id}）')
        try:
            await asyncio.sleep(20)
        finally:
            await session.close()

    await client.http.aclose()


if __name__ == '__main__':
    asyncio.run(main())
