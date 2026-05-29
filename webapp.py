from flask import Blueprint, request, render_template, redirect, url_for, flash, session, Flask, Response, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import User, Admin, db
from datetime import datetime
from utils.validation import validate_user_input, validate_user_pw_input
from itsdangerous import URLSafeTimedSerializer
import csv
import io
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Flask-Login 初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'  

@login_manager.user_loader
def load_user(user_id):
    admin = Admin.query.get(user_id)
    if admin:
        return admin
    return User.query.get(user_id)

# DB 接続設定
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB 初期化
db.init_app(app)

# Migrate 初期化
migrate = Migrate(app, db)

from utils.mail import send_register_mail, send_withdraw_mail, send_password_reset_mail

bp = Blueprint('main', __name__)

#####################################
#管理者設定のため一度だけ実行
#####################################

@app.route('/create_admin')
def create_admin():
    # すでに super が存在するなら実行しない（初期化は一度だけ）
    existing_super = Admin.query.filter_by(username='super').first()
    if existing_super:
        return "Admins already created", 403

    from werkzeug.security import generate_password_hash

    # 通常管理者 admin01
    admin01 = Admin(
        username='admin01',
        role='admin',
        password_hash=generate_password_hash('admin01')
    )

    # 上位管理者 super
    super_admin = Admin(
        username='super',
        role='super',
        password_hash=generate_password_hash('super')
    )

    db.session.add(admin01)
    db.session.add(super_admin)
    db.session.commit()
    return "Initial admins created"

@app.route('/fix_demo')
def fix_demo():
    from werkzeug.security import generate_password_hash
    new_hash = generate_password_hash("demo123")

    # SQLAlchemy を使って更新
    db.session.execute(
        "UPDATE admins SET password_hash = :hash WHERE username = 'demo'",
        {"hash": new_hash}
    )
    db.session.commit()

    return "done"


########################################
# 一般ユーザー向け
########################################

# TOPページ
@app.route('/')
def index():
    return render_template('index.html')

