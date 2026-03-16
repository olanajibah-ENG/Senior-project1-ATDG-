import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Minimize2, Maximize2, Bot, User } from 'lucide-react';
import './ChatWidget.css';

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const ChatWidget: React.FC<{ language: 'en' | 'ar' }> = ({ language }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: language === 'ar' 
        ? '👋 مرحباً! أنا مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟'
        : '👋 Hello! I\'m your AI assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateBotResponse = async (userMessage: string): Promise<string> => {
    // Simulate AI response with predefined patterns
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('help') || lowerMessage.includes('مساعدة')) {
      return language === 'ar'
        ? 'يمكنني مساعدتك في: 📚 إنشاء المستندات 🔄 تحليل الكود 📊 إنشاء المخططات 🤝 مشاركة المشاريع. هل تحتاج إلى مساعدة في شيء محدد؟'
        : 'I can help you with: 📚 Creating documents 🔄 Analyzing code 📊 Generating diagrams 🤝 Sharing projects. Do you need help with something specific?';
    }
    
    if (lowerMessage.includes('project') || lowerMessage.includes('مشروع')) {
      return language === 'ar'
        ? 'لإنشاء مشروع جديد، انقر على زر "مشروع جديد" في لوحة التحكم. يمكنك إضافة الكود والمستندات لمشروعك بعد إنشائه.'
        : 'To create a new project, click the "New Project" button in the dashboard. You can add code and documents to your project after creating it.';
    }
    
    if (lowerMessage.includes('share') || lowerMessage.includes('مشاركة')) {
      return language === 'ar'
        ? 'لمشاركة مشروع، اذهب إلى قائمة المشاريع وانقر على أيقونة المشاركة بجانب المشروع. يمكنك إنشاء رابط أو دعوة مستخدمين محددين.'
        : 'To share a project, go to your projects list and click the share icon next to your project. You can create a link or invite specific users.';
    }
    
    if (lowerMessage.includes('documentation') || lowerMessage.includes('توثيق')) {
      return language === 'ar'
        ? 'يقوم نظامنا بإنشاء توثيق تلقائي من كودك. ما عليك سوى إرفاق الكود بمشروعك وسنقوم بتحليله وإنشاء المستندات.'
        : 'Our system generates automatic documentation from your code. Simply attach code to your project and we\'ll analyze it and create documents.';
    }
    
    // Default response
    return language === 'ar'
      ? 'أفهم سؤالك. هل يمكنك أن تكون أكثر تحديداً؟ يمكنك أيضاً التحقق من مركز المساعدة للحصول على إجابات مفصلة.'
      : 'I understand your question. Could you be more specific? You can also check the help center for detailed answers.';
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsTyping(true);

    // Simulate bot thinking time
    await new Promise(resolve => setTimeout(resolve, 1000));

    const botResponse = await generateBotResponse(message);
    const botMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      text: botResponse,
      sender: 'bot',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, botMessage]);
    setIsTyping(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString(language === 'ar' ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isOpen) {
    return (
      <div className="chat-widget-bubble" onClick={() => setIsOpen(true)}>
        <MessageCircle size={24} />
        <span className="chat-bubble-text">
          {language === 'ar' ? 'دردشة' : 'Chat'}
        </span>
      </div>
    );
  }

  return (
    <div className={`chat-widget ${isMinimized ? 'minimized' : ''}`}>
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-info">
          <Bot size={20} />
          <div>
            <div className="chat-title">
              {language === 'ar' ? 'المساعد الذكي' : 'AI Assistant'}
            </div>
            <div className="chat-status">
              {isTyping 
                ? (language === 'ar' ? 'يكتب...' : 'Typing...')
                : (language === 'ar' ? 'متصل' : 'Online')
              }
            </div>
          </div>
        </div>
        <div className="chat-header-actions">
          <button
            className="chat-action-btn"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? (language === 'ar' ? 'تكبير' : 'Maximize') : (language === 'ar' ? 'تصغير' : 'Minimize')}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
          <button
            className="chat-action-btn"
            onClick={() => setIsOpen(false)}
            title={language === 'ar' ? 'إغلاق' : 'Close'}
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.sender}`}>
                <div className="message-avatar">
                  {msg.sender === 'bot' ? <Bot size={16} /> : <User size={16} />}
                </div>
                <div className="message-content">
                  <div className="message-text">{msg.text}</div>
                  <div className="message-time">{formatTime(msg.timestamp)}</div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="chat-message bot">
                <div className="message-avatar">
                  <Bot size={16} />
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={language === 'ar' ? 'اكتب رسالتك...' : 'Type your message...'}
              disabled={isTyping}
            />
            <button
              className="chat-send-btn"
              onClick={handleSendMessage}
              disabled={!message.trim() || isTyping}
            >
              <Send size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;
