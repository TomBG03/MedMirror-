
"""
Demonstrates how to use the asyncio compatible scheduler to schedule a job that executes on 3
second intervals.
"""

from datetime import datetime, timedelta
import asyncio
import os
from playsound import playsound

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class ReminderScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def add_reminder(self, seconds, reminder_message='Time to take a break!'):
        self.scheduler.add_job(self._play_sound, 'interval', seconds=seconds, args=[reminder_message])

    def add_reminder_at(self, time, reminder_message='Time to take a break!'):
        self.scheduler.add_job(self._play_sound, 'date', run_date=time, args=[reminder_message])
    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    def remind_me(self, reminder_message):
        print(reminder_message)

    def _play_sound(self, reminder_message):
        playsound('ding.mp3')
        print(reminder_message)

async def sleepyFunc():
    await asyncio.sleep(20)
    print('Sleepy Function')
def tick():
    print('Tick! The time is: %s' % datetime.now())


async def main():
    scheduler = ReminderScheduler()
    scheduler.add_reminder(seconds = 3, reminder_message='Time to take a break!')
    scheduler.add_reminder_at(datetime.now() + timedelta(seconds=8), reminder_message='TAKDBUQVD QTWD')
    print(datetime.now())
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    while True:
        scheduler.add_reminder_at(datetime.now() + timedelta(seconds=2), reminder_message='AHHHHHHH')
        print("Scheduling")
        await asyncio.sleep(1000)
        await sleepyFunc()

if __name__ == '__main__':
    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass