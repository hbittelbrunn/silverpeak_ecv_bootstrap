import getpass
import time

import colored
from colored import stylize

# Helper for API interaction with Silver Peak Edge Connect
from silverpeak_python_sdk import EdgeConnect
from tqdm import tqdm

# Console text highlight color parameters
red_text = colored.fg("red") + colored.attr("bold")
green_text = colored.fg("green") + colored.attr("bold")
blue_text = colored.fg("steel_blue_1b") + colored.attr("bold")
orange_text = colored.fg("dark_orange") + colored.attr("bold")


def ec_auto_map(ec_ip, ec_user="admin", ec_pass="admin"):

    ec = EdgeConnect(ec_ip)

    ec.login(ec_user, ec_pass)

    # Get appliance interfaces, which includes available unnassigned MAC addresses
    interfaces = ec.get_appliance_interfaces()

    # Sort out just the relevant availableMacs list
    for item in interfaces:
        try:
            availableMacs = item["dynamic"]["availableMacs"]
        except:
            pass

    # dictionary to store original MAC / converted integer pairings
    mac_dict = {}
    # list to easily sort converted integers of MAC addresses
    mac_int_list = []
    # convert MAC addresses to integers and store pair in dictionary, and store integer in list for sorting
    for mac in availableMacs:
        # replace ":" in MAC so that it's a base-16 hexadecimal number and convert it to an integer
        mac_int = int(mac.replace(":", ""), 16)
        # store in a dictionary as a key for the original MAC address string as its value
        mac_dict[mac_int] = mac
        # add the integer to a list for sorting in ascending order
        mac_int_list.append(mac_int)

    # sort the integer values in ascending order
    mac_int_list.sort()

    # logical ECV interface list
    ecv_interface_names = [
        "mgmt0",
        "wan0",
        "lan0",
        "wan1",
        "lan1",
        "wan2",
        "lan2",
        "wan3",
        "lan3",
    ]

    # List of interfaces to modify
    ifInfo = []

    # Pair available MAC addresses to logical interface names
    i = 0
    while i < len(availableMacs):
        ifInfo.append(
            {"ifname": ecv_interface_names[i], "mac": mac_dict[mac_int_list[i]]}
        )
        i = i + 1

    if not ifInfo:
        print("There were no available MAC addressess to map to interfaces")
    else:
        print("The following interface assignments are going to be made:")
        for interface in ifInfo:
            print(stylize(interface["ifname"] + ":  " + interface["mac"], blue_text))

    try:
        ec.modify_network_interfaces(ifInfo)
        # Per API documentation, waiting 30 seconds before another API call after performing a POST to /networkInterfaces
        print(
            stylize(
                "\n########## INTERFACES MAPPED - PAUSING FOR NEXT API CALL ##########",
                orange_text,
            )
        )

        i = 0
        for i in tqdm(range(10)):
            time.sleep(3)
            i = i + 1

    except:
        print("Unable to assign MAC addresses!")

    # Save changes on Edge Connect
    print(stylize("\n########## SAVING CHANGES ##########", orange_text))
    ec.save_changes()

    # Reboot Edge Connect if required
    print(stylize("\n########## CHECKING FOR REBOOT STATUS ##########", orange_text))
    reboot_required = ec.is_reboot_required()
    if reboot_required["isRebootRequired"] == True:
        print(
            stylize(
                "\n########## CONFIG COMPLETED - REBOOTING APPLIANCE ##########",
                green_text,
            )
        )
        ec.request_reboot(applyBeforeReboot={"hostname": "eve-silverpeak"})
    else:
        print("No reboot required")
        ec.logout()


if __name__ == "__main__":

    # Set custom Edge Connect Credentials, otherwise defaults to admin/admin
    ec_default_creds = input(
        "Are default credentials in use for the Edge Connect(s)? (y/n): "
    )
    if ec_default_creds == "n":
        print(stylize("Enter Edge Connect Credentials:", blue_text))
        ec_user = getpass.getuser()
        ec_pass = getpass.getpass()
    else:
        pass

    # Enter IP address of single Edge Connect
    ec_ip = input(
        "Please enter IP address of Edge Connect to Migrate (e.g. 10.1.30.100): "
    )

    # Auto-map interfaces to MAC addresses on Edge Connect
    if ec_default_creds == "y":
        ec_auto_map(ec_ip)
    else:
        ec_auto_map(ec_ip, ec_user, ec_pass)
