import os
import sys
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import mimetypes
from datetime import datetime
import stat

# 상위 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# S3 서비스는 지연 로딩으로 처리
from utils.auth_decorators import user_required
from utils.cors import add_cors_headers

# Blueprint 생성
test_scripts_bp = Blueprint('test_scripts', __name__)

# S3 서비스 지연 로딩 함수
def get_s3_service():
    """S3 서비스를 지연 로딩으로 가져오기"""
    try:
        from utils.s3_service import get_s3_service_instance
        return get_s3_service_instance()
    except ImportError as e:
        current_app.logger.error(f"S3 서비스 로딩 오류: {e}")
        return None

def get_file_info(file_path):
    """파일 정보를 가져오는 헬퍼 함수"""
    try:
        stat_info = os.stat(file_path)
        file_info = {
            'name': os.path.basename(file_path),
            'path': file_path,
            'type': 'file',
            'size': stat_info.st_size,
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'permissions': oct(stat_info.st_mode)[-3:]
        }
        
        # 파일 확장자에 따른 타입 분류
        if os.path.splitext(file_path)[1].lower() in ['.js', '.py', '.json', '.md', '.spec.js']:
            file_info['category'] = 'script'
        elif os.path.splitext(file_path)[1].lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            file_info['category'] = 'image'
        elif os.path.splitext(file_path)[1].lower() in ['.DS_Store']:
            file_info['category'] = 'system'
        else:
            file_info['category'] = 'other'
            
        return file_info
    except Exception as e:
        current_app.logger.error(f"파일 정보 조회 오류: {e}")
        return None

def get_directory_info(dir_path):
    """디렉토리 정보를 가져오는 헬퍼 함수"""
    try:
        stat_info = os.stat(dir_path)
        dir_info = {
            'name': os.path.basename(dir_path),
            'path': dir_path,
            'type': 'directory',
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'permissions': oct(stat_info.st_mode)[-3:],
            'children_count': 0
        }
        
        # 하위 항목 개수 계산
        try:
            children = os.listdir(dir_path)
            dir_info['children_count'] = len(children)
        except:
            dir_info['children_count'] = 0
            
        return dir_info
    except Exception as e:
        current_app.logger.error(f"디렉토리 정보 조회 오류: {e}")
        return None

def explore_directory(path):
    """디렉토리 내용을 탐색하는 함수"""
    try:
        if not os.path.exists(path):
            return None
            
        if not os.path.isdir(path):
            return None
            
        items = []
        children = os.listdir(path)
        
        # 숨김 파일 제외하고 정렬
        visible_children = [child for child in children if not child.startswith('.')]
        visible_children.sort(key=lambda x: (os.path.isdir(os.path.join(path, x)), x.lower()))
        
        for child in visible_children:
            child_path = os.path.join(path, child)
            
            if os.path.isdir(child_path):
                dir_info = get_directory_info(child_path)
                if dir_info:
                    items.append(dir_info)
            else:
                file_info = get_file_info(child_path)
                if file_info:
                    items.append(file_info)
                    
        return {
            'path': path,
            'type': 'directory',
            'children': items,
            'total_count': len(items)
        }
        
    except Exception as e:
        current_app.logger.error(f"디렉토리 탐색 오류: {e}")
        return None

