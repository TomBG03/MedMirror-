const express = require('express');
const app = express();
const port = 3001;

// Middleware to parse JSON bodies
app.use(express.json());


// Serve static files from the 'public' directory
app.use(express.static('public'));

// Example data
let medications = ['Medication 1', 'Medication 2'];
let calendarEvents = ['Event 1', 'Event 2'];
let todos = ['Todo 1', 'Todo 2'];

// Get medication reminders
app.get('/api/medications', (req, res) => {
    res.json(medications);
});

// Add a medication reminder
app.post('/api/medications', (req, res) => {
    const medication = req.body.medication;
    if (medication) {
        medications.push(medication);
        res.status(201).send();
    } else {
        res.status(400).send('Medication is required');
    }
});

// Get calendar events
app.get('/api/calendar', (req, res) => {
    res.json(calendarEvents);
});

// Add a calendar event
app.post('/api/calendar', (req, res) => {
    const event = req.body.event;
    if (event) {
        calendarEvents.push(event);
        res.status(201).send();
    } else {
        res.status(400).send('Event is required');
    }
});

// Get to-do items
app.get('/api/todos', (req, res) => {
    res.json(todos);
});

// Add a to-do item
app.post('/api/todos', (req, res) => {
    const todo = req.body.todo;
    if (todo) {
        todos.push(todo);
        res.status(201).send();
    } else {
        res.status(400).send('Todo is required');
    }
});

app.listen(port, () => {
    console.log(`Smart Mirror app listening at http://localhost:${port}`);
});
