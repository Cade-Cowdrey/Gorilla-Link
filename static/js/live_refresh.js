/**
 * Auto-refresh helper
 * @param {string} url  API endpoint returning JSON
 * @param {number} interval Refresh interval in ms (default 60000)
 * @param {function} onUpdate callback(data)
 * @param {function} onBefore optional callback before each refresh
 * @param {function} onAfter optional callback after successful refresh
 */
function autoRefreshJSON(url, interval = 60000, onUpdate, onBefore, onAfter) {
  async function refresh() {
    try {
      if (onBefore) onBefore();
      const res = await fetch(url, { cache: "no-store" });
      const data = await res.json();
      onUpdate(data);
      if (onAfter) onAfter();
    } catch (err) {
      console.error("Auto-refresh failed:", err);
    }
  }
  refresh();
  return setInterval(refresh, interval);
}

/* Example:
autoRefreshJSON("/admin_reports_summary_data", 45000, data => {
  // update charts here
}, () => {
  // before
}, () => {
  // after
});
*/
