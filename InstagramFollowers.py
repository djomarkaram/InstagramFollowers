import os
import threading
import sys
import instaloader
import tkinter as tk
from argparse import ArgumentParser
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

try:
    from instaloader import ConnectionException, Instaloader
except ModuleNotFoundError:
    raise SystemExit("Instaloader not found.\n  pip install [--user] instaloader")


class Console:
    def __init__(self, parent):
        self.parent = parent

        # Create a frame to hold the text widget and scrollbar.
        frame = tk.Frame(self.parent)
        frame.grid(row=6, column=0, columnspan=1, sticky=tk.NSEW, padx=30, pady=0)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Create the text widget and scrollbar.
        self.text = tk.Text(frame, wrap="word", state="disabled", relief=tk.FLAT)
        self.scrollbar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)

        # Pack the text widget and scrollbar into the frame.
        self.text.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS)

        # Redirect stdout and stderr to the console.
        # sys.stdout = self
        # sys.stderr = self

    def write(self, message, is_error=False):
        # Write the message to the console.
        self.text.configure(state="normal")
        if is_error:
            self.text.insert(tk.END, f"Error: {str(message)}\n")
        else:
            self.text.insert(tk.END, f"{str(message)}\n")
        self.text.configure(state="disabled")

        # Scroll to the bottom.
        self.text.yview_moveto(1.0)
        root.update()

    def clear_console(self):
        self.text.configure(state="normal")
        self.text.delete(1.0, "end")
        self.text.configure(state="disabled")
        return

    def flush(self):
        pass


def initialize_window():
    root.title("Who doesn't follow me back on Instagram?")
    root.config(border=5, width=430, height=330)
    root.resizable(True, True)
    root.minsize(450, 500)

    # This is set to False to prevent tkinter from resizing the window based on the widgets that are in place.
    root.grid_propagate(True)
    # This stretches the entire column when we resize the window horizontally.
    root.grid_columnconfigure(0, weight=2)
    # This configures the 6th row to have a weight of 1.
    root.grid_rowconfigure(6, weight=1)
    # This removes focus from the text boxes if we click outside of them.
    root.bind_all("<Button-1>", lambda event: event.widget.focus_set())

    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    left_padding = int(screen_width/2 - window_width/2)
    top_padding = int(screen_height/2 - window_height/2)

    # Set the window position.
    root.geometry(f"{window_width}x{window_height}+{left_padding}+{top_padding}")

def set_theme(theme="Dark"):
    if theme == "Light":
        root.config(background=WHITE)
        label.config(bg=WHITE, fg=BLACK)
        username_text_box.config(bg=GREY2, fg=BLACK, highlightcolor=BLUE, highlightbackground=GREY, insertbackground="black")
        button.config(bg=BLUE, fg=WHITE)
        separator.config(bg=GREY)
        console_text.config(bg=WHITE, fg=BLACK)
        clear_button.config(bg=GREY, fg=BLUE)
        console.text.config(bg=GREY, fg=BLACK)
        light_button.config(bg=GREY, fg=BLACK, selectcolor=GREY)
        dark_button.config(bg=GREY, fg=BLACK, selectcolor=GREY)
    else:
        root.config(background=BLACK)
        label.config(bg=BLACK, fg=WHITE)
        username_text_box.config(bg=DARK_GREY, fg=WHITE, highlightcolor=BLUE, highlightbackground=DARK_GREY2, insertbackground="white")
        button.config(bg=BLUE, fg=WHITE)
        separator.config(bg=DARK_GREY2)
        console_text.config(bg=BLACK, fg=WHITE)
        clear_button.config(bg=DARK_GREY, fg=BLUE)
        console.text.config(bg=DARK_GREY, fg=WHITE)
        menu.config(bg=DARK_GREY, fg=GREY, activeborderwidth=5, activeforeground=WHITE, borderwidth=0)
        light_button.config(bg=DARK_GREY, fg=WHITE, selectcolor=BLACK)
        dark_button.config(bg=DARK_GREY, fg=WHITE, selectcolor=BLACK)

def try_get_accounts(username):
    # Clear console first.
    console.clear_console()

    if username.lower() == "enter your username":
        console.write("Please enter a valid username", True)
        return
    elif not username.lower() or username.lower() == "":
        console.write("Username cannot be null nor empty. Please enter a valid username and try again.", True)
        return
    elif username.isspace():
        console.write("Username contains only whitespace. Please enter a valid username and try again.", True)
        return

    button.config(state='disabled')
    get_accounts_thread = threading.Thread(target=get_accounts(username))
    get_accounts_thread.start()

