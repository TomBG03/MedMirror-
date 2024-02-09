// script.js
document.addEventListener('DOMContentLoaded', () => {
    const showMedicationsBtn = document.getElementById('show-medications');
    const showCalendarBtn = document.getElementById('show-calendar');
    const showTodosBtn = document.getElementById('show-todos');

    showMedicationsBtn.addEventListener('click', () => switchView('medications-view'));
    showCalendarBtn.addEventListener('click', () => switchView('calendar-view'));
    showTodosBtn.addEventListener('click', () => switchView('todos-view'));
});

function switchView(viewId) {
    const views = document.querySelectorAll('.view');
    views.forEach(view => {
        view.style.display = 'none'; // Hide all views
    });

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'block'; // Show the selected view
}
