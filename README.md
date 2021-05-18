# F4CLOUD-BackEnd

- 독보적인 검색 기능을 가진 클라우드 제공
- 핵심 기능
  - 문서를 중심으로 검색을 진행할 때 키워드 검색을 해서 제목에 포함된, 내용도 포함된 검색 결과 구현
  - 과목 별 자동 분류 [CL], [DB], [CD1]
  - 문서 내에서 최다 빈도수, 자동 해시태그
  - 사진에서 인물 검색
  - 사물 검색
  - 사진에 있는 텍스트 검색
  - 지도 API를 사용하여 클라우드에서 기능 제공(장소에서 찍은 사진을 지도에서 띄워주는 기능)
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
├── f4cloud
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── files
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── folders
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── manage.py
└── requirements.txt
```
