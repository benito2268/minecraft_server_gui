An idea born from the desire to allow a friend to control a Minecraft server without knowledge of the Linux CLI.
Made using Python and Tkinter, with the paramiko SSH client library.

## FAQ
* Does the server have to be Linux: yes.
* Why does the server console take so long to update?
Because a Minecraft server cannot send data directly over SSH, the output is buffered in a file on the remote host.
To avoid lag, the file is read and new lines are displayed in the console every 5 seconds.
* Isn't this unsafe? yeah, probably. Maybe if I find more time, I'll make it a little more professional.

## Client Setup
* `pip install paramiko`
* `python3 serverman.py`

## Server Setup
* Have a (Linux) minecraft server with a start file named `start.sh`
* Have SSH enabled with a user that does not require pubkey auth. (don't give them sudo!)
* `sudo apt install screen` (or use your favorite package manager)
