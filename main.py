import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="주식 분석 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 한국 & 미국 주식 분석 대시보드")
st.markdown("yfinance와 Plotly로 만든 주식 수익률 비교 웹앱입니다.")
st.divider()

# 주요 종목 딕셔너리 (이름: 티커)
KR_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "기아": "000270.KS",
    "POSCO홀딩스": "005490.KS",
}

US_STOCKS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Meta": "META",
    "Netflix": "NFLX",
}

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

market = st.sidebar.radio("시장 선택", ["한국 🇰🇷", "미국 🇺🇸"])

if market == "한국 🇰🇷":
    stock_dict = KR_STOCKS
else:
    stock_dict = US_STOCKS

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(stock_dict.keys()),
    default=list(stock_dict.keys())[:3]
)

# 기간 선택
period_option = st.sidebar.selectbox(
    "조회 기간",
    ["1개월", "3개월", "6개월", "1년", "2년", "5년"],
    index=3
)

period_map = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}
period = period_map[period_option]


# 데이터 가져오는 함수 (캐싱으로 속도 향상)
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        return df
    except Exception as e:
        return pd.DataFrame()


# 메인 로직
if not selected_names:
    st.warning("⚠️ 사이드바에서 비교할 종목을 1개 이상 선택해주세요!")
else:
    # 데이터 수집
    data_dict = {}
    for name in selected_names:
        ticker = stock_dict[name]
        df = load_data(ticker, period)
        if not df.empty:
            data_dict[name] = df

    if not data_dict:
        st.error("❌ 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
    else:
        # ===== 1. 수익률 비교 차트 =====
        st.subheader("📊 누적 수익률 비교 (%)")

        fig_return = go.Figure()

        for name, df in data_dict.items():
            # 시작일 대비 수익률 계산
            normalized = (df["Close"] / df["Close"].iloc[0] - 1) * 100
            fig_return.add_trace(go.Scatter(
                x=df.index,
                y=normalized,
                mode="lines",
                name=name,
                line=dict(width=2)
            ))

        fig_return.update_layout(
            xaxis_title="날짜",
            yaxis_title="누적 수익률 (%)",
            hovermode="x unified",
            height=500,
            template="plotly_white"
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
            summary_data.append({
                "종목": name,
                "시작가": f"{start_price:,.2f}",
                "현재가": f"{end_price:,.2f}",
                "수익률(%)": f"{total_return:+.2f}%"
            })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.divider()

        # ===== 3. 개별 종목 캔들 차트 =====
        st.subheader("🕯️ 개별 종목 가격 차트")

        chart_name = st.selectbox(
            "차트를 볼 종목 선택",
            options=list(data_dict.keys())
        )

        df = data_dict[chart_name]

        fig_candle = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=("가격 (캔들차트)", "거래량")
        )

        # 캔들차트
        fig_candle.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="가격"
            ),
            row=1, col=1
        )

        # 거래량 막대
        fig_candle.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="거래량",
                marker_color="lightblue"
            ),
            row=2, col=1
        )

        fig_candle.update_layout(
            height=600,
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        st.plotly_chart(fig_candle, use_container_width=True)

st.divider()
st.caption("⚠️ 본 자료는 학습용이며, 투자 권유가 아닙니다. 데이터 출처: Yahoo Finance")
