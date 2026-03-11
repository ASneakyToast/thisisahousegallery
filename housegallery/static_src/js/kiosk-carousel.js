/**
 * Kiosk Carousel
 *
 * Auto-advancing carousel for the split template's image display.
 * Shows images with crossfade transitions, pauses when tab is hidden.
 */
const KioskCarousel = {
  init(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const images = container.querySelectorAll('.gallery-single-image');
    if (images.length === 0) return;

    // Single image: just show it statically
    if (images.length === 1) {
      images[0].classList.add('carousel-active');
      return;
    }

    let currentIndex = 0;
    let intervalId = null;
    const INTERVAL = 5000;

    // Show first image
    images[currentIndex].classList.add('carousel-active');

    function advance() {
      images[currentIndex].classList.remove('carousel-active');
      currentIndex = (currentIndex + 1) % images.length;
      images[currentIndex].classList.add('carousel-active');
    }

    function start() {
      if (!intervalId) {
        intervalId = setInterval(advance, INTERVAL);
      }
    }

    function stop() {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    }

    // Pause when tab is hidden, resume when visible
    document.addEventListener('visibilitychange', function() {
      if (document.hidden) {
        stop();
      } else {
        start();
      }
    });

    start();
  }
};

window.KioskCarousel = KioskCarousel;
