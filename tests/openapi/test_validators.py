import datetime
from typing import Type

import pytest
from chocs import HttpRequest, HttpMethod, Route, HttpHeaders

from chocs_middleware.openapi.error import RequestBodyValidationError, RequestValidationError, \
    RequestQueryValidationError, RequestPathValidationError, RequestHeadersValidationError, \
    RequestCookiesValidationError
from chocs_middleware.openapi.validators import RequestBodyValidator, RequestQueryValidator, RequestPathValidator, \
    RequestHeadersValidator, RequestCookiesValidator, create_request_validator


def test_pass_request_body_validator() -> None:
    # given
    validator = RequestBodyValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "age": {"type": "integer"},
        },
        "required": ["name"]
    })
    request = HttpRequest(
        HttpMethod.GET,
        body='{"name": "Bob", "dob": "1970-12-01"}',
        headers={"content-type": "application/json"}
    )

    # then
    validator(request)


def test_fails_request_body_validator_without_correct_content_headers() -> None:
    # given
    validator = RequestBodyValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "age": {"type": "integer"},
        },
        "required": ["name"]
    })
    request = HttpRequest(
        HttpMethod.GET,
        body='{"name": "Bob", "dob": "1970-12-01"}',
    )

    # then
    with pytest.raises(RequestValidationError):
        validator(request)


def test_fails_request_body_validator_with_invalid_body() -> None:
    # given
    validator = RequestBodyValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "age": {"type": "integer"},
        },
        "required": ["name"]
    })
    request = HttpRequest(
        HttpMethod.GET,
        body='{"dob": "1970-12-01"}',
        headers={"content-type": "application/json"}
    )

    # then
    with pytest.raises(RequestBodyValidationError):
        validator(request)


def test_pass_request_query_validator() -> None:
    # given
    validator = RequestQueryValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "age": {"type": "integer"},
        },
        "required": ["name"]
    })
    request = HttpRequest(
        HttpMethod.GET,
        query_string="name=Bob&dob=1970-12-01"
    )

    # then
    validator(request)


def test_fail_request_query_validator() -> None:
    # given
    validator = RequestQueryValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "age": {"type": "integer"},
        },
        "required": ["name"]
    })
    request = HttpRequest(
        HttpMethod.GET,
        query_string="dob=1970-12-01"
    )

    # then
    with pytest.raises(RequestQueryValidationError):
        validator(request)


def test_pass_request_path_validator() -> None:
    # given
    validator = RequestPathValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })

    request = HttpRequest(HttpMethod.GET, path="/users/bob/1970-12-01")
    route = Route("/users/{name}/{dob}")
    request.route = route.match(request.path)
    request.path_parameters = request.route.parameters

    # then
    validator(request)


def test_fail_request_path_validator() -> None:
    # given
    validator = RequestPathValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })

    request = HttpRequest(HttpMethod.GET, path="/users/bob/12")
    route = Route("/users/{name}/{dob}")
    request.route = route.match(request.path)
    request.path_parameters = route.parameters

    # then
    with pytest.raises(RequestPathValidationError):
        validator(request)


def test_pass_request_headers_validator() -> None:
    # given
    validator = RequestHeadersValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })
    request = HttpRequest(HttpMethod.GET, headers={
        "name": "Bob",
        "dob": "1970-01-01"
    })

    # then
    validator(request)


def test_fail_request_headers_validator() -> None:
    # given
    validator = RequestHeadersValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })
    request = HttpRequest(HttpMethod.GET, headers={
        "name": "Bob",
        "dob": "12"
    })

    # then
    with pytest.raises(RequestHeadersValidationError):
        validator(request)


def test_pass_request_cookies_validator() -> None:
    # given
    validator = RequestCookiesValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })
    headers = HttpHeaders()
    headers.set("cookie", "name=Bob;dob=1970-01-01")
    request = HttpRequest(HttpMethod.GET, headers=headers)

    # then
    validator(request)


def test_fail_request_cookies_validator() -> None:
    # given
    validator = RequestCookiesValidator({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
        },
        "required": ["name", "dob"]
    })
    headers = HttpHeaders()
    headers.set("cookie", "name=Bob;dob=1")
    request = HttpRequest(HttpMethod.GET, headers=headers)

    # then
    with pytest.raises(RequestCookiesValidationError):
        validator(request)


@pytest.mark.parametrize("parameter_location,expected_type", [
    ["header", RequestHeadersValidator],
    ["cookie", RequestCookiesValidator],
    ["path", RequestPathValidator],
    ["query", RequestQueryValidator]
])
def test_create_request_validator(parameter_location: str, expected_type: Type) -> None:
    validator = create_request_validator(parameter_location, None)

    assert isinstance(validator, expected_type)
