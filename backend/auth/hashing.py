from passlib.context import CryptContext

# CryptContext tells passlib which hashing algorithm to use
# bcrypt is the industry standard for password hashing
# It is intentionally slow to make brute force attacks harder
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Takes a plain text password and returns a hashed version.
    We call this when a user registers.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain text password matches a stored hash.
    Returns True if they match, False if not.
    We call this when a user tries to log in.
    """
    return pwd_context.verify(plain_password, hashed_password)