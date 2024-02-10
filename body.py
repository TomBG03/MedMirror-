import requests
import argparse

BASE_URL = 'http://localhost:3001/api'

def fetch_medications():
    response = requests.get(f'{BASE_URL}/medications')
    if response.status_code == 200:
        medications = response.json()
        for medication in medications:
            med_id = medication['_id']
            print(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    else:
        print("Failed to fetch medications")

def add_medication(name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.post(f'{BASE_URL}/medications', json=medication)
    if response.status_code == 201:
        print("Medication added:", response.json())
    else:
        print("Failed to add medication")

def delete_medication(medication_id):
    response = requests.delete(f'{BASE_URL}/medications/{medication_id}')
    if response.status_code == 200:
        print("Medication deleted")
    else:
        print("Failed to delete medication")

def main():
    parser = argparse.ArgumentParser(description='Medications Client')
    subparsers = parser.add_subparsers(dest='command')

    # Fetch medications command
    subparsers.add_parser('fetch', help='Fetch all medications')

    # Add medication command
    add_parser = subparsers.add_parser('add', help='Add a new medication')
    add_parser.add_argument('name', help='Name of the medication')
    add_parser.add_argument('dosage', help='Dosage of the medication')
    add_parser.add_argument('time', help='Time of administration')

    # Delete medication command
    delete_parser = subparsers.add_parser('delete', help='Delete a medication by its ID')
    delete_parser.add_argument('id', help='The ID of the medication to delete')

    args = parser.parse_args()

    if args.command == 'fetch':
        fetch_medications()
    elif args.command == 'add':
        add_medication(args.name, args.dosage, args.time)
    elif args.command == 'delete':
        delete_medication(args.id)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
