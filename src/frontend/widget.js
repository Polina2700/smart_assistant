// frontend/widget.js
function getUserIdFromCookie() {
    try {
        // Try cookie first
        const match = document.cookie.match(/(?:^|;\s*)access=([^;]+)/);
        let token = match ? match[1] : null;
        // Fallback to localStorage (ERP stores JWT there)
        if (!token) {
            token = localStorage.getItem('access');
        }
        if (!token) return null;
        const parts = token.split('.');
        if (parts.length < 2) return null;
        const payload = JSON.parse(atob(parts[1]));
        return payload.user_id ? 'user_' + payload.user_id : null;
    } catch (e) {
        return null;
    }
}

(function() {
    console.log('Upload ERP Chatbot Widget...');

    const cookieUserId = getUserIdFromCookie();
    let sessionId;

    if (cookieUserId) {
    
        sessionId = cookieUserId;
        localStorage.setItem('erp_chatbot_session_id', sessionId);
    } else {
    
        sessionId = localStorage.getItem('erp_chatbot_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('erp_chatbot_session_id', sessionId);
        }
    }

    // Create chatbot button
    const chatbotButton = document.createElement('button');
    chatbotButton.id = 'erp-chatbot-button';
    chatbotButton.innerHTML = '<span style="font-size:13px;font-weight:800;letter-spacing:1px;line-height:1.3;text-align:center;pointer-events:none;text-shadow:0 1px 3px rgba(0,0,0,0.3);">BINU<br>AI</span>';
    chatbotButton.title = 'ERP Assistant';
    chatbotButton.setAttribute('aria-label', 'Open ERP Chatbot');

    // Styles for the button
    Object.assign(chatbotButton.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        width: '68px',
        height: '68px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #1E6A95, #228BA0)',
        backgroundColor: 'transparent',
        color: 'white',
        border: 'none',
        fontSize: '13px',
        cursor: 'pointer',
        zIndex: '10000',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        transition: 'all 0.3s ease'
    });

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'erp-chatbot-window';

    // Styles for chat window
    Object.assign(chatWindow.style, {
        position: 'fixed',
        bottom: '90px',
        right: '20px',
        width: '380px',
        height: '500px',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxSizing: 'border-box',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        display: 'none',
        zIndex: '9999',
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
        flexDirection: 'column',
        margin: '0',
        padding: '0'
    });

    // Using iframe to load the chatbot interface
    // Iframe is created once and never reloaded — session persists via sessionStorage
    const iframe = document.createElement('iframe');
    const chatBaseUrl = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
        ? 'http://127.0.0.1:8080'
        : 'https://chat.rwave.eu';

    iframe.src = chatBaseUrl + '?widget=true&session_id=' + encodeURIComponent(sessionId);

    // Fixed styles for iframe
    Object.assign(iframe.style, {
        width: '100%',
        height: '100%',
        border: 'none',
        display: 'block',
        borderRadius: '12px',
        margin: '0',
        padding: '0',
        boxSizing: 'border-box'
    });

    // Add attributes for iframe
    iframe.setAttribute('frameborder', '0');
    iframe.setAttribute('scrolling', 'yes'); // Allow scrolling inside
    iframe.setAttribute('allow', 'clipboard-write');
    iframe.title = 'ERP Chatbot Assistant';

    chatWindow.appendChild(iframe);

    // Logic for closing/opening the chat window
    let isOpen = false;

    chatbotButton.addEventListener('click', function() {
        if (!isOpen) {
            // Open the window (iframe already loaded, just show it)
            chatWindow.style.display = 'flex';
            chatbotButton.innerHTML = '✕';
            chatbotButton.style.background = 'linear-gradient(135deg, #123244, #1E6A95)';
            chatbotButton.style.backgroundColor = 'transparent';
            chatbotButton.style.transform = 'rotate(90deg)';
            isOpen = true;
        } else {
            // Close the window
            chatWindow.style.display = 'none';
            chatbotButton.innerHTML = '<span style="font-size:13px;font-weight:800;letter-spacing:1px;line-height:1.3;text-align:center;pointer-events:none;text-shadow:0 1px 3px rgba(0,0,0,0.3);">BINU<br>AI</span>';
            chatbotButton.style.background = 'linear-gradient(135deg, #1E6A95, #228BA0)';
            chatbotButton.style.backgroundColor = 'transparent';
            chatbotButton.style.transform = 'rotate(0deg)';
            isOpen = false;
        }
    });

    // Add elements to the body
    document.body.appendChild(chatWindow);
    document.body.appendChild(chatbotButton);

    console.log('ERP Chatbot Widget successfully loaded.');

    // Additional functionality:
    // Close chat window when clicking outside
    document.addEventListener('click', function(event) {
        event.stopPropagation();
        if (isOpen &&
            !chatWindow.contains(event.target) &&
            event.target !== chatbotButton &&
            !chatbotButton.contains(event.target)) {
            chatWindow.style.display = 'none';
            chatbotButton.innerHTML = '<span style="font-size:13px;font-weight:800;letter-spacing:1px;line-height:1.3;text-align:center;pointer-events:none;text-shadow:0 1px 3px rgba(0,0,0,0.3);">BINU<br>AI</span>';
            chatbotButton.style.background = 'linear-gradient(135deg, #1E6A95, #228BA0)';
            chatbotButton.style.backgroundColor = 'transparent';
            isOpen = false;
        }
    });

    // Export API to control the widget externally
    window.ERPChatbotWidget = {
        open: function() {
            chatWindow.style.display = 'flex';
            chatbotButton.innerHTML = '✕';
            chatbotButton.style.background = 'linear-gradient(135deg, #123244, #1E6A95)';
            chatbotButton.style.backgroundColor = 'transparent';
            isOpen = true;
        },
        close: function() {
            chatWindow.style.display = 'none';
            chatbotButton.innerHTML = '<span style="font-size:13px;font-weight:800;letter-spacing:1px;line-height:1.3;text-align:center;pointer-events:none;text-shadow:0 1px 3px rgba(0,0,0,0.3);">BINU<br>AI</span>';
            chatbotButton.style.background = 'linear-gradient(135deg, #1E6A95, #228BA0)';
            chatbotButton.style.backgroundColor = 'transparent';
            isOpen = false;
        },
        toggle: function() {
            chatbotButton.click();
        },
        // Force reload iframe and generate a fresh session
        reload: function() {
            const newSessionId = getUserIdFromCookie() || ('session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
            sessionStorage.setItem('erp_chatbot_session_id', newSessionId);
            iframe.src = chatBaseUrl + '?widget=true&session_id=' + encodeURIComponent(newSessionId);
        }
    };
})();
