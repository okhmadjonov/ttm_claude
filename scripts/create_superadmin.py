import getpass

from pydantic import ValidationError

from app.core.database import SessionLocal
from app.modules.auth import service
from app.modules.auth.models import UserRole
from app.modules.auth.schemas import UserCreate


def main() -> None:
    username = input("Username: ").strip()
    full_name = input("Full name: ").strip()
    password = getpass.getpass("Password (min 8 characters): ")
    repeat = getpass.getpass("Repeat password: ")

    if password != repeat:
        print("Passwords do not match")
        return

    try:
        data = UserCreate(
            full_name=full_name,
            username=username,
            password=password,
            role=UserRole.superadmin,
        )
    except ValidationError as e:
        print("Invalid data:")
        for error in e.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")
        return

    with SessionLocal() as db:
        try:
            user = service.create_user(db, data)
        except service.UserRuleError as e:
            print(f"Error: {e}")
            return
        print(f"Superadmin created: id={user.id}, username={user.username}")


if __name__ == "__main__":
    main()