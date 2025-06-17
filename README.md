# 선물옵션 자동매매 시스템

## 프로젝트 개요

Django 기반의 선물/옵션  자동매매 시스템입니다. OpenAPI를 활용하여 실시간 시장 데이터를 수집하고, 다양한 알고리즘 전략을 통해 기회를 포착하고 조건도달시 자동으로 매매하고 포지션 청산을 합니다. 

##  시스템 아키텍처

### 주요 구성 요소

- **Django 웹 프레임워크**: 메인 애플리케이션 서버
- **PostgreSQL**: 거래 데이터 및 포트폴리오 정보 저장
- **WebSocket**: 실시간 시장 데이터 수신
- **Channels**: Django 비동기 처리 및 WebSocket 
- **FastAPI**: 고성능 API 엔드포인트 (별도 모듈)
- **LS증권 OpenAPI**: 시장 데이터 및 주문 처리

### 애플리케이션 구조

```
simple_trading/
├── mysite/              # Django 프로젝트 설정
├── dashboard/           # 시스템 상태 모니터링
├── trading/             # 기본 트레이딩 기능 및 변동성 분석
├── order/               # 주문 처리 및 포트폴리오 관리
├── api_auth/            # API 인증 관리
├── src/                 # 핵심 트레이딩 로직
│   ├── tr/              # LS증권 API 래퍼
│   └── mathematics/     # 수학적 모델 (Black-Scholes 등)
├── fastapi_app/         # FastAPI 기반 고성능 API
└── optimization/        # 전략 최적화 모듈
```

##  주요 기능

### 1. 실시간 시장 데이터 처리
- **주간/야간 시장 지원**: 코스피200 선물 및 유렉스 야간 시장
- **실시간 호가/체결 데이터**: WebSocket을 통한 실시간 데이터 수신
- **다양한 상품 지원**: 선물, 옵션, 주식 등

### 2. 트레이딩 전략

#### FlexSwitch 전략 시리즈
- **Buy Dip 전략**: 가격 하락 시 매수 진입
- **Sell Dip 전략**: 가격 하락 시 매도 진입  
- **Buy Peak 전략**: 가격 상승 시 매수 진입
- **Sell Peak 전략**: 가격 상승 시 매도 진입

#### 변동성 기반 전략
- **변동성 매도 전략**: 내재변동성 분석을 통한 옵션 매도
- **Black-Scholes 모델**: 옵션 가격 산정 및 그릭스 계산
- **20-Delta 변동성 추적**: 실시간 변동성 모니터링

### 3. 포트폴리오 관리
- **실시간 PnL 계산**: 포지션별 손익 실시간 추적
- **자동 청산 시스템**: 
  - 목표 수익률 달성 시 청산
  - 시간 기반 청산 (최대 보유 시간)
  - 손실 한도 기반 청산
- **리스크 관리**: 포지션 크기 제한 및 위험 관리

### 4. 백그라운드 작업 관리
- **비동기 전략 실행**: 다중 전략 동시 실행
- **자동 모니터링**: 포트폴리오 상태 실시간 감시
- **작업 스케줄링**: 정기적인 데이터 수집 및 분석

## 기술 스택

### Backend
- **Django 5.1.4**: 웹 프레임워크
- **Django Channels**: WebSocket 및 비동기 처리
- **FastAPI**: 고성능 API 서버
- **PostgreSQL**: 메인 데이터베이스
- **Redis** (선택사항): 캐싱 및 세션 관리

### Data Processing
- **Pandas 2.2.3**: 데이터 분석 및 처리
- **NumPy 2.2.0**: 수치 계산
- **SciPy 1.14.1**: 과학 계산
- **Matplotlib 3.9.3**: 데이터 시각화

### API & Communication
- **httpx 0.28.1**: 비동기 HTTP 클라이언트
- **websockets 13.1**: WebSocket 클라이언트
- **aiohttp 3.11.10**: 비동기 HTTP 서버/클라이언트

### Deployment
- **WhiteNoise**: 정적 파일 서빙
- **Uvicorn**: ASGI 서버

## 📊 데이터 모델

### 핵심 모델

#### Portfolio
```python
- portfolio_id: 고유 포트폴리오 식별자
- timestamp: 생성 시간
- status: 상태 (Active, Pending, Closed)
- pnl: 실현/미실현 손익
- target_profit: 목표 수익
- strategy: 사용된 전략
- liquidation_condition: 청산 조건
```

#### Trade
```python
- portfolio: 포트폴리오 외래키
- order_id: 주문 번호
- focode: 상품 코드
- price: 체결 가격
- volume: 수량
- direction: 매수/매도 구분
- multiplier: 승수
```

#### VolatilityData
```python
- date_time: 데이터 시간
- iv_20: 20-Delta 내재변동성
- option_code: 옵션 코드
- future_code: 기초자산 코드
- option_greeks: 델타, 감마, 베가, 세타
```

## 🔧 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:
```env
# LS증권 OpenAPI 키 (테스트)
EBEST-OPEN-API-APP-KEY-FUTURES-TEST=your_app_key
EBEST-OPEN-API-SECRET-KEY-FUTURES-TEST=your_secret_key

# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@localhost:5432/trading_db

# Django 설정
SECRET_KEY=your_secret_key
DEBUG=True
```

### 3. 데이터베이스 설정

```bash
# 마이그레이션 실행
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser
```

### 4. 서버 실행

```bash
# Django 개발 서버
python manage.py runserver

# FastAPI 서버 (별도 터미널)
cd fastapi_app
uvicorn app.main:app --reload --port 8001
```

## 📈 사용법

### 1. 대시보드 접속
- 메인 대시보드: `http://localhost:8000`
- 관리자 페이지: `http://localhost:8000/admin`

### 2. 전략 실행

#### FlexSwitch 전략 시작
```bash
POST /order/start_flexswitch_strategy/
{
    "action": "start",
    "strategy_type": "buydip",
    "shcode": "105W5000",
    "period": "5",
    "threshold": "15",
    "buffer": "2",
    "interval": "1"
}
```

#### 변동성 전략 실행
```bash
POST /order/run_volatility_strategy/
```

### 3. 포트폴리오 모니터링
- 포트폴리오 목록: `/order/portfolios/`
- 실시간 스트림: `/order/portfolio_stream/`

## 🔍 API 엔드포인트

### 주요 엔드포인트

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/` | GET | 메인 대시보드 |
| `/order/portfolios/` | GET | 포트폴리오 목록 |
| `/order/start_flexswitch_strategy/` | POST | FlexSwitch 전략 시작/중지 |
| `/order/run_volatility_strategy/` | POST | 변동성 전략 실행 |
| `/order/check_strategy_status/` | GET | 전략 실행 상태 확인 |
| `/order/start_auto_liquidation_task/` | POST | 자동 청산 시작 |
| `/trading/calc_spot_vol/` | POST | 현물 변동성 계산 |

### WebSocket 엔드포인트
- `/ws/futures/{shcode}/`: 실시간 선물 가격 스트림

## 🧪 테스트

```bash
# 단위 테스트 실행
python manage.py test

# 특정 앱 테스트
python manage.py test order
python manage.py test trading
```

## 📝 로깅

- **DEBUG**: 상세한 실행 정보
- **INFO**: 일반적인 실행 상태
- **WARNING**: 주의가 필요한 상황
- **ERROR**: 오류 상황

로그 파일: `logs/debug_YYYYMMDD_HHMMSS.log`
