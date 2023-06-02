package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type ItemMongoUrl struct {
	ID  primitive.ObjectID `bson:"_id"`
	URL string             `bson:"url"`
}

type GenericResponse struct {
	MessageCode string
}

type Event struct {
	URL string `json:"url"`
}

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	var event Event
	json.Unmarshal([]byte(request.Body), &event)

	csURI := os.Getenv("MONGO_CONNECTION_STRING")
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(csURI))

	if err != nil {
		panic(err)
	}

	defer func() {
		if err := client.Disconnect(ctx); err != nil {
			panic(err)
		}
	}()

	coll := client.Database("knowledge_base").Collection("info")

	var item ItemMongoUrl

	err = coll.FindOne(context.TODO(), bson.D{
		{"url", event.URL},
	}).Decode(&item)

	rs := &GenericResponse{MessageCode: "01"}

	if err != nil {
		if err == mongo.ErrNoDocuments {
			rs.MessageCode = "00"
		}
	}

	fmt.Print(item)

	jsonResponse, _ := json.Marshal(rs)

	return events.APIGatewayProxyResponse{Body: string(jsonResponse), StatusCode: 200}, nil
}

func main() {
	lambda.Start(handler)
}
