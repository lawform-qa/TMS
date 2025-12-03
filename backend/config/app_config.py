"""
Flask 앱 설정 관리
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

# .env 파일 로드 (절대 경로 사용)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

def get_database_url():
    """데이터베이스 URL 설정"""
    is_vercel = 'vercel.app' in os.environ.get('VERCEL_URL', '') or os.environ.get('VERCEL') == '1'
    
    if is_vercel:
        # Vercel 환경에서는 환경 변수 사용
        database_url = os.environ.get('DATABASE_URL')
        
        # DATABASE_URL이 없으면 SQLite 사용
        if not database_url:
            logger.warning("DATABASE_URL이 설정되지 않음, SQLite 사용")
            database_url = 'sqlite:///:memory:'
        elif database_url.startswith('mysql://'):
            database_url = database_url.replace('mysql://', 'mysql+pymysql://')
            # ssl_mode 파라미터 제거하고 기본 SSL 설정 사용
            if '?' in database_url:
                # 기존 파라미터가 있으면 ssl_mode만 제거
                params = database_url.split('?')[1].split('&')
                filtered_params = [p for p in params if not p.startswith('ssl_mode=')]
                if filtered_params:
                    database_url = database_url.split('?')[0] + '?' + '&'.join(filtered_params)
            logger.info("Vercel 환경에서 MySQL 연결 설정 적용")
        else:
            logger.info(f"Vercel 환경에서 데이터베이스 URL 사용: {database_url[:20]}...")
    else:
        # 로컬 개발 환경에서는 로컬 MySQL 사용
        database_url = 'mysql+pymysql://root:1q2w#E$R@localhost:3306/test_management'
        logger.info("로컬 환경에서 로컬 MySQL 사용")
    
    return database_url

def get_database_engine_options(database_url):
    """데이터베이스 엔진 옵션 설정"""
    is_vercel = 'vercel.app' in os.environ.get('VERCEL_URL', '') or os.environ.get('VERCEL') == '1'
    
    if is_vercel and 'sqlite' in database_url:
        logger.info("Vercel 환경에서 SQLite 사용")
        return {}
    else:
        # MySQL 환경 (Vercel 또는 로컬)
        return {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {
                'connect_timeout': 10,
                'read_timeout': 30,
                'write_timeout': 30,
                'ssl': {'ssl': True}
            }
        }

def configure_app(app):
    """Flask 앱 설정 적용"""
    # 기본 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    # JWT 설정
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # 24시간으로 연장
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # 30일로 연장
    
    # 데이터베이스 설정
    database_url = get_database_url()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = get_database_engine_options(database_url)
    
    # 환경 변수 로깅 (디버깅용)
    is_vercel = 'vercel.app' in os.environ.get('VERCEL_URL', '') or os.environ.get('VERCEL') == '1'
    logger.debug(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.debug(f"Secret Key: {app.config['SECRET_KEY']}")
    logger.debug(f"JWT Secret Key: {app.config['JWT_SECRET_KEY']}")
    logger.info(f"Environment: {'production' if is_vercel else 'development'}")
    logger.debug(f"Vercel URL: {os.environ.get('VERCEL_URL', 'Not Vercel')}")
    logger.debug(f".env 파일 경로: {env_path}")
    logger.debug(f".env 파일 존재: {os.path.exists(env_path)}")
    
    return app

def is_vercel_environment():
    """Vercel 환경 여부 확인"""
    return 'vercel.app' in os.environ.get('VERCEL_URL', '') or os.environ.get('VERCEL') == '1'

