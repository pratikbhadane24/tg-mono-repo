"""
CLI entry point for app module.

Usage:
    python -m app.cli add <chat_id> <name> [--join-model=invite_link]
    python -m app.cli list
    python -m app.cli remove <chat_id>
    python -m app.cli update <chat_id> --name=<name> [--join-model=<model>]
"""

if __name__ == "__main__":
    from app.cli import main

    main()
