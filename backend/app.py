from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import text
from sqlalchemy import inspect

# 모델 및 Blueprint 임포트
from models import db, TestCase, TestResult, Screenshot
from routes.testcases import testcases_bp
from routes.testcases_extended import testcases_extended_bp
from routes.dashboard_extended import dashboard_extended_bp
from routes.automation import automation_bp
from routes.performance import performance_bp
from routes.folders import folders_bp
from routes.users import users_bp
from routes.auth import auth_bp
from routes.test_scripts import test_scripts_bp
from routes.jira_issues import jira_issues_bp

# 유틸리티 임포트
from flask_jwt_extended import JWTManager
from utils.cors import setup_cors
from utils.logger import get_logger
from utils.timezone_utils import get_kst_now, get_kst_isoformat
from utils.common_helpers import handle_options_request
from utils.jwt_callbacks import setup_jwt_callbacks
from utils.db_init import initialize_database
from config.app_config import configure_app, is_vercel_environment
from utils.auth_decorators import user_required

# 로거 초기화
logger = get_logger(__name__)

# Flask 앱 생성
app = Flask(__name__)

# 앱 설정 적용
configure_app(app)

# 환경 확인
is_vercel = is_vercel_environment()

# CORS 설정
if is_vercel:
    setup_cors(app)
else:
    # 로컬 환경에서는 모든 origin 허용
    CORS(app, origins=["*"], supports_credentials=True)

# 데이터베이스 초기화
db.init_app(app)
migrate = Migrate(app, db)

# JWT 초기화 및 콜백 설정
jwt = JWTManager(app)
setup_jwt_callbacks(jwt)

# Blueprint 등록
app.register_blueprint(testcases_bp)
app.register_blueprint(testcases_extended_bp)
app.register_blueprint(dashboard_extended_bp)
app.register_blueprint(automation_bp)
app.register_blueprint(performance_bp)
app.register_blueprint(folders_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(test_scripts_bp, url_prefix='/api/test-scripts')
app.register_blueprint(jira_issues_bp)

# 전역 OPTIONS 핸들러
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """모든 경로에 대한 OPTIONS 요청 처리"""
    return handle_options_request()

# 기본 라우트들
@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """헬스 체크 엔드포인트"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        from utils.db_helper import get_database_info
        
        # 데이터베이스 연결 테스트
        db.session.execute(text('SELECT 1'))
        if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.session.commit()
        db_status = 'connected'
        
        # 데이터베이스 정보 가져오기
        db_info = get_database_info(app.config['SQLALCHEMY_DATABASE_URI'])
        
        response = jsonify({
            'status': 'healthy', 
            'message': 'Test Platform Backend is running',
            'version': '2.0.1',
            'timestamp': get_kst_isoformat(get_kst_now()),
            'environment': 'production' if is_vercel else 'development',
            'database': {
                'status': db_status,
                'type': db_info.get('type', 'Unknown'),
                'info': db_info
            }
        })
        return response, 200
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Health check 오류: {error_msg}")
        
        try:
            from utils.db_helper import get_database_info
            db_info = get_database_info(app.config['SQLALCHEMY_DATABASE_URI'])
        except Exception:
            db_info = {}
        
        response = jsonify({
            'status': 'degraded', 
            'message': 'Test Platform Backend is running (with database issues)',
            'version': '2.0.1',
            'timestamp': get_kst_isoformat(get_kst_now()),
            'environment': 'production' if is_vercel else 'development',
            'database': {
                'status': 'error',
                'type': db_info.get('type', 'Unknown'),
                'error': error_msg,
                'info': db_info
            },
            'note': 'Application is running but database connection failed'
        })
        return response, 200

@app.route('/cors-test', methods=['GET', 'OPTIONS'])
def cors_test():
    """CORS 테스트 엔드포인트"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        response = jsonify({
            'status': 'success',
            'message': 'CORS test endpoint is working',
            'timestamp': get_kst_isoformat(get_kst_now()),
            'cors_enabled': True
        })
        return response, 200
    except Exception as e:
        response = jsonify({
            'status': 'error',
            'message': f'CORS test failed: {str(e)}',
            'timestamp': get_kst_isoformat(get_kst_now())
        })
        return response, 500

@app.route('/simple-cors-test', methods=['GET', 'POST', 'OPTIONS'])
def simple_cors_test():
    """간단한 CORS 테스트 엔드포인트"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    response = jsonify({
        'status': 'success',
        'message': 'Simple CORS test successful',
        'method': request.method,
        'timestamp': get_kst_isoformat(get_kst_now())
    })
    return response, 200

@app.route('/ping', methods=['GET', 'OPTIONS'])
def ping():
    """가장 간단한 ping 엔드포인트 (데이터베이스 연결 없음)"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    return jsonify({
        'status': 'success',
        'message': 'pong',
        'timestamp': get_kst_isoformat(get_kst_now()),
        'environment': 'production' if is_vercel else 'development'
    }), 200

