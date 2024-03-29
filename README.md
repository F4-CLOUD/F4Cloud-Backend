# F4CLOUD-BackEnd

- 독보적인 검색 기능을 가진 클라우드 제공
- 핵심 기능
  - 문서 검색
  - 사진에서 인물 검색
  - 물체 인식을 통한 자동 해시태그 및 해시태그 검색
  
- 조장 : 김서현
- 팀원 : 노서연, 이상화, 장규범, 황성연

- 역할
  - Front-End Developer : 장규범, 황성연
  - Back-End Developer : 김서현, 노서연, 이상화
- 개발환경
  - Front-End 개발 환경 : React.js / TypeScript
  - Back-End 개발 환경 : Django, MySQL
  - AWS EC2, S3, Rekognition
  - Google Maps API

## How to run

### Install Module
```shelly
pip install -r requirements.txt
```

### Config.ini
```text
[DB]
ENGINE=django.db.backends.mysql     # DB 엔진 설정 (현재 MySQL 엔진 선택되있음)
NAME=                               # DB Schema 설정
HOST=                               # Host 설정
PORT=                               # Port 설정
USER=                               # User 설정
PASSWORD=                           # Password 설정

[AWS]
ACCESS_KEY_ID=                      # AWS Access Key
SECRET_ACCESS_KEY=                  # AWS Secret Access Key
ACCOUNTID=                          # 계정 ID
IDENTITY_POOL_ID=                   # Cognito 연동 자격 증명 풀 ID
DEFAULT_REGION_NAME=                # 지역 이름
DEFAULT_USER_POOL_ID=               # Cognito 풀 ID
DEFAULT_USER_POOL_APP_ID=           # Cognito 앱 클라이언트 ID
```

### Migration
```shelly
# Create Migration File
python manage.py makemigrations files
python manage.py makemigrations folders

# Migrate
python manage.py migrate
```

### App 실행
```shelly
python manage.py runserver
```

## Code Convention

### Dir 구조

```bash
├── README.md
├── config.ini      # 직접 추가해야 함
├── utils
│   ├── s3.py
│   └── cognito.py
├── f4cloud
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── files
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── folders
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── users
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── manage.py
└── requirements.txt
```
