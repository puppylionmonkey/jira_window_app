import csv
import flet as ft
import asyncio
import tkinter as tk
from tkinter import filedialog

# 確保這些自定義函式路徑正確
from export_test_from_jira.export_test_steps_from_jira import export_test_steps_from_jira
from export_test_from_jira.get_api_jira_test import verify_jira_login
from export_test_from_jira.get_excel import jira_test_csv_to_import_csv


async def main(page: ft.Page):
    # 1. 基礎設定與 Session 資料儲存
    session_data = {
        "account": "",
        "password": "",
        "token": ""
    }

    page.title = "Jira Test Downloader"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="blue")
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def show_snack(message):
        snack = ft.SnackBar(ft.Text(message))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- 頁面 2: 下載面板 ---
    async def go_to_downloader_page():
        issue_id_input = ft.TextField(
            label="Issue ID (單個或批次匯入)",
            hint_text="例如: PBPM-23583",
            width=320,
            text_align=ft.TextAlign.CENTER,
            prefix_icon=ft.Icons.TAG
        )

        # 內部狀態：儲存 CSV 匯入的 ID 列表
        imported_issues = []

        # 使用 tkinter 替代 Flet FilePicker，徹底解決 Unknown control 錯誤
        async def import_csv_click(e):
            try:
                # 建立隱藏的 tkinter 根視窗
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)  # 確保視窗跳到最前面

                # 開啟原生選取視窗
                file_path = filedialog.askopenfilename(
                    title="選擇包含 Issue ID 的 CSV 檔案",
                    filetypes=[("CSV Files", "*.csv")]
                )

                root.destroy()  # 釋放 tkinter 資源

                if file_path:
                    temp_list = []
                    # utf-8-sig 處理 Excel 可能產生的 BOM 編碼
                    with open(file_path, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row and row[0].strip():
                                temp_list.append(row[0].strip())

                    if temp_list:
                        nonlocal imported_issues
                        imported_issues = temp_list
                        issue_id_input.value = f"已匯入 {len(imported_issues)} 個 ID"
                        issue_id_input.disabled = True
                        show_snack(f"成功讀取 {len(imported_issues)} 筆資料")
                        page.update()
            except Exception as ex:
                show_snack(f"讀取檔案失敗: {str(ex)}")

        async def start_download_logic(e):
            # 優先使用匯入清單，否則使用手動輸入
            targets = imported_issues if imported_issues else ([issue_id_input.value] if issue_id_input.value else [])
            print(targets)

            if not targets:
                show_snack("請輸入 ID 或匯入 CSV！")
                return

            e.control.disabled = True
            e.control.content = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white")
            page.update()

            try:
                for idx, issue_id in enumerate(targets):
                    show_snack(f"執行中 ({idx + 1}/{len(targets)}): {issue_id}")
                    # 呼叫業務邏輯
                    await export_test_steps_from_jira([issue_id], session_data["account"], session_data["password"])
                    jira_test_csv_to_import_csv(issue_id, session_data["account"], session_data["token"])

                show_snack("✅ 所有任務已完成！")
            except Exception as ex:
                show_snack(f"❌ 執行出錯: {str(ex)}")
            finally:
                # 重置狀態
                issue_id_input.value = ""
                issue_id_input.disabled = False
                imported_issues.clear()
                e.control.disabled = False
                e.control.content = ft.Text("開始執行任務", weight=ft.FontWeight.BOLD)
                page.update()

        # UI 佈局
        page.clean()
        page.add(
            ft.AppBar(title=ft.Text("Jira 下載面板"), center_title=True, bgcolor="surfacevariant"),
            ft.Column([
                ft.Container(height=20),
                issue_id_input,
                ft.Row([
                    ft.TextButton("匯入 CSV", icon=ft.Icons.UPLOAD_FILE, on_click=import_csv_click),
                    ft.TextButton("清空重置", icon=ft.Icons.REFRESH,
                                  on_click=lambda _: (setattr(issue_id_input, "value", ""),
                                                      setattr(issue_id_input, "disabled", False),
                                                      imported_issues.clear(), page.update())),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=30),
                ft.FilledButton(
                    content=ft.Text("下載", weight=ft.FontWeight.BOLD),
                    icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                    width=320, height=55,
                    on_click=start_download_logic
                ),
                ft.Container(height=10),
                ft.TextButton("返回登入頁面", on_click=lambda _: show_login_ui())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- 頁面 1: 登入頁面 ---
    async def show_login_ui():
        email_input = ft.TextField(label="Jira Email", width=320, prefix_icon=ft.Icons.EMAIL, value=session_data["account"])
        password_input = ft.TextField(label="Jira Password", password=True, can_reveal_password=True, width=320, prefix_icon=ft.Icons.LOCK, value=session_data["password"])
        token_input = ft.TextField(label="API Token", password=True, can_reveal_password=True, width=320, prefix_icon=ft.Icons.KEY, value=session_data["token"])

        async def login_click(e):
            if not email_input.value or not password_input.value or not token_input.value:
                show_snack("欄位不可為空！")
                return

            e.control.disabled = True
            e.control.content = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white")
            page.update()

            # 驗證 Jira 登入
            is_success, msg = verify_jira_login(email_input.value, token_input.value)

            if is_success:
                session_data["account"] = email_input.value
                session_data["password"] = password_input.value
                session_data["token"] = token_input.value
                await go_to_downloader_page()
            else:
                show_snack(msg)
                e.control.disabled = False
                e.control.content = ft.Text("登入", weight=ft.FontWeight.BOLD)
                page.update()

        page.clean()
        page.add(
            ft.Icon(ft.Icons.HUB_ROUNDED, size=80, color="blue400"),
            ft.Text("Jira 下載器", size=32, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            email_input,
            password_input,
            ft.Column([
                token_input,
                ft.TextButton("如何取得 API Token?", url="https://id.atlassian.com/manage-profile/security/api-tokens")
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.FilledButton(
                content=ft.Text("登入", weight=ft.FontWeight.BOLD),
                on_click=login_click,
                width=320, height=45
            )
        )
        page.update()

    # 執行進入點
    await show_login_ui()


if __name__ == "__main__":
    # 使用 ft.app 代替 ft.run 是較現代的寫法，能更好地管理 async 任務
    ft.run(main, assets_dir="assets")
