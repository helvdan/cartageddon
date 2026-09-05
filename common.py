from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True, kw_only=True)
class RunTimeContext:
    # общие настройки
    work_dir: str
    tables: Optional[List[str]] = None

    # Стадия EXTRACT
    chunk_size: int = 5000

    # Креды для подключения к mysql в Open Cart
    oc_user: Optional[str] = None
    oc_password: Optional[str] = None
    oc_host: Optional[str] = None
    oc_port: Optional[int] = None
    oc_database: Optional[str] = None

    # Креды для подключения к postgresql в django
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None
    pg_host: Optional[str] = None
    pg_port: Optional[int] = None
    pg_database: Optional[str] = None

    # Настройки, влияющие на итоговую структуру таблиц
    single_language: bool = False

    def get_oc_db_config(self):
        return {
            "user": self.oc_user,
            "password": self.oc_password,
            "host": self.oc_host,
            "port": self.oc_port,
            "database": self.oc_database,
        }