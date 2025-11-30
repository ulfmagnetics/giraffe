// Client-side search and filtering for Giraffe music portfolio

(function() {
    'use strict';

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        // Only run on index page
        const trackGrid = document.getElementById('track-grid');
        if (!trackGrid) return;

        const searchInput = document.getElementById('search');
        const tagFiltersContainer = document.getElementById('tag-filters');
        const noResults = document.getElementById('no-results');
        const trackCards = Array.from(document.querySelectorAll('.track-card'));

        // Extract all unique tags from tracks
        const allTags = new Set();
        trackCards.forEach(card => {
            const tags = card.dataset.tags;
            if (tags) {
                tags.split(',').forEach(tag => allTags.add(tag.trim()));
            }
        });

        // Create tag filter buttons
        const sortedTags = Array.from(allTags).sort();
        sortedTags.forEach(tag => {
            const button = document.createElement('button');
            button.className = 'tag tag-filter';
            button.textContent = tag;
            button.dataset.tag = tag;
            button.addEventListener('click', () => {
                button.classList.toggle('active');
                filterTracks();
            });
            tagFiltersContainer.appendChild(button);
        });

        // Event listeners
        if (searchInput) {
            searchInput.addEventListener('input', filterTracks);
        }

        // Filter function
        function filterTracks() {
            const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
            const activeTagButtons = document.querySelectorAll('.tag-filter.active');
            const activeTags = Array.from(activeTagButtons).map(btn => btn.dataset.tag);

            let visibleCount = 0;

            trackCards.forEach(card => {
                let visible = true;

                // Filter by search term (title, category, year)
                if (searchTerm) {
                    const title = card.dataset.title || '';
                    const category = card.dataset.category || '';
                    const year = card.dataset.year || '';
                    const tags = card.dataset.tags || '';

                    const searchableText = `${title} ${category} ${year} ${tags}`.toLowerCase();
                    if (!searchableText.includes(searchTerm)) {
                        visible = false;
                    }
                }

                // Filter by active tags (AND logic - track must have all active tags)
                if (activeTags.length > 0) {
                    const trackTags = card.dataset.tags ? card.dataset.tags.split(',').map(t => t.trim()) : [];
                    const hasAllTags = activeTags.every(tag => trackTags.includes(tag));
                    if (!hasAllTags) {
                        visible = false;
                    }
                }

                // Show/hide card
                if (visible) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });

            // Show "no results" message if needed
            if (noResults) {
                noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        }

        // Add CSS for active tag filters
        const style = document.createElement('style');
        style.textContent = `
            .tag-filter {
                cursor: pointer;
                transition: all 0.2s;
                border: 1px solid transparent;
            }
            .tag-filter:hover {
                background: var(--border);
                border-color: var(--secondary-color);
            }
            .tag-filter.active {
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
            }
        `;
        document.head.appendChild(style);
    }

    // Image Carousel (for track detail pages)
    function initCarousel() {
        const carousel = document.querySelector('[data-carousel]');
        if (!carousel) return;

        const images = carousel.querySelectorAll('.carousel-image');
        const dots = carousel.querySelectorAll('.carousel-dot');
        const prevBtn = carousel.querySelector('.carousel-prev');
        const nextBtn = carousel.querySelector('.carousel-next');
        let currentIndex = 0;

        function showImage(index) {
            // Wrap around
            if (index < 0) index = images.length - 1;
            if (index >= images.length) index = 0;

            // Update images
            images.forEach((img, i) => {
                img.classList.toggle('active', i === index);
            });

            // Update dots
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i === index);
            });

            currentIndex = index;
        }

        // Navigation buttons
        if (prevBtn) {
            prevBtn.addEventListener('click', () => showImage(currentIndex - 1));
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => showImage(currentIndex + 1));
        }

        // Dot navigation
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => showImage(index));
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') showImage(currentIndex - 1);
            if (e.key === 'ArrowRight') showImage(currentIndex + 1);
        });
    }

    // Initialize carousel if on track page
    initCarousel();

    // Lightbox functionality
    function initLightbox() {
        const lightbox = document.getElementById('lightbox');
        const lightboxImage = document.getElementById('lightbox-image');
        if (!lightbox || !lightboxImage) return;

        const closeBtn = lightbox.querySelector('.lightbox-close');
        const prevBtn = lightbox.querySelector('.lightbox-prev');
        const nextBtn = lightbox.querySelector('.lightbox-next');

        // Get all clickable images
        const images = Array.from(document.querySelectorAll('.track-cover-large img, .carousel-image'));
        let currentLightboxIndex = 0;

        function openLightbox(index) {
            currentLightboxIndex = index;
            const imgSrc = images[index].src;
            lightboxImage.src = imgSrc;
            lightboxImage.alt = images[index].alt;

            lightbox.style.display = 'flex';
            // Trigger reflow for animation
            setTimeout(() => lightbox.classList.add('active'), 10);

            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox() {
            lightbox.classList.remove('active');
            setTimeout(() => {
                lightbox.style.display = 'none';
                document.body.style.overflow = '';
            }, 300);
        }

        function showLightboxImage(index) {
            if (index < 0) index = images.length - 1;
            if (index >= images.length) index = 0;

            currentLightboxIndex = index;
            lightboxImage.src = images[index].src;
            lightboxImage.alt = images[index].alt;
        }

        // Click on images to open lightbox
        images.forEach((img, index) => {
            img.addEventListener('click', (e) => {
                // Don't open lightbox if clicking carousel buttons
                if (e.target.closest('.carousel-btn')) return;
                openLightbox(index);
            });
        });

        // Close lightbox
        if (closeBtn) {
            closeBtn.addEventListener('click', closeLightbox);
        }

        // Click outside image to close
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target === lightboxImage) {
                closeLightbox();
            }
        });

        // Navigation buttons in lightbox
        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showLightboxImage(currentLightboxIndex - 1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showLightboxImage(currentLightboxIndex + 1);
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (lightbox.style.display === 'none') return;

            if (e.key === 'Escape') {
                closeLightbox();
            } else if (e.key === 'ArrowLeft' && images.length > 1) {
                showLightboxImage(currentLightboxIndex - 1);
            } else if (e.key === 'ArrowRight' && images.length > 1) {
                showLightboxImage(currentLightboxIndex + 1);
            }
        });
    }

    // Initialize lightbox
    initLightbox();
})();
