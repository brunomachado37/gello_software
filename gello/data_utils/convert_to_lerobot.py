import os
import pickle
import argparse
import datetime
import time

from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.datasets.utils import DEFAULT_FEATURES


def get_features(episode):
    """
    Get the features of the dataset from the first episode.
    """
    step_file = os.path.join(episode, os.listdir(episode)[0])

    with open(step_file, "rb") as f:
        step = pickle.load(f)

    camera_ft = {}

    for cam_key in ["wrist", "side"]:
        key = f"observation.images.{cam_key}_camera"
        camera_ft[key] = {
            "shape": (step[f"{cam_key}_rgb"].shape[0], step[f"{cam_key}_rgb"].shape[1], step[f"{cam_key}_rgb"].shape[2]),
            "names": ["height", "width", "channels"],
            "info": None,
            "dtype": "video",
        }

    motor_features = {
        "action": {
            "dtype": step["control"].dtype.name,
            "shape": (len(step["control"]),),
            "names": [f"joint_{i}" for i in range(len(step["control"]) - 1)] + ["gripper"],
        },
        "observation.state": {
            "dtype": step["joint_positions"].dtype.name,
            "shape": (len(step["joint_positions"]),),
            "names": [f"joint_{i}" for i in range(len(step["joint_positions"] - 1))] + ["gripper"],
        },
    }

    return {**motor_features, **camera_ft, **DEFAULT_FEATURES}


def convert(cfg):
    episodes = os.listdir(cfg.data_path)        # One folder per episode, one file per step
    episodes = [os.path.join(cfg.data_path, ep) for ep in episodes]

    features = get_features(episodes[0])

    dataset = LeRobotDataset.create(
        cfg.repo_id,
        cfg.fps,
        robot_type=cfg.robot,
        features=features,
    )
        
    for episode in episodes:
        steps = os.listdir(episode)

        for step_file in steps:
            step_path = os.path.join(episode, step_file)

            with open(step_path, "rb") as f:
                step = pickle.load(f)

            action = {"action": step["control"]}

            observation = {
                "observation.state": step["joint_positions"],
                "observation.images.wrist_camera": step["wrist_rgb"],
                "observation.images.base_camera": step["side_rgb"],
            }

            frame = {**observation, **action}
            dataset.add_frame(frame, task=cfg.task_description) #, timestamp=time.mktime(datetime.datetime.strptime(step_file.split(".pkl")[0], "%Y-%m-%dT%H:%M:%S.%f").timetuple()))

        dataset.save_episode()

    dataset.push_to_hub(tags=["franka", "panda", "pick_and_place"])


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Convert dataset from Gello to LeRobot format.")
    argparser.add_argument("--data_path", type=str, required=True, help="Path to the dataset folder.")
    argparser.add_argument("--repo_id", type=str, required=True, help="Desired LeRobot repository ID for the dataset (user_name/dataset_name).")
    argparser.add_argument("--task_description", type=str, required=True, help="Task description in natural language.")
    argparser.add_argument("--fps", type=int, default=10, help="Frames per second for the dataset.")
    argparser.add_argument("--robot", type=str, default="Franka", help="Robot name.")
    args = argparser.parse_args()

    convert(args)