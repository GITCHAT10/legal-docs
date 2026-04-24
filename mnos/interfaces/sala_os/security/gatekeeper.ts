/**
 * SALA-OS Security Enforcer (Frontend middleware).
 * Checks AEGIS session and Orban tunnel.
 */
export const enforceUiSecurity = () => {
  const session = localStorage.getItem('aegis_session');
  const tunnel = window.AIG_TUNNEL_ACTIVE;

  if (!session || !tunnel) {
    console.error("!!! SECURITY VIOLATION !!!");
    localStorage.clear();
    window.location.href = "/logout";
  }
};
