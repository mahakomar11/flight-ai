import re

FLIGHT_NUMBER_PATTERN = r"^([a-zA-Z0-9]{2}[a-zA-Z]?)(\d{1,4}[a-zA-Z]?)$"


def parse_iata_flight_number(full_flight_number: str) -> tuple[str, str]:
    # Define the regular expression pattern
    pattern = re.compile(FLIGHT_NUMBER_PATTERN)
    match = pattern.match(full_flight_number)

    if match:
        airline_iata, flight_number = match.groups()
        return airline_iata, flight_number
    else:
        raise ValueError(f"Invalid IATA full flight number: {full_flight_number}")
