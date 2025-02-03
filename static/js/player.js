document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const transcribeBtn = document.getElementById('transcribe-btn');
    const transcriptionContainer = document.getElementById('transcription-container');
    const transcriptionText = document.getElementById('transcription-text');
    const info = document.getElementById('info');

    // 从window.videoInfo获取视频信息
    const videoPath = window.videoInfo.path;
    const source = window.videoInfo.source;
    const transcribed = window.videoInfo.transcribed === '1';
    const transcription = window.videoInfo.transcription;

    console.log('Video Info:', window.videoInfo);  // 调试日志

    // 如果已经转录过，直接显示结果
    if (transcribed && transcription) {
        transcribeBtn.classList.add('d-none');
        transcriptionText.value = transcription;  // 直接使用Redis中的纯文本
        transcriptionContainer.classList.remove('d-none');
    }

    // 转录按钮点击事件
    transcribeBtn.addEventListener('click', async function() {
        console.log('转录按钮被点击');
        try {
            console.log('开始转录处理');
            showInfo('正在转录视频...');
            transcribeBtn.disabled = true;

            const response = await fetch('/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: videoPath,
                    source: source
                })
            });

            const data = await response.json();
            console.log('转录响应:', data);

            if (response.ok) {
                if (data.transcription && data.transcription.sentences) {
                    showSuccess('转录完成！');
                    updateTranscription(data);
                    transcribeBtn.classList.add('d-none');
                    transcriptionContainer.classList.remove('d-none');
                } else {
                    showError('转录结果格式不正确');
                }
            } else {
                showError(data.error || '转录失败');
            }
        } catch (error) {
            console.error('转录请求出错:', error);
            showError('网络错误，请稍后重试');
        } finally {
            transcribeBtn.disabled = false;
        }
    });

    // 辅助函数
    function showInfo(message) {
        info.textContent = message;
        info.className = 'alert alert-info mt-3';
        info.classList.remove('d-none');
    }

    function showError(message) {
        info.textContent = message;
        info.className = 'alert alert-danger mt-3';
        info.classList.remove('d-none');
    }

    function showSuccess(message) {
        info.textContent = message;
        info.className = 'alert alert-success mt-3';
        info.classList.remove('d-none');
    }

    // updateTranscription 只在新转录时使用
    function updateTranscription(data) {
        if (data && data.transcription && Array.isArray(data.transcription.sentences)) {
            const sentences = data.transcription.sentences;
            
            // 只提取纯文本
            const plainText = sentences.map(sentence => {
                return sentence.text.replace(/<\|[^>]+\|>/g, '').trim();
            }).join('\n\n');
            
            // 更新显示
            transcriptionText.value = plainText;
            transcriptionContainer.classList.remove('d-none');
            
            console.log('显示的转录文本:', plainText);  // 调试日志
        }
    }

    function formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const ms = Math.floor((milliseconds % 1000) / 10);
        return `${padZero(minutes)}:${padZero(seconds)}.${padZero(ms, 2)}`;
    }

    function padZero(num, length = 2) {
        return num.toString().padStart(length, '0');
    }
}); 