/**
 * MAIN.JS - Gộp logic xử lý Itinerary, Expenses, Map và UI
 * Updated: Tích hợp AI Chat nâng cao
 */

// 1. HELPER FUNCTIONS (Dùng chung toàn bộ file)
// -----------------------------------------------------------------------------
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

const csrftoken = getCookie('csrftoken');
// Lấy ngôn ngữ từ URL một cách an toàn hơn
const pathParts = window.location.pathname.split('/');
const currentLang = (pathParts[1] && pathParts[1].length === 2) ? pathParts[1] : 'en';

// Hàm lấy dữ liệu từ biến Global (được định nghĩa trong HTML)
function getDjangoData() {
    return window.djangoContext || { 
        systemDestinations: [], 
        budget: "0", 
        travelers: "1",
        translations: {} 
    };
}

// 2. DOM CONTENT LOADED (Logic chính)
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
    const contextData = getDjangoData();
    const systemDestinations = contextData.systemDestinations;
    const trans = contextData.translations;

    // --- AI CHAT EVENT LISTENERS ---
    // Xử lý nút mở chat
    const aiBtn = document.querySelector('.ai-chip');
    if (aiBtn) {
        aiBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Ngăn chặn hành vi mặc định (tránh reload trang nếu nằm trong form)
            console.log("Đã click vào nút AI"); // Kiểm tra xem nút có nhận lệnh click không
            toggleChat();
        });
    } else {
        console.warn("Không tìm thấy nút có class '.ai-chip'");
    }
    
    // Xử lý nút đóng chat (nếu bạn thêm nút X vào header của chat panel)
    const closeAiBtn = document.querySelector('#ai-chat-panel button'); 
    if (closeAiBtn) {
        closeAiBtn.addEventListener('click', toggleChat);
    }

    // Xử lý phím Enter trong ô input
    const aiInput = document.getElementById('ai-user-input');
    if (aiInput) {
        aiInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();   // ⛔ CHẶN RELOAD
                sendAIMessage();      // ✅ GỬI AI
            }
        });
    }

    // --- BIẾN DOM CHUNG ---
    const startInput = document.getElementById("start-date");
    const endInput = document.getElementById("end-date");
    const daysContainer = document.getElementById("itinerary-days");
    const sidebarDaysContainer = document.getElementById("sidebar-days");

    // --- CÁC HÀM FORMAT ---
    function formatDate(date) {
        const options = { weekday: 'long', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    function formatDateShort(date) {
        const options = { weekday: 'short', month: 'numeric', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // --- LOGIC TẠO NGÀY (GENERATE DAYS) ---
    function generateDays() {
        daysContainer.innerHTML = "";
        sidebarDaysContainer.innerHTML = "";

        function parseDate(dateStr) {
            if (!dateStr) return null;
            const parts = dateStr.split('/');
            if (parts.length === 3) {
                return new Date(parts[2], parts[1] - 1, parts[0]);
            }
            return new Date(dateStr);
        }

        const start = parseDate(startInput.value);
        const end = parseDate(endInput.value);

        if (!start || !end || isNaN(start) || isNaN(end) || start > end) {
            daysContainer.innerHTML = "<p style='color:#999;'>Please select valid dates</p>";
            return;
        }

        let current = new Date(start);
        let dayNumber = 1;

        while (current <= end) {
            const formatted = formatDate(current);
            const formattedShort = formatDateShort(current);

            // Create day card UI
            const dayCard = document.createElement("div");
            dayCard.classList.add("itinerary-day-full");
            dayCard.setAttribute("data-day", dayNumber);

            dayCard.innerHTML = `
                <div class="itinerary-day-full__head">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>${formatted}</h3>
                        <div class="itinerary-day-full__actions" style="margin-right: 10px;">
                        </div>
                        <button class="day-toggle-btn" data-day="${dayNumber}">
                            <span class="toggle-icon">▼</span>
                        </button>
                    </div>
                </div>

                <div class="itinerary-day-content" style="display: none;">
                    <div class="day-explore-section">
                        <h4 style="margin: 16px 0; font-size: 16px; color: var(--text-main);">Recommended destinations</h4>
                        <div class="day-carousel-wrapper">
                            <button class="day-carousel-btn day-prev-btn" data-day="${dayNumber}">❮</button>
                            <div class="day-carousel-track" id="day-carousel-${dayNumber}"></div>
                            <button class="day-carousel-btn day-next-btn" data-day="${dayNumber}">❯</button>
                        </div>
                    </div>
                    <div class="itinerary-timeline"></div>
                    <div class="place-input-row">
                        <button class="place-input-btn" data-day="${dayNumber}">
                            <span style="color: #999;">+ Add a place</span>
                        </button>
                    </div>
                </div>
            `;

            daysContainer.appendChild(dayCard);
            
            // Toggle functionality
            const toggleBtn = dayCard.querySelector('.day-toggle-btn');
            const dayContent = dayCard.querySelector('.itinerary-day-content');
            
            toggleBtn.addEventListener('click', function() {
                const isOpen = dayContent.style.display !== 'none';
                if (isOpen) {
                    dayContent.style.display = 'none';
                    toggleBtn.querySelector('.toggle-icon').textContent = '▼';
                    toggleBtn.classList.remove('open');
                } else {
                    dayContent.style.display = 'block';
                    toggleBtn.querySelector('.toggle-icon').textContent = '▲';
                    toggleBtn.classList.add('open');
                }
            });
            
            populateDayCarousel(dayNumber);

            // Sidebar navigation item
            const sidebarBtn = document.createElement("button");
            sidebarBtn.classList.add("nav-item");
            sidebarBtn.setAttribute("data-section", "itinerary-section");
            sidebarBtn.setAttribute("data-day", dayNumber);
            sidebarBtn.innerHTML = `
                <span>${formattedShort}</span>
                <span class="nav-item__pill">0 stops</span>
            `;
            
            sidebarBtn.addEventListener('click', function() {
                const dayCard = document.querySelector(`.itinerary-day-full[data-day="${dayNumber}"]`);
                const mainContainer = document.querySelector('.main');
                if (dayCard && mainContainer) {
                    const mainRect = mainContainer.getBoundingClientRect();
                    const dayRect = dayCard.getBoundingClientRect();
                    const scrollOffset = dayRect.top - mainRect.top + mainContainer.scrollTop - 20;
                    
                    mainContainer.scrollTo({
                        top: scrollOffset,
                        behavior: 'smooth'
                    });
                }
            });

            sidebarDaysContainer.appendChild(sidebarBtn);

            // Bind events for the newly created buttons (Auto-fill & Optimize)
            bindDayActions(dayCard, formatted);

            current.setDate(current.getDate() + 1);
            dayNumber++;
        }

        attachPlaceInputListeners();
        setupDayCarousels();
    }

    function populateDayCarousel(dayNumber) {
        const carouselTrack = document.getElementById(`day-carousel-${dayNumber}`);
        if (!carouselTrack) return;
        
        if (!systemDestinations || systemDestinations.length === 0) {
            carouselTrack.innerHTML = `<p style="color: #999; padding: 20px; text-align: center;">${trans.noDestinations || 'No destinations'}</p>`;
            return;
        }
        
        systemDestinations.forEach(dest => {
            const rating = dest.rating ? dest.rating.replace(/,/g, '.') : '';
            const subtitle = dest.category + (rating ? ` | ${rating}` : '');
            const location = dest.address || dest.name;
            
            const miniCard = document.createElement('div');
            miniCard.classList.add('day-explore-card');
            miniCard.setAttribute('data-location', location);
            miniCard.style.cursor = 'pointer';
            miniCard.innerHTML = `
                <div class="day-explore-card__image" style="background-image: url('${dest.image}'); background-size: cover; background-position: center;"></div>
                <div class="day-explore-card__body">
                    <h5 class="day-explore-card__title">${dest.name}</h5>
                    <p class="day-explore-card__subtitle">${subtitle}</p>
                    <button class="btn-add-to-day" data-day="${dayNumber}">
                        + ${trans.addToDay || 'Add'}
                    </button>
                </div>
            `;
            
            miniCard.addEventListener('click', function(e) {
                if (!e.target.closest('.btn-add-to-day')) {
                    showMapLocation(location);
                    showDetailPanel(dest, rating);
                }
            });
            
            const addBtn = miniCard.querySelector('.btn-add-to-day');
            addBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                addPlaceToDay(parseInt(dayNumber), {
                    title: dest.name,
                    subtitle: subtitle,
                    image: `url('${dest.image}')`,
                    itemId: dest.id
                });
            });
            
            carouselTrack.appendChild(miniCard);
        });
    }

    function setupDayCarousels() {
        document.querySelectorAll('.day-carousel-wrapper').forEach(wrapper => {
            const track = wrapper.querySelector('.day-carousel-track');
            const prevBtn = wrapper.querySelector('.day-prev-btn');
            const nextBtn = wrapper.querySelector('.day-next-btn');
            
            if (!track || !prevBtn || !nextBtn) return;
            
            prevBtn.addEventListener('click', () => {
                track.scrollBy({ left: -300, behavior: 'smooth' });
            });
            
            nextBtn.addEventListener('click', () => {
                track.scrollBy({ left: 300, behavior: 'smooth' });
            });
        });
    }

    function attachPlaceInputListeners() {
        document.querySelectorAll('.place-input-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const day = parseInt(this.getAttribute('data-day'));
                if (!day || isNaN(day)) return;
                showPlaceSelector(day, this);
            });
        });
    }

    function showPlaceSelector(day, btnElement) {
        const dropdown = document.createElement('div');
        dropdown.classList.add('place-selector-dropdown');
        dropdown.innerHTML = `
            <div style="padding: 10px; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-height: 400px; overflow-y: auto;">
                <p style="font-weight: 600; margin-bottom: 10px;">${trans.savedDestination || 'Saved destination'}</p>
                <div id="place-options-list"></div>
            </div>
        `;
        
        btnElement.parentElement.appendChild(dropdown);
        loadSavedPlaces(day, dropdown);
    }

    function loadSavedPlaces(day, dropdown) {
        const savedCarousel = document.getElementById('saved-carousel');
        const savedCards = savedCarousel.querySelectorAll('.explore-card');
        const optionsList = dropdown.querySelector('#place-options-list');

        if (savedCards.length === 0) {
            optionsList.innerHTML = '<p style="color: #999; font-size: 0.9rem;">No saved destinations yet.</p>';
            return;
        }

        savedCards.forEach(card => {
            const title = card.querySelector('.explore-card__title').textContent;
            let subtitle = card.querySelector('.explore-card__subtitle').textContent.replace(/,/g, '.');
            const img = card.querySelector('.explore-card__image').style.backgroundImage;
            const removeBtn = card.querySelector('.remove-trip-item-btn');
            const destinationId = removeBtn?.getAttribute('data-destination-id');

            const option = document.createElement('div');
            option.classList.add('place-option');
            option.style.cssText = 'padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; align-items: center; gap: 10px;';
            option.innerHTML = `
                <div style="width: 50px; height: 50px; border-radius: 6px; background-size: cover; background-position: center; ${img}"></div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.9rem;">${title}</div>
                    <div style="font-size: 0.8rem; color: #666;">${subtitle}</div>
                </div>
            `;

            option.addEventListener('click', function() {
                addPlaceToDay(day, {
                    title: title,
                    subtitle: subtitle,
                    image: img,
                    itemId: destinationId
                });
                dropdown.remove();
            });

            option.addEventListener('mouseenter', function() { this.style.background = '#f5f5f5'; });
            option.addEventListener('mouseleave', function() { this.style.background = 'white'; });

            optionsList.appendChild(option);
        });

        setTimeout(() => {
            document.addEventListener('click', function closeDropdown(e) {
                if (!dropdown.contains(e.target)) {
                    dropdown.remove();
                    document.removeEventListener('click', closeDropdown);
                }
            });
        }, 100);
    }

    function addPlaceToDay(day, placeData, existingItemId = null, existingNotes = null) {
        const dayCard = document.querySelector(`.itinerary-day-full[data-day="${day}"]`);
        if (!dayCard) return;
        
        const timeline = dayCard.querySelector('.itinerary-timeline');
        const placeCard = document.createElement('div');
        placeCard.classList.add('place-card');
        
        let imageUrl = placeData.image || '';
        if (imageUrl.includes('url(')) {
            const match = imageUrl.match(/url\(['"]?([^'"\)]+)['"]?\)/);
            imageUrl = match ? match[1] : '';
        } else if (imageUrl.includes('background-image:')) {
            const match = imageUrl.match(/url\(['"]?([^'"\)]+)['"]?\)/);
            imageUrl = match ? match[1] : '';
        }

        placeCard.innerHTML = `
            <div class="place-card__timeline-marker"></div>
            <div class="place-card__content">
                <div class="place-card__image" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center;"></div>
                <div class="place-card__info">
                    <h4 class="place-card__title">${placeData.title}</h4>
                    <p class="place-card__subtitle">${placeData.subtitle}</p>
                    <div class="place-card__actions">
                        <button class="tiny-link add-note-btn" style="color: #ff8427;">Add note</button>
                        <span class="dot-separator">·</span>
                        <button class="tiny-link remove-place-btn" style="color: #ff8427;">Remove</button>
                    </div>
                </div>
            </div>
        `;

        timeline.appendChild(placeCard);
        
        if (placeData.itemId) placeCard.dataset.destinationId = placeData.itemId;
        
        if (existingItemId) {
            placeCard.dataset.itemId = existingItemId;
            if (existingNotes) {
                placeCard.dataset.note = existingNotes;
                renderNoteUI(placeCard, existingNotes);
            }
        }

        // Add Note Handler
        const addNoteBtn = placeCard.querySelector('.add-note-btn');
        addNoteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            openNoteModal(placeCard);
        });

        // Remove Handler
        placeCard.querySelector('.remove-place-btn').addEventListener('click', function() {
            const itemId = placeCard.dataset.itemId;
            if (itemId) {
                removeItineraryItem(itemId);
            }
            placeCard.remove();
            updateStopCount(day);
        });

        updateStopCount(day);
    }

    function renderNoteUI(placeCard, text) {
        const info = placeCard.querySelector('.place-card__info');
        let noteEl = placeCard.querySelector('.place-card__note');
        if (!noteEl) {
            noteEl = document.createElement('div');
            noteEl.classList.add('place-card__note');
            info.appendChild(noteEl);
        }
        noteEl.innerHTML = `<span style="color: #666;">📝 ${text}</span>`;
    }

    // --- CÁC HÀM API ---
    // (Đã rút gọn để code ngắn hơn nhưng vẫn giữ logic)
    async function saveItineraryItem(destinationId, day, order, notes = '') {
        try {
            const response = await fetch('/api/itinerary/save/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ destination_id: destinationId, day: day, order: order, notes: notes })
            });
            const data = await response.json();
            return data.success ? data.item_id : null;
        } catch (error) { console.error(error); return null; }
    }

    async function updateItineraryNote(itemId, notes) {
        try {
            const response = await fetch('/api/itinerary/update-note/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ item_id: itemId, notes: notes })
            });
            return (await response.json()).success;
        } catch (error) { return false; }
    }

    async function removeItineraryItem(itemId) {
        try {
            const response = await fetch('/api/itinerary/remove/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ item_id: itemId })
            });
            return (await response.json()).success;
        } catch (error) { return false; }
    }

    async function updateItineraryOrder(itemId, day, order, notes) {
        try {
            const response = await fetch('/api/itinerary/update/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ item_id: itemId, day: day, order: order, notes: notes })
            });
            return (await response.json()).success;
        } catch (error) { return false; }
    }

    async function loadItinerary() {
        try {
            const response = await fetch('/api/itinerary/get/');
            const data = await response.json();
            if (data.success) {
                const itemsWithDay = data.items.filter(item => item.day && item.day !== null);
                itemsWithDay.forEach(item => {
                    addPlaceToDay(item.day, {
                        title: item.destination.name,
                        subtitle: `${item.destination.category}${item.destination.rating ? ' | ' + item.destination.rating : ''}`,
                        image: item.destination.image,
                        itemId: item.destination.id
                    }, item.id, item.notes);
                });
            }
        } catch (error) { console.error(error); }
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6';
        notification.style.cssText = `position: fixed; top: 20px; right: 20px; padding: 16px 24px; background: ${bgColor}; color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 10000; font-weight: 500; animation: slideIn 0.3s ease-out;`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => { notification.remove(); }, 3300);
    }

    function updateStopCount(day) {
        const dayCard = document.querySelector(`.itinerary-day-full[data-day="${day}"]`);
        if(!dayCard) return;
        const placeCount = dayCard.querySelectorAll('.place-card').length;
        const sidebarBtn = document.querySelector(`#sidebar-days .nav-item[data-day="${day}"]`);
        if (sidebarBtn) sidebarBtn.querySelector('.nav-item__pill').textContent = `${placeCount} stop${placeCount !== 1 ? 's' : ''}`;
    }

    // --- FLATPICKR INITIALIZATION ---
    let startPicker, endPicker;
    if (startInput && endInput) {
        startPicker = flatpickr(startInput, {
            dateFormat: "d/m/Y",
            minDate: "today",
            disableMobile: true,
            onChange: function (selectedDates) {
                if (selectedDates.length > 0) {
                    endPicker.set("minDate", selectedDates[0]);
                    if (endPicker.selectedDates.length > 0 && endPicker.selectedDates[0] < selectedDates[0]) {
                        endPicker.clear();
                    }
                }
                generateDays();
            }
        });

        endPicker = flatpickr(endInput, {
            dateFormat: "d/m/Y",
            minDate: "today",
            disableMobile: true,
            onChange: function () { generateDays(); }
        });
    }

    // --- ADD DAY BUTTON ---
    const addDayBtn = document.getElementById('add-day-btn');
    if (addDayBtn) {
        addDayBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!endPicker.selectedDates || endPicker.selectedDates.length === 0) {
                const startDate = startPicker.selectedDates[0] || new Date();
                endPicker.setDate(startDate, true);
                return;
            }
            const newEndDate = new Date(endPicker.selectedDates[0]);
            newEndDate.setDate(newEndDate.getDate() + 1);
            endPicker.setDate(newEndDate, true);
            
            setTimeout(() => {
                const daysContainer = document.getElementById("itinerary-days");
                const newDayCard = daysContainer.lastElementChild;
                if (newDayCard) newDayCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        });
    }

    // --- SAVE TRIP BUTTON ---
    const saveTripBtn = document.getElementById('save-trip-btn');
    if (saveTripBtn) {
        saveTripBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const originalText = saveTripBtn.innerHTML;
            saveTripBtn.innerHTML = '⏳ Saving...';
            saveTripBtn.disabled = true;

            try {
                const tripData = {
                    title: document.getElementById('trip-title').innerText.replace('Trip to ', '').trim(),
                    start_date: document.getElementById('start-date').value,
                    end_date: document.getElementById('end-date').value,
                    budget: document.getElementById('budget-slider').value,
                    travelers: document.getElementById('travelers-count').value,
                    items: [] 
                };

                document.querySelectorAll('.itinerary-day-full').forEach(dayCard => {
                    const dayNumber = parseInt(dayCard.getAttribute('data-day'));
                    dayCard.querySelectorAll('.place-card').forEach((placeCard, index) => {
                        const destinationId = placeCard.dataset.destinationId;
                        if (destinationId) {
                            tripData.items.push({
                                destination_id: destinationId,
                                day: dayNumber,
                                order: index,
                                notes: placeCard.dataset.note || ''
                            });
                        }
                    });
                });

                const apiUrl = `/${currentLang}/api/save-full-trip/`;
                const response = await fetch(apiUrl, { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                    body: JSON.stringify(tripData)
                });

                if (!response.ok) throw new Error(`Server error ${response.status}`);
                const result = await response.json();

                if (result.success) showNotification('Trip saved successfully!', 'success');
                else showNotification('Error: ' + result.message, 'error');

            } catch (error) {
                showNotification('Save failed: ' + error.message, 'error');
            } finally {
                saveTripBtn.innerHTML = originalText;
                saveTripBtn.disabled = false;
            }
        });
    }

    // --- AUTO FILL TRIP BUTTON ---
    const autoFillBtn = document.getElementById('auto-fill-btn');
    if (autoFillBtn) {
        autoFillBtn.addEventListener('click', async function() {
            const savedCarousel = document.getElementById('saved-carousel');
            const savedCards = Array.from(savedCarousel.querySelectorAll('.explore-card'));
            const dayCards = document.querySelectorAll('.itinerary-day-full');
            const totalDays = dayCards.length;

            if (savedCards.length === 0) { alert('No saved destinations to auto-fill.'); return; }
            if (totalDays === 0) { alert('Please add days to your trip first.'); return; }
            if (!confirm(`${trans.autoFillConfirm || 'Auto-fill'} ${savedCards.length} ${trans.placesAcross || 'places'} ${totalDays} ${trans.days || 'days?'}`)) return;

            const originalText = autoFillBtn.innerHTML;
            autoFillBtn.innerHTML = '⏳ Processing...';
            autoFillBtn.disabled = true;

            let currentDayIndex = 0;
            
            for (const card of savedCards) {
                const title = card.querySelector('.explore-card__title').textContent;
                const subtitle = card.querySelector('.explore-card__subtitle').textContent;
                const imgStyle = card.querySelector('.explore-card__image').style.backgroundImage;
                const removeBtn = card.querySelector('.remove-trip-item-btn');
                const destinationId = removeBtn?.getAttribute('data-destination-id'); 

                const targetDayCard = dayCards[currentDayIndex];
                const dayNumber = parseInt(targetDayCard.getAttribute('data-day'));
                
                addPlaceToDay(dayNumber, {
                    title: title,
                    subtitle: subtitle,
                    image: imgStyle,
                    itemId: destinationId
                }, null);

                card.remove();
                currentDayIndex = (currentDayIndex + 1) % totalDays;
            }

            if (savedCarousel.children.length === 0) savedCarousel.innerHTML = `<p>${trans.noDestinations}</p>`;
            
            for(let i = 1; i <= totalDays; i++) updateStopCount(i);
            
            showNotification(trans.autoFillSuccess || 'Success!', 'success');
            autoFillBtn.innerHTML = originalText;
            autoFillBtn.disabled = false;
        });
    }

    // --- EVENT DELEGATION FOR DYNAMIC BUTTONS (Optimize & Auto-fill Day) ---
    function bindDayActions(dayCard, dayName) {
        // Auto-fill day
        const afBtn = dayCard.querySelector('.auto-fill-day-btn');
        if(afBtn) {
            afBtn.addEventListener('click', function(e) {
                e.preventDefault();
                fetch('/auto-fill-day/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                    body: JSON.stringify({ day: dayName })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        alert('Auto-filled: ' + data.suggested.map(i => i.name).join(', '));
                        window.location.reload();
                    } else alert(data.message || 'Error');
                });
            });
        }

        // Optimize route
        const opBtn = dayCard.querySelector('.optimize-route-btn');
        if(opBtn) {
            opBtn.addEventListener('click', function(e) {
                e.preventDefault();
                fetch('/optimize-route/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                    body: JSON.stringify({ day: dayName })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        alert('Optimized order: ' + data.optimized.map(i => i.name).join(', '));
                        window.location.reload();
                    } else alert(data.message || 'Error');
                });
            });
        }
    }

    // --- NAVIGATION TOGGLES ---
    document.querySelectorAll('.nav-item[data-section]').forEach(item => {
        item.addEventListener('click', function() {
            const target = document.getElementById(this.getAttribute('data-section'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('nav-item--active'));
            this.classList.add('nav-item--active');
        });
    });

    // --- MAP & DETAIL PANEL LOGIC ---
    function showMapLocation(location) {
        const iframe = document.querySelector('.map-pane__body iframe');
        if (iframe && location) {
            iframe.src = `https://maps.google.com/maps?output=embed&q=$${encodeURIComponent(location)}&z=16`;
        }
    }

    function showDetailPanel(dest, ratingStr) {
        const detailPanel = document.getElementById('destination-detail-panel');
        if (detailPanel) {
            document.getElementById('detail-title').textContent = dest.name;
            document.getElementById('detail-category').textContent = dest.category || '';
            document.getElementById('detail-rating').textContent = ratingStr ? `⭐ ${ratingStr}` : '';
            document.getElementById('detail-address').textContent = dest.address || '';
            document.getElementById('detail-image').style.backgroundImage = `url('${dest.image}')`;
            detailPanel.style.display = 'block';
        }
    }

    const closeDetailBtn = document.getElementById('close-detail-panel');
    if (closeDetailBtn) closeDetailBtn.addEventListener('click', () => {
        document.getElementById('destination-detail-panel').style.display = 'none';
    });

    // Handle clicks on saved explore-cards to show map
    document.querySelectorAll('.explore-card[data-location]').forEach(card => {
        card.addEventListener('click', function () {
            showMapLocation(card.dataset.location);
        });
    });

    // --- RESIZABLE PANES (Split Screen) ---
    const appShell = document.querySelector('.app-shell');
    const gutterLeft = document.getElementById('gutter-left');
    const gutterRight = document.getElementById('gutter-right');
    const sidebarEl = document.querySelector('.sidebar');
    const mapEl = document.querySelector('.map-pane');
    const mapIframe = document.querySelector('.map-pane iframe');

    if (appShell && gutterLeft && gutterRight && sidebarEl && mapEl) {
        let isResizingLeft = false, isResizingRight = false;

        function toggleIframePointer(enable) {
            if (mapIframe) mapIframe.style.pointerEvents = enable ? 'auto' : 'none';
        }

        gutterLeft.addEventListener('mousedown', (e) => {
            e.preventDefault(); isResizingLeft = true;
            gutterLeft.classList.add('active'); toggleIframePointer(false);
            document.body.style.cursor = 'col-resize';
        });

        gutterRight.addEventListener('mousedown', (e) => {
            e.preventDefault(); isResizingRight = true;
            gutterRight.classList.add('active'); toggleIframePointer(false);
            document.body.style.cursor = 'col-resize';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizingLeft && !isResizingRight) return;
            const currentSidebarWidth = sidebarEl.offsetWidth;
            const currentMapWidth = mapEl.offsetWidth;

            if (isResizingLeft) {
                let newLeftWidth = e.clientX;
                if (newLeftWidth < 200) newLeftWidth = 200;
                if (newLeftWidth > 600) newLeftWidth = 600;
                appShell.style.gridTemplateColumns = `${newLeftWidth}px 4px 1fr 4px ${currentMapWidth}px`;
            }
            if (isResizingRight) {
                let newRightWidth = window.innerWidth - e.clientX;
                if (newRightWidth < 200) newRightWidth = 200;
                if (newRightWidth > 900) newRightWidth = 900;
                appShell.style.gridTemplateColumns = `${currentSidebarWidth}px 4px 1fr 4px ${newRightWidth}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizingLeft || isResizingRight) {
                isResizingLeft = isResizingRight = false;
                gutterLeft.classList.remove('active');
                gutterRight.classList.remove('active');
                toggleIframePointer(true);
                document.body.style.cursor = '';
            }
        });
    }

    // --- TRIP SETTINGS & BUDGET ---
    initTripSettings();
    initBudgetLogic(contextData);
    initNoteModal();

    // --- INITIALIZATION ---
    generateDays();
    setTimeout(() => { loadItinerary(); }, 1000);

    // Setup remove buttons for saved items (AJAX)
    document.querySelectorAll('.remove-trip-item-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!confirm(btn.getAttribute('data-confirm-msg'))) return;
            
            const itemId = btn.getAttribute('data-item-id');
            fetch(`/${currentLang}/trip/remove/${itemId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const card = btn.closest('.explore-card');
                    if (card) {
                        card.style.opacity = '0';
                        setTimeout(() => card.remove(), 300);
                    }
                } else alert(data.message || 'Error');
            });
        });
    });

    // Add to Trip buttons (Explore section)
    document.querySelectorAll('.add-to-trip-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const destId = btn.getAttribute('data-destination-id');
            fetch(`/${currentLang}/destination/${destId}/add-trip/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) { alert(data.message); window.location.reload(); }
                else alert(data.message);
            });
        });
    });
});

// 3. MODULES: SETTINGS, BUDGET, NOTES, AI
// -----------------------------------------------------------------------------
function initTripSettings() {
    const modal = document.getElementById('settings-modal');
    const btn = document.getElementById('settings-btn');
    if (!modal || !btn) return;

    btn.addEventListener('click', () => modal.style.display = 'flex');
    document.getElementById('close-settings')?.addEventListener('click', () => modal.style.display = 'none');
    document.getElementById('cancel-settings')?.addEventListener('click', () => modal.style.display = 'none');

    // Travelers Counter
    const tInput = document.getElementById('travelers-count');
    const tDisplay = document.getElementById('travelers-display');
    document.getElementById('decrease-travelers')?.addEventListener('click', () => {
        if (tInput.value > 1) { tInput.value--; if(tDisplay) tDisplay.textContent = tInput.value; }
    });
    document.getElementById('increase-travelers')?.addEventListener('click', () => {
        if (tInput.value < 20) { tInput.value++; if(tDisplay) tDisplay.textContent = tInput.value; }
    });

    // Budget Slider
    const bSlider = document.getElementById('budget-slider');
    const bValue = document.getElementById('budget-value');
    if(bSlider) bSlider.addEventListener('input', () => bValue.textContent = bSlider.value);

    // Save Settings
    document.getElementById('save-settings')?.addEventListener('click', () => {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        const tripType = document.querySelector('input[name="trip-type"]:checked').value;
        
        fetch(`/${currentLang}/update-trip-settings/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrftoken },
            body: `start_date=${startDate}&end_date=${endDate}&travelers=${tInput.value}&budget=${bSlider.value}&trip_type=${tripType}`
        }).then(r => r.json()).then(data => {
            if(data.success) { modal.style.display = 'none'; window.location.reload(); }
        });
    });
}

