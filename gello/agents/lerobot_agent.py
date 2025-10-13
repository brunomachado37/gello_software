import numpy as np
import torch
from contextlib import nullcontext
from typing import Dict
from gello.agents.agent import Agent

import copy

class LeRobotAgent(Agent):
    def __init__(
        self,
        model_id: str,
        policy_type: str,
        task: str,
        device: torch.device = torch.device("cuda"),
        use_amp: bool = False,
        language_model_id: str = "answerdotai/ModernBERT-base"
    ):
        super().__init__()

        if policy_type == 'act':
            from lerobot.policies.act.modeling_act import ACTPolicy
            policy_class = ACTPolicy
        elif policy_type == 'pi0':
            from lerobot.policies.pi0.modeling_pi0 import PI0Policy
            policy_class = PI0Policy
        elif policy_type == 'dif':
            from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy
            policy_class = DiffusionPolicy
        elif policy_type == 'vqbet':
            from lerobot.policies.vqbet.modeling_vqbet import VQBeTPolicy
            policy_class = VQBeTPolicy
        else:
            raise ValueError(f"Unsupported policy_type: {policy_type}")

        self.policy = policy_class.from_pretrained(model_id).to(device)
        self.task = task
        self.device = device
        self.use_amp = use_amp
        self.language_model_id = language_model_id

    def prepare_observation(
        self,
        observation: Dict[str, np.ndarray],
        task: str ,
        robot_type: str = 'franka',
    ) -> Dict[str, torch.Tensor]:
        obs = copy.deepcopy(observation)
        for name in obs:
            obs[name] = torch.from_numpy(obs[name])
            # Ensure float32 dtype for all inputs
            obs[name] = obs[name].float()
            if "image" in name:
                obs[name] = obs[name] / 255.0
                obs[name] = obs[name].permute(2, 0, 1).contiguous()
            obs[name] = obs[name].unsqueeze(0).to(self.device)

        obs["task"] = task if task else ""
        
        obs["robot_type"] = robot_type if robot_type else ""

        return obs

    def act(self, obs: Dict[str, np.ndarray]) -> np.ndarray:
        act_obs = {
            "observation.state": obs["joint_positions"],
        }
        if "wrist_rgb" in obs:
            act_obs["observation.images.wrist_camera"] = obs["wrist_rgb"]
        if "side_rgb" in obs:
            act_obs["observation.images.side_camera"] = obs["side_rgb"]
        if "task_embed" in obs:
            act_obs["task_embed"]  = obs["task_embed"]
        observation = self.prepare_observation(act_obs, task=self.task, robot_type='franka')
        with torch.inference_mode(), \
            torch.autocast(device_type=self.device.type) if (self.device.type == "cuda" and self.use_amp) else nullcontext():
            action = self.policy.select_action(observation)
            action = action.squeeze(0).to("cpu").numpy()

        return action

    def get_language_embedding(self):
        self._load_language_model()

        with torch.no_grad():
            language_input = self.language_tokenizer(self.task, return_tensors="pt", padding="max_length", truncation=True)
            language_input = {k: v.to(self.language_model.device) for k, v in language_input.items()}
            language_embedding = self.language_model(**language_input, output_hidden_states=True).hidden_states[-1]
            language_embedding = language_embedding[0, 0, :].cpu().numpy() # Get the first token (CLS token)

        return language_embedding

    def _load_language_model(self):
        if hasattr(self, "language_model"):
            return
        
        from transformers import AutoModelForMaskedLM, AutoTokenizer
        
        language_encoder = AutoModelForMaskedLM.from_pretrained(self.language_model_id, attn_implementation="sdpa")
        self.language_model = language_encoder.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        self.language_model.eval()
        
        for param in self.language_model.parameters():
            param.requires_grad = False

        self.language_tokenizer = AutoTokenizer.from_pretrained(self.language_model_id)

        
