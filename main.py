import flet as ft
import asyncio
# 確保你的 export 函式已經改為 async 定義
from export_test_from_jira.export_test_steps_from_jira import export_test_steps_from_jira
from export_test_from_jira.get_api_jira_test import verify_jira_login
from export_test_from_jira.get_excel import jira_test_csv_to_import_csv


# 將 main 改為 async def
async def main(page: ft.Page):
    session_data = {
        "account": "",
        "password": "",
        "token": ""
    }

    page.title = "Jira Test Downloader"
    page.window.width = 450
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="blue")

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def show_snack(message):
        snack = ft.SnackBar(ft.Text(message))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- 頁面 2: 下載頁面 ---
    async def go_to_downloader_page():
        issue_id_input = ft.TextField(
            label="Issue ID",
            hint_text="例如: PBPM-23583",
            width=320,
            text_align=ft.TextAlign.CENTER,
            prefix_icon=ft.Icons.TAG
        )

        # 核心修正：將下載邏輯改為 async
        async def start_download_logic(e):
            if not issue_id_input.value:
                show_snack("請輸入 Issue ID！")
                return

            # 下載期間禁用按鈕並顯示載入狀態
            e.control.disabled = True
            e.control.content = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white")
            page.update()

            account = session_data["account"]
            pwd = session_data["password"]
            token = session_data["token"]

            show_snack(f"正在透過 Playwright 下載 {issue_id_input.value}...")

            try:
                # 使用 await 呼叫非同步的 Playwright 邏輯
                issue_id = issue_id_input.value
                await export_test_steps_from_jira([issue_id], account, pwd)
                jira_test_csv_to_import_csv(issue_id, account, token)
                show_snack(f"{issue_id_input.value} 下載成功！")
            except Exception as ex:
                show_snack(f"下載失敗: {str(ex)}")
            finally:
                # 恢復按鈕狀態
                e.control.disabled = False
                e.control.content = ft.Text("執行 Playwright 下載", weight=ft.FontWeight.BOLD)
                page.update()

        page.clean()
        page.add(
            ft.AppBar(
                title=ft.Text("Jira 下載面板"),
                center_title=True,
                bgcolor="surfacevariant"
            ),
            ft.Column([
                ft.Container(height=20),
                ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, color="blue400", size=80),
                ft.Text("連線成功", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"登入帳號: {session_data['account']}", color="grey"),
                ft.Divider(height=40, thickness=1),
                issue_id_input,
                ft.Container(height=10),
                ft.FilledButton(
                    content=ft.Text("執行 Playwright 下載", weight=ft.FontWeight.BOLD),
                    icon=ft.Icons.PLAY_ARROW_ROUNDED,
                    width=320,
                    height=50,
                    on_click=start_download_logic  # Flet 會自動處理 async 回呼
                ),
                ft.TextButton("返回登入頁面", on_click=lambda _: asyncio.run(main(page)))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- 登入按鈕事件 ---
    async def login_click(e):
        if not email_input.value or not password_input.value or not token_input.value:
            show_snack("所有欄位皆為必填！")
            return

        login_btn.disabled = True
        login_btn.content = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white")
        page.update()

        # 如果 verify_jira_login 是同步的，可以直接呼叫；如果是 async 則加 await
        is_success, msg = verify_jira_login(email_input.value, token_input.value)

        if is_success:
            session_data["account"] = email_input.value
            session_data["password"] = password_input.value
            session_data["token"] = token_input.value
            await go_to_downloader_page()
        else:
            show_snack(msg)
            login_btn.disabled = False
            login_btn.content = ft.Text("登入", weight=ft.FontWeight.BOLD)
            page.update()

    # --- 登入介面 UI ---
    email_input = ft.TextField(label="Jira Email", width=320, prefix_icon=ft.Icons.EMAIL)
    password_input = ft.TextField(label="Jira Password", password=True, can_reveal_password=True, width=320, prefix_icon=ft.Icons.LOCK)
    token_input = ft.TextField(label="API Token", password=True, can_reveal_password=True, width=320, prefix_icon=ft.Icons.KEY)

    create_token_link = ft.TextButton(
        content=ft.Text("如何取得 API Token?", size=12, color="blue400"),
        url="https://id.atlassian.com/manage-profile/security/api-tokens"
    )

    login_btn = ft.FilledButton(
        content=ft.Text("登入", weight=ft.FontWeight.BOLD),
        on_click=login_click,
        width=320,
        height=45
    )

    page.clean()
    page.add(
        ft.Icon(ft.Icons.HUB_ROUNDED, size=80, color="blue400"),
        ft.Text("Jira 下載器", size=32, weight=ft.FontWeight.BOLD),
        ft.Container(height=10),
        email_input,
        password_input,
        ft.Column([token_input, create_token_link], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=10),
        login_btn
    )


if __name__ == "__main__":
    # 使用 assets_dir 指定一個空資料夾，強制 PyInstaller 捕捉路徑
    ft.run(main, assets_dir="assets")