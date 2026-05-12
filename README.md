# Instagram インサイト ダッシュボード

Instagram Graph API を使ってインサイトを自動取得し、Streamlit でリアルタイムダッシュボード表示するツールです。

## 機能

| 機能 | 内容 |
|------|------|
| アカウント概要 | フォロワー数・インプレッション・リーチ・プロフィール閲覧など KPI 表示 |
| 日次トレンド | リーチ・インプレッション・プロフィール閲覧・ウェブサイトクリック推移グラフ |
| 投稿分析 | いいね・コメント・保存・エンゲージメント率・メディアタイプ別比較 |
| オーディエンス | 性別・年齢層・国・都市別フォロワー属性 |
| Excel エクスポート | ワンクリックで Excel レポート出力 |
| 自動定期取得 | スケジューラで毎朝データを自動保存 |

## セットアップ

### 1. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# .env を編集して ACCESS_TOKEN と ACCOUNT_ID を入力
```

### 3. Meta Developer Console でトークンを取得

1. https://developers.facebook.com/ でアプリ作成（タイプ: ビジネス）
2. Instagram Graph API 製品を追加
3. Graph API Explorer でトークン生成（必要権限は下記）
4. ビジネスアカウント ID を確認

**必要な権限:**
- `instagram_basic`
- `instagram_manage_insights`
- `pages_show_list`
- `pages_read_engagement`

**ビジネスアカウント ID の確認コマンド:**
```bash
# Step 1: ページ ID を取得
curl "https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_TOKEN"

# Step 2: Instagram ビジネスアカウント ID を取得
curl "https://graph.facebook.com/v20.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```

### 4. ダッシュボードを起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

### 5. 定期自動エクスポート（オプション）

```bash
python scheduler.py
# 起動と同時に即時取得し、以後毎朝 9:00 に Excel 保存
```

## ファイル構成

```
instagram-insights/
├── app.py              # Streamlit ダッシュボード（メイン）
├── instagram_api.py    # Instagram Graph API クライアント
├── data_processor.py   # データ整形・集計・エクスポート
├── scheduler.py        # 定期自動取得スクリプト
├── requirements.txt
├── .env.example
└── README.md
```

## 注意事項

- Instagram **ビジネス** または **クリエイター** アカウントが必要です
- インサイトデータはフォロワー 100 人以上で取得可能な指標があります
- アクセストークンは 60 日で期限切れ → ダッシュボードの「設定」タブから長期トークンに交換可能
