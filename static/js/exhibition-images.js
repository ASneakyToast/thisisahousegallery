// Handle exhibition image fullscreen view
document.addEventListener('DOMContentLoaded', function() {
  // Find all images with the quickview-item class
  const quickviewItems = document.querySelectorAll('.quickview-item');
  
  // Add click event to toggle fullscreen
  quickviewItems.forEach(item => {
    item.addEventListener('click', function() {
      this.classList.toggle('fullscreen');
    });
  });

  // Close fullscreen when clicking outside or pressing Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const fullscreenImages = document.querySelectorAll('.fullscreen');
      fullscreenImages.forEach(img => {
        img.classList.remove('fullscreen');
      });
    }
  });
});