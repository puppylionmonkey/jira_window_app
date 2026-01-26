import asyncio
import sys
from pathlib import Path

# 1. 必須使用 async_api
from playwright.async_api import async_playwright
from path_config import project_path


# 2. 函式已經是 async def 沒錯
async def export_test_steps_from_jira(test_id_list, account, password):
    # 3. 必須使用 async_playwright()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="./_internal/ms-playwright/chromium-1200/chrome-win64/chrome.exe",
            headless=False
        )
        # browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = 'https://m3maintain.atlassian.net/jira/software/c/projects/PBPM/boards/29'

        await page.goto(url)
        # 5. 填寫、點擊等動作都要 await
        await page.get_by_placeholder('輸入您的電子郵件').fill(account)
        await page.get_by_text('繼續', exact=True).click()
        await page.get_by_placeholder('輸入密碼').fill(password)
        await page.get_by_text('登入', exact=True).click()

        # 等待網址跳轉
        await page.wait_for_url("**/jira/software/**", timeout=60000)

        for issue_id in test_id_list:
            print(f"正在處理: {issue_id}")
            test_url = f'https://m3maintain.atlassian.net/browse/{issue_id}'
            await page.goto(test_url)

            # 等待元素出現也要 await
            await page.get_by_text('工作時間記錄').first.wait_for(timeout=30000)
            expand_button = page.get_by_text('摺疊側邊欄')
            if await expand_button.is_visible():
                await expand_button.click()

            xray_frame = page.frame_locator('xpath=//iframe[contains(@id, "xray-test-details")]')
            await xray_frame.get_by_text('Export').click()

            # 在 async 環境中不要用 time.sleep，改用 asyncio.sleep 避免卡死 UI
            await asyncio.sleep(0.5)
            await xray_frame.get_by_text('To csv').click()

            xray_export_frame = page.frame_locator('xpath=//iframe[contains(@id, "xray__manual-export-csv")]')
            await xray_export_frame.get_by_text('Attachment links').first.wait_for(timeout=30000)

            # 下載邏輯在 async 中要這樣寫
            async with page.expect_download(timeout=60000) as download_info:
                await page.get_by_role("button", name="Export").click()

            downloads_path = Path.home() / "Downloads"
            # 組合完整的儲存路徑
            final_save_path = downloads_path / f"{issue_id}.csv"
            download = await download_info.value

            # 儲存檔案也要 await
            await download.save_as(final_save_path)
            print(f"檔案已儲存至: {final_save_path}")

        await browser.close()

# asyncio.run(export_test_steps_from_jira(['PBPM-23566'], account, password))
