/**
 * Artwork Hover Animations
 * Handles mouse-following hover preview images for exhibition artwork cards
 * Uses pure CSS animations with JavaScript for positioning
 */

class ArtworkHoverAnimations {
  constructor() {
    this.cards = [];
    this.activePreview = null;
    this.mousePosition = { x: 0, y: 0 };
    this.isTouch = false;
    
    // Configuration
    this.config = {
      offset: { x: 20, y: -20 }
    };
    
    this.init();
  }
  
  init() {
    // Check if touch device - disable on mobile
    this.detectTouch();
    
    if (this.isTouch) {
      return; // Exit early on touch devices
    }
    
    // Find all artwork cards
    this.cards = document.querySelectorAll('.exhibition-artwork-card');
    
    if (this.cards.length === 0) return;
    
    // Set up mouse tracking
    this.setupMouseTracking();
    
    // Set up card event listeners
    this.setupCardEventListeners();
  }
  
  detectTouch() {
    // Detect touch devices and accessibility preferences
    this.isTouch = (
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0 ||
      window.matchMedia('(hover: none)').matches ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }
  
  setupMouseTracking() {
    // Track mouse movement globally
    document.addEventListener('mousemove', (e) => {
      // Use clientX/clientY for fixed positioning (viewport coordinates)
      this.mousePosition.x = e.clientX;
      this.mousePosition.y = e.clientY;
      
      // Update active preview position in real-time
      if (this.activePreview) {
        this.activePreview.style.left = (this.mousePosition.x - 125) + 'px';
        this.activePreview.style.top = (this.mousePosition.y - 125) + 'px';
      }
    }, { passive: true });
  }
  
  setupCardEventListeners() {
    this.cards.forEach((card, index) => {
      const preview = card.querySelector('.exhibition-artwork-hover-preview');
      
      if (!preview) return;
      
      // Add accessibility attributes
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.setAttribute('aria-describedby', 'artwork-hover-instructions');
      
      // Mouse enter
      card.addEventListener('mouseenter', (e) => {
        this.showPreview(card, preview);
      });
      
      // Mouse leave
      card.addEventListener('mouseleave', (e) => {
        this.hidePreview(preview);
      });
      
      // Update position while hovering over card
      card.addEventListener('mousemove', (e) => {
        if (this.activePreview === preview) {
          this.updatePreviewPosition();
        }
      });
      
      // Keyboard support for focus/blur
      card.addEventListener('focus', (e) => {
        // Position preview at center of card for keyboard users
        const rect = card.getBoundingClientRect();
        this.mousePosition.x = rect.left + rect.width / 2;
        this.mousePosition.y = rect.top + rect.height / 2;
        this.showPreview(card, preview);
      });
      
      card.addEventListener('blur', (e) => {
        this.hidePreview(preview);
      });
      
      // Handle Enter key
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click(); // Trigger the existing click handler
        }
      });
    });
    
    // Add screen reader instructions (hidden)
    this.addAccessibilityInstructions();
  }
  
  showPreview(card, preview) {
    // Hide any currently active preview
    if (this.activePreview && this.activePreview !== preview) {
      this.hidePreview(this.activePreview);
    }
    
    this.activePreview = preview;
    
    // Move preview to body to avoid parent container positioning issues
    if (preview.parentNode !== document.body) {
      document.body.appendChild(preview);
    }
    
    // Show and position the actual preview
    preview.style.left = (this.mousePosition.x - 125) + 'px'; // Center it (-125px for 250px width)
    preview.style.top = (this.mousePosition.y - 125) + 'px'; // Center it (-125px for 250px height)
    preview.classList.add('show');
    card.classList.add('hover-active');
  }
  
  hidePreview(preview) {
    if (!preview) return;
    
    // Hide preview with CSS class removal
    preview.classList.remove('show');
    
    // Remove hover state from all cards
    this.cards.forEach(card => {
      card.classList.remove('hover-active');
    });
    
    // Clear active preview
    if (this.activePreview === preview) {
      this.activePreview = null;
    }
  }
  
  updatePreviewPosition() {
    if (!this.activePreview) return;
    
    // Calculate position with offset
    const x = this.mousePosition.x + this.config.offset.x;
    const y = this.mousePosition.y + this.config.offset.y;
    
    // Get viewport dimensions
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Get preview dimensions (use fallback if not loaded yet)
    const previewRect = this.activePreview.getBoundingClientRect();
    const previewWidth = previewRect.width || 250;
    const previewHeight = previewRect.height || 250;
    
    // Constrain to viewport bounds
    let finalX = x;
    let finalY = y;
    
    // Prevent overflow on right edge
    if (x + previewWidth > viewportWidth - 20) {
      finalX = this.mousePosition.x - previewWidth - Math.abs(this.config.offset.x);
    }
    
    // Prevent overflow on bottom edge
    if (y + previewHeight > viewportHeight - 20) {
      finalY = this.mousePosition.y - previewHeight - Math.abs(this.config.offset.y);
    }
    
    // Prevent overflow on edges
    if (finalX < 20) finalX = 20;
    if (finalY < 20) finalY = 20;
    
    // Apply position
    this.activePreview.style.left = `${finalX}px`;
    this.activePreview.style.top = `${finalY}px`;
  }
  
  // Handle window resize
  handleResize() {
    if (this.activePreview) {
      this.updatePreviewPosition();
    }
  }
  
  // Add accessibility instructions for screen readers
  addAccessibilityInstructions() {
    // Check if instructions already exist
    if (document.getElementById('artwork-hover-instructions')) return;
    
    const instructions = document.createElement('div');
    instructions.id = 'artwork-hover-instructions';
    instructions.className = 'sr-only';
    instructions.textContent = 'Hover or focus on artwork cards to see a larger preview image';
    instructions.style.cssText = `
      position: absolute;
      left: -10000px;
      top: auto;
      width: 1px;
      height: 1px;
      overflow: hidden;
    `;
    
    document.body.appendChild(instructions);
  }
  
  // Cleanup method
  destroy() {
    if (this.activePreview) {
      this.hidePreview(this.activePreview, false);
    }
    
    // Remove accessibility instructions
    const instructions = document.getElementById('artwork-hover-instructions');
    if (instructions) {
      instructions.remove();
    }
    
    this.cards = [];
    this.activePreview = null;
  }
}

// Initialize when DOM is ready
function initArtworkHoverAnimations() {
  // Only initialize on pages with artwork cards
  const artworkCards = document.querySelectorAll('.exhibition-artwork-card');
  
  if (artworkCards.length > 0) {
    const animations = new ArtworkHoverAnimations();
    
    // Handle window resize
    window.addEventListener('resize', () => {
      animations.handleResize();
    }, { passive: true });
    
    // Store instance globally for potential cleanup
    window.artworkHoverAnimations = animations;
  }
}

// Initialize immediately if DOM is ready, otherwise wait
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initArtworkHoverAnimations);
} else {
  initArtworkHoverAnimations();
}

// Export for module systems
if (typeof window !== 'undefined') {
  window.ArtworkHoverAnimations = ArtworkHoverAnimations;
}