import React, { useState } from 'react';
import { X, ChevronDown, ChevronUp, ExternalLink, MessageCircle, Bug, FileText, Send, BookOpen, HelpCircle, Star } from 'lucide-react';
import './HelpModal.css';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: 'general' | 'projects' | 'code' | 'sharing';
}

const HelpModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  language: 'en' | 'ar';
}> = ({ isOpen, onClose, language }) => {
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null);
  const [supportForm, setSupportForm] = useState({ subject: '', message: '' });
  const [isSubmittingSupport, setIsSubmittingSupport] = useState(false);
  const [activeTab, setActiveTab] = useState<'faq' | 'support' | 'docs' | 'changelog'>('faq');

  const faqs: FAQItem[] = [
    {
      id: 'share-project',
      category: 'sharing',
      question: language === 'ar' ? 'كيف يمكنني مشاركة مشروع؟' : 'How to share a project?',
      answer: language === 'ar'
        ? 'لمشاركة مشروع، اذهب إلى قائمة المشاريع، انقر على زر المشاركة بجانب المشروع الذي تريد مشاركته. يمكنك إنشاء رابط مشاركة أو دعوة مستخدمين محددين عبر البريد الإلكتروني.'
        : 'To share a project, go to your projects list, click share button next to project you want to share. You can create a share link or invite specific users via email.'
    },
    {
      id: 'attach-code',
      category: 'code',
      question: language === 'ar' ? 'كيف يمكنني إرفاق الكود؟' : 'How to attach code?',
      answer: language === 'ar'
        ? 'لإرفاق الكود، انقر على مشروعك ثم اختر "إضافة كود". يمكنك رفع ملفات الكود مباشرة أو لصق الكود في المحرر. ندعم لغات متعددة مثل Python و Java و JavaScript.'
        : 'To attach code, click on your project then select "Add Code". You can upload code files directly or paste code in editor. We support multiple languages like Python, Java, and JavaScript.'
    }
  ];

  const toggleFAQ = (id: string) => {
    setExpandedFAQ(expandedFAQ === id ? null : id);
  };

  const handleSupportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supportForm.subject.trim() || !supportForm.message.trim()) return;

    setIsSubmittingSupport(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      alert(language === 'ar' ? 'تم إرسال رسالتك بنجاح!' : 'Your message has been sent successfully!');
      setSupportForm({ subject: '', message: '' });
    } catch (error) {
      alert(language === 'ar' ? 'فشل إرسال الرسالة. يرجى المحاولة مرة أخرى.' : 'Failed to send message. Please try again.');
    } finally {
      setIsSubmittingSupport(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="help-modal-overlay" onClick={onClose}>
      <div className="help-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="help-modal-header">
          <div className="help-modal-title">
            <HelpCircle size={24} />
            <h2>{language === 'ar' ? 'مركز المساعدة' : 'Help Center'}</h2>
          </div>
          <button className="help-modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="help-tabs">
          <button
            className={`help-tab ${activeTab === 'faq' ? 'active' : ''}`}
            onClick={() => setActiveTab('faq')}
          >
            <BookOpen size={16} />
            {language === 'ar' ? 'الأسئلة الشائعة' : 'FAQ'}
          </button>
          <button
            className={`help-tab ${activeTab === 'support' ? 'active' : ''}`}
            onClick={() => setActiveTab('support')}
          >
            <MessageCircle size={16} />
            {language === 'ar' ? 'اتصل بالدعم' : 'Contact Support'}
          </button>
        </div>

        <div className="help-modal-body">
          {activeTab === 'faq' && (
            <div className="faq-section">
              <div className="faq-list">
                {faqs.map((faq) => (
                  <div key={faq.id} className="faq-item">
                    <button
                      className="faq-question"
                      onClick={() => toggleFAQ(faq.id)}
                    >
                      <span>{faq.question}</span>
                      {expandedFAQ === faq.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {expandedFAQ === faq.id && (
                      <div className="faq-answer">
                        <p>{faq.answer}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'support' && (
            <div className="support-section">
              <form className="support-form" onSubmit={handleSupportSubmit}>
                <div className="form-group">
                  <label>{language === 'ar' ? 'الموضوع' : 'Subject'}</label>
                  <input
                    type="text"
                    value={supportForm.subject}
                    onChange={(e) => setSupportForm({ ...supportForm, subject: e.target.value })}
                    placeholder={language === 'ar' ? 'اكتب موضوع رسالتك...' : 'Enter your subject...'}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>{language === 'ar' ? 'الرسالة' : 'Message'}</label>
                  <textarea
                    value={supportForm.message}
                    onChange={(e) => setSupportForm({ ...supportForm, message: e.target.value })}
                    placeholder={language === 'ar' ? 'اكتب تفاصيل طلبك...' : 'Enter your message details...'}
                    rows={5}
                    required
                  />
                </div>
                <button type="submit" className="support-submit-btn" disabled={isSubmittingSupport}>
                  {isSubmittingSupport ? (
                    language === 'ar' ? 'جاري الإرسال...' : 'Sending...'
                  ) : (
                    <>
                      <Send size={16} />
                      {language === 'ar' ? 'إرسال الرسالة' : 'Send Message'}
                    </>
                  )}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
