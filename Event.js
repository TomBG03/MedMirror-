const mongoose = require('mongoose');

const EventsSchema = new mongoose.Schema({
    subject: String,
    start: String,
    end: String,
    location: String,
});

const Event = mongoose.model('Event', EventsSchema);

module.exports = Event; 