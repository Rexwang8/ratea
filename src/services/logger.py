# src/services/logger.py
from rich.console import Console as rc



class Logger:
    console = rc()
    history = []
    debug_level = 0  # 0=ALL, 1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL

    @staticmethod
    def RichPrint(message: str, logType: str = "info"):
        """Print messages to console with rich formatting."""

        msg_level = {
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }

        if msg_level.get(logType, 1) >= Logger.debug_level:
            if logType == "info":
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

    @staticmethod
    def info(message: str):
        Logger.RichPrint(message, "info")

    @staticmethod
    def warning(message: str):
        Logger.RichPrint(message, "warning")

    @staticmethod
    def error(message: str):
        Logger.RichPrint(message, "error")

    @staticmethod
    def critical(message: str):
        Logger.RichPrint(message, "critical")

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
