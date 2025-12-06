// TripPlanner.js - extracted from Trip-planner.html inline scripts
(function () {
  'use strict';

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
  const mapElement = document.getElementById('smarttour-map');
  if (!mapElement) return;

  // Lấy destination từ session (Django render vào HTML)
  const destination = mapElement.getAttribute('data-destination');

  // Nếu chưa có destination thì set mặc định Paris
  const defaultDestination = "Paris, France";
  const dest = destination && destination.trim() !== "" ? destination : defaultDestination;

  console.log("Setting map for destination:", dest);

  // Chuyển đổi tên destination thành URL Google Maps
  const mapsUrl = `https://www.google.com/maps?q=${encodeURIComponent(dest)}&output=embed`;

  // Thêm iframe vào mapElement
  mapElement.innerHTML = `<iframe 
      width="100%" 
      height="100%" 
      style="border:0;" 
      loading="lazy" 
      allowfullscreen
      src="${mapsUrl}">
    </iframe>`;
}


  function setupSettingsModal() {
    // Debug: Kiểm tra xem script có chạy không
    console.log('TripPlanner: setupSettingsModal');

    // Function to show toast notification
    function showToast(message, type = 'success') {
      // Create toast element
      const toast = document.createElement('div');
      toast.className = `toast toast--${type}`;
      toast.textContent = message;
      toast.style.cssText = `
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        padding: 15px 25px;
        border-radius: 6px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        z-index: 10002;
        font-family: Arial, sans-serif;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        opacity: 0;
        transition: all 0.2s ease;
        pointer-events: none;
      `;
      
      document.body.appendChild(toast);
      
      // Animate in
      setTimeout(() => {
        toast.style.opacity = '1';
      }, 10);
      
      // Auto remove after 1 seconds
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }, 1000);
    }

    const settingsButton = document.getElementById('settings-btn') || document.querySelector('.hero-card__actions .icon-button[aria-label="Settings"]');
    const settingsModal = document.getElementById('settings-modal');

    if (!settingsButton || !settingsModal) {
      console.warn('TripPlanner: settings button or modal not found');
      return;
    }

    // Open modal
    settingsButton.addEventListener('click', function (e) {
      e.stopPropagation();
      // Populate inputs with current values
      const metaPills = document.querySelectorAll('.meta-pill');
      metaPills.forEach(pill => {
        const icon = pill.querySelector('.meta-pill__icon');
        if (icon && icon.textContent.includes('👥')) {
          const textNode = Array.from(pill.childNodes).find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
          if (textNode) {
            const match = textNode.textContent.trim().match(/(\d+) travelers/);
            if (match && travelersCountInput) {
              travelersCountInput.value = match[1];
            }
          }
        }
      });
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
<<<<<<< HEAD
      saveSettingsBtn.addEventListener('click', function (e) {
        e.preventDefault(); // Prevent form submission
        
        // Get current values
        const travelers = travelersCountInput ? travelersCountInput.value : null;
        const budget = budgetSlider ? budgetSlider.value : null;
        
        // Send AJAX request
        fetch('/update-trip-settings/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: new URLSearchParams({
            travelers: travelers,
            budget: budget
          })
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Update the display
            const metaPills = document.querySelectorAll('.meta-pill');
            metaPills.forEach(pill => {
              const icon = pill.querySelector('.meta-pill__icon');
              if (icon && icon.textContent.includes('👥')) {
                const textNode = Array.from(pill.childNodes).find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
                if (textNode && travelers) {
                  textNode.textContent = ` ${travelers} travelers`;
                }
              }
            });
            showToast('Settings saved successfully!');
          } else {
            showToast('Error saving settings: ' + (data.error || 'Unknown error'), 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Error saving settings', 'error');
        });
      });
    }
=======
      saveSettingsBtn.addEventListener("click", function (e) {
          e.preventDefault();

          const start = document.getElementById("start-date").value;
          const end = document.getElementById("end-date").value;
          const travelers = document.getElementById("travelers-count").value;
          const budget = document.getElementById("budget-slider").value;

          const payload = new FormData();
          payload.append("start_date", start);
          payload.append("end_date", end);
          payload.append("travelers", travelers);
          payload.append("budget", budget);

          // ⭐ Cập nhật Hero Card ngay lập tức
          const heroDates = document.getElementById("hero-trip-dates");
          
          if (heroDates) {
              function fmt(dateStr) {
                  const d = new Date(dateStr);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
              }
              heroDates.textContent = `${fmt(start)} – ${fmt(end)}`;
          }

          // UPDATE TRAVELERS COUNT IN HERO CARD
          // ⭐ Cập nhật Travelers trên Hero Card
              const travelersValue = document.getElementById("travelers-count").value;
              const travelersDisplay = document.getElementById("hero-travelers");

              if (travelersDisplay) {
                  travelersDisplay.innerHTML = `
                      <span class="meta-pill__icon">👥</span>
                      ${travelersValue} traveler${travelersValue > 1 ? "s" : ""}
                  `;
              }

              const tripType = document.querySelector('input[name="trip-type"]:checked').value;
              payload.append("trip_type", tripType);

          // ⭐ Gửi lên Django mà KHÔNG reload trang
          fetch("/update-trip/", {
              method: "POST",
              headers: {
                  "X-CSRFToken": getCookie("csrftoken"),
              },
              body: payload,
          })
              .then(res => res.json())
              .then(data => {
                  if (data.status === "ok") {
                      settingsModal.style.display = "none";
                      document.body.style.overflow = "auto";
                      alert("Saved successfully!");
                  }
            });
    });
}

>>>>>>> Frontend

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
  
  document.querySelectorAll(".collapsible-header").forEach(header => {
      header.addEventListener("click", () => {
          const content = header.nextElementSibling;
          header.classList.toggle("collapsed");

          if (content.style.display === "none") {
              content.style.display = "block";
          } else {
              content.style.display = "none";
          }
      });
});

  // Initialize all behaviors after DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
      setupNavigation();
      setupOverviewToggle();
      setupCarousels();
      setupMap();
      setupSettingsModal();
      setupTitleEditor();
      setupSectionToggles();
    });

    document.addEventListener("DOMContentLoaded", () => {
      const prevBtns = document.querySelectorAll(".carousel-btn.prev-btn");
      const nextBtns = document.querySelectorAll(".carousel-btn.next-btn");

      prevBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
          const track = btn.nextElementSibling; // assumes button -> track
          const cardWidth = track.querySelector(".explore-card").offsetWidth + 16; // margin/padding
          track.scrollBy({ left: -cardWidth, behavior: "smooth" });
        });
      });

      nextBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
          const track = btn.previousElementSibling; // assumes track -> button
          const cardWidth = track.querySelector(".explore-card").offsetWidth + 16;
          track.scrollBy({ left: cardWidth, behavior: "smooth" });
        });
      });
    });

})();
