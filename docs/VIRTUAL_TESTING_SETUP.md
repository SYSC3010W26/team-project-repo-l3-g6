# Virtual Testing Setup - Pi Mesh Network

**Objective:** Test the full distributed demo flow locally from anywhere without being physically present.
**Method:** VPN mesh network (Tailscale)
**Timeline:** ~15 minutes for the first setup, then instant repeatable testing anytime.

---

## How It Works

Tailscale creates a secure, flat mesh network between all your devices (your laptop and the 4 Raspberry Pis), regardless of what physical network (Wi-Fi, cellular, home router) they are connected to. This allows the Pis to communicate with each other and your laptop as if they were all plugged into the same local switch. They will all get a `100.x.y.z` IP address.

### 1. Account Setup (Admin / Laptop)
1. Go to [Tailscale.com](https://tailscale.com/) and create a free account (GitHub/Google login works well).
2. Download the Tailscale client for your laptop's OS (Windows/macOS/Linux).
3. Install, launch, and log in.
4. Your laptop now has a `100.x.y.z` IP address on the mesh. You can view all connected devices in the [Tailscale Admin Console](https://login.tailscale.com/admin/machines).

### 2. Connect the Raspberry Pis (Team Members)
Your team members just need to run the automated setup script on each Pi. The script will install Tailscale, connect it to the mesh, and automatically update the `.env` configuration file for the project.

```bash
# Run this from the root of the project repository
chmod +x setup_remote_testing.sh
./setup_remote_testing.sh
```

**What the script does:**
1. Installs Tailscale if it's not already present.
2. Starts Tailscale and enables Tailscale SSH (so you can SSH remotely without managing SSH keys).
3. *It will pause and give you a URL. Click it to authenticate the Pi to your Tailscale network.*
4. Shows a list of other devices already on the network.
5. Asks if the current Pi is the Master node or a Worker node.
6. Automatically writes the correct `NODE_IP`, `MASTER_IP`, and `API_URL` values into the project's `.env` file.

### 3. Start the Application
Because the `.env` file is automatically updated by the script, you just start your application as usual:

```bash
# Example
npm start
# or
python main.py
```

*Important:* Make sure your application servers (Express, Flask, FastAPI, etc.) are configured in your code to bind to `0.0.0.0` (all interfaces) or the specific Tailscale IP, rather than `127.0.0.1` or `localhost`. This ensures they accept incoming traffic from the Tailscale network.

### 4. Remote Access and Testing
You can now take your laptop home. As long as the Pis are powered on and connected to *any* internet connection (campus Wi-Fi, home network), you can:

- **SSH into them:** `ssh pi@100.x.y.z` (No need to be on the same Wi-Fi anymore!)
- **Access web interfaces:** `http://100.x.y.z:3000` (Open the Master node's Tailscale IP in your browser)
- **Run the full distributed system:** The Pis will seamlessly talk to each other over the Tailscale mesh using the IPs saved in their `.env` files.

---

## Troubleshooting

- **Authentication Link:** If the script prints a URL for authentication, you *must* open that URL in a browser on your laptop (where you are logged into Tailscale) to approve the Pi joining your network.
- **Pis drop offline:** Ensure the Pis are connected to a stable Wi-Fi network. If they change networks, Tailscale will automatically reconnect once internet is restored.
- **Key Expiry:** By default, Tailscale node keys expire every 180 days. You can disable key expiry for the Pis in the Tailscale admin console so they never unexpectedly disconnect.
- **Firewalls:** Tailscale automatically configures iptables/ufw to allow mesh traffic, so you generally do not need to open router ports or adjust local firewalls.
