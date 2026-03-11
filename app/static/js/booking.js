const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

const authHeaders = { 'Authorization': `Bearer ${token}` };

// Helper function to safely parse JSON responses
async function safeJsonParse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        return null;
    }

    try {
        return await response.json();
    } catch (e) {
        console.error('JSON parse error:', e);
        return null;
    }
}

async function getErrorMessage(response, fallbackMessage) {
    const data = await safeJsonParse(response.clone());
    if (data && data.detail) {
        return data.detail;
    }

    const text = await response.text();
    if (text) {
        return text;
    }

    return fallbackMessage;
}

// Time slots mapping
const TIME_SLOTS = ['7:00-9:30', '10:00-12:30', '13:00-15:30', '16:00-18:30', '19:00-21:30'];

// State
let currentDate = new Date();
let selectedDate = new Date();
selectedDate.setHours(12, 0, 0, 0); // Set to noon to avoid timezone issues
let machines = [];
let myBookings = [];

// Calendar functions
function updateScheduleDate() {
    const dateEl = document.getElementById('schedule-date');
    if (dateEl) {
        const day = String(selectedDate.getDate()).padStart(2, '0');
        const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
        const year = selectedDate.getFullYear();
        dateEl.textContent = `(${day}.${month}.${year})`;
    }
}

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const monthNames = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                       'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];
    document.getElementById('current-month').textContent = `${monthNames[month]} ${year}`;
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const prevLastDay = new Date(year, month, 0);
    
    const firstDayWeek = (firstDay.getDay() + 6) % 7; // Monday = 0
    const lastDate = lastDay.getDate();
    const prevLastDate = prevLastDay.getDate();
    
    const calendarDays = document.getElementById('calendar-days');
    calendarDays.innerHTML = '';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Previous month days
    for (let i = firstDayWeek - 1; i >= 0; i--) {
        const day = prevLastDate - i;
        const dayEl = createDayElement(day, true, null, true);
        calendarDays.appendChild(dayEl);
    }
    
    // Current month days
    for (let day = 1; day <= lastDate; day++) {
        const date = new Date(year, month, day);
        date.setHours(0, 0, 0, 0);
        const isDisabled = date < today;
        const isToday = date.getTime() === today.getTime();
        
        // Normalize selectedDate for comparison
        const selectedDateNormalized = new Date(selectedDate);
        selectedDateNormalized.setHours(0, 0, 0, 0);
        const isSelected = date.getTime() === selectedDateNormalized.getTime();
        
        const dayEl = createDayElement(day, false, date, isDisabled, isToday, isSelected);
        calendarDays.appendChild(dayEl);
    }
    
    // Next month days
    const remainingDays = 42 - (firstDayWeek + lastDate);
    for (let day = 1; day <= remainingDays; day++) {
        const dayEl = createDayElement(day, true, null, true);
        calendarDays.appendChild(dayEl);
    }
}

function createDayElement(day, otherMonth, date, disabled = false, today = false, selected = false) {
    const dayEl = document.createElement('div');
    dayEl.className = 'calendar-day';
    dayEl.textContent = day;
    
    if (otherMonth) dayEl.classList.add('other-month');
    if (disabled) dayEl.classList.add('disabled');
    if (today) dayEl.classList.add('today');
    if (selected) dayEl.classList.add('selected');
    
    if (!disabled && !otherMonth && date) {
        dayEl.addEventListener('click', () => {
            selectedDate = new Date(date);
            selectedDate.setHours(12, 0, 0, 0); // Set to noon to avoid timezone issues
            renderCalendar();
            updateScheduleDate();
            loadSchedule();
        });
    }
    
    return dayEl;
}

document.getElementById('prev-month').addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
});

document.getElementById('next-month').addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
});

// Load machines
async function loadMachines() {
    try {
        const response = await fetch('/machines/', { headers: authHeaders });
        if (!response.ok) throw new Error('Не вдалося завантажити машини');
        machines = await safeJsonParse(response) || [];
        
        if (machines.length === 0) {
            document.getElementById('loading').classList.add('d-none');
            document.getElementById('no-machines').classList.remove('d-none');
            return;
        }
        
        loadSchedule();
    } catch (error) {
        showToast('Помилка завантаження машин', 'danger');
        document.getElementById('loading').classList.add('d-none');
    }
}

