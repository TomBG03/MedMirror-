document.addEventListener('DOMContentLoaded', () => {
    setupViewButtons();
    //setupSpeechRecognition();
});

function setupViewButtons() {
    const showMedicationsBtn = document.getElementById('show-medications');
    const showCalendarBtn = document.getElementById('show-calendar');
    const showTodosBtn = document.getElementById('show-todos');

    showMedicationsBtn.addEventListener('click', () => {
        switchView('medications-view');
        fetchMedicationsAndUpdateView(); // Fetch medications when the view is switched to
    });
    showCalendarBtn.addEventListener('click', () => switchView('calendar-view'));
    showTodosBtn.addEventListener('click', () => switchView('todos-view'));
}


// SPEECH RECOGNITION FUNCTIONS
// DELETE IS REMOVE SPEECH RECOGNITION FROM WEBPAGE
function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    
    recognition.onstart = () => {
        console.log('Voice recognition activated. Start speaking.');
    };

    recognition.onresult = (event) => {
        const last = event.results.length - 1;
        const text = event.results[last][0].transcript.trim().toLowerCase();
        console.log("Recognized text:", text);

        if (text.includes("love")) {
            console.log("Keyword 'love' recognized.");
            keywordAction();
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
    };

    recognition.start();
}

function keywordAction() {
    console.log('Performing keyword action');
    switchView('calendar-view');
}


// VIEW FUNCTIONS
function switchView(viewId) {
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.style.display = 'none'); // Hide all views

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'block'; // Show the selected view
}

// MEDICATION FUNCTIONS

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


function updateTime() {
    const now = new Date(); // Get the current time
    let hours = now.getHours(); // Get hours from the current time
    let minutes = now.getMinutes(); // Get minutes from the current time

    // Format hours and minutes to ensure two digits
    hours = hours.toString().padStart(2, '0');
    minutes = minutes.toString().padStart(2, '0');

    // Combine hours and minutes in hh:mm format
    const timeString = `${hours}:${minutes}`;

    // Update the div with id='time-display' with the current time
    document.getElementById('time-display').textContent = timeString;
}

// Call updateTime() function every minute to keep the time updated
updateTime(); // Update time immediately when the page loads
setInterval(updateTime, 60000); // Then update it every 60 seconds