const axios = require("axios");

export const handler = async (event, context) => {
  console.log(event);
  console.log(event.answer);
  const query = "```" + `${event.text}` + "```";

  await axios({
    method: "post",
    url: "https://api.openai.com/v1/chat/completions",
    headers: {
      Authorization: `${process.env.OPENAI_API_KEY}`,
    },
    data: {
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "eres un analista de cadenas de texto",
        },
        {
          role: "user",
          content: `de la siguiente respuesta '${event.answer}' Puedes decirme si es una respuesta que indica que la respuesta no se sabe? Respondeme solo con si o no`,
        },
      ],
    },
  }).then(async (resp) => {
    if (
      resp.data.choices[0].message.content == "Sí." ||
      resp.data.choices[0].message.content == "Sí"
    ) {
      await axios({
        method: "post",
        url: "https://slack.com/api/chat.postMessage",
        headers: {
          Authorization: `${process.env.SLACK_TOKEN}`,
        },
        responseType: "stream",
        data: {
          channel: "C05ARPHHF41",
          attachments: [
            {
              text: `<!channel> El usuario <@${event.user}> realizó la siguiente pregunta: ${query} alguien puede contestarla?`,
              fallback: "Responder a Knowledge Center",
              callback_id: "knowledge_answer",
              color: "#3AA3E3",
              attachment_type: "default",
              actions: [
                {
                  name: "answer",
                  text: "Responder",
                  type: "button",
                  value: "answer",
                },
              ],
            },
          ],
        },
      });
    }
  });

  console.log("EVENT: \n" + JSON.stringify(event));
  return "";
};
