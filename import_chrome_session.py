from argparse import ArgumentParser
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

try:
    from instaloader import ConnectionException, Instaloader
except ModuleNotFoundError:
    raise SystemExit("Instaloader not found.\n  pip install [--user] instaloader")


def get_cookiefile():
    default_cookiefile = {
        "Windows": "~/AppData/Local/Google/Chrome/User Data/Default/Network/Cookies",
        "Darwin": "~/Library/Application Support/Google/Chrome/Default/Cookies",
        "Linux": "~/.config/google-chrome/Default/Cookies",
    }.get(system(), "")
    cookiefiles = glob(expanduser(default_cookiefile))
    if not cookiefiles:
        raise SystemExit("No Chrome cookies file found. Use -c COOKIEFILE.")
    return cookiefiles[0]


def import_session(cookiefile, sessionfile):
    print("Using cookies from {}.".format(cookiefile))
    conn = connect(cookiefile)
    try:
        cookie_data = conn.execute(
            "SELECT name, value FROM cookies WHERE host_key LIKE '%instagram.com'"
        )
    except OperationalError:
        raise SystemExit("Error accessing Chrome cookies. Make sure Chrome is closed.")
    instaloader = Instaloader(max_connection_attempts=1)
    for cookie in cookie_data:
        instaloader.context._session.cookies.set(cookie[0], cookie[1])
    username = instaloader.test_login()
    if not username:
        raise SystemExit("Not logged in. Are you logged in successfully in Chrome?")
    print("Imported session cookie for {}.".format(username))
    instaloader.context.username = username
    instaloader.save_session_to_file(sessionfile)


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("-c", "--cookiefile")
    p.add_argument("-f", "--sessionfile")
    args = p.parse_args()
    try:
        import_session(args.cookiefile or get_cookiefile(), args.sessionfile)
    except (ConnectionException, OperationalError) as e:
        raise SystemExit("Cookie import failed: {}".format(e))
