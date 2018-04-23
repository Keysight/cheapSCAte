#!/bin/bash
#
# Lists the scope two times with sigrok to load the firmware on the Hantek-6022BE scope
# Script comes as-is, use it carefully (no safety checks on parameters!)

echo Initializing all the scopes connected to the computer...
sigrok-cli --scan > /dev/null
sleep 5
echo The line below should display a string starting with hantek-6xxx:conn=x.x
echo If the conn=x.x string is missing, rerun the script
echo
sigrok-cli --scan
