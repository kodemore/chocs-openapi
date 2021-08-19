import json

import pytest
from chocs import HttpRequest, HttpMethod, HttpResponse, Route

from chocs_middleware.openapi import OpenApiMiddleware
from os import path

from chocs_middleware.openapi.error import RequestBodyValidationError


def test_can_pass_validate_request_body() -> None:
    # given
    dirname = path.dirname(__file__)
    middleware = OpenApiMiddleware(path.join(dirname, "../fixtures/openapi.yml"))
    request_payload = {
        "name": "Bobik",
        "base_tag": "Good boi!"
    }
    request = HttpRequest(
        HttpMethod.POST,
        "/pets",
        body=json.dumps(request_payload),
        headers={"content-type": "application/json"}
    )
    request.route = Route("/pets")
    success_response = HttpResponse()

    def _next(request: HttpRequest) -> HttpResponse:
        return success_response

    # when
    response = middleware.handle(request, _next)

    # then
    assert response == success_response


def test_can_fail_validate_request_body() -> None:
    # given
    dirname = path.dirname(__file__)
    middleware = OpenApiMiddleware(path.join(dirname, "../fixtures/openapi.yml"))
    request_payload = {
        "base_tag": "Good boi!"
    }
    request = HttpRequest(
        HttpMethod.POST,
        "/pets",
        body=json.dumps(request_payload),
        headers={"content-type": "application/json"}
    )
    request.route = Route("/pets")

    def _next(request: HttpRequest) -> HttpResponse:
        return HttpResponse()

    # then
    with pytest.raises(RequestBodyValidationError):
        middleware.handle(request, _next)


def test_can_pass_validate_request_parameters() -> None:
    # given
    dirname = path.dirname(__file__)
    middleware = OpenApiMiddleware(path.join(dirname, "../fixtures/openapi.yml"))
    request = HttpRequest(
        HttpMethod.GET,
        "/pets",
        query_string="tags[]=good&tags[]=boi",
    )
    request.route = Route("/pets")
    success_response = HttpResponse()

    def _next(request: HttpRequest) -> HttpResponse:
        return success_response

    # when
    response = middleware.handle(request, _next)

    # then
    assert response == success_response
