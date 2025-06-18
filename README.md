# 선물옵션 자동매매 시스템

**Made by: 박정현 (jh70035@gmail.com)**

## 프로젝트 개요

본 프로젝트는 단순한 매매 시그널 생성이나 수익률 예측을 넘어, 실제 거래의 전 과정을 자동화하는 것을 목표로 하는 Django 기반 선물/옵션 자동매매 시스템입니다. OpenAPI를 통해 실시간 시장 데이터를 수집하고, 사전에 정의된 다양한 알고리즘 전략에 따라 매매 기회를 포착합니다.

시스템은 전략에 따라 자동으로 주문을 실행하고, 거래내역을 DB에 저장하고 실시간으로 포지션의 손익(P&L)을 추적합니다. 이후, 설정된 목표 수익 달성, 손실 한도 도달, 또는 시간 기반 조건 등 미리 정의된 청산 조건이 충족되면 포지션을 자동으로 청산하여 전체 거래를 마무리합니다.

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


## 데이터 모델

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

## 스크린샷

### 1. 시장 데이터 모니터링
- 실시간 시세, 호가, 변동성 등 시장 데이터를 관찰하고 기회를 포착합니다.
![시장 데이터 모니터링](media/market_monitoring.png)

### 2. 전략 구성 및 주문
- 다양한 전략(FlexSwitch, 변동성)을 설정하고 주문을 실행합니다.
![전략 구성 및 주문](media/strategy_order.png)

### 3. 포트폴리오 및 손익(P/L) 관리
- 체결된 주문 내역과 실시간 손익(P/L), 포지션 상태(대기/청산)를 추적합니다.
![포트폴리오 및 손익 관리](media/portfolio.png)


## 🔧 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 파이썬 경로 설정 (.pth 파일)

프로젝트의 `src` 폴더와 루트 폴더를 파이썬 경로에 추가하여 모듈을 올바르게 인식시키기 위해 `.pth` 파일을 설정해야 합니다.

가상환경의 `site-packages` 디렉토리 안에 `_custom_paths.pth`와 같은 파일을 생성하고, 아래와 같이 프로젝트의 **절대 경로**를 추가합니다.

- **`site-packages` 경로 예시**:
  - Windows: `.venv\Lib\site-packages\`
  - macOS/Linux: `.venv/lib/pythonX.X/site-packages/`

- **`.pth` 파일 내용 예시** (`D:\dev\option_bot`에 프로젝트가 있는 경우):
  ```
  D:\dev\option_bot
  D:\dev\option_bot\src
  ```

위 예시의 `D:\dev\option_bot` 부분을 자신의 실제 프로젝트 경로로 수정하여 사용하세요.

### 3. 환경 변수 설정

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

### 4. 데이터베이스 설정

```bash
# 마이그레이션 실행
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser
```

### 5. 서버 실행

```bash
# Django 개발 서버
python manage.py runserver

# Uvicorn 서버 실행행
uvicorn mysite.asgi:application --reload
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

## API 엔드포인트

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



## 로깅

- **DEBUG**: 상세한 실행 정보
- **INFO**: 일반적인 실행 상태
- **WARNING**: 주의가 필요한 상황
- **ERROR**: 오류 상황

로그 파일: `logs/debug_YYYYMMDD_HHMMSS.log`
