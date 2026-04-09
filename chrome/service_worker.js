chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url) return;

  const isArmadaHelpCenter = tab.url.startsWith("https://console.armada.ai/my-apps");
  if (!isArmadaHelpCenter) return;

  try {
    await chrome.tabs.sendMessage(tab.id, { type: "TOGGLE_OVERLAY" });
  } catch (err) {
    console.warn("Could not send TOGGLE_OVERLAY message:", err);
  }
});