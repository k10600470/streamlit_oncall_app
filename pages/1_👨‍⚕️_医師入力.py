import streamlit as st
import pandas as pd
from datetime import date
from scheduler import sheet_io

st.title("👨‍⚕️ 医師入力")

# Secrets 読み込み
if "gcp_service_account" not in st.secrets or "SHEET_ID" not in st.secrets:
    st.error("管理者へ: Streamlit Secrets に gcp_service_account と SHEET_ID を設定してください。")
    st.stop()

service_account_info = dict(st.secrets["gcp_service_account"])
sheet_id = st.secrets["SHEET_ID"]

df_d, df_o, sh, ws_d, ws_o = sheet_io.read_tables(service_account_info, sheet_id)

st.markdown("#### 1. 医師を選択 / 新規登録")
existing_names = df_d["name"].dropna().unique().tolist()
mode = st.radio("選択してください", ["既存医師から選ぶ", "新規登録"], horizontal=True)

if mode == "既存医師から選ぶ" and len(existing_names) > 0:
    name = st.selectbox("名前", existing_names)
    doctor_row = df_d[df_d["name"] == name].head(1)
    if len(doctor_row) == 0:
        st.stop()
    doctor_id = int(doctor_row["doctor_id"].iloc[0])
else:
    name = st.text_input("氏名（新規）")
    doctor_id = st.number_input("doctor_id（整数・被らないように）", min_value=1, step=1, value=1)

if not name:
    st.stop()

st.markdown("#### 2. 曜日NG の設定")
dow_labels = ["月","火","水","木","金","土","日"]
dow_keys = ["mon","tue","wed","thu","fri","sat","sun"]

defaults = {k:0 for k in dow_keys}
if doctor_id in df_d["doctor_id"].dropna().astype(int).values:
    row = df_d[df_d["doctor_id"] == doctor_id].iloc[0]
    defaults = {k:int(row[f"cannot_{k}"]) for k in dow_keys}

cols = st.columns(7)
ng_vals = {}
for i,(lab,key) in enumerate(zip(dow_labels,dow_keys)):
    with cols[i]:
        ng_vals[key] = st.checkbox(lab+"曜不可", value=bool(defaults[key]))

st.markdown("#### 3. 特定日希望休")
# 既存希望休を取得
existing_off = df_o[df_o["doctor_id"] == doctor_id]["date"].tolist()
st.write("登録済み：", ", ".join(existing_off) if existing_off else "なし")

new_dates = st.date_input("希望休を追加（複数選択可）", [])
# 日付を文字列へ
new_dates_str = [d.strftime("%Y-%m-%d") for d in new_dates]

if st.button("保存 / 更新", type="primary"):
    # upsert doctors row
    row_dict = {
        "doctor_id": int(doctor_id),
        "name": name,
        "cannot_mon": int(ng_vals["mon"]),
        "cannot_tue": int(ng_vals["tue"]),
        "cannot_wed": int(ng_vals["wed"]),
        "cannot_thu": int(ng_vals["thu"]),
        "cannot_fri": int(ng_vals["fri"]),
        "cannot_sat": int(ng_vals["sat"]),
        "cannot_sun": int(ng_vals["sun"]),
    }
    sheet_io.upsert_doctor_row(ws_d, row_dict)

    # replace off requests
    sheet_io.replace_off_requests(ws_o, int(doctor_id), new_dates_str)

    st.success("保存しました！")

    st.experimental_rerun()
