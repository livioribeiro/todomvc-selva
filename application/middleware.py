from http import HTTPStatus
from urllib.parse import parse_qs, urlencode, urlparse

from asgikit.requests import Request
from selva import di
from selva.web import Middleware


def get_filter(request: Request) -> str:
    todo_filter = request.query.get("filter")

    if not todo_filter and request.path != "/":
        if referer := request.headers.get("Referer"):
            todo_filter_list = parse_qs(urlparse(referer).query).get("filter")
            todo_filter = todo_filter_list[0] if todo_filter_list else None

    return todo_filter


def patch_location_header(headers: list[tuple[str, ...]], todo_filter: str):
    for i, header in enumerate(headers, 0):
        header_name, header_value = header

        if header_name != b"location":
            continue

        location = urlparse(header_value)
        query = parse_qs(location.query)

        if todo_filter:
            query["filter"] = todo_filter
            location = location._replace(query=urlencode(query, doseq=True).encode())

        headers[i] = (header_name, location.geturl())


@di.service
class TodoFilterMiddleware(Middleware):
    async def __call__(self, call_next, request: Request):
        todo_filter = get_filter(request)
        request["todo_filter"] = todo_filter

        async def send(orig, event: dict):
            if (
                todo_filter
                and event["type"] == "http.response.start"
                and event["status"] == HTTPStatus.SEE_OTHER
            ):
                patch_location_header(event["headers"], todo_filter)

            await orig(event)

        request.wrap_asgi(send=send)
        await call_next(request)
