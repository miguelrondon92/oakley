"""Allow `python -m oakley` when the console script is unavailable."""

from oakley.cli import main

if __name__ == "__main__":
    main()
