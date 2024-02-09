// Import the functions you need from the SDKs you need
import firebase from 'firebase/app';
import 'firebase/firestore';

// Your web app's Firebase configuration (replace with your actual config)
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  // other config properties
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firestore and export it
const db = firebase.firestore();
export { db };