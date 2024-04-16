from typing import Annotated as A
from urllib.parse import urlparse, parse_qs

from asgikit.requests import Request
from asgikit.responses import respond_redirect_post_get, respond_file
from pydantic import BaseModel
from selva import di, web
from selva.ext.templates.jinja import Template

from application.model import Todo
from application.service import TodoService


class TodoDTO(BaseModel):
    title: str


class TodoCompleteDTO(BaseModel):
    completed: bool = False


@web.controller
class TodoController:
    template: A[Template, di.Inject]
    service: A[TodoService, di.Inject]

    @staticmethod
    def get_filter(request: Request) -> str | None:
        todo_filter = request.query.get("filter")

        if not todo_filter:
            if request.path == "/":
                return None

            if referer := request.headers.get('Referer'):
                todo_filter = parse_qs(urlparse(referer).query).get("filter")
                todo_filter = todo_filter[0] if todo_filter else None

        return todo_filter

    async def get_context(self, request: Request) -> dict:
        todo_filter = self.get_filter(request)

        if todo_filter == "active":
            filtered_todos = await self.service.get_active()
        elif todo_filter == "completed":
            filtered_todos = await self.service.get_completed()
        else:
            filtered_todos = await self.service.get_all()

        todo_count = await self.service.count()
        active_todo_count = await self.service.count(is_completed=False)
        completed_todo_count = await self.service.count(is_completed=True)

        return {
            "todo_count": todo_count,
            "active_todo_count": active_todo_count,
            "completed_todo_count": completed_todo_count,
            "todos": filtered_todos,
            "filter": todo_filter or "all",
        }

    async def redirect(self, request: Request):
        if todo_filter := self.get_filter(request):
            location = f"/?filter={todo_filter}"
        else:
            location = "/"

        await respond_redirect_post_get(request.response, location)

    @web.get
    async def index(self, request: Request):
        context = await self.get_context(request)
        await self.template.respond(request.response, "index.jinja", context)

    @web.get("/favicon.ico")
    async def favicon(self, request: Request):
        await respond_file(request.response, "resources/static/favicon.ico")

    @web.post("todo")
    async def new_todo(self, request: Request, dto: TodoDTO):
        await self.service.save(Todo(title=dto.title))
        await self.redirect(request)

    @web.post("todo/:todo_id/edit")
    async def edit_todo(
        self, request: Request, dto: TodoDTO, todo_id: A[int, web.FromPath]
    ):
        await self.service.edit(todo_id, dto.title)
        await self.redirect(request)

    @web.post("todo/:todo_id/complete")
    async def complete_todo(
        self, request: Request, dto: TodoCompleteDTO, todo_id: A[int, web.FromPath]
    ):
        await self.service.complete(todo_id, dto.completed)
        await self.redirect(request)

    @web.post("todo/complete_all")
    async def complete_all(self, request: Request, dto: TodoCompleteDTO):
        await self.service.complete_all(dto.completed)
        await self.redirect(request)

    @web.post("todo/:todo_id/delete")
    async def delete_todo(self, request: Request, todo_id: A[int, web.FromPath]):
        await self.service.delete(todo_id)
        await self.redirect(request)

    @web.post("todo/delete_completed")
    async def delete_completed(self, request: Request):
        await self.service.delete_completed()
        await self.redirect(request)
