from typing import Annotated

from selva import di
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from .model import Base, Todo


@di.service
class TodoService:
    engine: Annotated[AsyncEngine, di.Inject]
    sessionmaker: Annotated[async_sessionmaker, di.Inject]

    async def initialize(self):
        async with self.engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_all(self) -> list[Todo]:
        async with self.sessionmaker() as session:
            result = await session.execute(select(Todo))
            return list(result.scalars())

    async def get_active(self) -> list[Todo]:
        async with self.sessionmaker() as session:
            result = await session.execute(
                select(Todo).where(Todo.is_completed == False)
            )
            return list(result.scalars())

    async def get_completed(self) -> list[Todo]:
        async with self.sessionmaker() as session:
            result = await session.execute(
                select(Todo).where(Todo.is_completed == True)
            )
            return list(result.scalars())

    async def get_one(self, todo_id: int) -> Todo:
        async with self.sessionmaker() as session:
            return await session.scalar(select(Todo).where(Todo.id == todo_id))

    async def save(self, todo: Todo):
        async with self.sessionmaker() as session:
            session.add(todo)
            await session.commit()

    async def edit(self, todo_id: int, title: str):
        async with self.sessionmaker() as session:
            await session.execute(
                update(Todo).where(Todo.id == todo_id).values(title=title)
            )
            await session.commit()

    async def complete(self, todo_id: int, completed: bool):
        async with self.sessionmaker() as session:
            await session.execute(
                update(Todo).where(Todo.id == todo_id).values(is_completed=completed)
            )
            await session.commit()

    async def complete_all(self, completed: bool):
        async with self.sessionmaker() as session:
            await session.execute(update(Todo).values(is_completed=completed))
            await session.commit()

    async def delete(self, todo_id: int):
        async with self.sessionmaker() as session:
            await session.execute(delete(Todo).where(Todo.id == todo_id))
            await session.commit()

    async def delete_completed(self):
        async with self.sessionmaker() as session:
            await session.execute(delete(Todo).where(Todo.is_completed == True))
            await session.commit()

    async def count(self, is_completed: bool | None = None) -> int:
        async with self.sessionmaker() as session:
            stmt = select(func.count(Todo.id))
            if is_completed is not None:
                stmt = stmt.where(Todo.is_completed == is_completed)

            return await session.scalar(stmt)
