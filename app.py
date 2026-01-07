import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="晏駒的 2026 資產配置", layout="wide")

st.title("📊 晏駒的資產配置決策中心")
st.write("同步追蹤股市、加密貨幣與選擇權權利金")

# --- 1. 設定目標配置比例 (根據 2026 佈局建議) ---
# 你可以在這裡調整你理想中的比例
targets = {
    "BTC/ETH": 0.15,   # 加密貨幣佔 15%
    "VEA": 0.20,       # 已開發市場 ETF
    "TSLA": 0.10,      # 特斯拉
    "CVX": 0.05,       # 雪佛龍 (能源防守)
    "ONDS": 0.05,      # 成長型小盤股
    "OPTIONS": 0.20,   # 選擇權操作資金
    "CASH": 0.25       # 現金儲備 (包含 TWD)
}

# --- 2. 抓取即時數據 (股市、加密貨幣、匯率) ---
@st.cache_data(ttl=300) # 每 5 分鐘更新一次
def get_all_data():
    tickers = ["VEA", "TSLA", "CVX", "ONDS", "BTC-USD", "ETH-USD", "TWDUSD=X"]
    data = yf.download(tickers, period="1d")['Close'].iloc[-1]
    return data

try:
    prices = get_all_data()
    usd_twd = 1 / prices["TWDUSD=X"] # 取得 1 美金兌換台幣匯率
except:
    st.error("無法抓取即時數據，請稍後再試。")
    st.stop()

# --- 3. 輸入目前持倉 ---
st.sidebar.header("📝 目前持倉數據")
st.sidebar.subheader("加密貨幣")
# 因為你提供的是總額，這裡讓你輸入目前 BTC+ETH 的總價值
crypto_val = st.sidebar.number_input("BTC + ETH 總市值 (USD)", value=3750.0)

st.sidebar.subheader("美股持倉 (股數)")
shares_vea = st.sidebar.number_input("VEA 股數", value=25.0)
shares_onds = st.sidebar.number_input("ONDS 股數", value=50.0)
shares_cvx = st.sidebar.number_input("CVX 股數", value=6.0)
shares_tsla = st.sidebar.number_input("TSLA 股數", value=7.5)

st.sidebar.subheader("其他資產")
options_val = st.sidebar.number_input("選擇權部位價值 (USD)", value=3000.0)
cash_usd = st.sidebar.number_input("美金現金", value=1730.0)
cash_twd = st.sidebar.number_input("台幣現金", value=140000.0)

# --- 4. 資產計算邏輯 ---
# 統一換算為 USD
cash_twd_in_usd = cash_twd / usd_twd
total_cash_usd = cash_usd + cash_twd_in_usd

assets = [
    {"名稱": "BTC/ETH", "市值(USD)": crypto_val, "類別": "加密貨幣"},
    {"名稱": "VEA", "市值(USD)": shares_vea * prices["VEA"], "類別": "ETF"},
    {"名稱": "TSLA", "市值(USD)": shares_tsla * prices["TSLA"], "類別": "個股"},
    {"名稱": "CVX", "市值(USD)": shares_cvx * prices["CVX"], "類別": "個股"},
    {"名稱": "ONDS", "市值(USD)": shares_onds * prices["ONDS"], "類別": "個股"},
    {"名稱": "OPTIONS", "市值(USD)": options_val, "類別": "選擇權"},
    {"名稱": "CASH", "市值(USD)": total_cash_usd, "類別": "現金"}
]

total_portfolio_value = sum(item["市值(USD)"] for item in assets)

# --- 5. 計算調整建議 ---
results = []
for item in assets:
    name = item["名稱"]
    current_val = item["市值(USD)"]
    current_pct = current_val / total_portfolio_value
    target_pct = targets[name]
    target_val = total_portfolio_value * target_pct
    diff = target_val - current_val
    
    results.append({
        "項目": name,
        "目前市值": f"${current_val:,.2f}",
        "目前比例": f"{current_pct*100:.1f}%",
        "目標比例": f"{target_pct*100:.1f}%",
        "需調整金額": f"{'+' if diff > 0 else ''}${diff:,.2f}",
        "狀態": "✅ 達標" if abs(current_pct - target_pct) < 0.02 else ("🔼 補倉" if diff > 0 else "🔽 減碼")
    })

# --- 6. 顯示結果介面 ---
col1, col2, col3 = st.columns(3)
col1.metric("總資產 (USD)", f"${total_portfolio_value:,.2f}")
col2.metric("台幣匯率", f"{usd_twd:.2f}")
col3.metric("比特幣價格", f"${prices['BTC-USD']:,.0f}")

st.write("### ⚖️ 配置平衡表")
df = pd.DataFrame(results)
st.table(df)

st.success(f"💡 貼心提醒：你目前的台幣 14 萬約等於 {cash_twd_in_usd:,.2f} 美金。")
st.info("目前的流：當『狀態』顯示補倉時，優先使用現金買入；當顯示減碼時，可以考慮賣出部分或針對該標的操作 Covered Call 賺取權利金。")