@app.route('/init-db', methods=['GET', 'POST', 'OPTIONS'])
def init_database():
    """데이터베이스 초기화 엔드포인트"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    result, status_code = initialize_database(app)
    response = jsonify(result)
    return response, status_code

# 테스트 케이스 관련 라우트 (Blueprint에 없는 일부 라우트만 유지)
@app.route('/testcases/<int:testcase_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
def manage_testcase(testcase_id):
    """테스트 케이스 관리 (단일 엔드포인트)"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        testcase = TestCase.query.get_or_404(testcase_id)
        
        if request.method == 'GET':
            data = {
                'id': testcase.id,
                'name': testcase.name,
                'description': testcase.description,
                'test_type': testcase.test_type,
                'script_path': testcase.script_path,
                'folder_id': testcase.folder_id,
                'main_category': testcase.main_category,
                'sub_category': testcase.sub_category,
                'detail_category': testcase.detail_category,
                'pre_condition': testcase.pre_condition,
                'expected_result': testcase.expected_result,
                'remark': testcase.remark,
                'automation_code_path': testcase.automation_code_path,
                'environment': testcase.environment,
                'created_at': testcase.created_at.isoformat(),
                'updated_at': testcase.updated_at.isoformat()
            }
            return jsonify(data), 200
        
        elif request.method == 'PUT':
            data = request.get_json()
            testcase.name = data.get('name', testcase.name)
            testcase.description = data.get('description', testcase.description)
            testcase.test_type = data.get('test_type', testcase.test_type)
            testcase.script_path = data.get('script_path', testcase.script_path)
            testcase.folder_id = data.get('folder_id', testcase.folder_id)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Test case updated successfully'}), 200
        
        elif request.method == 'DELETE':
            db.session.delete(testcase)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Test case deleted successfully'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/testcases/<int:testcase_id>/status', methods=['PUT', 'OPTIONS'])
def update_testcase_status(testcase_id):
    """테스트 케이스 상태 업데이트"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        testcase = TestCase.query.get_or_404(testcase_id)
        data = request.get_json()
        new_status = data.get('status')
        
        # 테스트 결과 생성 또는 업데이트
        test_result = TestResult.query.filter_by(test_case_id=testcase_id).first()
        if not test_result:
            test_result = TestResult(test_case_id=testcase_id)
            db.session.add(test_result)
        
        test_result.result = new_status
        test_result.execution_time = data.get('execution_time', 0)
        test_result.notes = data.get('result_data', '')
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Test case status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/testcases/<int:testcase_id>/screenshots', methods=['GET', 'OPTIONS'])
def get_testcase_screenshots(testcase_id):
    """테스트 케이스 스크린샷 조회"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        test_results = TestResult.query.filter_by(test_case_id=testcase_id).all()
        screenshots = []
        
        for result in test_results:
            result_screenshots = Screenshot.query.filter_by(test_result_id=result.id).all()
            for screenshot in result_screenshots:
                screenshots.append({
                    'id': screenshot.id,
                    'screenshot_path': screenshot.file_path,
                    'timestamp': screenshot.created_at.isoformat() if screenshot.created_at else None
                })
        
        return jsonify(screenshots), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/testcases/<int:testcase_id>/execute', methods=['POST', 'OPTIONS'])
