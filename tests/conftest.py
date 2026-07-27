import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.core.database import Base, get_db
from app.models.user import User
from app.models.role import Role
from app.models.offer import Offer, OfferStatus
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.database_url)

# ----------------------------------------------------------------------
# 1. Configuration du Moteur Async (Scope Function)
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Engine propre par test pour éviter les conflits d'event loops asyncpg."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()

# ----------------------------------------------------------------------
# 2. Préparation & Nettoyage de la Base de Données
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database(test_engine):
    """Purge et re-crée la structure de la base avant chaque test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Session SQLAlchemy isolée."""
    testing_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    async with testing_session_maker() as session:
        yield session
        await session.rollback()

# ----------------------------------------------------------------------
# 3. Client HTTP Async
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client httpx pour requêter l'API FastAPI."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

# ----------------------------------------------------------------------
# 4. Rôles, Utilisateurs et Tokens JWT
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def company_role(db_session: AsyncSession) -> Role:
    """Récupère ou crée le rôle company."""
    result = await db_session.execute(select(Role).where(Role.name == "company"))
    role = result.scalars().first()
    if not role:
        role = Role(name="company")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
    return role

@pytest_asyncio.fixture(scope="function")
async def company_user(db_session: AsyncSession, company_role: Role) -> User:
    """Entreprise 1."""
    user = User(
        email="company1@test.com",
        hashed_password=hash_password("password123"),
        role_id=company_role.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user.role = company_role
    return user

@pytest_asyncio.fixture(scope="function")
async def company_user_2(db_session: AsyncSession, company_role: Role) -> User:
    """Entreprise 2 (pour tester l'isolation)."""
    user = User(
        email="company2@test.com",
        hashed_password=hash_password("password123"),
        role_id=company_role.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user.role = company_role
    return user

@pytest.fixture(scope="function")
def company_token(company_user: User) -> str:
    """Token pour l'Entreprise 1 avec rôle en minuscule."""
    return create_access_token(
        subject=str(company_user.id),
        role="company"
    )

@pytest.fixture(scope="function")
def company_token_2(company_user_2: User) -> str:
    """Token pour l'Entreprise 2 avec rôle en minuscule."""
    return create_access_token(
        subject=str(company_user_2.id),
        role="company"
    )

# ----------------------------------------------------------------------
# 5. Offres de Stage (Modèle Offer exact)
# ----------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def company_offer(db_session: AsyncSession, company_user: User) -> Offer:
    """Offre créée par la première entreprise."""
    offer = Offer(
        title="Offre Entreprise 1",
        mission="Mission de test 1",
        skills="Python, FastAPI",
        status=OfferStatus.draft,
        company_id=company_user.id
    )
    db_session.add(offer)
    await db_session.commit()
    await db_session.refresh(offer)
    return offer

@pytest_asyncio.fixture(scope="function")
async def other_company_offer(db_session: AsyncSession, company_user_2: User) -> Offer:
    """Offre créée par la seconde entreprise."""
    offer = Offer(
        title="Offre Entreprise 2",
        mission="Mission de test 2",
        skills="Docker, PostgreSQL",
        status=OfferStatus.draft,
        company_id=company_user_2.id
    )
    db_session.add(offer)
    await db_session.commit()
    await db_session.refresh(offer)
    return offer

@pytest.fixture(scope="function")
def other_company_offer_id(other_company_offer: Offer) -> int:
    """Identifiant numérique de l'offre de la seconde entreprise."""
    return other_company_offer.id

@pytest_asyncio.fixture(scope="function")
async def student_role(db_session: AsyncSession) -> Role:
    result = await db_session.execute(select(Role).where(Role.name == "student"))
    role = result.scalars().first()
    if not role:
        role = Role(name="student")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
    return role

@pytest_asyncio.fixture(scope="function")
async def student_user(db_session: AsyncSession, student_role: Role) -> User:
    user = User(
        email="student1@test.com",
        hashed_password=hash_password("password123"),
        role_id=student_role.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user.role = student_role
    return user

@pytest.fixture(scope="function")
def student_token(student_user: User) -> str:
    return create_access_token(subject=str(student_user.id), role="student")

@pytest_asyncio.fixture(scope="function")
async def program_manager_role(db_session: AsyncSession) -> Role:
    result = await db_session.execute(select(Role).where(Role.name == "program_manager"))
    role = result.scalars().first()
    if not role:
        role = Role(name="program_manager")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
    return role

@pytest_asyncio.fixture(scope="function")
async def program_manager_user(db_session: AsyncSession, program_manager_role: Role) -> User:
    user = User(
        email="pm1@test.com",
        hashed_password=hash_password("password123"),
        role_id=program_manager_role.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user.role = program_manager_role
    return user

@pytest.fixture(scope="function")
def program_manager_token(program_manager_user: User) -> str:
    return create_access_token(subject=str(program_manager_user.id), role="program_manager")