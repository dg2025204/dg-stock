import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(
    page_title="AI 주식 분석 대시보드",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI 관련 주식 분석 대시보드")
st.markdown("AI 테마로 분류되는 종목들을 데이터로 비교 분석해보는 학습용 도구입니다.")
st.divider()

# AI 관련 종목 (카테고리별 분류)
AI_STOCKS = {
    # --- 미국: AI 반도체 ---
    "NVIDIA (AI반도체)": "NVDA",
    "AMD (AI반도체)": "AMD",
    "Broadcom (AI반도체)": "AVGO",
    "TSMC (파운드리)": "TSM",
    # --- 미국: 빅테크/AI 플랫폼 ---
    "Microsoft (AI플랫폼)": "MSFT",
    "Google (AI플랫폼)": "GOOGL",
    "Meta (AI플랫폼)": "META",
    "Amazon (클라우드AI)": "AMZN",
    # --- 미국: AI 소프트웨어/서버 ---
    "Palantir (AI SW)": "PLTR",
    "Super Micro (AI서버)": "SMCI",
    # --- 한국: AI 반도체/메모리 ---
    "삼성전자 (메모리)": "005930.KS",
    "SK하이닉스 (HBM)": "000660.KS",
}

# 카테고리 설명
st.info("""
**📌 AI 테마 분류**
- 🔧 **AI 반도체**: NVIDIA, AMD, Broadcom, TSMC
- 💻 **AI 플랫폼/빅테크**: Microsoft, Google, Meta, Amazon
- 📊 **AI 소프트웨어/서버**: Palantir, Super Micro
- 🇰🇷 **국내 메모리/HBM**: 삼성전자, SK하이닉스
""")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

selected_names = st.sidebar.multiselect(
    "비교할 AI 종목을 선택하세요",
    options=list(AI_STOCKS.keys()),
    default=["NVIDIA (AI반도체)", "Microsoft (AI플랫폼)", "SK하이닉스 (HBM)"]
)

period_option = st.sidebar.selectbox(
    "조회 기간",
    ["1개월", "3개월", "6개월", "1년", "2년", "5년"],
    index=3
)

period_map = {
    "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
    "1년": "1y", "2년": "2y", "5년": "5y",
}
period = period_map[period_option]


# 데이터 가져오는 함수 (캐싱)
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        return df
    except Exception:
        return pd.DataFrame()


# 메인 로직
if not selected_names:
    st.warning("⚠️ 사이드바에서 비교할 AI 종목을 1개 이상 선택해주세요!")
else:
    data_dict = {}
    for name in selected_names:
        ticker = AI_STOCKS[name]
        df = load_data(ticker, period)
        if not df.empty:
            data_dict[name] = df

    if not data_dict:
        st.error("❌ 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
    else:
        # ===== 1. 누적 수익률 비교 =====
        st.subheader("📊 AI 종목 누적 수익률 비교 (%)")

        fig_return = go.Figure()
        for name, df in data_dict.items():
            normalized = (df["Close"] / df["Close"].iloc[0] - 1) * 100
            fig_return.add_trace(go.Scatter(
                x=df.index, y=normalized,
                mode="lines", name=name, line=dict(width=2)
            ))

        fig_return.update_layout(
            xaxis_title="날짜", yaxis_title="누적 수익률 (%)",
            hovermode="x unified", height=500, template="plotly_white"
        )
        st.plotly_chart(fig_return, use_container_width=True)

        st.divider()

        # ===== 2. 수익률 요약 테이블 =====
        st.subheader("📋 수익률 요약")

        summary_data = []
        for name, df in data_dict.items():
            start_price = df["Close"].iloc[0]
            end_price = df["Close"].iloc[-1]
            total_return = (end_price / start_price - 1) * 100
            # 변동성 (일간 수익률 표준편차)
            daily_returns = df["Close"].pct_change().dropna()
            volatility = daily_returns.std() * 100
            summary_data.append({
                "종목": name,
                "시작가": f"{start_price:,.2f}",
                "현재가": f"{end_price:,.2f}",
                "수익률(%)": f"{total_return:+.2f}%",
                "변동성(%)": f"{volatility:.2f}%"
            })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.caption("💡 변동성이 클수록 가격 등락이 심하다는 의미예요 (위험도 지표).")

        st.divider()

        # ===== 3. 수익률 막대그래프 =====
        st.subheader("🏆 기간 내 수익률 순위")

        return_data = []
        for name, df in data_dict.items():
            total_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
            return_data.append({"종목": name, "수익률": total_return})

        return_df = pd.DataFrame(return_data).sort_values("수익률", ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=return_df["수익률"],
            y=return_df["종목"],
            orientation="h",
            marker_color=["crimson" if v < 0 else "seagreen" for v in return_df["수익률"]],
            text=[f"{v:+.1f}%" for v in return_df["수익률"]],
            textposition="outside"
        ))
        fig_bar.update_layout(
            xaxis_title="수익률 (%)", height=400, template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # ===== 4. 개별 종목 캔들 차트 =====
        st.subheader("🕯️ 개별 종목 상세 차트")

        chart_name = st.selectbox("차트를 볼 종목 선택", options=list(data_dict.keys()))
        df = data_dict[chart_name]

        # 20일 이동평균선 계산
        df["MA20"] = df["Close"].rolling(20).mean()

        fig_candle = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=[0.7, 0.3],
            subplot_titles=("가격 + 20일 이동평균선", "거래량")
        )

        fig_candle.add_trace(
            go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"], name="가격"
            ), row=1, col=1
        )
        fig_candle.add_trace(
            go.Scatter(
                x=df.index, y=df["MA20"],
                line=dict(color="orange", width=1.5), name="20일 이평선"
            ), row=1, col=1
        )
        fig_candle.add_trace(
            go.Bar(x=df.index, y=df["Volume"], name="거래량",
                   marker_color="lightblue"), row=2, col=1
        )

        fig_candle.update_layout(
            height=600, template="plotly_white",
            xaxis_rangeslider_visible=False, showlegend=True
        )
        st.plotly_chart(fig_candle, use_container_width=True)

st.divider()
st.caption("⚠️ 본 자료는 학습용이며, 투자 권유나 종목 추천이 아닙니다. 데이터 출처: Yahoo Finance")
