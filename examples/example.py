import asyncio

from twikit import Client

###########################################

# アカウント情報を入力してください。
# パスワードによるログイン（client.login）は X 側で廃止されたため、
# ブラウザでログインした状態の Cookie（auth_token と ct0）を使います。
# 取得方法は README の「使い方」を参照してください。
AUTH_TOKEN = ...
CT0 = ...

client = Client('ja')

async def main():
    # 非同期クライアントのメソッドはコルーチンなので、
    # `await` を付けて呼び出す必要があります。
    client.set_cookies({'auth_token': AUTH_TOKEN, 'ct0': CT0})

    # Cookie がまだ有効か確認する
    if not await client.is_logged_in():
        raise SystemExit('Cookie が無効です。ブラウザから取り直してください。')

    ###########################################

    # 最新のツイートを検索
    tweets = await client.search_tweet('query', 'Latest')
    for tweet in tweets:
        print(tweet)
    # 続きのツイートを取得
    more_tweets = await tweets.next()

    ###########################################

    # ユーザーを検索
    users = await client.search_user('query')
    for user in users:
        print(user)
    # 続きのユーザーを取得
    more_users = await users.next()

    ###########################################

    # スクリーンネームからユーザーを取得
    USER_SCREEN_NAME = 'example_user'
    user = await client.get_user_by_screen_name(USER_SCREEN_NAME)

    # ユーザーの属性にアクセス
    print(
        f'id: {user.id}',
        f'name: {user.name}',
        f'followers: {user.followers_count}',
        f'tweets count: {user.statuses_count}',
        sep='\n'
    )

    # フォロー
    await user.follow()
    # フォロー解除
    await user.unfollow()

    # ユーザーのツイートを取得
    user_tweets = await user.get_tweets('Tweets')
    for tweet in user_tweets:
        print(tweet)
    # 続きのツイートを取得
    more_user_tweets = await user_tweets.next()

    ###########################################

    # ユーザーに DM を送る
    media_id = await client.upload_media('./image.png', 0)
    await user.send_dm('dm text', media_id)

    # DM の履歴を取得
    messages = await user.get_dm_history()
    for message in messages:
        print(message)
    # 続きのメッセージを取得
    more_messages = await messages.next()

    ###########################################

    # ID からツイートを取得
    TWEET_ID = '0000000000'
    tweet = await client.get_tweet_by_id(TWEET_ID)

    # ツイートの属性にアクセス
    print(
        f'id: {tweet.id}',
        f'text {tweet.text}',
        f'favorite count: {tweet.favorite_count}',
        f'media: {tweet.media}',
        sep='\n'
    )

    # いいね
    await tweet.favorite()
    # いいね解除
    await tweet.unfavorite()
    # リツイート
    await tweet.retweet()
    # リツイート解除
    await tweet.delete_retweet()

    # ツイートに返信
    await tweet.reply('tweet content')

    ###########################################

    # メディア付きツイートを作成
    TWEET_TEXT = 'tweet text'
    MEDIA_IDS = [
        await client.upload_media('./media1.png', 0),
        await client.upload_media('./media2.png', 1),
        await client.upload_media('./media3.png', 2)
    ]

    await client.create_tweet(TWEET_TEXT, MEDIA_IDS)

    # 投票付きツイートを作成
    TWEET_TEXT = 'tweet text'
    POLL_URI = await client.create_poll(
        ['Option 1', 'Option 2', 'Option 3']
    )

    await client.create_tweet(TWEET_TEXT, poll_uri=POLL_URI)

    ###########################################

    # ニュースのトレンドを取得
    trends = await client.get_trends('news')
    for trend in trends:
        print(trend)

    ###########################################

asyncio.run(main())