// Load my bookings
async function loadMyBookings() {
    try {
        const response = await fetch('/bookings/my', { headers: authHeaders });
        if (!response.ok) throw new Error('Не вдалося завантажити бронювання');
        myBookings = await safeJsonParse(response) || [];
    } catch (error) {
        console.error('Error loading bookings:', error);
        myBookings = [];
    }
}

// Load schedule for all machines
async function loadSchedule() {
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('schedule-container').classList.add('d-none');
    
    await loadMyBookings();
    
    // Format date correctly to avoid timezone issues
    const year = selectedDate.getFullYear();
    const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
    const day = String(selectedDate.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    const scheduleBody = document.getElementById('schedule-body');
    scheduleBody.innerHTML = '';
    
    for (const machine of machines) {
        try {
            const response = await fetch(
                `/machines/${machine.id}/schedule?target_date=${dateStr}`,
                { headers: authHeaders }
            );
            
            if (!response.ok) continue;
            
            const schedule = await safeJsonParse(response);
            if (!schedule || !Array.isArray(schedule)) continue;
            
            const row = document.createElement('tr');
            
            // Machine name cell
            const nameCell = document.createElement('td');
            nameCell.className = 'machine-name';
            nameCell.textContent = machine.name;
            row.appendChild(nameCell);
            
            // Slot cells
            TIME_SLOTS.forEach(slot => {
                const cell = document.createElement('td');
                cell.setAttribute('data-time-slot', slot);
                const slotData = schedule.find(s => s.time_slot === slot);
                
                if (slotData) {
                    const myBooking = myBookings.find(b => 
                        b.machine_id === machine.id && 
                        b.date === dateStr && 
                        b.time_slot === slot
                    );
                    
                    const button = document.createElement('button');
                    button.className = 'slot-btn';
                    
                    if (myBooking) {
                        button.classList.add('my-booking');
                        button.innerHTML = '<i class="fas fa-check"></i> Заброньовано';
                        button.onclick = () => cancelBooking(myBooking.id);
                    } else if (slotData.status === 'free') {
                        button.classList.add('free');
                        button.textContent = 'Забронювати';
                        button.onclick = () => bookSlot(machine.id, dateStr, slot);
                    } else {
                        button.classList.add('booked');
                        button.textContent = 'Зайнято';
                        button.disabled = true;
                    }
                    
                    cell.appendChild(button);
                } else {
                    // Hide empty slots on mobile
                    cell.classList.add('empty-slot');
                    cell.textContent = '-';
                }
                
                row.appendChild(cell);
            });
            
            scheduleBody.appendChild(row);
        } catch (error) {
            console.error(`Error loading schedule for machine ${machine.id}:`, error);
        }
    }
    
    document.getElementById('loading').classList.add('d-none');
    document.getElementById('schedule-container').classList.remove('d-none');
}

// Book slot
async function bookSlot(machineId, date, timeSlot) {
    try {
        const response = await fetch('/bookings/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                machine_id: machineId,
                date: date,
                time_slot: timeSlot
            })
        });
        
        if (!response.ok) {
            const errorMessage = await getErrorMessage(response, 'Не вдалося створити бронювання');
            throw new Error(errorMessage);
        }
        
        showToast(`Слот ${timeSlot} успішно заброньовано!`, 'success');
        loadSchedule();
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

// Cancel booking
let pendingCancellationId = null;

function cancelBooking(bookingId) {
    pendingCancellationId = bookingId;
    const modal = new bootstrap.Modal(document.getElementById('cancelBookingModal'));
    modal.show();
}

async function confirmCancelBooking() {
    if (!pendingCancellationId) return;
    
    const bookingId = pendingCancellationId;
    pendingCancellationId = null;
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('cancelBookingModal'));
    if (modal) {
        modal.hide();
    }
    
    try {
        const response = await fetch(`/bookings/${bookingId}`, {
            method: 'DELETE',
            headers: authHeaders
        });
        
        if (!response.ok) {
            throw new Error('Не вдалося скасувати бронювання');
        }
        
        showToast('Бронювання успішно скасовано', 'success');
        loadSchedule();
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    renderCalendar();
    updateScheduleDate();
    loadMachines();
    
    // Set up cancel booking confirmation handler
    const confirmCancelBtn = document.getElementById('confirmCancelBtn');
    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', confirmCancelBooking);
    }
});
