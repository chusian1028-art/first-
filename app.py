import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. 頁面基本設定
st.set_page_config(page_title="晏駒的資產決策中心", layout="wide")

# 2. 初始化資產數據
if 'df' not in st.session_state:
    initial_data = [
        {"項目": "VEA", "持有數量": 25.0, "單位": "股", "手動單價": 0.0},
        {"項目": "TSLA", "持有數量": 7.5, "單位": "股", "手動單價": 0.0},
        {"項目": "CVX", "持有數量": 6.0, "單位": "股", "手動單價": 0.0},
        {"項目": "ONDS", "持有數量": 50.0, "單位": "股", "手動單價": 0.0},
        {"項目": "00830.TW", "持有數量": 873.0, "單位": "股", "手動單價": 0.0},
        {"項目": "2362.TW", "持有數量": 500.0, "單位": "股", "手動單價": 0.0},
        {"項目": "6748.TWO", "持有數量": 500.0, "單位": "股", "手動單價": 0.0},
        {"項目": "景順全球科技基金", "持有數量": 453.52, "單位": "單位", "手動單價": 73.58},
        {"項目": "BTC-USD", "持有數量": 3800.0, "單位": "USD總額", "手動單價": 0.0},
        {"項目": "OPTIONS", "持有數量": 3000.0, "單位": "USD總額", "手動單價": 0.0},
        {"項目": "CASH_USD", "持有數量": 1730.0, "單位": "USD", "手動單價": 0.0},
        {"項目": "CASH_TWD", "持有數量": 140000.0, "單位": "TWD", "手動單價": 0.0},
    ]
    st.session_state.df = pd.DataFrame(initial_data)

# 3. 側邊欄控制
st.sidebar.header("🛠️ 全域參數調整")
loan_balance = st.sidebar.number_input("信貸剩餘金額 (TWD)", value=1070103.0)
target_lev = st.sidebar.slider("目標目標槓桿", 1.0, 5.0, 1.25, 0.05)

# 4. 預留頂部顯示空間
header_placeholder = st.empty()
viz_placeholder = st.empty()

# 5. [可調整區] 下方編輯器
st.divider()
st.subheader("⌨️ 可調整：資產項目編輯器")
current_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
st.session_state.df = current_df

# 6. 抓取即時價格
@st.cache_data(ttl=300)
def fetch_prices(tickers):
    to_fetch = [t for t in tickers if t not in ["OPTIONS", "CASH_USD", "CASH_TWD", "景順全球科技基金"]]
    to_fetch += ["TWDUSD=X"]
    try:
        data = yf.download(to_fetch, period="5d", group_by='ticker', progress=False)
        prices = {}
        for t in to_fetch:
            try:
                s = data[t]['Close'].dropna()
                prices[t] = s.iloc[-1] if not s.empty else 0.0
            except: prices[t] = 0.0
        return prices
    except: return {}

prices_dict = fetch_prices(current_df["項目"].tolist())
usd_twd = 1 / prices_dict.get("TWDUSD=X", 0.031)

# 7. 核心計算邏輯 (確保現金與基金計算正確)
final_list = []
total_usd = 0.0

for _, row in current_df.iterrows():
    name, qty, unit, manual = row["項目"], row["持有數量"], row["單位"], row["手動單價"]
    val_usd = 0.0
    p_display = 0.0
    
    if name == "CASH_TWD":
        p_display = 1.0
        val_usd = qty / usd_twd
    elif "USD" in unit or "USD總額" in unit:
        p_display = manual if manual > 0 else 1.0
        val_usd = qty 
    elif name == "景順全球科技基金":
        p_display = manual
        val_usd = (qty * manual) / usd_twd
    else:
        p_display = manual if manual > 0 else prices_dict.get(name, 0.0)
        if ".TW" in name or ".TWO" in name:
            val_usd = (qty * p_display) / usd_twd
        else:
            val_usd = qty * p_display
            
    total_usd += val_usd
    final_list.append({
        "項目": name, "持有數量": qty, "市值 (USD)": round(val_usd, 2), 
        "市值 (TWD)": round(val_usd * usd_twd, 0), "佔比": 0
    })

total_twd = total_usd * usd_twd
net_twd = total_twd - loan_balance
display_df = pd.DataFrame(final_list)

# 8. [可視化區] 數據呈現
with header_placeholder.container():
    st.title("⚖️ 晏駒的資產槓桿與配置中心")
    m1, m2, m3 = st.columns(3)
    m1.metric("台幣總資產 (TWD)", f"NT$ {total_twd:,.0f}")
    m2.metric("美金總資產 (USD)", f"$ {total_usd:,.2f}")
    m3.metric("目前匯率 (USD/TWD)", f"{usd_twd:.2f}")

    if net_twd > 0:
        curr_lev = total_twd / net_twd
        st.write(f"ℹ️ **目前槓桿:** {curr_lev:.2f}x | **淨資產:** NT$ {net_twd:,.0f} | **負債:** NT$ {loan_balance:,.0f}")
    else:
        st.error(f"⚠️ **負淨值狀態**: 目前總資產尚未覆蓋國泰信貸。缺口：NT$ {abs(net_twd):,.0f}")

with viz_placeholder.container():
    c1, c2 = st.columns([1.2, 0.8])
    with c1:
        st.subheader("🔍 詳細資產清單")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    with c2:
        st.subheader("🎡 資產分佈 (含標籤)")
        # 更新圓餅圖設定：顯示標籤與百分比
        fig = px.pie(display_df, values='市值 (USD)', names='項目', hole=0.4,
                     hover_data=['市值 (TWD)'],
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        # 關鍵設定：將文字資訊放在圓餅圖內部
        fig.update_traces(textinfo='label+percent', textposition='inside')
        
        fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
