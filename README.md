# Description
Check who doesn't follow you back on Instagram without providing your password.

# Purpose
I created this app because i wanted to check who unfollows me on Instagram without giving my password to third party applications. You never know who they sell your data to.

# How It Works
Bacially you log in to your Instagram account on https://www.instagram.com/ using Firefox (other browsers are not supported at the moment) and then the app will use your session cookie to fetch the data. The only thing that you need to provide the app with is your instagram handle (i.e. your username).

![image](https://github.com/djomarkaram/InstagramFollowers/assets/65378783/2ef08f69-35da-426c-8780-8270ef4a4922)

# Links/References
This app uses the `instaloader` library in Python https://instaloader.github.io/index.html. I used the code that the library provides to import the session cookie from Firefox which can be found in the file `import_firefox_session.py` or on their website here https://instaloader.github.io/troubleshooting.html#login-error.

The `import_chrome_session.py` is a work in progress to be able to get the session cookie from Chrome.
