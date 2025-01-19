// 视频播放器监听
const videoPlayer = document.getElementById('video-player');
const textContainer = document.getElementById('text-container');

videoPlayer.addEventListener('timeupdate', () => {
    const currentTime = videoPlayer.currentTime * 1000; // 转换为毫秒
    
    // 遍历所有文本段落，找到当前应该高亮的段落
    sentences.forEach(sentence => {
        const textElement = document.getElementById(`text-${sentence.begin_time}`);
        if (currentTime >= sentence.begin_time && currentTime <= sentence.end_time) {
            textElement.classList.add('highlight');
            // 确保高亮文本在可视区域内
            textElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            textElement.classList.remove('highlight');
        }
    });
}); 