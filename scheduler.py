"""
定期自動取得スクリプト
使い方: python scheduler.py
毎朝 9:00 にデータを取得してExcelに保存します。
"""

import schedule
import time
from datetime import datetime
from instagram_api import InstagramAPI
from data_processor import fetch_account_insights_df, fetch_posts_df, compute_summary, export_to_excel


def run_export():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] インサイト取得開始...")
    try:
        api = InstagramAPI()
        account_info = api.get_account_info()
        insights_frames = fetch_account_insights_df(api, days=30)
        posts_df = fetch_posts_df(api, limit=50)
        filename = f"instagram_report_{datetime.now():%Y%m%d}.xlsx"
        path = export_to_excel(posts_df, insights_frames, path=filename)
        summary = compute_summary(account_info, insights_frames, posts_df)
        print(f"  フォロワー数: {summary.get('followers', 0):,}")
        print(f"  リーチ合計:  {summary.get('reach_total', 0):,}")
        print(f"  保存先:      {path}")
        print("完了")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    run_export()  # 起動時に即実行
    schedule.every().day.at("09:00").do(run_export)
    print("スケジューラ起動中（毎朝 9:00 に実行）。Ctrl+C で停止。")
    while True:
        schedule.run_pending()
        time.sleep(60)
