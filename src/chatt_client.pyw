import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from Crypto.PublicKey import RSA
import json
from secure_socket import secure_socket
import sys

class client:
    def __init__(self):
        self.connected = False
        
    def popup_window(self, message):
        popup = tk.Toplevel(self.root_window)
        popup.focus_force()
        popup.title('Message')
        popup.rowconfigure(0, weight=1)
        popup.columnconfigure(0, weight=1)
        popup.wm_attributes('-topmost', True)
        popup.geometry('400x200')
        message_label = tk.Label(popup, text=message)
        message_label.grid(row=0, column=0)
        accept_button = tk.Button(popup, text='Accept', width=20, command=popup.destroy)
        accept_button.grid(row=1, column=0, pady=20)
        popup.mainloop()
        
    def connect(self, *args):
        if not self.connected:
            server_address = self.server_address_entry.get()
            username = self.username_entry.get()
            password = self.password_entry.get()
            if (len(server_address) == 0) or (len(username) == 0) or (len(password) == 0):
                self.popup_window('Field(s) left empty.')
                return
            else:
                try:
                    server_address = server_address.split(':')
                    server_address[0] = socket.gethostbyname(server_address[0])
                    server_address[1] = int(server_address[1])
                    server_address = tuple(server_address)
                except:
                    self.popup_window('Invalid server address.')
                    return
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.socket.connect(server_address)
                    self.secure = secure_socket(self.socket, self.key_pair)
                    self.secure.handshake()
                    self.secure.sendall(username.encode())
                    motd = self.secure.recv(1024).decode()
                    self.secure.sendall(password.encode())
                    response = self.secure.recv(1024)
                except:
                    try:
                        self.socket.shutdown(1)
                        self.socket.close()
                    except:
                        pass
                    self.popup_window('Failed to connect to server.')
                    return
                if response == bytes(0):
                    self.socket.shutdown(1)
                    self.socket.close()
                    self.popup_window('Invalid username and/or password.')
                    return
                elif response == bytes(1):
                    self.socket.shutdown(1)
                    self.socket.close()
                    self.popup_window('User already connected.')
                    return
                elif response == bytes(2):
                    self.connected = True
                    self.kill_thread = False
                    threading.excepthook = self.excepthook
                    threading.Thread(target=self.recv_messages).start()
                    self.root_window.bind('<Return>', self.send_message)
                    self.status_label.config(text='Connected to {}:{}, MOTD: {}'.format(server_address[0], server_address[1], motd))
                    self.server_address_entry.delete(0, tk.END)
                    self.username_entry.delete(0, tk.END)
                    self.password_entry.delete(0, tk.END)
                    
    def disconnect(self):
        if self.connected:
            self.connected = False
            self.kill_thread = True
            self.socket.shutdown(1)
            self.socket.close()
            self.root_window.bind('<Return>', self.connect)
            self.output_box.configure(state='normal')
            self.output_box.delete(1.0, tk.END)
            self.output_box.yview(tk.END)
            self.output_box.configure(state='disabled')
            self.status_label.config(text='')
            
    def send_message(self, event):
        message = self.input_box.get()
        if message:
            self.secure.sendall(message.encode())
            self.input_box.delete(0, tk.END)
            
    def recv_messages(self):
        while True:
            message = self.secure.recv(1024).decode()
            self.output_box.configure(state='normal')
            self.output_box.insert(tk.END, message + '\n')
            self.output_box.yview(tk.END)
            self.output_box.configure(state='disabled')
            
    def excepthook(self, exception):
        if not self.kill_thread:
            self.socket.shutdown(1)
            self.socket.close()
            self.connected = False
            self.root_window.bind('<Return>', self.connect)
            self.output_box.configure(state='normal')
            self.output_box.delete(1.0, tk.END)
            self.output_box.yview(tk.END)
            self.output_box.configure(state='disabled')
            self.status_label.config(text='')
            try:
                self.popup_window('Disconnected from server.')
            except:
                pass
            
    def on_window_close(self):
        if self.connected:
            self.kill_thread = True
            self.socket.shutdown(1)
            self.socket.close()
        sys.exit()
        
    def main(self):
        self.root_window = tk.Tk()
        self.root_window.rowconfigure(0, weight=1)
        self.root_window.columnconfigure(0, weight=1)
        self.root_window.title('CHATT Client')
        self.root_window.bind('<Return>', self.connect)
        self.root_window.protocol('WM_DELETE_WINDOW', self.on_window_close)
        chat_frame = tk.LabelFrame(self.root_window, text='Chat')
        chat_frame.rowconfigure(1, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.grid(row=0, column=0, padx=3, pady=3, sticky='NESW')
        self.status_label = tk.Label(chat_frame, text='')
        self.status_label.grid(row=0, column=0, sticky='NESW')
        self.output_box = scrolledtext.ScrolledText(chat_frame)
        self.output_box.configure(state='disabled')
        self.output_box.grid(row=1, column=0, sticky='NESW')
        self.input_box = tk.Entry(chat_frame)
        self.input_box.grid(row=2, column=0, sticky='NESW')
        frame_group = tk.Frame(self.root_window)
        frame_group.rowconfigure(0, weight=1)
        frame_group.rowconfigure(1, weight=1)
        frame_group.columnconfigure(0, weight=1)
        frame_group.grid(row=0, column=1, sticky='NESW')
        info_frame = tk.LabelFrame(frame_group, text='Info')
        info_frame.grid(row=0, column=0, padx=3, pady=3, sticky='NESW')
        name_label = tk.Label(info_frame, text='CHATT Client', font=("Arial", 15))
        name_label.pack()
        acronym_label = tk.Label(info_frame, text='C: Compact\nH: Helpful\nA: Asynchronous\nT: Text\nT: Transmission', justify='left')
        acronym_label.pack()
        control_frame = tk.LabelFrame(frame_group, text='Control')
        control_frame.grid(row=1, column=0, padx=3, pady=3, sticky='NESW')
        input_group = tk.Frame(control_frame)
        input_group.pack(padx=5, pady=5)
        server_address_label = tk.Label(input_group, text='Server Address')
        server_address_label.grid(row=0, column=0, sticky='NESW')
        self.server_address_entry = tk.Entry(input_group, width=30)
        self.server_address_entry.grid(row=1, column=0, sticky='NESW')
        username_label = tk.Label(input_group, text='Username')
        username_label.grid(row=2, column=0, sticky='NESW')
        self.username_entry = tk.Entry(input_group)
        self.username_entry.grid(row=3, column=0, sticky='NESW')
        password_label = tk.Label(input_group, text='Password')
        password_label.grid(row=4, column=0, sticky='NESW')
        self.password_entry = tk.Entry(input_group)
        self.password_entry.grid(row=5, column=0, sticky='NESW')
        button_group = tk.Frame(control_frame)
        button_group.pack(padx=5, pady=5)
        connect_button = tk.Button(button_group, text='Connect', width=25, command=self.connect)
        connect_button.grid(row=0, column=0, sticky='NESW')
        disconnect_button = tk.Button(button_group, text='Disconnect', width=25, command=self.disconnect)
        disconnect_button.grid(row=1, column=0, sticky='NESW')
        while True:
            try:
                f = open('client_config.json', 'r')
                config = json.load(f)
                f.close()
                load_rsa_from_file = config['load_rsa_from_file']
                break
            except:
                f = open('client_config.json', 'w')
                f.write('{"load_rsa_from_file":false}')
                f.close()
        if load_rsa_from_file:
            while True:
                try:
                    f = open('client_rsa.pem', 'r')
                    break
                except:
                    f = open('client_rsa.pem', 'w')
                    f.write(RSA.generate(1024).exportKey().decode())
                    f.close()
            try:
                self.key_pair = RSA.importKey(f.read())
                f.close()
            except:
                self.popup_window('Invalid RSA keys. Delete client_rsa.pem to regenerate.\nRandomly generated RSA keys will be used for now.')
                self.key_pair = RSA.generate(1024)
        else:
            self.key_pair = RSA.generate(1024)
        self.root_window.mainloop()
        
if __name__ == '__main__':
    c = client()
    c.main()