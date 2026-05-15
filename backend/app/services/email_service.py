from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText


class EmailService:
    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_pass = os.getenv("SMTP_PASS", "").strip()
        self.sender_name = os.getenv("SMTP_SENDER_NAME", "AI教学助手")

    def send_code(self, to_email: str, code: str) -> None:
        if not self.smtp_user or not self.smtp_pass:
            raise ValueError("SMTP 未配置，请设置 SMTP_USER/SMTP_PASS")

        subject = "AI教学助手注册验证码"
        body = f"您的验证码为：{code}，5分钟内有效。若非本人操作请忽略。"

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.smtp_user}>"
        msg["To"] = to_email

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10) as server:
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, [to_email], msg.as_string())