@test_scripts_bp.route('/explore', methods=['GET'])
def explore_test_scripts():
    """테스트 스크립트 폴더 구조를 탐색하는 API"""
    try:
        # 기본 경로 설정 (프로젝트 루트의 test-scripts 폴더)
        base_path = request.args.get('path', 'test-scripts')
        
        # 프로젝트 루트 경로 계산 (backend/routes/에서 3단계 위로)
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        test_scripts_root = os.path.join(project_root, 'test-scripts')
        
        # 요청된 경로 처리
        if base_path == 'test-scripts':
            # 루트 test-scripts 폴더
            full_path = test_scripts_root
        elif base_path.startswith('test-scripts/'):
            # test-scripts 하위 폴더
            relative_path = base_path.replace('test-scripts/', '', 1)
            full_path = os.path.join(test_scripts_root, relative_path)
        else:
            # 잘못된 경로
            return jsonify({'error': '잘못된 경로입니다.'}), 400
            
        # 디버그 로그
        current_app.logger.info(f"요청 경로: {base_path}")
        current_app.logger.info(f"프로젝트 루트: {project_root}")
        current_app.logger.info(f"테스트 스크립트 루트: {test_scripts_root}")
        current_app.logger.info(f"최종 경로: {full_path}")
        
        # 경로 존재 여부 확인
        if not os.path.exists(full_path):
            current_app.logger.error(f"경로가 존재하지 않음: {full_path}")
            return jsonify({'error': f'경로를 찾을 수 없습니다: {base_path}'}), 404
            
        if not os.path.isdir(full_path):
            current_app.logger.error(f"경로가 디렉토리가 아님: {full_path}")
            return jsonify({'error': f'디렉토리가 아닙니다: {base_path}'}), 400
            
        # 경로 검증 (보안상 test-scripts 폴더 내에서만 탐색 허용)
        if not full_path.startswith(test_scripts_root):
            current_app.logger.error(f"허용되지 않은 경로: {full_path}")
            return jsonify({'error': '허용되지 않은 경로입니다.'}), 403
            
        # 디렉토리 탐색
        result = explore_directory(full_path)
        
        if result is None:
            current_app.logger.error(f"디렉토리 탐색 실패: {full_path}")
            return jsonify({'error': '디렉토리를 탐색할 수 없습니다.'}), 500
            
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"테스트 스크립트 탐색 오류: {e}")
        current_app.logger.error(f"오류 상세: {str(e)}")
        import traceback
        current_app.logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return jsonify({'error': f'서버 오류가 발생했습니다: {str(e)}'}), 500

@test_scripts_bp.route('/file-content', methods=['GET'])
def get_file_content():
    """파일 내용을 읽는 API"""
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({'error': '파일 경로가 필요합니다.'}), 400
            
        # 프로젝트 루트 기준으로 경로 설정
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(project_root, file_path)
        
        # 경로 검증 (보안상 test-scripts 폴더 내에서만 접근 허용)
        if not full_path.startswith(os.path.join(project_root, 'test-scripts')):
            return jsonify({'error': '허용되지 않은 경로입니다.'}), 403
            
        if not os.path.exists(full_path):
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
            
        if not os.path.isfile(full_path):
            return jsonify({'error': '파일이 아닙니다.'}), 400
            
        # 파일 크기 제한 (10MB)
        file_size = os.path.getsize(full_path)
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': '파일이 너무 큽니다. (최대 10MB)'}), 413
            
        # 텍스트 파일인지 확인
        text_extensions = ['.js', '.py', '.json', '.md', '.txt', '.spec.js', '.env']
        file_ext = os.path.splitext(full_path)[1].lower()
        
        if file_ext in text_extensions:
            # 텍스트 파일 읽기
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # UTF-8로 읽을 수 없는 경우 다른 인코딩 시도
                try:
                    with open(full_path, 'r', encoding='cp949') as f:
                        content = f.read()
                except:
                    with open(full_path, 'r', encoding='latin-1') as f:
                        content = f.read()
        else:
            # 바이너리 파일인 경우
            content = f"[바이너리 파일] - 크기: {file_size} bytes"
            
        return jsonify({
            'path': file_path,
            'content': content,
            'size': file_size,
            'type': 'text' if file_ext in text_extensions else 'binary',
            'extension': file_ext
        })
        
    except Exception as e:
        current_app.logger.error(f"파일 내용 읽기 오류: {e}")
        return jsonify({'error': '파일을 읽을 수 없습니다.'}), 500

