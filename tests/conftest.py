
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env.test")

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing")

url = make_url(TEST_DATABASE_URL)

if url.get_backend_name() != "postgresql":
    raise RuntimeError("Tests require PostgreSQL")

if url.database != "ecommerce_test_db":
    raise RuntimeError("Refusing to use a non-test database")

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

with test_engine.connect() as connection:
    database_name = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if database_name != "ecommerce_test_db":
        raise RuntimeError("Wrong test database connection")

from database.base import Base
import models

from database.connection import get_db
from models.user_model import User
from utils.dependencies import get_current_user
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(setup_database):
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def customer(db_session):
    user = User(
        name="Test Customer",
        email="customer@test.com",
        mobile="9000000001",
        role="customer",
        hashed_password="test-hash"
    )

    db_session.add(user)
    db_session.flush()

    return user


@pytest.fixture
def shopkeeper(db_session):
    user = User(
        name="Test Shopkeeper",
        email="shopkeeper@test.com",
        mobile="9000000002",
        role="shopkeeper",
        hashed_password="test-hash"
    )

    db_session.add(user)
    db_session.flush()

    return user


@pytest.fixture
def admin(db_session):
    user = User(
        name="Test Admin",
        email="admin@test.com",
        mobile="9000000003",
        role="admin",
        hashed_password="test-hash"
    )

    db_session.add(user)
    db_session.flush()

    return user


@pytest.fixture
def mock_login(client):
    def login_as(user):
        app.dependency_overrides[get_current_user] = lambda: user

    return login_as
