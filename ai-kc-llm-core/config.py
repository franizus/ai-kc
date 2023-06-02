from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Needed for reading secrets from SecretManager
    # See https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html#ps-integration-lambda-extensions-add
    OPENAI_LAYER_ARN = "arn:aws:lambda:us-east-1:134498530679:layer:layer:1"
    ATLASSIAN_LAYER_ARN = "arn:aws:lambda:us-east-1:134498530679:layer:atlassian:1"

    # Queue name for the slack messages
    MESSAGE_QUEUE_NAME = "llm-message-queue"


config = Config()