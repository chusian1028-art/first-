import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="晏駒的資產決策中心", layout="wide")

st.title("📊 晏駒的動態資產配置中心")
st.info("💡 提示：若自動抓取不到價格（如 6748），請直接在『手動單價』欄位輸入價格，系統會優先採用該值。")

# --- 1. 初始數據設定 ---
if 'df' not in st.session_state:
    initial_data = [
        {"項目": "VEA", "類型": "美股", "持有數量": 25.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "TSLA", "類型": "美股", "持有數量": 7.5, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "CVX", "類型": "美股", "持有數量": 6.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "ONDS", "類型": "美股", "持有數量": 50.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "00830.TW", "類型": "台股", "持有數量": 873.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "2362.TW", "類型": "台股", "持有數量": 500.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "6748.TWO", "類型": "台股", "持有數量": 500.0, "單位": "股 (Shares)", "手動單價": 0.0},
        {"項目": "BTC-USD", "類型": "加密貨幣", "持有數量": 3750.0, "單位": "金額 (USD)", "手動單價": 0.0},
        {"項目": "OPTIONS", "類型": "選擇權", "持有數量": 3000.0, "單位": "金額 (USD)", "手動單價": 0.0},
        {"項目": "CASH_USD", "類型": "現金", "持有數量": 1730.0, "單位": "金額 (USD)", "手動單價": 0.0},
        {"項目": "CASH_TWD", "類型": "現金", "持有數量": 140000.0, "單位": "金額 (TWD)", "手動單價": 0.0},
    ]
    st.session_state.df = pd.DataFrame(initial_data)

# --- 2. 互動式表格 (新增手動單價欄位) ---
edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "手動單價": st.column_config.NumberColumn(help="若填寫此欄，將忽略自動抓取的市場價。")
    },
    key="portfolio_editor_v3"
)

# --- 3. 抓取數據 (包含匯率與價格) ---
@st.cache_data(ttl=300)
def fetch_all_prices(ticker_list):
    to_fetch = [t for t in ticker_list if t not in ["OPTIONS", "CASH_USD", "CASH_TWD"]]
    if "TWDUSD=X" not in to_fetch: to_fetch.append("TWDUSD=X")
    
    try:
        data = yf.download(to_fetch, period="5d", group_by='ticker', progress=False)
        prices = {}
        for t in to_fetch:
            try:
                series = data[t]['Close'].dropna()
                prices[t] = series.iloc[-1] if not series.empty else 0.0
            except:
                prices[t] = 0.0
        return prices
    except:
        return {}

current_tickers = edited_df["項目"].tolist()
prices = fetch_all_prices(current_tickers)
usd_twd = 1 / prices.get("TWDUSD=X", 0.031)

# --- 4. 核心計算邏輯 (優先判定手動單價) ---
final_list = []
total_usd = 0

for _, row in edited_df.iterrows():
    name = row["項目"]
    qty = row["持有數量"]
    unit = row["單位"]
    manual_p = row["手動單價"]
    
    # 決定使用的價格
    if manual_p > 0:
        current_price = manual_p
    elif name in prices:
        current_price = prices[name]
    else:
        current_price = 1.0 if "金額" in unit else 0.0
    
    val_usd = 0
    if "TWD" in unit or name == "CASH_TWD":
        val_usd = qty / usd_twd if manual_p == 0 else (qty * current_price) / usd_twd
        if "金額" in unit: current_price = 1.0 # 台幣現金單價設為 1
    elif "金額 (USD)" in unit:
        val_usd = qty
        current_price = 1.0
    elif ".TW" in name or ".TWO" in name:
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
    st.dataframe(
        display_df,
        column_config={
            "市值 (USD)": st.column_config.NumberColumn(format="$%.2f"),
            "市值 (TWD)": st.column_config.NumberColumn(format="NT$ %d"),
        },
        use_container_width=True, hide_index=True
    )

with c2:
    st.write("### 🎡 資產分佈圖")
    fig = px.pie(display_df, values='市值 (USD)', names='項目', hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.T10)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.success("✅ 手動價格功能已啟動。若看到價格為 0，請直接填入『手動單價』即可排除。")