# 会員登録
@bp.route('/register', methods=['GET', 'POST'])
def register():
    get_flashed_messages(category_filter=["register"])
    if request.method == 'POST':
        # 入力値取得
        data = {
            "name": request.form.get('name', ''),
            "email": request.form.get('email', ''),
            "zip1": request.form.get('zip1', ''),
            "zip2": request.form.get('zip2', ''),
            "zipcode": (request.form.get('zip1', '') + request.form.get('zip2', '')),
            "address": request.form.get('address', ''),
            "phone": request.form.get('phone', ''),
            "password": request.form.get('password', ''),
            "password_check": request.form.get('password_check', '')
        }

        # バリデーション実行
        errors = validate_user_input(data, check_email_duplicate=True, check_password=True, check_name=True, check_zipcode=True)

        if errors:
            for err in errors:
                if "パスワード" in err:
                    data["password"] = ""
                    data["password_check"] = ""

                flash(err, "register")
            return render_template('user/register.html', data=data)

        # DB登録
        user = User(
            name=data["name"],
            email=data["email"],
            zipcode=data["zipcode"],
            address=data["address"],
            phone=data["phone"]
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        # メール送信
        try:
            send_register_mail(user)
            flash("登録が完了しました", "login")
        except Exception as e:
            print("MAIL ERROR:", e)

        return redirect(url_for('main.login'))

    return render_template('user/register.html')

# ログイン
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.membership_status != '退会' :
            login_user(user)
            return redirect(url_for('main.mypage'))
        else:
            flash("メールアドレスまたはパスワードが違います", "login")
            return render_template('user/login.html')

    get_flashed_messages()
    return render_template('user/login.html')

# パスワードリセット
@bp.route('/forget_pw', methods=['GET', 'POST'])
def forget_pw():
    if request.method == 'POST':
        # 入力値取得
        data = {
            "name": "",
            "email": request.form.get('email', ''),
            "zipcode": "",
            "address": "",
            "phone": "",
            "password": ""
        }

        # バリデーション実行
        errors = validate_user_input(
            data, 
            check_email_duplicate=False, 
            check_password=False, 
            check_name=False,
            check_zipcode=False
        )

        if errors:
            for err in errors:
                flash(err, "forget_pw")
            return render_template('user/forget_pw.html', data=data)

        # ユーザー取得
        user = User.query.filter_by(email=data["email"]).first()
        if not user:
            flash("このメールアドレスは登録されていません", "forget_pw")
            return render_template('user/forget_pw.html', data=data)

        # シリアライザ作成
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

        # トークン作成
        token = serializer.dumps(user.email, salt='password-reset')

        # メールに貼るURL
        reset_url = url_for('main.reset_password', token=token, _external=True)

        # メール送信
        send_password_reset_mail(user, reset_url)

        flash("パスワードリセット用メールを送信しました", "login")
        return redirect(url_for('main.login'))
    
    return render_template('user/forget_pw.html')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    # トークン検証
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash("リンクが無効か、有効期限が切れています", "forget_pw")
        return redirect(url_for('main.forget_pw'))

    # ユーザー取得
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("ユーザーが存在しません", "forget_pw")
        return redirect(url_for('main.forget_pw'))

    # POST（パスワード更新）
    if request.method == 'POST':
        # 入力値取得
        data = {
            "password": user.password_hash
        }

        pw = {   
            "pw_new": request.form.get('password_new', ''),
            "pw_check": request.form.get('password_check', ''),
        }
        # バリデーション
        errors = validate_user_pw_input(data, pw, check_current=False)
        if errors:
            for err in errors:
                flash(err, "reset_password")
            return render_template('user/reset_password.html', token=token)

        # パスワード更新
        user.set_password(pw['pw_new'])
        db.session.commit()

        flash("パスワードを更新しました。ログインしてください。", "login")
        return redirect(url_for('main.login'))

    # GET（画面表示）
    return render_template('user/reset_password.html', token=token)

# マイページ
@bp.route('/mypage')
@login_required
def mypage():
    zipcode = current_user.zipcode or ""

    zip1 = zipcode[:3] if len(zipcode) == 7 else ""
    zip2 = zipcode[3:] if len(zipcode) == 7 else ""

    return render_template('user/mypage.html', user=current_user, zip1=zip1, zip2=zip2)

# 会員情報更新
@bp.route('/mypage/edit', methods=['GET', 'POST'])
@login_required
def update_mypage():
    if request.method == 'POST':
        # 入力値取得
        data = {
            "id": request.form.get('id', ''),
            "name": request.form.get('name', ''),
            "email": request.form.get('email', ''),
            "zip1": request.form.get('zip1', ''),
            "zip2": request.form.get('zip2', ''),
            "zipcode": (request.form.get('zip1', '') + request.form.get('zip2', '')),
            "address": request.form.get('address', ''),
            "phone": request.form.get('phone', ''),
        }

        # バリデーション実行
        errors = validate_user_input(
            data, 
            check_email_duplicate=True, 
            check_password=False,
            current_user_id=current_user.id
        )

        if errors:
            for err in errors:
                if "メールアドレス" in err:
                    data["email"] = ""
                if "パスワード" in err:
                    data["password"] = ""

                flash(err, "mypage_edit")
            return render_template(
                'user/mypage_edit.html', 
                data=data, 
                zip1=data["zip1"], 
                zip2=data["zip2"]
            )

        # DB更新
        current_user.name = data["name"]
        current_user.email = data["email"]
        current_user.zipcode = data["zipcode"]
        current_user.address = data["address"]
        current_user.phone = data["phone"]

        db.session.commit()        
        flash("更新しました", "mypage")
        return redirect(url_for('main.mypage'))

    # zipcode を取得して分割する
    zipcode = current_user.zipcode or ""
    zip1 = zipcode[:3] if len(zipcode) == 7 else ""
    zip2 = zipcode[3:] if len(zipcode) == 7 else ""

    data = {
        "name": current_user.name,
        "email": current_user.email,
        "zip1": zip1,
        "zip2": zip2,
        "zipcode": current_user.zipcode,
        "address": current_user.address,
        "phone": current_user.phone,
        "password": ""
    }
    return render_template('user/mypage_edit.html', data=data)

# 休会
@bp.route('/inactive', methods=['POST'])
@login_required
def inactive():
    current_user.membership_status = '休会'
    db.session.commit()

    flash("ステータスを休会に変更しました", "mypage")
    return redirect(url_for('main.mypage'))

# 再開
@bp.route('/reactivate', methods=['POST'])
@login_required
def reactivate():
    current_user.membership_status = '活動中'
    db.session.commit()

    flash("ステータスを活動中に変更しました")
    return redirect(url_for('main.mypage'))

# パスワード変更
@bp.route('/ch_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        # 入力値取得
        data = {
            "password": current_user.password_hash
        }

        pw = {   
            "pw_current": request.form.get('password_current', ''),
            "pw_new": request.form.get('password_new', ''),
            "pw_check": request.form.get('password_check', ''),
        }

        # バリデーション実行
        errors = validate_user_pw_input(data, pw, check_current=True)

        if errors:
            for err in errors:
                flash(err, "ch_password")
            return render_template('user/ch_password.html')

        # DB更新
        current_user.set_password(pw["pw_new"])

        db.session.commit()        
        flash("パスワードを更新しました")
        return redirect(url_for('main.mypage'))
    
    return render_template('user/ch_password.html')

# 退会
@bp.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    current_user.membership_status = '退会'
    db.session.commit()

    withdrawn_at = datetime.now()
    try:
        send_withdraw_mail(current_user, withdrawn_at)
        flash("登録が完了しました", "withdraw")
    except Exception as e:
        print("MAIL ERROR:", e)

    logout_user()
    session.clear()
    flash("退会が完了しました", "login")
    return redirect(url_for('main.login'))

# ログアウト
@bp.route('/logout', methods=['GET'])
@login_required
def logout():    
    session.clear() 
    logout_user()
    return render_template('user/login.html')

########################################
# 管理者向け
########################################

# 管理者ログイン
@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    get_flashed_messages()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('main.admin_search_form'))
        else:
            flash("認証に失敗しました", "login")
            return redirect(url_for('main.admin_login'))

    return render_template('admin/login.html')

# 会員検索フォーム表示
@bp.route('/admin/search', methods=['GET'])
@login_required
def admin_search_form():
    return render_template('admin/search.html')

# 会員検索
@bp.route('/admin/search/results', methods=['GET', 'POST'])
@login_required
def admin_search_results():
    if request.method == 'POST': 
        # フォームから検索条件を取得
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        status = request.form.get('status', '').strip()

        # 検索条件をセッションに保存
        session['search'] = {
            'name': name,
            'email': email,
            'address': address,
            'status': status
        }

    # GET でも POST でもここで検索実行
    cond = session.get('search', {})
    query = User.query

    if cond.get('name'):
        query = query.filter(User.name.contains(cond['name']))
    if cond.get('email'):
        query = query.filter(User.email.contains(cond['email']))
    if cond.get('address'):
        query = query.filter(User.address.contains(cond['address']))
    if cond.get('status'):
        query = query.filter_by(membership_status=cond['status'])
    
    users = query.all()
    return render_template('admin/users.html', users=users)

# 会員詳細
@bp.route('/admin/users/<int:id>', methods=['GET'])
@login_required
def admin_user_detail(id):
    user = User.query.get_or_404(id)

    zipcode = user.zipcode or ""

    zip1 = zipcode[:3] if len(zipcode) == 7 else ""
    zip2 = zipcode[3:] if len(zipcode) == 7 else ""

    return render_template('admin/user_detail.html', user=user, zip1=zip1, zip2=zip2)


# 会員編集
@bp.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_user_update(id):
    user = User.query.get_or_404(id)
    # Demo 管理者は編集前に当該会員のパスワード確認が必要
    verification_key = f'demo_edit_verified_{id}'

    # パスワード確認フォームの送信（demo 用）
    if request.method == 'POST' and request.form.get('action') == 'verify_member_password':
        member_pw = request.form.get('member_password', '')
        if user.check_password(member_pw):
            session[verification_key] = True
            return redirect(url_for('main.admin_user_update', id=id))
        else:
            flash('パスワードが一致しません', 'user_detail')
            return redirect(url_for('main.admin_user_detail', id=id))

    # 通常の編集処理（保存）
    if request.method == 'POST':
        # 入力値取得
        data = {
            "id": request.form.get('id', ''),
            "name": request.form.get('name', ''),
            "email": request.form.get('email', ''),
            "zip1": request.form.get('zip1', ''),
            "zip2": request.form.get('zip2', ''),
            "zipcode": (request.form.get('zip1', '') + request.form.get('zip2', '')),
            "address": request.form.get('address', ''),
            "membership_status": user.membership_status,            
            "phone": request.form.get('phone', ''),
        }

        # バリデーション実行
        errors = validate_user_input(
            data, 
            check_email_duplicate=False,
            check_password=False,
            current_user_id=current_user.id
        )

        if errors:
            for err in errors:
                if "メールアドレス" in err:
                    data["email"] = ""
                if "パスワード" in err:
                    data["password"] = ""

                flash(err, "user_detail_edit")
            return render_template(
                'admin/user_detail_edit.html', 
                data=data, 
                zip1=data["zip1"], 
                zip2=data["zip2"]
            )

        # DB更新
        user.name = data["name"]
        user.email = data["email"]
        user.zipcode = data["zipcode"]
        user.address = data["address"]
        user.phone = data["phone"]
        db.session.commit()
        # 編集セッションフラグを消す
        session.pop(verification_key, None)
        flash("更新しました", "user_detail")
        return redirect(url_for('main.admin_user_detail', id=id))
    
    # zipcode を取得して分割する
    zipcode = user.zipcode or ""
    zip1 = zipcode[:3] if len(zipcode) == 7 else ""
    zip2 = zipcode[3:] if len(zipcode) == 7 else ""

    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "zip1": zip1,
        "zip2": zip2,
        "zipcode": user.zipcode,
        "address": user.address,
        "phone": user.phone,
        "membership_status": user.membership_status,
        "password": ""
    }
    # demo 管理者の場合、編集前に確認済みでなければパスワード入力画面へ
    if current_user.username == 'demo' and not session.get(verification_key):
        return render_template(
            'admin/confirm_member_password.html',
            user=user,
            form_action=url_for('main.admin_user_update', id=id),
            title='編集のための確認',
            button_text='確認'
        )

    return render_template('admin/user_detail_edit.html', data=data)

