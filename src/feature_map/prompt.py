"""Tiny terminal prompts: confirm (y/N) and an arrow-key select menu.

The arrow menu uses POSIX raw-mode terminal control when available and falls
back to a numbered list everywhere else. There are no third-party deps.
"""

import sys

UP_KEY = "A"
DOWN_KEY = "B"


def confirm(question, default=False):
    hint = " [Y/n]: " if default else " [y/N]: "
    try:
        answer = input(question + hint).strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer.startswith("y")


def select(question, options):
    """Return the chosen option, or None when the user skips.

    Arrow keys navigate, Enter selects, q/Ctrl-C skip. Falls back to a
    numbered list when raw terminal control is unavailable.
    """
    if not options:
        return None
    if len(options) == 1:
        return options[0]
    if sys.platform != "win32" and sys.stdin.isatty():
        try:
            return _arrow_select(question, options)
        except KeyboardInterrupt:
            raise
        except Exception:
            pass  # fall back to the numbered list
    return _numbered_select(question, options)


def _numbered_select(question, options):
    print(question)
    for i, option in enumerate(options):
        print("  {}) {}".format(i + 1, option))
    while True:
        try:
            answer = input("Pick 1-{} (blank to skip): ".format(len(options))).strip()
        except EOFError:
            return None
        if not answer:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print("Please enter a valid number.")


def _arrow_select(question, options):
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    index = 0

    sys.stdout.write("? " + question + "\n")

    def draw(redraw):
        if redraw:
            sys.stdout.write("\x1b[%dA" % len(options))
        for i, option in enumerate(options):
            marker = ">" if i == index else " "
            sys.stdout.write("\r\x1b[K%s %s\n" % (marker, option))
        sys.stdout.flush()

    try:
        tty.setraw(fd)
        draw(redraw=False)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                seq = sys.stdin.read(2)
                if seq == "[" + UP_KEY and index > 0:
                    index -= 1
                elif seq == "[" + DOWN_KEY and index < len(options) - 1:
                    index += 1
                draw(redraw=True)
            elif ch in ("\r", "\n"):
                sys.stdout.write("\n")
                return options[index]
            elif ch in ("q", "Q"):
                sys.stdout.write("\n")
                return None
            elif ch == "\x03":
                raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
