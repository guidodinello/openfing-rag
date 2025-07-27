class ValidationException(Exception):
    def __init__(
        self,
        message: str,
        field_errors: dict[str, list[str]] | None = None,
        error_code: str = "validation_error",
    ):
        self.message = message
        self.field_errors = field_errors or {}
        self.error_code = error_code
        super().__init__(message)
