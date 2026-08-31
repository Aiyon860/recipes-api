from enum import Enum as PyEnum


class DifficultyEnum(str, PyEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class UserRoleEnum(str, PyEnum):
    superadmin = "superadmin"
    admin_recipe = "admin_recipe"
    admin_tag = "admin_tag"
