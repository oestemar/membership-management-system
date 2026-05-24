# ■README

## １．プロジェクト概要
本プロジェクトは、Flask + MySQL を用いて構築した
会員管理システム（ポートフォリオ用） です。

- 会員登録（メール送信：Resend）
- ログイン / ログアウト
- 会員情報編集
- 退会機能
- 管理者画面（ユーザー一覧・削除・CSVインポート・CSVエクスポート）
- メールログ管理（mail_logs）

バックエンドは Railway にデプロイし、
GitHub を用いてバージョン管理を行っています。

## ２．使用技術
- Python 3.x
- Flask
- MySQL
- SQLAlchemy
- Railway（本番環境）
- GitHub（ソース管理）
- Resend（メール送信予定）
- HTML / CSS

## ３．ディレクトリ構成
membership-management-system/
├──  webapp.py 
├──  models.py
├──  Procfile
├──  REAEME.md
├──  .gitignore
├──  requirements.txt
├──  migrations/
│    ├── alembic.ini
│    ├── env.py
│    └── script.py.mako
├──  utils/
│    ├── mail.py
│    └── validations.py
├──  templates/
│    └── index.html
          ├──  users/
          │    ├── ch_password.html
          │    ├── forget_pw.html
          │    ├── login.html
          │    ├── mypage_edit.html
          │    ├── mypage.html
          │    ├── register.html
          │    └── reset_password.html
          └──  admin/
               ├── ch_admins_password.html
               ├── im_ex_port.html
               ├── login.html
               ├── search.html
               ├── user_detail_edit.html
               ├── user_detail.html
               └── users.html
└──  static/
          └──  style.css

## ４．主な機能
- 会員側
- 新規登録
- ログイン / ログアウト
- パスワード変更・パスワード忘れ
- プロフィール表示
- 退会
- メール送信（Resend 予定）
- 管理者側
- 管理者ログイン
- 会員一覧
- 会員削除
- メールログ確認

## ５．画面一覧
- トップページ
- 会員登録画面
- ログイン画面
- マイページ
- 管理者ログイン
- 管理者ダッシュボード
- 会員一覧
- 会員削除確認

## ER 図
コード
users
     ├──  id (PK)
     ├──  name
     ├──  email
     ├──  zipcode
     ├──  address
     ├──  phone
     ├──  membership_status
     ├──  created_at
     ├──  updated_at
     └──  password_hash

admins
     ├──  id (PK)
     ├──  username
     ├──  role
     ├──  created_at
     ├──  updated_at
     └──  password_hash

mail_logs
     ├──  id (PK)
     ├──  user_id (FK → users.id)
     ├──  email
     ├──  subject
     ├──  body
     ├──  sent_at
     └──  status

## ローカル環境構築
1. 仮想環境作成
コード
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
2. パッケージインストール
コード
pip install -r requirements.txt
3. .env を作成（例）
コード
SECRET_KEY=xxxx
DATABASE_URL=mysql+pymysql://user:pass@localhost/dbname
RESEND_API_KEY=xxxx
MAIL_FROM=onboarding@resend.dev
4. 起動
コード
python app.py

## 本番環境（Railway）
1. 設定する Variables
- SECRET_KEY
- DATABASE_URL
- RESEND_API_KEY
- MAIL_FROM
2. デプロイ方法
GitHub リポジトリを Railway に接続
自動デプロイを有効化
Variables を設定
Deploy ボタンを押すだけ

## メール送信（Resend）
現在、メール送信は Resend の新規ドメイン（aiueo-system.com）伝播待ち。
Verified 後に以下を設定：

コード
MAIL_FROM=noreply@aiueo-system.com

## テスト手順
会員側
新規登録
ログイン
ログアウト
退会
メールログ確認

管理者側
管理者ログイン
会員一覧表示
会員削除
メールログ確認

📄 ライセンス
This project is for portfolio use.
