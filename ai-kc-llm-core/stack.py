from aws_cdk import (
    App, Duration, Stack,
    aws_lambda as lambda_,
    aws_sqs as sqs,
    aws_lambda_event_sources as event_sources,
    aws_apigateway as apigateway, 
)
import config


class SlackBotApp(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        queue = sqs.Queue(
            self, 
            config.config.MESSAGE_QUEUE_NAME, 
            queue_name=config.config.MESSAGE_QUEUE_NAME,
            visibility_timeout=Duration.minutes(2)
        )

        layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "OpenAILayer",
            layer_version_arn=config.config.OPENAI_LAYER_ARN
        )

        layerAtlassian = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "AtlassianLayer",
            layer_version_arn=config.config.ATLASSIAN_LAYER_ARN
        )

        # Reader lambda
        handler = lambda_.Function(self, "llm",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("dist_reader/lambda.zip"),
            handler="llm.lambda_handler",
            layers=[layer],
            timeout=Duration.minutes(1),
            memory_size=1024
        )
        queue.grant_consume_messages(handler)
        handler.add_event_source(event_sources.SqsEventSource(queue))

        # Lambda load info
        handlerInfo = lambda_.Function(self, "loadInfo",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("dist_reader/lambda.zip"),
            handler="loadInfo.handler",
            layers=[layer, layerAtlassian],
            timeout=Duration.minutes(10)
        )

        api = apigateway.RestApi(self, "knowledge-center",
            rest_api_name="knowledge",
            description="",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS
            )
        )

        post_integration = apigateway.LambdaIntegration(handlerInfo)

        api.root.add_method(
            "POST", 
            post_integration
        )


app = App()
SlackBotApp(app, "usrv-knowledge-center")
app.synth()