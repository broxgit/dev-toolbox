# OpenSUSE Setup Script
This script gives any user the ability to install Minikube, Docker, Kubectl, and Helm with a few simple commands. 
The script can also be used to enable SSH, install Nginx, and configure Kubernetes configure bash aliases in a few commands.
## Usage
### Copy and prepare the script 
Run the script as the user that will be managing your Kubernetes cluster, this SHOULD NOT be the root user
```bash
# Copy the script to your Home directory from the root of the k8s-hello-world project
cp linux/open_suse_setup.sh $HOME

# Navigate to your Home directory
cd $HOME

# Give the script permissions to run
chmod 777 open_suse_setup.sh

# Run the script with the help flag to display usage and options:
./open_suse_setup.sh -h
```

### Using the script (Interactive Mode)
Run the script in interactive mode: 
```bash
./open_suse_setup.sh
```
When the script runs, you will be prompted with a menu:
```bash
This script is used to install Docker, Kubectl, Minikube, and Helm. It also configures openSUSE for using said packages.
1. Install container-related packages (Docker, Kubectl, Minikube, and Helm)
2. Install Git
3. Install Nginx (to prep for a local-reverse-proxy)
4. Install all of the above packages
5. Add Kubernetes bash aliases
6. Enable SSH
7. All of the Above
8. Select packages to install (Existing setup)
Enter 1-8 to continue, or press any key to exit:
```

#### Option 1: Install container-related packages
This option will install the following: 
- Docker
- Kubectl
- Minikube
- Helm (version of your choice)

This option will ask you which version of Helm you wish to install, and then ask you to enter your sudo password for the first docker command, after that the script can run uninterrupted until finished.
```bash
----- HELM INSTALLATION -----
Which version of Helm would you like to install?
2: Helm 2
3: Helm 3
<your response here>

----- Installing Docker -----
+ sudo zypper -n install docker
[sudo] password for root:
```    

#### Option 2: Install Git
Install Git

#### Option 3: Install Nginx
Install and configure Nginx.

#### Option 4: Install all of the above packages
This option installs all container-related packages, along with Git and Nginx, when complete the following will be installed:
- Docker
- Kubectl
- Minikube
- Helm (version of your choice)
- Git
- Nginx

#### Option 5: Add Kubernetes bash aliases
This will add the Kubernetes bash aliases to your bash profile. In order for the aliases to work, you will have to restart your Terminal or run `source .bashrc`

#### Option 6: Enable SSH
This will enable SSH, allowing you to remotely login. 

#### Option 7: All of the Above
This combines options 4-6 and will install all packages, enable SSH, and add the Kubernetes Aliases to your path. 

#### Option 8: Select packages to install
You will be prompted yes/no for each of the packages above, this gives you the ability to install only the packages you want.

### Using the script (Non-Interactive Mode)
The options above still apply, however you can run the script in "non-interactive mode":
```bash
./open_suse_setup.sh -o <optionNumber>
```

If the -o flag is used, non-interactive mode is assumed by the script.

For instance, if I wanted to install Nginx in "non-interactive mode", I would run the following command: 
```bash
./open_suse_setup.sh -o 3
```

When installing Helm, the -v flag must also be specified:

Example: Installing all packages (including Helm 2)
```bash
./open_suse_setup.sh -o 4 -v 2
```