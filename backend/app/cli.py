import argparse
import getpass
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth import hash_password


def create_user() -> int:
    username = input('Username: ').strip().casefold()
    if not username or len(username) > 80:
        print('Username must be between 1 and 80 characters.', file=sys.stderr)
        return 1

    password = getpass.getpass('Password (at least 5 characters): ')
    confirmation = getpass.getpass('Confirm password: ')
    if len(password) < 5:
        print('Password must be at least 5 characters.', file=sys.stderr)
        return 1
    if len(password) > 256:
        print('Password must be no more than 256 characters.', file=sys.stderr)
        return 1
    if password != confirmation:
        print('Passwords do not match.', file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.username == username)) is not None:
            print('That username already exists.', file=sys.stderr)
            return 1
        db.add(User(username=username, password_hash=hash_password(password), is_active=True))
        db.commit()
    print(f'User {username} created.')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog='python -m app.cli')
    parser.add_argument('command', choices=['create-user'])
    args = parser.parse_args()
    if args.command == 'create-user':
        return create_user()
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
