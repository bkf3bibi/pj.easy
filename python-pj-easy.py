import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time

# 1. 基礎設定：解決圖表中文顯示問題
# 優先順序：微軟正黑體 -> Mac黑體 -> Linux黑體 -> 系統預設黑體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'Heiti TC', 'SimHei', 'sans-serif'] 
plt.rcParams['axes.unicode_minus'] = False 

st.set_page_config(page_title="簡易餐飲經營模擬", layout="wide")
st.title("🍳 餐廳經營診斷模擬器")

# --- 側邊欄：讓使用者輸入參數 ---
with st.sidebar:
    st.header("🏪 營運設定")
    shop_hours = st.slider("預計營業時數", 1, 12, 8)
    kitchen_staff = st.number_input("廚房人力 (名)", 1, 5, 2)
    
    st.header("💰 成本設定")
    avg_price = st.number_input("平均客單價", 100, 500, 200)
    food_rate = st.slider("食材成本佔比 (%)", 20, 50, 35)
    platform_fee = st.slider("外送平台抽成 (%)", 20, 40, 32)

# --- 模擬核心邏輯 ---
def customer_process(env, name, kitchen, stats):
    arrival_time = env.now
    with kitchen.request() as request:
        yield request
        cooking_time = random.randint(3, 7)
        yield env.timeout(cooking_time)
        
        wait_time = env.now - arrival_time
        stats.append({
            "訂單編號": name,
            "等待分鐘": wait_time,
            "類型": random.choice(["現場", "外送"])
        })

def setup_shop(env, kitchen, stats):
    customer_id = 0
    while True:
        yield env.timeout(random.randint(3, 8))
        customer_id += 1
        env.process(customer_process(env, f"客{customer_id}", kitchen, stats))

# --- 執行按鈕 ---
if st.button("🚀 開始模擬一天營運"):
    results = []
    env = simpy.Environment()
    kitchen_res = simpy.Resource(env, capacity=kitchen_staff)
    
    env.process(setup_shop(env, kitchen_res, results))
    env.run(until=shop_hours * 60) 
    
    df = pd.DataFrame(results)
    
    if not df.empty:
        total_orders = len(df)
        revenue = total_orders * avg_price
        delivery_count = len(df[df["類型"] == "外送"])
        delivery_cost = (delivery_count * avg_price) * (platform_fee / 100)
        food_cost = revenue * (food_rate / 100)
        profit = revenue - food_cost - delivery_cost
        
        st.header("📊 今日營運成績單")
        c1, c2, c3 = st.columns(3)
        c1.metric("總訂單數", f"{total_orders} 單")
        c2.metric("預估營收", f"${revenue:,.0f}")
        c3.metric("預估淨利", f"${profit:,.0f}")

        st.subheader("📈 營運分析圖表")
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig, ax = plt.subplots()
            ax.hist(df["等待分鐘"], bins=10, color='skyblue', edgecolor='black')
            ax.set_title("客戶等待時間分布")
            ax.set_xlabel("分鐘")
            ax.set_ylabel("人數")
            st.pyplot(fig)
            
        with col_right:
            fig2, ax2 = plt.subplots()
            labels = ['食材成本', '外送抽成', '剩餘利潤']
            sizes = [food_cost, delivery_cost, max(0, profit)]
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
            ax2.set_title("今日支出結構")
            st.pyplot(fig2)

        st.divider()
        st.header("💡 創業中老闆經營實戰建議")
        
        avg_wait = df["等待分鐘"].mean()
        delivery_ratio = (delivery_count / total_orders * 100) if total_orders > 0 else 0
        
        c_diag1, c_diag2, c_diag3 = st.columns(3)
        
        with c_diag1:
            st.write("### 🚀 效率與人力分析")
            if avg_wait > 8:
                st.error("**產能亮紅燈！**")
                st.write(f"• 平均等待時間已達 {avg_wait:.1f} 分鐘。")
                st.write("👉 **老闆注意：** 客人耐心極限通常是 15 分鐘。目前的廚房人力在尖峰期會造成嚴重負評，建議考慮增加 1 名 PT 人力。")
            else:
                st.success("**產能效率優良**")
                st.write(f"• 目前平均等待僅 {avg_wait:.1f} 分鐘。")

        with c_diag2:
            st.write("### 🛵 通路獲利分析")
            if delivery_ratio > 40:
                st.warning("**過度依賴平台**")
                st.write(f"• 外送佔比高達 {delivery_ratio:.1f}%。")
                st.write("👉 **老闆注意：** 你正在幫平台打工！建議推行店取優惠，將外送客轉為內用客。")
            else:
                st.success("**通路結構健康**")
                st.write(f"• 外送佔比僅 {delivery_ratio:.1f}%。")

        with c_diag3:
            st.write("### 💰 財務生存指南")
            margin_rate = (profit / revenue * 100) if revenue > 0 else 0
            if margin_rate < 15:
                st.error("**獲利空間過薄**")
                st.write(f"• 今日預估利潤率僅 {margin_rate:.1f}%。")
                # --- 修正後的字串，確保引號完全閉合且不換行 ---
                st.write("👉 **老闆注意：** 扣除租金與水電後你可能在虧錢，請立即檢查食材浪費或客單價問題。")
            else:
                st.success("**獲利體質強健**")
                st.write(f"• 今日利潤率達 {margin_rate:.1f}%。")

        st.info(f"📌 **老闆碎碎念：** 今日損益平衡點(不含租金)約需 {int((food_cost + delivery_cost)/avg_price) if avg_price > 0 else 0} 單。")
        #streamlit run "c:/Users/user/Desktop/黃沛瑜/python/專案相關/python專案/python-pj-easy.py"
