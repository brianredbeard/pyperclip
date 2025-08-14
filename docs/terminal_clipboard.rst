.. _terminal_clipboard:

==================================================
Terminal Clipboard Support (OSC 52 & OSC 5522)
==================================================

Pyperclip includes support for two terminal-based clipboard protocols, OSC 52 and OSC 5522. These are used as a fallback on Linux systems when traditional clipboard utilities (``xclip``, ``xsel``, ``wl-clipboard``) are not available. This allows `pyperclip` to work seamlessly in headless environments, such as over an SSH connection or within terminal multiplexers like ``tmux`` and ``screen``.

This document provides a detailed breakdown of these protocols, how they are implemented in `pyperclip`, and the security considerations involved.

.. note::

   The ``paste()`` functionality for these protocols is intentionally disabled in `pyperclip`. Programmatic reading of the clipboard via terminal escape sequences is a significant security risk and is not widely supported by terminal emulators.

---

OSC 52: The de facto Standard
=============================

OSC 52 is a widely adopted terminal control sequence for interacting with the system clipboard. Its specification is maintained as part of the XTerm documentation, which serves as the de facto standard.

- **Authoritative Specification:** `XTerm Control Sequences - OSC 52 <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Operating-System-Commands>`_

Protocol Breakdown
------------------

The OSC 52 sequence for writing to the clipboard follows this structure:

.. code-block:: none

   \x1b]52;{selection};{data}\x07

Each component is explained below:

*   ``\x1b]`` (ESC ``]``): This is the **Operating System Command (OSC)** initiator. It is a standard sequence defined by ECMA-48 that tells the terminal emulator to interpret the following characters as a command for the terminal itself, not as text to be displayed.
*   ``52``: This is the identifier for the clipboard operation.
*   ``;``: A literal semicolon character, used as a parameter separator.
*   ``{selection}``: A character indicating which clipboard to use. `pyperclip` uses:
    *   ``c``: The system clipboard (the default).
    *   ``p``: The primary selection (used when ``primary=True``).
*   ``;``: Another parameter separator.
*   ``{data}``: The text to be copied, encoded in **Base64** (RFC-4648). Base64 encoding ensures that any binary data or special characters are represented using a safe, printable subset of ASCII characters (``A-Z``, ``a-z``, ``0-9``, ``+``, ``/``, ``=``). This prevents the data from being misinterpreted as other control sequences.
*   ``\x07`` (BEL): This is the **String Terminator (ST)**, which marks the end of the OSC sequence. XTerm and other terminals also accept the Bell character (``\x07``) for this purpose.

Example Sequence
~~~~~~~~~~~~~~~~

To copy the string ``"Hello"``, `pyperclip` performs the following steps:
1.  The string is encoded to Base64: ``"Hello"`` -> ``"SGVsbG8="``.
2.  The full OSC 52 sequence is constructed (for the default clipboard): ``\x1b]52;c;SGVsbG8=\x07``.

This byte sequence is then written to the controlling terminal (``/dev/tty``). The terminal emulator receives these bytes, recognizes the OSC 52 command, decodes the Base64 data, and places the resulting ``"Hello"`` string into the system clipboard.

Terminal Multiplexer Passthrough
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When running inside ``tmux`` or ``screen``, the OSC 52 sequence must be wrapped in a special "passthrough" sequence so that the multiplexer forwards it to the host terminal instead of trying to interpret it.

*   **tmux:** ``\x1bPtmux;\x1b{...OSC 52 sequence...}\x1b\\``
*   **screen:** ``\x1bP{...OSC 52 sequence...}\x1b\\``

``\x1bP`` is the **Device Control String (DCS)** initiator, which tells the multiplexer to handle the sequence. The multiplexer then passes the inner OSC 52 command to the outer terminal.

---

OSC 5522: The Kitty Protocol
============================

OSC 5522 is an advanced clipboard protocol developed for the Kitty terminal. It extends OSC 52 to support modern features, most notably the ability to send large amounts of data by splitting it into chunks.

- **Authoritative Specification:** `Kitty Clipboard Protocol <https://sw.kovidgoyal.net/kitty/clipboard/#writing-data-to-the-system-clipboard>`_

Protocol Breakdown
------------------

Writing to the clipboard with OSC 5522 is a multi-step process:

1.  **Initiate Write:** A sequence is sent to begin the clipboard write operation.
    *   Sequence: ``\x1b]5522;type=write\x1b\\``
    *   ``5522`` is the Kitty-specific command number.
    *   ``type=write`` indicates a write operation.

2.  **Send Data Chunks:** The data is sent in one or more chunks, each with its own OSC 5522 sequence. `pyperclip` uses a chunk size of 4096 bytes.
    *   Sequence: ``\x1b]5522;type=wdata:mime=text/plain;{data}\x1b\\``
    *   ``type=wdata`` indicates a data packet.
    *   ``mime=text/plain`` specifies the data type.
    *   ``{data}`` is a chunk of the text, encoded in **Base64**.

3.  **Finalize Write:** A final sequence is sent to signal that all data has been transmitted.
    *   Sequence: ``\x1b]5522;type=wdata\x1b\\`` (note the empty data field).

Example Sequence
~~~~~~~~~~~~~~~~

To copy the string ``"Hello"``:
1.  Start: ``\x1b]5522;type=write\x1b\\``
2.  Data: ``\x1b]5522;type=wdata:mime=text/plain;SGVsbG8=\x1b\\``
3.  End: ``\x1b]5522;type=wdata\x1b\\``

Multiplexer passthrough sequences for ``tmux`` and ``screen`` are handled similarly to OSC 52.

---

Security Considerations
=======================

The use of these terminal protocols has been implemented with security as a primary concern.

1.  **No Arbitrary Code Execution:** OSC sequences are *not* shell commands and are not executed by the shell. They are instructions interpreted by the terminal emulator's own state machine. The sequences are strictly formatted, and there is no mechanism within them to execute arbitrary code.

2.  **Safe Data Encoding:** All clipboard content is Base64 encoded. This ensures that the data being transmitted is confined to a safe subset of characters and cannot be crafted to inject other terminal control sequences or malicious shellcode. The terminal's role is to decode this data and place it in the clipboard, not to execute it.

3.  **Write-Only Implementation:** `pyperclip` only implements the "copy" (write) part of these protocols. The "paste" (read) functionality is explicitly disabled because allowing a program running over SSH to silently read the local clipboard is a significant security vulnerability.

4.  **Trusted Terminal:** This entire mechanism relies on a trusted, spec-compliant terminal emulator. Users should always use well-maintained and reputable terminal software.
