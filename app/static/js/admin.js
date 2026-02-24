// Admin Dashboard
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

const authHeaders = {
    'Authorization': `Bearer ${token}`
};

let machineModal = null;

const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
        headers: {
            ...authHeaders,
            ...(options.headers || {})
        },
        ...options
    });
    if (!response.ok) {
        throw new Error('Помилка запиту');
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
};

const loadStats = async () => {
    const stats = await fetchJson('/admin-api/stats');
    document.getElementById('stat-users').textContent = stats.users;
    document.getElementById('stat-machines').textContent = stats.machines;
    document.getElementById('stat-active').textContent = stats.active_machines;
    document.getElementById('stat-bookings').textContent = stats.today_bookings;
};

const renderMachines = (machines) => {
    const table = document.getElementById('machines-table');
    table.innerHTML = '';
    machines.forEach((machine) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${machine.id}</td>
            <td><input class="form-control form-control-sm" value="${machine.name}" data-machine-name="${machine.id}"></td>
            <td>
                <input type="checkbox" class="form-check-input" ${machine.is_active ? 'checked' : ''} data-machine-active="${machine.id}">
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" data-save-machine="${machine.id}">Зберегти</button>
                <button class="btn btn-sm btn-outline-danger" data-delete-machine="${machine.id}">Видалити</button>
            </td>
        `;
        table.appendChild(row);
    });
};

const loadMachines = async () => {
    const machines = await fetchJson('/admin-api/machines');
    renderMachines(machines);
};

const loadUsers = async () => {
    const users = await fetchJson('/admin-api/users');
    const table = document.getElementById('users-table');
    table.innerHTML = '';
    users.forEach((user) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.full_name}</td>
            <td>${user.washes_left}</td>
            <td>${user.washes_used_this_month}</td>
            <td>${user.is_admin ? 'Так' : 'Ні'}</td>
            <td>
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control" placeholder="+/-" data-user-delta="${user.id}">
                    <button class="btn btn-outline-secondary" data-user-apply="${user.id}">Застосувати</button>
                </div>
            </td>
        `;
        table.appendChild(row);
    });
};

const loadBookings = async () => {
    const today = new Date().toISOString().split('T')[0];
    const bookings = await fetchJson(`/admin-api/bookings?date_filter=${today}`);
    const table = document.getElementById('bookings-table');
    table.innerHTML = '';
    
    if (bookings.length === 0) {
        table.innerHTML = '<tr><td colspan="6" class="text-center py-3 text-muted">Немає бронювань на сьогодні</td></tr>';
        return;
    }
    
    bookings.forEach((booking) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${booking.id}</td>
            <td>${booking.user_full_name || 'N/A'}</td>
            <td>${booking.machine_id}</td>
            <td>${booking.date}</td>
            <td>${booking.time_slot}</td>
            <td>${booking.created_at}</td>
        `;
        table.appendChild(row);
    });
};

document.getElementById('add-machine-btn').addEventListener('click', () => {
    if (!machineModal) {
        machineModal = new bootstrap.Modal(document.getElementById('machine-modal'));
    }
    document.getElementById('machine-name').value = '';
    document.getElementById('machine-active').checked = true;
    document.getElementById('machine-modal-error').classList.add('d-none');
    machineModal.show();
});

document.getElementById('save-machine').addEventListener('click', async () => {
    const name = document.getElementById('machine-name').value.trim();
    const isActive = document.getElementById('machine-active').checked;
    const errorBox = document.getElementById('machine-modal-error');

    if (!name) {
        errorBox.textContent = 'Вкажіть назву машинки.';
        errorBox.classList.remove('d-none');
        return;
    }

    errorBox.classList.add('d-none');
    await fetchJson('/admin-api/machines', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, is_active: isActive })
    });

    machineModal.hide();
    await loadMachines();
    await loadStats();
});

document.getElementById('machines-table').addEventListener('click', async (event) => {
    const target = event.target;
    const machineId = target.getAttribute('data-save-machine') || target.getAttribute('data-delete-machine');
    if (!machineId) {
        return;
    }

    if (target.hasAttribute('data-save-machine')) {
        const nameInput = document.querySelector(`[data-machine-name="${machineId}"]`);
        const activeInput = document.querySelector(`[data-machine-active="${machineId}"]`);
        await fetchJson(`/admin-api/machines/${machineId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: nameInput.value.trim(),
                is_active: activeInput.checked
            })
        });
        await loadMachines();
        await loadStats();
    }

    if (target.hasAttribute('data-delete-machine')) {
        await fetchJson(`/admin-api/machines/${machineId}`, {
            method: 'DELETE'
        });
        await loadMachines();
        await loadStats();
    }
});

document.getElementById('users-table').addEventListener('click', async (event) => {
    const target = event.target;
    const userId = target.getAttribute('data-user-apply');
    if (!userId) {
        return;
    }

    const deltaInput = document.querySelector(`[data-user-delta="${userId}"]`);
    const deltaValue = Number(deltaInput.value);
    if (Number.isNaN(deltaValue) || deltaValue === 0) {
        return;
    }

    await fetchJson(`/admin-api/users/${userId}/adjust-washes?delta=${deltaValue}`, {
        method: 'POST'
    });
    deltaInput.value = '';
    await loadUsers();
    await loadStats();
});

Promise.all([loadStats(), loadMachines(), loadUsers(), loadBookings()]).catch((error) => {
    console.error(error);
});
// Debug: Load scheduler jobs
async function loadSchedulerJobs() {
    try {
        const data = await fetchJson('/admin-api/scheduler/jobs');
        
        const infoDiv = document.getElementById('scheduler-info');
        const table = document.getElementById('scheduler-jobs-table');
        
        if (data.status === 'error') {
            infoDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            table.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Scheduler не ініціалізований</td></tr>';
            return;
        }
        
        infoDiv.innerHTML = `
            <div class="alert alert-info mb-0">
                <strong>Status:</strong> ${data.scheduler_running ? '✅ Running' : '❌ Stopped'} | 
                <strong>Total Jobs:</strong> ${data.total_jobs}
            </div>
        `;
        
        if (data.jobs.length === 0) {
            table.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Немає запланованих завдань</td></tr>';
            return;
        }
        
        table.innerHTML = '';
        data.jobs.forEach(job => {
            const row = document.createElement('tr');
            const nextRun = job.next_run_time ? new Date(job.next_run_time).toLocaleString('uk-UA') : 'N/A';
            
            row.innerHTML = `
                <td><code class="small">${job.id}</code></td>
                <td><small>${job.func}</small></td>
                <td>${nextRun}</td>
                <td><small>${job.args}</small></td>
            `;
            table.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading scheduler jobs:', error);
        document.getElementById('scheduler-info').innerHTML = 
            `<div class="alert alert-danger">Помилка завантаження: ${error.message}</div>`;
    }
}

// Load scheduler jobs on page load
loadSchedulerJobs();