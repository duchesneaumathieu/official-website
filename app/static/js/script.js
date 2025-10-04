const chatbot = document.getElementById('chatbot');
const footer = document.querySelector('footer');

function updateChatbotPosition() {
  const footerRect = footer.getBoundingClientRect();
  const windowHeight = window.innerHeight;

  if (footerRect.top < windowHeight) {
    // Footer overlaps viewport → lift chatbot above it
    chatbot.style.bottom = (windowHeight - footerRect.top + 12) + 'px';
    chatbot.style.height = `clamp(0px, calc(100vh - 24px - 1rem - 12px - ${(windowHeight - footerRect.top)}px), 500px)`;
  } else {
    // Footer not visible → keep at default
    chatbot.style.bottom = '12px';
    chatbot.style.height = 'clamp(0px, calc(100vh - 24px - 1rem - 12px), 500px)';
  }
}

// Run once on load
updateChatbotPosition();

// Run on scroll/resize
window.addEventListener('scroll', updateChatbotPosition);
window.addEventListener('resize', updateChatbotPosition);

