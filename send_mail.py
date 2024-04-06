#https://qiita.com/Nats72/items/b5ca98c5fe1c41551a8e のコピペ
#https://qiita.com/eito_2/items/ef77e44955e43f31ba78 ここも問題解決に役立った
#https://note.com/noa813/n/nde0116fcb03f これが最新の内容
#アプリパスワードとメールのパスワードは別物！
import smtplib
from email.mime.text import MIMEText
import json

def send_gmail(mail_from, mail_to, mail_subject, mail_body):

    """ メッセージのオブジェクト """
    msg = MIMEText(mail_body, "plain", "utf-8")
    msg['Subject'] = mail_subject
    msg['From'] = mail_from
    msg['To'] = mail_to

    # エラーキャッチ
    try:
        """ SMTPメールサーバーに接続 """
        smtpobj = smtplib.SMTP('smtp.gmail.com', 587)  # SMTPオブジェクトを作成。smtp.gmail.comのSMTPサーバーの587番ポートを設定。
        smtpobj.ehlo()                                 # SMTPサーバとの接続を確立
        smtpobj.starttls()                             # TLS暗号化通信開始
        gmail_addr = "yuruyurusearch@gmail.com"       # Googleアカウント(このアドレスをFromにして送られるっぽい)
        app_passwd = "bpri yddj jnna lkex"    # アプリパスワード
        smtpobj.login(gmail_addr, app_passwd)          # SMTPサーバーへログイン

        """ メール送信 """
        smtpobj.sendmail(mail_from, mail_to, msg.as_string())

        """ SMTPサーバーとの接続解除 """
        smtpobj.quit()

    except Exception as e:
        print(e)
    
    return "メール送信完了"


# 直接起動の場合はこちらの関数を実行
if __name__== "__main__":

    """ メール設定 """
    mail_from = "yuruyurusearch@gmail.com"       # 送信元アドレス
    mail_to = "yuruyurusearch@gmail.com"         # 送信先アドレス(To)
    mail_subject = "件名"                   # メール件名
    mail_body = "本文"                      # メール本文

    """ send_gmail関数実行 """
    result = send_gmail(mail_from, mail_to, mail_subject, mail_body)
    print(result)