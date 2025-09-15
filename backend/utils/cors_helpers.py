"""
CORS 관련 헬퍼 함수들
"""
from flask import jsonify

def create_cors_response(data=None, status_code=200):
    """CORS 헤더가 포함된 응답 생성"""
    if data is None:
        data = {'status': 'preflight_ok'}
    
    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
    response.headers['Access-Control-Max-Age'] = '86400'
    
    return response, status_code

def handle_options_request():
    """OPTIONS 요청 처리"""
    return create_cors_response()
