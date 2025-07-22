import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

DOCTOR_SHEET = "doctors"
OFFREQ_SHEET = "off_requests"

COLUMNS_DOCTORS = [
    "doctor_id","name",
    "cannot_mon","cannot_tue","cannot_wed","cannot_thu","cannot_fri","cannot_sat","cannot_sun"
]
COLUMNS_OFF = ["doctor_id","date"]

def get_client(service_account_info: dict):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(creds)

def open_or_init_sheets(gc, sheet_id: str):
    sh = gc.open_by_key(sheet_id)

    # doctors sheet
    try:
        ws_d = sh.worksheet(DOCTOR_SHEET)
    except gspread.WorksheetNotFound:
        ws_d = sh.add_worksheet(title=DOCTOR_SHEET, rows=100, cols=20)
        ws_d.append_row(COLUMNS_DOCTORS)

    # off_requests sheet
    try:
        ws_o = sh.worksheet(OFFREQ_SHEET)
    except gspread.WorksheetNotFound:
        ws_o = sh.add_worksheet(title=OFFREQ_SHEET, rows=100, cols=10)
        ws_o.append_row(COLUMNS_OFF)

    return sh, ws_d, ws_o

def read_tables(service_account_info: dict, sheet_id: str):
    gc = get_client(service_account_info)
    sh, ws_d, ws_o = open_or_init_sheets(gc, sheet_id)

    d_vals = ws_d.get_all_records()
    o_vals = ws_o.get_all_records()

    df_d = pd.DataFrame(d_vals, columns=COLUMNS_DOCTORS)
    df_o = pd.DataFrame(o_vals, columns=COLUMNS_OFF)
    # 型調整
    if "doctor_id" in df_d.columns and len(df_d)>0:
        df_d["doctor_id"] = pd.to_numeric(df_d["doctor_id"], errors="coerce").astype("Int64")
    if "doctor_id" in df_o.columns and len(df_o)>0:
        df_o["doctor_id"] = pd.to_numeric(df_o["doctor_id"], errors="coerce").astype("Int64")
    return df_d, df_o, sh, ws_d, ws_o

def upsert_doctor_row(ws_d, row_dict: dict):
    """doctor_idが既にいれば更新、なければappend"""
    # 既存の全データ取得
    all_vals = ws_d.get_all_records()
    # doctor_idで検索
    target_id = int(row_dict["doctor_id"])
    found_index = None
    for idx, r in enumerate(all_vals, start=2):  # 2行目からデータ
        if int(r.get("doctor_id", -1)) == target_id:
            found_index = idx
            break

    row_values = [row_dict.get(c, "") for c in COLUMNS_DOCTORS]
    if found_index:
        ws_d.update(f"A{found_index}:H{found_index}", [row_values])
    else:
        ws_d.append_row(row_values)

def replace_off_requests(ws_o, doctor_id: int, dates: list[str]):
    """該当doctor_idの行を全削除→datesで再挿入"""
    all_vals = ws_o.get_all_records()
    # 削除対象の行番号を特定（後ろから消す）
    to_delete = []
    for idx, r in enumerate(all_vals, start=2):
        if int(r.get("doctor_id",-1)) == int(doctor_id):
            to_delete.append(idx)
    for row_idx in reversed(to_delete):
        ws_o.delete_rows(row_idx)

    # 追加
    for dt in dates:
        ws_o.append_row([doctor_id, dt])
