import { parse } from "querystring";
import { get } from "lodash";
import * as AWS from "aws-sdk";

const axios = require("axios");

export interface SlackWebhookRequest {
  type: string;
  user: {
    id: string;
    username: string;
    name: string;
    team_id: string;
    [k: string]: any;
  };
  api_app_id: string;
  token: string;
  container: {
    type: string;
    message_ts: string;
    channel_id: string;
    is_ephemeral: boolean;
    [k: string]: any;
  };
  trigger_id: string;
  team: {
    id: string;
    domain: string;
    [k: string]: any;
  };
  action_ts: string;
  enterprise: null;
  is_enterprise_install: boolean;
  channel: {
    id: string;
    name: string;
    [k: string]: any;
  };
  message: {
    type: string;
    subtype: string;
    text: string;
    ts: string;
    bot_id: string;
    blocks: [
      {
        type: string;
        block_id: string;
        text: {
          type: string;
          text: string;
          verbatim: boolean;
          [k: string]: any;
        };
        accessory: {
          type: string;
          action_id: string;
          placeholder: {
            type: string;
            text: string;
            emoji: boolean;
            [k: string]: any;
          };
          options: [
            {
              text: {
                type: string;
                text: string;
                emoji: boolean;
                [k: string]: any;
              };
              value: string;
              [k: string]: any;
            },
            {
              text: {
                type: string;
                text: string;
                emoji: boolean;
                [k: string]: any;
              };
              value: string;
              [k: string]: any;
            },
            {
              text: {
                type: string;
                text: string;
                emoji: boolean;
                [k: string]: any;
              };
              value: string;
              [k: string]: any;
            }
          ];
          [k: string]: any;
        };
        [k: string]: any;
      }
    ];
    [k: string]: any;
  };
  state: {
    values: {
      section678: {
        text1234: {
          type: string;
          selected_option: {
            text: {
              type: string;
              text: string;
              emoji: boolean;
              [k: string]: any;
            };
            value: string;
            [k: string]: any;
          };
          [k: string]: any;
        };
        [k: string]: any;
      };
      [k: string]: any;
    };
    [k: string]: any;
  };
  response_url: string;
  actions: [
    {
      type: string;
      action_id: string;
      block_id: string;
      selected_option: {
        text: {
          type: string;
          text: string;
          emoji: boolean;
          [k: string]: any;
        };
        value: string;
        [k: string]: any;
      };
      placeholder: {
        type: string;
        text: string;
        emoji: boolean;
        [k: string]: any;
      };
      action_ts: string;
      [k: string]: any;
    }
  ];
  callback_id: string;
  action_id: string;
  value: string;

  [k: string]: any;
}

export const handler = async (event, context) => {
  const payload = parse(event.body);
  const body: SlackWebhookRequest = JSON.parse(
    get(<object>payload, "payload", "")
  );

  console.log(body);

  if (get(body, "type", "") === "view_submission") {
    const blockId = body.view.blocks[0].block_id;
    const key_value = Object.keys(body.view.state.values[blockId])[0];
    const user = key_value.split("_")[1];

    console.log("BLOCKS: \n" + JSON.stringify(body.view.blocks));
    console.log("STATE: \n" + JSON.stringify(body.view.state));
    console.log(
      "RESPUESTA: \n" +
        JSON.stringify(body.view.state.values[blockId][key_value].value)
    );

    const responseToLoad = body.view.state.values[blockId][key_value].value;
    let type = "text";
    let value = responseToLoad;
    let url = "";

    if (isValidHttpUrl(responseToLoad)) {
      type = await typeOfPage(responseToLoad);
      url = responseToLoad;
      value = getValue(type, url);
    }

    let params = {
      FunctionName: "usrv-knowledge-center-loadInfoC818B6CF-nvTOyQoHb9Kn",
      InvocationType: "Event",
      Payload: JSON.stringify({
        body: JSON.stringify({
          type: type,
          value: value,
          url: url,
        }),
      }),
    };
    AWS.config.region = "us-east-1";
    const lambda = new AWS.Lambda();
    const lambdaResult = await lambda.invoke(params).promise();
    const response = "```" + value + "```";

    await axios({
      method: "post",
      url: "https://slack.com/api/chat.postMessage",
      headers: {
        Authorization: `${process.env.SLACK_TOKEN}`,
      },
      data: {
        channel: user,
        text: `El usuario <@${body.user.id}> respondió lo siguiente: ${response}. Y ya ha sido agregado a mi base de datos.`,
      },
    });

    console.log("LAMBDA RESPONSE: \n" + JSON.stringify(lambdaResult));
  } else if (get(body, "actions[0].value", "") === "answer") {
    console.log(body.original_message.attachments);
    const question = body.original_message.attachments[0].text
      .split("```")[1]
      .split("```")[0];
    const user = body.original_message.attachments[0].text
      .split("<")[2]
      .split(">")[0]
      .replace("@", "");

    await axios({
      method: "post",
      url: "https://slack.com/api/views.open",
      headers: {
        Authorization: `${process.env.SLACK_TOKEN}`,
      },
      responseType: "stream",
      data: {
        trigger_id: body.trigger_id,
        view: {
          blocks: [
            {
              element: {
                action_id: `answer_${user}`,
                type: "plain_text_input",
                multiline: true,
                placeholder: {
                  type: "plain_text",
                  text: "Respuesta",
                },
              },
              label: {
                emoji: true,
                text: question,
                type: "plain_text",
              },
              type: "input",
            },
          ],
          submit: {
            text: "Responder",
            type: "plain_text",
          },
          title: {
            emoji: true,
            text: "Responder",
            type: "plain_text",
          },
          type: "modal",
        },
      },
    }).then(function (response) {
      console.log(response.data);
    });
  }

  console.log("EVENT: \n" + JSON.stringify(body));
  return {
    statusCode: 200,
  };
};

async function typeOfPage(url) {
  let rs = "website";

  if (url.includes("kushki.atlassian.net/wiki")) rs = "confluence";

  if (url.includes("docs.google.com")) rs = "gdrive";

  return rs;
}

function isValidHttpUrl(string) {
  let url;

  try {
    url = new URL(string);
  } catch (_) {
    return false;
  }

  return url.protocol === "http:" || url.protocol === "https:";
}

function getValue(urlType, url) {
  let value = "";

  if (urlType == "confluence") {
    const splitText = url.split("/");
    value = splitText[7];
  }

  if (urlType == "gdrive") {
    const splitText = url.split("/");
    value = splitText[5];
  }

  return value;
}
