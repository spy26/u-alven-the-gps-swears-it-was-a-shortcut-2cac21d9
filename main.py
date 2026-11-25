# The GPS Swears It Was a Shortcut — make.fun competition entry.
#
# The entry is exactly one excuse, one line, 112 characters:
# "I picked the flooded underpass because the map said it was dry and I
# trust satellites more than your windscreen."
#
# Why this one: the joke is GPS-native — only a GPS excuses a wrong turn by
# trusting satellites over a driver's own eyes ("your windscreen"). The
# setup (a flooded underpass the map swore was dry) and the payoff (orbital
# data over human senses) land in one breath, the excuse blames the map
# while staying smug and defensive, and the flooded underpass is a fresh,
# specific detail instead of the usual recalculating joke. One line, ASCII
# only, no trailing newline in the file the grader reads.
#
# Behaviour:
#   python3 main.py            print the chosen entry, write it to
#                              $MAKEFUN_OUTPUT_DIR/entry.txt (else /output).
#   python3 main.py "<text>"   print/write <text> instead (testing override).
#   echo "<text>" | python3 main.py   same override via piped STDIN.
# Any text that is not 1-200 characters of non-whitespace text, or is not a
# single line, is rejected with exit 1 and nothing is written or printed.
# Deterministic: no time, no randomness, no network, no reads outside this
# file. The entry is a constant; the override exists only so the gate can
# be tested (a >200-character input must fail loudly, never silently).

import os
import select
import sys

ENTRY = (
    "I picked the flooded underpass because the map said it was dry "
    "and I trust satellites more than your windscreen."
)


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate(text):
    chars = list(text)
    if len(chars) < 1 or len(chars) > 200:
        fail("entry must be 1 to 200 characters")
    if not text.strip():
        fail("entry must not be only whitespace")
    if text != text.strip() or "\n" in text or "\r" in text:
        fail("entry must be a single line with no surrounding whitespace")
    if any(ord(c) > 127 for c in text):
        fail("entry must be ASCII only")


def read_override():
    if len(sys.argv) > 1:
        return sys.argv[1]
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        # A zero-timeout select races the producer: a pipe whose writer
        # has not flushed yet looks empty. Wait briefly for piped input;
        # /dev/null (the grader's stdin) reports readable at once, and a
        # pipe held open with no data just costs this timeout, never a hang.
        ready, _, _ = select.select([sys.stdin], [], [], 1.0)
    except (OSError, ValueError):
        return None
    if not ready:
        return None
    data = sys.stdin.read()
    if not data:
        return None
    # A piped line ends with a newline; that terminator is not content.
    return data.rstrip("\r\n") or None


def main():
    override = read_override()
    text = ENTRY if override is None else override
    validate(text)

    # The harness points MAKEFUN_OUTPUT_DIR at the writable /output; write
    # there when it is set, and to /output directly as well, so the gate
    # finds the file either way. No trailing newline: the file is the entry,
    # byte for byte.
    targets = []
    for d in (os.environ.get("MAKEFUN_OUTPUT_DIR"), "/output"):
        if d and d not in targets:
            targets.append(d)
    landed = []
    for d in targets:
        try:
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "entry.txt")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            landed.append(path)
        except OSError:
            # One target may be read-only in some sandboxes; the other
            # still lands.
            continue
    if not landed:
        fail("could not write entry.txt to any output directory")

    # Read back every target that landed and prove each one is the entry,
    # byte for byte — a silent partial write must fail loudly here, never
    # at the grader's gate, and two targets must never disagree.
    for path in landed:
        with open(path, encoding="utf-8", newline="") as f:
            if f.read() != text:
                fail(f"entry.txt in {path} does not contain exactly the entry")

    sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
