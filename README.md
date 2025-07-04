# Discord TTS Bot with Web UI

A.I.VOICE を使用したDiscord TTSボット。Webブラウザから詳細な音声設定が可能です。

## 🌟 機能一覧

### TTS機能
- Discord ボイスチャンネルでのリアルタイム読み上げ
- A.I.VOICE による高品質な音声合成
- ユーザーごとの個別音声設定

### Web UI機能
- ブラウザからの直感的な音声パラメータ調整
- Discord OAuth2 による安全なログイン
- リアルタイム設定反映（Web画面で変更→即座にDiscordに反映）

### 設定可能パラメータ
- 🎭 音声キャラクター選択
- 🎚️ ピッチ・速度・音量調整
- 🎪 ピッチレンジ・ポーズ時間設定
- 😊 感情スタイル（Joy/Angry/Sad）

## 🚀 セットアップ

### 1. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数設定
`.env` ファイルを作成：
```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/callback
```

### 3. データベース初期化
初回起動時、自動的にSQLiteデータベースが作成されます。
既存の `voice_settings.json` がある場合は自動的にマイグレーションされます。

### 4. 起動
```bash
python main.py
```

## 🎮 使用方法

### Discord コマンド
- `/voice join` - ボイスチャンネルに参加
- `/voice leave` - ボイスチャンネルから退出
- `/voice set_voice` - 音声キャラクター設定
- `/voice settings` - Web設定画面のリンク表示

### Web設定画面
1. http://localhost:8080 にアクセス
2. Discordアカウントでログイン
3. 音声パラメータを調整
4. 設定は即座にDiscordに反映されます

## 🗄️ データベース

- **SQLite** + **Tortoise ORM** を使用
- 非同期処理対応
- 自動マイグレーション機能
- JSON設定ファイルからの移行サポート

## 📝 ライセンス

MIT License
