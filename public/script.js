document.addEventListener('DOMContentLoaded', () => {
    const showMedicationsBtn = document.getElementById('show-medications');
    const showCalendarBtn = document.getElementById('show-calendar');
    const showTodosBtn = document.getElementById('show-todos');

    showMedicationsBtn.addEventListener('click', () => switchView('medications-view'));
    showCalendarBtn.addEventListener('click', () => switchView('calendar-view'));
    showTodosBtn.addEventListener('click', () => switchView('todos-view'));
    
    populateMedications();
    populateCalendar();
    populateTodos();
});

function populateMedications() {
    const meds = ['Medication 1', 'Medication 2', 'Medication 3']; // Example data
    const list = document.getElementById('medication-list');
    meds.forEach(med => {
        const item = document.createElement('li');
        item.textContent = med;
        list.appendChild(item);
    });
}

function populateCalendar() {
    const events = ['Event 1', 'Event 2', 'Event 3']; // Example data
    const list = document.getElementById('calendar-events');
    events.forEach(event => {
        const item = document.createElement('li');
        item.textContent = event;
        list.appendChild(item);
    });
}

function populateTodos() {
    const todos = ['Todo 1', 'Todo 2', 'Todo 3']; // Example data
    const list = document.getElementById('todos');
    todos.forEach(todo => {
        const item = document.createElement('li');
        item.textContent = todo;
        list.appendChild(item);
    });
}

function switchView(viewId) {
    const views = document.querySelectorAll('.view');
    views.forEach(view => {
        view.style.display = 'none'; // Hide all views
    });

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'block'; // Show the selected view
}