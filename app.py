import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="晏駒的 2026 資產決策中心", layout="wide")

st.title("📊 晏駒的資產配置決策中心")

# --- 1. 設定目標配置比例 (2026 佈局規劃) ---
# 你可以隨時在這裡微調你的理想比例
target_config = {
    "BTC/ETH": 0.15, "VEA": 0.15, "TSLA": 0.10, "CVX": 0.05, 
    "ONDS": 0.05, "00830.TW": 0.10, "2362.TW": 0.05, "6748.TW": 0.05,
    "OPTIONS": 0.15, "CASH": 0.15
}

# --- 2. 抓取即時數據 (包含新加入的台股) ---
@st.cache_data(ttl=300)
def get_live_prices():
    tickers = ["VEA", "TSLA", "CVX", "ONDS", "00830.TW", "2362.TW", "6748.TW", "BTC-USD", "TWDUSD=X"]
    df = yf.download(tickers, period="5d", group_by='ticker')
    latest = {}
    for t in tickers:
        series = df[t]['Close'].dropna()
        latest[t] = series.iloc[-1] if not series.empty else 0.0
    return latest

prices = get_live_prices()
usd_twd = 1 / prices["TWDUSD=X"]

# --- 3. 互動式持股調整區 ---
st.subheader("📝 實時持股調整")
st.info("直接在下方表格的『持有數量』欄位輸入新數字，全站數據會同步計算。")

# 初始化數據框架
initial_data = [
    {"項目": "VEA", "類別": "美股ETF", "持有數量": 25.0, "單位": "股"},
    {"項目": "TSLA", "類別": "美股個股", "持有數量": 7.5, "單位": "股"},
    {"項目": "CVX", "類別": "美股個股", "持有數量": 6.0, "單位": "股"},
    {"項目": "ONDS", "類別": "美股個股", "持有數量": 50.0, "單位": "股"},
    {"項目": "00830.TW", "類別": "台股ETF", "持有數量": 873.0, "單位": "股"},
    {"項目": "2362.TW", "類別": "台股個股", "持有數量": 500.0, "單位": "股"},
    {"項目": "6748.TW", "類別": "台股個股", "持有數量": 500.0, "單位": "股"},
    {"項目": "BTC/ETH", "類別": "加密貨幣", "持有數量": 3750.0, "單位": "USD總額"},
    {"項目": "OPTIONS", "類別": "選擇權", "持有數量": 3000.0, "單位": "USD總額"},
    {"項目": "CASH_USD", "類別": "現金", "持有數量": 1730.0, "單位": "USD"},
    {"項目": "CASH_TWD", "類別": "現金", "持有數量": 140000.0, "單位": "TWD"},
]

# 顯示可編輯表格
edited_df = st.data_editor(pd.DataFrame(initial_data), hide_index=True, use_container_width=True)

# --- 4. 計算資產現況 ---
final_assets = []
total_usd = 0

for _, row in edited_df.iterrows():
    name = row["項目"]
    qty = row["持有數量"]
    val_usd = 0
    
    if name in ["BTC/ETH", "OPTIONS", "CASH_USD"]:
        val_usd = qty
    elif name == "CASH_TWD":
        val_usd = qty / usd_twd
    elif ".TW" in name:
        val_usd = (qty * prices[name]) / usd_twd # 台股轉美金
    else:
        val_usd = qty * prices[name] # 美股
    
    total_usd += val_usd
    final_assets.append({"項目": name, "市值_USD": val_usd})

# 整合現金類別以利畫圖
plot_df = pd.DataFrame(final_assets)

# --- 5. 視覺化展示 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.write(f"### 💰 總資產估值: ${total_usd:,.2f} USD")
    st.write(f"約合台幣: NT$ {total_usd * usd_twd:,.0f}")
    
    # 圓餅圖
    fig = px.pie(plot_df, values='市值_USD', names='項目', title="資產分佈比例", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write("### ⚖️ 配置平衡分析")
    rebalance_data = []
    # 這裡將 CASH_USD 和 CASH_TWD 合併計算
    actual_cash = sum(d["市值_USD"] for d in final_assets if "CASH" in d["項目"])
    
    for name, target_pct in target_config.items():
        # 找出該項目的目前總值
        if name == "CASH":
            current_val = actual_cash
        else:
            current_val = sum(d["市值_USD"] for d in final_assets if d["項目"] == name)
            
        current_pct = current_val / total_usd
        diff = (total_usd * target_pct) - current_val
        
        rebalance_data.append({
            "標的": name,
            "目前比例": f"{current_pct*100:.1f}%",
            "目標比例": f"{target_pct*100:.1f}%",
            "建議調整": f"{'+' if diff > 0 else ''}${diff:,.0f}"
        })
    
    st.table(pd.DataFrame(rebalance_data))

st.success("💡 操作流提醒：當你買入新股票時，更新『持有數量』，系統會自動告訴你目前的現金比例是否還在目標範圍內。")
