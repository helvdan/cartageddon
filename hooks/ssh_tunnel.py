import logging
from typing import Any, List, Optional
# pip install sshtunnel
from sshtunnel import SSHTunnelForwarder

from artifacts import Artifact
from hooks.base import BaseHook

logger = logging.getLogger("HOOK.SSH")


class SSHTunnelHook(BaseHook):
    # Гарантирует закрытие туннеля, даже если стадия упала с ошибкой
    run_anyway: bool = True

    def __init__(
            self,
            ssh_host: str,
            ssh_username: str,
            remote_port_address: tuple,  # Например, ('127.0.0.1', 5432) для удаленной БД
            ssh_pkey_path: Optional[str] = None,  # Путь к ключу, например, '~/.ssh/id_rsa'
            ssh_password: Optional[str] = None
    ):
        self.ssh_host = ssh_host
        self.ssh_username = ssh_username
        self.remote_port_address = remote_port_address
        self.ssh_pkey_path = ssh_pkey_path
        self.ssh_password = ssh_password

        # Переменная для хранения активной сессии между Before и After фазами
        self._tunnel: Optional[SSHTunnelForwarder] = None

    def run_before(self, stage: Any, artifacts: List[Artifact]) -> None:
        logger.info(f"[{stage.name}] Инициализация SSH-туннеля до {self.ssh_host}...")
        try:
            self._tunnel = SSHTunnelForwarder(
                ssh_address_or_host=self.ssh_host,
                ssh_username=self.ssh_username,
                ssh_pkey=self.ssh_pkey_path,
                ssh_password=self.ssh_password,
                remote_bind_address=self.remote_port_address,
                # 0 заставляет ОС выдать любой случайный свободный порт.
                # Это защищает от конфликтов, если параллельно идут другие стадии или пайплайны.
                local_bind_address=('127.0.0.1', 0)
            )
            self._tunnel.start()

            # Достаем порт, который нам выделила операционная система
            allocated_port = self._tunnel.local_bind_port
            logger.info(f"[{stage.name}] SSH-туннель успешно поднят на локальном порту: {allocated_port}")

            # Передаем динамический порт в контекст конкретной стадии,
            # чтобы код внутри stage.run() знал, куда коннектиться
            context = stage.get_context()
            context.ssh_local_port = allocated_port

        except Exception as e:
            logger.error(f"[{stage.name}] Критическая ошибка при запуске SSH-туннеля: {e}")
            if self._tunnel:
                self._tunnel.stop()
            raise e

    def run_after(self, stage: Any, artifacts: List[Artifact]) -> None:
        if self._tunnel and self._tunnel.is_active:
            logger.info(f"[{stage.name}] Закрытие SSH-туннеля и освобождение порта {self._tunnel.local_bind_port}...")
            self._tunnel.stop()
            logger.info(f"[{stage.name}] SSH-туннель успешно закрыт.")
        else:
            logger.debug(f"[{stage.name}] Вызван run_after для SSH, но активный туннель отсутствует.")
