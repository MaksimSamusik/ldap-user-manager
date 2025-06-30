import fcntl
import json
import os
import threading
import time
import logging
from datetime import datetime
from django.apps import AppConfig

from expiry_notifier.services.email_service import notify_admins
from expiry_notifier.services.notification_service import send_notification

logger = logging.getLogger(__name__)

class ExpiryNotifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expiry_notifier'
    _lock = threading.Lock()
    _last_run = {}
    _thread_started = False

    def ready(self):
        if self._thread_started:
            return

        lockfile = '/tmp/notifier.lock'
        with open(lockfile, 'w') as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logger.info("Notifier already running in another process")
                return

            self._thread_started = True
            self.start_notifier_thread(f)

    def start_notifier_thread(self, lock_file):
        """Запускает поток для проверки времени"""
        def check_time():
            logger.info("Notifier thread started")
            while True:
                try:
                    with open('config.json', 'r', encoding='utf-8') as file:
                        data = json.load(file)

                    user_time = tuple(map(int, data['notification_time']['automatic_message_all_users'].split(':')))
                    admin_time = tuple(map(int, data['notification_time']['automatic_message_admins'].split(':')))

                    now = datetime.now().time()
                    current_hour_minute = (now.hour, now.minute)

                    with self._lock:
                        if current_hour_minute != self._last_run.get('user') and current_hour_minute == user_time:
                            logger.info("Sending user notifications (pid: %s)", os.getpid())
                            send_notification()
                            self._last_run['user'] = current_hour_minute

                        if current_hour_minute != self._last_run.get('admin') and current_hour_minute == admin_time:
                            logger.info("Sending admin notifications (pid: %s)", os.getpid())
                            notify_admins()
                            self._last_run['admin'] = current_hour_minute

                except Exception as e:
                    logger.error(f"Error in notifier thread: {e}", exc_info=True)
                finally:
                    time.sleep(30)

        thread = threading.Thread(target=check_time, daemon=True)
        thread.start()
        logger.info("Notifier thread started in process %s", os.getpid())