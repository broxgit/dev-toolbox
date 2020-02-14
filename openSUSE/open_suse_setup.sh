#!/usr/bin/env bash

shopt -s expand_aliases
alias trace_on='set -x'
alias trace_off='{ set +x; } 2>/dev/null'

HELM_INSTALL=0

function installDocker()
{
    set -x

    (trace_off; echo -e "\n----- Installing Docker -----")

    sudo zypper -n install docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    newgrp docker << DOCKERGRP
    docker --version
DOCKERGRP

    # Setup daemon.
    sudo bash -c 'cat > /etc/docker/daemon.json' <<EOF
    {
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m"
      },
      "storage-driver": "overlay2"
    }
EOF

    sudo mkdir -p /etc/systemd/system/docker.service.d

    sudo systemctl daemon-reload
    sudo systemctl restart docker
}

function installMinikube()
{
    set -x

    (trace_off; echo -e "\n----- Installing kubectl -----")

    curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
    chmod +x ./kubectl
    sudo mv ./kubectl /usr/local/bin/kubectl

    mkdir $HOME/.kube || true
    touch $HOME/.kube/config
    sudo chown -R $USER $HOME/.kube

    sudo zypper -n in socat

    (trace_off; echo -e "\n----- Installing Minikube -----")

    curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

    chmod +x minikube

    sudo mkdir -p /usr/local/bin/
    sudo install minikube /usr/local/bin/
    export MINIKUBE_HOME=$HOME
    export CHANGE_MINIKUBE_NONE_USER=true
    export KUBECONFIG=$HOME/.kube/config

    cd /usr/local/bin

    DOCKERGROUP=$(newgrp docker <<DOCKERGRP
    docker info -f {{.CgroupDriver}}
DOCKERGRP
    )

    sudo -E ./minikube start --vm-driver=none --extra-config=kubelet.cgroup-driver=$DOCKERGROUP

    cd $HOME

    minikube status
}

function installHelm2()
{
    (trace_off; echo -e "\n---- Installing Helm 2 -----")

    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get
    chmod 700 get_helm.sh
    sh ./get_helm.sh

#    wget https://get.helm.sh/helm-v2.16.1-linux-amd64.tar.gz
#    tar -zxvf helm-v2.16.1-linux-amd64.tar.gz
#    sudo mv linux-amd64/helm /usr/local/bin/helm
    helm init
}

function installHelm3()
{
    (trace_off; echo -e "\n----- Installing Helm 3 -----")

    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
    chmod 700 get_helm.sh
    sh ./get_helm.sh

#    wget https://get.helm.sh/helm-v3.0.2-linux-amd64.tar.gz
#    tar -zxvf helm-v3.0.2-linux-amd64.tar.gz
#    sudo mv linux-amd64/helm /usr/local/bin/helm
}

function installHelm()
{
  (
      trace_off
      if [ $HELM_INSTALL -eq 2 ]; then
          installHelm2
      elif [ $HELM_INSTALL -eq 3 ]; then
          installHelm3
      fi
  )
}

function addBashAliases()
{
(
    trace_off
    (trace_off; echo -e "\n----- Adding Kubernetes Aliases to Bash -----")
    touch ~/.bash_aliases
    cat <<EOT >> ~/.bashrc
    if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
    fi
EOT

    cat <<'EOF' >> ~/.bash_aliases
    # kubectl shortcut - k:
    alias k='kubectl'

    # Get all pods in all namespaces
    alias kgpa='k get pods -A'

    # Get all resources in all namespaces
    alias kga='k get all -A'

    # Get all nodes
    alias kgno='k get nodes'

    # Get all deployments in all namespaces
    alias kgda='k get deployments -A'

    # Get all services in all namespaces
    alias kgsa='k get services -A'

    # Get all secrets in all namespaces
    alias kgseca='k get secrets -A'

    # Get all namespaces
    alias kgns='k get namespaces'

    # Quickly switch Kubernetes context with the given namespace
    alias kctx='f(){ kubectl config set-context $(kubectl config current-context) --namespace="$@"; unset -f f; }; f'
EOF
    echo "Please run this command or restart your terminal window to activate aliases: source .bashrc"
)
}

function enableSSH()
{
    (trace_off; echo -e "\n----- Enabling SSH -----")
    sudo systemctl enable sshd
    sudo systemctl start sshd
}

function installNginx()
{
    (trace_off; echo -e "\n----- Installing Nginx -----")
    # Install Nginx
    sudo zypper -n install nginx

    # Start and enable the Nginx service
    sudo systemctl start nginx
    sudo systemctl enable nginx.service

    # Create log files/directories necessary for Nginx local reverse proxy
    sudo mkdir /usr/logs
    sudo touch /usr/logs/access-stream.log
}

function installGit()
{
    (trace_off; echo -e "\n----- Installing Git -----")
    sudo zypper -n in git
}

