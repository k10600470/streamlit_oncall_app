import streamlit as st

st.set_page_config(page_title="当直割り振り", layout="wide")

st.title("当直割り振り Web アプリ")

st.markdown(
"""
### 使い方
- 左のサイドバーのページを選んでください。
  - 👨‍⚕️ **医師入力**：各医師が自分の曜日NGと希望休を登録
  - 🧑‍💼 **管理者 / スケジュール生成**：管理者が月を指定して当直表を生成
"""
)
