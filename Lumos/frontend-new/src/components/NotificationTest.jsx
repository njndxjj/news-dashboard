import React, { useState } from 'react';
import { sendTestNotification } from '../services/api';
import axios from 'axios';
import Toast from './Toast';

function NotificationTest() {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const handleTestNotification = async () => {
    try {
      const result = await sendTestNotification();
      if (result) {
        addToast('Test notification sent successfully!', 'success');
        console.log('Notification result:', result);
      } else {
        addToast('Failed to send test notification.', 'error');
      }
    } catch (error) {
      console.error('Error in notification test:', error);
      addToast(`Failed to send test notification: ${error.message}`, 'error');
    }
  };

  const handleGeneralNotification = async () => {
    try {
      const response = await axios.post('/api/notify', {
        message: 'General notification test'
      });
      if (response.data) {
        addToast('General notification sent successfully!', 'success');
        console.log('Notification response:', response.data);
      } else {
        addToast('Failed to send general notification.', 'error');
      }
    } catch (error) {
      console.error('Error in general notification:', error);
      addToast(`Failed to send general notification: ${error.message}`, 'error');
    }
  };

  return (
    <div style={{ margin: '20px 0' }}>
      <h2>Notification Controls</h2>
      <div style={{ marginBottom: '10px' }}>
        <button onClick={handleTestNotification} style={{ marginRight: '10px' }}>Send Test Notification</button>
        <button onClick={handleGeneralNotification}>Send Notification</button>
      </div>

      {/* Toast 通知容器 */}
      <div className="toast-container" style={{ position: 'fixed', top: '20px', right: '20px' }}>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            duration={3000}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
}

export default NotificationTest;
