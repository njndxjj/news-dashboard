import React, { useEffect } from 'react';
import './Toast.css';

/**
 * Toast 通知组件
 * @param {Object} props
 * @param {string} props.message - 显示的消息内容
 * @param {'success' | 'error' | 'info'} props.type - 通知类型
 * @param {number} props.duration - 显示时长（毫秒），默认 3000ms
 * @param {Function} props.onClose - 关闭回调
 */
function Toast({ message, type = 'info', duration = 3000, onClose }) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const typeClass = `toast-${type}`;

  return (
    <div className={`toast ${typeClass}`}>
      <span className="toast-icon">{getTypeIcon(type)}</span>
      <span className="toast-message">{message}</span>
      <button className="toast-close" onClick={onClose}>
        ✕
      </button>
    </div>
  );
}

function getTypeIcon(type) {
  switch (type) {
    case 'success':
      return '✓';
    case 'error':
      return '✕';
    case 'info':
    default:
      return 'ℹ';
  }
}

export default Toast;
