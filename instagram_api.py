import os
import requests
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://graph.facebook.com/v20.0"

def _get_secret(key: str) -> str:
    """ローカル .env → Streamlit secrets の順で取得"""
    value = os.getenv(key)
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(key)
        except Exception:
            pass
    return value or ""


class InstagramAPI:
    def __init__(self):
        self.access_token = _get_secret("INSTAGRAM_ACCESS_TOKEN")
        self.account_id = _get_secret("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        if not self.access_token or not self.account_id:
            raise ValueError(".env ファイルに INSTAGRAM_ACCESS_TOKEN と INSTAGRAM_BUSINESS_ACCOUNT_ID を設定してください")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        params["access_token"] = self.access_token
        url = f"{BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── アカウント基本情報 ──────────────────────────────────────────────
    def get_account_info(self) -> dict:
        data = self._get(
            self.account_id,
            {"fields": "id,name,username,followers_count,media_count,biography,profile_picture_url,website"},
        )
        return data

    # ── アカウントレベルのインサイト ─────────────────────────────────────
    def get_account_insights(self, period: str = "day", days: int = 30) -> list[dict]:
        """
        period: "day" | "week" | "month"
        metrics: impressions, reach, profile_views, website_clicks, follower_count
        """
        since = int((datetime.now() - timedelta(days=days)).timestamp())
        until = int(datetime.now().timestamp())

        metrics = [
            "impressions",
            "reach",
            "profile_views",
            "website_clicks",
            "follower_count",
        ]
        data = self._get(
            f"{self.account_id}/insights",
            {
                "metric": ",".join(metrics),
                "period": period,
                "since": since,
                "until": until,
            },
        )
        return data.get("data", [])

    # ── 投稿一覧 ────────────────────────────────────────────────────────
    def get_media_list(self, limit: int = 50) -> list[dict]:
        data = self._get(
            f"{self.account_id}/media",
            {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
                "limit": limit,
            },
        )
        return data.get("data", [])

    # ── 投稿ごとのインサイト ─────────────────────────────────────────────
    def get_media_insights(self, media_id: str, media_type: str = "IMAGE") -> dict:
        if media_type in ("IMAGE", "CAROUSEL_ALBUM"):
            metrics = "impressions,reach,likes,comments,saved,shares,engagement"
        elif media_type == "VIDEO":
            metrics = "impressions,reach,likes,comments,saved,shares,plays"
        elif media_type == "REELS":
            metrics = "plays,reach,likes,comments,saved,shares"
        else:
            metrics = "impressions,reach,likes,comments,saved"

        try:
            data = self._get(f"{media_id}/insights", {"metric": metrics})
            result = {}
            for item in data.get("data", []):
                result[item["name"]] = item["values"][0]["value"] if item.get("values") else item.get("value", 0)
            return result
        except requests.HTTPError:
            return {}

    # ── フォロワーデモグラフィクス ────────────────────────────────────────
    def get_audience_demographics(self) -> dict:
        metrics = ["audience_city", "audience_country", "audience_gender_age"]
        result = {}
        for metric in metrics:
            try:
                data = self._get(
                    f"{self.account_id}/insights",
                    {"metric": metric, "period": "lifetime"},
                )
                if data.get("data"):
                    result[metric] = data["data"][0].get("value", {})
            except requests.HTTPError:
                result[metric] = {}
        return result

    # ── トークン有効期限確認 ───────────────────────────────────────────────
    def check_token_expiry(self) -> dict:
        data = self._get(
            "debug_token",
            {
                "input_token": self.access_token,
                "access_token": self.access_token,
            },
        )
        return data.get("data", {})

    # ── 長期トークンへの交換 ───────────────────────────────────────────────
    def exchange_for_long_lived_token(self) -> str:
        app_id = os.getenv("FB_APP_ID")
        app_secret = os.getenv("FB_APP_SECRET")
        if not app_id or not app_secret:
            raise ValueError("FB_APP_ID と FB_APP_SECRET を .env に設定してください")
        data = self._get(
            "oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": self.access_token,
            },
        )
        return data.get("access_token", "")
