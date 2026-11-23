"""
Tools exposed to the model. Each function validates its own input and returns plain data;
the ToolBox derives the JSON schema from the signature and docstring.
"""

import secrets
from datetime import date
from typing import Literal

from db import connect

from toolkit import ToolBox

Cabin = Literal["economy", "business"]


def list_destinations() -> list[dict]:
    """List every destination served from Lagos with economy fares and flight times."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT city, country, fare_economy, flight_hours FROM routes ORDER BY city"
        ).fetchall()
    return [dict(r) for r in rows]


def get_fare(city: str, cabin: Cabin = "economy") -> dict:
    """Get the return fare from Lagos to a destination.

    Args:
        city: Destination city, e.g. "London".
        cabin: Cabin class.
    """
    with connect() as conn:
        row = conn.execute("SELECT * FROM routes WHERE city = ?", (city.lower(),)).fetchone()
    if not row:
        return {"error": f"No route to {city}. Use list_destinations to see options."}
    return {
        "city": row["city"].title(),
        "cabin": cabin,
        "fare_usd": row[f"fare_{cabin}"],
        "flight_hours": row["flight_hours"],
    }


def book_flight(passenger: str, city: str, travel_date: str, cabin: Cabin = "economy") -> dict:
    """Book a return flight from Lagos. Only call after the customer confirmed all details.

    Args:
        passenger: Full name of the passenger.
        city: Destination city.
        travel_date: Departure date in YYYY-MM-DD format.
        cabin: Cabin class.
    """
    try:
        when = date.fromisoformat(travel_date)
    except ValueError:
        return {"error": "travel_date must be YYYY-MM-DD"}
    if when <= date.today():
        return {"error": "travel_date must be in the future"}

    fare = get_fare(city, cabin)
    if "error" in fare:
        return fare

    reference = "HA" + secrets.token_hex(3).upper()
    with connect() as conn:
        conn.execute(
            "INSERT INTO bookings (reference, passenger, city, cabin, travel_date, price)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (reference, passenger, city.lower(), cabin, when.isoformat(), fare["fare_usd"]),
        )
    return {"reference": reference, "status": "confirmed", **fare, "travel_date": travel_date}


def get_booking(reference: str) -> dict:
    """Look up an existing booking.

    Args:
        reference: Booking reference, e.g. HA1F2E3D.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM bookings WHERE reference = ?", (reference.upper(),)
        ).fetchone()
    return dict(row) if row else {"error": f"No booking with reference {reference}"}


def cancel_booking(reference: str) -> dict:
    """Cancel a booking. Only call after the customer explicitly confirmed the cancellation.

    Args:
        reference: Booking reference.
    """
    with connect() as conn:
        updated = conn.execute(
            "UPDATE bookings SET status = 'cancelled'"
            " WHERE reference = ? AND status != 'cancelled'",
            (reference.upper(),),
        ).rowcount
    if not updated:
        return {"error": f"No active booking with reference {reference}"}
    return {"reference": reference.upper(), "status": "cancelled"}


def make_toolbox(on_call=None) -> ToolBox:
    return ToolBox(on_call=on_call).add(
        list_destinations, get_fare, book_flight, get_booking, cancel_booking
    )
