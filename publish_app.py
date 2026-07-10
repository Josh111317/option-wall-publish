"""只读发布版：展示 daily_data 中已经导出的期权 Wall 结果。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
GA_MEASUREMENT_ID = "G-9VW3TM6793"
FEEDBACK_FORM_URL = ""
DONATION_LINKS = {
    "爱发电": "",
    "Buy Me a Coffee": "",
}
DONATION_QR_FILES = {
    "微信打赏": APP_DIR / "assets" / "wechat_reward.png",
    "支付宝打赏": APP_DIR / "assets" / "alipay_reward.png",
}
DATA_DIR_CANDIDATES = [
    APP_DIR / "daily_data",
    APP_DIR.parent / "daily_data",
]


def inject_google_analytics(measurement_id: str) -> None:
    """Inject GA4 tracking for the read-only published dashboard."""
    if not measurement_id:
        return
    components.html(
        f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          let pagePath = window.location.pathname || '/';
          try {{
            if (window.parent && window.parent.location && window.parent.location.pathname) {{
              pagePath = window.parent.location.pathname;
            }}
          }} catch (error) {{
            pagePath = window.location.pathname || '/';
          }}
          gtag('js', new Date());
          gtag('config', '{measurement_id}', {{
            page_title: 'Option Wall Published Dashboard',
            page_path: pagePath,
            send_page_view: true
          }});
          gtag('event', 'page_view', {{
            page_title: 'Option Wall Published Dashboard',
            page_path: pagePath
          }});
        </script>
        """,
        height=0,
        width=0,
    )


def inject_ga_event(event_name: str, params: dict[str, object] | None = None) -> None:
    """Send a lightweight GA4 custom event from a Streamlit component iframe."""
    if not GA_MEASUREMENT_ID:
        return
    params = params or {}
    safe_params = {
        str(key): "" if value is None else str(value)
        for key, value in params.items()
    }
    params_lines = ",\n".join(
        f"{key!r}: {value!r}" for key, value in safe_params.items()
    )
    components.html(
        f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{GA_MEASUREMENT_ID}', {{ send_page_view: false }});
          gtag('event', '{event_name}', {{
            {params_lines}
          }});
        </script>
        """,
        height=0,
        width=0,
    )


def inject_tab_click_tracking() -> None:
    """Track Streamlit tab clicks in GA4 without changing the visual layout."""
    if not GA_MEASUREMENT_ID:
        return
    components.html(
        f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{GA_MEASUREMENT_ID}', {{ send_page_view: false }});

          function bindTabTracking() {{
            let doc = null;
            try {{
              doc = window.parent.document;
            }} catch (error) {{
              return;
            }}
            const tabs = doc.querySelectorAll('button[role="tab"]');
            tabs.forEach((tab) => {{
              if (tab.dataset.gaBound === '1') {{
                return;
              }}
              tab.dataset.gaBound = '1';
              tab.addEventListener('click', () => {{
                const label = (tab.innerText || tab.textContent || '').trim();
                if (label) {{
                  gtag('event', 'view_tab', {{
                    tab_name: label,
                    app_name: 'option_wall_publish'
                  }});
                }}
              }});
            }});
          }}
          setTimeout(bindTabTracking, 1000);
          setTimeout(bindTabTracking, 2500);
        </script>
        """,
        height=0,
        width=0,
    )


def track_download_click(file_name: str, trade_date_text: str) -> None:
    """Store a download event so the next Streamlit run can emit it to GA4."""
    st.session_state["pending_ga_event"] = {
        "event_name": "download_result_file",
        "params": {
            "file_name": file_name,
            "trade_date": trade_date_text,
        },
    }


def emit_pending_ga_event() -> None:
    """Emit and clear one pending GA event from a widget callback."""
    event = st.session_state.pop("pending_ga_event", None)
    if isinstance(event, dict):
        inject_ga_event(str(event.get("event_name", "")), event.get("params", {}))


def find_daily_data_dir() -> Path:
    """寻找 daily_data 目录，兼容本地生产目录和云端 repo 目录。"""
    for path in DATA_DIR_CANDIDATES:
        if path.exists():
            return path
    return DATA_DIR_CANDIDATES[0]


DAILY_DATA_DIR = find_daily_data_dir()


def format_date_token(value) -> str:
    """把日期转为文件名中的 YYYYMMDD。"""
    return pd.to_datetime(value).strftime("%Y%m%d")