function initBudgetLogic(contextData) {
    let expenses = [];
    const rawBudget = contextData.budget;
    const rawTravelers = contextData.travelers;

    const totalBudget = (Number(rawBudget.replace(/[^0-9.-]/g, '')) || 0) * 1000000;
    const travelers = Number(rawTravelers.replace(/[^0-9.-]/g, '')) || 1;

    function formatVND(amount) {
        return Math.round(amount).toLocaleString('en-US') + ' VND';
    }

    function updateBudgetDisplay() {
        const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0);
        const currentBudget = totalBudget + totalExpenses; 
        
        const bDisplay = document.getElementById('total-budget-display');
        if (bDisplay) bDisplay.textContent = formatVND(currentBudget).replace(' VND', '');
        
        const ppDisplay = document.getElementById('per-person-display');
        if (ppDisplay) ppDisplay.textContent = formatVND(currentBudget / travelers);
    }

    // Expense Modal
    const modal = document.getElementById('expense-modal');
    const addBtn = document.getElementById('add-expense-btn');
    const addOtherBtn = document.getElementById('add-other-expense-btn');
    
    function openModal() { if(modal) { modal.classList.add('show'); document.body.style.overflow = 'hidden'; }}
    function closeModal() { if(modal) { modal.classList.remove('show'); document.body.style.overflow = ''; }}

    if(addBtn) addBtn.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
    if(addOtherBtn) addOtherBtn.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
    document.getElementById('close-expense-modal')?.addEventListener('click', closeModal);

    // Categories
    let selectedCategory = null;
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedCategory = btn.dataset.category;
            const nameGroup = document.getElementById('expense-name-group');
            if(nameGroup) nameGroup.style.display = selectedCategory === 'other' ? 'flex' : 'none';
        });
    });

    const form = document.getElementById('expense-form');
    if(form) form.addEventListener('submit', (e) => {
        e.preventDefault();
        const amount = Number(document.getElementById('expense-amount').value);
        if(!selectedCategory) { alert('Please select a category'); return; }
        
        expenses.push({
            id: Date.now(),
            name: selectedCategory === 'other' ? document.getElementById('expense-name').value : selectedCategory,
            amount: amount,
            category: selectedCategory
        });
        
        renderExpenses();
        updateBudgetDisplay();
        closeModal();
        form.reset();
    });

    function renderExpenses() {
        const list = document.getElementById('expenses-list');
        if(!list) return;
        if(expenses.length === 0) { list.innerHTML = '<p style="text-align:center; padding:20px;">No expenses</p>'; return; }
        
        list.innerHTML = expenses.map(e => `
            <div class="expense-item">
                <div class="expense-item__left"><h4>${e.name}</h4></div>
                <div class="expense-item__amount">${formatVND(e.amount)}</div>
            </div>
        `).join('');
    }

    updateBudgetDisplay();
}