@bp.route('/admin/users/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_user_delete(id):
    user = User.query.get_or_404(id)
    verification_key = f'demo_edit_verified_{id}'
    
    # ① demo-admin のパスワード確認処理
    if current_user.role == 'demo_admin':
        # パスワード確認フォームの送信（demo 用）
        if request.method == 'POST' and request.form.get('action') == 'verify_member_password':
            member_pw = request.form.get('member_password', '')
            if user.check_password(member_pw):
                session[verification_key] = True
            else:
                flash('パスワードが一致しません', 'user_detail')
                return redirect(url_for('main.admin_user_detail', id=id))

        # 初回はパスワード入力画面へ
        if not session.get(verification_key):
            return render_template(
                'admin/confirm_member_password.html',
                user=user,
                form_action=url_for('main.admin_user_delete', id=id),
                title='削除のための確認',
                button_text='削除を進める'
            )
        

    if current_user.role not in ['super','demo_admin']:
        flash("権限がありません", "user_detail")
        return redirect(url_for('main.admin_user_detail', id=id))

    if user.membership_status != '退会':
        flash("当会員は退会していません", "user_detail")
        return render_template('admin/user_detail.html', user=user)

    db.session.delete(user)
    db.session.commit()

    flash("削除しました")

    return redirect(url_for('main.admin_search_results'))


# 管理者パスワード変更
@bp.route('/ch_admins_password', methods=['GET', 'POST'])
@login_required
def change_admins_password():
    # GET の場合はクエリパラメータから取得
    # POST の場合は hidden input から取得
    target_username = request.args.get("target") if request.method == "GET" else request.form.get("target")

    # 対象管理者を DB から取得
    target = Admin.query.filter_by(username=target_username).first()
    if not target:
        flash("対象の管理者が見つかりません", "search")
        return redirect(url_for('main.admin_search_form'))

    # demo 管理者はパスワード変更不可
    if current_user.username == 'demo':
        flash("権限がありません", "search")
        return render_template('admin/search.html')

    # super 以外は自身のパスワードのみ変更可
    if current_user.role != "super" and target.username != current_user.username:
        flash("権限がありません", "search")
        return render_template('admin/search.html')

    if request.method == 'POST':
               
        # targetのパスワードを取得する
        data = {
            "password": target.password_hash
        }

        pw = {   
            "pw_current": request.form.get('password_current', ''),
            "pw_new": request.form.get('password_new', ''),
            "pw_check": request.form.get('password_check', ''),
        }

        # バリデーション実行
        errors = validate_user_pw_input(data, pw, check_current=True)

        if errors:
            for err in errors:
                flash(err, "ch_admins_password")
            return render_template('admin/ch_admins_password.html', target=target)

        # DB更新
        target.set_password(pw["pw_new"])

        db.session.commit()        
        flash("パスワードを更新しました","search")
        return redirect(url_for('main.admin_search_form'))

    # パスワード変更画面へ
    return render_template("admin/ch_admins_password.html", target=target)

# ログアウト
@bp.route('/admin/logout', methods=['GET'])
@login_required
def admin_logout():
    session.clear()
    logout_user()
    return render_template('admin/login.html')

########################################
# CSVインポート / エクスポート
########################################
#CSVインポート/エクスポート画面
@bp.route("/admin/users/im_ex_port", methods=["GET"])
def im_ex_port_files():
    return render_template("admin/im_ex_port.html")

@bp.route('/admin/users/import', methods=['POST'])
@login_required
def import_csv():
        # demo 管理者はCSVインポート不可
    if current_user.username == 'demo':
        flash("権限がありません", "search")
        return render_template('admin/search.html')

    if current_user.role != 'super':
        flash("権限がありません", "search")
        return redirect(url_for('main.admin_search_form'))

    file = request.files['file']

    if file.filename=="":
        return "ファイルが選択されていません"
    
    #CSVを読み込む
    stream = io.TextIOWrapper(file.stream, encoding='utf-8')
    reader=csv.reader(stream)

    #見出しを1行読み飛ばす
    next(reader)

    for row in reader:
        if len(row) < 6:
            continue 
        
        name = row[0]
        email = row[1]
        zipcode = row[2]
        address = row[3]
        phone = row[4]
        password = row[5]

        user = User (
            name = name,
            email = email,
            zipcode = zipcode,
            address = address,
            phone = phone
        )

        user.set_password(password)
        db.session.add(user)

    db.session.commit()

    flash("インポートが完了しました", "im_ex_port")
    return render_template('admin/im_ex_port.html')

@bp.route('/admin/users/export')
@login_required
def export_csv():
    if current_user.role not in ['super', 'demo_admin']:
        flash("権限がありません", "search")
        return redirect(url_for('main.admin_search_form'))

    # メモリ上に CSV を作成
    output = io.StringIO()

    # Excel で文字化けしないように BOM を付与
    output.write('\ufeff')

    writer = csv.writer(output)

    # ヘッダー行
    writer.writerow(["名前", "メール", "郵便番号", "住所", "電話", "ステータス"])

    # DB から全件取得
    users = User.query.all()

    # データ行を書き込み
    for u in users:
        writer.writerow([
            u.name,
            u.email,
            u.zipcode,
            u.address,
            u.phone,
            u.membership_status
        ])

    # CSV をレスポンスとして返す
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )

    return response

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

