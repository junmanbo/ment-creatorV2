"""
사용자 서비스
"""


from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, ValidationError
from app.core.security import security
from app.models.user import User
from app.schemas.user import UserChangePassword, UserCreate, UserUpdate
from app.services.base import BaseService
from app.utils.constants import UserRole


class UserService(BaseService[User]):
    """사용자 서비스"""

    def __init__(self):
        super().__init__(User)

    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """사용자 생성"""
        # 중복 확인
        await self._check_duplicate_user(db, user_in.username, user_in.email)

        # 비밀번호 해시화
        hashed_password = security.get_password_hash(user_in.password)

        # 사용자 생성
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password

        return await self.create(db, obj_in=user_data)

    async def update_user(
        self, db: AsyncSession, *, user_id: int, user_in: UserUpdate
    ) -> User:
        """사용자 정보 수정"""
        user = await self.get_or_404(db, user_id)

        # 업데이트 데이터에서 None이 아닌 값만 추출
        update_data = user_in.model_dump(exclude_unset=True)

        return await self.update(db, db_obj=user, obj_in=update_data)

    async def change_password(
        self, db: AsyncSession, *, user_id: int, password_data: UserChangePassword
    ) -> User:
        """비밀번호 변경"""
        user = await self.get_or_404(db, user_id)

        # 현재 비밀번호 확인
        if not security.verify_password(
            password_data.current_password, user.hashed_password
        ):
            raise ValidationError("현재 비밀번호가 올바르지 않습니다.")

        # 새 비밀번호 해시화
        new_hashed_password = security.get_password_hash(password_data.new_password)

        return await self.update(
            db, db_obj=user, obj_in={"hashed_password": new_hashed_password}
        )

    async def get_user_by_username(
        self, db: AsyncSession, username: str
    ) -> User | None:
        """사용자명으로 사용자 조회"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        """이메일로 사용자 조회"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def search_users(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        department: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """사용자 검색"""
        query = select(User)
        count_query = select(func.count(User.id))

        # 검색 조건 적용
        conditions = []

        if search:
            conditions.append(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                )
            )

        if role:
            conditions.append(User.role == role)

        if department:
            conditions.append(User.department.ilike(f"%{department}%"))

        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # 정렬 및 페이징
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)

        # 실행
        users_result = await db.execute(query)
        count_result = await db.execute(count_query)

        users = users_result.scalars().all()
        total = count_result.scalar()

        return users, total

    async def activate_user(self, db: AsyncSession, user_id: int) -> User:
        """사용자 활성화"""
        user = await self.get_or_404(db, user_id)
        return await self.update(db, db_obj=user, obj_in={"is_active": True})

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> User:
        """사용자 비활성화"""
        user = await self.get_or_404(db, user_id)
        return await self.update(db, db_obj=user, obj_in={"is_active": False})

    async def _check_duplicate_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        exclude_id: int | None = None,
    ) -> None:
        """중복 사용자 확인"""
        query = select(User).where(or_(User.username == username, User.email == email))

        if exclude_id:
            query = query.where(User.id != exclude_id)

        result = await db.execute(query)
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.username == username:
                raise DuplicateError("이미 존재하는 사용자명입니다.")
            if existing_user.email == email:
                raise DuplicateError("이미 존재하는 이메일입니다.")