def get_accounts(username):
    global session_file
    session_file = f"session-{username}"

    session_import_successful = try_import_session()
    if not session_import_successful:
        return
    
    try:
        instaloader_dir = os.path.expandvars(r'%LOCALAPPDATA%\Instaloader')
        L.load_session_from_file(username.strip(), filename=f"{instaloader_dir}\\{session_file}")
    except FileNotFoundError:
        console.write(f"FileNotFoundError: File 'session-{username}' not found at path '{instaloader_dir}'. " + 
            "Make sure you are logged in to your Instagram account on FireFox.")
        button.config(state='normal')
        return
    
    console.write("Successfully logged in using session's cookie. Fetching profile's metadata...")
    profile = instaloader.Profile.from_username(L.context, username)

    console.write("Successfully fetched profile's metadata. Checking the accounts who don't follow you back...")

    following_list, following_count = get_following_list(profile)
    followers_list, followers_count = get_followers_list(profile)
    not_following_back_count = get_accounts_not_following_back(following_list, followers_list)

    console.write("Successfully fetched the accounts who don't follow you back. Below is your summary:")
    console.write(f"\tYou are following {following_count} account(s),")
    console.write(f"\tyou have {followers_count} follower(s), ")
    console.write(f"\tand {not_following_back_count} account(s) don't follow you back.")

    button.config(state='normal')
    return

def try_import_session():
    p = ArgumentParser()
    p.add_argument("-c", "--cookiefile")
    p.add_argument("-f", "--sessionfile")
    args = p.parse_args()
    try:
        return import_session(args.cookiefile or get_cookiefile(), args.sessionfile)
    except (ConnectionException, OperationalError) as e:
        console.write(f"Cookie import failed: {e}")
        button.config(state='normal')
        return False

def import_session(cookiefile, sessionfile):
    console.write(f"Using cookies from {cookiefile}.")
    conn = connect(f"file:{cookiefile}?immutable=1", uri=True)
    try:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'"
            )
    except OperationalError:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
            )
        button.config(state='normal')
    
    instaloader = Instaloader(max_connection_attempts=1)
    instaloader.context._session.cookies.update(cookie_data)

    username = instaloader.test_login()
    if not username:
        console.write(f"Invalid username or not logged in. Are you logged in successfully to your" + 
                      " Instagram account on Firefox using the correct username? If not, please log in and try again.", True)
        button.config(state='normal')
        return False
    
    console.write(f"Imported session cookie for {username}.")
    instaloader.context.username = username
    instaloader.save_session_to_file(sessionfile)
    return True

def get_cookiefile():
    default_cookiefile = {
        "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
        "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
    }.get(system(), "~/.mozilla/firefox/*/cookies.sqlite")
    cookiefiles = glob(expanduser(default_cookiefile))
    if not cookiefiles:
        raise SystemExit("No Firefox cookies.sqlite file found. Use -c COOKIEFILE.")
    return cookiefiles[0]

def get_following_list(profile):
    following_list = []
    count = 0
    for followee in profile.get_followees():
        following_list.append(followee.username)
        console.write(f"Followee: {following_list[count]}")
        count = count + 1
        root.update_idletasks()
    
    write_to_file("my_followings.txt", following_list, count)

    return following_list, count

def get_followers_list(profile):
    followers_list = []
    count = 0
    for follower in profile.get_followers():
        followers_list.append(follower.username)
        console.write(f"Follower: {followers_list[count]}")
        count = count + 1
        root.update_idletasks()
    
    write_to_file("my_followers.txt", followers_list, count)

    return followers_list, count

def get_accounts_not_following_back(following_list, followers_list):
    accounts_not_following_back = []
    count = 0
    for followee in following_list:
        if followers_list.__contains__(followee):
            continue
        else:
            accounts_not_following_back.append(followee)
            console.write(f"Not following: {followee}")
            count = count + 1
            root.update_idletasks()

    write_to_file("accounts_not_following_back.txt", accounts_not_following_back, count)

    return count

def write_to_file(file_name, account_list, count):
    results_directory = 'Results'

    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    path = os.path.join(results_directory, file_name)

    with open(path, "w") as fp:
        if file_name == "my_followings.txt":
            fp.write(f"============= You are following {count} accounts =============")
        elif file_name == "my_followers.txt":
            fp.write(f"============= You have {count} followers =============")
        elif file_name == "accounts_not_following_back.txt":
            fp.write(f"============= There are {count} accounts not following you back =============")
        else:
            fp.write(f"============= An Error Occurred! =============")

        for account in account_list:
            fp.write("%s\n" % account)

        fp.close()
    
    console.write(f"============= Successfully wrote to file '{file_name}' =============")

def on_focus_in(entry, placeholder):
    if entry._name == "passwordTextBox":
        entry.config(show="*")
        
    if entry.get() == placeholder:
        entry.delete(0, 'end')

