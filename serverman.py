from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import font
from tkinter import *

from time import sleep
import os
import difflib
import threading
import paramiko
import subprocess

root = Tk() 
LF = "\n"
SERVER_DIR = "~/server"
SCREEN_SESSION = "server"
SCREEN_LOG_FILE = f"{SERVER_DIR}/stdout.log"
SCREEN_LOG_DIFF = f"{SERVER_DIR}/diff.log"

REMOTE_HOST = "tiger"
USER = "minecarft"

class TkGUI:

    def __init__(self, root):
        self.root = root
        root.title("funny server console thingy :)")
        root.config(bg="grey")
        
        root.geometry("1200x900")  # Set a fixed size for the window

        notebook = ttk.Notebook(root)
        notebook.pack(side="bottom", fill="both", expand=True)

        self.left = Frame(root, bg="sky blue", width=300)
        self.right = Frame(root, bg="gray64", width=400)
        #self.term = Frame(root, bg="blue", width=400)
        
        self.term = Frame(notebook, bg="black", width=400)
        notebook.add(self.term, text="Shell Output")
        
        self.server_console = Frame(notebook, bg="black", width=400)
        notebook.add(self.server_console, text="Server Output")
        
        self.left.pack(side="left", fill="both")
        self.right.pack(side="top", fill="both", expand=True)
        #self.term.pack(side="bottom", fill="both", expand=True)
        
        # ========== status control ==========
        self.user_label = Label(self.left, text=f"user: {USER}", font=("Consolas", 12))
        self.user_label.grid(row=0, column=0, padx=30, pady=10)
        
        self.host_label = Label(self.left, text=f"remote host: {REMOTE_HOST}", font=("Consolas", 12))
        self.host_label.grid(row=1, column=0, padx=30, pady=10)
        
        self.shell_button = Button(self.left, text="Reconnect", command=self.reconnect, font=("Consolas", 14))
        self.shell_button.grid(row=2, column=0, padx=30, pady=10)
        
        self.shell_button = Button(self.left, text="Edit server.properties", command=self.edit_props, font=("Consolas", 14))
        self.shell_button.grid(row=3, column=0, padx=30, pady=10)
        
        self.shell_button = Button(self.left, text="Launch real shell", command=self.launch_shell, font=("Consolas", 14))
        self.shell_button.grid(row=4, column=0, padx=30, pady=10)
        
        # ========== shell commands ==========
        
        self.shell_label = Label(self.right, text="Run Shell Command:", font=("Consolas", 16))
        self.shell_label.grid(row=0, column=0, padx=30, pady=10)
    
        self.shell_entry = Entry(self.right, bg="black", fg="white", font=("Consolas", 14))
        self.shell_entry.grid(row=1, column=0, padx=30, pady=0)
    
        self.shell_button = Button(self.right, text="Run", command=self.run_shell_cmd, font=("Consolas", 16))
        self.shell_button.grid(row=2, column=0, padx=30, pady=10)
        
        # ========== server commands ==========
        
        self.server_label = Label(self.right, text="Run Server Command:", font=("Consolas", 16))
        self.server_label.grid(row=0, column=1, padx=30, pady=10)
    
        self.server_entry = Entry(self.right, bg="black", fg="white", font=("Consolas", 14))
        self.server_entry.grid(row=1, column=1, padx=30, pady=0)
    
        self.server_button = Button(self.right, text="Run", command=self.run_server_cmd, font=("Consolas", 16))
        self.server_button.grid(row=2, column=1, padx=30, pady=10)
        
        # ========== server buttons ==========
        
        self.start_server_b = Button(self.right, text="Start Server", command=self.start_server, font=("Consolas", 16), fg="white", bg="green")
        self.stop_server_b = Button(self.right, text="Stop Server", command=self.stop_server, font=("Consolas", 16), fg="white", bg="red")
        self.restart_server_b = Button(self.right, text="Restart Server", command=self.restart_server, font=("Consolas", 16), fg="white", bg="orange")
        
        self.stop_server_b.grid(row=3, column=0, padx=30, pady=30)
        self.start_server_b.grid(row=3, column=1, padx=30, pady=30)
        self.restart_server_b.grid(row=3, column=2, padx=30, pady=30)
        
        # ========== shell listbox ==========
        self.lb_font = font.Font(family="Consolas", size=12)
        self.term_lb = Listbox(self.term, 
                                   bg = 'black', 
                                   fg = 'white', 
                                   highlightcolor = 'black', 
                                   highlightthickness = 0, 
                                   selectbackground = 'black',
                                   font=self.lb_font,
                                   activestyle = NONE)
        self.term_lb.pack(fill="both", expand=True)
        #self.term_scrollbar = Scrollbar(self.term_lb)
        #self.term_scrollbar.pack(side = RIGHT, fill = Y)
        
        # ========== server listbox ==========
        
        self.server_lb = Listbox(self.server_console, 
                                   bg = 'black', 
                                   fg = 'white', 
                                   highlightcolor = 'black', 
                                   highlightthickness = 0, 
                                   selectbackground = 'black',
                                   font=self.lb_font,
                                   activestyle = NONE)
        self.server_lb.pack(fill="both", expand=True)
        self.last_output = ""
        #self.server_scrollbar = Scrollbar(self.server_lb)
        #self.server_scrollbar.pack(side = RIGHT, fill = Y)
        
        # ========== status labels ==========
        self.status_title = Label(self.right, text="Server Status", font=("Consolas", 16))
        
        self.cpu = Label(self.right, text="CPU: 0.0%", font=("Consolas", 16), fg="white", bg="green", relief="sunken")
        self.mem = Label(self.right, text="MEM: 0mb", font=("Consolas", 16), fg="white", bg="green", relief="sunken")
        
        self.status_title.grid(row=4, column=0, padx=10, pady=10)
        self.cpu.grid(row=4, column=1, padx=10, pady=10)
        self.mem.grid(row=4, column=2, padx=10, pady=10)
        
        self.host, self.user, self.passwd = self.get_passwd()
        self.session = RemoteSession(self.host, self.user, self.passwd)
        
        status = self.session.do_shell_cmd("ps")
        if "screen" in "".join(status):   
            self.status = Label(self.right, text="Running", font=("Consolas", 16), fg="white", bg="Green", relief="sunken")
        else:
            self.status = Label(self.right, text="Stopped", font=("Consolas", 16), fg="white", bg="Red", relief="sunken")
            
        self.status.grid(row=5, column=0, padx=10, pady=0)
        self.term_lb.insert(END, f"Connected to {self.session.host}! Output from shell commands will appear here")
        
    def run_shell_cmd(self):
        output = self.session.do_shell_cmd(self.shell_entry.get())
        self.term_lb.insert(END, f"{LF}{self.session.host}> {self.shell_entry.get()}")
        self.term_lb.insert(END, *output)
        self.term_lb.insert(END, "========== end of message ==========")
        self.shell_entry.delete(0, END)
        self.term_lb.yview(END)
        
    def reconnect(self): 
        self.host, self.user, self.passwd = self.get_passwd()
        self.session = RemoteSession(self.host, self.user, self.passwd)
        
    def edit_props(self):
        self.session.edit_remote_file(f"/home/{self.user}/server/server.properties")
    
    def launch_shell(self):
        subprocess.Popen(["cmd", "/K", f"ssh {USER}@{REMOTE_HOST}"])
        
    def run_server_cmd(self):
        self.session.do_server_cmd(self.server_entry.get())
        self.server_entry.delete(0, END)
        
    def update_server_output(self):
        # get the output
        output = self.session.do_shell_cmd(f"cat {SCREEN_LOG_FILE}")
        p = '\n'.join(output)
                
        if p != self.last_output:
            # append the diff and scroll to the bottom
            orig = self.last_output.splitlines()
            new = p.splitlines()
            diff = difflib.ndiff(orig, new)
            added = [line[2:] for line in diff if line.startswith('+ ')]
            
            for line in added:
                self.server_lb.insert(END, line)
            self.server_lb.yview(END)
            self.last_output = p
            
    def update_cpu_mem(self):
        cpu = self.session.do_shell_cmd("awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else print ($2+$4-u1) * 100 / (t-t1); }' <(grep 'cpu ' /proc/stat) <(sleep 1;grep 'cpu ' /proc/stat)")
        cpustr = "\n".join(cpu)
        if float(cpustr) >= 95:
            self.cpu.config(bg="red")
        elif float(cpustr) >= 75:
            self.cpu.config(bg="orange")
        else:
            self.cpu.config(bg="green")
        
        self.cpu.config(text=f"CPU: {cpustr[:-3]}%")
        
        mem = self.session.do_shell_cmd("free -m | awk 'NR==2 {print $3}'")
        memstr = "\n".join(mem)
        if float(memstr) >= 15000:
            self.mem.config(bg="red")
        elif float(cpustr) >= 15000:
            self.mem.config(bg="orange")
        else:
            self.mem.config(bg="green")
        
        self.mem.config(text="MEM: " + memstr + "mb")
        
    def start_server(self):
        self.session.do_shell_cmd(f"cd {SERVER_DIR} && screen -L -Logfile stdout.log -dmS {SCREEN_SESSION} bash start.sh && > stdout.log")
        self.term_lb.insert(END, f"{LF}{self.session.host}> {self.shell_entry.get()}")
        self.term_lb.insert(END, f"cd {SERVER_DIR} && screen -L -Logfile stdout.log -dmS {SCREEN_SESSION} bash start.sh && > stdout.log")
        self.status.config(text="Running", bg="green")
    
    def stop_server(self):
        self.session.do_server_cmd("saveall")
        self.session.do_server_cmd("stop")
        self.status.config(text="Stopped", bg="red")
        
    def restart_server(self):
        self.stop_server()
        sleep(60)
        self.start_server()
    
    def get_passwd(self):
        ret = ()
        
        dialog = Toplevel(root)
        dialog.title("Connect to remote host")
        
        host = StringVar(value=REMOTE_HOST)
        user = StringVar(value=USER)
        pas  = StringVar()

        # Add labels and entry widgets
        Label(dialog, text="host:").grid(row=0, column=0, padx=10, pady=5)
        entry1 = Entry(dialog, textvariable=host)
        entry1.grid(row=0, column=1, padx=10, pady=5)

        Label(dialog, text="user:").grid(row=1, column=0, padx=10, pady=5)
        entry2 = Entry(dialog, textvariable=user)
        entry2.grid(row=1, column=1, padx=10, pady=5)
        
        Label(dialog, text="password:").grid(row=2, column=0, padx=10, pady=5)
        entry3 = Entry(dialog, textvariable=pas, show='*')
        entry3.grid(row=2, column=1, padx=10, pady=5)

        def get_resp():
            dialog.destroy()
            nonlocal ret 
            ret = host.get(), user.get(), pas.get()

        # Add a submit button
        submit_button = Button(dialog, text="connect", command=lambda: get_resp())
        submit_button.grid(row=3, columnspan=2, pady=10)
        
        dialog.grab_set()
        dialog.wait_window()

        return ret

