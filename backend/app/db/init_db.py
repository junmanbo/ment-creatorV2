"""
데이터베이스 초기화
"""

import asyncio

from sqlalchemy import select, text

from app.core.config import settings
from app.core.security import security
from app.db.session import AsyncSessionLocal, async_engine


async def init_database() -> None:
    """데이터베이스 초기화"""

    print(f"🔧 Environment: {settings.ENVIRONMENT}")

    # 테이블 생성 (개발 환경에서만)
    if settings.ENVIRONMENT == "development":
        try:
            from app.db.base import Base

            # 모든 모델을 명시적으로 import해서 SQLAlchemy가 인식하도록 함
            print("📦 Importing models...")

            print(f"📊 Found {len(Base.metadata.tables)} tables to create:")
            for table_name in Base.metadata.tables:
                print(f"  - {table_name}")

            print("🚀 Creating tables...")
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            print("✅ Database tables created successfully")

            # 테이블 생성 확인
            async with AsyncSessionLocal() as session:
                # PostgreSQL에서 테이블 목록 조회
                result = await session.execute(
                    text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                )
                tables = result.fetchall()
                print("📋 Created tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")

        except Exception as e:
            print(f"❌ Error during table creation: {e}")
            import traceback

            traceback.print_exc()
            raise
    else:
        print(f"⚠️ Skipping table creation (environment: {settings.ENVIRONMENT})")

    # 기본 관리자 계정 생성
    print("👤 Creating initial admin user...")
    await create_initial_admin()


async def create_initial_admin() -> None:
    """초기 관리자 계정 생성"""
    from app.models.user import User
    from app.utils.constants import UserRole

    async with AsyncSessionLocal() as session:
        # 기존 관리자 확인
        result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
        existing_admin = result.scalars().first()

        if not existing_admin:
            # 관리자 계정 생성
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Administrator",
                hashed_password=security.get_password_hash("admin123!"),
                role=UserRole.ADMIN,
                department="IT",
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            print("✅ Initial admin user created: admin / admin123!")


async def check_database_connection() -> bool:
    """데이터베이스 연결 확인"""
    try:
        async with AsyncSessionLocal() as session:
            # text()를 사용하여 명시적으로 SQL 문 지정
            await session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(init_database())
