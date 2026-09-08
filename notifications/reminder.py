"""
    DocMindX AI - Medication & Health Check Reminder Engine
"""
import datetime

def create_medication_reminder(medicine_name: str, dose: str, time_str: str, instructions: str = "") -> dict:
    """Creates a structured pill reminder payload."""
    return {
        "medicine_name": medicine_name,
        "dose": dose,
        "scheduled_time": time_str,
        "instructions": instructions or "Take with a full glass of water after food.",
        "created_at": datetime.datetime.now().isoformat(),
        "status": "ACTIVE"
    }

def format_reminder_alert(reminder: dict, lang_code: str = "en") -> str:
    """Formats reminder message in user's preferred language."""
    name = reminder.get("medicine_name", "Medicine")
    time_val = reminder.get("scheduled_time", "Now")
    dose = reminder.get("dose", "1 Tablet")

    clock_icon = '<img src="https://cdn-icons-png.flaticon.com/512/2015/2015205.png" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 4px; display: inline-block;"/>'
    if lang_code == "hi":
        return f"{clock_icon} **दवा का समय:** {name} ({dose}) लेने का समय हो गया है ({time_val})।"
    elif lang_code == "gu":
        return f"{clock_icon} **દવાનો સમય:** {name} ({dose}) લેવાનો સમય થયો છે ({time_val})."
    else:
        return f"{clock_icon} **Medication Reminder:** Time to take {name} ({dose}) at {time_val}."
