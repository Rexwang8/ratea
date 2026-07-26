# src/services/logger.py
from rich.console import Console as rc



class Logger:
    console = rc()
    history = []
    debug_level = 0  # -1=ALL, 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL

    def __init__(self, debug_level: int = 0):
        msg_level = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        Logger.debug_level = int(msg_level.get(debug_level, 0)) if isinstance(debug_level, str) else debug_level
        Logger.console.print(f"[bold cyan]Logger initialized with debug level {debug_level}[/bold cyan]")

    @staticmethod
    def _rich_print(message: str, logType: str = "info"):
        """Print messages to console with rich formatting."""

        msg_level = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }

        msg_level_num = msg_level.get(logType, 1)

        if msg_level_num >= Logger.debug_level:
            if logType == "debug":
                Logger.console.print(f"[bold blue][DEBUG][/bold blue] {message}")
            elif logType == "info":
                Logger.console.print(f"[bold green][INFO][/bold green] {message}")
            elif logType == "warning":
                Logger.console.print(f"[bold yellow][WARNING][/bold yellow] {message}")
            elif logType == "error":
                Logger.console.print(f"[bold red][ERROR][/bold red] {message}")
            elif logType == "critical":
                Logger.console.print(f"[bold red][CRITICAL][/bold red] {message}", style="blink")



        history_entry = f"[{logType.upper()}] {message}"
        Logger.history.append(history_entry)

        if len(Logger.history) > 1000:
            Logger.history = Logger.history[-1000:]

    # Public logging methods

    # Debug is for detailed information, typically of interest only when diagnosing problems.
    @staticmethod
    def debug(message: str):
        Logger._rich_print(message, "debug")

    # Info is the default logging level, used for general information about the application's operation.
    @staticmethod
    def info(message: str):
        Logger._rich_print(message, "info")

    # Warning is for potentially harmful situations that are not necessarily errors but may require attention.
    @staticmethod
    def warning(message: str):
        Logger._rich_print(message, "warning")

    # Error is for error events that might still allow the application to continue running.
    @staticmethod
    def error(message: str):
        Logger._rich_print(message, "error")

    # Critical is for very severe error events that will presumably lead the application to abort.
    @staticmethod
    def critical(message: str):
        Logger._rich_print(message, "critical")

    @staticmethod
    def get_history():
        return Logger.history

    @staticmethod
    def nprint(message: str):
        """Normal print without formatting."""
        print(message)
        Logger.history.append(message)
        if len(Logger.history) > 1000:
            Logger.history = Logger.history[-1000:]
