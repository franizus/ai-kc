package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httputil"
	"os"

	"github.com/aws/aws-lambda-go/events"
	lambdaMain "github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sqs"
)

type Body struct {
	Event Event `json:"event"` //
}

type Event struct {
	Channel string `json:"channel"`
	User    string `json:"user"`
	Text    string `json:"text"`
}

func handleRequest(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	fmt.Printf("Processing request data for request %s.\n", request.RequestContext.RequestID)
	fmt.Printf("Body:\n", request.Body)
	bodyRequest := Body{}
	sess := session.Must(session.NewSessionWithOptions(session.Options{
		SharedConfigState: session.SharedConfigEnable,
	}))

	json.Unmarshal([]byte(request.Body), &bodyRequest)
	fmt.Printf("Body:\n", request.Body)

	//response to slack
	if bodyRequest.Event.User != "U05A9KR1UCD" {
		body := map[string]interface{}{
			"channel": bodyRequest.Event.Channel,
			"text":    "Estamos procesando tu requerimiento.",
		}

		bodyMarshall, _ := json.Marshal(body)
		var jsonStr = []byte(string(bodyMarshall))

		client := &http.Client{}
		req, _ := http.NewRequest("POST", "https://slack.com/api/chat.meMessage", bytes.NewBuffer(jsonStr))
		req.Header.Add("Authorization", os.Getenv("SLACK_TOKEN"))
		req.Header.Add("Content-Type", "application/json")
		res, _ := client.Do(req)
		defer res.Body.Close()
		respDump, _ := httputil.DumpResponse(res, true)
		fmt.Printf("RESPONSE:\n%s", string(respDump))
		println("STATUS CODE:", res.StatusCode, "\n")

		sqsGtw := sqs.New(sess)
		requestBody, _ := json.Marshal(
			bodyRequest.Event,
		)

		responseSQS, errorSqs := sqsGtw.SendMessage(&sqs.SendMessageInput{
			MessageBody: aws.String(string(requestBody)),
			QueueUrl:    aws.String(os.Getenv("SLACK_FR_SQS")),
		})

		print("COLA", responseSQS.String())
		fmt.Sprintf("RESPONSE SQS: %+v", responseSQS)
		if errorSqs != nil {
			print("ERROR", errorSqs.Error())
			fmt.Sprintf("[LAMBDA ERROR]: %+v", errorSqs)
		}

		println("SENT TO SQS")
	}

	return events.APIGatewayProxyResponse{Body: request.Body, StatusCode: 200}, nil
}

func main() {
	lambdaMain.Start(handleRequest)
}
