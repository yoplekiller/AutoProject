from jira import JIRA
from dotenv import load_dotenv
import os

load_dotenv()

# Jira 클라이언트 초기화
jira = JIRA(
    server=os.getenv("JIRA_URL"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
)   
# 조회할 프로젝트 키
project_key = os.getenv("JIRA_PROJECT_KEY")

# 프로젝트 티켓 목록 조회
issues = jira.search_issues(f"project={project_key} ORDER BY created DESC", maxResults=5)

print(f"=== [{project_key}] 최근 티켓 목록 ===")
for issue in issues:
    print(f"[{issue.key}] {issue.fields.summary} / 상태: {issue.fields.status.name}")
