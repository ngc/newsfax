// Background service worker for Newsfax extension

// Listen for extension icon clicks
chrome.action.onClicked.addListener(async (tab) => {
  try {
    // Send message to content script to start fact-checking
    await chrome.tabs.sendMessage(tab.id, {
      action: 'START_FACT_CHECKING'
    });
  } catch (error) {
    console.error('Failed to send message to content script:', error);
  }
});

// Optional: Set a badge or icon state when activated
chrome.action.onClicked.addListener((tab) => {
  chrome.action.setBadgeText({
    text: '✓',
    tabId: tab.id
  });
  
  chrome.action.setBadgeBackgroundColor({
    color: '#22c55e',
    tabId: tab.id
  });
  
  // Clear badge after 3 seconds
  setTimeout(() => {
    chrome.action.setBadgeText({
      text: '',
      tabId: tab.id
    });
  }, 3000);
}); 