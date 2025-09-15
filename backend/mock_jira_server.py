#!/usr/bin/env python3
"""
Mock JIRA Server
실제 JIRA API와 동일한 인터페이스를 제공하는 Mock 서버
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import uuid
import random
import requests
import os

app = Flask(__name__)

# Mock 데이터 저장소
mock_issues = {}
mock_projects = {
    'TEST': {
        'id': '10000',
        'key': 'TEST',
        'name': 'Test Project',
        'projectTypeKey': 'software'
    }
}

# 이슈 카운터
issue_counter = 1

# 백엔드 API URL
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000')

def sync_issues_from_database():
    """데이터베이스에서 기존 이슈들을 가져와서 Mock 서버에 로드"""
    try:
        print("🔄 데이터베이스에서 기존 이슈들을 동기화 중...")
        
        # 백엔드 API에서 이슈 목록 가져오기
        response = requests.get(f"{BACKEND_API_URL}/api/jira/issues", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                issues = data['data'].get('issues', [])
                
                print(f"📋 {len(issues)}개의 기존 이슈를 발견했습니다.")
                
                for issue in issues:
                    issue_key = issue.get('jira_issue_key')
                    if issue_key:
                        # Mock 이슈 데이터 생성
                        mock_issue = {
                            'id': str(uuid.uuid4()),
                            'key': issue_key,
                            'self': f"https://mock-jira.atlassian.net/rest/api/3/issue/{issue_key}",
                            'fields': {
                                'summary': issue.get('summary', ''),
                                'description': issue.get('description', ''),
                                'issuetype': {
                                    'id': '10001',
                                    'name': issue.get('issue_type', 'Task'),
                                    'iconUrl': f"https://mock-jira.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10318&avatarType=issuetype"
                                },
                                'priority': {
                                    'id': '3',
                                    'name': issue.get('priority', 'Medium')
                                },
                                'status': {
                                    'id': '10000',
                                    'name': issue.get('status', 'To Do'),
                                    'statusCategory': {
                                        'id': 2,
                                        'key': 'new' if issue.get('status') == 'To Do' else 'in-progress',
                                        'colorName': 'blue-gray' if issue.get('status') == 'To Do' else 'yellow'
                                    }
                                },
                                'project': {
                                    'id': '10000',
                                    'key': 'TEST',
                                    'name': 'Test Project'
                                },
                                'reporter': {
                                    'accountId': 'admin',
                                    'displayName': 'Admin User',
                                    'emailAddress': 'admin@example.com'
                                },
                                'assignee': {
                                    'accountId': issue.get('assignee'),
                                    'displayName': f"User {issue.get('assignee')}",
                                    'emailAddress': issue.get('assignee')
                                } if issue.get('assignee') else None,
                                'labels': json.loads(issue.get('labels', '[]')) if issue.get('labels') else [],
                                'created': issue.get('created_at', datetime.now().isoformat() + 'Z'),
                                'updated': issue.get('updated_at', datetime.now().isoformat() + 'Z'),
                                'components': [],
                                'fixVersions': [],
                                'versions': []
                            }
                        }
                        
                        mock_issues[issue_key] = mock_issue
                        print(f"  ✅ {issue_key}: {issue.get('summary', 'No title')}")
                
                # 이슈 카운터 업데이트
                global issue_counter
                if issues:
                    max_issue_num = max([int(issue.get('jira_issue_key', 'TEST-0').split('-')[1]) for issue in issues if issue.get('jira_issue_key', '').startswith('TEST-')])
                    issue_counter = max_issue_num + 1
                
                print(f"✅ 데이터베이스 동기화 완료! 다음 이슈 번호: {issue_counter}")
            else:
                print("⚠️ 데이터베이스에서 이슈를 가져올 수 없습니다.")
        else:
            print(f"⚠️ 백엔드 API 연결 실패: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ 백엔드 서버가 실행되지 않았습니다. 데이터베이스 동기화를 건너뜁니다.")
    except Exception as e:
        print(f"⚠️ 데이터베이스 동기화 중 오류 발생: {str(e)}")

def generate_issue_key(project_key):
    global issue_counter
    issue_key = f"{project_key}-{issue_counter}"
    issue_counter += 1
    return issue_key

def create_mock_issue(project_key, summary, description, issue_type, **kwargs):
    """Mock 이슈 생성"""
    issue_id = str(uuid.uuid4())
    issue_key = generate_issue_key(project_key)
    
    issue = {
        'id': issue_id,
        'key': issue_key,
        'self': f"https://mock-jira.atlassian.net/rest/api/3/issue/{issue_id}",
        'fields': {
            'summary': summary,
            'description': description,
            'issuetype': {
                'id': '10001',
                'name': issue_type,
                'iconUrl': f"https://mock-jira.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10318&avatarType=issuetype"
            },
            'project': {
                'id': mock_projects[project_key]['id'],
                'key': project_key,
                'name': mock_projects[project_key]['name']
            },
            'status': {
                'id': '10000',
                'name': 'To Do',
                'statusCategory': {
                    'id': 2,
                    'key': 'new',
                    'colorName': 'blue-gray'
                }
            },
            'priority': {
                'id': '3',
                'name': kwargs.get('priority', 'Medium')
            },
            'assignee': None,
            'reporter': {
                'accountId': 'admin',
                'displayName': 'Admin User',
                'emailAddress': 'admin@example.com'
            },
            'created': datetime.now().isoformat() + 'Z',
            'updated': datetime.now().isoformat() + 'Z',
            'labels': kwargs.get('labels', []),
            'components': [],
            'fixVersions': [],
            'versions': []
        }
    }
    
    # 추가 필드 설정
    if 'assignee' in kwargs and kwargs['assignee']:
        issue['fields']['assignee'] = {
            'accountId': kwargs['assignee'],
            'displayName': f"User {kwargs['assignee']}",
            'emailAddress': f"user{kwargs['assignee']}@example.com"
        }
    
    mock_issues[issue_key] = issue
    return issue

@app.route('/rest/api/3/issue', methods=['POST'])
def create_issue():
    """이슈 생성 API"""
    try:
        data = request.get_json()
        
        fields = data.get('fields', {})
        project_key = fields.get('project', {}).get('key')
        summary = fields.get('summary')
        description = fields.get('description', '')
        issue_type = fields.get('issuetype', {}).get('name', 'Task')
        
        if not project_key or not summary:
            return jsonify({
                'errorMessages': ['Project key and summary are required'],
                'errors': {}
            }), 400
        
        if project_key not in mock_projects:
            return jsonify({
                'errorMessages': [f'Project {project_key} does not exist'],
                'errors': {}
            }), 400
        
        # 이슈 생성
        issue = create_mock_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=fields.get('priority', {}).get('name', 'Medium'),
            assignee=fields.get('assignee', {}).get('accountId'),
            labels=fields.get('labels', [])
        )
        
        return jsonify(issue), 201
        
    except Exception as e:
        return jsonify({
            'errorMessages': [str(e)],
            'errors': {}
        }), 500

@app.route('/rest/api/3/issue/<issue_key>', methods=['GET'])
def get_issue(issue_key):
    """이슈 조회 API"""
    if issue_key not in mock_issues:
        return jsonify({
            'errorMessages': [f'Issue {issue_key} does not exist'],
            'errors': {}
        }), 404
    
    return jsonify(mock_issues[issue_key])

@app.route('/rest/api/3/issue/<issue_key>', methods=['PUT'])
def update_issue(issue_key):
    """이슈 업데이트 API"""
    if issue_key not in mock_issues:
        return jsonify({
            'errorMessages': [f'Issue {issue_key} does not exist'],
            'errors': {}
        }), 404
    
    try:
        data = request.get_json()
        fields = data.get('fields', {})
        
        # 이슈 업데이트
        issue = mock_issues[issue_key]
        
        if 'summary' in fields:
            issue['fields']['summary'] = fields['summary']
        if 'description' in fields:
            issue['fields']['description'] = fields['description']
        if 'status' in fields:
            issue['fields']['status'] = {
                'id': '10001',
                'name': fields['status']['name'],
                'statusCategory': {
                    'id': 2,
                    'key': 'in-progress' if fields['status']['name'] == 'In Progress' else 'done',
                    'colorName': 'yellow' if fields['status']['name'] == 'In Progress' else 'green'
                }
            }
        if 'assignee' in fields:
            if fields['assignee']:
                issue['fields']['assignee'] = {
                    'accountId': fields['assignee']['accountId'],
                    'displayName': f"User {fields['assignee']['accountId']}",
                    'emailAddress': f"user{fields['assignee']['accountId']}@example.com"
                }
            else:
                issue['fields']['assignee'] = None
        
        if 'labels' in fields:
            issue['fields']['labels'] = fields['labels']
        
        issue['fields']['updated'] = datetime.now().isoformat() + 'Z'
        
        return jsonify(issue)
        
    except Exception as e:
        return jsonify({
            'errorMessages': [str(e)],
            'errors': {}
        }), 500

@app.route('/rest/api/3/issue/<issue_key>/comment', methods=['POST'])
def add_comment(issue_key):
    """이슈에 댓글 추가 API"""
    if issue_key not in mock_issues:
        return jsonify({
            'errorMessages': [f'Issue {issue_key} does not exist'],
            'errors': {}
        }), 404
    
    try:
        data = request.get_json()
        comment_id = str(uuid.uuid4())
        
        comment = {
            'id': comment_id,
            'self': f"https://mock-jira.atlassian.net/rest/api/3/issue/{issue_key}/comment/{comment_id}",
            'author': {
                'accountId': 'admin',
                'displayName': 'Admin User',
                'emailAddress': 'admin@example.com'
            },
            'body': data.get('body', ''),
            'created': datetime.now().isoformat() + 'Z',
            'updated': datetime.now().isoformat() + 'Z'
        }
        
        # 댓글을 이슈에 추가 (실제로는 별도 저장소에 저장)
        if 'comments' not in mock_issues[issue_key]['fields']:
            mock_issues[issue_key]['fields']['comments'] = []
        mock_issues[issue_key]['fields']['comments'].append(comment)
        
        return jsonify(comment), 201
    
    except Exception as e:
        return jsonify({
            'errorMessages': [str(e)],
            'errors': {}
        }), 500

@app.route('/rest/api/3/issue/<issue_key>/comment', methods=['GET'])
def get_comments(issue_key):
    """이슈 댓글 목록 조회 API"""
    if issue_key not in mock_issues:
        return jsonify({
            'errorMessages': [f'Issue {issue_key} does not exist'],
            'errors': {}
        }), 404
    
    try:
        comments = mock_issues[issue_key]['fields'].get('comments', [])
        return jsonify({
            'comments': comments,
            'maxResults': len(comments),
            'total': len(comments),
            'startAt': 0
        })
    
    except Exception as e:
        return jsonify({
            'errorMessages': [str(e)],
            'errors': {}
        }), 500

@app.route('/rest/api/3/search', methods=['GET'])
def search_issues():
    """이슈 검색 API (JQL)"""
    try:
        jql = request.args.get('jql', '')
        start_at = int(request.args.get('startAt', 0))
        max_results = int(request.args.get('maxResults', 50))
        
        # 간단한 JQL 파싱 (실제로는 더 복잡한 파서 필요)
        filtered_issues = []
        
        for issue_key, issue in mock_issues.items():
            if not jql or 'project' in jql.lower():
                filtered_issues.append(issue)
        
        # 페이지네이션
        total = len(filtered_issues)
        issues = filtered_issues[start_at:start_at + max_results]
        
        return jsonify({
            'expand': 'schema,names',
            'startAt': start_at,
            'maxResults': max_results,
            'total': total,
            'issues': issues
        })
        
    except Exception as e:
        return jsonify({
            'errorMessages': [str(e)],
            'errors': {}
        }), 500

@app.route('/rest/api/3/project', methods=['GET'])
def get_projects():
    """JIRA 프로젝트 목록 조회 API"""
    return jsonify(list(mock_projects.values()))

@app.route('/rest/api/3/project/<project_key>', methods=['GET'])
def get_project(project_key):
    """JIRA 프로젝트 조회 API"""
    if project_key not in mock_projects:
        return jsonify({
            'errorMessages': [f'Project {project_key} does not exist'],
            'errors': {}
        }), 404
    
    return jsonify(mock_projects[project_key])

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'issues_count': len(mock_issues),
        'projects_count': len(mock_projects)
    })

@app.route('/', methods=['GET'])
def index():
    """Mock JIRA 서버 정보"""
    return jsonify({
        'name': 'Mock JIRA Server',
        'version': '1.0.0',
        'description': 'Mock JIRA API server for development',
        'endpoints': [
            'POST /rest/api/3/issue - Create issue',
            'GET /rest/api/3/issue/{issueKey} - Get issue',
            'PUT /rest/api/3/issue/{issueKey} - Update issue',
            'POST /rest/api/3/issue/{issueKey}/comment - Add comment',
            'GET /rest/api/3/search - Search issues',
            'GET /rest/api/3/project - List projects',
            'GET /rest/api/3/project/{projectKey} - Get project',
            'GET /health - Health check'
        ]
    })

if __name__ == '__main__':
    print("🚀 Mock JIRA Server starting...")
    print("📋 Available endpoints:")
    print("   POST /rest/api/3/issue - Create issue")
    print("   GET /rest/api/3/issue/{issueKey} - Get issue")
    print("   PUT /rest/api/3/issue/{issueKey} - Update issue")
    print("   POST /rest/api/3/issue/{issueKey}/comment - Add comment")
    print("   GET /rest/api/3/search - Search issues")
    print("   GET /rest/api/3/project - List projects")
    print("   GET /health - Health check")
    print("\n🌐 Server will run on http://localhost:5004")
    
    # 서버 시작 전 데이터베이스 동기화
    sync_issues_from_database()
    
    app.run(host='0.0.0.0', port=5004, debug=True)
