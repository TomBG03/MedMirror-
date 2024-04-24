
// VIEW FUNCTIONS
function switchView(viewId) {
    if (viewId == 'medications-view') {
        fetchMedicationsAndUpdateView();
    }
    if (viewId == 'calendar-view') {
        fetchEventsAndDisplay();
    }
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.style.display = 'none'); // Hide all views

    const selectedView = document.getElementById(viewId);
    selectedView.style.display = 'flex'; // Show the selected view
}


// display all events for today in time order
//  EXAMPLE DO NOT USE 
function fetchEventsAndDisplay() {
    fetch('/api/events')
        .then(response => response.json())
        .then(events => {
            const calendarView = document.getElementById('calendar-view');
            const timeColumn = calendarView.querySelector('.time-column');
            const eventsContainer = calendarView.querySelector('.events-container');

            // Clear previous content
            timeColumn.innerHTML = '';
            eventsContainer.innerHTML = '';

            // Generate time slots from 7 AM to 11 PM
            for (let hour = 7; hour <= 23; hour++) {
                const timeSlot = document.createElement('div');
                timeSlot.classList.add('time-slot');
                timeSlot.textContent = `${String(hour).padStart(2, '0')}:00`;
                timeColumn.appendChild(timeSlot);
            }

            // Assuming each time slot is 1 hour and the container's full height represents the hours from 7 AM to 11 PM (16 hours)
            const hourHeight = eventsContainer.clientHeight / 17; // 16 hours plus 7 AM slot

            // Sort events by start time
            events.sort((a, b) => new Date(a.start) - new Date(b.start));

            // Display events
            events.forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.classList.add('event');
                const startTime = new Date(event.start);
                const endTime = new Date(event.end);

                // Check if event start or end time is within the schedule hours (7 AM to 11 PM)
                const startHour = startTime.getHours() + startTime.getMinutes() / 60;
                const endHour = endTime.getHours() + endTime.getMinutes() / 60;

                if (startHour >= 7 && endHour <= 23) {
                    const positionStart = startHour - 7; // Shift position to start at 7 AM
                    const positionEnd = endHour <= 23 ? endHour - 7 : 16; // Do not go beyond 11 PM

                    // Calculate event position and height
                    eventElement.style.top = `${positionStart * hourHeight}px`;
                    eventElement.style.height = `${(positionEnd - positionStart) * hourHeight}px`;
                    eventElement.textContent = `${event.subject} (${startTime.toLocaleTimeString()} - ${endTime.toLocaleTimeString()})`;

                    // Append event to the events container
                    eventsContainer.appendChild(eventElement);
                }
            });
        })
        .catch(error => console.error('Error fetching events:', error));
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

switchView('welcome-view');   
let currentView = 'welcome-view';
// Call updateTime() function every minute to keep the time updated


fetchMedicationsAndUpdateView()
updateDateTime(); // Update time immediately when the page loads
checkAndUpdateViewState();
setInterval(checkAndUpdateViewState, 1_000);
setInterval(updateDateTime, 1_000);