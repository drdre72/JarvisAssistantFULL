"""Retired vendor-backed wake listener.

The exposed Picovoice key cannot enable this local entry point. Use the
in-app microphone control until a keyless offline wake word is implemented.
"""


def main():
    raise SystemExit(
        "Picovoice wake listener is disabled; use the in-app microphone control."
    )


if __name__ == "__main__":
    main()
