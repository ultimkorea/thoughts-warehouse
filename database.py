from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, ForeignKey, select, update, delete
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # 👈 Добавляем импорт
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///thoughts.db"

# Создание асинхронного движка SQLite
engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

class Thought(Base):
    __tablename__ = "thoughts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tag_id: Mapped[int | None] = mapped_column(ForeignKey("tags.id"), nullable=True)
    image_path: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    tag = relationship("Tag", lazy="joined")  # 👈 Добавляем связь

# Инициализация БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_tag(name: str) -> int:
    """Добавляет тег в нижнем регистре, если его ещё нет"""
    name = name.strip().lower()  # 👈 Приводим к нижнему регистру

    async with async_session() as session:
        existing_tag = await session.execute(select(Tag).where(Tag.name == name))
        tag = existing_tag.scalar()

        if tag:
            return tag.id  # Тег уже существует

        new_tag = Tag(name=name)
        session.add(new_tag)
        await session.commit()
        return new_tag.id


async def get_all_tags() -> list[Tag]:
    """Получает список всех тегов"""
    async with async_session() as session:
        result = await session.execute(select(Tag))
        return result.scalars().all()

async def update_thought_tag(thought_id: int, tag_id: int):
    """Присваивает тег мысли"""
    async with async_session() as session:
        await session.execute(update(Thought).where(Thought.id == thought_id).values(tag_id=tag_id))
        await session.commit()

async def save_thought(user_id: int, text: str, image_path: str | None = None) -> int:
    """Сохраняет мысль в БД"""
    async with async_session() as session:
        thought = Thought(user_id=user_id, text=text, image_path=image_path)
        session.add(thought)
        await session.commit()
        return thought.id

async def get_all_thoughts():
    """Возвращает все мысли"""
    async with async_session() as session:
        result = await session.execute(select(Thought).order_by(Thought.created_at.desc()))
        return result.scalars().all()


async def get_tag_usage_counts():
    """Возвращает список тегов с количеством их использования"""
    async with async_session() as session:
        result = await session.execute(
            select(Tag.id, Tag.name, func.count(Thought.id).label("usage_count"))
            .outerjoin(Thought, Thought.tag_id == Tag.id)
            .group_by(Tag.id)
            .order_by(func.count(Thought.id).desc())  # Сортируем по убыванию
        )
        return result.mappings().all()

async def update_thought_text(thought_id: int, new_text: str):
    """Обновляет текст мысли"""
    async with async_session() as session:
        await session.execute(
            update(Thought).where(Thought.id == thought_id).values(text=new_text)
        )
        await session.commit()

async def delete_thought(thought_id: int):
    """Удаляет мысль"""
    async with async_session() as session:
        await session.execute(delete(Thought).where(Thought.id == thought_id))
        await session.commit()

async def get_thoughts_by_tag(tag_name: str):
    """Возвращает мысли, которые имеют указанный тег"""
    async with async_session() as session:
        result = await session.execute(
            select(Thought)
            .join(Tag, Thought.tag_id == Tag.id)
            .where(Tag.name == tag_name.lower())  # Приводим к нижнему регистру
            .order_by(Thought.created_at.desc())
        )
        return result.scalars().all()
