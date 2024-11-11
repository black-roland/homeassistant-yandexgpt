"""YandexART wrapper."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import aiohttp


# TODO: Replace with the official SDK:
# https://github.com/yandex-cloud/yandex-cloud-ml-sdk/tree/master/examples/async/image_generation
class YandexArt:
    """YandexART wrapper."""

    def __init__(self, folder_id, api_key):
        self.folder_id = folder_id
        self.api_key = api_key

    async def generate(self, seed: str, prompt: str):

        operation_id = None

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
                headers=self._request_headers,
                json=self._build_request_payload(seed, prompt),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    operation_id = data["id"]
                else:
                    data = await resp.text()
                    raise Exception(
                        f"Failed to send async request, status code: {resp.status}"
                    )

            return await self._poll_for_results(self._request_headers, operation_id)

    def _build_request_payload(self, seed, prompt):
        return {
            "modelUri": f"art://{self.folder_id}/yandex-art/latest",
            "generationOptions": {
                "seed": seed,
                "aspectRatio": {
                    "widthRatio": "16",
                    "heightRatio": "9",
                },
            },
            "messages": [
                {
                    "weight": "1",
                    "text": prompt,
                }
            ],
        }

    @property
    def _request_headers(self):
        return {
            "Accept": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
        }

    async def _poll_for_results(self, headers, operation_id):
        async with aiohttp.ClientSession() as session:
            end_time = asyncio.get_event_loop().time() + 30
            while True:
                if asyncio.get_event_loop().time() > end_time:
                    raise TimeoutError("Operation timed out after 30 seconds")

                async with session.get(
                    f"https://llm.api.cloud.yandex.net/operations/{operation_id}",
                    headers=headers,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("done", False):
                            return data["response"]["image"]
                    else:
                        raise Exception(
                            f"Failed to poll operation status, status code: {resp.status}"
                        )
                await asyncio.sleep(1)
