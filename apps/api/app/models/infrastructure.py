"""Infrastructure domain re-exports.

Authoritative domain models for residential and transport operations are defined in:
- `app.models.residential` (Step 54)
- `app.models.transport` (Step 55)

These re-exports preserve backwards compatibility with early monolithic references.
"""

from app.models.residential import (
    Hostel,
    HostelAllocation,
    HostelBed,
    HostelBlock,
    HostelComplaint,
    HostelFloor,
    HostelLeavePass,
    HostelRoom,
)
from app.models.transport import (
    TransportAllocation,
    TransportDriver,
    TransportRoute,
    TransportStop,
    TransportVehicle,
)

__all__ = [
    "Hostel",
    "HostelBlock",
    "HostelFloor",
    "HostelRoom",
    "HostelBed",
    "HostelAllocation",
    "HostelLeavePass",
    "HostelComplaint",
    "TransportVehicle",
    "TransportDriver",
    "TransportRoute",
    "TransportStop",
    "TransportAllocation",
]
