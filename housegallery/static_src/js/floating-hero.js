/**
 * Floating Hero Images
 * Continuous right-to-left floating images for the hero section
 */

class FloatingHero {
    constructor(element) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;
        if (!this.element) return;

        this.container = this.element.querySelector('.floating-hero__container');

        // Configuration
        this.imageSizes = ['tiny', 'small', 'medium', 'large', 'huge'];
        this.sizeWeights = [20, 30, 25, 20, 5]; // Probability weights for each size
        
        // Transform groups configuration
        this.groupCount = 5; // 5 groups for up to 20 images
        this.groupSpeeds = [45, 55, 65, 75, 85]; // Different speeds in seconds
        this.groupDelays = [0, 8, 16, 24, 32]; // Staggered start delays
        
        // State
        this.isAnimating = false;
        this.images = [];
        this.groups = [];
        
        // Performance optimization
        this.preferReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isMobile = window.innerWidth <= 768;
        
        // Cache container dimensions for stable positioning
        this.containerHeight = 0;
        this.resizeObserver = null;
        this.intersectionObserver = null;
        this.isVisible = true;
        
        this.init();
    }

    init() {
        if (this.preferReducedMotion) {
            console.log('⚡ Reduced motion preference detected, skipping floating hero animation');
            return;
        }

        this.setupImages();
        this.setupEventListeners();
        this.startAnimation();
    }

    setupImages() {
        // Get all floating images
        const images = Array.from(this.container.querySelectorAll('[data-floating-image]'));
        
        console.log(`🎨 Floating Hero: Found ${images.length} images`);
        
        if (images.length === 0) {
            console.log('⚠️ No floating images found, skipping animation');
            return;
        }

        // Cache container height for stable positioning
        this.containerHeight = this.container.offsetHeight;

        // Store images for processing
        this.images = images;
        
        // Create transform groups
        this.createTransformGroups();
        
        // Distribute images into groups
        this.distributeImagesIntoGroups();
        
        console.log(`✅ Floating hero: ${images.length} images grouped into ${this.groups.length} transform groups`);
    }

    createTransformGroups() {
        // Determine how many groups we need (max 5, min based on image count)
        const actualGroupCount = Math.min(this.groupCount, Math.ceil(this.images.length / 2));
        
        // Create group containers
        for (let i = 0; i < actualGroupCount; i++) {
            const group = document.createElement('div');
            group.className = 'floating-hero__group';
            group.dataset.groupIndex = i;
            
            // Apply animation immediately to prevent flash
            const speed = this.groupSpeeds[i] || this.groupSpeeds[0];
            const delay = this.groupDelays[i] || 0;
            
            group.style.animationName = 'floating-hero-group';
            group.style.animationDuration = `${speed}s`;
            group.style.animationTimingFunction = 'linear';
            group.style.animationIterationCount = 'infinite';
            group.style.animationDelay = `${delay}s`;
            
            this.container.appendChild(group);
            this.groups.push(group);
        }
        
        console.log(`🔧 Created ${actualGroupCount} transform groups with immediate animations`);
    }

    distributeImagesIntoGroups() {
        // Remove images from DOM temporarily
        this.images.forEach(img => img.remove());
        
        // Distribute images into groups and assign properties
        this.images.forEach((img, index) => {
            const groupIndex = index % this.groups.length;
            const group = this.groups[groupIndex];
            
            // Assign size class
            const sizeClass = this.getRandomWeightedSize();
            img.classList.add(`floating-hero__image--${sizeClass}`);
            
            // Position within group (vertical spread) - use container height instead of viewport
            const verticalOffset = (Math.random() - 0.5) * (this.containerHeight * 0.6);
            img.style.setProperty('--vertical-offset', `${verticalOffset}px`);
            
            // Random horizontal spacing within group
            const horizontalSpacing = Math.random() * 300; // 0-300px spacing
            img.style.setProperty('--horizontal-spacing', `${horizontalSpacing}px`);
            
            // Add to group
            group.appendChild(img);
        });
        
        console.log(`📦 Distributed ${this.images.length} images into ${this.groups.length} groups`);
    }


    getRandomWeightedSize() {
        const totalWeight = this.sizeWeights.reduce((sum, weight) => sum + weight, 0);
        const random = Math.random() * totalWeight;
        
        let weightSum = 0;
        for (let i = 0; i < this.imageSizes.length; i++) {
            weightSum += this.sizeWeights[i];
            if (random <= weightSum) {
                return this.imageSizes[i];
            }
        }
        
        return this.imageSizes[0]; // Fallback
    }

    startAnimation() {
        if (this.isAnimating || !this.isVisible || this.preferReducedMotion) return;
        
        this.isAnimating = true;
        
        // Ensure group animations are running
        this.groups.forEach(group => {
            group.style.animationPlayState = 'running';
        });
        
        console.log('🚀 Floating hero group animations started');
    }

    setupEventListeners() {
        // Use ResizeObserver for better performance than window resize events
        if ('ResizeObserver' in window) {
            this.resizeObserver = new ResizeObserver((entries) => {
                for (let entry of entries) {
                    this.handleContainerResize(entry.contentRect);
                }
            });
            this.resizeObserver.observe(this.container);
        } else {
            // Fallback for older browsers
            window.addEventListener('resize', () => {
                this.handleResize();
            });
        }
        
        // Use Intersection Observer to pause animations when off-screen
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    this.isVisible = entry.isIntersecting;
                    if (entry.isIntersecting) {
                        this.startAnimation();
                    } else {
                        this.stop();
                    }
                });
            }, {
                rootMargin: '50px 0px', // Start animation slightly before visible
                threshold: 0.1
            });
            this.intersectionObserver.observe(this.element);
        }
        
        // Handle reduced motion preference changes
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        mediaQuery.addEventListener('change', (e) => {
            if (e.matches) {
                this.stop();
            } else if (this.isVisible) {
                this.startAnimation();
            }
        });
    }

    handleContainerResize(contentRect) {
        // Modern ResizeObserver handler - more efficient than window resize
        this.isMobile = window.innerWidth <= 768;
        
        // Update cached container height from ResizeObserver
        this.containerHeight = contentRect.height;
        
        // Re-calculate vertical offsets using stable container height
        this.images.forEach(img => {
            const verticalOffset = (Math.random() - 0.5) * (this.containerHeight * 0.6);
            img.style.setProperty('--vertical-offset', `${verticalOffset}px`);
        });
    }

    handleResize() {
        // Fallback debounced resize handling for older browsers
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.isMobile = window.innerWidth <= 768;
            
            // Update cached container height
            this.containerHeight = this.container.offsetHeight;
            
            // Re-calculate vertical offsets using stable container height
            this.images.forEach(img => {
                const verticalOffset = (Math.random() - 0.5) * (this.containerHeight * 0.6);
                img.style.setProperty('--vertical-offset', `${verticalOffset}px`);
            });
        }, 250);
    }

    stop() {
        this.isAnimating = false;
        
        // Pause group animations by setting animation-play-state
        this.groups.forEach(group => {
            group.style.animationPlayState = 'paused';
        });
        
        console.log('⏹️ Floating hero groups stopped');
    }

    start() {
        if (!this.preferReducedMotion) {
            this.isAnimating = true;
            
            // Resume group animations
            this.groups.forEach(group => {
                group.style.animationPlayState = 'running';
            });
            
            console.log('▶️ Floating hero groups started');
        }
    }

    destroy() {
        this.stop();
        
        // Clean up resize timeout
        clearTimeout(this.resizeTimeout);
        
        // Clean up observers
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
        
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
            this.intersectionObserver = null;
        }
        
        // Clean up fallback event listener
        window.removeEventListener('resize', this.handleResize.bind(this));
        
        console.log('🔥 Floating hero destroyed');
    }
}

// Initialize floating hero when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const floatingHero = document.querySelector('[data-floating-hero]');
    if (floatingHero && !window.floatingHero) {
        console.log('🎬 Initializing Floating Hero...');
        window.floatingHero = new FloatingHero(floatingHero);
    } else if (window.floatingHero) {
        console.log('⚠️ FloatingHero already initialized, skipping...');
    }
});

// Export for global access
if (typeof window !== 'undefined') {
    window.FloatingHero = FloatingHero;
}