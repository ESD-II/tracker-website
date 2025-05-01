use pgrep -f tennis_sim.py to find PID then kill <pid> to end the process
use ps aux | grep tennis_sim.py to check if process is running
use nohup ./tennis_sim.py > tennis_sim.log 2>&1 & to start script
