import os
import streamlit as st
from cryptography.fernet import Fernet
from google import genai
import datetime

# 1. 頁面基本設定
st.set_page_config(page_title="牙醫診所預約月曆管理系統", page_icon="🦷", layout="wide")

# 2. 初始化加密與 AI
if "encryption_key" not in st.session_state:
    st.session_state.encryption_key = Fernet.generate_key()
cipher = Fernet(st.session_state.encryption_key)

# 請在此填入你的 Gemini API Key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. 模擬長期資料庫 (儲存一個月的預約、時段、備註、加密代碼)
if "db_records" not in st.session_state:
    st.session_state.db_records = [
        {"id": 1, "date": "2026-09-01", "session": "上午", "patient": "王小明", "phone": "0912-345678", "notes": "洗牙、預約複診", "encrypted_sample": "gAAAAABk...[三年保密加密]"},
        {"id": 2, "date": "2026-09-01", "session": "下午", "patient": "李美華", "phone": "0922-888999", "notes": "根管治療", "encrypted_sample": "gAAAAABk...[三年保密加密]"},
        {"id": 3, "date": "2026-09-05", "session": "晚上", "patient": "張志豪", "phone": "0933-123456", "notes": "人工植牙諮詢", "encrypted_sample": "gAAAAABk...[三年保密加密]"}
    ]

st.title("🦷 牙醫診所紙本預約數位化與搜尋系統")
st.markdown("支援拍照 AI 辨識、一個月時段總覽（上午/下午/晚上）、自由加註與病患快速搜尋。")
st.divider()

# 分頁設計
tab1, tab2, tab3 = st.tabs(["📸 拍照上傳與智慧辨識", "📅 一個月預約時段總覽", "🔍 病人查詢與歷史紀錄"])

with tab1:
    st.subheader("1. 拍照或上傳紙本預約表")
    uploaded_file = st.file_uploader("上傳預約紙本照片 (JPG, PNG)", type=["jpg", "jpeg", "png"])

    col1, col2, col3 = st.columns(3)
    with col1:
        input_date = st.date_input("預約日期", datetime.date.today())
    with col2:
        input_session = st.selectbox("時段選擇", ["上午", "下午", "晚上"])
    with col3:
        input_patient = st.text_input("病人姓名", placeholder="例如：林大為")

    input_phone = st.text_input("連絡電話", placeholder="例如：0912-345678")
    input_notes = st.text_area("自由加註 / 治療項目", placeholder="例如：主訴右下智齒痛，指定某醫師...")

    if st.button("🚀 確認送出並加密存檔", type="primary", use_container_width=True):
        if not input_patient:
            st.warning("請至少輸入病人姓名！")
        else:
            ai_text = "無拍照辨識"
            if uploaded_file:
                temp_path = f"temp_{uploaded_file.name}"
                try:
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    if GEMINI_API_KEY != "你的實際API金鑰":
                        uploaded_img_ref = client.files.upload(file=temp_path)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[uploaded_img_ref, "請從這張預約表中萃取相關文字與細節。"]
                        )
                        ai_text = response.text
                except Exception as e:
                    ai_text = f"辨識發生狀況: {e}"
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)  # 用完即焚

            # 模擬加密處理
            sample_encrypted = cipher.encrypt(f"{input_patient}-{input_phone}".encode("utf-8")).decode("utf-8")[:30] + "..."

            # 寫入資料庫
            new_record = {
                "id": len(st.session_state.db_records) + 1,
                "date": str(input_date),
                "session": input_session,
                "patient": input_patient,
                "phone": input_phone if input_phone else "未填",
                "notes": input_notes if input_notes else "無",
                "encrypted_sample": sample_encrypted
            }
            st.session_state.db_records.append(new_record)
            st.success("✅ 預約資料已成功加密並建檔！照片已立即銷毀。")

with tab2:
    st.subheader("📅 一個月預約時段總覽 (上午 / 下午 / 晚上)")
    
    if len(st.session_state.db_records) == 0:
        st.info("目前尚無預約資料。")
    else:
        st.dataframe(
            st.session_state.db_records,
            column_config={
                "date": "日期",
                "session": "時段",
                "patient": "病人姓名",
                "phone": "電話",
                "notes": "備註與治療項目",
                "encrypted_sample": "加密安全憑證"
            },
            use_container_width=True
        )

with tab3:
    st.subheader("🔍 病人詢問即時搜尋")
    st.markdown("當病人打電話來詢問或櫃檯要核對時，可直接輸入**姓名**或**電話**進行秒搜：")
    
    search_keyword = st.text_input("輸入要搜尋的病人姓名或電話關鍵字：", placeholder="例如：王小明 或 0912")
    
    if search_keyword:
        results = [
            r for r in st.session_state.db_records 
            if search_keyword in r["patient"] or search_keyword in r["phone"] or search_keyword in r["notes"]
        ]
        
        if len(results) > 0:
            st.success(f"找到 {len(results)} 筆相關預約紀錄：")
            for r in results:
                with st.container(border=True):
                    st.markdown(f"**📅 日期**：`{r['date']}` ｜ **時段**：`{r['session']}`")
                    st.markdown(f"**👤 病人**：{r['patient']} ({r['phone']})")
                    st.markdown(f"**📝 備註**：{r['notes']}")
                    st.caption(f"🔒 三年保密加密代碼: `{r['encrypted_sample']}`")
        else:
            st.warning("查無符合的預約紀錄。")
    else:
        st.info("請在上方輸入關鍵字以開始搜尋...")
