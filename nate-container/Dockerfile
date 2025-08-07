FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update package lists and install essential packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    wget \
    git \
    vim \
    htop \
    build-essential \
    python3 \
    python3-pip \
    nodejs \
    npm \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install NVIDIA Container Toolkit and CUDA
RUN wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub | apt-key add - \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
    && apt-get update \
    && apt-get install -y cuda-toolkit-12-8 \
    && rm -rf /var/lib/apt/lists/*

# Set CUDA environment variables
ENV PATH=/usr/local/cuda/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Create user 'nate' with sudo privileges
RUN useradd -m -s /bin/bash nate \
    && echo "nate:nate123" | chpasswd \
    && usermod -aG sudo nate \
    && echo "nate ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Configure SSH
RUN mkdir /var/run/sshd \
    && echo 'PermitRootLogin no' >> /etc/ssh/sshd_config \
    && echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config \
    && echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config \
    && echo 'Port 22' >> /etc/ssh/sshd_config

# Create SSH directory for nate user
RUN mkdir -p /home/nate/.ssh \
    && chown nate:nate /home/nate/.ssh \
    && chmod 700 /home/nate/.ssh

# Set working directory
WORKDIR /home/nate

# Switch to nate user for final setup
USER nate

# Create a welcome message
RUN echo 'echo "Welcome to Nate'\''s Container! GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits)"' >> /home/nate/.bashrc

# Switch back to root for SSH daemon
USER root

# Expose SSH port
EXPOSE 22

# Create startup script
RUN echo '#!/bin/bash\n\
# Start SSH daemon\n\
service ssh start\n\
# Keep container running\n\
tail -f /dev/null' > /start.sh \
    && chmod +x /start.sh

# Start SSH daemon
CMD ["/start.sh"]