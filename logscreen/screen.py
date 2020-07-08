class pycolor:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    END = '\033[0m'
    BOLD = '\038[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERCE = '\033[07m'

def logFatal(msg):
    print("[" + pycolor.RED + " FATAL " + pycolor.END + "] " + msg)

def logOK(msg):
    print("[" + pycolor.GREEN + "  O K  " + pycolor.END + "] " + msg)

def logWarning(msg):
    print("[" + pycolor.YELLOW + "WARNING" + pycolor.END + "] " + msg)


if __name__ == "__main__":
    msg = "test message"
    logFatal(msg)
    logOK(msg)
    logWarning(msg)