class RemoteSession:
    
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.client.connect(self.host, username=self.user, password=self.passwd)
        except Exception as e:
            msg = messagebox.showinfo("yikes something broke :(", 
                                      f"connection closed by the remote host {LF}{e}")
            exit(1)

    def __del__(self):
        self.client.close()
        
    def do_shell_cmd(self, command):
        retval = []
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            for line in stdout:
                retval.append(line.strip())
                
            for line in stderr:
                retval.append(line.strip())
            
        except Exception as e:
            retval.append("yikes something broke :( (exec_command() failed)") 
            retval.append(e)
            
        return retval
    
    def do_server_cmd(self, command):
        # send command to the relavant session
        output = self.do_shell_cmd(f"screen -S {SCREEN_SESSION} -X stuff '{command}'`echo -ne \015`")
        print(f"output {output}")
        
    def edit_remote_file(self, filename):
        sftp = self.client.open_sftp()
        sftp.get(filename, "./tmp.txt")
        sftp.close()
        
        subprocess.run(["notepad.exe", "./tmp.txt"])
        
        sftp = self.client.open_sftp()
        sftp.put("./tmp.txt", filename)
        sftp.close()

        os.remove("./tmp.txt")
        
        messagebox.showinfo("Restart Required!", "you must restart the server for changes to take effect.")

gui = TkGUI(root)

def update():
    threading.Thread(target=gui.update_server_output, daemon=True).start()
    threading.Thread(target=gui.update_cpu_mem, daemon=True).start()
    root.after(5000, update)

root.after(5000, update)
root.mainloop() 