function helmPrompt()
{
    if [[ $HELM_INSTALL -eq 0 ]]; then
      (
          trace_off
          echo -e "\n----- HELM INSTALLATION -----"
          echo -e "Which version of Helm would you like to install?"
          echo "2: Helm 2"
          echo "3: Helm 3"
          echo "Enter a Helm version: "
      )
      HELM_INSTALL=$(
          trace_off
          read -t 30 response
          helm2=2
          helm3=3
          if [[ "$response" =~ ^($helm2|$helm3)$ ]]; then
              if [ $response -eq $helm2 ]; then
                  helm_install=2
              elif [ $response -eq $helm3 ]; then
                  helm_install=3
              fi
          else
              helm_install=2
          fi

          echo $helm_install
      )
    fi
}

function systemChecks()
{
    (
    trace_off

    echo -e "\n----- Performing System Checks -----"

    echo "Verifying Zypper isn't locked by PackageKit"

    PID=`ps -eaf | grep packagekitd | grep -v grep | awk '{print $2}'`
    if [[ "" !=  "$PID" ]]; then
        echo "killing $PID"
        kill -9 $PID
    fi

    echo "Verifying the Firewall Service is disabled"

    firewallStatus=$(systemctl status firewalld | grep inactive)
    firewallEnabled=$(systemctl status firewalld | grep "service; disabled;")

    if [[ -z $firewallStatus ]]; then
        echo "Stopping firewall"
        sudo systemctl stop firewalld
    fi

    if [[ -z $firewallEnabled ]]; then
      echo "Disabling firewall service on startup"
      sudo systemctl disable firewalld
    fi
    )
}

function menu()
{
    (
    trace_off
    echo -e "\nThis script is used to install Docker, Kubectl, Minikube, and Helm. It also configures openSUSE for using said packages."
    printOptions

    read -t 30 response
    options $response

    )
}

function options()
{
  choice1=1
  choice2=2
  choice3=3
  choice4=4
  choice5=5
  choice6=6
  choice7=7
  choice8=8
  response=$1

  if [[ "$response" =~ ^($choice1|$choice2|$choice3|$choice4|$choice5|$choice6|$choice7|$choice8)$ ]]; then
      systemChecks

    if [ $response -eq $choice1 ]; then
        helmPrompt
        installDocker
        installMinikube
        installHelm

    elif [ $response -eq $choice2 ]; then
        installGit

    elif [ $response -eq $choice3 ]; then
        installNginx

    elif [ $response -eq $choice4 ]; then
        helmPrompt
        installDocker
        installMinikube
        installHelm
        installGit
        installNginx

    elif [ $response -eq $choice5 ]; then
        addBashAliases

    elif [ $response -eq $choice6 ]; then
        enableSSH

    elif [ $response -eq $choice7 ]; then
        helmPrompt
        enableSSH
        installDocker
        installMinikube
        installHelm
        installGit
        installNginx
        addBashAliases

    elif [[ "$response" -eq $choice8 ]]; then
        echo -e "\nInstall Docker? [Y/n]"
        read response
        response=${response,,}
        if [[ "$response" =~ ^(yes|y)$ ]]; then
            installDocker
        fi

        echo -e "\nInstall MiniKube and Kubectl? [Y/n]"
        read response
        response=${response,,}
        if [[ "$response" =~ ^(yes|y)$ ]]; then
            installMinikube
        fi

        echo -e "\nInstall Helm? [Y/n]"
        read response
        response=${response,,}
        if [[ "$response" =~ ^(yes|y)$ ]]; then
            helmPrompt
            installHelm
        fi

    else
        exit 1
    fi
  fi
}

function printOptions()
{
  echo "Enter 1-8 to continue, or press any key to exit
    1. Install container-related packages (Docker, Kubectl, Minikube, and Helm)
    2. Install Git
    3. Install Nginx (to prep for a local-reverse-proxy)
    4. Install all of the above packages
    5. Add Kubernetes bash aliases
    6. Enable SSH
    7. All of the Above
    8. Select packages to install (Existing setup)"
}

function usage()
{
  echo "usage: open_suse_setup.sh [[-o option] -v helmVersion]] | [-h]
    Help:
          -h      displays the help and usage

    Non-interactive Mode:
          -o <#>  runs the script with the defined option number
          -v <#>  defines the version of Helm to install (2 or 3) - only needed when option selected includes a Helm install"


  echo -e "\nExample (install git): open_suse_setup.sh -o 2\n"
  echo "Options:"
  printOptions
}

option=0

while [ "$1" != "" ]; do
  case $1 in
    -o | --option )         shift
                            option=$1
                            ;;
    -v | --helmVersion )    shift
                            HELM_INSTALL=$1
                            ;;
    -h | --help )           usage
                            exit
                            ;;
    * )                     usage
                            exit 1
  esac
  shift
done

if [ "$option" = 0 ]; then
  menu
else
  options $option
fi