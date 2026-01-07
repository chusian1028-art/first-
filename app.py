import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="晏駒的 2026 資產決策中心", layout="wide")

st.title("📊 晏駒的動態資產配置中心")
st.write("提示：在『持有數量』欄位輸入數值（股數或金額），系統會自動計算各幣值總額。")

# --- 1. 初始數據設定 (包含詳細單位說明) ---
if 'df' not in st.session_state:
    initial_data = [
        {"項目": "VEA", "類型": "美股", "持有數量": 25.0, "單位": "股 (Shares)"},
        {"項目": "TSLA", "類型": "美股", "持有數量": 7.5, "單位": "股 (Shares)"},
        {"項目": "CVX", "類型": "美股", "持有數量": 6.0, "單位": "股 (Shares)"},
        {"項目": "ONDS", "類型": "美股", "持有數量": 50.0, "單位": "股 (Shares)"},
        {"項目": "00830.TW", "類型": "台股", "持有數量": 873.0, "單位": "股 (Shares)"},
        {"項目": "2362.TW", "類型": "台股", "持有數量": 500.0, "單位": "股 (Shares)"},
        {"項目": "6748.TW", "類型": "台股", "持有數量": 500.0, "單位": "股 (Shares)"},
        {"項目": "BTC-USD", "類型": "加密貨幣", "持有數量": 3750.0, "單位": "金額 (USD)"},
        {"項目": "OPTIONS", "類型": "選擇權", "持有數量": 3000.0, "單位": "金額 (USD)"},
        {"項目": "CASH_USD", "類型": "現金", "持有數量": 1730.0, "單位": "金額 (USD)"},
        {"項目": "CASH_TWD", "類型": "現金", "持有數量": 140000.0, "單位": "金額 (TWD)"},
    ]
    st.session_state.df = pd.DataFrame(initial_data)

# --- 2. 互動式表格 ---
st.subheader("📝 資產項目管理")
edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic",
    use_container_width=True,
    key="portfolio_editor_v2"
)

# --- 3. 抓取數據 (包含匯率與價格) ---
@st.cache_data(ttl=300)
def fetch_all_prices(ticker_list):
    # 需要抓取價格的標的
    to_fetch = [t for t in ticker_list if t not in ["OPTIONS", "CASH_USD", "CASH_TWD", "BTC/ETH"]]
    if "TWDUSD=X" not in to_fetch: to_fetch.append("TWDUSD=X")
    if "BTC-USD" not in to_fetch: to_fetch.append("BTC-USD")
    
    try:
        data = yf.download(to_fetch, period="5d", group_by='ticker', progress=False)
        prices = {}
        for t in to_fetch:
            series = data[t]['Close'].dropna()
            prices[t] = series.iloc[-1] if not series.empty else 0.0
        return prices
    except:
        return {}

current_tickers = edited_df["項目"].tolist()
prices = fetch_all_prices(current_tickers)
usd_twd = 1 / prices.get("TWDUSD=X", 0.031)

# --- 4. 核心計算邏輯 ---
final_list = []
total_usd = 0

for _, row in edited_df.iterrows():
    name = row["項目"]
    qty = row["持有數量"]
    unit = row["單位"]
    
    current_price = 0
    val_usd = 0
    
    # 分類處理計算
    if "TWD" in unit or name == "CASH_TWD":
        val_usd = qty / usd_twd
        current_price = 1 / usd_twd
    elif "金額 (USD)" in unit:
        val_usd = qty
        current_price = 1.0
    elif name in prices:
        current_price = prices[name]
        if ".TW" in name:
            val_usd = (qty * current_price) / usd_twd
        else:
            val_usd = qty * current_price
    
    total_usd += val_usd
    final_list.append({
        "項目": name,
        "類型": row["類型"],
        "單位": unit,
        "持有數量": qty,
        "目前單價": round(current_price, 2),
        "市值 (USD)": round(val_usd, 2),
        "市值 (TWD)": round(val_usd * usd_twd, 0)
    })

total_twd = total_usd * usd_twd
display_df = pd.DataFrame(final_list)

# --- 5. 儀表板顯示 ---
st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("台幣總資產 (TWD)", f"NT$ {total_twd:,.0f}")
m2.metric("美金總資產 (USD)", f"$ {total_usd:,.2f}")
m3.metric("目前匯率 (USD/TWD)", f"{usd_twd:.2f}")

c1, c2 = st.columns([1.2, 0.8])

with c1:
    st.write("### 🔍 詳細資產清單")
    # 格式化顯示表格
    st.dataframe(
        display_df,
        column_config={
            "市值 (USD)": st.column_config.NumberColumn(format="$%.2f"),
            "市值 (TWD)": st.column_config.NumberColumn(format="NT$ %d"),
        },
        use_container_width=True,
        hide_index=True
    )

with c2:
    st.write("### 🎡 資產分佈圖")
    fig = px.pie(display_df, values='市值 (USD)', names='項目', hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=False) # 隱藏側邊圖例讓圓餅圖大一點
    st.plotly_chart(fig, use_container_width=True)

# --- 6. 心理建設與決策流 ---
st.divider()
st.info(f"""
**🎯 2026 目標決策流回顧：**
* **消除壓力**：看到總資產的成長（無論是台幣還是美金），能幫你緩解創作時的「輸出焦慮」。
* **維持頻率**：如果某個項目的比例突然變大，代表該賣出一點或進行 Covered Call 操作來換取現金，維持你的「流」。
* **穩步成長**：這個 App 是你自媒體事業的後盾，數字會告訴你現在走在正確的軌道上。
""")
