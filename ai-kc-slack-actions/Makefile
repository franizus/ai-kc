BIN_PATH = ./bin
HANDLER_PATH = src/Handler
BUILD_COMMAND = rm -rf node_modules && npm init -y && npm i --only=prod && rm package.json && rm package-lock.json
ZIP_RESOURCES = src/* node_modules/*
build:
	rm -rf bin
	node esbuild.mjs

	mkdir -p $(BIN_PATH)/Handler/$(HANDLER_PATH)
	mkdir -p $(BIN_PATH)/SlackResponse/$(HANDLER_PATH)

	mv $(BIN_PATH)/Handler/Handler.js $(BIN_PATH)/Handler/$(HANDLER_PATH)
	mv $(BIN_PATH)/SlackResponse/SlackResponse.js $(BIN_PATH)/SlackResponse/$(HANDLER_PATH)

	cd $(BIN_PATH)/Handler && $(BUILD_COMMAND)
	cd $(BIN_PATH)/SlackResponse && $(BUILD_COMMAND)

	cd $(BIN_PATH)/Handler && zip -r Handler.zip $(ZIP_RESOURCES)
	cd $(BIN_PATH)/SlackResponse && zip -r SlackResponse.zip $(ZIP_RESOURCES)

	mv $(BIN_PATH)/Handler/Handler.zip $(BIN_PATH)/
	mv $(BIN_PATH)/SlackResponse/SlackResponse.zip $(BIN_PATH)/