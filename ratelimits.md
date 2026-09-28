# レート制限

**レート制限は 15 分ごとにリセットされます。**

\* `create_tweet` には、15 分枠とは別の、より厳しい制限があります。無料アカウントでは **1 日あたり約 50 投稿** が上限です。これに達すると、次のメッセージとともに `CouldNotTweet` が送出されます。

```
Authorization: You've hit the daily limit. Subscribe to Premium for higher limits. (501)
```

このとき 15 分枠のカウンターはまだ約 250 リクエスト残っていると報告するため、レート制限ヘッダーを見張るだけでは事前に気付けません。新規アカウント 4 つで計測したところ、いずれも毎分約 70 投稿のペースで **51 投稿目** で止められました。読み取り・いいね・フォローは引き続き動作し、投稿だけが翌日まで（または Premium に加入するまで）ブロックされます。

直近のレスポンスに含まれる残りリクエスト数とリセット時刻は、`Client.rate_limit_remaining` と `Client.rate_limit_reset` で確認できます。

「上限」の `-` は未計測（不明）を表します。

| 関数                                  | 上限  | エンドポイント                      |
|---------------------------------------|-------|-------------------------------------|
| add_members_to_group                  | -     | AddParticipantsMutation             |
| block_user                            | 187   | blocks/create.json                  |
| get_user_verified_followers           | 500   | BlueVerifiedFollowers               |
| get_bookmarks                         | 500   | Bookmarks                           |
| delete_all_bookmarks                  | -     | BookmarksAllDelete                  |
| change_group_name                     | 900   | {GroupID}/update_name.json          |
| get_group_dm_history, get_dm_history  | 900   | conversation/{ConversationID}.json  |
| bookmark_tweet                        | -     | CreateBookmark                      |
| create_poll                           | -     | cards/create.json                   |
| follow_user                           | 15    | friendships/create.json             |
| create_list                           | -     | CreateList                          |
| retweet                               | -     | CreateRetweet                       |
| create_scheduled_tweet                | -     | CreateScheduledTweet                |
| create_tweet                          | 300*  | CreateTweet                         |
| delete_bookmark                       | -     | DeleteBookmark                      |
| delete_dm                             | -     | DMMessageDeleteMutation             |
| delete_list_banner                    | -     | DeleteListBanner                    |
| delete_retweet                        | -     | DeleteRetweet                       |
| delete_scheduled_tweet                | -     | DeleteScheduledTweet                |
| delete_tweet                          | -     | DeleteTweet                         |
| unfollow_user                         | 187   | friendships/destroy.json            |
| edit_list_banner                      | -     | EditListBanner                      |
| get_favoriters                        | 500   | Favoriters                          |
| favorite_tweet                        | -     | FavoriteTweet                       |
| get_scheduled_tweets                  | 500   | FetchScheduledTweets                |
| get_user_followers                    | 50    | Followers                           |
| get_user_followers_you_know           | 500   | FollowersYouKnow                    |
| get_user_following                    | 500   | Following                           |
| get_guest_token                       | -     | guest/activate.json                 |
| get_latest_timeline                   | 500   | HomeLatestTimeline                  |
| get_timeline                          | 500   | HomeTimeline                        |
| -                                     | 450   | dm/inbox_initial_state.json         |
| add_list_member                       | -     | ListAddMember                       |
| get_list                              | 500   | ListByRestId                        |
| get_list_tweets                       | 500   | ListLatestTweetsTimeline            |
| get_lists                             | 500   | ListsManagementPageTimeline         |
| get_list_members                      | 500   | ListMembers                         |
| remove_list_member                    | -     | ListRemoveMember                    |
| get_list_subscribers                  | 500   | ListSubscribers                     |
| logout                                | 187   | account/logout.json                 |
| add_reaction_to_message               | -     | /useDMReactionMutationAddMutation   |
| remove_reaction_from_message          | -     | useDMReactionMutationRemoveMutation |
| -                                     | -     | MuteList                            |
| mute_user                             | 187   | mutes/users/create.json             |
| get_notifications[type="All"]         | 180   | notifications/all.json              |
| get_notifications[type="Mentions"]    | 180   | notifications/mentions.json         |
| get_notifications[type="Verified"]    | 180   | notifications/verified.json         |
| get_retweeters                        | 500   | Retweeters                          |
| search_tweet, search_user             | 50    | SearchTimeline                      |
| send_dm                               | 187   | dm/new2.json                        |
| user_id                               | -     | account/settings.json               |
| get_user_subscriptions                | 500   | UserCreatorSubscriptions            |
| login                                 | 187   | onboarding/task.json                |
| get_trends                            | 20000 | guide.json                          |
| get_tweet_by_id                       | 150   | TweetDetail                         |
| unblock_user                          | 187   | blocks/destroy.json                 |
| unfavorite_tweet                      | -     | UnfavoriteTweet                     |
| -                                     | -     | UnmuteList                          |
| unmute_user                           | 187   | mutes/users/destroy.json            |
| edit_list                             | -     | UpdateList                          |
| upload_media                          | -     | media/upload.json                   |
| get_user_by_id                        | 500   | UserByRestId                        |
| get_user_by_screen_name               | 95    | UserByScreenName                    |
| get_user_tweets[tweet_type="Likes"]   | 500   | Likes                               |
| get_user_tweets[tweet_type="Media"]   | 500   | UserMedia                           |
| get_user_tweets[tweet_type="Tweets"]  | 50    | UserTweets                          |
| get_user_tweets[tweet_type="Replies"] | 50    | UserTweetsAndReplies                |
| vote                                  | -     | capi/passthrough/1                  |
| create_group                          | -     | dm/new2.json                        |
| delete_dm_conversation                | -     | dm/conversation/{id}/delete.json    |
| delete_list                           | -     | DeleteList                          |
| get_about_account                     | -     | AboutAccountQuery                   |
| get_blocked_users                     | -     | BlockedAccountsAll                  |
| get_dm_inbox                          | -     | dm/inbox_initial_state.json         |
| get_muted_users                       | -     | MutedAccounts                       |
| get_user_lists                        | -     | CombinedLists                       |
| get_user_spotlights                   | -     | ProfileSpotlightsQuery              |
| update_profile                        | -     | account/update_profile.json         |
