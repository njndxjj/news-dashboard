// OpenClaw Gateway Token Configuration
window.OPENCLAW_GATEWAY_TOKEN = '6a18e607f503da246628896da5649b06dc05446da4c88fd5';

// Auto-configure on load
(function() {
  const token = window.OPENCLAW_GATEWAY_TOKEN;
  if (token) {
    localStorage.setItem('openclaw-gateway-token', token);
    localStorage.setItem('gateway-token', token);
    localStorage.setItem('token', token);
    localStorage.setItem('auth-token', token);
    sessionStorage.setItem('gateway-token', token);

    // Dispatch event for app to detect
    window.dispatchEvent(new CustomEvent('openclaw-token-ready', { detail: { token } }));
  }
})();
