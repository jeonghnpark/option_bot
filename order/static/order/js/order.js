
let liquidationInterval = null;

let strategyIntervals = {
    buydip: null,
    selldip: null,
    buypeak: null,
    sellpeak: null,
};

let strategySellVolInterval = null;


document.addEventListener('DOMContentLoaded', function () {
    Object.keys(strategyIntervals).forEach(strategyType => {
        document.getElementById(`start_strategy_${strategyType}`).addEventListener('click', () => {
            startStrategy(strategyType);
        });

        // localStorage에서 전략 상태 복원
        const status = JSON.parse(localStorage.getItem(`${strategyType}Status`));
        if (status) {
            const button = document.getElementById(`start_strategy_${strategyType}`);
            button.textContent = `Stop ${strategyType}`;
            strategyIntervals[strategyType] = 'running';
        }
    });

    document.getElementById('start_strategy_sellvol').addEventListener('click', startVolStrategy);
    document.getElementById('start_auto_liquidation').addEventListener('click', startAutoLiquidation);
    document.getElementById('init_button').addEventListener('click', initialize);
    document.getElementById('price_button').addEventListener('click', get_price);
    document.getElementById('multi_order_button').addEventListener('click', placeMultiOrder);
    document.getElementById('multi_order_button_for_single_order').addEventListener('click', placeMultiOrderForSingleOrder);
    document.getElementById('set_vol_threshold').addEventListener('click', set_vol_threshold);

    //코드 변경시 자동으로 실행되는 코드
    document.getElementById('fut_code_select').addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        document.getElementById('fut_code').value = selectedOption.value;
        document.getElementById('shcode').value = selectedOption.value;
        document.getElementById('maturity').value = "20" + selectedOption.text.slice(-4);
    });

    //order/index.html 페이지가 로드되면 실행되는 코드
    initialize().then(() => {
    }).catch(error => {
        console.error('초기화 중 오류 발생:', error);
    });

});


function startStrategy(strategyType) {
    const button = document.getElementById(`start_strategy_${strategyType}`);
    const params = {
        shcode: document.getElementById(`${strategyType}_shcode`).value,
        period: document.getElementById(`${strategyType}_period`).value,
        threshold: document.getElementById(`${strategyType}_threshold`).value,
        buffer: document.getElementById(`${strategyType}_buffer`).value,
        liquidation_delay: document.getElementById(`${strategyType}_liquidation_delay`).value,
        monitoring_duration: document.getElementById(`${strategyType}_monitoring_duration`).value,
        interval: document.getElementById(`${strategyType}_interval`).value,
        strategy_type: strategyType,
        min_max_interval: document.getElementById('min-max-interval').value,
    };

    if (!strategyIntervals[strategyType]) {
        fetch('/order/start_flexswitch_strategy/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                ...params,
                action: 'start'
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`${strategyType} 전략 시작 서버응답오류`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    button.textContent = `Stop ${strategyType}`;
                    strategyIntervals[strategyType] = 'running';
                    localStorage.setItem(`${strategyType}Status`, JSON.stringify(true));
                } else if (data.status === 'already_running') {
                    alert(`${strategyType} strategy is already running`);
                    button.textContent = `Stop ${strategyType}`;
                    strategyIntervals[strategyType] = 'running';
                    localStorage.setItem(`${strategyType}Status`, JSON.stringify(true));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`${strategyType} 전략 시작 실패`);
            });
    } else {
        fetch('/order/start_flexswitch_strategy/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                strategy_type: strategyType,  //반드시 필요함?
                action: 'stop'
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`${strategyType} 전략 중지 서버응답오류`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' || data.status === 'not_running') {
                    button.textContent = `Start ${strategyType}`;
                    strategyIntervals[strategyType] = null;
                    localStorage.setItem(`${strategyType}Status`, JSON.stringify(false));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`${strategyType} 전략 중지 실패`);
            });
    }
}

