// menu.js - Main Menu Animations
// Now using CSS-based animations similar to exhibition lightbox pattern

// Menu Animation Controller
class MenuAnimationController {
  constructor() {
    // DOM Elements
    this.menuButton = document.querySelector('.header__menu-button');
    this.closeButton = document.querySelector('.main-menu__close-button');
    this.mainMenu = document.getElementById('main-menu');
    this.body = document.body;
    this.overlay = document.querySelector('.header__overlay');
    this.menuItems = document.querySelectorAll('.main-menu__items .button-carrot');
    this.ctaButtons = document.querySelectorAll('.main-menu__container .cta-button');

    // Initialize
    if (this.menuButton && this.mainMenu) {
      this.setupEventListeners();
    }
  }

  setupEventListeners() {
    // Toggle menu on button click
    this.menuButton.addEventListener('click', () => this.toggleMenu());

    // Close menu when clicking close button
    if (this.closeButton) {
      this.closeButton.addEventListener('click', () => this.closeMenu());
    }

    // Close menu when clicking on overlay
    if (this.overlay) {
      this.overlay.addEventListener('click', () => this.closeMenu());
    }

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
      const isClickInsideMenu = this.mainMenu.contains(event.target);
      const isClickOnButton = this.menuButton.contains(event.target);
      const isClickOnOverlay = this.overlay && this.overlay.contains(event.target);

      if (!isClickInsideMenu && !isClickOnButton && !isClickOnOverlay &&
          this.mainMenu.classList.contains('main-menu--open')) {
        this.closeMenu();
      }
    });

    // Handle escape key
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && this.mainMenu.classList.contains('main-menu--open')) {
        this.closeMenu();
      }
    });
  }

  toggleMenu() {
    const isOpen = this.mainMenu.classList.contains('main-menu--open');

    if (isOpen) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }

  openMenu() {
    // Toggle active class on menu button
    this.menuButton.classList.add('active');

    // Toggle menu visibility class - CSS handles animation
    this.mainMenu.classList.add('main-menu--open');

    // Add overlay visible class - CSS handles animation
    if (this.overlay) {
      this.overlay.classList.add('header__overlay--visible');
    }

    // Update ARIA attributes
    this.menuButton.setAttribute('aria-expanded', 'true');

    // Prevent body scrolling
    this.body.classList.add('menu-open');

    // Optional: Add staggered menu item animation with CSS classes
    this.animateMenuItems(true);
  }

  closeMenu() {
    // Remove menu items animation classes first
    this.animateMenuItems(false);
    
    // Remove overlay visible class - CSS handles animation
    if (this.overlay) {
      this.overlay.classList.remove('header__overlay--visible');
    }

    // Remove menu visibility class - CSS handles animation  
    this.mainMenu.classList.remove('main-menu--open');

    // Wait for CSS transition to complete before cleanup
    setTimeout(() => {
      // Remove button active state and attributes
      this.menuButton.classList.remove('active');
      this.menuButton.setAttribute('aria-expanded', 'false');
      
      // Restore body scrolling
      this.body.classList.remove('menu-open');
    }, 300); // Match CSS transition duration
  }

  animateMenuItems(isOpening) {
    // Add/remove animation classes for menu items with stagger
    this.menuItems.forEach((item, index) => {
      const delay = index * 50; // 50ms stagger
      
      if (isOpening) {
        setTimeout(() => {
          item.classList.add('menu-item--animate-in');
        }, delay);
      } else {
        const reverseDelay = (this.menuItems.length - 1 - index) * 30; // Reverse stagger
        setTimeout(() => {
          item.classList.remove('menu-item--animate-in');
          item.classList.add('menu-item--animate-out');
        }, reverseDelay);
      }
    });

    // Clean up animation classes after closing
    if (!isOpening) {
      setTimeout(() => {
        this.menuItems.forEach(item => {
          item.classList.remove('menu-item--animate-out');
        });
      }, 300);
    }
  }
}

// Initialize Menu Animation on DOM load
document.addEventListener('DOMContentLoaded', () => {
  window.menuController = new MenuAnimationController();
});
