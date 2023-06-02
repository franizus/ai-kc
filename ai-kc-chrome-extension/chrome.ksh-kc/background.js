async function checkStatus(url) {
  const data = {
    url: url,
  };

  const response = await fetch(
    "https://5umou7qypvwag4uauzfpfuzwsy0ehfbr.lambda-url.us-east-1.on.aws/",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );

  const jsonData = await response.json();
  const rs = jsonData["MessageCode"] == "01" ? "SI" : "NO";

  return rs;
}

async function saveOnKB(url) {
  chrome.notifications.create("", {
    title: "Kushki Knowledge Center",
    message: "Estamos procesando el documento",
    iconUrl: "/images/icon-48.png",
    type: "basic",
    priority: 10,
  });

  const urlType = await typeOfPage(url);
  let value = url;

  if (urlType == "confluence") {
    const splitText = url.split("/");
    value = splitText[7];
  }

  if (urlType == "gdrive") {
    const splitText = url.split("/");
    value = splitText[5];
  }

  const data = {
    type: urlType,
    value: value,
    url: url,
  };

  const response = await fetch(
    "https://hfjxdcf5zj.execute-api.us-east-1.amazonaws.com/prod",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );

  return response.status;
}

async function typeOfPage(url) {
  let rs = "website";

  if (url.includes("kushki.atlassian.net/wiki")) rs = "confluence";

  if (url.includes("docs.google.com")) rs = "gdrive";

  return rs;
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({
    text: "NO",
  });
});

const extensions = "https://developer.chrome.com/docs/extensions";
const webstore = "https://developer.chrome.com/docs/webstore";

chrome.action.onClicked.addListener(async (tab) => {
  const currentStatus = await checkStatus(tab.url);

  if (currentStatus == "NO") {
    let rs;

    try {
      rs = await saveOnKB(tab.url);

      if (rs == 200) {
        chrome.notifications.create("", {
          title: "Kushki Knowledge Center",
          message: "Haz añadido el documento a nuestra base de conocimiento",
          iconUrl: "/images/icon-48.png",
          type: "basic",
          priority: 10,
        });

        await chrome.action.setBadgeText({
          tabId: tab.id,
          text: "SI",
        });
      }
    } catch (e) {
      chrome.notifications.create("", {
        title: "Kushki Knowledge Center",
        message:
          "Oops no pudimos guardar el documento en nuestra base de conocimiento",
        iconUrl: "/images/icon-48.png",
        type: "basic",
        priority: 10,
      });
    }
  }

  if (currentStatus == "SI") {
    await chrome.action.setBadgeText({
      tabId: tab.id,
      text: await checkStatus(tab.url),
    });

    chrome.notifications.create("", {
      title: "Kushki Knowledge Center",
      message: "Este documento ya se encuentra en nuestra base de Conocimiento",
      iconUrl: "/images/icon-48.png",
      type: "basic",
      priority: 10,
    });
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status == "complete") {
    await chrome.action.setBadgeText({
      tabId: tab.id,
      text: await checkStatus(tab.url),
    });
  }
});
