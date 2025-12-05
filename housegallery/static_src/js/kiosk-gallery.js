/**
 * Floating Particles Kiosk Gallery
 * Modern screensaver-style floating image gallery
 */

class KioskGallery {
    constructor(element) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;
        if (!this.element) return;

        this.container = this.element.querySelector('.kiosk-gallery-container');
        this.loadingElement = this.element.querySelector('#kiosk-loading');

        // Configuration
        this.maxParticles = 8; // Maximum particles on screen at once
        this.spawnInterval = 2000; // Milliseconds between spawning new particles
        this.minSpawnDelay = 1500; // Minimum delay between spawns
        this.maxSpawnDelay = 4000; // Maximum delay between spawns

        // Animation patterns and their weights (probability)
        this.animationPatterns = [
            { class: 'float-horizontal-slow', weight: 15 },
            { class: 'float-horizontal-medium', weight: 20 },
            { class: 'float-horizontal-fast', weight: 15 },
            { class: 'float-horizontal-reverse-slow', weight: 10 },
            { class: 'float-horizontal-reverse-medium', weight: 15 },
            { class: 'float-horizontal-reverse-fast', weight: 10 },
            { class: 'float-diagonal-up-slow', weight: 8 },
            { class: 'float-diagonal-up-medium', weight: 12 },
            { class: 'float-diagonal-down-slow', weight: 8 },
            { class: 'float-diagonal-down-medium', weight: 12 },
            { class: 'float-vertical-slow', weight: 5 },
            { class: 'float-vertical-medium', weight: 8 },
            { class: 'float-vertical-reverse-slow', weight: 5 },
            { class: 'float-vertical-reverse-medium', weight: 7 }
        ];

        // Particle size classes and their weights
        this.sizeClasses = [
            { class: 'particle-tiny', weight: 20 },
            { class: 'particle-small', weight: 30 },
            { class: 'particle-medium', weight: 25 },
            { class: 'particle-large', weight: 20 },
            { class: 'particle-huge', weight: 5 }
        ];

        // State
        this.sourceImages = [];
        this.activeParticles = [];
        this.isPaused = false;
        this.spawnTimer = null;

        // Performance optimization: Object pooling
        this.particlePool = [];
        this.maxPoolSize = 15; // Keep a few extra for smooth recycling

