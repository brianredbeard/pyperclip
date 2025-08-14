Pyperclip is a cross-platform Python module for copy and paste clipboard functions. It works with Python 2 and 3.

Install on Windows: `pip install pyperclip`

Install on Linux/macOS: `pip3 install pyperclip`

Al Sweigart al@inventwithpython.com
BSD License

Example Usage
=============

    >>> import pyperclip
    >>> pyperclip.copy('The text to be copied to the clipboard.')
    >>> pyperclip.paste()
    'The text to be copied to the clipboard.'


Currently only handles plaintext.

On Windows, no additional modules are needed.

On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.

On Linux, this module makes use of the `xclip`, `xsel`, or `wl-clipboard` commands, which can be installed via your distribution's package manager. For example, in Debian:
    sudo apt-get install xclip
    sudo apt-get install xsel
    sudo apt-get install wl-clipboard

It can also use the `qtpy` or `PyQt5` Python modules. If none of these are found, this module will automatically fall back to the OSC 52 and 5522 terminal escape sequences, which work in many modern terminal emulators and remote SSH sessions without needing any additional packages.

Support
-------

If you find this project helpful and would like to support its development, [consider donating to its creator on Patreon](https://www.patreon.com/AlSweigart).
