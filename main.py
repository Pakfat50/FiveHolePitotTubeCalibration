"""Application entry point for the 5-hole Pitot calibration GUI."""


def main() -> None:
    """Construct application dependencies and start the GUI.

    The concrete composition follows the layered dependency direction defined in
    the architecture: Presentation -> Application -> Domain/Core, while file I/O
    remains in Infrastructure.

    Requirements:
        REQ-GUI-004
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
