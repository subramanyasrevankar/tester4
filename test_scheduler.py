from datetime import datetime

from scheduler import Appointment, is_slot_available, overlaps, find_available_slots


def dt(hour, minute=0):
    return datetime(2026, 5, 12, hour, minute)


def appointment(start_hour, start_minute, end_hour, end_minute, customer="Alex"):
    return Appointment(
        customer=customer,
        start=dt(start_hour, start_minute),
        end=dt(end_hour, end_minute),
    )


def test_slot_before_existing_appointment_is_available():
    existing = [appointment(10, 0, 10, 30)]
    assert is_slot_available(existing, dt(9, 30), dt(10, 0))


def test_slot_after_existing_appointment_is_available():
    existing = [appointment(10, 0, 10, 30)]
    assert is_slot_available(existing, dt(10, 30), dt(11, 0))


def test_real_overlap_is_not_available():
    existing = [appointment(10, 0, 10, 30)]
    assert not is_slot_available(existing, dt(10, 15), dt(10, 45))


def test_slot_inside_existing_appointment_is_not_available():
    existing = [appointment(10, 0, 11, 0)]
    assert not is_slot_available(existing, dt(10, 15), dt(10, 45))


def test_slot_covering_existing_appointment_is_not_available():
    existing = [appointment(10, 15, 10, 45)]
    assert not is_slot_available(existing, dt(10, 0), dt(11, 0))


def test_empty_schedule_has_available_slot():
    assert is_slot_available([], dt(9, 0), dt(9, 30))


def test_invalid_zero_length_slot_is_unavailable():
    assert not is_slot_available([], dt(9, 0), dt(9, 0))


def test_find_slots_allows_adjacent_slots():
    existing = [appointment(10, 0, 10, 30)]
    slots = find_available_slots(existing, dt(10), slot_minutes=30)
    assert any(slot.start == dt(10, 30) for slot in slots)
