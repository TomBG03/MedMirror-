const mongoose = require('mongoose');


// select=["subject", "organizer", "attendees", "start", "end", "location"]

const calendarEventSchema = new mongoose.Schema({
  subject: {
    type: String,
    required: true
  },
  description: String,
  location: String,
  start: {
    type: Date,
    required: true
  },
  end: {
    type: Date,
    required: true
  },
  attendees: [String] // Array of strings to store email addresses or names of attendees
});

const CalendarEvent = mongoose.model('CalendarEvent', calendarEventSchema);

module.exports = CalendarEvent;