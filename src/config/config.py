import logging
import os

from pydantic import Extra
from pydantic_settings import BaseSettings

DEFAULT_CONFIG_FILE = os.getenv("CONFIG_FILE", ".env-dev")


class Config(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_name: str
    postgres_host: str
    postgres_port: str

    rabbitmq_host: str
    rabbitmq_user: str
    rabbitmq_pass: str
    rabbitmq_port_main: int

    flight_api_path: str
    flight_api_key: str
    flight_api_mock: bool

    open_ai_path: str
    open_ai_key: str
    open_ai_mock: bool

    bot_token: str

    class Config:
        extra = Extra.ignore

    @property
    def postgres_url(self):
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_name}"

    @property
    def async_postgres_url(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_name}"

    def __new__(cls, _env_file):
        if not hasattr(cls, "instance"):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance  # noqa


def get_config() -> Config:
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        logging.warning(
            "Config path %s does not exist, environmental variables will be used",
            DEFAULT_CONFIG_FILE,
        )
    return Config(_env_file=DEFAULT_CONFIG_FILE)  # type: ignore
