// TripPlanner.js - extracted from Trip-planner.html inline scripts
(function () {
  'use strict';

  function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-section]');
    const navSubItems = document.querySelectorAll('.nav-sub[data-section]');

    // Handle main nav items
    navItems.forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.section;
        const target = document.getElementById(id);
        if (!target) return;

        target.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Update active class for main nav items
        navItems.forEach(b => b.classList.remove('nav-item--active'));
        btn.classList.add('nav-item--active');

        // Remove active from submenu items
        navSubItems.forEach(b => b.classList.remove('nav-item--active'));
      });
    });

    // Handle submenu nav items: keep Overview active + highlight submenu item
    navSubItems.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.dataset.section;
        const target = document.getElementById(id);
        if (!target) return;

        target.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Remove active from all nav items and submenu items
        navItems.forEach(b => b.classList.remove('nav-item--active'));
        navSubItems.forEach(b => b.classList.remove('nav-item--active'));

        // Keep Overview active and add active to the clicked submenu item
        const overviewBtn = document.getElementById('overview-btn');
        if (overviewBtn) {
          overviewBtn.classList.add('nav-item--active');
        }
        btn.classList.add('nav-item--active');
      });
    });
  }

  function setupOverviewToggle() {
    const overviewBtn = document.getElementById('overview-btn');
    const overviewSubmenu = document.getElementById('overview-submenu');
    if (!overviewBtn || !overviewSubmenu) return;

    overviewBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      const isVisible = overviewSubmenu.style.display === 'block';
      overviewSubmenu.style.display = isVisible ? 'none' : 'block';
      // update aria-expanded and chevron rotation
      overviewBtn.setAttribute('aria-expanded', String(!isVisible));
      if (!isVisible) {
        overviewBtn.classList.add('nav-item--chev-rotated');
      } else {
        overviewBtn.classList.remove('nav-item--chev-rotated');
      }
    });
  }

  function addCarouselLogic(trackId, wrapper) {
    const track = document.getElementById(trackId);
    if (!track || !wrapper) return;
    const prev = wrapper.querySelector('.prev-btn');
    const next = wrapper.querySelector('.next-btn');
    const scrollBy = Math.max(260, Math.floor(track.clientWidth * 0.6));

    if (next) {
      next.addEventListener('click', () => {
        track.scrollBy({ left: scrollBy, behavior: 'smooth' });
      });
    }
    if (prev) {
      prev.addEventListener('click', () => {
        track.scrollBy({ left: -scrollBy, behavior: 'smooth' });
      });
    }
  }

  function setupCarousels() {
    document.querySelectorAll('.carousel-wrapper').forEach(wrapper => {
      const track = wrapper.querySelector('.carousel-track');
      if (!track) return;
      if (track.id === 'recommended-carousel') addCarouselLogic('recommended-carousel', wrapper);
      if (track.id === 'saved-carousel') addCarouselLogic('saved-carousel', wrapper);
    });
  }

  function setupMap() {
    if (typeof L === 'undefined') return;
    const defaultCenter = [48.8566, 2.3522];
    const map = L.map('smarttour-map').setView(defaultCenter, 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    L.marker([48.8584, 2.2945])
      .addTo(map)
      .bindPopup('<b>Eiffel Tower</b><br>Iconic landmark in Paris.')
      .openPopup();
  }

  function setupSettingsModal() {
    // Debug: Kiểm tra xem script có chạy không
    console.log('TripPlanner: setupSettingsModal');

    const settingsButton = document.getElementById('settings-btn') || document.querySelector('.hero-card__actions .icon-button[aria-label="Settings"]');
    const settingsModal = document.getElementById('settings-modal');

    if (!settingsButton || !settingsModal) {
      console.warn('TripPlanner: settings button or modal not found');
      return;
    }

    // Open modal
    settingsButton.addEventListener('click', function (e) {
      e.stopPropagation();
      settingsModal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    });

    // Close controls
    const closeButtons = [
      document.getElementById('close-settings'),
      document.getElementById('cancel-settings')
    ].filter(Boolean);

    closeButtons.forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      });
    });

    // Close when clicking outside
    settingsModal.addEventListener('click', function (e) {
      if (e.target === this) {
        settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });

    // Travelers counter
    const decreaseTravelersBtn = document.getElementById('decrease-travelers');
    const increaseTravelersBtn = document.getElementById('increase-travelers');
    const travelersCountInput = document.getElementById('travelers-count');

    if (decreaseTravelersBtn && increaseTravelersBtn && travelersCountInput) {
      decreaseTravelersBtn.addEventListener('click', function () {
        let currentValue = parseInt(travelersCountInput.value) || 1;
        if (currentValue > 1) travelersCountInput.value = currentValue - 1;
      });

      increaseTravelersBtn.addEventListener('click', function () {
        let currentValue = parseInt(travelersCountInput.value) || 1;
        if (currentValue < 20) travelersCountInput.value = currentValue + 1;
      });
    }

    // Budget slider
    const budgetSlider = document.getElementById('budget-slider');
    const budgetValue = document.getElementById('budget-value');

    if (budgetSlider && budgetValue) {
      budgetSlider.addEventListener('input', function () {
        budgetValue.textContent = this.value;
      });
    }

    // Save settings
    const saveSettingsBtn = document.getElementById('save-settings');
    if (saveSettingsBtn) {
      saveSettingsBtn.addEventListener('click', function () {
        settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
        // Simple notification
        alert('Settings saved!');
      });
    }

    // Escape key to close
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && settingsModal.style.display === 'flex') {
        settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });

    console.log('TripPlanner: settings modal handlers attached');
  }

  function setupTitleEditor() {
    const editBtn = document.getElementById('edit-title-btn') || document.querySelector('.edit-title-btn');
    if (!editBtn) return;

    editBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      const titleEl = document.querySelector('.hero-card__title');
      if (!titleEl) return;

      // Prevent multiple inputs
      if (titleEl.tagName.toLowerCase() === 'input') return;

      const current = titleEl.textContent.trim();
      const input = document.createElement('input');
      input.type = 'text';
      input.value = current;
      input.className = 'title-edit-input';

      // Replace h1 with input
      titleEl.replaceWith(input);
      input.focus();
      input.select();

      function finish(save) {
        const h1 = document.createElement('h1');
        h1.className = 'hero-card__title';
        h1.textContent = save ? (input.value.trim() || 'Untitled Trip') : current;
        input.replaceWith(h1);
      }

      input.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
          finish(true);
        } else if (ev.key === 'Escape') {
          finish(false);
        }
      });

      input.addEventListener('blur', () => {
        finish(true);
      });
    });
  }

  // Initialize all behaviors after DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
      setupNavigation();
      setupOverviewToggle();
      setupCarousels();
      setupMap();
      setupSettingsModal();
      setupTitleEditor();
    });

})();