def dated_name(file_name: str, trade_date_value) -> str:
    """根据原始导出名生成带日期文件名。"""
    path = Path(file_name)
    return f"{path.stem}_{format_date_token(trade_date_value)}{path.suffix}"


@st.cache_data(show_spinner=False)
def load_index(data_dir_text: str) -> pd.DataFrame:
    """读取 daily_data/index.csv。"""
    path = Path(data_dir_text) / "index.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def scan_dates_from_files(data_dir: Path) -> list[date]:
    """没有 index.csv 时，从文件名中扫描可用日期。"""
    dates = set()
    for path in data_dir.glob("*_*.*"):
        token = path.stem.rsplit("_", 1)[-1]
        if len(token) == 8 and token.isdigit():
            parsed = pd.to_datetime(token, format="%Y%m%d", errors="coerce")
            if pd.notna(parsed):
                dates.add(parsed.date())
    return sorted(dates)


def available_dates(index: pd.DataFrame, data_dir: Path) -> list[date]:
    """获取可发布日期列表。"""
    if not index.empty and "trade_date" in index.columns:
        values = pd.to_datetime(index["trade_date"], errors="coerce").dropna().dt.date.unique().tolist()
        return sorted(values)
    return scan_dates_from_files(data_dir)


def resolve_export_path(data_dir: Path, file_name: str, trade_date_value) -> Path:
    """解析某个导出文件在 daily_data 下的路径。"""
    dated = data_dir / dated_name(file_name, trade_date_value)
    if dated.exists():
        return dated
    plain = data_dir / file_name
    if plain.exists():
        return plain
    return dated


@st.cache_data(show_spinner=False)
def read_csv_file(path_text: str) -> pd.DataFrame:
    """读取 CSV，缺失时返回空表。"""
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def read_text_file(path_text: str) -> str:
    """读取 TXT，缺失时返回空字符串。"""
    path = Path(path_text)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def load_exports(data_dir: Path, trade_date_value) -> dict[str, object]:
    """读取发布页需要展示的导出文件。"""
    csv_names = [
        "daily_wall_summary.csv",
        "etf_gamma_by_strike.csv",
        "key_strike_context.csv",
        "wall_confidence.csv",
        "spot_position_features.csv",
        "wall_features.csv",
        "key_level_table.csv",
        "gamma_audit_table.csv",
        "comparison_table.csv",
    ]
    result: dict[str, object] = {}
    for name in csv_names:
        path = resolve_export_path(data_dir, name, trade_date_value)
        result[name] = read_csv_file(str(path))
        result[f"{name}__path"] = path

    for name in ["market_structure_report.txt", "range_structure_report.txt"]:
        path = resolve_export_path(data_dir, name, trade_date_value)
        result[name] = read_text_file(str(path))
        result[f"{name}__path"] = path
    return result


def format_value(value, digits: int = 4) -> str:
    """格式化指标卡。"""
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return str(value)


def add_vline(fig: go.Figure, value, label: str, color: str) -> None:
    """给图表增加关键价位竖线。"""
    if value is not None and pd.notna(value):
        fig.add_vline(x=value, line_dash="dash", line_color=color, annotation_text=label)


def build_etf_gex_chart(frame: pd.DataFrame, summary_row: dict) -> go.Figure:
    """构建只读 ETF Gamma Wall 图。"""
    fig = go.Figure()
    if frame.empty:
        return fig
    data = frame.sort_values("strike")
    fig.add_bar(x=data["strike"], y=data["call_gex"], name="Call GEX", marker_color="#d84a4a")
    fig.add_bar(x=data["strike"], y=data["put_gex"], name="Put GEX", marker_color="#37a66b")
    fig.add_trace(go.Scatter(x=data["strike"], y=data["net_gex"], mode="lines+markers", name="Net GEX"))
    for key, label, color in [
        ("underlying_price", "Spot", "#f2c94c"),
        ("call_wall", "Call Wall", "#ff5c5c"),
        ("put_wall", "Put Wall", "#4cd97b"),
        ("price_wall", "Price Wall", "#f2994a"),
        ("max_gamma_strike", "Max Gamma", "#bb6bd9"),
        ("gex_flip", "GEX Flip", "#56ccf2"),
    ]:
        add_vline(fig, summary_row.get(key), label, color)
    fig.update_layout(
        template="plotly_dark",
        barmode="relative",
        height=560,
        title="ETF Gamma Wall",
        xaxis_title="Strike",
        yaxis_title="Gamma Exposure",
        legend_orientation="h",
    )
    return fig


