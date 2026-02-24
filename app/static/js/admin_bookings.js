// Admin Bookings Management
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

const authHeaders = {
    'Authorization': `Bearer ${token}`
};

let allBookings = [];
let allMachines = [];
let currentDeleteId = null;
let deleteModal = null;

const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
        headers: {
            ...authHeaders,
            ...(options.headers || {})
        },
        ...options
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
};

const loadMachines = async () => {
    try {
        allMachines = await fetchJson('/admin-api/machines');
        const select = document.getElementById('filter-machine');
        allMachines.forEach(machine => {
            const option = document.createElement('option');
            option.value = machine.id;
            option.textContent = machine.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Помилка завантаження машин:', error);
    }
};

const loadBookings = async () => {
    try {
        allBookings = await fetchJson('/admin-api/bookings?limit=500');
        applyFilters();
    } catch (error) {
        console.error('Помилка завантаження бронювань:', error);
        showToast('Помилка завантаження бронювань', 'danger');
    }
};

const applyFilters = () => {
    const selectedDate = document.getElementById('filter-date').value;
    const selectedMachine = document.getElementById('filter-machine').value;

    let filtered = allBookings;

    if (selectedDate) {
        filtered = filtered.filter(booking => booking.date === selectedDate);
    }

    if (selectedMachine) {
        filtered = filtered.filter(booking => booking.machine_id === Number(selectedMachine));
    }

    renderBookings(filtered);
};

const renderBookings = (bookings) => {
    const table = document.getElementById('bookings-table');
    table.innerHTML = '';

    if (bookings.length === 0) {
        table.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Бронювань не знайдено</td></tr>';
        return;
    }

    bookings.forEach((booking) => {
        const row = document.createElement('tr');
        const machineObj = allMachines.find(m => m.id === booking.machine_id);
        const machineName = machineObj ? machineObj.name : `Машина #${booking.machine_id}`;
        
        const bookingDate = new Date(booking.date);
        const formattedDate = bookingDate.toLocaleDateString('uk-UA', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit' 
        });

        // Create user cell with telegram link if available
        let userCell = booking.user_full_name || 'N/A';
        if (booking.user_telegram_id) {
            userCell = `<a href="tg://user?id=${booking.user_telegram_id}" class="text-decoration-none">${booking.user_full_name}</a>`;
        }

        row.innerHTML = `
            <td>${booking.id}</td>
            <td>${userCell}</td>
            <td>${machineName}</td>
            <td>${formattedDate}</td>
            <td><span class="badge text-bg-info">${booking.time_slot}</span></td>
            <td>${new Date(booking.created_at).toLocaleString('uk-UA')}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" data-delete-booking="${booking.id}">Видалити</button>
            </td>
        `;
        table.appendChild(row);
    });
};

const openDeleteModal = (bookingId) => {
    currentDeleteId = bookingId;
    if (!deleteModal) {
        deleteModal = new bootstrap.Modal(document.getElementById('delete-modal'));
    }
    deleteModal.show();
};

const confirmDelete = async () => {
    if (!currentDeleteId) return;

    try {
        await fetchJson(`/admin-api/bookings/${currentDeleteId}`, {
            method: 'DELETE'
        });

        deleteModal.hide();
        await loadBookings();
        showToast('Бронювання видалено', 'success');
    } catch (error) {
        console.error('Помилка:', error);
        showToast(`Помилка: ${error.message}`, 'danger');
    }
};

document.getElementById('confirm-delete-btn').addEventListener('click', confirmDelete);

document.getElementById('bookings-table').addEventListener('click', (event) => {
    const deleteBtn = event.target.closest('[data-delete-booking]');
    if (deleteBtn) {
        const bookingId = Number(deleteBtn.getAttribute('data-delete-booking'));
        openDeleteModal(bookingId);
    }
});

document.getElementById('filter-date').addEventListener('change', applyFilters);
document.getElementById('filter-machine').addEventListener('change', applyFilters);
document.getElementById('refresh-btn').addEventListener('click', loadBookings);

Promise.all([loadMachines(), loadBookings()]).catch(console.error);
