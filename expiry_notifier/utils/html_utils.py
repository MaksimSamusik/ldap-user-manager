def format_string(template: str, context: dict) -> str:
    return template.format(**context)


def generate_user_table(users: list) -> str:
    if not users:
        return "<p>No users were notified.</p>"

    rows = [
        f"""
        <tr>
            <td>{idx}</td>
            <td>{user.get('username')}</td>
            <td>{user.get('email')}</td>
            <td>{user.get('days_left')}</td>
            <td>{user.get('stage')}</td>
            <td>{user.get('expiry_date')}</td>
            <td>{user.get('sent_at')}</td>
        </tr>
        """ for idx, user in enumerate(users, 1)
    ]

    return f"""
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Username</th>
                <th>Email</th>
                <th>Days Left</th>
                <th>Stage</th>
                <th>Expiry Date</th>
                <th>Sent At</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """
