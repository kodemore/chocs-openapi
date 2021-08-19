from opyapi.errors import ValidationError


class RequestValidationError(ValidationError):
    code = "invalid_request"
    message = "Failed to validate request: {reason}"

    @classmethod
    def for_invalid_body(cls) -> "RequestValidationError":
        return cls(reason="Request's content type is invalid.")


class RequestBodyValidationError(RequestValidationError):
    code = "invalid_request_body"
    message = "Failed to validate request's body: {reason}"


class RequestQueryValidationError(RequestValidationError):
    code = "invalid_request_query"
    message = "Failed to validate request's query string: {reason}"


class RequestPathValidationError(RequestValidationError):
    code = "invalid_request_uri"
    message = "Failed to validate request's uri: {reason}"


class RequestHeadersValidationError(RequestValidationError):
    code = "invalid_request_query"
    message = "Failed to validate request's headers: {reason}"


class RequestCookiesValidationError(RequestValidationError):
    code = "invalid_request_cookies"
    message = "Failed to validate request's cookies: {reason}"
