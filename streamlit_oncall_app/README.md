# 当直割り振り Web アプリ（ブラウザのみ運用：Streamlit Cloud / Google Colab対応）

各医師が自分で **曜日NG** と **特定日希望休** を入力し、管理者がワンクリックで **当直表（Excel/A4印刷用）** を生成できる簡易Webアプリです。  
Python実行環境はクラウド側に任せるため、ローカルにPythonを入れる必要はありません。

---

## 0. 全体構成

- フロント＆バックエンド：**Streamlit**（無料の Streamlit Community Cloud にデプロイ可）
- 永続データストア：**Googleスプレッドシート**（医師の入力内容を保存）
- 最適化エンジン：Google OR-Tools（Streamlit上で動作）

### 主要ページ（GUI）
1. **医師用フォーム**  
   - 自分の名前を選択/入力  
   - 曜日NGをチェックボックスで選択  
   - 希望休の日付をカレンダーで複数選択 → 追加ボタンで登録  
   - 送信後、反映済み内容が表示される

2. **管理者ページ**  
   - 年・月を指定  
   - 「生成」ボタンで当直表作成（平日1名、土日祝2名、連続不可・回数差最小）  
   - 結果プレビュー＋Excelダウンロード  
   - 各医師の当直回数サマリ

---

## 1. デプロイ手順（Streamlit Cloud）

1. **GitHubリポジトリを作成**  
   このフォルダの中身をアップロード（ZIPを展開してpush）

2. **Streamlit Community Cloud にログイン**  
   https://share.streamlit.io/  
   - 「New app」→ 先ほどのGitHubリポジトリを指定

3. **Secrets設定（Google Sheets接続用）**  
   Streamlitの「Secrets」画面に以下を JSON で設定します。  
   サービスアカウントの作成は README 下部「2. Google Sheets 接続設定」を参照。

   ```toml
   [gcp_service_account]
   type = "..."
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "..."
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."

   SHEET_ID = "（あなたのスプレッドシートID）"
   ```

4. **Deploy**  
   Secrets 設定後、再デプロイすれば動作します。

---

## 2. Google Sheets 接続設定

### 2-1. スプレッドシート作成
- Google Drive で「当直入力」用スプレッドシートを作成
  - シート1: `doctors`（医師の曜日NG）
  - シート2: `off_requests`（特定日希望休）

初期のヘッダーはアプリが無ければ自動作成します。

### 2-2. サービスアカウント作成（GCP）
1. https://console.cloud.google.com/ でプロジェクト作成
2. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」
3. 作成後、「鍵を追加」→「JSON」形式でダウンロード
4. JSON 内容を Secrets に貼り付ける（上記toml形式）
5. スプレッドシートを **サービスアカウントのメールアドレスに共有（編集可）** してください。

---

## 3. ローカルで試す（オプション）

Pythonが使えるPCなら：

```bash
pip install -r requirements.txt
streamlit run app.py
```

※ ローカル試験時は secrets.toml を `.streamlit/secrets.toml` に用意してください。

---

## 4. Google Colabで使う場合（代替案）

- Colab ノートブックにこのリポジトリをコピーし、`!pip install -r requirements.txt`
- `streamlit` を `localtunnel`/`ngrok` 経由で公開する or Colab上で `gradio` に作り替える

（必要なら別途ノートブックを用意します）

---

## 5. カスタマイズ
- 希望休をソフト制約に変更（solver.py 内でペナルティ変数導入）
- 前月末・翌月頭の連続禁止チェックを追加
- 専門科毎の最低人数なども制約に追加可能

---

## 6. フォルダ構成

```
.
├── app.py                     # Streamlitメインアプリ
├── pages/
│   ├── 1_👨‍⚕️_医師入力.py
│   └── 2_🧑‍💼_管理者_スケジュール生成.py
├── scheduler/
│   ├── solver.py              # OR-Tools最適化
│   ├── excel_out.py           # Excel出力
│   └── sheet_io.py            # Google Sheets read/write
├── sample_data/
│   ├── doctors_template.csv
│   └── off_requests_template.csv
├── requirements.txt
└── README.md
```

---

何か追加したい機能や、院内ポリシーに合わせた変更があれば、お気軽にお知らせください。
