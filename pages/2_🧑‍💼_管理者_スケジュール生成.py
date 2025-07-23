import streamlit as st, json

sa = st.secrets.get("gcp_service_account")
sid = st.secrets.get("SHEET_ID")

if not sa:
    st.warning("一時対応：サービスアカウントJSONを貼ってください（外部公開しないでください）")
    txt = st.text_area("Service Account JSON", height=200)
    if not txt:
        st.stop()
    sa = json.loads(txt)

if not sid:
    sid = st.text_input("SHEET_ID を入力してください")
    if not sid:
        st.stop()

service_account_info = dict(sa)
sheet_id = sid



import streamlit as st
import pandas as pd
from datetime import date
from calendar import monthrange
from scheduler import sheet_io, solver, excel_out
import io, base64

st.title("🧑‍💼 管理者 / スケジュール生成")

if "gcp_service_account" not in st.secrets or "SHEET_ID" not in st.secrets:
    st.error("管理者へ: Streamlit Secrets に gcp_service_account と SHEET_ID を設定してください。")
    st.stop()

service_account_info = dict(st.secrets["gcp_service_account"])
sheet_id = st.secrets["SHEET_ID"]

df_d, df_o, sh, ws_d, ws_o = sheet_io.read_tables(service_account_info, sheet_id)

if len(df_d)==0:
    st.warning("医師データがありません。まず 医師入力 ページから登録してください。")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", min_value=2024, max_value=2100, value=date.today().year)
with col2:
    month = st.number_input("月", min_value=1, max_value=12, value=date.today().month)

# 実行
if st.button("生成する", type="primary"):
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)

    try:
        schedule_df, counts = solver.build_schedule(start, end, df_d, df_o)
    except Exception as e:
        st.error(f"エラー: {e}")
        st.stop()

    st.success("生成しました。")

    st.subheader("割当結果プレビュー")
    st.dataframe(schedule_df)

    st.subheader("当直回数（公平性確認）")
    cnt_df = pd.DataFrame(counts.items(), columns=["doctor_id","count"])
    cnt_df = cnt_df.merge(df_d[["doctor_id","name"]], on="doctor_id", how="left")
    st.dataframe(cnt_df[["doctor_id","name","count"]])

    # Excel DL
    bio = io.BytesIO()
    title = f"{year}年{month}月 当直表"
    excel_out.to_excel(schedule_df, bio, title=title)
    bio.seek(0)
    b64 = base64.b64encode(bio.read()).decode('utf-8')
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="schedule_{year}-{month:02d}.xlsx">Excelをダウンロード</a>'
    st.markdown(href, unsafe_allow_html=True)
