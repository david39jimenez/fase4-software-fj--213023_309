class SoftwareFJError(Exception):
    """Excepción base del dominio Software FJ."""


class ValidationError(SoftwareFJError):
    pass


class MissingParameterError(ValidationError):
    pass


class InvalidValueError(ValidationError):
    pass


class ClienteError(SoftwareFJError):
    pass


class ServicioError(SoftwareFJError):
    pass


class ReservaError(SoftwareFJError):
    pass


class ServiceNotAvailableError(ServicioError):
    pass


class OperationNotAllowedError(SoftwareFJError):
    pass


class InconsistentCalculationError(SoftwareFJError):
    pass


class BookingConflictError(ReservaError):
    pass