def build_context_chart(context: pd.DataFrame) -> go.Figure:
    """构建分价位上下文图。"""
    fig = go.Figure()
    if context.empty:
        return fig
    data = context.sort_values("strike")
    fig.add_bar(x=data["strike"], y=data["total_abs_gex"], name="Total Abs GEX", marker_color="#56ccf2")
    fig.add_trace(go.Scatter(x=data["strike"], y=data["total_oi"], mode="lines+markers", name="Total OI", yaxis="y2"))
    fig.update_layout(
        template="plotly_dark",
        height=420,
        title="Key Strike Context",
        xaxis_title="Strike",
        yaxis_title="Total Abs GEX",
        yaxis2={"title": "Total OI", "overlaying": "y", "side": "right"},
        legend_orientation="h",
    )
    return fig


def build_confidence_chart(confidence: pd.DataFrame) -> go.Figure:
    """构建 Wall 可信度图。"""
    fig = go.Figure()
    if confidence.empty:
        return fig
    data = confidence.copy()
    data["label"] = data["underlying"].astype(str) + " " + data["contract_month"].astype(str) + " " + data["wall_type"].astype(str)
    data = data.sort_values("confidence_score", ascending=False).head(30)
    fig.add_bar(
        x=data["confidence_score"],
        y=data["label"],
        orientation="h",
        marker_color="#f2994a",
        customdata=data[["strike", "confidence_label"]],
        hovertemplate="score=%{x:.3f}<br>strike=%{customdata[0]}<br>label=%{customdata[1]}<extra></extra>",
    )
    fig.update_layout(template="plotly_dark", height=620, title="Wall Confidence", xaxis_title="Confidence Score")
    fig.update_yaxes(autorange="reversed")
    return fig


def build_regime_distribution_chart(comparison: pd.DataFrame) -> go.Figure:
    """构建 Gamma Regime 分布图。"""
    fig = go.Figure()
    if comparison.empty or "gamma_regime" not in comparison.columns:
        return fig
    counts = (
        comparison["gamma_regime"]
        .fillna("Unavailable")
        .replace("", "Unavailable")
        .value_counts()
        .rename_axis("gamma_regime")
        .reset_index(name="count")
    )
    fig.add_bar(x=counts["gamma_regime"], y=counts["count"], marker_color="#4c78a8", name="count")
    fig.update_layout(template="plotly_dark", height=330, title="Gamma Regime Distribution", yaxis_title="Count")
    return fig


def build_net_gex_ranking_chart(comparison: pd.DataFrame) -> go.Figure:
    """构建多标的 Net GEX 排名图。"""
    fig = go.Figure()
    if comparison.empty or "underlying" not in comparison.columns or "net_gex" not in comparison.columns:
        return fig
    data = comparison.copy()
    data["net_gex"] = pd.to_numeric(data["net_gex"], errors="coerce")
    data["total_abs_gex"] = pd.to_numeric(data.get("total_abs_gex", pd.Series(dtype=float)), errors="coerce")
    ranking = (
        data.groupby("underlying", dropna=False)
        .agg(net_gex=("net_gex", "sum"), total_abs_gex=("total_abs_gex", "sum"))
        .reset_index()
        .sort_values("net_gex", ascending=True)
    )
    colors = ["#d84a4a" if value < 0 else "#37a66b" for value in ranking["net_gex"].fillna(0)]
    fig.add_bar(
        x=ranking["net_gex"],
        y=ranking["underlying"],
        orientation="h",
        marker_color=colors,
        customdata=ranking[["total_abs_gex"]],
        hovertemplate="underlying=%{y}<br>net_gex=%{x:,.2f}<br>total_abs_gex=%{customdata[0]:,.2f}<extra></extra>",
        name="Net GEX",
    )
    fig.update_layout(template="plotly_dark", height=420, title="Net GEX Ranking", xaxis_title="Net GEX")
    return fig


