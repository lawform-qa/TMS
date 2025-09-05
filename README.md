# 🚀 Integrated Test Platform

## 📋 프로젝트 개요

통합 테스트 플랫폼은 다양한 테스트 유형(API, 성능, 자동화)을 통합 관리할 수 있는 웹 기반 플랫폼입니다.

## ✨ 주요 기능

- **🧪 Test Cases**: 테스트 케이스 관리 및 실행
- **⚡ Performance Tests**: K6 기반 성능 테스트
- **🤖 Automation Tests**: Playwright 기반 자동화 테스트
- **📁 Folder Management**: 계층적 폴더 구조 관리
- **📊 Dashboard**: 테스트 결과 통계 및 분석
- **👥 User Management**: 사용자 및 프로젝트 관리
- **🌍 KST 시간대**: 한국 표준시 기반 일관된 시간 처리
- **☁️ S3 Integration**: AWS S3를 통한 테스트 스크립트 클라우드 저장
- **💻 Code Editor**: Monaco Editor 기반 고급 코드 에디터
- **📝 Script Management**: 테스트 스크립트 생성, 편집, 관리

## 🏗️ 기술 스택

### Backend
- **Python 3.13+**
- **Flask 2.3+**
- **SQLAlchemy 2.0+**
- **MySQL 8.0+**
- **Docker**
- **pytz**: KST 시간대 처리
- **boto3**: AWS S3 연동

### Frontend
- **React 18+**
- **Axios**
- **Chart.js**
- **Monaco Editor**: 고급 코드 에디터

### Testing Tools
- **K6** (성능 테스트)
- **Playwright** (자동화 테스트)

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone <repository-url>
cd integrated-test-platform
```

### 2. 백엔드 실행
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 3. 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

### 4. 데이터베이스 설정
```bash
# Docker로 MySQL 실행
docker-compose up -d mysql

# 또는 docs/mysql-init/ 스크립트 실행
```

## 📁 프로젝트 구조

```
integrated-test-platform/
├── backend/                 # Flask 백엔드
│   ├── app.py              # 메인 애플리케이션
│   ├── models.py           # 데이터베이스 모델
│   ├── routes/             # API 라우트
│   ├── utils/              # 유틸리티 함수
│   │   └── timezone_utils.py # KST 시간대 처리
│   └── engines/            # 테스트 엔진 (K6, Playwright)
├── frontend/                # React 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── contexts/       # React Context
│   │   ├── pages/          # 페이지 컴포넌트
│   │   └── config.js       # API 설정
│   └── package.json
├── docs/                    # 문서 및 설정 파일
│   ├── postman_collection_v2.json
│   ├── postman_environment_v2.json
│   ├── PERMISSION_GUIDE.md # 권한별 기능 가이드
│   ├── API_TESTING_GUIDE.md # API 테스트 가이드
│   ├── TESTING_GUIDE.md    # 테스트 가이드
│   └── PROJECT_STRUCTURE.md # 프로젝트 구조
├── test-scripts/            # 테스트 스크립트
│   ├── performance/        # K6 성능 테스트
│   └── playwright/         # Playwright 자동화 테스트
└── README.md               # 이 파일
```

## 🔐 권한 시스템

이 플랫폼은 **admin**, **user**, **guest** 세 가지 사용자 역할을 지원합니다.

- **📖 [권한별 기능 가이드](docs/PERMISSION_GUIDE.md)** - 각 역할별 접근 가능한 기능 상세 설명
- **🛡️ JWT 기반 인증** - 보안된 API 접근
- **🔒 역할 기반 접근 제어** - 사용자 권한에 따른 기능 제한

## 🌍 시간대 처리

- **KST (한국 표준시) 기반**: 모든 시간 데이터를 KST로 일관되게 처리
- **백엔드**: `utils/timezone_utils.py`를 통한 KST 시간 생성 및 변환
- **데이터베이스**: 모든 타임스탬프를 KST로 저장
- **API 응답**: KST 시간 형식으로 응답

## 🌐 배포

### Vercel 배포
- **Backend**: `https://backend-alpha-liard.vercel.app`
- **Frontend**: `https://integrated-test-platform-dydlxktca-gyeonggong-parks-projects.vercel.app`

### 환경 변수
```bash
DATABASE_URL=mysql+pymysql://user:password@host:port/database
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

## 📚 문서

- **API 가이드**: `docs/API_TESTING_GUIDE.md`
- **Postman 사용법**: `docs/POSTMAN_USAGE_GUIDE.md`
- **프로젝트 구조**: `docs/PROJECT_STRUCTURE.md`
- **배포 요약**: `docs/DEPLOYMENT_SUMMARY.md`
- **테스트 가이드**: `docs/TESTING_GUIDE.md`
- **권한 가이드**: `docs/PERMISSION_GUIDE.md`

## 🧪 테스트

### API 테스트
```bash
# Postman Collection 사용
docs/postman_collection_v2.json
```

### 성능 테스트
```bash
cd test-scripts/performance
k6 run script.js
```

### 자동화 테스트
```bash
cd test-scripts/playwright
npx playwright test
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 🆕 최신 기능 (v2.2.0)

### ☁️ S3 통합 테스트 스크립트 관리
- **클라우드 저장**: AWS S3를 통한 테스트 스크립트 클라우드 저장
- **운영 환경 호환**: 로컬 파일 의존성 제거로 운영 환경에서 완전 동작
- **실시간 편집**: Monaco Editor를 통한 고급 코드 편집 기능
- **파일 관리**: 업로드, 다운로드, 삭제, 편집 등 완전한 파일 관리
- **다중 언어 지원**: JavaScript, Python, JSON, Markdown 등 다양한 언어 지원

### 💻 고급 코드 에디터
- **Monaco Editor**: VS Code와 동일한 편집 경험
- **구문 강조**: 프로그래밍 언어별 자동 구문 강조
- **자동 완성**: 스마트 자동 완성 및 IntelliSense
- **폴딩**: 코드 블록 접기/펼치기
- **다크 모드**: 눈에 편한 다크 테마 지원

### 📁 통합 파일 관리
- **탭 기반 UI**: 테스트 케이스와 테스트 스크립트를 탭으로 분리
- **S3/로컬 전환**: 클라우드와 로컬 파일 시스템 간 쉬운 전환
- **드래그 앤 드롭**: 직관적인 파일 업로드
- **실시간 미리보기**: 파일 내용을 즉시 확인하고 편집

## 📞 연락처

- 프로젝트 링크: [https://github.com/username/integrated-test-platform](https://github.com/username/integrated-test-platform)
- E-Mail : [bakgg93@gmail.com](bakgg93@gmail.com)
- H.P : 010-8496-1463

---

**마지막 업데이트**: 2025년 1월 9일  
**버전**: 2.2.0  
**상태**: 프로덕션 배포 완료 ✅  
**주요 업데이트**: S3 통합, 코드 에디터, 클라우드 스크립트 관리
