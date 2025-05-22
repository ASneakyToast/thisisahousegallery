document.addEventListener('DOMContentLoaded', function() {
  // Find all images with the quickview-item class
  const quickviewItems = document.querySelectorAll('.quickview-item');
  
  // Add click event to toggle fullscreen
  quickviewItems.forEach(item => {
    item.addEventListener('click', function(event) {
      // Don't trigger fullscreen if the image is inside a link
      if (event.target.closest('a')) {
        return;
      }
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
  
  // Close fullscreen when clicking on a fullscreen image
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('fullscreen')) {
      e.target.classList.remove('fullscreen');
    }
  });
});