def build_price_wall_distance_heatmap(comparison: pd.DataFrame) -> go.Figure:
    """构建 Price Wall Distance 热力图。"""
    fig = go.Figure()
    required = {"underlying", "contract_month", "price_wall_distance"}
    if comparison.empty or not required.issubset(comparison.columns):
        return fig
    data = comparison.copy()
    data["price_wall_distance"] = pd.to_numeric(data["price_wall_distance"], errors="coerce")
    matrix = data.pivot_table(
        index="underlying",
        columns="contract_month",
        values="price_wall_distance",
        aggfunc="mean",
    ).sort_index(axis=0).sort_index(axis=1)
    if matrix.empty:
        return fig
    fig.add_heatmap(
        z=matrix.values,
        x=[str(col) for col in matrix.columns],
        y=[str(idx) for idx in matrix.index],
        colorscale="RdYlGn",
        zmid=0,
        colorbar={"title": "distance"},
        hovertemplate="underlying=%{y}<br>contract_month=%{x}<br>price_wall_distance=%{z:.2%}<extra></extra>",
    )
    fig.update_layout(
        template="plotly_dark",
        height=max(380, 34 * len(matrix.index) + 140),
        title="Price Wall Distance Heatmap",
        xaxis_title="Contract Month",
    )
    return fig


def show_downloads(exports: dict[str, object], trade_date_value) -> None:
    """展示已导出结果的下载按钮。"""
    st.subheader("下载结果")
    names = [
        "daily_wall_summary.csv",
        "etf_gamma_by_strike.csv",
        "key_strike_context.csv",
        "wall_confidence.csv",
        "spot_position_features.csv",
        "wall_features.csv",
        "comparison_table.csv",
        "market_structure_report.txt",
        "range_structure_report.txt",
    ]
    cols = st.columns(3)
    for idx, name in enumerate(names):
        path = exports.get(f"{name}__path")
        with cols[idx % 3]:
            if isinstance(path, Path) and path.exists():
                mime = "text/plain" if name.endswith(".txt") else "text/csv"
                st.download_button(
                    f"下载 {name}",
                    data=path.read_bytes(),
                    file_name=dated_name(name, trade_date_value),
                    mime=mime,
                    key=f"publish_download_{name}",
                    on_click=track_download_click,
                    args=(name, str(trade_date_value)),
                )
            else:
                st.button(f"缺失 {name}", disabled=True, key=f"missing_{name}")


def render_overview(exports: dict[str, object], report_text: str) -> None:
    """今日总览。"""
    summary = exports["daily_wall_summary.csv"]
    wall_features = exports["wall_features.csv"]
    st.subheader("今日总览")
    if isinstance(summary, pd.DataFrame) and not summary.empty:
        etf_count = int(summary[summary.get("market_type", "").eq("ETF")]["underlying"].nunique()) if "market_type" in summary.columns else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Summary Rows", len(summary))
        c2.metric("ETF Count", etf_count)
        if "gamma_regime" in summary.columns:
            positive = int(summary["gamma_regime"].fillna("").eq("Positive Gamma").sum())
            negative = int(summary["gamma_regime"].fillna("").eq("Negative Gamma").sum())
            c3.metric("Positive Gamma", positive)
            c4.metric("Negative Gamma", negative)
        st.dataframe(summary, use_container_width=True)
    else:
        st.warning("未找到 daily_wall_summary.csv。")

    if isinstance(wall_features, pd.DataFrame) and not wall_features.empty:
        with st.expander("wall_features", expanded=False):
            st.dataframe(wall_features, use_container_width=True)

    st.subheader("自动报告")
    if report_text:
        st.text_area("市场结构分析报告", report_text, height=520, key="publish_market_report")
    else:
        st.info("未找到 market_structure_report.txt。")


