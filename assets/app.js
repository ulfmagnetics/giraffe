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
        const showDraftsCheckbox = document.getElementById('show-drafts');
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

        if (showDraftsCheckbox) {
            showDraftsCheckbox.addEventListener('change', filterTracks);
        }

        // Filter function
        function filterTracks() {
            const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
            const showDrafts = showDraftsCheckbox ? showDraftsCheckbox.checked : true;
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

                // Filter by draft status
                if (!showDrafts) {
                    const status = card.dataset.status;
                    if (status === 'draft') {
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
})();
