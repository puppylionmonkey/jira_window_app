import requests
from requests.auth import HTTPBasicAuth



def verify_jira_login(account, jira_api_token):
    """真正的 Jira API 驗證邏輯"""
    # 使用使用者輸入的網域前綴
    JIRA_DOMAIN = "m3maintain"
    domain = f"https://{JIRA_DOMAIN}.atlassian.net"
    url = f"{domain}/rest/api/3/myself"
    auth = HTTPBasicAuth(account, jira_api_token)

    try:
        # 增加 timeout 避免程式卡死
        response = requests.get(url, auth=auth, timeout=5)
        if response.status_code == 200:
            return True, "驗證成功"
        elif response.status_code == 401:
            return False, "驗證失敗：帳號或 Token 錯誤"
        elif response.status_code == 404:
            return False, "驗證失敗：找不到該 Jira 網域"
        else:
            return False, f"連線錯誤：{response.status_code}"
    except Exception as e:
        return False, f"連線異常: {str(e)}"


def get_test_summary_from_jira_api(issue_id, account, jira_api_token):
    JIRA_DOMAIN = "m3maintain"
    url = f"https://{JIRA_DOMAIN}.atlassian.net/rest/api/3/issue/{issue_id}"

    auth = HTTPBasicAuth(account, jira_api_token)

    headers = {
        "Accept": "application/json"
    }

    query = {
        'fields': 'summary,issuelinks'
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth,
        params=query
    )

    data = response.json()

    # 提取資訊
    summary = data['fields']['summary']
    return summary


def get_issue_links(issue_id, account, jira_api_token):
    JIRA_DOMAIN = "m3maintain"
    url = f"https://{JIRA_DOMAIN}.atlassian.net/rest/api/3/issue/{issue_id}"

    auth = HTTPBasicAuth(account, jira_api_token)

    headers = {
        "Accept": "application/json"
    }

    query = {
        'fields': 'summary,issuelinks'
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth,
        params=query
    )

    data = response.json()
    # 提取關聯的 Issue Links
    links = data['fields'].get('issuelinks', [])
    link_list = [link['outwardIssue']['key'] for link in links if 'outwardIssue' in link]
    return link_list
