import { db } from './firebaseConfig.js';

// Function to add a medication
export const addMedication = (name, dosage, time) => {
  return db.collection('medications').add({
    name,
    dosage,
    time
  });
};

// Function to fetch all medications
export const getMedications = () => {
  return db.collection('medications').get();
};