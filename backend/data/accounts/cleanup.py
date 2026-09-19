from data.database import db


def main():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("DELETE FROM sessions WHERE created_at <= NOW() - INTERVAL '30 days'")
    deleted_sessions = cursor.rowcount

    db.connection.commit()
    cursor.close()

    print(f"Deleted {deleted_sessions} expired sessions.")


if __name__ == "__main__":
    main()