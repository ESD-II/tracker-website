export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM="xterm-256color"
alias ls="ls --color=auto"
echo -e "\033[2J\033[H"
cat /tmp/blender.crash.txt
nvidia-smi
glxinfo | grep "OpenGL renderer"
apt update && apt install -y mesa-utils
glxinfo | grep "OpenGL renderer"
glxinfo | grep "OpenGL renderer"
nvidia-smi
apt update && apt install -y vulkan-tools
vulkaninfo | grep "GPU"
blender --debug-gpu
return
exit
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM="xterm-256color"
alias ls="ls --color=auto"
echo -e "\033[2J\033[H"
glxinfo | grep "OpenGL version"
glxinfo | grep "OpenGL renderer"
apt update && apt install -y libgl1 libglvnd-dev libnvidia-gl-525
nvidia-smi
apt update && apt install -y libgl1 libglvnd-dev libnvidia-gl-550
apt --fix-broken install
glxinfo | grep "OpenGL renderer"
