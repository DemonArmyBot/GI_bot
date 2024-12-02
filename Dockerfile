# Base Image 
FROM fedora:37

# 1. Setup home directory, non interactive shell and timezone
RUN mkdir -p /bot /chiori && chmod 777 /bot
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Africa/Lagos
ENV TERM=xterm

# 2. Install Dependencies
RUN dnf -qq -y update && dnf -qq -y install git bash xz wget curl python3-pip psmisc procps-ng && if [[ $(arch) == 'aarch64' ]]; then   dnf -qq -y install gcc python3-devel; fi && python3 -m pip install --upgrade pip setuptools

# 3. Copy files from repo to home directory
COPY . .

# 4. Install python3 requirements
RUN pip3 install -r requirements.txt

# 5. cleanup for arm64
RUN if [[ $(arch) == 'aarch64' ]]; then   dnf -qq -y history undo last; fi && dnf clean all

# 6. Start bot
CMD ["bash","run.sh"]