function startAutoLiquidation() {
    const button = document.getElementById('start_auto_liquidation');
    if (!liquidationInterval) {
        //첫실행이라면 liquidationInterval==null
        fetch('/order/start_auto_liquidation_task/', {
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
                    button.textContent = 'Stop auto liquidation';
                    liquidationInterval = 'running';
                    localStorage.setItem('autoLiquidationStatus', JSON.stringify(true));
                    //dashboard업데이트
                    // updateAutoLiquidationStatus(true);
                    if (data.status === 'already_running') {
                        alert('자동청산이 이미 실행중입니다. ')
                    }
                }
            })
            .catch(error => {
                alert('자동청산 에러!!');
                // updateAutoLiquidationStatus(false);
            });
    } else { //실행중일때 stop하기 
        fetch('/order/start_auto_liquidation_task/', {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ action: 'stop' })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('자동청산 task 중지 서버응답오류')
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' || data.status === 'not_running') {
                    button.textContent = 'RESTART auto liquidation';
                    liquidationInterval = null;
                    localStorage.setItem('autoLiquidationStatus', JSON.stringify(false));
                    // updateAutoLiquidationStatus(false);
                    // 대시보드 상태 업데이트
                    // updateAutoLiquidationStatus(false);
                } else {
                    alert('알수없는 오류발생');
                    throw new Error(data.message || '알수없는 오류발생');
                }
            })
            .catch(error => {
                alert('자동청산 해지 실패');
                // updateAutoLiquidationStatus(true);
            });
    }
}


function set_vol_threshold() {
    const fut_code = document.getElementById('fut_code').value;
    const maturity = document.getElementById('maturity').value;

    fetch('/order/set_vol_threshold/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ fut_code: fut_code, maturity: maturity })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('cd_rate').value = data.cd_rate;
            document.getElementById('theta_vega_ratio').value = data.theta_vega_ratio.toFixed(4)

            const multiple = parseFloat(document.getElementById('vol_strategy_threshold_multiplier').value);
            const threshold = data.theta_vega_ratio * multiple;
            document.getElementById('vol_strategy_threshold').value = threshold.toFixed(4); // 소수점 4자리까지 표시

            console.log('Multiple:', multiple);
            console.log('Calculated threshold:', threshold);
        })
        .catch(error => {
            console.error("Error:", error);
        });
}


function startVolStrategy() {
    // const auto_order_resultContainer = document.getElementById('auto_order_result');
    // console.log('monvol and order ')
    const button = document.getElementById('start_strategy_sellvol');
    const params = {

    }
    fetch('/order/run_volatility_strategy/', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },

    })
        .then(response => response.json())
        .then(data => {
            if (typeof data.result === 'object' && data.result !== null) {
                let resultHTML = '<ul>';
                for (const [key, value] of Object.entries(data.result)) {
                    if (key === "order_results") {
                        console.log("order_results", value);
                    }
                    if (key === 'order_results' && Array.isArray(value)) {
                        console.log("wow");
                        resultHTML += `<li><strong>${key}:</strong><ul>`;
                        value.forEach((order, index) => {
                            resultHTML += `<li>주문 ${index + 1}:<ul>`;
                            for (const [orderKey, orderValue] of Object.entries(order)) {
                                resultHTML += `<li><strong>${orderKey}:</strong> ${orderValue}</li>`;
                            }
                            resultHTML += '</ul></li>';
                        });
                        resultHTML += '</ul></li>';
                    } else {
                        resultHTML += `<li><strong>${key}:</strong> ${value}</li>`;
                    }
                }
                resultHTML += '</ul>';
                auto_order_resultContainer.innerHTML = resultHTML;
            } else {
                // 객체가 아닌 경우 그대로 표시
                auto_order_resultContainer.innerHTML = data.result;
            }

        })
        .catch(error => {
            console.error('Error:', error);
            auto_order_resultContainer.innerHTML = 'Error occurred while fetching data.';
        });
}