@test_scripts_bp.route('/search', methods=['GET'])
def search_test_scripts():
    """테스트 스크립트 파일을 검색하는 API"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': '검색어가 필요합니다.'}), 400
            
        # 프로젝트 루트 기준으로 test-scripts 폴더 검색
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_scripts_path = os.path.join(project_root, 'test-scripts')
        
        if not os.path.exists(test_scripts_path):
            return jsonify({'error': 'test-scripts 폴더를 찾을 수 없습니다.'}), 404
            
        results = []
        
        def search_recursive(path):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    
                    # 숨김 파일 제외
                    if item.startswith('.'):
                        continue
                        
                    if os.path.isdir(item_path):
                        search_recursive(item_path)
                    else:
                        # 파일명에 검색어가 포함된 경우
                        if query.lower() in item.lower():
                            file_info = get_file_info(item_path)
                            if file_info:
                                # 상대 경로로 변환
                                file_info['relative_path'] = os.path.relpath(item_path, project_root)
                                results.append(file_info)
                                
            except Exception as e:
                current_app.logger.error(f"검색 중 오류: {e}")
                
        search_recursive(test_scripts_path)
        
        # 결과 정렬 (파일명 기준)
        results.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            'query': query,
            'results': results,
            'total_count': len(results)
        })
        
    except Exception as e:
        current_app.logger.error(f"테스트 스크립트 검색 오류: {e}")
        return jsonify({'error': '검색 중 오류가 발생했습니다.'}), 500

@test_scripts_bp.route('/stats', methods=['GET'])
def get_test_scripts_stats():
    """테스트 스크립트 폴더 통계 정보를 가져오는 API"""
    try:
        # 프로젝트 루트 기준으로 test-scripts 폴더 통계
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_scripts_path = os.path.join(project_root, 'test-scripts')
        
        if not os.path.exists(test_scripts_path):
            return jsonify({'error': 'test-scripts 폴더를 찾을 수 없습니다.'}), 404
            
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_size': 0,
            'file_types': {},
            'directory_structure': {}
        }
        
        def collect_stats_recursive(path, level=0):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    
                    # 숨김 파일 제외
                    if item.startswith('.'):
                        continue
                        
                    if os.path.isdir(item_path):
                        stats['total_directories'] += 1
                        
                        # 디렉토리 구조 기록
                        if level < 3:  # 최대 3단계까지만 기록
                            dir_name = os.path.basename(item_path)
                            if dir_name not in stats['directory_structure']:
                                stats['directory_structure'][dir_name] = {
                                    'type': 'directory',
                                    'children_count': 0,
                                    'subdirectories': []
                                }
                            
                            # 하위 항목 개수 계산
                            try:
                                children = [child for child in os.listdir(item_path) if not child.startswith('.')]
                                stats['directory_structure'][dir_name]['children_count'] = len(children)
                                
                                # 하위 디렉토리만 기록
                                subdirs = [child for child in children if os.path.isdir(os.path.join(item_path, child))]
                                stats['directory_structure'][dir_name]['subdirectories'] = subdirs[:5]  # 최대 5개만
                            except:
                                pass
                                
                        collect_stats_recursive(item_path, level + 1)
                    else:
                        stats['total_files'] += 1
                        
                        # 파일 크기 추가
                        try:
                            file_size = os.path.getsize(item_path)
                            stats['total_size'] += file_size
                        except:
                            pass
                            
                        # 파일 타입별 카운트
                        file_ext = os.path.splitext(item)[1].lower()
                        if file_ext:
                            if file_ext not in stats['file_types']:
                                stats['file_types'][file_ext] = 0
                            stats['file_types'][file_ext] += 1
                        else:
                            if 'no_extension' not in stats['file_types']:
                                stats['file_types']['no_extension'] = 0
                            stats['file_types']['no_extension'] += 1
                                
            except Exception as e:
                current_app.logger.error(f"통계 수집 중 오류: {e}")
                
        collect_stats_recursive(test_scripts_path)
        
        # 파일 타입별 통계 정렬
        stats['file_types'] = dict(sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True))
        
        # 디렉토리 구조 정렬
        stats['directory_structure'] = dict(sorted(stats['directory_structure'].items(), key=lambda x: x[0].lower()))
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f"테스트 스크립트 통계 오류: {e}")
        return jsonify({'error': '통계 정보를 가져올 수 없습니다.'}), 500

# S3 관련 API 엔드포인트들
@test_scripts_bp.route('/s3/upload', methods=['POST'])
def upload_to_s3():
    """파일을 S3에 업로드"""
    try:
        if 'file' not in request.files:
            response = jsonify({'error': '파일이 없습니다.'})
            return add_cors_headers(response), 400
        
        file = request.files['file']
        if file.filename == '':
            response = jsonify({'error': '파일이 선택되지 않았습니다.'})
            return add_cors_headers(response), 400
        
        # 파일명 보안 처리
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"test-scripts/{timestamp}_{filename}"
        
        # 임시 파일로 저장
        temp_path = f"/tmp/{filename}"
        file.save(temp_path)
        
        try:
            # S3 서비스 가져오기
            s3_service = get_s3_service()
            if not s3_service:
                response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
                return add_cors_headers(response), 500
            
            # S3에 업로드
            result = s3_service.upload_file(temp_path, s3_key)
            
            # 임시 파일 삭제
            os.remove(temp_path)
            
            response = jsonify({
                'success': True,
                'message': '파일이 성공적으로 업로드되었습니다.',
                'url': result['url'],
                's3_key': result['s3_key']
            })
            return add_cors_headers(response), 200
            
        except Exception as e:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        current_app.logger.error(f"S3 업로드 오류: {e}")
        response = jsonify({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/upload-content', methods=['POST'])
def upload_content_to_s3():
    """문자열 내용을 S3에 업로드"""
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'filename' not in data:
            response = jsonify({'error': '내용과 파일명이 필요합니다.'})
            return add_cors_headers(response), 400
        
        content = data['content']
        filename = secure_filename(data['filename'])
        is_new_file = data.get('is_new_file', True)  # 기본값은 새 파일
        existing_s3_key = data.get('existing_s3_key', None)  # 기존 파일의 S3 키
        
        if is_new_file or not existing_s3_key:
            # 새 파일인 경우 타임스탬프 추가
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"test-scripts/{timestamp}_{filename}"
        else:
            # 기존 파일 수정인 경우 기존 S3 키 사용 (덮어쓰기)
            s3_key = existing_s3_key
        
        # Content-Type 결정
        content_type = 'text/plain'
        if filename.endswith('.js'):
            content_type = 'application/javascript'
        elif filename.endswith('.py'):
            content_type = 'text/x-python'
        elif filename.endswith('.json'):
            content_type = 'application/json'
        elif filename.endswith('.md'):
            content_type = 'text/markdown'
        
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        # S3에 업로드
        result = s3_service.upload_content(content, s3_key, content_type)
        
        response = jsonify({
            'success': True,
            'message': '내용이 성공적으로 업로드되었습니다.',
            'url': result['url'],
            's3_key': result['s3_key']
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 내용 업로드 오류: {e}")
        response = jsonify({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/list', methods=['GET'])
def list_s3_files():
    """S3에서 파일 목록 조회"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.', 'debug': 'S3 service is None'})
            return add_cors_headers(response), 500
        
        prefix = request.args.get('prefix', 'test-scripts/')
        files = s3_service.list_files(prefix)
        
        response = jsonify({
            'success': True,
            'files': files,
            'total_count': len(files),
            'debug': {
                's3_service_exists': s3_service is not None,
                'prefix': prefix,
                'environment': os.getenv('ENVIRONMENT', 'unknown')
            }
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 파일 목록 조회 오류: {e}")
        response = jsonify({'error': f'파일 목록 조회 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/folders', methods=['GET'])
def list_s3_folders():
    """S3에서 모든 폴더 목록 조회 (재귀적)"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        prefix = request.args.get('prefix', 'test-scripts/')
        folders = s3_service.list_all_folders(prefix)
        
        response = jsonify({
            'success': True,
            'folders': folders,
            'total_count': len(folders)
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 폴더 목록 조회 오류: {e}")
        response = jsonify({'error': f'폴더 목록 조회 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/content', methods=['GET'])
def get_s3_file_content():
    """S3에서 파일 내용 조회"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        s3_key = request.args.get('key')
        if not s3_key:
            response = jsonify({'error': 'S3 키가 필요합니다.'})
            return add_cors_headers(response), 400
        
        content = s3_service.get_file_content(s3_key)
        
        response = jsonify({
            'success': True,
            'content': content,
            's3_key': s3_key
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 파일 내용 조회 오류: {e}")
        response = jsonify({'error': f'파일 내용 조회 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/download-url', methods=['GET'])
def get_s3_download_url():
    """S3 파일 다운로드 URL 생성"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        s3_key = request.args.get('key')
        if not s3_key:
            response = jsonify({'error': 'S3 키가 필요합니다.'})
            return add_cors_headers(response), 400
        
        url = s3_service.generate_presigned_url(s3_key)
        
        response = jsonify({
            'success': True,
            'download_url': url,
            's3_key': s3_key
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 다운로드 URL 생성 오류: {e}")
        response = jsonify({'error': f'다운로드 URL 생성 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/delete', methods=['DELETE'])
def delete_s3_file():
    """S3에서 파일 삭제"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        data = request.get_json()
        if not data or 's3_key' not in data:
            response = jsonify({'error': 'S3 키가 필요합니다.'})
            return add_cors_headers(response), 400
        
        s3_key = data['s3_key']
        s3_service.delete_file(s3_key)
        
        response = jsonify({
            'success': True,
            'message': '파일이 성공적으로 삭제되었습니다.',
            's3_key': s3_key
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"S3 파일 삭제 오류: {e}")
        response = jsonify({'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/upload-folder', methods=['POST'])
def upload_folder_to_s3():
    """로컬 폴더 구조를 유지하면서 S3에 업로드"""
    try:
        # S3 서비스 가져오기
        s3_service = get_s3_service()
        if not s3_service:
            response = jsonify({'error': 'S3 서비스를 사용할 수 없습니다.'})
            return add_cors_headers(response), 500
        
        data = request.get_json()
        if not data or 'folder_path' not in data:
            response = jsonify({'error': '폴더 경로가 필요합니다.'})
            return add_cors_headers(response), 400
        
        folder_path = data['folder_path']
        
        # 프로젝트 루트 기준으로 경로 설정
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(project_root, folder_path)
        
        # 경로 검증 (보안상 test-scripts 폴더 내에서만 업로드 허용)
        if not full_path.startswith(os.path.join(project_root, 'test-scripts')):
            response = jsonify({'error': '허용되지 않은 경로입니다.'})
            return add_cors_headers(response), 403
        
        if not os.path.exists(full_path):
            response = jsonify({'error': '폴더를 찾을 수 없습니다.'})
            return add_cors_headers(response), 404
        
        if not os.path.isdir(full_path):
            response = jsonify({'error': '폴더가 아닙니다.'})
            return add_cors_headers(response), 400
        
        # 폴더 구조를 재귀적으로 탐색하여 업로드
        uploaded_files = []
        failed_files = []
        
        def upload_directory_recursive(current_path, s3_prefix=""):
            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    
                    # 숨김 파일 제외
                    if item.startswith('.'):
                        continue
                    
                    if os.path.isdir(item_path):
                        # 디렉토리인 경우 재귀 호출
                        new_prefix = f"{s3_prefix}{item}/" if s3_prefix else f"{item}/"
                        upload_directory_recursive(item_path, new_prefix)
                    else:
                        # 파일인 경우 업로드
                        try:
                            # S3 키 생성 (폴더 구조 유지)
                            s3_key = f"test-scripts/{s3_prefix}{item}"
                            
                            # Content-Type 결정
                            content_type = 'text/plain'
                            if item.endswith('.js'):
                                content_type = 'application/javascript'
                            elif item.endswith('.py'):
                                content_type = 'text/x-python'
                            elif item.endswith('.json'):
                                content_type = 'application/json'
                            elif item.endswith('.md'):
                                content_type = 'text/markdown'
                            
                            # 파일 내용 읽기
                            with open(item_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # S3에 업로드
                            result = s3_service.upload_content(content, s3_key, content_type)
                            uploaded_files.append({
                                'local_path': os.path.relpath(item_path, project_root),
                                's3_key': s3_key,
                                'url': result['url']
                            })
                            
                        except Exception as e:
                            failed_files.append({
                                'file': os.path.relpath(item_path, project_root),
                                'error': str(e)
                            })
                            
            except Exception as e:
                current_app.logger.error(f"디렉토리 탐색 오류: {e}")
        
        # 업로드 시작
        upload_directory_recursive(full_path)
        
        response = jsonify({
            'success': True,
            'message': f'폴더 업로드가 완료되었습니다. {len(uploaded_files)}개 파일 업로드됨',
            'uploaded_files': uploaded_files,
            'failed_files': failed_files,
            'total_uploaded': len(uploaded_files),
            'total_failed': len(failed_files)
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"폴더 업로드 오류: {e}")
        response = jsonify({'error': f'폴더 업로드 중 오류가 발생했습니다: {str(e)}'})
        return add_cors_headers(response), 500

def _get_user_settings_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    settings_dir = os.path.join(base_dir, '..', 'config')
    settings_dir = os.path.abspath(settings_dir)
    os.makedirs(settings_dir, exist_ok=True)
    return os.path.join(settings_dir, 'test_scripts_user_settings.json')


def _read_user_settings():
    path = _get_user_settings_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _write_user_settings(settings: dict):
    path = _get_user_settings_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

@test_scripts_bp.route('/s3/settings/prefix', methods=['GET'])
@user_required
def get_user_s3_prefix():
    try:
        settings = _read_user_settings()
        user_id = str(request.user.id)
        user_settings = settings.get(user_id, {})
        prefix = user_settings.get('s3_base_prefix', 'test-scripts/')
        response = jsonify({'success': True, 's3_base_prefix': prefix})
        return add_cors_headers(response), 200
    except Exception as e:
        current_app.logger.error(f"사용자 S3 프리픽스 조회 오류: {e}")
        response = jsonify({'error': '설정을 조회할 수 없습니다.'})
        return add_cors_headers(response), 500

@test_scripts_bp.route('/s3/settings/prefix', methods=['POST'])
@user_required
def set_user_s3_prefix():
    try:
        data = request.get_json() or {}
        new_prefix = data.get('s3_base_prefix')
        if not new_prefix:
            response = jsonify({'error': 's3_base_prefix가 필요합니다.'})
            return add_cors_headers(response), 400
        # 접미사 슬래시 보정
        if not new_prefix.endswith('/'):
            new_prefix = new_prefix + '/'
        settings = _read_user_settings()
        user_id = str(request.user.id)
        user_settings = settings.get(user_id, {})
        user_settings['s3_base_prefix'] = new_prefix
        settings[user_id] = user_settings
        _write_user_settings(settings)
        response = jsonify({'success': True, 's3_base_prefix': new_prefix})
        return add_cors_headers(response), 200
    except Exception as e:
        current_app.logger.error(f"사용자 S3 프리픽스 저장 오류: {e}")
        response = jsonify({'error': '설정을 저장할 수 없습니다.'})
        return add_cors_headers(response), 500
