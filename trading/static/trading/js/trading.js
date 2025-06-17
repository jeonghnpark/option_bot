
let graphInterval;
let ivolInterval;
let isCalVol = false;
let isLoadGraph = false;

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('load_graph').addEventListener('click', loadGraph);
    document.getElementById('init_button').addEventListener('click', init);
    document.getElementById("impvol").addEventListener('click', function () {
        impvol();
    });
    document.getElementById('calc_vol_continue').addEventListener('click', calcVolContinue);
    document.getElementById('historic_data').addEventListener('click', historical_vol);

});  //for DOMContentLoaded

function historical_vol() {
    const selectedIndex = document.getElementById('fut_code_select').selectedIndex
    const yymm = document.getElementById('fut_code_select').options[selectedIndex].text.slice(-4);
    console.log(yymm)
    const cd_rate = document.getElementById('cd_rate')

    fetch('/trading/historic/', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 'yymm': yymm })
    })
        .then(response => response.json())
        .then(data => {
            // const successMessage = document.createElement('div');
            // successMessage.textContent = "과거데이터 로딩 성공";
            // document.body.appendChild(successMessage);
        })
        .catch(error => {
            console.error("Error:", error);
        });
}

function calcVolContinue() {
    const button = document.getElementById('calc_vol_continue');
    if (!isCalVol) {
        impvol();
        if (ivolInterval) {
            clearInterval(ivolInterval);
        }

        ivolInterval = setInterval(impvol, 10000);
        button.textContent = 'stop calculating vol';
        isCalVol = true;
    } else {
        button.textContent = 'continue calculating vol';
        clearInterval(ivolInterval);
        isCalVol = false;
    }
}

function init() {
    fetch('/trading/init/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('cd_rate').value = data.cd_rate;
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
                    document.getElementById('maturity').value = "20" + option.text.slice(-4);
                }
                futCodeSelect.add(option);
            });
        })
        .catch(error => {
            console.error("Error:", error);
        });
}

function stopGraph() {
    if (graphInterval) {
        clearInterval(graphInterval);
        graphInterval = null;
        console.log('graph was stopped');
    }
}

function stopIvol() {
    if (ivolInterval) {
        clearInterval(ivolInterval);
        ivolInterval = null;
        console.log('ivol calc was stopped');
    }
}


function loadGraph() {
    let vol_threshold = parseFloat(document.getElementById('vol_threshold').value);
    if (isNaN(vol_threshold) || vol_threshold === undefined) {
        vol_threshold = 0.25;
    }
    console.log("vol_threshold: " + vol_threshold)
    const img = document.getElementById('volGraph');
    const button = document.getElementById('load_graph');
    if (!isLoadGraph) {
        img.src = '/trading/graph/?threshold=' + vol_threshold + '&time=' + new Date().getTime();
        if (graphInterval) {
            clearInterval(graphInterval);
        }
        graphInterval = setInterval(function () {
            img.src = '/trading/graph/?threshold=' + vol_threshold + '&time=' + new Date().getTime();
        }, 10000);
        button.textContent = 'stop loading graph';
        isLoadGraph = true;

    } else {

        button.textContent = 'load graph';
        clearInterval(graphInterval);
        isLoadGraph = false;
    }
    // 기존에 실행 중인 interval이 있다면 clear



}


function impvol() {
    // 프론트엔드에서 <button onclick="">으로 클릭이벤트를 설정하는경우
    const fut_code = document.getElementById('fut_code').value;
    const maturity = document.getElementById('maturity').value;
    const cd_rate = document.getElementById('cd_rate').value;

    fetch('/trading/impvol/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            fut_code: fut_code,
            maturity: maturity,
            cd_rate: cd_rate
        })
    })
        .then(response => response.json())
        .then(data => {
            const resultContainer = document.getElementById('result');
            // const newResult = document.createElement('pre');
            // newResult.textContent = data.result != null ? data.result : "None";
            const resultText = data.result != null ? data.result : "None";
            resultContainer.innerHTML = `<pre>${resultText}</pre>`;
            // resultContainer.insertBefore(newResult, resultContainer.firstChild);
            document.getElementById('vol_threshold').value = data.vol_threshold;
        })
        .catch(error => {
            console.error('Error:', error);
        });


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