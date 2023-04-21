import os
import re
import platform
import shlex
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import Any, Callable

import typer
from click import BadParameter


class ModelOptions(str, Enum):
    GPT3 = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    GPT4_32K = "gpt-4-32k"


def get_edited_prompt() -> str:
    """
    Opens the user's default editor to let them
    input a prompt, and returns the edited text.

    :return: String prompt.
    """
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        # Create file and store path.
        file_path = file.name
    editor = os.environ.get("EDITOR", "vim")
    # This will write text to file using $EDITOR.
    os.system(f"{editor} {file_path}")
    # Read file when editor is closed.
    with open(file_path, "r", encoding="utf-8") as file:
        output = file.read()
    os.remove(file_path)
    if not output:
        raise BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output


def run_command(command: str, ask_inputs: bool = False) -> None:
    """
    Runs a command in the user's shell.
    It is aware of the current user's $SHELL.
    :param command: A shell command to run.
    :param ask_inputs: Prompt for concrete input if there are placeholders in the command
    """
    if ask_inputs:
        command = ask_command_inputs(command)

    if platform.system() == "Windows":
        is_powershell = len(os.getenv("PSModulePath", "").split(os.pathsep)) >= 3
        full_command = (
            f'powershell.exe -Command "{command}"'
            if is_powershell
            else f'cmd.exe /c "{command}"'
        )
    else:
        shell = os.environ.get("SHELL", "/bin/sh")
        full_command = f"{shell} -c {shlex.quote(command)}"

    os.system(full_command)
    

def ask_command_inputs(command: str) -> str:
    """
    Prompt user to input required arguments in the command.

    :param raw_command: command that may contain argument placeholders
    :return: complete command that is ready to be executed
    """
    raw_command = command
    variables = re.findall(r"\<([\w\- ]+)\>", raw_command)
    if len(variables) > 0:
        command = raw_command
        for var in dict.fromkeys(variables):
            value = typer.prompt(var)
            command = command.replace(f"<{var}>", value)
    return command


def option_callback(func: Callable) -> Callable:  # type: ignore
    def wrapper(cls: Any, value: str) -> None:
        if not value:
            return
        func(cls, value)
        raise typer.Exit()

    return wrapper
