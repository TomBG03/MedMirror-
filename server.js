require('dotenv').config();
import { Client } from '@microsoft/microsoft-graph-client';
import 'isomorphic-fetch';
const apiKey = process.env.OPENAI_API_KEY;
const client_id = process.env.CLIENT_ID;
const tenant_id = process.env.TENANT_ID;
const client_secret = process.env.CLIENT_SECRET;


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



const client = Client.init({
    authProvider: (done) => {
        // Get the token from your authentication mechanism
        const token = 'YOUR_ACCESS_TOKEN';
        done(null, token); // First parameter takes an error if you can't get an access token
    },
});


async function getCalendarEvents() {
    try {
        let events = await client
            .api('/me/events')
            .select('subject,start,end,location')
            .orderby('createdDateTime DESC')
            .get();

        console.log(events);
        return events;
    } catch (error) {
        console.error(error);
    }
}


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
        console.log('New Medication added');
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
const outlook = require('node-outlook');
const moment = require('moment');

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


// Fetch calendar events
app.get('/api/calendar', async (req, res) => {
  try {
    const accessToken = req.headers.authorization;
    const events = await outlook.calendar.getEvents({ token: accessToken });
    res.json(events);
  } catch (error) {
    res.status(500).send(error);
  }
});

// Create a new calendar event
app.post('/api/calendar', async (req, res) => {
  try {
    const accessToken = req.headers.authorization;
    const event = req.body;

    // Set start and end time using moment.js
    event.start = moment(event.start).toISOString();
    event.end = moment(event.end).toISOString();

    const createdEvent = await outlook.calendar.createEvent({ token: accessToken, event });
    res.status(201).json(createdEvent);
  } catch (error) {
    res.status(400).send(error);
  }
});

// Update a calendar event
app.put('/api/calendar/:id', async (req, res) => {
  try {
    const accessToken = req.headers.authorization;
    const eventId = req.params.id;
    const updatedEvent = req.body;

    // Set start and end time using moment.js
    updatedEvent.start = moment(updatedEvent.start).toISOString();
    updatedEvent.end = moment(updatedEvent.end).toISOString();

    const result = await outlook.calendar.updateEvent({ token: accessToken, eventId, updatedEvent });
    if (result) {
      res.send({ message: "Calendar event updated successfully" });
    } else {
      res.status(404).send({ message: "Calendar event not found" });
    }
  } catch (error) {
    res.status(500).send(error);
  }
});

// Delete a calendar event
app.delete('/api/calendar/:id', async (req, res) => {
  try {
    const accessToken = req.headers.authorization;
    const eventId = req.params.id;

    const result = await outlook.calendar.deleteEvent({ token: accessToken, eventId });
    if (result) {
      res.send({ message: "Calendar event deleted successfully" });
    } else {
      res.status(404).send({ message: "Calendar event not found" });
    }
  } catch (error) {
    res.status(500).send(error);
  }
});



// This direct call is no longer necessary, as adding events is handled via the API endpoint


