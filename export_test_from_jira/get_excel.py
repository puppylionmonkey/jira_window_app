from pathlib import Path

import pandas as pd

from export_test_from_jira.get_api_jira_test import *
from export_test_from_jira.repo import test_id_lipped_repo_dict
from path_config import project_path


def jira_test_csv_to_import_csv(issue_id, account='', jira_api_token=''):
    # --- 自動獲取 Windows 使用者的下載資料夾 ---
    downloads_path = Path.home() / "Downloads"
    # 組合完整的儲存路徑
    final_save_path = downloads_path / f"{issue_id}_importer.csv"

    target_columns = [
        'Test Repo', 'Issue Id', 'Issue key', 'Test type', 'Test Summary',
        'Test Priority', 'Action', 'Data', 'Expected Result', 'Links',
        'Description', 'Unstructured', 'definition'
    ]

    df = pd.read_csv(f'{downloads_path}/{issue_id}.csv')
    print(df['Expected Result'], 'abc1')
    df = df.reindex(columns=target_columns)
    df = df.astype(object)  # 強制整張表轉為 object 型別
    print(df['Expected Result'], 'abc2')

    df = df.rename(columns={
        'Action': 'Action',
        'Data': 'Data',
        'Expected Result': 'Result'
    })
    df = df.reindex(columns=target_columns)
    print(df['Result'], 'abc3')

    test_summary = get_test_summary_from_jira_api(issue_id, account, jira_api_token)
    story_list = get_issue_links(issue_id, account, jira_api_token)

    df.at[0, 'Test Repo'] = test_id_lipped_repo_dict.get(issue_id, '')
    df.at[0, 'Test Summary'] = test_summary
    df.at[0, 'Issue key'] = issue_id
    df['Test type'] = 'Manual'
    df.at[0, 'Test Priority'] = 'Medium'
    df.at[0, 'Links'] = ';'.join(story_list)
    df.to_csv(final_save_path, index=False)


jira_test_csv_to_import_csv(issue_id='PBPM-25818')
