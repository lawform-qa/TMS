"""
공통 헬퍼 함수들
"""
from flask import jsonify
from models import Project, Folder
from utils.cors import add_cors_headers
from utils.logger import get_logger

logger = get_logger(__name__)

def get_or_create_default_project():
    """기본 프로젝트 조회 또는 생성"""
    default_project = Project.query.filter_by(name='Test Management System').first()
    if not default_project:
        default_project = Project(
            name='Test Management System',
            description='기본 테스트 관리 시스템 프로젝트'
        )
        from models import db
        db.session.add(default_project)
        db.session.flush()  # ID 생성을 위해 flush
        logger.info(f"기본 프로젝트 생성됨: {default_project.name} (ID: {default_project.id})")
    return default_project

def get_or_create_default_folder():
    """기본 폴더 조회 또는 생성"""
    # DEV 환경의 첫 번째 배포일자 폴더를 기본으로 사용
    dev_folder = Folder.query.filter_by(folder_type='environment', environment='dev').first()
    if dev_folder:
        default_deployment_folder = Folder.query.filter_by(
            folder_type='deployment_date', 
            parent_folder_id=dev_folder.id
        ).first()
        if default_deployment_folder:
            return default_deployment_folder
    return None

def validate_required_fields(data, required_fields):
    """필수 필드 검증"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        response = jsonify({'error': f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}'})
        return add_cors_headers(response), 400
    return None

def create_error_response(message, status_code=400):
    """에러 응답 생성"""
    response = jsonify({'error': message})
    return add_cors_headers(response), status_code

def create_success_response(data, status_code=200):
    """성공 응답 생성"""
    response = jsonify(data)
    return add_cors_headers(response), status_code
