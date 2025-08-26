class ValidationException(Exception):
    def __init__(
        self,
        message: str,
        field_errors: dict[str, list[str]] | None = None,
        error_code: str = "validation_error",
    ):
        self.message = message
        self.error_code = error_code
        self.field_errors = field_errors or {}
        super().__init__(message)
