#!/usr/bin/env python3
"""
간단한 브랜치별 데이터베이스 설정
- MAIN: test_management_main
- ALPHA + 로컬: test_management_alpha
"""

import os
from dotenv import load_dotenv

load_dotenv()

def setup_branch(branch_name):
    """브랜치별 데이터베이스 설정"""
    
    # AWS RDS 기본 정보
    host = 'test-management-db2.c3ago8cqsq3j.ap-southeast-2.rds.amazonaws.com'
    user = 'admin'
    password = 'Si1vesterl!#'
    port = 3306
    
    # 데이터베이스 선택
    if branch_name == 'main':
        database = 'test_management_main'
    else:  # alpha 또는 기타
        database = 'test_management_alpha'
    
    # 데이터베이스 URL 생성
    database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    # .env 파일 업데이트
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # MYSQL_DATABASE_URL 업데이트
    updated_lines = []
    mysql_url_updated = False
    
    for line in lines:
        if line.startswith('MYSQL_DATABASE_URL='):
            updated_lines.append(f'MYSQL_DATABASE_URL={database_url}\n')
            mysql_url_updated = True
        else:
            updated_lines.append(line)
    
    # MYSQL_DATABASE_URL이 없으면 추가
    if not mysql_url_updated:
        updated_lines.append(f'MYSQL_DATABASE_URL={database_url}\n')
    
    # .env 파일 쓰기
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ {branch_name} 브랜치 설정 완료")
    print(f"📋 데이터베이스: {database}")
    print(f"🔗 URL: {database_url}")

def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) != 2:
        print("사용법: python simple_branch_setup.py <브랜치명>")
        print("예시: python simple_branch_setup.py main")
        print("예시: python simple_branch_setup.py alpha")
        sys.exit(1)
    
    branch_name = sys.argv[1]
    setup_branch(branch_name)

if __name__ == "__main__":
    main()
