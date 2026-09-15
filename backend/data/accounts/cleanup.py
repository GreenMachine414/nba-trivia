from data.database import db


def main():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("DELETE FROM sessions WHERE created_at <= NOW() - INTERVAL '30 days'")
    deleted_sessions = cursor.rowcount

    cursor.execute("DELETE FROM pending_answers WHERE created_at <= NOW() - INTERVAL '1 hour'")
    deleted_answers = cursor.rowcount

    db.connection.commit()
    cursor.close()

    print(f"Deleted {deleted_sessions} expired sessions.")
    print(f"Deleted {deleted_answers} stale pending answers.")


if __name__ == "__main__":
    main()