# utils/validation.py
import re
from models import User
from werkzeug.security import check_password_hash
import requests

def validate_user_input(data, check_email_duplicate=True, check_password=True, 
                        current_user_id=None, check_name=True, check_zipcode=True):
    """
    data: {
        "name": "",
        "email": "",
        "zip1": "",
        "zip2": "",
        "zipcode": "",
        "address": "",
        "phone": "",
        "password": ""
    }
    """

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    zipcode = data.get("zipcode", "").strip()
    address = data.get("address", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    password_check = data.get("password_check", "").strip()

    # 必須チェック
    if check_name and (not name or not email):
        return "名前・メールは必須です"
    
    if check_zipcode and not zipcode:
        return "郵便番号を入力してください"

    if check_zipcode and (not zipcode.isdigit() or len(zipcode) != 7):
        return "郵便番号は7桁の数字で入力してください"

    # zipcloud API で存在チェック
    url = f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zipcode}"
    res = requests.get(url).json()

    if check_zipcode and res["results"] is None:
        return "存在しない郵便番号です"

    if check_zipcode and not address:
        return "住所が空欄です。郵便番号を入れて検索ボタンを押してください"
    
    # パスワード必須チェック
    if check_password and not password:
        return "パスワードは必須です"
    
    # メール形式チェック
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, email):
        return "メールアドレスの形式が正しくありません"

    # メール重複チェック（登録時のみ）
    if check_email_duplicate:
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != current_user_id:
            return "このメールアドレスは既に登録されています"

    # パスワード強度チェック
    if check_password and len(password) < 3:
        return "パスワードは3文字以上で入力してください"

    # 新パスワード一致チェック
    if check_password and (password != password_check):
        return "新しいパスワードが一致しません"

    # 電話番号が空欄なら完全にスルー
    if phone:
        # ハイフン除去
        phone_clean = phone.replace("-", "")

        # 数字チェック
        if not phone_clean.isdigit():
            return "電話番号は数字とハイフンのみで入力してください"

        # 桁数チェック（任意）
        if not (10 <= len(phone_clean) <= 11):
            return "電話番号は10桁または11桁で入力してください"

    # 住所チェック
    if len(address) > 200:
        return "住所が長すぎます"

    return None  # 問題なし

def validate_user_pw_input(data, pw, check_current=True):

    # 現行パスワードチェック
    if check_current:
        if not check_password_hash(data["password"], pw.get("pw_current", "")):
            return "現在のパスワードが正しくありません"

    # 新パスワード一致チェック
    if pw["pw_new"] != pw["pw_check"]:
        return "新しいパスワードが一致しません"

    # パスワード強度チェック
    if len(pw["pw_new"]) < 3:
        return "パスワードは3文字以上で入力してください"

    # 現行と同じ禁止
    if check_password_hash(data["password"], pw["pw_new"]):
        return "新しいパスワードが現在のパスワードと同じです"

    return None