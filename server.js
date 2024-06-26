require('dotenv').config();

const express = require('express');
const app = express();
const port = 3001;
const mongoose = require('mongoose');


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



const Medication = require('./Medication'); // Path to Medication model

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
    console.log(Medication);
    const newMedication = new Medication(req.body);

    try {
        const savedMedication = await newMedication.save();
        res.status(201).json(savedMedication);
        console.log('Medication added');
    } catch (error) {
        res.status(400).send(error);
    }
});

// Endpoint to remove a medication by its _id
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

// Endpoint to update a medication by its _id
app.put('/api/medications/:id', async (req, res) => {
    try {
        const result = await Medication.findByIdAndUpdate
            (req.params.id, req.body, { new: true });
        if (result) {
            res.json(result);
        }
        else {
            res.status(404).send({ message: "Medication not found" });
        }
    } catch (error) {
        res.status(500)
            .send(error);
    }
});

const Event = require('./Event'); // Path to Event model

app.get('/api/events', async (req, res) => {
    try {
        const events = await Event.find();
        res.json(events);
    } catch (error) {
        res.status(500).send(error);
    }
});
//  add new event
app.post('/api/events', async (req, res) => {
    const newEvent = new Event(req.body);

    try {
        const savedEvent = await newEvent.save();
        res.status(201).json(savedEvent);
    } catch (error) {
        res.status(400).send(error);
    }
});
// clear all events
app.delete('/api/events', async (req, res) => {
    try {
        await Event.deleteMany();
        res.send({ message: 'All events deleted successfully' });
    } catch (error) {
        res.status(500).send(error);
    }
});

const ViewState = require('./View'); // Path to View model

// Endpoint to get the current view state
app.get('/api/view', async (req, res) => {
    try {
        const viewState = await ViewState.findOne();
        res.json(viewState);
    } catch (error) {
        res.status(500).send(error);
    }
});

app.post('/api/view', async (req, res) => {
  const { viewName } = req.body;
  await ViewState.updateOne({}, { currentView: viewName }, { upsert: true });
  res.send({ status: 'View updated successfully', currentView: viewName });
});


const FeatureUsage = require('./FeatureUsage'); 

app.post('/api/featureUsage', async (req, res) => {
    try {
      const {featureName} = req.body;
      const newUsage = new FeatureUsage({ featureName});
      await newUsage.save();
      res.status(201).json({ message: "Feature usage logged successfully." });
    } catch (error) {
      res.status(500).send(error);
    }
  });
  
  app.get('/api/featureUsage', async (req, res) => {
    try {
      const usageData = await FeatureUsage.find({});
      // Further processing can be done here as needed, e.g., counting, aggregating
      res.json(usageData);
    } catch (error) {
      res.status(500).send(error);
    }
  });