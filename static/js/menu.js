// menu.js - Main Menu Animations with anime.js
import { animate, createTimeline, stagger } from 'animejs'

// Menu Animation Controller
class MenuAnimationController {
  constructor() {
    // DOM Elements
    this.menuButton = document.querySelector('.header__menu-button');
    this.closeButton = document.querySelector('.main-menu__close-button');
    this.mainMenu = document.getElementById('main-menu');
    this.body = document.body;
    this.overlay = document.querySelector('.header__overlay');
    this.menuItems = document.querySelectorAll('.main-menu__item');
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

    // Toggle menu visibility class for CSS hook
    this.mainMenu.classList.add('main-menu--open');

    // Add overlay visible class
    if (this.overlay) {
      this.overlay.classList.add('header__overlay--visible');
    }

    // Update ARIA attributes
    this.menuButton.setAttribute('aria-expanded', 'true');

    // Prevent body scrolling
    this.body.classList.add('menu-open');

    // Create and play opening animation
    const openAnimation = createTimeline({
      easing: 'easeOutExpo',
      duration: 700
    });

    // Menu container animation
    openAnimation.add({
      targets: this.mainMenu,
      translateX: ['100%', '0%'],
      opacity: [0, 1],
      duration: 600
    });

    // Overlay animation
    if (this.overlay) {
      openAnimation.add({
        targets: this.overlay,
        opacity: [0, 1],
        duration: 500
      }, '-=500');
    }

    // Menu items animation
    openAnimation.add({
      targets: this.menuItems,
      translateY: [20, 0],
      opacity: [0, 1],
      delay: stagger(80),
      duration: 800
    }, '-=400');

    // CTA buttons animation
    if (this.ctaButtons.length > 0) {
      openAnimation.add({
        targets: this.ctaButtons,
        translateY: [20, 0],
        opacity: [0, 1],
        delay: stagger(100),
        duration: 800
      }, '-=600');
    }
  }

  closeMenu() {
    // Create closing animation
    const closeAnimation = createTimeline({
      easing: 'easeInOutQuad',
      duration: 500
    });

    // Animate menu items out first
    closeAnimation.add({
      targets: this.menuItems,
      translateY: [0, 10],
      opacity: [1, 0],
      delay: stagger(50, {from: 'last'}),
      duration: 300
    });

    // Animate CTA buttons out
    if (this.ctaButtons.length > 0) {
      closeAnimation.add({
        targets: this.ctaButtons,
        translateY: [0, 10],
        opacity: [0],
        delay: stagger(50, {from: 'last'}),
        duration: 300
      }, '-=200');
    }

    // Animate container out
    closeAnimation.add({
      targets: this.mainMenu,
      translateX: ['0%', '100%'],
      opacity: [1, 0],
      duration: 500,
      complete: () => {
        // Remove classes once animation completes
        this.mainMenu.classList.remove('main-menu--open');
        this.menuButton.classList.remove('active');
        this.menuButton.setAttribute('aria-expanded', 'false');
        this.body.classList.remove('menu-open');
      }
    }, '-=200');

    // Animate overlay out
    if (this.overlay) {
      closeAnimation.add({
        targets: this.overlay,
        opacity: [1, 0],
        duration: 300,
        complete: () => {
          this.overlay.classList.remove('header__overlay--visible');
        }
      }, '-=400');
    }
  }
}

// Initialize Menu Animation on DOM load
document.addEventListener('DOMContentLoaded', () => {
  window.menuController = new MenuAnimationController();
});
