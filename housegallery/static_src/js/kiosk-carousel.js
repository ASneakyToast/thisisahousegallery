/**
 * Kiosk Carousel
 *
 * Auto-advancing carousel for the split template's image display.
 * Shows images with configurable transitions, pauses when tab is hidden.
 */
const KioskCarousel = {
  init(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const images = container.querySelectorAll('.gallery-single-image, .gallery-image');
    if (images.length === 0) return;

    // Read configurable settings from data attributes
    const interval = parseInt(container.dataset.carouselInterval, 10) || 5000;
    const duration = parseInt(container.dataset.carouselDuration, 10) || 1200;
    const transition = container.dataset.carouselTransition || 'crossfade';

    // Apply transition duration as CSS custom property
    container.style.setProperty('--carousel-transition-duration', duration + 'ms');

    // Apply transition effect class (crossfade is default, no extra class needed)
    if (transition !== 'crossfade') {
      container.classList.add('transition-' + transition);
    }

    // Single image: just show it statically
    if (images.length === 1) {
      images[0].classList.add('carousel-active');
      return;
    }

    let currentIndex = 0;
    let intervalId = null;

    // Show first image
    images[currentIndex].classList.add('carousel-active');

    function advance() {
      images[currentIndex].classList.remove('carousel-active');
      currentIndex = (currentIndex + 1) % images.length;
      images[currentIndex].classList.add('carousel-active');
    }

    function start() {
      if (!intervalId) {
        intervalId = setInterval(advance, interval);
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
