
let autoLiquidationCheckInterval = null;
let portfolioMonitorCheckInterval = null;

let strategyCheckIntervals = {
    buydip: null,
    selldip: null,
    buypeak: null,
    sellpeak: null,
};


// DOM 로드 시 실행
document.addEventListener('DOMContentLoaded', function () {
    // 모든 전략  초기 상태 체크
    checkAllStrategiesStatus();
    checkAutoLiquidationStatus();
    checkPortfolioMonitorStatus();

    // 30초마다 모든 전략 상태 체크 설정
    Object.keys(strategyCheckIntervals).forEach(strategy => {
        strategyCheckIntervals[strategy] = setInterval(() => checkStrategyStatus(strategy), 30000);
    });

    autoLiquidationCheckInterval = setInterval(checkAutoLiquidationStatus, 30000);
    portfolioMonitorCheckInterval = setInterval(checkPortfolioMonitorStatus, 30000);

    // localStorage 변경 이벤트 감지
    window.addEventListener('storage', function (e) {
        const strategyTypes = ['buydip', 'selldip', 'buypeak', 'sellpeak'];
        if (strategyTypes.includes(e.key.replace('Status', ''))) {
            updateStrategyStatus(e.key.replace('Status', ''), JSON.parse(e.newValue));
        }
    });

    window.addEventListener('storage', function (e) {
        if (e.key === 'autoLiquidationStatus') {
            updateAutoLiquidationStatus(JSON.parse(e.newValue));
        }
    });
    window.addEventListener('storage', function (e) {
        if (e.key === 'portfolioMonitorStatus') {
            updatePortfolioMonitorStatus(JSON.parse(e.newValue));
        }
    });
});

function checkStrategyStatus(strategyType) {
    fetch(`/order/check_strategy_status/?strategy=${strategyType}`)
        .then(response => response.json())
        .then(data => {
            localStorage.setItem(`${strategyType}Status`, JSON.stringify(data.is_running));
            updateStrategyStatus(strategyType, data.is_running);
        })
        .catch(error => {
            console.error(`${strategyType} 전략 상태 확인중 오류:`, error);
            localStorage.setItem(`${strategyType}Status`, JSON.stringify(false));
            updateStrategyStatus(strategyType, false);
        });
}

function updateStrategyStatus(strategyType, isActive) {
    const circle = document.getElementById(`${strategyType}-circle`);
    const statusText = document.getElementById(`${strategyType}-status-text`);

    if (!circle || !statusText) return;

    if (isActive) {
        circle.classList.remove('status-inactive');
        circle.classList.add('status-active');
        statusText.textContent = `${strategyType}: 활성화`;
    } else {
        circle.classList.remove('status-active');
        circle.classList.add('status-inactive');
        statusText.textContent = `${strategyType}: 비활성화`;
    }
}


function checkAllStrategiesStatus() {
    const strategies = ['buydip', 'selldip', 'buypeak', 'sellpeak'];
    strategies.forEach(strategy => checkStrategyStatus(strategy));

}

function checkAutoLiquidationStatus() {
    fetch('/order/check_auto_liquidation_status/')
        .then(response => response.json())
        .then(data => {

            localStorage.setItem('autoLiquidationStatus', JSON.stringify(data.is_running));
            console.log(`자동청산상태${data.is_running}`)
            updateAutoLiquidationStatus(data.is_running);
        })
        .catch(error => {
            console.error('자동청산 상태 확인중 오류', error);
            localStorage.setItem('autoLiquidationStatus', JSON.stringify(false));
            updateAutoLiquidationStatus(false);
        });
}

// buydip 전략 상태 확인
function checkBuydipStatus() {
    // console.log('checkBuydipStatus');
    fetch('/order/check_buydip_status/')
        .then(response => response.json())
        .then(data => {
            // localStorage에 상태 저장
            localStorage.setItem('buydipStatus', JSON.stringify(data.is_running));
            console.log(`buydip status ${data.is_running}`)
            updateBuydipStatus(data.is_running);
        })
        .catch(error => {
            console.error('매수전략 상태 확인 중 오류:', error);
            localStorage.setItem('buydipStatus', JSON.stringify(false));
            updateBuydipStatus(false);
        });
}

function updateAutoLiquidationStatus(isActive) {
    const circle = document.getElementById('auto-liquidation-circle');
    const statusText = document.getElementById('auto-liquidation-status-text');
    if (isActive) {
        circle.classList.remove('status-inactive');
        circle.classList.add('status-active');
        statusText.textContent = '자동청산:활성화';
    } else {
        circle.classList.remove('status-active');
        circle.classList.add('status-inactive');
        statusText.textContent = '자동청산:비활성화';

    }
}

function checkPortfolioMonitorStatus() {
    fetch('/order/check_portfolio_monitor_status/')
        .then(response => response.json())
        .then(data => {
            localStorage.setItem('portfolioMonitorStatus', JSON.stringify(data.is_running));
            updatePortfolioMonitorStatus(data.is_running);
        })
        .catch(error => {
            console.error('포트폴리오 모니터링 상태 확인 중 오류:', error);
            localStorage.setItem('portfolioMonitorStatus', JSON.stringify(false));
            updatePortfolioMonitorStatus(false);
        });
}

function updatePortfolioMonitorStatus(isActive) {
    const circle = document.getElementById('portfolio-monitor-circle');
    const statusText = document.getElementById('portfolio-monitor-status-text');
    if (isActive) {
        circle.classList.remove('status-inactive');
        circle.classList.add('status-active');
        statusText.textContent = '포트폴리오 모니터링:활성화';
    } else {
        circle.classList.remove('status-active');
        circle.classList.add('status-inactive');
        statusText.textContent = '포트폴리오 모니터링:비활성화';
    }
}
