import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time

# 1. 基礎設定：解決圖表中文顯示問題
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
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

# --- 模擬核心邏輯：模擬客人在餐廳發生的事 ---
def customer_process(env, name, kitchen, stats):
    # 客人到達的時間
    arrival_time = env.now
    
    # 請求廚房資源（排隊做餐）
    with kitchen.request() as request:
        yield request
        # 模擬做餐時間 (3~7分鐘)
        cooking_time = random.randint(3, 7)
        yield env.timeout(cooking_time)
        
        # 紀錄這筆訂單的等待時間
        wait_time = env.now - arrival_time
        stats.append({
            "訂單編號": name,
            "等待分鐘": wait_time,
            "類型": random.choice(["現場", "外送"])
        })

def setup_shop(env, kitchen, stats):
    customer_id = 0
    while True:
        # 每隔 3~8 分鐘來一個客人
        yield env.timeout(random.randint(3, 8))
        customer_id += 1
        env.process(customer_process(env, f"客{customer_id}", kitchen, stats))

# --- 執行按鈕 ---
if st.button("🚀 開始模擬一天營運"):
    results = []
    env = simpy.Environment()
    kitchen_res = simpy.Resource(env, capacity=kitchen_staff)
    
    env.process(setup_shop(env, kitchen_res, results))
    env.run(until=shop_hours * 60) # 轉為分鐘
    
    df = pd.DataFrame(results)
    
    # --- 報告呈現區：計算結果 ---
    if not df.empty:
        # 1. 營業額與成本計算
        total_orders = len(df)
        revenue = total_orders * avg_price
        
        # 分類統計 (現場 vs 外送)
        delivery_count = len(df[df["類型"] == "外送"])
        delivery_cost = (delivery_count * avg_price) * (platform_fee / 100)
        food_cost = revenue * (food_rate / 100)
        
        # 淨利計算
        profit = revenue - food_cost - delivery_cost
        
        # 2. 數據看板
        st.header("📊 今日營運成績單")
        c1, c2, c3 = st.columns(3)
        c1.metric("總訂單數", f"{total_orders} 單")
        c2.metric("預估營收", f"${revenue:,.0f}")
        c3.metric("預估淨利", f"${profit:,.0f}")

        # 3. 圖表展示
        st.subheader("📈 營運分析圖表")
        col_left, col_right = st.columns(2)
        
        with col_left:
            # 等待時間分布圖
            fig, ax = plt.subplots()
            ax.hist(df["等待分鐘"], bins=10, color='skyblue', edgecolor='black')
            ax.set_title("客戶等待時間分布")
            ax.set_xlabel("分鐘")
            ax.set_ylabel("人數")
            st.pyplot(fig)
            
        with col_right:
            # 成本比例圓餅圖
            fig2, ax2 = plt.subplots()
            labels = ['食材成本', '外送抽成', '剩餘利潤']
            sizes = [food_cost, delivery_cost, max(0, profit)]
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
            ax2.set_title("今日支出結構")
            st.pyplot(fig2)

        # 4. 專業經營診斷報告 (老闆專用版)
        st.divider()
        st.header("💡 創業中老闆經營實戰建議")
        
        avg_wait = df["等待分鐘"].mean()
        max_wait = df["等待分鐘"].max()
        delivery_ratio = (delivery_count / total_orders * 100) if total_orders > 0 else 0
        
        # 根據經營指標分層建議
        c_diag1, c_diag2, c_diag3 = st.columns(3)
        
        with c_diag1:
            st.write("### 🚀 效率與人力分析")
            if avg_wait > 8:
                st.error(f"**產能亮紅燈！**")
                st.write(f"• 平均等待時間已達 {avg_wait:.1f} 分鐘。")
                st.write(f"• 最久客人等了 {max_wait:.0f} 分鐘。")
                st.write("👉 **老闆注意：** 客人耐心極限通常是 15 分鐘。目前的廚房人力在尖峰期會造成嚴重負評，建議檢視 SOP 或考慮增加 1 名 PT 人力支援出餐。")
            else:
                st.success(f"**產能效率優良**")
                st.write(f"• 目前平均等待僅 {avg_wait:.1f} 分鐘。")
                st.write("👉 **老闆注意：** 目前人力配置相當精簡有效。若未來訂單成長 20%，仍有緩衝空間，暫不需增加薪資支出。")

        with c_diag2:
            st.write("### 🛵 通路獲利分析")
            if delivery_ratio > 40:
                st.warning(f"**過度依賴平台**")
                st.write(f"• 外送佔比高達 {delivery_ratio:.1f}%。")
                st.write(f"• 今日平台抽成吃掉了 ${delivery_cost:,.0f}。")
                st.write("👉 **老闆注意：** 你正在幫平台打工！建議推行『店取優惠』或隨餐附上『下次內用贈品券』，設法將外送客轉為內用客。")
            else:
                st.success(f"**通路結構健康**")
                st.write(f"• 外送佔比僅 {delivery_ratio:.1f}%。")
                st.write("👉 **老闆注意：** 實體訂單為主能確保毛利穩定。建議維持內用品質，鞏固基本盤。")

        with c_diag3:
            st.write("### 💰 財務生存指南")
            margin_rate = (profit / revenue * 100) if revenue > 0 else 0
            if margin_rate < 15:
                st.error(f"**獲利空間過薄**")
                st.write(f"• 今日預估利潤率僅 {margin_rate:.1f}%。")
                st.write("👉 **老闆注意：** 扣除租金與水電後你可能在虧錢。請立即檢查：1. 是否有食材浪費？2. 客單價是否太低？建議針對高毛利品項做加價購促銷。")
            else:
                st.success(f"**獲利體質強健**")
                st.write(f"• 今日利潤率達 {margin_rate:.1f}%。")
                st.write("👉 **老闆注意：** 經營模型成立。若能維持此表現，可開始規劃行銷預算或尋找下個營運成長點。")

        # 底部總結提醒
        st.info(f"📌 **老闆碎碎念：** 今日損益平衡點(不含租金)約需 **{int((food_cost + delivery_cost)/avg_price) if avg_price > 0 else 0}** 單。請持續監控食材損耗，那是看不見的獲利黑洞。")


        #streamlit run "c:/Users/user/Desktop/黃沛瑜/python/專案相關/python專案/python-pj-easy.py"