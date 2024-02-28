
const mongoose = require('mongoose');

const viewStateSchema = new mongoose.Schema({
  currentView: String, // For example, "medicationsList", "detailsView", etc.
});

const ViewState = mongoose.model('ViewState', viewStateSchema);
module.exports = ViewState; 
