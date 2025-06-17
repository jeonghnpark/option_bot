let fetchPortfolioInterval = null;
let isFetchingPortfolio = false;
let eventSource = null;

document.addEventListener('DOMContentLoaded', function () {
    const portfolioTable = document.querySelector('table tbody');
    portfolioTable.addEventListener('click', function (e) {
        if (e.target.classList.contains('liquidate-link')) {
            e.preventDefault();
            const portfolio_id = e.target.getAttribute('data-portfolio-id');
            liquidatePortfolio(portfolio_id);
            console.log(portfolio_id);
        }
    });
    document.getElementById("start-stream-portfolios").addEventListener("click", startPortfolioStream);
    document.getElementById("start-fetch").addEventListener("click", startFetch);
    document.getElementById("view-portfolios-once").addEventListener("click", fetchPortfoliosWithTime);
});


function formatPnl(number) {
    const roundedNumber = Math.round(number);
    return roundedNumber.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

}

function startPortfolioStream() {
    //background 매니저 없는 버전
    if (eventSource) {
        eventSource.close();
    }
    eventSource = new EventSource('/order/portfolio_stream/');

    eventSource.onmessage = function (event) { //eventsource에서 송출(yield)되는 경우
        const data = JSON.parse(event.data);
        // console.log('송출된 데이터:', {
        //     total_pnl_today: data.total_pnl_today,
        //     strategy_pnl: data.strategy_pnl,
        //     portfolios: data.portfolios
        // })
        updatePortfolioUI(data);
    };

    eventSource.onerror = function (error) {
        console.error('EventSource failed:', error);
        eventSource.close();
    };
}

