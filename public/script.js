document.addEventListener('DOMContentLoaded', () => {
    const showMedicationsBtn = document.getElementById('show-medications');
    const showCalendarBtn = document.getElementById('show-calendar');
    const showTodosBtn = document.getElementById('show-todos');

    showMedicationsBtn.addEventListener('click', () => {
        switchView('medications-view');
        fetchMedicationsAndUpdateView(); // Fetch medications when the view is switched to
    });
    showCalendarBtn.addEventListener('click', () => switchView('calendar-view'));
    showTodosBtn.addEventListener('click', () => switchView('todos-view'));
});

function switchView(viewId) {
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.style.display = 'none'); // Hide all views

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'block'; // Show the selected view
}

function fetchMedicationsAndUpdateView() {
    fetch('/api/medications')
        .then(response => response.json())
        .then(medications => {
            const medicationsView = document.getElementById('medications-view');
            // Ensure there's a <ul> element for listing medications
            let list = medicationsView.querySelector('ul');
            if (!list) {
                list = document.createElement('ul');
                medicationsView.appendChild(list);
            }
            list.innerHTML = ''; // Clear existing list items

            medications.forEach(med => {
                // Create a container <li> for each medication
                const listItem = document.createElement('li');
                
                // Create a span to hold medication text
                const medText = document.createElement('span');
                medText.textContent = `${med.name} - ${med.dosage} - ${med.time}`;
                listItem.appendChild(medText);

                // Create and append the delete button
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.onclick = () => deleteMedication(med._id);
                listItem.appendChild(deleteBtn); // Append button to the listItem

                list.appendChild(listItem); // Append listItem to the list
            });
        })
        .catch(error => console.error('Error fetching medications:', error));
}

function deleteMedication(id) {
    fetch(`/api/medications/${id}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Refresh the medication list to reflect the deletion
            fetchMedicationsAndUpdateView();
        })
        .catch(error => console.error('Error deleting medication:', error));
}