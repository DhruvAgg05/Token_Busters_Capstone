from __future__ import annotations


def main() -> None:
    from _bootstrap import ensure_src_on_path
    import sys

    ensure_src_on_path()
    from cx_agent.cli.main import main as cli_main

    sys.argv = [sys.argv[0], "evals", "--show-details", *sys.argv[1:]]
    cli_main()


if __name__ == "__main__":
    main()
