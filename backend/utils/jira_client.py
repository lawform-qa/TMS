"""
JIRA API 클라이언트
실제 JIRA API와 Mock JIRA 서버 모두 지원
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class JiraClient:
    """JIRA API 클라이언트"""
    
    def __init__(self, server_url: str = None, username: str = None, api_token: str = None):
        """
        JIRA 클라이언트 초기화
        
        Args:
            server_url: JIRA 서버 URL (기본값: Mock 서버)
            username: JIRA 사용자명
            api_token: JIRA API 토큰
        """
        self.server_url = server_url or os.getenv('JIRA_SERVER_URL', 'http://localhost:5004')
        self.username = username or os.getenv('JIRA_USERNAME', 'admin')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN', 'mock-token')
        
        # 세션 설정
        self.session = requests.Session()
        self.session.auth = (self.username, self.api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # 기본 프로젝트 키
        self.default_project_key = os.getenv('JIRA_PROJECT_KEY', 'TEST')
        self.default_issue_type = os.getenv('JIRA_DEFAULT_ISSUE_TYPE', 'Task')
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """JIRA API 요청 실행"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"JIRA API 요청 실패: {e}")
    
    def health_check(self) -> Dict:
        """JIRA 서버 상태 확인"""
        try:
            response = self._make_request('GET', '/health')
            return {
                'status': 'healthy',
                'server_url': self.server_url,
                'response': response
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'server_url': self.server_url,
                'error': str(e)
            }
    
    def get_projects(self) -> List[Dict]:
        """JIRA 프로젝트 목록 조회"""
        response = self._make_request('GET', '/rest/api/3/project')
        return response
    
    def get_project(self, project_key: str) -> Dict:
        """특정 프로젝트 정보 조회"""
        response = self._make_request('GET', f'/rest/api/3/project/{project_key}')
        return response
    
    def create_issue(self, summary: str, description: str = "", issue_type: str = None, 
                    priority: str = "Medium", project_key: str = None) -> Dict:
        """
        JIRA 이슈 생성
        
        Args:
            summary: 이슈 제목
            description: 이슈 설명
            issue_type: 이슈 타입 (Bug, Task, Story, Epic)
            priority: 우선순위 (Low, Medium, High, Critical)
            project_key: 프로젝트 키
            
        Returns:
            생성된 이슈 정보
        """
        project_key = project_key or self.default_project_key
        issue_type = issue_type or self.default_issue_type
        
        issue_data = {
            'fields': {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
        }
        
        return self._make_request('POST', '/rest/api/3/issue', data=issue_data)
    
    def get_issue(self, issue_key: str) -> Dict:
        """JIRA 이슈 조회"""
        return self._make_request('GET', f'/rest/api/3/issue/{issue_key}')
    
    def update_issue(self, issue_key: str, **kwargs) -> Dict:
        """
        JIRA 이슈 업데이트
        
        Args:
            issue_key: 이슈 키
            **kwargs: 업데이트할 필드들 (summary, description, status, priority, issue_type)
        """
        update_data = {'fields': {}}
        
        # 필드 매핑
        field_mapping = {
            'summary': 'summary',
            'description': 'description',
            'status': 'status',
            'priority': 'priority',
            'issue_type': 'issuetype',
            'labels': 'labels'
        }
        
        for key, value in kwargs.items():
            if key in field_mapping:
                field_name = field_mapping[key]
                if key == 'status':
                    update_data['fields'][field_name] = {'name': value}
                elif key == 'priority':
                    update_data['fields'][field_name] = {'name': value}
                elif key == 'issue_type':
                    update_data['fields'][field_name] = {'name': value}
                else:
                    update_data['fields'][field_name] = value
        
        return self._make_request('PUT', f'/rest/api/3/issue/{issue_key}', data=update_data)
    
    def add_comment(self, issue_key: str, comment: str) -> Dict:
        """
        JIRA 이슈에 댓글 추가
        
        Args:
            issue_key: 이슈 키
            comment: 댓글 내용
            
        Returns:
            추가된 댓글 정보
        """
        comment_data = {'body': comment}
        return self._make_request('POST', f'/rest/api/3/issue/{issue_key}/comment', data=comment_data)
    
    def get_comments(self, issue_key: str) -> List[Dict]:
        """이슈 댓글 목록 조회"""
        endpoint = f"/rest/api/3/issue/{issue_key}/comment"
        response = self._make_request('GET', endpoint)
        return response.get('comments', [])
    
    def search_issues(self, jql: str = "", start_at: int = 0, max_results: int = 50) -> Dict:
        """
        JQL을 사용한 이슈 검색
        
        Args:
            jql: JQL 쿼리
            start_at: 시작 인덱스
            max_results: 최대 결과 수
            
        Returns:
            검색 결과
        """
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': max_results
        }
        return self._make_request('GET', '/rest/api/3/search', params=params)


class JiraIntegrationService:
    """JIRA 연동 서비스"""
    
    def __init__(self, jira_client: JiraClient):
        self.jira_client = jira_client
    
    def create_issue_from_test_case(self, test_case_id: int, test_case_name: str, 
                                  test_case_description: str = "") -> Dict:
        """
        테스트 케이스에서 JIRA 이슈 생성
        
        Args:
            test_case_id: 테스트 케이스 ID
            test_case_name: 테스트 케이스 이름
            test_case_description: 테스트 케이스 설명
            
        Returns:
            생성된 이슈 정보
        """
        summary = f"[테스트 케이스] {test_case_name}"
        description = f"테스트 케이스 ID: {test_case_id}\n\n{test_case_description}"
        
        return self.jira_client.create_issue(
            summary=summary,
            description=description,
            issue_type="Task",
            priority="Medium"
        )
    
    def create_issue_from_automation_test(self, automation_test_id: int, 
                                        automation_test_name: str, 
                                        automation_test_description: str = "") -> Dict:
        """
        자동화 테스트에서 JIRA 이슈 생성
        
        Args:
            automation_test_id: 자동화 테스트 ID
            automation_test_name: 자동화 테스트 이름
            automation_test_description: 자동화 테스트 설명
            
        Returns:
            생성된 이슈 정보
        """
        summary = f"[자동화 테스트] {automation_test_name}"
        description = f"자동화 테스트 ID: {automation_test_id}\n\n{automation_test_description}"
        
        return self.jira_client.create_issue(
            summary=summary,
            description=description,
            issue_type="Task",
            priority="Medium"
        )
    
    def create_issue_from_performance_test(self, performance_test_id: int, 
                                         performance_test_name: str, 
                                         performance_test_description: str = "") -> Dict:
        """
        성능 테스트에서 JIRA 이슈 생성
        
        Args:
            performance_test_id: 성능 테스트 ID
            performance_test_name: 성능 테스트 이름
            performance_test_description: 성능 테스트 설명
            
        Returns:
            생성된 이슈 정보
        """
        summary = f"[성능 테스트] {performance_test_name}"
        description = f"성능 테스트 ID: {performance_test_id}\n\n{performance_test_description}"
        
        return self.jira_client.create_issue(
            summary=summary,
            description=description,
            issue_type="Task",
            priority="Medium"
        )
    
    def sync_issue_status(self, jira_integration_id: int) -> bool:
        """
        JIRA 이슈 상태 동기화
        
        Args:
            jira_integration_id: JIRA 연동 ID
            
        Returns:
            동기화 성공 여부
        """
        # 이 부분은 실제 데이터베이스 연동이 필요하므로
        # 나중에 구현 예정
        pass