function initNoteModal() {
    const modal = document.getElementById('note-modal');
    const form = document.getElementById('note-form');
    
    if(!modal || !form) return;
    
    window.openNoteModal = function(placeCard) {
        if(!placeCard.id) placeCard.id = 'place-' + Date.now();
        modal.dataset.targetPlace = placeCard.id;
        document.getElementById('note-text').value = placeCard.dataset.note || '';
        modal.style.display = 'flex';
    };

    const close = () => modal.style.display = 'none';
    document.getElementById('close-note-modal')?.addEventListener('click', close);
    document.getElementById('cancel-note')?.addEventListener('click', close);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = document.getElementById('note-text').value.trim();
        const placeId = modal.dataset.targetPlace;
        const placeCard = document.getElementById(placeId);
        
        if(placeCard) {
            placeCard.dataset.note = text;
            const info = placeCard.querySelector('.place-card__info');
            let noteEl = placeCard.querySelector('.place-card__note');
            if(!noteEl) {
                noteEl = document.createElement('div');
                noteEl.classList.add('place-card__note');
                info.appendChild(noteEl);
            }
            noteEl.innerHTML = `<span style="color: #666;">📝 ${text}</span>`;

            const itemId = placeCard.dataset.itemId;
            if(itemId) await updateItineraryNote(itemId, text);
        }
        close();
    });
}

