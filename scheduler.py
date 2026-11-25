"""
Schedule utilities for a small appointment-booking service.

This module intentionally contains one subtle bug in the appointment conflict
check. Other functions are included to make the file longer and realistic,
so a debugging agent must locate the relevant logic rather than patch blindly.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional


DEFAULT_SLOT_MINUTES = 30
MAX_BOOKING_MINUTES = 240
BUSINESS_OPEN_HOUR = 9
BUSINESS_CLOSE_HOUR = 17


@dataclass(frozen=True)
class Appointment:
    customer: str
    start: datetime
    end: datetime
    service: str = "general"


@dataclass(frozen=True)
class TimeSlot:
    start: datetime
    end: datetime


def normalize_customer_name(name: str) -> str:
    """Normalize a customer name for display and comparisons."""
    return " ".join(name.strip().split()).title()


def duration_minutes(start: datetime, end: datetime) -> int:
    """Return duration as whole minutes."""
    return int((end - start).total_seconds() // 60)


def is_valid_interval(start: datetime, end: datetime) -> bool:
    """Check that an interval has a positive duration."""
    return start < end


def is_within_business_hours(start: datetime, end: datetime) -> bool:
    """Return whether an appointment is within 09:00–17:00 on one day."""
    if start.date() != end.date():
        return False
    if not is_valid_interval(start, end):
        return False
    opening = start.replace(hour=BUSINESS_OPEN_HOUR, minute=0, second=0, microsecond=0)
    closing = start.replace(hour=BUSINESS_CLOSE_HOUR, minute=0, second=0, microsecond=0)
    return start >= opening and end <= closing


def has_valid_booking_length(start: datetime, end: datetime) -> bool:
    """Appointments must be positive and no longer than four hours."""
    length = duration_minutes(start, end)
    return 0 < length <= MAX_BOOKING_MINUTES


def overlaps(existing: Appointment, start: datetime, end: datetime) -> bool:
    """
    Determine whether a requested interval conflicts with an existing appointment.

    Appointment intervals are intended to be half-open: [start, end).
    This means one appointment may end exactly when another begins.
    """
    # INTENTIONAL BUG: adjacent appointments are treated as overlapping.
    return start <= existing.end and end >= existing.start


def is_slot_available(
    appointments: Iterable[Appointment],
    start: datetime,
    end: datetime,
    service: Optional[str] = None,
) -> bool:
    """Return True when the requested time has no conflicting appointment."""
    if not is_valid_interval(start, end):
        return False
    if not is_within_business_hours(start, end):
        return False
    if not has_valid_booking_length(start, end):
        return False

    for appointment in appointments:
        if service is not None and appointment.service != service:
            continue
        if overlaps(appointment, start, end):
            return False
    return True


def create_appointment(
    customer: str,
    start: datetime,
    end: datetime,
    service: str = "general",
) -> Appointment:
    """Create an appointment after basic input validation."""
    clean_name = normalize_customer_name(customer)
    if not clean_name:
        raise ValueError("Customer name cannot be empty")
    if not is_valid_interval(start, end):
        raise ValueError("End time must be after start time")
    if not is_within_business_hours(start, end):
        raise ValueError("Appointment is outside business hours")
    if not has_valid_booking_length(start, end):
        raise ValueError("Appointment length is invalid")
    return Appointment(clean_name, start, end, service)


def add_minutes(value: datetime, minutes: int) -> datetime:
    """Return a datetime shifted by the requested number of minutes."""
    return value + timedelta(minutes=minutes)


def generate_slots(
    day: datetime,
    slot_minutes: int = DEFAULT_SLOT_MINUTES,
) -> list[TimeSlot]:
    """Generate fixed-size slots between opening and closing times."""
    if slot_minutes <= 0:
        raise ValueError("slot_minutes must be positive")
    opening = day.replace(hour=BUSINESS_OPEN_HOUR, minute=0, second=0, microsecond=0)
    closing = day.replace(hour=BUSINESS_CLOSE_HOUR, minute=0, second=0, microsecond=0)
    slots: list[TimeSlot] = []
    cursor = opening
    while cursor + timedelta(minutes=slot_minutes) <= closing:
        next_cursor = cursor + timedelta(minutes=slot_minutes)
        slots.append(TimeSlot(cursor, next_cursor))
        cursor = next_cursor
    return slots


def find_available_slots(
    appointments: Iterable[Appointment],
    day: datetime,
    slot_minutes: int = DEFAULT_SLOT_MINUTES,
) -> list[TimeSlot]:
    """Return generated slots that are available against existing appointments."""
    appointments_list = list(appointments)
    return [
        slot
        for slot in generate_slots(day, slot_minutes)
        if is_slot_available(appointments_list, slot.start, slot.end)
    ]


def count_appointments(appointments: Iterable[Appointment]) -> int:
    """Count the appointments in an iterable."""
    return sum(1 for _ in appointments)


def total_booked_minutes(appointments: Iterable[Appointment]) -> int:
    """Sum appointment durations."""
    return sum(duration_minutes(item.start, item.end) for item in appointments)


def appointments_for_customer(
    appointments: Iterable[Appointment],
    customer_name: str,
) -> list[Appointment]:
    """Return appointments matching a normalized customer name."""
    target = normalize_customer_name(customer_name)
    return [
        item for item in appointments
        if normalize_customer_name(item.customer) == target
    ]


def sort_appointments(appointments: Iterable[Appointment]) -> list[Appointment]:
    """Sort appointments by start time, then customer name."""
    return sorted(appointments, key=lambda item: (item.start, item.customer.lower()))


def daily_summary(appointments: Iterable[Appointment], day: datetime) -> dict:
    """Summarize appointment count and booked minutes for a given day."""
    same_day = [item for item in appointments if item.start.date() == day.date()]
    return {
        "date": day.date().isoformat(),
        "appointment_count": count_appointments(same_day),
        "booked_minutes": total_booked_minutes(same_day),
    }


def next_slot_start(
    appointments: Iterable[Appointment],
    day: datetime,
    slot_minutes: int = DEFAULT_SLOT_MINUTES,
) -> Optional[datetime]:
    """Return the start of the earliest available slot, or None."""
    available = find_available_slots(appointments, day, slot_minutes)
    if not available:
        return None
    return available[0].start


def format_slot(slot: TimeSlot) -> str:
    """Format a slot as a readable time range."""
    return f"{slot.start:%H:%M}-{slot.end:%H:%M}"


def get_schedule_for_day(
    appointments: Iterable[Appointment],
    day: datetime,
) -> list[Appointment]:
    """Return appointments for the requested calendar day in chronological order."""
    return sort_appointments(
        item for item in appointments if item.start.date() == day.date()
    )
