# Import necessary libraries
import subprocess
import getpass

ascii_art1 = """
  __  __      _         ___ _____  ___   ___  ___   _   ___  ___ _
 |  \/  |__ _| |_____  | __/ __\ \/ (_) | _ \/ __| /_\ | _ \/ __| |
 | |\/| / _` | / / -_) | _|\__ \>  <| | |  _/ (__ / _ \|  _/\__ \_|
 |_|  |_\__,_|_\_\___| |___|___/_/\_\_| |_|  \___/_/ \_\_|  |___(_)
                                                                  """

ascii_art2 = """
                        Virtual Machine           Virtual Machine
                            ┌────┐                  ┌────┐
                            │    │                  │    │
                            │    │                  │    │
                            └─┬──┘                  └──┬─┘
        vNic Capture Point    │                        │      vNic Capture Point
                       ─────► │                        │  ◄──────
                              │                        │
                       ──────►│                        │  ◄─────────
PortOutput or PortInput       │                        │       PortOuput or PortInput Capture Point
                 ┌────────────┴────────────────────────┴────────────┐
                 │                                                  │
                 │                                                  │
                 │         dVSwitch or Standard Switch              │
                 │                                                  │
                 │                                                  │
                 └──────────────────────────────────────────────┬───┘
                                                                │     PortOutput or PortInput
                                                                │   ◄───────────
                                                                │
                                                                │
                                                                │
                                                                │   ◄──────────────
                                                                │   UplinkSndKernel or UplinkRcvKernel
                                                                │
                                                            ┌───┴───┐
                                                            │       │ vmnic (also known as pnic)
                                                            │       │
                                                            │       │
                                                            └───────"""

# Welcome the user
print(ascii_art1)
print("Welcome to the ESXi packet capture command creator!\n")

# Prompt the user for the ESXi hostname or IP address
esxi_server = input("Enter the hostname or IP address of the ESXi server: ")

# Test if the ESXi server is reachable
if subprocess.run(["ping", "-c", "1", esxi_server]).returncode == 0:
    print(f"{esxi_server} is reachable!")
else:
    print(f"{esxi_server} is not reachable. Please check reachability in another terminal.")
    exit()

# Test if the ESXi server is listening on port 22
if subprocess.run(["nc", "-z", esxi_server, "22"]).returncode == 0:
    print(f"{esxi_server} is listening on port 22.\n")
else:
    print(f"{esxi_server} is not listening on port 22. Exiting program.\n")
    exit()

# Collect the password from the user
password = getpass.getpass("Enter the password for the ESXi server: ")

# Connect to the ESXi server and retrieve output for the "net-stats -l" command
from netmiko import ConnectHandler

device = ConnectHandler(
    host=esxi_server,
    username="root",
    password=password,
    device_type="generic",
)

output = device.send_command("net-stats -l")

device.disconnect()

# Print the output and prompt the user for the name of the VM they want to packet capture on
print(f"\n\n\nThis is a list of VMs connected to the virtual switch on host: \n{output}")
print(ascii_art2)
vm_name = input("Which virtual machine do you want to packet capture on? ")

# Check if the user's input is a valid VM name - problem is here somewhere
vm_list = []
port_list = []
for line in output.split("\n"):
    if "PortNum" not in line:
        vm_list.append(line.split()[5])
        port_list.append(line.split()[0])

my_dict = dict(zip(vm_list,port_list))

if vm_name not in vm_list:
    print("Invalid VM name. Exiting program.")
    exit()


if 'vmnic' in vm_name:
    print(f"You've identified device {vm_name}. This is a physical nic on an ESXi host. Here is the command to"
          " perform packet capture:\n")
    print(f"pktcap-uw --uplink {my_dict[vm_name]} --capture UplinkSndKernel,UplinkRcvKernel -o - | tcpdump-uw -enr -")
    print()
    print(f"pktcap-uw --uplink {my_dict[vm_name]} --capture PortInput,PortOutput -o - | tcpdump-uw -enr -")
    print()
elif 'vmk' in vm_name:
    print(f"You've identified device {vm_name}. This is a VMkernel interface. it does not have a vnic."
          f" Capture it at the virtual port.\n")
    print(f"pktcap-uw --switchport {my_dict[vm_name]} --capture PortInput,PortOutput -o - | tcpdump-uw -enr -")
    print()
else:
    print(f"You've identified device {vm_name}. This is a VM. We are capturing at the virtual nic of the VM.\n")
    print(f"pktcap-uw --switchport {my_dict[vm_name]} --capture VnicTx,VnicRx -o - | tcpdump-uw -enr -")
    print()
    print(f"pktcap-uw --switchport {my_dict[vm_name]} --capture PortInput,PortOutput -o - | tcpdump-uw -enr -")
    print()