def on_focus_out(entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(show="")    

def do_popup(event):
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

def copy_func():
    try:
        selected_text = username_text_box.selection_get()
        if selected_text:
            root.clipboard_clear()
            root.clipboard_append(selected_text)
    except tk.TclError:
        pass

def paste_func():
    if root.clipboard_get() != "":
        try:
            selected_text = username_text_box.selection_get()
            if selected_text:
                username_text_box.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

        try:
            cursorPosition = username_text_box.index(tk.INSERT)
            username_text_box.insert(cursorPosition, root.clipboard_get())
            return 'break'
        except tk.TclError:
            pass

def clear_func():
    username_text_box.delete(0, tk.END)

def close_app():
    sys.exit("Closing the app...")

root = tk.Tk()
L = instaloader.Instaloader()

'''CREATE THE UI'''
WHITE = "#ffffff"
BLACK = "#000000"
BLUE = "#0095f6"
GREY = "#f0f0f0"
GREY2 = "#fafafa"
DARK_GREY = "#121212"
DARK_GREY2 = "#1d1d1d"

initialize_window()

# Create the Instagram text label.
label = tk.Label(root, text="Instagram", font=("Impact 35"))
label.grid(row=0, column=0, sticky=tk.NSEW, padx= 30, pady=(40, 50))

# Create the username entry textbox.
username_text_box = tk.Entry(root, width=30, name="usernameTextBox", highlightthickness=1, font="Helvetica 12", relief=tk.FLAT, state='normal')
username_text_box.grid(row=1, column=0, columnspan=1, sticky=tk.NSEW, padx=30, pady=(0, 5))
username_placeholder_text = "Enter your username"
username_text_box.insert(0, username_placeholder_text)
username_text_box.bind("<FocusIn>", lambda args: on_focus_in(username_text_box, username_placeholder_text))
username_text_box.bind("<FocusOut>", lambda args: on_focus_out(username_text_box, username_placeholder_text))
username_text_box.bind("<Button-3>", do_popup)

# Create the Who Doesn't Follow Me Back button.
button = tk.Button(root, text="Who Doesn't Follow Me Back", font=("Helvetica", 12, "bold"), width=30, height=1, relief=tk.FLAT,
    command= lambda: try_get_accounts(username_text_box.get()))
button.grid(row=3, column=0, padx=30, pady=15, sticky=tk.NSEW)

# Create a separator.
separator = tk.Frame(root, width=30, height=1)
separator.grid(row=4, column=0, sticky=tk.EW, padx=30, pady=(10, 0))

# Create the Console text.
console_text = tk.Label(root, text="Console:", font=("Helvetica", 12))
console_text.grid(row=5, column=0, sticky=tk.W, padx= 30, pady=(25, 4))

# Create the Clear button.
clear_button = tk.Button(root, text="Clear", font=("Helvetica", 10, "bold"), width=10, height=1, relief=tk.FLAT, command= lambda: console.clear_console())
clear_button.grid(row=5, column=0, padx=(0, 30), pady=(25, 4), sticky=tk.E)

# Create the actual Console.
console = Console(root)

# Create the Theme radio buttons.
var = tk.StringVar()
light_button = tk.Radiobutton(root, text="Light", variable=var, value="Light", width=10, height=1, relief=tk.FLAT, command=lambda: set_theme(var.get()))
light_button.grid(row=7, column=0, padx=(30, 0), pady=(25, 25), sticky=tk.W)
dark_button = tk.Radiobutton(root, text="Dark", variable=var, value="Dark", width=10, height=1, relief=tk.FLAT, command=lambda: set_theme(var.get()))
dark_button.grid(row=7, column=0, padx=(0, 30), pady=(25, 25), sticky=tk.E)

# Add the right click menu popup.
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="   Clear   ", command= lambda: clear_func())
menu.add_separator()
menu.add_command(label="   Copy   ", command= lambda: copy_func())
menu.add_command(label="   Paste   ", command= lambda: paste_func())

# Set the default theme.
dark_button.select()
set_theme("Dark")

# Keep the program running.
root.mainloop()


'''
Note #1
    Below is how you read a file if you needed it:
    my_file = open("my_followings.txt", "r")
    following_data = my_file.read()

    following_list = following_data.split("\n")
    my_file.close()
'''
'''
Note #2
    To use the login_using_session() method, you have to be logged in to your insta account on Firefox and follow these steps:

    1) Download and install Firefox for Windows
    2) Login to your Instagram account in Firefox
    3) Execute the snippet in a terminal/command line, e.g. with "python 615_import_firefox_session.py"
    4) Then, "instaloader -l USERNAME"
    5) Finally, run the "InstagramAnalytics.py" file in Visual Studio code and enter your USERNAME
    6) The application should generate 3 text files: 
        - my_followings.txt
        - my_followers.txt
        - accounts_not_following_back.txt
'''
'''
Note #3
    [dkaram]: Compare the old accounts that are not following me back to the ones that i just generated to see if someone unfollowed me.
    [dkaram]: Start using the ttk instead of tk in order to stylize everything to make it look modern.
    [dkaram]: Find a way to make this a standalone Windows app, MacOS app, and even a mobile app if possible instead of a script.
    [dkaram]: Find a way to get the cookie file from chrome.
'''
'''
To build this file and make it a .exe write the following in a terminal: pyinstaller --onefile -w .\InstagramAnalytics.py
'''
