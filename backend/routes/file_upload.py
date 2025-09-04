"""
S3 파일 업로드 관련 API 엔드포인트
"""

import os
import boto3
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from utils.auth_decorators import user_required
from utils.response_utils import success_response, error_response
from utils.logger import get_logger

# 로거 초기화
logger = get_logger(__name__)

# Blueprint 생성
file_upload_bp = Blueprint('file_upload', __name__)

# S3 클라이언트 초기화
def get_s3_client():
    """S3 클라이언트 생성"""
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'ap-northeast-2')
    )

def get_s3_bucket():
    """S3 버킷 이름 반환"""
    return os.environ.get('AWS_S3_BUCKET', 'test-management-files')

@file_upload_bp.route('/upload', methods=['POST'])
@user_required
def upload_file():
    """파일 업로드"""
    try:
        # 파일 확인
        if 'file' not in request.files:
            return error_response('파일이 선택되지 않았습니다.', 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('파일이 선택되지 않았습니다.', 400)
        
        # 파일명 보안 처리
        filename = secure_filename(file.filename)
        
        # 고유한 파일명 생성 (중복 방지)
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # S3에 업로드할 경로 생성
        upload_path = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
        
        # S3 클라이언트 생성
        s3_client = get_s3_client()
        bucket_name = get_s3_bucket()
        
        # S3에 파일 업로드
        s3_client.upload_fileobj(
            file,
            bucket_name,
            upload_path,
            ExtraArgs={
                'ContentType': file.content_type or 'application/octet-stream',
                'ACL': 'public-read'  # 공개 읽기 권한
            }
        )
        
        # S3 URL 생성
        file_url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'ap-northeast-2')}.amazonaws.com/{upload_path}"
        
        logger.info(f"파일 업로드 완료: {upload_path}")
        
        return success_response({
            'message': '파일 업로드가 완료되었습니다.',
            'file_url': file_url,
            'filename': filename,
            'upload_path': upload_path
        })
        
    except Exception as e:
        logger.error(f"파일 업로드 오류: {str(e)}")
        return error_response(f'파일 업로드 중 오류가 발생했습니다: {str(e)}', 500)

@file_upload_bp.route('/delete', methods=['DELETE'])
@user_required
def delete_file():
    """파일 삭제"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return error_response('파일 경로가 제공되지 않았습니다.', 400)
        
        # S3 클라이언트 생성
        s3_client = get_s3_client()
        bucket_name = get_s3_bucket()
        
        # S3에서 파일 삭제
        s3_client.delete_object(Bucket=bucket_name, Key=file_path)
        
        logger.info(f"파일 삭제 완료: {file_path}")
        
        return success_response({
            'message': '파일이 삭제되었습니다.',
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"파일 삭제 오류: {str(e)}")
        return error_response(f'파일 삭제 중 오류가 발생했습니다: {str(e)}', 500)

@file_upload_bp.route('/list', methods=['GET'])
@user_required
def list_files():
    """파일 목록 조회"""
    try:
        # 쿼리 파라미터
        prefix = request.args.get('prefix', 'uploads/')
        max_keys = int(request.args.get('max_keys', 100))
        
        # S3 클라이언트 생성
        s3_client = get_s3_client()
        bucket_name = get_s3_bucket()
        
        # S3에서 파일 목록 조회
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'ap-northeast-2')}.amazonaws.com/{obj['Key']}"
                })
        
        return success_response({
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"파일 목록 조회 오류: {str(e)}")
        return error_response(f'파일 목록 조회 중 오류가 발생했습니다: {str(e)}', 500)