function updatePortfolioUI(data) {
    const totalPnlSpan = document.getElementById('total-pnl-today');
    const strategyPnlList = document.getElementById('strategy-pnl-list');

    // 기존 UI 업데이트 로직 재사용
    totalPnlSpan.textContent = `오늘 P&L: ${formatPnl(data.total_pnl_today)}`;

    strategyPnlList.innerHTML = '';
    for (const [strategy, pnl] of Object.entries(data.strategy_pnl)) {
        const li = document.createElement('li');
        li.textContent = `${strategy}: ${formatPnl(pnl)}`;
        strategyPnlList.appendChild(li);
    }

    const portfolioTable = document.querySelector('table tbody');
    portfolioTable.innerHTML = '';

    data.portfolios.forEach(portfolio => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${portfolio.portfolio_id}</td>
            <td>${new Date(portfolio.timestamp).toLocaleString()}</td>
            <td><a href="#" onclick="openCenteredWindow('/order/portfolios/${portfolio.portfolio_id}/'); event.preventDefault();">상세 거래 보기</a></td>
            <td>${portfolio.status}</td>
            <td>${formatPnl(portfolio.pnl)}</td>
            <td><a href="#" class="liquidate-link" data-portfolio-id="${portfolio.portfolio_id}">바로청산</a></td>
            <td>${portfolio.target_profit !== null ? formatPnl(portfolio.target_profit) : portfolio.target_profit}</td>
            <td>${portfolio.strategy}</td>
            <td>${portfolio.description}</td>
            <td>${portfolio.liquidation_condition}</td>
        `;
        portfolioTable.appendChild(row);
    });

    updateLastFetchTime();
}
///////////////end of portfolio streaming /////////


function fetchPortfolios() {
    const totalPnlSpan = document.getElementById('total-pnl-today');
    const strategyPnlList = document.getElementById('strategy-pnl-list');
    fetch("/order/fetchPortfolios_async/")
        .then(response => response.json())
        .then(data => {
            totalPnlSpan.textContent = `오늘 P&L: ${formatPnl(data.total_pnl_today)}`;

            strategyPnlList.innerHTML = '';
            for (const [strategy, pnl] of Object.entries(data.strategy_pnl)) {
                const li = document.createElement('li');
                li.textContent = `${strategy}: ${formatPnl(pnl)}`;
                strategyPnlList.appendChild(li);
            }
            const portfolioTable = document.querySelector('table tbody');
            portfolioTable.innerHTML = '';

            data.portfolios.forEach(portfolio => {
                const row = document.createElement('tr');
                row.innerHTML = `
            <td>${portfolio.portfolio_id}</td>
            
            <td>${new Date(portfolio.timestamp).toLocaleString()}</td>

            <td><a href="#" onclick="openCenteredWindow('/order/portfolios/${portfolio.portfolio_id}/'); event.preventDefault();">상세 거래 보기</a></td>
            <td>${portfolio.status}</td>
            <td>${formatPnl(portfolio.pnl)}</td>
            
            <td><a href="#" class="liquidate-link" data-portfolio-id="${portfolio.portfolio_id}">바로청산</a></td>
            <td>${portfolio.target_profit !== null ? formatPnl(portfolio.target_profit) : portfolio.target_profit}</td>
            <td>${portfolio.strategy}</td>
            <td>${portfolio.description}</td>
            <td>${portfolio.liquidation_condition}</td>
          `;
                portfolioTable.appendChild(row);
            });
        });
}

function updateLastFetchTime() {
    const now = new Date();
    lastFetchTime = now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
    const lastFetchSpan = document.getElementById('last-fetch-time');
    if (lastFetchSpan) {
        lastFetchSpan.textContent = `마지막 조회: ${lastFetchTime}`;
    } else {
        const button = document.getElementById('start-fetch');
        const span = document.createElement('span');
        span.id = 'last-fetch-time';
        span.textContent = `마지막 조회: ${lastFetchTime}`;
        button.parentNode.insertBefore(span, button.nextSibling);
    }
}

function fetchPortfoliosWithTime() {
    fetchPortfolios();
    updateLastFetchTime();
}


function startFetch_old() {
    const button = document.getElementById('start-fetch');
    if (!isFetchingPortfolio) {

        fetchPortfoliosWithTime();

        fetchPortfolioInterval = setInterval(fetchPortfoliosWithTime, 10000);
        isFetchingPortfolio = true;
        if (button) {
            button.textContent = '포트폴리오 연속조회 중지';
        }
    } else {

        if (fetchPortfolioInterval) {
            clearInterval(fetchPortfolioInterval);
        }
        isFetchingPortfolio = false;

        if (button) {
            button.textContent = '포트폴리오 연속조회';
        }

    }
}

function startFetch() {
    const button = document.getElementById('start-fetch');
    if (!isFetchingPortfolio) {
        fetch('/order/start_portfolio_monitor_task/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ action: 'start' })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' || data.status === 'already_running') {
                    //running중일때 페이지를 reload하는 경우 !isFetchingPortfolio 이면서 already_running 
                    button.textContent = '포트폴리오 연속조회 중지';
                    isFetchingPortfolio = true;
                    localStorage.setItem('portfolioMonitorStatus', JSON.stringify(true));
                    // 스트림 시작
                    startPortfolioStream();  // 이미 구현된 SSE 리스너 시작
                    if (data.status === 'already_running') {
                        alert('포트폴리오 모니터링이 이미 실행중입니다.');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('포트폴리오 모니터링 시작 중 오류가 발생했습니다.');
            });
    } else {
        if (eventSource) {
            eventSource.close();  // SSE 연결 종료
        }

        fetch('/order/start_portfolio_monitor_task/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ action: 'stop' })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' || data.status === 'not_running') {
                    button.textContent = '포트폴리오 연속조회';
                    isFetchingPortfolio = false;
                    localStorage.setItem('portfolioMonitorStatus', JSON.stringify(false));

                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('포트폴리오 모니터링 중지 중 오류가 발생했습니다.');
            });
    }
}


function liquidatePortfolio(portfolio_id) {
    console.log('liquidate....')
    if (confirm('이 포트폴리오를 직접 청산하시겠습니까?')) {
        fetch(`/order/liquidate/${portfolio_id}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let message = `${data.message}\n\n결과:\n${JSON.stringify(data.result, null, 2)}`;
                    alert(message);
                    // window.location.href = data.redirect_url;
                } else {
                    alert('청산이 완료되지 않거나 문제가 발생하였습니다.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('청산 요청 중 오류가 발생했습니다.');
            });
    }
}


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

