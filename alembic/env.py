from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# DB URL 구성
def get_url():
    user = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_DATABASE")
    port = os.getenv("DB_PORT", "3306")  # 기본 포트
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

from app.db.base import Base

# 모든 모델 파일 임포트 (모델들을 메모리에 로드하고 Base.metadata를 기준으로 자동 생성)
from app.models import privacy, user, verify, file, comment

# Base 모델 구조를 기준으로 revision --autogenerate 해라
target_metadata = Base.metadata

# alembic.ini에 있는 설정 정보를 읽어옴
config = context.config 

# CLI 인자에서 db_url 받아오기
cli_db_url = context.get_x_argument(as_dictionary=True).get("db_url")
if cli_db_url:
    config.set_main_option("sqlalchemy.url", cli_db_url)
else:
    config.set_main_option("sqlalchemy.url", get_url())


# 로그 설정을 초기화 (fileConfig는 Python의 기본 로깅 설정)
if config.config_file_name is not None: 
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
