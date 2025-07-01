source ~/.bashrc
conda activate gello

pkill -9 run_server
pkill -9 franka_panda_cl
pkill -9 gripper
pkill -9 -f launch_nodes.py

launch_robot.py robot_client=franka_hardware &
launch_gripper.py gripper=franka_hand &

sleep 5

python experiments/launch_nodes.py --robot=panda --robot_ip=localhost &

sleep 2

python experiments/run_env.py --agent=gello