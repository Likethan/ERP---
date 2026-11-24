"""CampusOS Backend Application Package."""

import datetime
import enum

# Python 3.10 backwards compatibility polyfills
if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.timezone.utc  # noqa: UP017

if not hasattr(enum, "StrEnum"):

    class StrEnum(str, enum.Enum):

        def _generate_next_value_(name, start, count, last_values):
            return name.lower()

        def __str__(self):
            return str(self.value)

    enum.StrEnum = StrEnum

__version__ = "0.1.0"
