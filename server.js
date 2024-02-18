require('dotenv').config();

const express = require('express');
const app = express();
const port = 3001;
const mongoose = require('mongoose');

// Replace 'myDatabase' with your database name or use your MongoDB Atlas connection string
mongoose.connect('mongodb://localhost/medMirror', { useNewUrlParser: true, useUnifiedTopology: true });
mongoose.connection.once('open', () => {
    console.log('Connected to MongoDB');
}).on('error', (error) => {
    console.log('Connection error:', error);
});



// Middleware to parse JSON bodies
app.use(express.json());

// Serve static files from the 'public' directory
app.use(express.static('public'));


app.listen(port, () => {
    console.log(`Smart Mirror app listening at http://localhost:${port}`);
});

// using mongo database to get medication 
const Medication = require('./Medication'); // Path to your Medication model

// Endpoint to get all medications
app.get('/api/medications', async (req, res) => {
    try {
        const medications = await Medication.find();
        res.json(medications);
    } catch (error) {
        res.status(500).send(error);
    }
});

// Endpoint to add a new medication
app.post('/api/medications', async (req, res) => {
    const newMedication = new Medication(req.body);

    try {
        const savedMedication = await newMedication.save();
        res.status(201).json(savedMedication);
        console.log('Medication added');
    } catch (error) {
        res.status(400).send(error);
    }
});

// DELETE endpoint to remove a medication by its _id
app.delete('/api/medications/:id', async (req, res) => {
    try {
        const result = await Medication.findByIdAndDelete(req.params.id);
        if (result) {
            res.send({ message: "Medication deleted successfully" });
        } else {
            res.status(404).send({ message: "Medication not found" });
        }
    } catch (error) {
        res.status(500).send(error);
    }
});


const CalendarEvent = require('./calendarEvent'); // Import the model
app.get('/api/calendar', async (req, res) => {
    try {
        const events = await CalendarEvent.find();
        res.json(events);
    } catch (error) {
        res.status(500).send(error);
    }
});

app.post('/api/calendar', async (req, res) => {
    const event = new CalendarEvent(req.body);
    try {
        const savedEvent = await event.save();
        res.status(201).json(savedEvent);
        console.log('Event added')
    } catch (error) {
        res.status(400).send(error);
    }
});

app.delete('/api/calendar/:id', async (req, res) => {
    try {
        const result = await CalendarEvent.findByIdAndDelete(req.params.id);
        if (result) {
            res.send({ message: "Calendar event deleted successfully" });
        } else {
            res.status(404).send({ message: "Calendar event not found" });
        }
    } catch (error) {
        res.status(500).send(error);
    }
});

