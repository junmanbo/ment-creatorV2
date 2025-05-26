#!/bin/bash

# 코드 포맷팅
echo 'ruff 포맷팅...'
uv run ruff format app/

# 타입 체킹
echo 'ruff 타입 체킹...'
uv run ruff check app/ --fix

# 테스트 실행
#uv run pytest