def render_etf_gamma(exports: dict[str, object]) -> None:
    """ETF Gamma Wall 结果。"""
    summary = exports["daily_wall_summary.csv"]
    by_strike = exports["etf_gamma_by_strike.csv"]
    st.subheader("ETF Gamma Wall 结果")
    if not isinstance(summary, pd.DataFrame) or summary.empty or not isinstance(by_strike, pd.DataFrame) or by_strike.empty:
        st.warning("缺少 ETF Gamma Wall 展示所需 CSV。")
        return

    etf_summary = summary[summary["market_type"].eq("ETF")].copy() if "market_type" in summary.columns else summary.copy()
    if etf_summary.empty:
        st.warning("当前 summary 中没有 ETF 数据。")
        return
    choices = [
        f"{row.underlying} | {row.contract_month}"
        for row in etf_summary.itertuples(index=False)
    ]
    selected = st.selectbox("ETF 标的 / 合约月份", choices, key="publish_etf_choice")
    underlying, month = selected.split(" | ", 1)
    summary_row = etf_summary[
        (etf_summary["underlying"].astype(str) == underlying)
        & (etf_summary["contract_month"].astype(str) == month)
    ].iloc[0].to_dict()
    frame = by_strike[
        (by_strike["underlying"].astype(str) == underlying)
        & (by_strike["contract_month"].astype(str) == month)
    ]

    cols = st.columns(6)
    for col, key in zip(cols, ["underlying_price", "call_wall", "put_wall", "price_wall", "gex_flip", "net_gex"]):
        col.metric(key, format_value(summary_row.get(key)))
    st.plotly_chart(build_etf_gex_chart(frame, summary_row), use_container_width=True)
    st.dataframe(frame, use_container_width=True)


def render_structure_tabs(exports: dict[str, object]) -> None:
    """分价位、可信度和现价位置。"""
    context = exports["key_strike_context.csv"]
    confidence = exports["wall_confidence.csv"]
    spot_position = exports["spot_position_features.csv"]

    st.subheader("分价位结构")
    if isinstance(context, pd.DataFrame) and not context.empty:
        choices = sorted((context["underlying"].astype(str) + " | " + context["contract_month"].astype(str)).unique())
        selected = st.selectbox("选择标的 / 月份", choices, key="publish_context_choice")
        underlying, month = selected.split(" | ", 1)
        frame = context[
            (context["underlying"].astype(str) == underlying)
            & (context["contract_month"].astype(str) == month)
        ]
        st.plotly_chart(build_context_chart(frame), use_container_width=True)
        st.dataframe(frame, use_container_width=True)
    else:
        st.warning("未找到 key_strike_context.csv。")

    st.subheader("Wall 可信度")
    if isinstance(confidence, pd.DataFrame) and not confidence.empty:
        st.plotly_chart(build_confidence_chart(confidence), use_container_width=True)
        st.dataframe(confidence, use_container_width=True)
    else:
        st.warning("未找到 wall_confidence.csv。")

    st.subheader("现价位置分析")
    if isinstance(spot_position, pd.DataFrame) and not spot_position.empty:
        st.dataframe(spot_position, use_container_width=True)
    else:
        st.warning("未找到 spot_position_features.csv。")


def render_comparison(exports: dict[str, object]) -> None:
    """多标的对比。"""
    comparison = exports["comparison_table.csv"]
    st.subheader("多标的对比")
    if not isinstance(comparison, pd.DataFrame) or comparison.empty:
        st.warning("未找到 comparison_table.csv。请先在主系统中一键导出结果。")
        return
    etf = comparison[comparison["market_type"].astype(str).eq("ETF")].copy() if "market_type" in comparison.columns else comparison.copy()
    if etf.empty:
        st.warning("comparison_table.csv 中没有 ETF 数据。")
        return

    left, right = st.columns([1, 1.4])
    with left:
        st.plotly_chart(build_regime_distribution_chart(etf), use_container_width=True)
        if "gamma_regime" in etf.columns:
            counts = (
                etf["gamma_regime"]
                .fillna("Unavailable")
                .replace("", "Unavailable")
                .value_counts()
                .rename_axis("gamma_regime")
                .reset_index(name="count")
            )
            st.dataframe(counts, use_container_width=True, hide_index=True)
    with right:
        st.plotly_chart(build_net_gex_ranking_chart(etf), use_container_width=True)

    st.plotly_chart(build_price_wall_distance_heatmap(etf), use_container_width=True)

    st.markdown("#### 关键价位对比表")
    display_cols = [
        "trade_date", "underlying", "contract_month", "underlying_price",
        "call_wall", "put_wall", "price_wall", "gex_flip",
        "net_gex", "total_abs_gex", "price_wall_distance",
        "gamma_regime", "gex_ratio",
    ]
    st.dataframe(etf[[col for col in display_cols if col in etf.columns]], use_container_width=True, hide_index=True)


