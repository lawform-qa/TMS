import boto3
import os
from datetime import datetime
from flask import current_app
import json
from botocore.exceptions import ClientError, NoCredentialsError

class S3Service:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'test-platform-scripts')
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
            else:
                print(f"버킷 접근 오류: {e}")
    
    def upload_file(self, file_path, s3_key, content_type=None):
        """파일을 S3에 업로드"""
        if not self.s3_client:
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
        """S3에서 파일 목록 조회"""
        if not self.s3_client:
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                    })
            
            return files
            
        except ClientError as e:
            raise Exception(f"S3 파일 목록 조회 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 목록 조회 중 오류 발생: {e}")
    
    def delete_file(self, s3_key):
        """S3에서 파일 삭제"""
        if not self.s3_client:
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
            raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
        
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