// Hàm UI: Toggle Chat
function toggleChat() {
    const panel = document.getElementById('ai-chat-panel');
    if (panel) {
        // Sử dụng getComputedStyle để lấy trạng thái hiển thị thực tế (kể cả khi ẩn bằng CSS class)
        const currentStyle = window.getComputedStyle(panel).display;
        
        if (currentStyle === 'none') {
            // Mở panel
            panel.style.display = 'flex';
            
            // CỰC KỲ QUAN TRỌNG: Set z-index cao để không bị bản đồ hoặc header che mất
            panel.style.zIndex = "10000"; 
            
            // Auto focus vào ô nhập liệu
            const input = document.getElementById('ai-user-input');
            if (input) input.focus();
        } else {
            // Đóng panel
            panel.style.display = 'none';
        }
    } else {
        console.error("Lỗi: Không tìm thấy phần tử có id='ai-chat-panel' trong HTML");
    }
}

// Hàm Logic: Gửi tin nhắn AI
async function sendAIMessage(){
    const input = document.getElementById('ai-user-input');
    const messages = document.getElementById('ai-chat-messages');
    const msg = input.value.trim();
    if (!msg) return;

    // 1. Hiển thị tin nhắn người dùng (UI Đẹp hơn)
    messages.innerHTML += `<div style="text-align: right; margin-bottom: 8px;">
        <span style="background: #fb8700; color: white; padding: 8px 12px; border-radius: 12px 12px 0 12px; display: inline-block;">${msg}</span>
    </div>`;
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    // 2. Hiển thị trạng thái "Typing..."
    const loadingId = 'ai-loading-' + Date.now();
    messages.innerHTML += `<div id="${loadingId}" style="margin-bottom: 8px;">
        <span style="background: #f0f0f0; color: #666; padding: 8px 12px; border-radius: 12px 12px 12px 0; display: inline-block; font-style: italic;">AI is typing...</span>
    </div>`;
    messages.scrollTop = messages.scrollHeight;

    // 3. Thu thập ngữ cảnh chuyến đi
    const destination = document.getElementById('trip-title')?.innerText.replace('Trip to', '').trim() || 'unknown';
    const travelers = document.getElementById('travelers-count')?.value || '1';
    const startDate = document.getElementById('start-date')?.value || '';
    const endDate = document.getElementById('end-date')?.value || '';
    const budget = document.getElementById('budget-slider')?.value || '0'; // Lấy budget từ thanh trượt

    // 4. Xác định ngôn ngữ và API URL
    const lang = window.location.pathname.split('/')[1] || 'en';
    // Đảm bảo URL hợp lệ (nếu lang là 'tripplanner' hoặc rỗng thì mặc định 'en')
    const safeLang = (lang.length === 2) ? lang : 'en';
    const apiUrl = `/${safeLang}/api/chat/`;

    try {
        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                message: msg,
                type: 'tripplanner', // Đánh dấu request từ Trip Planner
                destination: destination,
                travelers: travelers,
                budget: budget, // Gửi budget cho backend
                date_range: `${startDate} - ${endDate}`
            })
        });

        // Xóa dòng loading
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) loadingDiv.remove();

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        
        // 5. Hiển thị câu trả lời của AI
        const reply = data.reply || "I couldn't get a response.";
        messages.innerHTML += `<div style="text-align: left; margin-bottom: 8px;">
            <span style="background: #f0f0f0; color: #333; padding: 8px 12px; border-radius: 12px 12px 12px 0; display: inline-block;">${reply}</span>
        </div>`;

    } catch (err) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) loadingDiv.remove();
        
        messages.innerHTML += `
          <div style="color:red; font-size: 0.9em; margin-bottom: 8px;">
            <b>AI error:</b> ${err.message}
          </div>`;
    }
    messages.scrollTop = messages.scrollHeight;
}
