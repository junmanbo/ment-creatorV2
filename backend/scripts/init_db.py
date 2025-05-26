# scripts/init_db.py
"""
데이터베이스 초기화 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.db.init_db import init_database
from app.utils.logger import logger


async def main():
    """메인 함수"""
    try:
        logger.info("🔄 Initializing database...")
        await init_database()
        logger.info("✅ Database initialization completed successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
