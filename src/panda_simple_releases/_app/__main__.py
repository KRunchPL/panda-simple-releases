from typing import Annotated

import typer

from panda_simple_releases._app._version_handler import version_callback
from panda_simple_releases._run import run

from ._config import APP_NAME, ENV_VAR_PREFIX
from ._dotenv_loader import load_dotenv
from ._logger_configurator import configure_logger, LoggerConfiguration


app = typer.Typer(
    name=APP_NAME,
    help='A simple tool for managing releases and changelogs of projects.',
    add_completion=False,
)


@app.callback()
def _(
    *,
    _: Annotated[
        bool,
        typer.Option(
            '--version',
            help='Show the version and exit.',
            is_eager=True,
            callback=lambda value: version_callback(package_name=APP_NAME, version_flag=value),
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            '--debug',
            help='Show debug logs in the console.',
            envvar=f'{ENV_VAR_PREFIX}_DEBUG',
        ),
    ] = False,
) -> None:
    logger_configuration = LoggerConfiguration(console_level='DEBUG' if debug else 'INFO')
    configure_logger(logger_configuration)


@app.command()
def execute() -> None:
    run()


def main() -> None:
    """Load settings and run the application."""
    load_dotenv(ENV_VAR_PREFIX)
    app()


if __name__ == '__main__':
    main()  # pragma: no cover
