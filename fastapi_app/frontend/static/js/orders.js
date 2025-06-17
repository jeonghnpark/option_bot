
async function placeMultiOrderForSingleOrder(orderData) {
    try {
        const response = await fetch('/api/v1/orders/place', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Order placed successfully:', result);
        return result;
    } catch (error) {
        console.error('Error placing order:', error);
        throw error;
    }
}
// HTML 이벤트 핸들러
document.getElementById('orderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const orderData = {
        focode: document.getElementById('focode').value,
        direction: document.getElementById('direction').value,
        price: parseFloat(document.getElementById('price').value),
        quantity: parseInt(document.getElementById('quantity').value),
    };

    try {
        const result = await placeMultiOrderForSingleOrder(orderData);
        alert('주문이 성공적으로 처리되었습니다.');
    } catch (error) {
        alert('주문 처리 중 오류가 발생했습니다.');
    }
});
