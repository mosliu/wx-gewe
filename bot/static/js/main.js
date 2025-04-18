function sendMessage() {
    const roomId = document.getElementById('room_id').value;
    const text = document.getElementById('message').value;
    const responseDiv = document.getElementById('response');

    if (!roomId || !text) {
        showResponse('请填写完整信息', false);
        return;
    }

    fetch('/push', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            room_id: roomId,
            text: text
        })
    })
    .then(response => response.json())
    .then(data => {
        showResponse(data.message, data.success);
    })
    .catch(error => {
        showResponse('发送请求失败: ' + error, false);
    });
}

function showResponse(message, success) {
    const responseDiv = document.getElementById('response');
    responseDiv.textContent = message;
    responseDiv.className = success ? 'success' : 'error';
    responseDiv.style.display = 'block';

    // 3秒后自动隐藏
    setTimeout(() => {
        responseDiv.style.display = 'none';
    }, 3000);
}