"""
Instagram インサイト ダッシュボード
起動: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from instagram_api import InstagramAPI
from data_processor import fetch_account_insights_df, fetch_posts_df, compute_summary, export_to_excel

# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Instagram インサイト ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── スタイル ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px; border-radius: 12px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { font-size: 0.85rem; opacity: 0.9; margin-top: 4px; }
    .stAlert { border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── サイドバー ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png", width=60)
    st.title("設定")

    days = st.slider("取得期間（日数）", min_value=7, max_value=90, value=30, step=1)
    post_limit = st.slider("取得投稿数", min_value=10, max_value=100, value=30, step=5)

    st.divider()
    refresh = st.button("データを更新", type="primary", use_container_width=True)

    st.divider()
    st.caption("Instagram Graph API v20.0")
    st.caption(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── データ取得（キャッシュ付き） ──────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def load_data(days: int, post_limit: int):
    api = InstagramAPI()
    account_info = api.get_account_info()
    insights_frames = fetch_account_insights_df(api, days=days)
    posts_df = fetch_posts_df(api, limit=post_limit)
    summary = compute_summary(account_info, insights_frames, posts_df)
    demographics = api.get_audience_demographics()
    return account_info, insights_frames, posts_df, summary, demographics


if refresh:
    st.cache_data.clear()

# ── 初期化チェック ─────────────────────────────────────────────────────────────
try:
    with st.spinner("Instagram データを取得中..."):
        account_info, insights_frames, posts_df, summary, demographics = load_data(days, post_limit)
except ValueError as e:
    st.error(f"設定エラー: {e}")
    st.info("プロジェクトルートに `.env` ファイルを作成し、`.env.example` を参考に設定してください。")
    st.stop()
except Exception as e:
    st.error(f"API エラー: {e}")
    st.stop()

# ── ヘッダー ──────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(f"@{summary.get('username', '')} のインサイト")
    st.caption(f"過去 {days} 日間のデータ  |  投稿数: {summary.get('media_count', 0)}")
with col_h2:
    if st.button("Excelエクスポート"):
        path = export_to_excel(posts_df, insights_frames)
        with open(path, "rb") as f:
            st.download_button("ダウンロード", f, file_name=path, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()

# ── サマリー KPI ───────────────────────────────────────────────────────────────
kpi_cols = st.columns(5)
kpis = [
    ("フォロワー数", f"{summary.get('followers', 0):,}", "👥"),
    ("リーチ合計", f"{summary.get('reach_total', 0):,}", "📡"),
    ("インプレッション", f"{summary.get('impressions_total', 0):,}", "👁️"),
    ("プロフィール閲覧", f"{summary.get('profile_views_total', 0):,}", "🔍"),
    ("平均エンゲージ率", f"{summary.get('avg_engagement_rate', 0):.2f}%", "💬"),
]
for col, (label, value, icon) in zip(kpi_cols, kpis):
    with col:
        st.metric(label=f"{icon} {label}", value=value)

st.divider()

# ── タブレイアウト ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 トレンド", "📝 投稿分析", "👥 オーディエンス", "🔧 設定・ヘルプ"])

# ═══════════════════════════════════════════════════════════════════
# Tab 1: トレンドグラフ
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("日次トレンド")

    metric_labels = {
        "impressions": "インプレッション",
        "reach": "リーチ",
        "profile_views": "プロフィール閲覧数",
        "website_clicks": "ウェブサイトクリック",
        "follower_count": "フォロワー数",
    }

    # リーチ + インプレッション
    if "reach" in insights_frames and "impressions" in insights_frames:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=insights_frames["impressions"]["date"], y=insights_frames["impressions"]["value"],
                   name="インプレッション", marker_color="rgba(102,126,234,0.7)"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=insights_frames["reach"]["date"], y=insights_frames["reach"]["value"],
                       name="リーチ", line=dict(color="#f093fb", width=2.5), mode="lines+markers"),
            secondary_y=True,
        )
        fig.update_layout(title="インプレッション & リーチ", hovermode="x unified", height=380,
                          legend=dict(orientation="h", y=1.1))
        fig.update_yaxes(title_text="インプレッション", secondary_y=False)
        fig.update_yaxes(title_text="リーチ", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        if "profile_views" in insights_frames:
            df_pv = insights_frames["profile_views"]
            fig = px.area(df_pv, x="date", y="value", title="プロフィール閲覧数",
                          color_discrete_sequence=["#4facfe"])
            fig.update_layout(height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if "follower_count" in insights_frames:
            df_fc = insights_frames["follower_count"]
            fig = px.line(df_fc, x="date", y="value", title="フォロワー推移",
                          color_discrete_sequence=["#43e97b"], markers=True)
            fig.update_layout(height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    if "website_clicks" in insights_frames:
        df_wc = insights_frames["website_clicks"]
        fig = px.bar(df_wc, x="date", y="value", title="ウェブサイトクリック数",
                     color_discrete_sequence=["#fa709a"])
        fig.update_layout(height=260, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# Tab 2: 投稿分析
# ═══════════════════════════════════════════════════════════════════
with tab2:
    if posts_df.empty:
        st.info("投稿データが取得できませんでした。")
    else:
        st.subheader("投稿パフォーマンス")

        col_a, col_b = st.columns(2)

        with col_a:
            # エンゲージメント率 バブルチャート
            if "engagement_rate" in posts_df.columns and "reach" in posts_df.columns:
                fig = px.scatter(
                    posts_df.head(30),
                    x="timestamp", y="engagement_rate",
                    size="reach" if "reach" in posts_df.columns else None,
                    color="media_type",
                    hover_data=["caption", "like_count", "comments_count"],
                    title="エンゲージメント率（バブル=リーチ数）",
                    height=360,
                )
                fig.update_layout(legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            # メディアタイプ別 平均エンゲージメント
            if "engagement_rate" in posts_df.columns:
                type_avg = posts_df.groupby("media_type")["engagement_rate"].mean().reset_index()
                fig = px.bar(type_avg, x="media_type", y="engagement_rate",
                             title="メディアタイプ別 平均エンゲージメント率",
                             color="media_type", height=360,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # いいね・コメント・保存 分布
        metric_options = [c for c in ["like_count", "comments_count", "saved", "shares", "impressions", "reach"] if c in posts_df.columns]
        if metric_options:
            selected_metric = st.selectbox("指標を選択", metric_options,
                                           format_func=lambda x: {"like_count": "いいね", "comments_count": "コメント",
                                                                   "saved": "保存", "shares": "シェア",
                                                                   "impressions": "インプレッション", "reach": "リーチ"}.get(x, x))
            fig = px.histogram(posts_df, x=selected_metric, nbins=20,
                               title=f"{selected_metric} の分布",
                               color_discrete_sequence=["#667eea"])
            fig.update_layout(height=260)
            st.plotly_chart(fig, use_container_width=True)

        # トップ投稿テーブル
        st.subheader("トップ投稿")
        display_cols = [c for c in ["timestamp", "media_type", "caption", "like_count", "comments_count",
                                    "saved", "impressions", "reach", "engagement_rate", "permalink"]
                        if c in posts_df.columns]
        top_posts = posts_df[display_cols].head(20).copy()
        top_posts["timestamp"] = top_posts["timestamp"].dt.strftime("%Y-%m-%d")
        if "permalink" in top_posts.columns:
            top_posts["permalink"] = top_posts["permalink"].apply(lambda u: f"[開く]({u})" if u else "")
        st.dataframe(top_posts, use_container_width=True, height=420)

# ═══════════════════════════════════════════════════════════════════
# Tab 3: オーディエンス
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("フォロワー属性")

    gender_age = demographics.get("audience_gender_age", {})
    country = demographics.get("audience_country", {})
    city = demographics.get("audience_city", {})

    if gender_age:
        col_ga, col_c = st.columns(2)
        with col_ga:
            ga_df = pd.DataFrame(list(gender_age.items()), columns=["segment", "count"])
            ga_df["gender"] = ga_df["segment"].str.split(".").str[0]
            ga_df["age"] = ga_df["segment"].str.split(".").str[1]
            fig = px.bar(ga_df.sort_values("count", ascending=False).head(20),
                         x="age", y="count", color="gender",
                         title="性別・年齢層", barmode="group",
                         color_discrete_map={"F": "#f093fb", "M": "#4facfe", "U": "#aaa"},
                         height=340)
            st.plotly_chart(fig, use_container_width=True)

        if country:
            with col_c:
                c_df = pd.DataFrame(list(country.items()), columns=["country", "count"])
                fig = px.pie(c_df.head(10), values="count", names="country",
                             title="国別フォロワー TOP10", height=340)
                st.plotly_chart(fig, use_container_width=True)

        if city:
            city_df = pd.DataFrame(list(city.items()), columns=["city", "count"]).sort_values("count", ascending=False).head(15)
            fig = px.bar(city_df, x="count", y="city", orientation="h",
                         title="都市別フォロワー TOP15", height=400,
                         color_discrete_sequence=["#43e97b"])
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("オーディエンスデータが取得できませんでした（Businessアカウントかつフォロワー100人以上が必要です）。")

# ═══════════════════════════════════════════════════════════════════
# Tab 4: 設定・ヘルプ
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("セットアップガイド")

    with st.expander("1. Meta Developer Console でアプリを作成する", expanded=True):
        st.markdown("""
        1. [developers.facebook.com](https://developers.facebook.com/) にアクセスしてログイン
        2. 「アプリを作成」→ タイプ「ビジネス」を選択
        3. 「Instagram Graph API」製品を追加
        4. Instagram ビジネスアカウントをリンク
        """)

    with st.expander("2. アクセストークンを取得する"):
        st.markdown("""
        1. Graph API Explorer (`/tools/explorer/`) を開く
        2. アプリを選択 → 「ユーザートークンを生成」
        3. 権限: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`
        4. 生成されたトークンを `.env` の `INSTAGRAM_ACCESS_TOKEN` にセット
        """)

    with st.expander("3. ビジネスアカウント ID を確認する"):
        st.markdown("""
        ```bash
        curl "https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_TOKEN"
        # → page の id を取得
        curl "https://graph.facebook.com/v20.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
        # → instagram_business_account.id を INSTAGRAM_BUSINESS_ACCOUNT_ID にセット
        ```
        """)

    with st.expander("4. 長期トークンに交換する（推奨）"):
        st.markdown("""
        短期トークン（1時間）を60日有効な長期トークンに交換します。
        `.env` に `FB_APP_ID` と `FB_APP_SECRET` を設定後、以下を実行:
        """)
        if st.button("長期トークンに交換"):
            try:
                api = InstagramAPI()
                new_token = api.exchange_for_long_lived_token()
                st.success("交換成功！以下のトークンを `.env` に保存してください:")
                st.code(new_token)
            except Exception as e:
                st.error(f"エラー: {e}")

    st.subheader("トークン情報")
    if st.button("トークン有効期限を確認"):
        try:
            api = InstagramAPI()
            info = api.check_token_expiry()
            exp = info.get("expires_at")
            if exp:
                exp_dt = datetime.fromtimestamp(exp)
                remaining = (exp_dt - datetime.now()).days
                st.info(f"有効期限: {exp_dt.strftime('%Y-%m-%d %H:%M')}（残り {remaining} 日）")
            else:
                st.success("無期限トークン（または期限情報なし）")
            st.json(info)
        except Exception as e:
            st.error(f"エラー: {e}")
