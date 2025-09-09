import boto3
import os
from datetime import datetime
from flask import current_app
import json
from botocore.exceptions import ClientError, NoCredentialsError

class S3Service:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'test-management-upload')
        self.region = os.getenv('AWS_REGION', 'ap-northeast-2')
        self._initialize_client()
    
    def _initialize_client(self):
        """S3 클라이언트 초기화"""
        try:
            # AWS 자격 증명 설정
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not aws_access_key_id or not aws_secret_access_key:
                print("AWS 자격 증명이 설정되지 않았습니다. S3 기능이 제한됩니다.")
                return
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=self.region
            )
            
            # 버킷 존재 확인 및 생성
            self._ensure_bucket_exists()
            
        except Exception as e:
            print(f"S3 클라이언트 초기화 오류: {e}")
            self.s3_client = None
    
    def _ensure_bucket_exists(self):
        """버킷이 존재하는지 확인하고 없으면 생성"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"S3 버킷 '{self.bucket_name}' 확인됨")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # 버킷이 존재하지 않음 - 생성
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    print(f"S3 버킷 '{self.bucket_name}' 생성됨")
                except Exception as create_error:
                    print(f"버킷 생성 오류: {create_error}")
            elif error_code == '403':
                # 권한 없음 - S3 기능 비활성화
                print(f"버킷 접근 권한 없음: {e}")
                print("S3 기능이 비활성화됩니다.")
                self.s3_client = None
            else:
                print(f"버킷 접근 오류: {e}")
    
    def upload_file(self, file_path, s3_key, content_type=None):
        """파일을 S3에 업로드"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 파일 업로드를 건너뜁니다.")
            return None
        
        try:
            # Content-Type 자동 감지
            if not content_type:
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # 파일 업로드
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': {
                            'uploaded_at': datetime.now().isoformat(),
                            'original_filename': os.path.basename(file_path)
                        }
                    }
                )
            
            # 업로드된 파일의 URL 생성
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                'url': file_url,
                's3_key': s3_key,
                'bucket': self.bucket_name
            }
            
        except FileNotFoundError:
            raise Exception(f"파일을 찾을 수 없습니다: {file_path}")
        except NoCredentialsError:
            raise Exception("AWS 자격 증명이 올바르지 않습니다.")
        except ClientError as e:
            raise Exception(f"S3 업로드 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 업로드 중 오류 발생: {e}")
    
    def upload_content(self, content, s3_key, content_type='text/plain'):
        """문자열 내용을 S3에 업로드"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.now().isoformat(),
                    'content_type': content_type
                }
            )
            
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                'url': file_url,
                's3_key': s3_key,
                'bucket': self.bucket_name
            }
            
        except NoCredentialsError:
            raise Exception("AWS 자격 증명이 올바르지 않습니다.")
        except ClientError as e:
            raise Exception(f"S3 업로드 오류: {e}")
        except Exception as e:
            raise Exception(f"내용 업로드 중 오류 발생: {e}")
    
    def download_file(self, s3_key, local_path):
        """S3에서 파일 다운로드"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise Exception(f"파일을 찾을 수 없습니다: {s3_key}")
            else:
                raise Exception(f"S3 다운로드 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 다운로드 중 오류 발생: {e}")
    
    def get_file_content(self, s3_key):
        """S3에서 파일 내용 가져오기"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read()
            
            # 메타데이터에서 Content-Type 확인
            content_type = response.get('ContentType', 'text/plain')
            
            # 텍스트 파일인 경우 UTF-8로 디코딩
            if content_type.startswith('text/') or s3_key.endswith(('.js', '.py', '.json', '.md', '.txt')):
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    return content.decode('utf-8', errors='replace')
            else:
                return content
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise Exception(f"파일을 찾을 수 없습니다: {s3_key}")
            else:
                raise Exception(f"S3 파일 조회 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 내용 조회 중 오류 발생: {e}")
    
    def list_files(self, prefix=''):
        """S3에서 파일 목록 조회 (폴더 구조 포함)"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            print(f"S3 파일 목록 조회 시작 - 버킷: {self.bucket_name}, 접두사: {prefix}")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            print(f"S3 응답: {response}")
            
            files = []
            folders = []
            
            # 폴더 목록 처리
            if 'CommonPrefixes' in response:
                for folder in response['CommonPrefixes']:
                    folder_name = folder['Prefix'].rstrip('/')
                    
                    # 폴더의 하위 항목 개수 계산
                    children_count = 0
                    try:
                        # 해당 폴더의 하위 항목 조회
                        folder_response = self.s3_client.list_objects_v2(
                            Bucket=self.bucket_name,
                            Prefix=folder['Prefix'],
                            Delimiter='/'
                        )
                        
                        # 하위 폴더 개수
                        if 'CommonPrefixes' in folder_response:
                            children_count += len(folder_response['CommonPrefixes'])
                        
                        # 하위 파일 개수
                        if 'Contents' in folder_response:
                            # 폴더 자체는 제외하고 실제 파일만 카운트
                            file_count = sum(1 for obj in folder_response['Contents'] if not obj['Key'].endswith('/'))
                            children_count += file_count
                            
                    except Exception as e:
                        print(f"폴더 {folder_name}의 하위 항목 개수 계산 오류: {e}")
                        children_count = 0
                    
                    folders.append({
                        'key': folder_name,
                        'name': folder_name.split('/')[-1],
                        'type': 'folder',
                        'children_count': children_count,
                        'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{folder['Prefix']}"
                    })
            
            # 파일 목록 처리
            if 'Contents' in response:
                for obj in response['Contents']:
                    # 폴더 자체는 제외 (파일만)
                    if not obj['Key'].endswith('/'):
                        files.append({
                            'key': obj['Key'],
                            'name': obj['Key'].split('/')[-1],
                            'size': obj['Size'],
                            'type': 'file',
                            'last_modified': obj['LastModified'].isoformat(),
                            'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                        })
            
            # 폴더와 파일을 합쳐서 반환
            return folders + files
            
        except ClientError as e:
            print(f"S3 ClientError: {e}")
            print(f"Error Code: {e.response['Error']['Code']}")
            print(f"Error Message: {e.response['Error']['Message']}")
            raise Exception(f"S3 파일 목록 조회 오류: {e}")
        except Exception as e:
            print(f"S3 일반 오류: {e}")
            print(f"오류 타입: {type(e)}")
            raise Exception(f"파일 목록 조회 중 오류 발생: {e}")
    
    def delete_file(self, s3_key):
        """S3에서 파일 삭제"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            raise Exception(f"S3 파일 삭제 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 삭제 중 오류 발생: {e}")
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        """파일 다운로드를 위한 사전 서명된 URL 생성"""
        if not self.s3_client:
            print("S3 클라이언트가 초기화되지 않았습니다. 작업을 건너뜁니다.")
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"사전 서명된 URL 생성 오류: {e}")
        except Exception as e:
            raise Exception(f"URL 생성 중 오류 발생: {e}")

# 전역 S3 서비스 인스턴스 (지연 초기화)
s3_service = None

def get_s3_service_instance():
    """S3 서비스 인스턴스를 지연 초기화로 가져오기"""
    global s3_service
    if s3_service is None:
        s3_service = S3Service()
    return s3_service
