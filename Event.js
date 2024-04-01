const mongoose = require('mongoose');

const EventsSchema = new mongoose.Schema({
    subject: String,
    start: String,
    end: String,
    location: String,
});

const Events = mongoose.model('Medication', EventsSchema);

module.exports = Events; 