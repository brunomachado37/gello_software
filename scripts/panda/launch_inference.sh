source ~/miniconda3/bin/activate
conda activate gello

sudo chmod 666 /dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_FTA7NNHW-if00-port0
sudo chmod 666 /dev/ttyUSB0

sudo pkill -9 run_server
sudo pkill -9 -f launch_nodes.py
sudo pkill -9 franka_panda_cl
sudo pkill -9 gripper
sudo pkill -9 -f launch_nodes.py
sudo pkill -9 -f launch_camera_nodes.py
sudo pkill -9 -f run_env.py
rm ./logs/*.log

sleep 1

launch_robot.py robot_client=franka_hardware robot_client.executable_cfg.robot_ip=192.168.10.100 > ./logs/launch_robot.log 2>&1 &
launch_gripper.py gripper=robotiq_2f gripper.comport=/dev/ttyUSB0 > ./logs/launch_gripper.log 2>&1 &

sleep 5

python experiments/launch_nodes.py --robot=panda --robot_ip=localhost > ./logs/launch_nodes.log 2>&1 &
python experiments/launch_camera_nodes.py > ./logs/launch_camera_nodes.log 2>&1 &

python experiments/run_env.py --use-save-interface agent:le-robot --agent.id=HF_HUB_MODEL_ID --agent.type=POLICY_TYPE --agent.task=TASK_DESCRIPTION > ./logs/run_env.log 2>&1 &

# Examples:
# python experiments/run_env.py --use-save-interface agent:le-robot --agent.id=/home/panda/Downloads/CHECKPOINTS_ACT/ckpt_resnet/pretrained_model/ --agent.type=act --agent.task='Stack the bowls in the pan.'
# python experiments/run_env.py --use-save-interface agent:le-robot --agent.id=/home/panda/Downloads/CHECKPOINTS_ACT/ckpt_resnet/pretrained_model/ --agent.type=act --agent.task='Pick up all the bowls from the table and stack them one by one on the plate inside the red dish rack'
# python experiments/run_env.py --use-save-interface agent:le-robot --agent.id=/home/panda/Downloads/CHECKPOINTS_ACT/ckpt_resnet/pretrained_model/ --agent.type=act --agent.task='Put the cans into the bin.'


