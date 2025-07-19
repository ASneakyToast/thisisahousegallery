/**
 * Horizontal Features Block
 * Netflix-style horizontal scrolling carousel with auto-scroll support
 */

import { animate, createTimeline, stagger } from 'animejs';

class HorizontalFeaturesCarousel {
  constructor(element) {
    this.element = element;
    this.track = element.querySelector('.horizontal-features-block__track');
    this.cards = element.querySelectorAll('.horizontal-features-card');
    this.prevBtn = element.querySelector('.horizontal-features-block__nav--prev');
    this.nextBtn = element.querySelector('.horizontal-features-block__nav--next');
    this.progressBar = element.querySelector('.horizontal-features-block__progress-bar');
    this.scrollContainer = element.querySelector('.horizontal-features-block__scroll-container');
    
    // Configuration
    this.autoScroll = element.dataset.autoScroll === 'true';
    this.scrollSpeed = element.dataset.scrollSpeed || 'medium';
    this.currentIndex = 0;
    this.cardWidth = 0;
    this.visibleCards = 1;
    this.maxIndex = 0;
    this.isAnimating = false;
    this.autoScrollTimer = null;
    this.autoScrollPaused = false;
    
    // Speed mapping (in milliseconds)
    this.speedMap = {
      slow: 8000,
      medium: 5000,
      fast: 3000
    };
    
    this.init();
  }
  
  init() {
    if (!this.track || this.cards.length === 0) return;
    
    this.calculateDimensions();
    this.setupEventListeners();
    this.updateNavigation();
    this.updateProgress();
    
    if (this.autoScroll) {
      this.startAutoScroll();
    }
    
    // Handle resize
    window.addEventListener('resize', () => {
      this.calculateDimensions();
      this.updateProgress();
    });
  }
  
  calculateDimensions() {
    if (this.cards.length === 0) return;
    
    // Get card width including margin
    const cardStyle = window.getComputedStyle(this.cards[0]);
    this.cardWidth = this.cards[0].offsetWidth + parseInt(cardStyle.marginRight);
    
    // Calculate visible cards based on container width
    const containerWidth = this.scrollContainer.offsetWidth;
    this.visibleCards = Math.floor(containerWidth / this.cardWidth);
    
    // Ensure at least 1 card is visible
    this.visibleCards = Math.max(1, this.visibleCards);
    
    // Calculate maximum index
    this.maxIndex = Math.max(0, this.cards.length - this.visibleCards);
    
    // Adjust current index if necessary
    this.currentIndex = Math.min(this.currentIndex, this.maxIndex);
  }
  
  setupEventListeners() {
    // Navigation buttons
    this.prevBtn?.addEventListener('click', () => this.goToPrevious());
    this.nextBtn?.addEventListener('click', () => this.goToNext());
    
    // Pause auto-scroll on hover
    if (this.autoScroll) {
      this.element.addEventListener('mouseenter', () => this.pauseAutoScroll());
      this.element.addEventListener('mouseleave', () => this.resumeAutoScroll());
    }
    
    // Pause auto-scroll on touch (but don't interfere with native scrolling)
    this.scrollContainer.addEventListener('touchstart', () => {
      this.pauseAutoScroll();
    }, { passive: true });
    
    this.scrollContainer.addEventListener('touchend', () => {
      this.resumeAutoScroll();
    }, { passive: true });
    
    // Keyboard navigation
    this.element.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        this.goToPrevious();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        this.goToNext();
      }
    });
  }
  
  goToPrevious() {
    if (this.isAnimating || this.currentIndex === 0) return;
    
    this.currentIndex--;
    this.slideToIndex(this.currentIndex);
  }
  
  goToNext() {
    if (this.isAnimating || this.currentIndex >= this.maxIndex) return;
    
    this.currentIndex++;
    this.slideToIndex(this.currentIndex);
  }
  
  slideToIndex(index) {
    if (this.isAnimating) return;
    
    this.isAnimating = true;
    const scrollPosition = index * this.cardWidth;
    
    // Use native smooth scrolling instead of anime.js
    this.scrollContainer.scrollTo({
      left: scrollPosition,
      behavior: 'smooth'
    });
    
    // Wait for scroll to complete
    setTimeout(() => {
      this.isAnimating = false;
      this.updateNavigation();
      this.updateProgress();
    }, 600);
  }
  
  updateNavigation() {
    if (this.prevBtn) {
      this.prevBtn.disabled = this.currentIndex === 0;
      this.prevBtn.setAttribute('aria-disabled', this.currentIndex === 0);
    }
    
    if (this.nextBtn) {
      this.nextBtn.disabled = this.currentIndex >= this.maxIndex;
      this.nextBtn.setAttribute('aria-disabled', this.currentIndex >= this.maxIndex);
    }
  }
  
  updateProgress() {
    if (!this.progressBar || this.maxIndex === 0) return;
    
    const progress = (this.currentIndex / this.maxIndex) * 100;
    
    animate({
      targets: this.progressBar,
      width: `${progress}%`,
      duration: 300,
      easing: 'easeOutQuart'
    });
  }
  
  startAutoScroll() {
    if (!this.autoScroll || this.autoScrollPaused) return;
    
    const interval = this.speedMap[this.scrollSpeed];
    
    this.autoScrollTimer = setTimeout(() => {
      if (this.currentIndex >= this.maxIndex) {
        // Loop back to beginning
        this.currentIndex = 0;
      } else {
        this.currentIndex++;
      }
      
      this.slideToIndex(this.currentIndex);
      this.startAutoScroll(); // Continue the loop
    }, interval);
  }
  
  pauseAutoScroll() {
    this.autoScrollPaused = true;
    if (this.autoScrollTimer) {
      clearTimeout(this.autoScrollTimer);
      this.autoScrollTimer = null;
    }
  }
  
  resumeAutoScroll() {
    if (!this.autoScroll) return;
    
    this.autoScrollPaused = false;
    this.startAutoScroll();
  }
  
  destroy() {
    if (this.autoScrollTimer) {
      clearTimeout(this.autoScrollTimer);
    }
    
    // Remove event listeners
    this.prevBtn?.removeEventListener('click', this.goToPrevious);
    this.nextBtn?.removeEventListener('click', this.goToNext);
  }
}

// Initialize all horizontal features blocks
document.addEventListener('DOMContentLoaded', () => {
  const horizontalFeatures = document.querySelectorAll('.horizontal-features-block');
  
  horizontalFeatures.forEach(element => {
    new HorizontalFeaturesCarousel(element);
  });
});

// Handle dynamic content (e.g., via AJAX)
if (typeof window !== 'undefined') {
  window.HorizontalFeaturesCarousel = HorizontalFeaturesCarousel;
}