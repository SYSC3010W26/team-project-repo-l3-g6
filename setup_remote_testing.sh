#!/bin/bash

###############################################################################
# DISTRIBUTED TESTING SETUP - Tailscale Mesh Network
#
# Run this on each Pi to join the Tailscale mesh network
# Usage: ./setup_remote_testing.sh
#
# This script installs Tailscale and automatically configures your .env file
# so the Pis can communicate over the mesh network.
###############################################################################

set -e

echo "======================================================="
echo "   Tailscale Mesh Network Installer for Raspberry Pi   "
echo "======================================================="

# 1. Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "[-] curl is not installed. Installing curl..."
    sudo apt-get update
    sudo apt-get install -y curl
fi

# 2. Install Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "[+] Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "[+] Tailscale is already installed. Skipping installation."
fi

# 3. Bring Tailscale Up
echo ""
echo "======================================================="
echo " ⚠️ CRITICAL STEP: JOINING THE RIGHT NETWORK ⚠️ "
echo "======================================================="
echo "If you are a team member, you MUST have accepted an invite"
echo "link from the project admin BEFORE doing this step."
echo ""
echo "When you click the authentication link below, look at the"
echo "TOP LEFT CORNER of the Tailscale website."
echo "Make sure the dropdown is set to the TEAM'S network name,"
echo "NOT your personal email address! Otherwise, your Pis won't"
echo "be able to see each other."
echo "======================================================="
echo ""
echo "[+] Starting Tailscale..."
sudo tailscale up --ssh

# 4. Fetch the new Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
HOSTNAME=$(hostname)

echo "[+] Node Hostname: $HOSTNAME"
echo "[+] Tailscale IP:  $TAILSCALE_IP"

echo ""
echo "======================================================="
echo "   Application Configuration (.env setup)              "
echo "======================================================="

# Show other nodes on the network to make it easy for the user to find the Master IP
echo "Other devices currently on your Tailscale network:"
PEERS=$(tailscale status | grep -v "$TAILSCALE_IP" || true)

if [ -z "$PEERS" ]; then
    echo "  ❌ WARNING: No other active devices found!"
    echo "  If you are a worker node, this means you probably logged into"
    echo "  your own personal network instead of the team's network."
    echo "  You should press Ctrl+C, run 'sudo tailscale logout', accept"
    echo "  the admin's invite link, and run this script again."
    echo ""
else
    echo "$PEERS"
    echo ""
fi

read -p "Is this Pi the MAIN/MASTER node? (y/n): " IS_MASTER

ENV_FILE=".env"
echo "[+] Updating $ENV_FILE..."

# Ensure .env exists
touch $ENV_FILE

# Remove old IP configurations to avoid duplicates in the .env file
sed -i '/^NODE_IP=/d' $ENV_FILE
sed -i '/^MASTER_IP=/d' $ENV_FILE
sed -i '/^API_URL=/d' $ENV_FILE

# Set the current node's IP
echo "NODE_IP=$TAILSCALE_IP" >> $ENV_FILE

if [[ "$IS_MASTER" =~ ^[Yy]$ ]]; then
    echo "MASTER_IP=$TAILSCALE_IP" >> $ENV_FILE
    echo "API_URL=http://$TAILSCALE_IP:3000" >> $ENV_FILE
    echo "[+] Configured as MASTER node."
else
    echo ""
    read -p "Enter the Tailscale IP of the MASTER node (from the list above): " MASTER_IP
    echo "MASTER_IP=$MASTER_IP" >> $ENV_FILE
    echo "API_URL=http://$MASTER_IP:3000" >> $ENV_FILE
    echo "[+] Configured as WORKER node pointing to $MASTER_IP."
fi

echo ""
echo "======================================================="
echo "   Setup Complete!                                     "
echo "======================================================="
echo "Your $ENV_FILE has been automatically updated with the new Tailscale IPs:"
echo "-------------------------------------------------------"
cat $ENV_FILE | grep -E 'NODE_IP|MASTER_IP|API_URL'
echo "-------------------------------------------------------"
echo ""
echo "You can now start your application normally."
echo "It will communicate over the secure 100.x.y.z Tailscale network."
echo ""
echo "To access this node remotely, SSH using: ssh $(whoami)@$TAILSCALE_IP"
echo "======================================================="