@user_required
def execute_testcase(testcase_id):
    """테스트 케이스 실행"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        testcase = TestCase.query.get_or_404(testcase_id)
        
        test_result = TestResult(
            test_case_id=testcase_id,
            result='running',
            execution_time=0,
            notes='Test execution started'
        )
        db.session.add(test_result)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'Test execution started',
            'result_id': test_result.id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 테스트 실행 결과 관련 라우트
@app.route('/test', methods=['GET', 'OPTIONS'])
def get_test_data():
    """테스트 데이터 조회"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        total_testcases = TestCase.query.count()
        
        try:
            running_tests = TestResult.query.filter_by(result='running').count()
            completed_tests = TestResult.query.filter_by(result='completed').count()
            failed_tests = TestResult.query.filter_by(result='failed').count()
        except Exception:
            running_tests = 0
            completed_tests = 0
            failed_tests = 0
        
        test_data = {
            'total_tests': total_testcases,
            'running_tests': running_tests,
            'completed_tests': completed_tests,
            'failed_tests': failed_tests,
            'last_updated': get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(test_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-executions', methods=['GET', 'OPTIONS'])
def get_test_executions():
    """테스트 실행 결과 조회"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        try:
            executions = TestResult.query.all()
        except Exception:
            return jsonify([]), 200
        
        data = []
        
        for exe in executions:
            try:
                execution_data = {
                    'id': exe.id,
                    'test_case_id': exe.test_case_id,
                    'status': getattr(exe, 'result', 'unknown'),
                    'execution_time': exe.execution_time,
                    'notes': exe.notes,
                    'created_at': exe.created_at.isoformat()
                }
                data.append(execution_data)
            except Exception:
                continue
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/testresults/<int:testcase_id>', methods=['GET', 'OPTIONS'])
def get_test_results(testcase_id):
    """특정 테스트 케이스의 결과 조회"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        results = TestResult.query.filter_by(test_case_id=testcase_id).all()
        data = [{
            'id': result.id,
            'test_case_id': result.test_case_id,
            'status': result.result,
            'execution_time': result.execution_time,
            'notes': result.notes,
            'created_at': result.created_at.isoformat()
        } for result in results]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 폴더 관련 라우트
@app.route('/folders/feature', methods=['POST', 'OPTIONS'])
def add_feature_folders():
    """기능 폴더 추가"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        from models import Folder
        from utils.timezone_utils import get_kst_now
        
        date_folder_ids = [4, 5, 6]
        
        feature_folders = [
            {'name': 'CLM/Draft', 'parent_id': 4},
            {'name': 'CLM/Review', 'parent_id': 4},
            {'name': 'CLM/Sign', 'parent_id': 4},
            {'name': 'CLM/Process', 'parent_id': 4},
            {'name': 'Litigation/Draft', 'parent_id': 5},
            {'name': 'Litigation/Schedule', 'parent_id': 5},
            {'name': 'Dashboard/Setting', 'parent_id': 6}
        ]
        
        added_folders = []
        for feature in feature_folders:
            existing = Folder.query.filter_by(name=feature['name'], parent_id=feature['parent_id']).first()
            if not existing:
                new_folder = Folder(
                    name=feature['name'],
                    parent_id=feature['parent_id'],
                    created_at=get_kst_now()
                )
                db.session.add(new_folder)
                added_folders.append(feature['name'])
        
        if added_folders:
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': f'기능 폴더 {len(added_folders)}개가 추가되었습니다.',
                'added_folders': added_folders
            }), 200
        else:
            return jsonify({
                'status': 'info',
                'message': '추가할 기능 폴더가 없습니다.'
            }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/testcases/reorganize', methods=['POST', 'OPTIONS'])
def reorganize_testcases():
    """테스트 케이스 폴더 재배치"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        testcases = TestCase.query.all()
        moved_count = 0
        
        for tc in testcases:
            new_folder_id = None
            
            if 'CLM' in tc.name:
                if 'Draft' in tc.name:
                    new_folder_id = 7
                elif 'Review' in tc.name:
                    new_folder_id = 8
                elif 'Sign' in tc.name:
                    new_folder_id = 9
                elif 'Process' in tc.name:
                    new_folder_id = 10
                else:
                    new_folder_id = 7
            elif 'Litigation' in tc.name:
                if 'Draft' in tc.name:
                    new_folder_id = 11
                elif 'Schedule' in tc.name:
                    new_folder_id = 12
                else:
                    new_folder_id = 11
            elif 'Dashboard' in tc.name:
                new_folder_id = 13
            
            if new_folder_id and tc.folder_id != new_folder_id:
                tc.folder_id = new_folder_id
                moved_count += 1
        
        if moved_count > 0:
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': f'{moved_count}개의 테스트 케이스가 기능 폴더로 이동되었습니다.'
            }), 200
        else:
            return jsonify({
                'status': 'info',
                'message': '이동할 테스트 케이스가 없습니다.'
            }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/db-status', methods=['GET', 'OPTIONS'])
def check_database_status():
    """데이터베이스 연결 상태 확인"""
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    try:
        db.session.execute(text('SELECT 1'))
        
        try:
            inspector = inspect(db.engine)
            columns = inspector.get_columns('Users')
            
            table_info = {
                'table_name': 'Users',
                'columns': [],
                'last_login_exists': False
            }
            
            for col in columns:
                col_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', 'unknown'),
                    'default': col.get('default', 'unknown')
                }
                table_info['columns'].append(col_info)
                
                if col['name'] == 'last_login':
                    table_info['last_login_exists'] = True
                    table_info['last_login_info'] = col_info
            
            try:
                from models import User
                sample_user = User.query.first()
                if sample_user:
                    table_info['sample_user'] = {
                        'id': sample_user.id,
                        'username': sample_user.username,
                        'last_login': sample_user.last_login.isoformat() if sample_user.last_login else None,
                        'created_at': sample_user.created_at.isoformat() if sample_user.created_at else None
                    }
            except Exception as user_error:
                table_info['user_query_error'] = str(user_error)
            
            return jsonify({
                'status': 'success',
                'database_connected': True,
                'table_info': table_info,
                'environment': 'production' if is_vercel else 'development',
                'database_url': app.config['SQLALCHEMY_DATABASE_URI'][:50] + '...' if len(app.config['SQLALCHEMY_DATABASE_URI']) > 50 else app.config['SQLALCHEMY_DATABASE_URI']
            }), 200
            
        except Exception as inspect_error:
            return jsonify({
                'status': 'error',
                'database_connected': True,
                'inspect_error': str(inspect_error),
                'environment': 'production' if is_vercel else 'development'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'database_connected': False,
            'error': str(e),
            'environment': 'production' if is_vercel else 'development'
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)
