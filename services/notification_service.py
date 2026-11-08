"""
Hostel Complaint Management System (HCMS)
Notification Service (services/notification_service.py)
"""

from db import query_one, query_all, execute_dml

class NotificationService:

    @staticmethod
    def get_user_notifications(user_id: int, limit: int = 30) -> list:
        """Retrieves in-app notifications for the specified user."""
        sql = """
            SELECT n.*, c.ticket_number 
            FROM notifications n
            LEFT JOIN complaints c ON n.complaint_id = c.complaint_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
        """
        return query_all(sql, (user_id, limit))

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Marks a single notification as read."""
        sql = "UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s"
        rows, _ = execute_dml(sql, (notification_id, user_id))
        return rows > 0

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Marks all notifications for a user as read."""
        sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0"
        rows, _ = execute_dml(sql, (user_id,))
        return rows
