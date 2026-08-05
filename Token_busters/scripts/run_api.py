from __future__ import annotations


def main() -> None:
    from _bootstrap import ensure_src_on_path

    ensure_src_on_path()

    from cx_agent.api.app import run

    run()


if __name__ == "__main__":
    main()