        this.init();
    }

    async init() {
        try {
            this.showLoading();
            await this.loadSourceImages();
            this.hideLoading();
            this.setupEventListeners();
            this.startParticleSystem();
        } catch (error) {
            this.hideLoading();
        }
    }

    showLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'block';
        }
    }

    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.classList.add('fade-out');
            setTimeout(() => {
                this.loadingElement.style.display = 'none';
            }, 500);
        }
    }

    async loadSourceImages() {
        // Get all gallery images from the StreamField content
        const galleryImages = this.container.querySelectorAll('.gallery-image, .gallery-single-image');

        if (galleryImages.length === 0) {
            throw new Error('No images found in gallery');
        }

        this.sourceImages = Array.from(galleryImages);

        // Hide original images (they'll be cloned as particles)
        this.sourceImages.forEach(img => {
            img.style.display = 'none';
        });

        // Preload images for better performance
        const imagePromises = this.sourceImages.map(item => {
            const img = item.querySelector('img');
            if (img && !img.complete) {
                return new Promise((resolve, reject) => {
                    img.onload = resolve;
                    img.onerror = reject;
                    if (img.complete) resolve();
                });
            }
            return Promise.resolve();
        });

        await Promise.all(imagePromises);
    }

    setupEventListeners() {
        // Performance optimization: Event delegation for click rotation
        this.container.addEventListener('click', (e) => {
            const particle = e.target.closest('.gallery-image, .gallery-single-image');
            if (particle && this.activeParticles.includes(particle)) {
                this.rotateParticle(particle);
            }
        });

        // Pause on hover/focus
        this.element.addEventListener('mouseenter', () => this.pauseParticleSystem());
        this.element.addEventListener('mouseleave', () => this.resumeParticleSystem());

        // Handle visibility changes (tab switching, etc.)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseParticleSystem();
            } else {
                this.resumeParticleSystem();
            }
        });

        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ') {
                e.preventDefault();
                this.toggleParticleSystem();
            }
        });
    }

    startParticleSystem() {
        this.isPaused = false;
        this.scheduleNextSpawn();
    }

    scheduleNextSpawn() {
        if (this.isPaused) return;

        const delay = this.minSpawnDelay + Math.random() * (this.maxSpawnDelay - this.minSpawnDelay);

        this.spawnTimer = setTimeout(() => {
            this.spawnParticle();
            this.scheduleNextSpawn();
        }, delay);
    }

    getPooledParticle() {
        // Performance optimization: Reuse pooled particles
        if (this.particlePool.length > 0) {
            return this.particlePool.pop();
        }

        // If pool is empty, create new particle
        const sourceImage = this.sourceImages[Math.floor(Math.random() * this.sourceImages.length)];
        return sourceImage.cloneNode(true);
    }

    returnParticleToPool(particle) {
        // Performance optimization: Reset and pool particle for reuse
        if (this.particlePool.length < this.maxPoolSize) {
            // Reset particle state
            particle.className = '';
            particle.style.cssText = '';
            particle.id = '';

            // Remove from DOM if attached
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }

            this.particlePool.push(particle);
        }
    }

    spawnParticle() {
        if (this.isPaused || this.activeParticles.length >= this.maxParticles) {
            return;
        }

        // Get particle from pool or create new one
        const particle = this.getPooledParticle();

        // CRITICAL: Override the inherited display: none
        particle.style.display = 'block';

        // Add unique ID for debugging
        particle.id = `particle-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Select random source for consistent styling
        const sourceImage = this.sourceImages[Math.floor(Math.random() * this.sourceImages.length)];

        // Assign random size
        const sizeClass = this.getRandomWeightedChoice(this.sizeClasses);
        particle.className = `${sourceImage.className} ${sizeClass.class}`;

        // Assign random animation pattern
        const animationClass = this.getRandomWeightedChoice(this.animationPatterns);
        particle.classList.add(animationClass.class);

        // Set custom CSS properties for animation variance
        this.setRandomAnimationProperties(particle);

        // Add to DOM
        this.container.appendChild(particle);
        this.activeParticles.push(particle);

        // Set up cleanup when animation completes
        this.setupParticleCleanup(particle, animationClass.class);
    }

    setRandomAnimationProperties(particle) {
        // Generate random CSS custom properties for animation variation
        const startY = (Math.random() - 0.5) * window.innerHeight * 0.6;
        const endY = (Math.random() - 0.5) * window.innerHeight * 0.6;
        const startX = (Math.random() - 0.5) * window.innerWidth * 0.3;
        const endX = (Math.random() - 0.5) * window.innerWidth * 0.3;

        const startScale = 0.7 + Math.random() * 0.4; // 0.7 to 1.1
        const endScale = 0.8 + Math.random() * 0.6;   // 0.8 to 1.4

        const startRotation = (Math.random() - 0.5) * 30; // -15 to 15 degrees
        const endRotation = (Math.random() - 0.5) * 40;   // -20 to 20 degrees

        particle.style.setProperty('--start-y', `${startY}px`);
        particle.style.setProperty('--end-y', `${endY}px`);
        particle.style.setProperty('--start-x', `${startX}px`);
        particle.style.setProperty('--end-x', `${endX}px`);
        particle.style.setProperty('--start-scale', startScale);
        particle.style.setProperty('--end-scale', endScale);
        particle.style.setProperty('--start-rotation', `${startRotation}deg`);
        particle.style.setProperty('--end-rotation', `${endRotation}deg`);
    }

    rotateParticle(particle) {
        // Get current computed transform to preserve floating animation
        const currentTransform = window.getComputedStyle(particle).transform;

        // Temporarily pause the CSS animation and apply rotation manually
        particle.style.animationPlayState = 'paused';

        // Apply rotation while preserving current position
        particle.style.transition = 'transform 500ms ease-out';
        particle.style.transform = `${currentTransform} rotateY(720deg)`;

        // Reset after animation
        setTimeout(() => {
            particle.style.transform = '';
            particle.style.transition = '';
            particle.style.animationPlayState = '';
        }, 500);
    }

    setupParticleCleanup(particle, animationClass) {
        // Extract animation duration from CSS (approximate)
        const durations = {
            'float-horizontal-slow': 25000,
            'float-horizontal-medium': 18000,
            'float-horizontal-fast': 12000,
            'float-horizontal-reverse-slow': 22000,
            'float-horizontal-reverse-medium': 16000,
            'float-horizontal-reverse-fast': 11000,
            'float-diagonal-up-slow': 28000,
            'float-diagonal-up-medium': 20000,
            'float-diagonal-up-fast': 14000,
            'float-diagonal-down-slow': 26000,
            'float-diagonal-down-medium': 19000,
            'float-diagonal-down-fast': 13000,
            'float-vertical-slow': 24000,
            'float-vertical-medium': 17000,
            'float-vertical-fast': 12000,
            'float-vertical-reverse-slow': 23000,
            'float-vertical-reverse-medium': 16000,
            'float-vertical-reverse-fast': 11000
        };

        const duration = durations[animationClass] || 15000;

        setTimeout(() => {
            this.removeParticle(particle);
        }, duration);
    }

    removeParticle(particle) {
        const index = this.activeParticles.indexOf(particle);
        if (index > -1) {
            this.activeParticles.splice(index, 1);
        }

        // Performance optimization: Return to pool instead of destroying
        this.returnParticleToPool(particle);
    }

    getRandomWeightedChoice(choices) {
        const totalWeight = choices.reduce((sum, choice) => sum + choice.weight, 0);
        const random = Math.random() * totalWeight;

        let weightSum = 0;
        for (const choice of choices) {
            weightSum += choice.weight;
            if (random <= weightSum) {
                return choice;
            }
        }

        return choices[choices.length - 1]; // Fallback
    }

    pauseParticleSystem() {
        this.isPaused = true;
        if (this.spawnTimer) {
            clearTimeout(this.spawnTimer);
            this.spawnTimer = null;
        }
    }

    resumeParticleSystem() {
        if (!this.isPaused) return;
        this.isPaused = false;
        this.scheduleNextSpawn();
    }

    toggleParticleSystem() {
        if (this.isPaused) {
            this.resumeParticleSystem();
        } else {
            this.pauseParticleSystem();
        }
    }

    destroy() {
        this.pauseParticleSystem();

        // Performance optimization: Clean up all particles and pool
        this.activeParticles.forEach(particle => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        });
        this.activeParticles = [];

        // Clear the object pool
        this.particlePool = [];
    }
}

// Initialize kiosk gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const kioskGallery = document.querySelector('#kiosk-gallery');
    if (kioskGallery && !window.kioskGallery) {
        window.kioskGallery = new KioskGallery(kioskGallery);
    }
});

// Export for global access
if (typeof window !== 'undefined') {
    window.KioskGallery = KioskGallery;
}
