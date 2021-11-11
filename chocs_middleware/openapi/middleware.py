from typing import Callable, Dict, List, Any

from chocs import HttpMethod, HttpRequest, HttpResponse
from chocs.middleware import Middleware, MiddlewareHandler
from opyapi import JsonSchema

from chocs_middleware.openapi.validators import RequestBodyValidator, create_request_validator


class OpenApiMiddleware(Middleware):
    def __init__(
        self,
        openapi_filename: str,
        validate_body: bool = True,
        validate_headers: bool = True,
        validate_query: bool = True,
        validate_path: bool = True,
        validate_cookies: bool = True,
    ):
        self.openapi = JsonSchema.from_file(openapi_filename)
        self.validators = {
            "body": validate_body,
            "headers": validate_headers,
            "query": validate_query,
            "path": validate_path,
            "cookies": validate_cookies,
        }

        self._validators: Dict[str, List[Callable]] = {}

    def handle(self, request: HttpRequest, next: MiddlewareHandler) -> HttpResponse:
        route = request.route
        if not route:
            return next(request)

        if route and "skip_validation" in route.attributes and route.attributes["skip_validation"]:
            return next(request)

        validator_cache_key = f"{request.method} {route.route}".lower()
        if validator_cache_key not in self._validators:
            self._validators[validator_cache_key] = self._get_validators_for_uri(
                route.route,
                request.method,
                str(request.headers.get("content-type", "application/json")),
            )

        validators = self._validators[validator_cache_key]
        if not validators:
            return next(request)
        for validator in validators:
            validator(request)

        return next(request)

    def _get_validators_for_uri(self, route: str, method: HttpMethod, content_type: str) -> List[Callable]:
        path = route.replace("/", "\\/")
        method_name = str(method).lower()
        validators: List[Callable] = []
        content_type = content_type.split(";")[0].strip()  # e.g. application/json ; encoding=utf8

        try:
            open_api_uri_schema = self.openapi.query(f"/paths/{path}")
            open_api_method_schema = open_api_uri_schema[method_name]
        except (KeyError, LookupError):
            return validators

        if self.validators["body"]:
            if (
                "requestBody" in open_api_method_schema
                and "content" in open_api_method_schema["requestBody"]
                and content_type in open_api_method_schema["requestBody"]["content"]
                and "schema" in open_api_method_schema["requestBody"]["content"][content_type]
            ):
                validators.append(
                    RequestBodyValidator(open_api_method_schema["requestBody"]["content"][content_type]["schema"])
                )

        uri_parameters = []
        if "parameters" in open_api_uri_schema:
            uri_parameters = open_api_uri_schema["parameters"]
        if "parameters" in open_api_method_schema:
            uri_parameters = uri_parameters + open_api_method_schema["parameters"]
        self._process_uri_parameters(uri_parameters, validators)

        return validators

    def _process_uri_parameters(self, uri_parameters: List[Dict[str, Any]], validators: List[Callable]) -> None:
        merged_parameters: Dict[str, Any] = {}

        for parameter in uri_parameters:
            if "in" not in parameter:
                continue

            location = parameter["in"]
            name = parameter["name"]
            if location not in merged_parameters:
                merged_parameters[location] = {"type": "object"}
                merged_parameters[location]["parameters"] = {}
            merged_parameters[location]["parameters"][name] = parameter.get("schema", {})

            if "required" in parameter and parameter["required"]:
                if "required" not in merged_parameters[location]:
                    merged_parameters[location]["required"] = []
                merged_parameters[location]["required"].append(name)

        for location, schema in merged_parameters.items():
            if location in self.validators and self.validators[location]:
                validators.append(create_request_validator(location, schema))


__all__ = ["OpenApiMiddleware"]
