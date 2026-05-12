from __future__ import annotations
from datetime import datetime
import pandas as pd
from instagram_api import InstagramAPI


def fetch_account_insights_df(api: InstagramAPI, days: int = 30) -> dict[str, pd.DataFrame]:
    """アカウントインサイトを指標ごとの日次 DataFrame にまとめる"""
    raw = api.get_account_insights(period="day", days=days)
    frames = {}
    for metric_data in raw:
        name = metric_data["name"]
        rows = []
        for v in metric_data.get("values", []):
            rows.append({"date": pd.to_datetime(v["end_time"]).date(), "value": v["value"]})
        if rows:
            frames[name] = pd.DataFrame(rows).sort_values("date")
    return frames


def fetch_posts_df(api: InstagramAPI, limit: int = 50) -> pd.DataFrame:
    """投稿一覧 + 各投稿のインサイトを1つの DataFrame に"""
    media_list = api.get_media_list(limit=limit)
    rows = []
    for media in media_list:
        insights = api.get_media_insights(media["id"], media.get("media_type", "IMAGE"))
        row = {
            "id": media["id"],
            "timestamp": pd.to_datetime(media["timestamp"]),
            "media_type": media.get("media_type", ""),
            "caption": (media.get("caption", "") or "")[:80],
            "permalink": media.get("permalink", ""),
            "like_count": media.get("like_count", 0),
            "comments_count": media.get("comments_count", 0),
            **insights,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 型整形
    numeric_cols = ["like_count", "comments_count", "impressions", "reach", "saved", "shares", "engagement", "plays"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # エンゲージメント率
    if "impressions" in df.columns:
        df["engagement_rate"] = (
            (df.get("like_count", 0) + df.get("comments_count", 0) + df.get("saved", 0))
            / df["impressions"].replace(0, 1)
            * 100
        ).round(2)

    return df.sort_values("timestamp", ascending=False).reset_index(drop=True)


def compute_summary(account_info: dict, insights_frames: dict, posts_df: pd.DataFrame) -> dict:
    """サマリー指標を辞書で返す"""
    summary = {
        "followers": account_info.get("followers_count", 0),
        "media_count": account_info.get("media_count", 0),
        "username": account_info.get("username", ""),
    }

    for metric, df in insights_frames.items():
        if not df.empty:
            summary[f"{metric}_total"] = int(df["value"].sum())
            summary[f"{metric}_avg"] = round(df["value"].mean(), 1)
            summary[f"{metric}_latest"] = int(df["value"].iloc[-1])

    if not posts_df.empty:
        summary["avg_likes"] = round(posts_df["like_count"].mean(), 1) if "like_count" in posts_df.columns else 0
        summary["avg_comments"] = round(posts_df["comments_count"].mean(), 1) if "comments_count" in posts_df.columns else 0
        summary["avg_engagement_rate"] = round(posts_df["engagement_rate"].mean(), 2) if "engagement_rate" in posts_df.columns else 0

    return summary


def export_to_excel(posts_df: pd.DataFrame, insights_frames: dict, path: str = "instagram_report.xlsx"):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        if not posts_df.empty:
            posts_df.drop(columns=["permalink"], errors="ignore").to_excel(writer, sheet_name="投稿インサイト", index=False)
        for metric, df in insights_frames.items():
            df.to_excel(writer, sheet_name=metric[:31], index=False)
    return path
