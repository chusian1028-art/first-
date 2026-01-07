import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="晏駒的 2026 資產決策中心", layout="wide")

st.title("📊 晏駒的動態資產配置工具")
st.write("提示：直接在表格中修改『項目』或『持有數量』，系統將自動重新抓取價格並繪圖。")

# --- 1. 初始數據設定 ---
if 'df' not in st.session_state:
    initial_data = [
        {"項目": "VEA", "類別": "美股", "持有數量": 25.0},
        {"項目": "TSLA", "類別": "美股", "持有數量": 7.5},
        {"項目": "CVX", "類別": "美股", "持有數量": 6.0},
        {"項目": "ONDS", "類別": "美股", "持有數量": 50.0},
        {"項目": "00830.TW", "類別": "台股", "持有數量": 873.0},
        {"項目": "2362.TW", "類別": "台股", "持有數量": 500.0},
        {"項目": "6748.TW", "類別": "台股", "持有數量": 500.0},
        {"項目": "BTC-USD", "類別": "加密貨幣", "持有數量": 0.04}, # 建議改輸入顆數，或維持總額
        {"項目": "OPTIONS", "類別": "其他", "持有數量": 3000.0},
        {"項目": "CASH_USD", "類別": "現金", "持有數量": 1730.0},
        {"項目": "CASH_TWD", "類別": "現金", "持有數量": 140000.0},
    ]
    st.session_state.df = pd.DataFrame(initial_data)

# --- 2. 互動式表格 (允許新增/刪除行) ---
edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic", # 允許你自行增加新標的
    use_container_width=True,
    key="portfolio_editor"
)

# --- 3. 動態抓取價格功能 ---
@st.cache_data(ttl=300)
def fetch_dynamic_prices(ticker_list):
    # 過濾掉非股票標的
    valid_tickers = [t for t in ticker_list if t not in ["OPTIONS", "CASH_USD", "CASH_TWD"]]
    if "TWDUSD=X" not in valid_tickers:
        valid_tickers.append("TWDUSD=X")
    
    try:
        data = yf.download(valid_tickers, period="5d", group_by='ticker', progress=False)
        prices = {}
        for t in valid_tickers:
            series = data[t]['Close'].dropna()
            prices[t] = series.iloc[-1] if not series.empty else 0.0
        return prices
    except:
        return {}

# 取得目前表格中所有的代號
current_tickers = edited_df["項目"].tolist()
prices = fetch_dynamic_prices(current_tickers)
usd_twd = 1 / prices.get("TWDUSD=X", 0.031) # 預設一個匯率以防萬一

# --- 4. 資產計算 ---
final_assets = []
total_usd = 0

for _, row in edited_df.iterrows():
    name = row["項目"]
    qty = row["持有數量"]
    val_usd = 0
    
    if name == "CASH_TWD":
        val_usd = qty / usd_twd
    elif name in ["CASH_USD", "OPTIONS"] or "USD" in name:
        val_usd = qty
    elif name in prices:
        price = prices[name]
        if ".TW" in name:
            val_usd = (qty * price) / usd_twd
        else:
            val_usd = qty * price
    else:
        # 如果是剛輸入但還沒抓到價格的代號
        val_usd = 0
        
    total_usd += val_usd
    final_assets.append({"項目": name, "市值_USD": val_usd})

# --- 5. 圓餅圖與平衡表 ---
plot_df = pd.DataFrame(final_assets)
col1, col2 = st.columns([1, 1])

with col1:
    st.write(f"### 💰 總資產: ${total_usd:,.2f} (USD)")
    fig = px.pie(plot_df, values='市值_USD', names='項目', title="當前配置比例", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write("### ⚖️ 配置狀態")
    # 這裡顯示目前各項目的實際佔比，方便你跟 2026 目標對照
    plot_df["目前比例"] = (plot_df["市值_USD"] / total_usd * 100).map("{:.1f}%".format)
    st.dataframe(plot_df[["項目", "市值_USD", "目前比例"]], use_container_width=True)

st.info(f"💡 當前匯率參考：1 USD = {usd_twd:.2f} TWD。")
