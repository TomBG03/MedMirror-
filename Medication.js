const mongoose = require('mongoose');

const MedicationSchema = new mongoose.Schema({
    name: String,
    dosage: String,
    time: String,
});

const Medication = mongoose.model('Medication', MedicationSchema);

module.exports = Medication;