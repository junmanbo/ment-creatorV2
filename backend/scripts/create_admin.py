# scripts/create_admin.py
"""
관리자 계정 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.security import security
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.utils.constants import UserRole
from app.utils.logger import logger


async def create_admin_user():
    """관리자 계정 생성"""
    
    username = input("관리자 사용자명을 입력하세요: ").strip()
    if not username:
        print("❌ 사용자명은 필수입니다.")
        return
    
    email = input("관리자 이메일을 입력하세요: ").strip()
    if not email:
        print("❌ 이메일은 필수입니다.")
        return
    
    full_name = input("관리자 이름을 입력하세요: ").strip()
    if not full_name:
        print("❌ 이름은 필수입니다.")
        return
    
    password = input("비밀번호를 입력하세요: ").strip()
    if not password:
        print("❌ 비밀번호는 필수입니다.")
        return
    
    try:
        async with AsyncSessionLocal() as session:
            # 기존 사용자 확인
            from sqlalchemy import select
            
            # 사용자명 중복 확인
            result = await session.execute(
                select(User).where(User.username == username)
            )
            if result.scalars().first():
                print(f"❌ 사용자명 '{username}'이 이미 존재합니다.")
                return
            
            # 이메일 중복 확인
            result = await session.execute(
                select(User).where(User.email == email)
            )
            if result.scalars().first():
                print(f"❌ 이메일 '{email}'이 이미 존재합니다.")
                return
            
            # 관리자 계정 생성
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=security.get_password_hash(password),
                role=UserRole.ADMIN,
                department="IT",
                is_active=True,
            )
            
            session.add(admin_user)
            await session.commit()
            
            print(f"✅ 관리자 계정이 성공적으로 생성되었습니다.")
            print(f"   사용자명: {username}")
            print(f"   이메일: {email}")
            print(f"   이름: {full_name}")
            
    except Exception as e:
        logger.error(f"관리자 계정 생성 실패: {e}")
        print(f"❌ 관리자 계정 생성에 실패했습니다: {e}")


async def main():
    """메인 함수"""
    print("🔧 관리자 계정 생성 도구")
    print("=" * 40)
    
    try:
        await create_admin_user()
    except KeyboardInterrupt:
        print("\n❌ 작업이 취소되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    asyncio.run(main())