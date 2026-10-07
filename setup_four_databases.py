from pathlib import Path

from config import LEVEL_DATABASE_PATHS
from services.level_database import (
    initialize_all_level_databases,
)


def main():

    initialize_all_level_databases()

    print("Four independent VeriVote databases initialized.")

    for level, path in LEVEL_DATABASE_PATHS.items():

        exists = Path(path).exists()

        print(
            f"{level:7} -> {path} -> "
            f"{'OK' if exists else 'MISSING'}"
        )


if __name__ == "__main__":
    main()
