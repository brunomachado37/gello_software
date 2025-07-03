from dataclasses import dataclass
from multiprocessing import Process

import tyro

from gello.cameras.zed_camera import ZedCamera, get_devices
from gello.zmq_core.camera_node import ZMQServerCamera


@dataclass
class Args:
    hostname: str = "127.0.0.1"


def launch_server(port: int, camera_id: int, args: Args):
    camera = ZedCamera(camera_id)
    server = ZMQServerCamera(camera, port=port, host=args.hostname)
    print(f"Starting camera server on port {port}")
    server.serve()


def main(args):
    ids = get_devices()
    camera_port = 5000
    camera_servers = []
    for camera_id in ids:
        # start a python process for each camera
        print(f"Launching camera {camera_id} on port {camera_port}")
        camera_servers.append(
            Process(target=launch_server, args=(camera_port, camera_id, args))
        )
        camera_port += 1

    for server in camera_servers:
        server.start()


if __name__ == "__main__":
    main(tyro.cli(Args))
