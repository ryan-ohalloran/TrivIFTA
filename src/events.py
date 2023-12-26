
class NoFuelTaxDataException(Exception):
    """
    Raised when no data is returned from the FuelTaxDetails endpoint
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)