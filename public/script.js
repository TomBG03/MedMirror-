document.addEventListener('DOMContentLoaded', () => {
    setupViewButtons();
    //setupSpeechRecognition();
});

function setupViewButtons() {
    const showWelcomeBtn = document.getElementById('show-welcome');
    const showDefaultBtn = document.getElementById('show-mirror');
    const showMedicationsBtn = document.getElementById('show-medications');
    const showCalendarBtn = document.getElementById('show-calendar');
    const showTodosBtn = document.getElementById('show-todos');

    showMedicationsBtn.addEventListener('click', () => {
        fetchMedicationsAndUpdateView(); // Fetch medications when the view is switched to
        switchView('medications-view');
         
    });
    showCalendarBtn.addEventListener('click', () => {
        generateCalendar(); // Generate the calendar when the view is switched to
        switchView('calendar-view');
        
    });
    
    showWelcomeBtn.addEventListener('click', () => switchView('welcome-view'));
    showDefaultBtn.addEventListener('click', () => switchView('mirror-view'));
    showTodosBtn.addEventListener('click', () => switchView('todos-view'));
}


// VIEW FUNCTIONS
function switchView(viewId) {
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.style.display = 'none'); // Hide all views

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'block'; // Show the selected view
}


// display all events for today in time order
//  EXAMPLE DO NOT USE 
function fetchEventsAndUpdateView(){
    fetch('/api/events').then(response => response.json()).then(events => {
        const dayStart = 7 * 60; // Day starts at 8 AM, for example
        const scale = 1; // 1 minute = 1 pixel, adjust as needed
        const container = document.getElementById('day-container');
        events.forEach(event => {
            const eventDiv = document.createElement('div');
            eventDiv.classList.add('event');
            const startMinutes = event.startHour * 60 + event.startMinute - dayStart;
            const duration = (event.endHour * 60 + event.endMinute) - (event.startHour * 60 + event.startMinute);
            eventDiv.style.top = `${startMinutes * scale}px`;
            eventDiv.style.height = `${duration * scale}px`;
            // Add more styling as needed
            container.appendChild(eventDiv);
        });
    });
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
                // const deleteBtn = document.createElement('button');
                // deleteBtn.textContent = 'Delete';
                // deleteBtn.onclick = () => deleteMedication(med._id);
                // listItem.appendChild(deleteBtn); // Append button to the listItem

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

function generateCalendar() {

    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    const dateString = firstDayOfMonth.toLocaleDateString('en-us', {
        weekday: 'long',
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
    });
    const paddingDays = weekdays.indexOf(dateString.split(', ')[0]);

    const totalSquares = Math.ceil((paddingDays + daysInMonth) / 7) * 7; // Total cells to fill a complete grid

    document.querySelector(".calendar-body").innerHTML = '';
    
    for(let i = 1; i <= totalSquares; i++) {
        const daySquare = document.createElement("div");
        daySquare.classList.add("day");
        
        if (i > paddingDays && i <= paddingDays + daysInMonth) {
            // Current month's days
            daySquare.innerText = i - paddingDays;
            daySquare.addEventListener('click', () => console.log(`${currentMonth + 1}/${i - paddingDays}/${currentYear}`));
        } else if (i > paddingDays + daysInMonth) {
            // Next month's days
            daySquare.innerText = i - (paddingDays + daysInMonth);
            daySquare.classList.add("next-month");
            // Optionally add a different event listener or styling for next month's days
        } else {
            // Preceding month's padding days
            daySquare.classList.add("padding");
        }

        document.querySelector(".calendar-body").appendChild(daySquare);    
    }
}

const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// Get the current view state and update view accordingly 
function checkAndUpdateViewState() {
    fetch('/api/view')
        .then(response => response.json())
        .then(data => {
            if (data.currentView && data.currentView !== currentView) {
                switchView(data.currentView);
                console.log(currentView);
                
                currentView = data.currentView; // Update the currentView variable
            }
        })
        .catch(error => console.error('Error fetching view state:', error));
}


function updateDateTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    hours = hours.toString().padStart(2, '0');
    minutes = minutes.toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}`;

    // Format the date to include the month name
    const options = { month: 'long', day: 'numeric', year: 'numeric' };
    const dateString = now.toLocaleDateString('en-US', options);

    document.getElementById('time-display').textContent = timeString;
    document.getElementById('date-display').textContent = dateString;
    
}

    
let currentView = 'welcome-view';
// Call updateTime() function every minute to keep the time updated


// fetchMedicationsAndUpdateView()
updateDateTime(); // Update time immediately when the page loads
checkAndUpdateViewState();
setInterval(checkAndUpdateViewState, 1_000);
setInterval(updateDateTime, 10_000);