def render_support_box(location: str = "main") -> None:
    """Show voluntary support links and QR images if they are configured."""
    st.markdown("#### 支持项目")
    st.caption("结果文件可以免费下载。如果这个面板对你有帮助，可以自愿打赏支持维护；这不是强制付费。")

    active_links = {name: url for name, url in DONATION_LINKS.items() if url}
    existing_qrs = {name: path for name, path in DONATION_QR_FILES.items() if path.exists()}

    if active_links:
        link_cols = st.columns(min(3, len(active_links)))
        for idx, (name, url) in enumerate(active_links.items()):
            with link_cols[idx % len(link_cols)]:
                st.link_button(name, url, use_container_width=True)

    if existing_qrs:
        qr_cols = st.columns(min(2, len(existing_qrs)))
        for idx, (name, path) in enumerate(existing_qrs.items()):
            with qr_cols[idx % len(qr_cols)]:
                st.image(str(path), caption=name, use_container_width=True)

    if not active_links and not existing_qrs:
        st.info("打赏入口尚未配置。可在 assets/ 放入 wechat_reward.png、alipay_reward.png，或在 publish_app.py 填入爱发电 / Buy Me a Coffee 链接。")


def render_feedback() -> None:
    """Embed a public feedback form, or show setup instructions when missing."""
    st.subheader("留言反馈")
    st.caption("欢迎留下问题、建议、数据口径反馈或合作线索。")

    if FEEDBACK_FORM_URL:
        components.iframe(FEEDBACK_FORM_URL, height=760, scrolling=True)
    else:
        st.info("留言表单尚未配置。创建 Google Form、腾讯问卷或飞书表单后，把公开填写链接填入 publish_app.py 的 FEEDBACK_FORM_URL。")

    render_support_box(location="feedback_tab")


def main() -> None:
    """Streamlit 入口。"""
    st.set_page_config(page_title="Option Wall Published Dashboard", layout="wide")
    inject_google_analytics(GA_MEASUREMENT_ID)
    emit_pending_ga_event()
    st.title("Option Wall Published Dashboard")
    st.caption("只读发布版：仅展示 daily_data 中已导出的结果，不上传文件、不读取 Access、不重新计算。")
    st.sidebar.caption(f"GA4 tracking: {GA_MEASUREMENT_ID}")

    data_dir_text = st.sidebar.text_input("daily_data 目录", value=str(DAILY_DATA_DIR))
    data_dir = Path(data_dir_text)
    index = load_index(str(data_dir))
    dates = available_dates(index, data_dir)
    if not dates:
        st.error("未找到可展示的 daily_data 日期。请先在主系统中一键导出结果，并把 daily_data 推送到发布仓库。")
        return

    default_date = dates[-1]
    selected_date = st.sidebar.selectbox("选择发布日期", dates, index=len(dates) - 1, format_func=lambda value: str(value))
    if st.session_state.get("last_tracked_trade_date") != str(selected_date):
        inject_ga_event("select_trade_date", {"trade_date": str(selected_date)})
        st.session_state["last_tracked_trade_date"] = str(selected_date)
    exports = load_exports(data_dir, selected_date)
    report_text = exports.get("market_structure_report.txt", "")

    st.sidebar.success(f"当前展示日期: {selected_date}")
    st.sidebar.caption(f"数据目录: {data_dir}")
    if not index.empty:
        latest_index = index[pd.to_datetime(index["trade_date"], errors="coerce").dt.date.eq(selected_date)].copy()
        if not latest_index.empty:
            st.sidebar.dataframe(latest_index[["file_name", "rows", "saved_at"]].tail(30), use_container_width=True, hide_index=True)

    inject_tab_click_tracking()
    tab_overview, tab_gamma, tab_structure, tab_comparison, tab_feedback, tab_download = st.tabs([
        "今日总览",
        "ETF Gamma Wall",
        "结构分析",
        "多标的对比",
        "留言反馈",
        "下载结果",
    ])
    with tab_overview:
        render_overview(exports, str(report_text or ""))
    with tab_gamma:
        render_etf_gamma(exports)
    with tab_structure:
        render_structure_tabs(exports)
    with tab_comparison:
        render_comparison(exports)
    with tab_feedback:
        render_feedback()
    with tab_download:
        render_support_box(location="download_tab")
        show_downloads(exports, selected_date)
        if not index.empty:
            st.markdown("#### daily_data/index.csv")
            st.dataframe(index, use_container_width=True)


if __name__ == "__main__":
    main()
