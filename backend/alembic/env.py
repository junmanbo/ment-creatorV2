# alembic/env.py
"""
Alembic 환경 설정
"""
import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context

# Alembic Config 객체 - 이 객체는 .ini 파일의 값들에 접근할 수 있게 해줍니다.
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델의 MetaData 객체를 추가합니다 - 'autogenerate' 지원을 위해
# 모든 모델을 import해야 합니다
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.core.config import settings

# 모든 모델 import (나중에 모델 구현 후 추가)
# from app.models import user, scenario, voice_actor, tts, deployment, audit

target_metadata = Base.metadata

def get_url():
    return str(settings.DATABASE_URL_SYNC)

def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())