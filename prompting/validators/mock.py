# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Opentensor Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import torch
import asyncio
import bittensor as bt
from prompting.validators.prompts import FirewallPrompt, FollowupPrompt, AnswerPrompt
from prompting.validators.gating import BaseGatingModel
from prompting.validators.reward import BaseRewardModel
from typing import List


class MockGatingModel(BaseGatingModel):
    def __init__(self, num_uids: int):
        super(MockGatingModel, self).__init__()

        self.num_uids = num_uids
        self.linear = torch.nn.Linear(256, 10)

    def forward(self, message: str) -> "torch.FloatTensor":
        return torch.randn(self.num_uids)

    def backward(self, scores: torch.FloatTensor, rewards: torch.FloatTensor):
        return torch.tensor(0.0)

    def resync(
        self,
        previous_metagraph: "bt.metagraph.Metagraph",
        metagraph: "bt.metagraph.Metagraph",
    ):
        pass


class MockRewardModel(BaseRewardModel):
    question_blacklist = []
    answer_blacklist = []

    @property
    def name(self) -> str:
        return self.mock_name

    def __init__(self, mock_name: str = "MockReward"):
        super().__init__()
        self.mock_name = mock_name
        self.question_blacklist = []
        self.answer_blacklist = []

    def apply(self, prompt: str, completion: List[str], name: str) -> torch.FloatTensor:
        mock_reward = torch.tensor([1 for _ in completion], dtype=torch.float32)
        return mock_reward, mock_reward

    def reset(self):
        return self

    def reward(
        self,
        completions_with_prompt: List[str],
        completions_without_prompt: List[str],
        difference=False,
        shift=3,
    ) -> torch.FloatTensor:
        return torch.zeros(len(completions_with_prompt))


class MockDendriteResponse:
    class mock_status:
        status_code = 200

    completion = ""
    status_message = "Success"
    status_code = "1"
    elapsed_time = 0
    is_success = True
    firewall_prompt = FirewallPrompt()
    followup_prompt = FollowupPrompt()
    answer_prompt = AnswerPrompt()
    dendrite = mock_status()

    def __init__(self, message: str):
        if self.firewall_prompt.matches_template(message):
            self.completion = self.firewall_prompt.mock_response()
        elif self.followup_prompt.matches_template(message):
            self.completion = self.followup_prompt.mock_response()
        elif self.answer_prompt.matches_template(message):
            self.completion = self.answer_prompt.mock_response()
        else:
            self.completion = "The capital of Texas is Austin."

    def __str__(self):
        return f"MockDendriteResponse({self.completion})"

    def __repr__(self):
        return f"MockDendriteResponse({self.completion})"


class MockDendrite(torch.nn.Module):
    async def query(self, synapse, axons, timeout):
        async def test():
            await asyncio.sleep(0.01)
            return [MockDendriteResponse(synapse.messages[0]) for _ in axons]

        return await test()

    def resync(self, metagraph):
        pass

    async def async_backward(
        self,
        uids: List[int],
        roles: List[str],
        messages: List[str],
        completions: List[str],
        rewards: List[float],
    ):
        async def query():
            await asyncio.sleep(0.01)
            return [MockDendriteResponse(messages[0]) for _ in uids]

        return await query()
