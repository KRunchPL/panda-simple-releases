import os
from pathlib import Path

import dotenv
import typer


def load_dotenv(env_vars_prefix: str) -> None:
    """
    Load environment variables from a custom or auto-discovered .env file.

    Checks for a custom file path defined in `{env_vars_prefix}_DOTENV_FILE`. If unset,
    searches for a standard `.env` file starting from the current working directory.

    :param env_vars_prefix: Prefix for the environment variable holding the target dotenv file path.
    """
    dotenv_file_override = os.getenv(f'{env_vars_prefix}_DOTENV_FILE')
    if dotenv_file_override:
        if not Path(dotenv_file_override).is_file():
            typer.echo(f'The specified dotenv file does not exist: {dotenv_file_override}', err=True)
            raise typer.Exit(code=1)
    else:
        dotenv_file_override = dotenv.find_dotenv(usecwd=True)
    dotenv.load_dotenv(dotenv_file_override, override=False)
