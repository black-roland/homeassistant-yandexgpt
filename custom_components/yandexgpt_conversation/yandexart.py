"""YandexART wrapper."""

# flake8: noqa: F501

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# This file is based on allseeteam/yandexgpt-python and incorporates
# work covered by the following copyright and permission notice:
#
# Copyright (c) 2024 ALL SEE LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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
