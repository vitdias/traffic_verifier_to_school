from __future__ import annotations

import subprocess


def send_android_notification(title: str, content: str, notification_id: int) -> None:
    subprocess.run(
        [
            "termux-notification",
            "--id",
            str(notification_id),
            "--title",
            title,
            "--content",
            content,
            "--priority",
            "high",
            "--sound",
            "--vibrate",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
