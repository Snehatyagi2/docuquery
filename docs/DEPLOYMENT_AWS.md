# AWS Deployment Guide (EC2 + Docker + Nginx + k3s)

This document records the exact steps used to deploy **DocuQuery** on **AWS (`ap-southeast-2`)** at minimal/zero Free-Tier cost.

---

## 1. Prerequisites & AWS CLI Authentication

1. Install **AWS CLI v2** and `uv`.
2. Configure the project region and authenticate via browser login (`aws login --remote` for cross-device/headless environments):
   ```powershell
   aws configure set region ap-southeast-2 --profile docuquery
   aws login --region ap-southeast-2 --profile docuquery --remote
   aws sts get-caller-identity --profile docuquery
   ```

---

## 2. Provision Network Security & Key Pair (`ap-southeast-2`)

1. Create an SSH key pair (`docuquery-k3s-key.pem` stored outside the repository in `~/.ssh/`):
   ```powershell
   aws ec2 create-key-pair --key-name docuquery-k3s-key --query "KeyMaterial" --output text --region ap-southeast-2 --profile docuquery > $env:USERPROFILE\.ssh\docuquery-k3s-key.pem
   ```
2. Create a Security Group in the default VPC allowing:
   - **Port `80` (HTTP)** and **`30080` (NodePort)** from `0.0.0.0/0`
   - **Port `22` (SSH)** restricted strictly to your public IP (`<YOUR_IP>/32`)

---

## 3. Launch Free-Tier EC2 Instance (`t3.micro`)

Launch an **Ubuntu 24.04 LTS** `t3.micro` instance (`20 GB` `gp3` EBS volume) with a bootstrap script that:
1. Adds **2 GB swap** (`/swapfile`) so `pip install` / `docker build` succeeds within 1 GiB RAM.
2. Installs `docker.io`, `git`, and `nginx`.
3. Clones `https://github.com/Snehatyagi2/docuquery.git` into `/opt/docuquery` and builds the image:
   ```bash
   docker build -t docuquery-api:v1 .
   ```

---

## 4. Runtime Architecture: Docker + Nginx (and Kubernetes `k3s` Note)

- **Kubernetes (`k3s`) Evaluation:** We authored [k8s/deployment.yaml](../k8s/deployment.yaml), [k8s/service.yaml](../k8s/service.yaml), and [k8s/ingress.yaml](../k8s/ingress.yaml) and tested `k3s` on `t3.micro`. Because `t3.micro` has ~909 MB RAM, running the `k3s` control plane alongside `scikit-learn`/`scipy` caused swap thrashing and intermittent `502 Bad Gateway` responses.
- **Production-Stable Free-Tier Runtime:** To stay at **$0 on the Free Tier** without paying ~$73/month for Amazon EKS, we run `docuquery-api:v1` directly via Docker behind Nginx on port `80`:
  ```bash
  sudo docker run -d --name docuquery-api --restart unless-stopped -p 127.0.0.1:8000:8000 docuquery-api:v1
  ```
- **Nginx Reverse Proxy (`/etc/nginx/sites-available/default`):**
  ```nginx
  server {
    listen 80 default_server;
    client_max_body_size 50M;
    location / {
      proxy_pass http://127.0.0.1:8000;
    }
  }
  ```

---

## 5. Verification & Cost Management

- **Verify Live Endpoints:**
  - Web UI: `http://16.179.104.253/`
  - Swagger Docs: `http://16.179.104.253/docs`
  - Health Check: `http://16.179.104.253/health`
- **Stop / Start Instance to Save Free-Tier Hours:**
  ```powershell
  aws ec2 stop-instances --instance-ids i-040d5a549cc8b3e90 --region ap-southeast-2 --profile docuquery
  aws ec2 start-instances --instance-ids i-040d5a549cc8b3e90 --region ap-southeast-2 --profile docuquery
  ```
- **Terminate Instance (Full Cleanup):**
  ```powershell
  aws ec2 terminate-instances --instance-ids i-040d5a549cc8b3e90 --region ap-southeast-2 --profile docuquery
  ```
