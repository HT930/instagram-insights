"""
デモ用サンプルデータ生成
認証情報がない環境で動くポートフォリオデモ用
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)


def _date_range(days: int):
    today = datetime.now().date()
    return [today - timedelta(days=i) for i in range(days - 1, -1, -1)]


def get_demo_account_info() -> dict:
    return {
        "id": "demo_account",
        "name": "Demo Brand",
        "username": "demo_brand_official",
        "followers_count": 12480,
        "media_count": 312,
        "biography": "📊 Instagram インサイトダッシュボード — デモアカウント",
        "website": "https://example.com",
    }


def get_demo_account_insights(days: int = 30) -> dict[str, pd.DataFrame]:
    dates = _date_range(days)
    base = len(dates)

    def trend(base_val, noise=0.15, drift=0.003):
        vals = []
        v = base_val
        for i in range(base):
            v = v * (1 + drift) + v * np.random.normal(0, noise)
            vals.append(max(0, int(v)))
        return vals

    frames = {
        "impressions":    pd.DataFrame({"date": dates, "value": trend(3200, 0.2)}),
        "reach":          pd.DataFrame({"date": dates, "value": trend(1800, 0.18)}),
        "profile_views":  pd.DataFrame({"date": dates, "value": trend(420, 0.25)}),
        "website_clicks": pd.DataFrame({"date": dates, "value": trend(85, 0.3)}),
        "follower_count": pd.DataFrame({"date": dates, "value": trend(12100, 0.01, 0.005)}),
    }
    return frames


def get_demo_posts_df(limit: int = 30) -> pd.DataFrame:
    media_types = ["IMAGE", "IMAGE", "IMAGE", "CAROUSEL_ALBUM", "REELS", "VIDEO"]
    captions = [
        "新しいプロダクトをリリースしました！詳細はプロフィールのリンクから",
        "チームの裏側を少しだけご紹介 #BehindTheScenes",
        "お客様の声をいただきました。ありがとうございます！",
        "季節限定コレクション、本日より販売開始",
        "朝の習慣を変えると一日が変わる ✨ #ライフスタイル",
        "新機能アップデートのお知らせ📱",
        "イベントレポート — 多くの方にお会いできました",
        "今月のハイライトをまとめました",
        "製品の使い方をご紹介します",
        "フォロワー様へ感謝のメッセージ 🙏",
    ]
    rows = []
    now = datetime.now()
    for i in range(min(limit, 30)):
        mt = random.choice(media_types)
        impressions = random.randint(800, 8000)
        reach = int(impressions * random.uniform(0.55, 0.85))
        likes = int(reach * random.uniform(0.03, 0.12))
        comments = int(likes * random.uniform(0.05, 0.2))
        saved = int(likes * random.uniform(0.1, 0.4))
        shares = int(likes * random.uniform(0.05, 0.15))
        engagement = likes + comments + saved
        rows.append({
            "id": f"demo_{i}",
            "timestamp": now - timedelta(days=i * 2 + random.randint(0, 1)),
            "media_type": mt,
            "caption": captions[i % len(captions)],
            "permalink": "https://www.instagram.com/p/demo/",
            "like_count": likes,
            "comments_count": comments,
            "impressions": impressions,
            "reach": reach,
            "saved": saved,
            "shares": shares,
            "engagement": engagement,
            "plays": random.randint(500, 5000) if mt in ("REELS", "VIDEO") else 0,
            "engagement_rate": round(engagement / impressions * 100, 2),
        })
    return pd.DataFrame(rows)


def get_demo_demographics() -> dict:
    gender_age = {
        "F.18-24": 820, "F.25-34": 1640, "F.35-44": 980, "F.45-54": 410,
        "M.18-24": 620, "M.25-34": 1240, "M.35-44": 740, "M.45-54": 310,
        "U.18-24": 120, "U.25-34": 180,
    }
    country = {
        "JP": 7200, "US": 1800, "TW": 840, "KR": 620,
        "HK": 410, "SG": 380, "AU": 290, "GB": 240,
    }
    city = {
        "東京都": 3200, "大阪府": 1400, "神奈川県": 980, "愛知県": 720,
        "福岡県": 580, "北海道": 430, "京都府": 390, "兵庫県": 360,
        "埼玉県": 310, "千葉県": 280,
    }
    return {
        "audience_gender_age": gender_age,
        "audience_country": country,
        "audience_city": city,
    }


def get_demo_summary(account_info: dict, insights_frames: dict, posts_df: pd.DataFrame) -> dict:
    from data_processor import compute_summary
    return compute_summary(account_info, insights_frames, posts_df)
