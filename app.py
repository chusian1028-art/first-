import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 網頁標題與設定
st.set_page_config(page_title="晏駒的 2026 決策儀表板", layout="wide")
st.title("💰 2026 投資決策系統")

# 側邊欄：名詞解釋
with st.sidebar:
    st.header("📚 投資必學術語")
    st.info("**EPS (每股盈餘)**: 企業為每一股賺到的錢。數字越高代表賺錢能力越強。")
    st.info("**PE (本益比)**: 回本年數。代表投資人願意花多少倍價格買入獲利潛力。")
    st.info("**便宜價 (Burry防線)**: 參考黎志建 (Vic) 策略，預估 EPS × 保守 PE × 0.8 安全邊際。")

# 第一行：輸入框
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("輸入股票代碼 (美股如 NVDA，台股如 2330.TW)", "NVDA")
with col2:
    manual_eps = st.number_input("自訂 2026 預估 EPS (若為 0 則使用法人預估)", value=0.0)

if st.button("開始專業估值"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 抓取數據
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        trailing_eps = info.get('trailingEps', 0)
        forward_eps = info.get('forwardEps')
        final_eps = manual_eps if manual_eps > 0 else (forward_eps if forward_eps else trailing_eps)
        curr_pe = info.get('trailingPE') or 20
        
        # 計算估值
        low_pe, mid_pe, high_pe = curr_pe * 0.7, curr_pe, curr_pe * 1.3
        safety_margin = 0.8
        
        cheap = final_eps * low_pe * safety_margin
        fair = final_eps * mid_pe
        expensive = final_eps * high_pe
        
        # 顯示結果
        st.subheader(f"📊 {info.get('longName', ticker)} 分析報告")
        st.metric("目前股價", f"${curr_price:.2f}")
        
        df_results = pd.DataFrame({
            "位階名稱": ["🔵 便宜價 (8折)", "🟢 合理價", "🔴 昂貴價"],
            "估算價格": [f"${cheap:.2f}", f"${fair:.2f}", f"${expensive:.2f}"],
            "操作建議": ["分批買進", "續抱觀望", "分批減碼"]
        })
        st.table(df_results)
        
        # 診斷提醒
        if curr_price <= cheap:
            st.success(f"🔥 診斷：股價 ${curr_price:.2f} 已低於安全邊際，具備高盈虧比！")
        elif curr_price >= expensive:
            st.warning("⚠️ 診斷：市場極度瘋狂，注意回檔風險。")
        else:
            st.info("⚖️ 診斷：目前處於合理估值區間。")
            
    except Exception as e:
        st.error(f"數據抓取失敗，請確認代碼格式是否正確。錯誤訊息: {e}")