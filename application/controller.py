from typing import Annotated

from asgikit.requests import Request
from asgikit.responses import respond_file, respond_redirect_post_get
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
    template: Annotated[Template, di.Inject]
    service: Annotated[TodoService, di.Inject]

    @staticmethod
    async def redirect(request: Request):
        await respond_redirect_post_get(request.response, "/")

    @web.get
    async def index(self, request: Request):
        match todo_filter := request["todo_filter"]:
            case "active":
                filtered_todos = await self.service.get_active()
            case "completed":
                filtered_todos = await self.service.get_completed()
            case _:
                filtered_todos = await self.service.get_all()
                todo_filter = "all"

        todo_count = await self.service.count()
        active_todo_count = await self.service.count(is_completed=False)
        completed_todo_count = await self.service.count(is_completed=True)

        context = {
            "todo_count": todo_count,
            "active_todo_count": active_todo_count,
            "completed_todo_count": completed_todo_count,
            "todos": filtered_todos,
            "filter": todo_filter,
        }

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
        self, request: Request, dto: TodoDTO, todo_id: Annotated[int, web.FromPath]
    ):
        await self.service.edit(todo_id, dto.title)
        await self.redirect(request)

    @web.post("todo/:todo_id/complete")
    async def complete_todo(
        self,
        request: Request,
        dto: TodoCompleteDTO,
        todo_id: Annotated[int, web.FromPath],
    ):
        await self.service.complete(todo_id, dto.completed)
        await self.redirect(request)

    @web.post("todo/:todo_id/delete")
    async def delete_todo(
        self, request: Request, todo_id: Annotated[int, web.FromPath]
    ):
        await self.service.delete(todo_id)
        await self.redirect(request)

    @web.post("todo/complete_all")
    async def complete_all(self, request: Request, dto: TodoCompleteDTO):
        await self.service.complete_all(dto.completed)
        await self.redirect(request)

    @web.post("todo/delete_completed")
    async def delete_completed(self, request: Request):
        await self.service.delete_completed()
        await self.redirect(request)
