
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
    selectedView.style.display = 'block'; // Show the selected view
}


// display all events for today in time order
//  EXAMPLE DO NOT USE 
function fetchEventsAndDisplay() {
    fetch('/api/events')
        .then(response => response.json())
        .then(events => {
            const container = document.getElementById('calendar-view');
            container.innerHTML = ''; // Clear existing events
            
            events.forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.classList.add('event');
                
                // Assuming 'start' and 'end' are ISO strings
                const startTime = new Date(event.start);
                const endTime = new Date(event.end);

                // Example: Position based on a day starting at 8 AM and ending at 5 PM
                const dayStart = 7;
                const dayEnd = 23;
                const hoursInDay = dayEnd - dayStart;

                // Calculate top and height based on event's start and end time
                const minutesFromDayStart = (startTime.getHours() - dayStart) * 60 + startTime.getMinutes();
                const eventDuration = (endTime - startTime) / (1000 * 60); // Duration in minutes

                const pixelsPerMinute = container.clientHeight / (hoursInDay * 60); // Convert container height to total day minutes

                eventElement.style.top = `${minutesFromDayStart * pixelsPerMinute}px`;
                eventElement.style.height = `${eventDuration * pixelsPerMinute}px`;

                eventElement.textContent = `${event.subject} (${startTime.toLocaleTimeString()} - ${endTime.toLocaleTimeString()})`;
                container.appendChild(eventElement);
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

    
let currentView = 'welcome-view';
// Call updateTime() function every minute to keep the time updated


fetchMedicationsAndUpdateView()
updateDateTime(); // Update time immediately when the page loads
checkAndUpdateViewState();
setInterval(`checkAndUpdateViewState`, 1_000);
setInterval(updateDateTime, 10_000);