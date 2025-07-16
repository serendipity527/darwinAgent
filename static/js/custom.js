// 自定义JavaScript脚本

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('Darwin Agent UI 已加载');
    
    // 可以在这里添加自定义的JavaScript逻辑
    setupKeyboardShortcuts();
    enhanceUIInteractions();
});

// 设置键盘快捷键
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl+Enter 提交表单
        if (event.ctrlKey && event.key === 'Enter') {
            const submitButton = document.querySelector('button[variant="primary"]');
            if (submitButton) {
                submitButton.click();
            }
        }
        
        // Esc 清空输入
        if (event.key === 'Escape') {
            const textInputs = document.querySelectorAll('textarea, input[type="text"]');
            const activeElement = document.activeElement;
            
            if (textInputs.contains(activeElement)) {
                activeElement.value = '';
            }
        }
    });
}

// 增强UI交互
function enhanceUIInteractions() {
    // 这里可以添加额外的UI交互增强功能
    
    // 例如: 自动滚动聊天记录到底部
    const chatbox = document.getElementById('chatbot');
    if (chatbox) {
        const observer = new MutationObserver(function() {
            chatbox.scrollTop = chatbox.scrollHeight;
        });
        
        observer.observe(chatbox, { childList: true, subtree: true });
    }
} 