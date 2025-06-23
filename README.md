See [description in English](#yandexgpt-integration-for-home-assistant) below 👇
<br>
<br>

# Интеграция YandexGPT для Home Assistant

[![Добавить репозиторий в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-yandexgpt&category=integration) [![Настроить интеграцию с YandexGPT](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandexgpt_conversation)

Ассистент с искусственным интеллектом для вашего умного дома. Интеграция объединяет возможности [YandexGPT](https://ya.ru/ai/gpt) с Home Assistant, позволяя создать полноценную систему управления умным домом с естественным языковым интерфейсом.

## Возможности

- Общение с ассистентом через интерфейс Home Assistant.
- Полноценное управление умным домом: ассистент может не только сообщать состояние устройств, но и управлять ими (включать свет, регулировать температуру и т.д.), а также запускать скрипты и автоматизации ([демо](https://boosty.to/mansmarthome/posts/bb1e2d91-6edb-4dfe-b96f-99de636ce844)).
- Общение с ассистентом через приложение Home Assistant на смартфоне или умных часах.
- Интеграция может служить «мозгом» для создания DIY-умной колонки на базе ESPHome, если помимо YandexGPT добавить в Home Assistant синтез и распознавание речи.
- YandexGPT можно использовать в автоматизациях, например, для создания чат-бота в Telegram.
- Кроме того, интеграция позволяет генерировать изображения с помощью [YandexART](https://ya.ru/ai/art).

YandexGPT — это облачный сервис, плата за который взимается в соответствии с тарифами Yandex Cloud. При первой регистрации [можно получить стартовый грант](https://yandex.cloud/ru/docs/getting-started/usage-grant).

## Установка и настройка

Инструкции по получению ключа API и настройке интеграции можно найти в [wiki](https://github.com/black-roland/homeassistant-yandexgpt/wiki).

TLDR: Добавьте интеграцию, используя голубые кнопки выше, а затем получите [идентификатор каталога](https://yandex.cloud/ru/docs/resource-manager/operations/folder/get-id) и [ключ API](https://yandex.cloud/en/docs/iam/operations/api-key/create). Сервисному аккаунту нужно указать следующие роли: `ai.languageModels.user` и `ai.imageGeneration.user`.

## Примеры использования

Примеры использования можно найти в [моем блоге](https://mansmarthome.info/tags/yandexgpt/). Кроме того, про первую версию интеграции я рассказывал на [YouTube](https://www.youtube.com/watch?v=C1KcW--vnUo).

<p>
  <img src="https://github.com/user-attachments/assets/c4f2520d-a1e7-433b-99d6-9db29b2c99f1" height="340px" alt="Assist" />
  <img src="https://github.com/user-attachments/assets/34f05829-7a10-4087-8596-5087b8310533" height="340px" alt="Morning digests" />
</p>

## Спасибо

Интеграция оказалась полезной? Хотите сказать спасибо? Кофе автору — ваша благодарность. <kbd>[☕ На кофе](https://mansmarthome.info/donate/?utm_source=github&utm_medium=referral&utm_campaign=gpt#donationalerts)</kbd>

Большое спасибо всем, кто меня поддерживает:

![Спасибо][donors-list]

## Уведомление

Это независимая интеграция, разработанная сообществом. Я не связан с Яндексом или Яндекс Облаком. YandexGPT и YandexART — это сервисы, предоставляемые Яндекс Облаком.

Данная интеграция не является официальным продуктом Яндекса и не поддерживается Яндексом.

---

# YandexGPT integration for Home Assistant

[![Add custom repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-yandexgpt&category=integration) [![Set up YandexGPT integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandexgpt_conversation)

AI-powered assistant for your smart home. This integration bridges [YandexGPT](https://yandex.cloud/en/services/yandexgpt) capabilities with Home Assistant, enabling a complete smart home control system with natural language interface.

## Features

- Chat with the assistant directly from Home Assistant's interface.
- Full smart home control: the assistant can not only report device states but also control them (turn lights on/off, adjust temperature, etc.) and execute scripts/automations.
- Chat with the assistant using Home Assistant app on a smartphone or smartwatch.
- Can serve as the "brain" for a DIY smart speaker using ESPHome when combined with speech synthesis/recognition.
- Useful for creating Telegram chatbots and other automations.
- Includes image generation capabilities via YandexART.

YandexGPT is a cloud service with pricing according to Yandex Cloud tariffs.

## Set up

Use blue buttons above to install and configure the integration. Please check out the official documentation on how to retrieve [folder ID](https://yandex.cloud/en/docs/resource-manager/operations/folder/get-id) and [API key](https://yandex.cloud/en/docs/iam/operations/api-key/create). For a service account it's required to set the following roles: `ai.languageModels.user` and `ai.imageGeneration.user`.

## Notice


This is an independent community-developed integration. I'm not affiliated with Yandex or Yandex Cloud in any way. YandexGPT and YandexART are services provided by Yandex Cloud.

This integration is not an official Yandex product and is not supported by Yandex.

[donors-list]: https://github.com/user-attachments/assets/218c7080-14a6-4f35-957d-41ceb0acbd4d
