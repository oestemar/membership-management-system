from flask_mail import Message
from flask import render_template_string
from datetime import datetime, timezone, timedelta
from webapp import db
from models import MailLog

def send_register_mail(user, mail):
    subject = "あいうえお美術館会員登録完了のお知らせ"
    body_template = """
{{ user.name }}様

この度は、あいうえお美術館の会員登録をいただき、誠に有難うございます。
以下の内容でユーザー登録が完了しました。

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
■登録情報
お名前：{{ user.name }}
メールアドレス：{{ user.email }}
登録日時：{{ user.created_at or '' }}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

今後とも当館を宜しくお願い致します。

あいうえお美術館会員管理システム
noreply.aiueosystem@gmail.com
"""

    body = render_template_string(body_template, user=user)
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    mail.send(msg)

    # ログ保存
    log = MailLog(
        user_id=user.id,
        mail_type="register",
        sent_at=datetime.now(timezone(timedelta(hours=9)))
    )
    db.session.add(log)
    db.session.commit()

def send_withdraw_mail(user, mail, withdrawn_at):
    subject = "あいうえお美術館退会手続き完了のお知らせ"
    body_template = """
{{ user.name }}様

この度は、あいうえお美術館の会員退会手続きを承りました。
以下の内容で退会処理が完了しました。

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
■退会情報
お名前：{{ user.name }}
退会日時：{{ withdrawn_at }}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

これまでご利用いただき、誠に有難うございました。
またのご利用を心よりお待ちしております。

あいうえお美術館会員管理システム
noreply.aiueosystem@gmail.com
"""

    body = render_template_string(body_template, user=user, withdrawn_at=withdrawn_at)
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    mail.send(msg)

    # ログ保存
    log = MailLog(
        user_id=user.id,
        mail_type="withdraw",
        sent_at=datetime.now(timezone(timedelta(hours=9)))
    )
    db.session.add(log)
    db.session.commit()

def send_password_reset_mail(user, reset_url, mail):
    subject = "あいうえお美術館：パスワードリセット手続き"
    body_template = """
{{ email }}様

あいうえお美術館のパスワードリセット手続きは下記リンクを開いて進めてください。

◆パスワードリセットURL
{{ reset_url }}


※1時間以内にパスワード更新作業を完了しないとキャンセルとなります。

あいうえお美術館会員管理システム
noreply.aiueosystem@gmail.com
"""

    body = render_template_string(body_template, email=user.email, reset_url=reset_url)

    msg = Message(subject, recipients=[user.email])
    msg.body = body
    mail.send(msg)

    # ログ保存
    log = MailLog(
        user_id=user.id,
        mail_type="password-reset",
        sent_at=datetime.now(timezone(timedelta(hours=9)))
    )
    db.session.add(log)
    db.session.commit()