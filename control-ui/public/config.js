// OpenClaw Gateway Token Configuration
// ⚠️ SECURITY: Token should be set via environment variable, not hardcoded
// Use: window.OPENCLAW_GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN;
window.OPENCLAW_GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN || '';

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
