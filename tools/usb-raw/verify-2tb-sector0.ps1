$ErrorActionPreference = 'Stop'
$dev = '\\.\PHYSICALDRIVE2'
& python 'C:\asolaria-acer\tools\usb-raw\usb_raw_io.py' --read 0 --device $dev
