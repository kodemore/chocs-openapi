from abc import abstractmethod, ABC
from functools import cached_property
from typing import Any, Callable

from chocs import HttpRequest, Route, HttpHeaders
from opyapi import build_validator_for
from opyapi.errors import ValidationError

from chocs_middleware.openapi.error import (
    RequestValidationError,
    RequestBodyValidationError,
    RequestPathValidationError,
    RequestHeadersValidationError,
    RequestQueryValidationError,
    RequestCookiesValidationError,
)


class Validator(ABC):
    def __init__(self, schema: Any):
        self.schema = schema

    @cached_property
    def _validator(self) -> Callable:
        if self.schema is None:
            return lambda x: x
        return build_validator_for(self.schema)

    @abstractmethod
    def validate(self, request: HttpRequest) -> None:
        pass

    def __call__(self, *args, **kwargs) -> None:
        self.validate(*args, **kwargs)


class RequestBodyValidator(Validator):
    def validate(self, request: HttpRequest) -> None:
        if not hasattr(request.parsed_body, "data"):
            raise RequestValidationError.for_invalid_body()

        if isinstance(request.parsed_body.data, dict) or isinstance(request.parsed_body.data, list):  # type: ignore
            parsed_body = request.parsed_body.data  # type: ignore
        else:
            raise RequestValidationError.for_invalid_body()

        try:
            request._parsed_body = self._validator(parsed_body)
        except ValidationError as e:
            raise RequestBodyValidationError(reason=str(e)) from e


class RequestPathValidator(Validator):
    def validate(self, request: HttpRequest) -> None:
        path_parameters = request.path_parameters
        try:
            request.path_parameters = self._validator(path_parameters)
            if isinstance(request.route, Route):
                request.route._parameters = request.path_parameters
        except ValidationError as e:
            raise RequestPathValidationError(reason=str(e)) from e


class RequestHeadersValidator(Validator):
    def validate(self, request: HttpRequest) -> None:
        # We have to normalise headers before validation
        headers = {}
        for name, values in request.headers.items():
            headers[name] = values[0] if len(values) == 1 else values

        try:
            headers = self._validator(headers)
            request._headers = HttpHeaders(headers)
        except ValidationError as e:
            raise RequestHeadersValidationError(reason=str(e)) from e


class RequestQueryValidator(Validator):
    def validate(self, request: HttpRequest) -> None:
        query = dict(request.query_string)

        try:
            query = self._validator(query)
            request.query_string._params = query
        except ValidationError as e:
            raise RequestQueryValidationError(reason=str(e)) from e


class RequestCookiesValidator(Validator):
    def validate(self, request: HttpRequest) -> None:
        cookies = {}
        for name, cookie in request.cookies.items():
            cookies[name] = str(cookie)

        try:
            validated_cookies = self._validator(cookies)
            request_cookies = request._cookies._cookies
            for cookie_name in request_cookies.keys():
                request_cookies[cookie_name].value = validated_cookies[cookie_name]
        except ValidationError as e:
            raise RequestCookiesValidationError(reason=str(e)) from e


def create_request_validator(validator_type: str, schema: Any) -> Validator:
    if validator_type == "path":
        return RequestPathValidator(schema)
    if validator_type == "query":
        return RequestQueryValidator(schema)
    if validator_type == "header":
        return RequestHeadersValidator(schema)
    if validator_type == "cookie":
        return RequestCookiesValidator(schema)

    raise ValueError("Unexpected validator type")
