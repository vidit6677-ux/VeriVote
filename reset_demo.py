from database import initialize_database, reset_demo_voters


def main():
    print("Initializing database...")

    initialize_database()

    print("Resetting all demo votes...")

    reset_demo_voters()

    print()
    print("======================================")
    print("      DEMO VOTES RESET SUCCESSFULLY")
    print("======================================")
    print("All votes have been deleted.")
    print("All voters can vote again.")
    print("======================================")


if __name__ == "__main__":
    main()