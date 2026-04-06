from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS / Cognito
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_user_pool_client_id: str = ""

    # RDS PostgreSQL
    database_url: str = "sqlite:///./test.db"

    # S3
    s3_documents_bucket: str = ""

    # SNS
    sns_alerts_topic_arn: str = ""

    # Step Functions
    step_functions_state_machine_arn: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Environment
    app_env: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cognito_jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com"
            f"/{self.cognito_user_pool_id}/.well-known/jwks.json"
        )

    @property
    def cognito_issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com"
            f"/{self.cognito_user_pool_id}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