function initialize() {
    return new Promise((resolve, reject) => {
        fetch('/trading/init/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(response => response.json())
            .then(data => {
                const futCodeSelect = document.getElementById('fut_code_select');
                futCodeSelect.innerHTML = '';
                let firstFuture = null;

                data.listed_fut.forEach((fut, index) => {
                    const option = document.createElement('option');
                    option.value = fut.shcode;
                    option.text = fut.hname;
                    if (index == 0) {
                        firstFuture = option;
                        option.selected = true;
                        document.getElementById('fut_code').value = option.value;
                        document.getElementById('shcode').value = option.value;
                        document.getElementById('maturity').value = "20" + option.text.slice(-4);

                        document.getElementById('buydip_shcode').value = option.value;
                        document.getElementById('buypeak_shcode').value = option.value;
                        document.getElementById('selldip_shcode').value = option.value;
                        document.getElementById('sellpeak_shcode').value = option.value;
                    }
                    futCodeSelect.add(option);
                });
                resolve(); // 초기화 완료
            })
            .catch(error => {
                console.error("Error:", error);
                reject(error);
            });
    });
}


function get_price() {
    const fut_code = document.getElementById('fut_code').value;
    const orderbook_display_bid = document.getElementById('orderbook_display_bid')
    const orderbook_display_ask = document.getElementById('orderbook_display_ask')

    fetch('/order/price/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ fut_code: fut_code }),
    }).then(response => response.json())
        .then(data => {
            const bidho1 = data.orderbook_data['bidho1'];
            const offerho1 = data.orderbook_data['offerho1'];
            orderbook_display_bid.value = `${bidho1}`;
            orderbook_display_ask.value = `${offerho1}`;

        })
}

function placeMultiOrder() {
    console.log('place multi order')
    const orders = [];
    const orderItems = document.querySelectorAll('.order_item');

    orderItems.forEach((item, index) => {
        const focode = document.getElementById(`focode_${index + 1}`).value;
        if (focode.trim() !== '') {
            console.log(`${focode} was ok`)
            const order = {
                focode: focode,
                quantity: document.getElementById(`quantity_${index + 1}`).value,
                direction: document.getElementById(`direction_${index + 1}`).value,
                order_type: document.getElementById(`order_type_${index + 1}`).value,
                order_price: document.getElementById(`order_price_${index + 1}`).value,
                portfolio_id: null
            };
            if (order.order_type === "market") {
                order.order_price = null;
                console.log('market order..')
            }
            orders.push(order);
        }

    });
    orders.forEach((order, index) => {
        console.log(`Order ${index + 1}:`, JSON.stringify(order, null, 2));
    });

    if (orders.length === 0) {
        const multiOrderResultContainer = document.getElementById('multi_order_result');
        multiOrderResultContainer.innerHTML = '<p>No valid orders to place.</p>';
        return;
    }

    console.log(JSON.stringify({ orders: orders }));
    fetch('/order/manual_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ orders: orders })
    })
        .then(response => response.json())
        .then(data => displayMultiOrderResults(data))
        .catch(error => {
            console.error('Error:', error);
            const multiOrderResultContainer = document.getElementById('multi_order_result');
            multiOrderResultContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

function placeMultiOrderForSingleOrder() {
    console.log('place multi order for single')
    const orders = [];

    const order = {
        focode: document.getElementById('focode').value,
        quantity: document.getElementById('quantity').value,
        direction: document.getElementById('direction').value,
        order_type: document.getElementById('order_type').value,
        order_price: document.getElementById('order_price').value,
        portfolio_id: null,
    };
    if (order.order_type === "market") {
        order.order_price = null;
        console.log('market order..')
    }
    orders.push(order)

    const liquidation_condition = document.getElementById('liquidation_condition').value;
    const liquidation_value = document.getElementById('liquidation_value').value;
    console.log(JSON.stringify({ orders: orders, liquidation_condition: liquidation_condition, liquidation_value: liquidation_value }));
    fetch('/order/manual_order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            orders: orders,
            order_category: 'new',
            liquidation_condition: liquidation_condition,
            liquidation_value: liquidation_value
        })
    })
        .then(response => response.json())
        .then(data => displayMultiOrderResults(data))
        .catch(error => {
            console.error('Error:', error);
            const multiOrderResultContainer = document.getElementById('multi_order_result');
            multiOrderResultContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

function displayMultiOrderResults(data) {
    const multiOrderResultContainer = document.getElementById('multi_order_result');
    let resultHTML = '<h5>Multi-Order Results:</h5>';
    data.results.forEach((result, index) => {
        resultHTML += `<p>Order ${index + 1}:<br>`;
        resultHTML += `Status: ${result.status}<br>`;
        resultHTML += `Order ID: ${result.order_id || 'N/A'}<br>`;
        if (result.error) {
            resultHTML += `Error: ${result.error}<br>`;
        }
        resultHTML += '</p>';
    });
    multiOrderResultContainer.innerHTML = resultHTML;
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
