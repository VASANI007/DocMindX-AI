"""
    DocMindX AI - Patient Checkup and Dose Scheduler
"""
import datetime

class HealthCheckScheduler:
    """Manages active patient reminder queues and follow-up intervals."""
    def __init__(self):
        self.reminders = []

    def add_schedule(self, item_name: str, interval_hours: int = 8, total_days: int = 5) -> list:
        now = datetime.datetime.now()
        schedule_slots = []
        
        current_time = now
        end_time = now + datetime.timedelta(days=total_days)
        
        while current_time < end_time:
            schedule_slots.append(current_time.strftime("%Y-%m-%d %H:%M"))
            current_time += datetime.timedelta(hours=interval_hours)
            
        return schedule_slots

health_scheduler = HealthCheckScheduler()
