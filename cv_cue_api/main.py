"""
CV-CUE API Wrapper CLI

Command-line interface for the CV-CUE API wrapper.
"""

import sys
import json
import click
from .config import logger
from .cv_cue_client import CVCueClient
from .resources.filters import FilterBuilder


# Context object to pass client between commands
class CLIContext:
    """Context object for CLI commands."""

    def __init__(self):
        self.client = None
        self.verbose = False


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@pass_context
def cli(ctx, verbose):
    """CV-CUE API Wrapper - Command-line interface for CV-CUE API."""
    ctx.verbose = verbose
    if verbose:
        logger.info("Verbose mode enabled")


@cli.group()
def session():
    """Session management commands."""
    pass


@session.command()
@pass_context
def login(ctx):
    """Login and create a new session."""
    try:
        with CVCueClient() as client:
            if ctx.verbose:
                click.echo("Attempting to login...")

            response = client.login()
            click.echo(click.style("✓ Login successful", fg="green"))

            if ctx.verbose:
                click.echo(json.dumps(response, indent=2))
    except Exception as e:
        click.echo(click.style(f"✗ Login failed: {e}", fg="red"), err=True)
        sys.exit(1)


@session.command()
@pass_context
def status(ctx):
    """Check session status."""
    try:
        with CVCueClient() as client:
            if client.is_session_active():
                click.echo(click.style("✓ Session is active", fg="green"))
            else:
                click.echo(click.style("✗ Session is not active", fg="yellow"))
                click.echo("Run 'cv-cue-api session login' to create a new session")
    except Exception as e:
        click.echo(click.style(f"✗ Error checking session: {e}", fg="red"), err=True)
        sys.exit(1)


@session.command()
@pass_context
def clear(ctx):
    """Clear cached session."""
    try:
        with CVCueClient() as client:
            client.clear_session()
            click.echo(click.style("✓ Session cache cleared", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error clearing session: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.group(name='managed-devices')
def managed_devices():
    """Managed devices (Access Points) commands."""
    pass


@managed_devices.command(name='list-aps')
@click.option('--pagesize', default=10, help='Number of results per page')
@click.option('--startindex', default=0, help='Start index for pagination')
@click.option('--total-count', is_flag=True, help='Include total count in response')
@click.option('--sortby', default='boxid', help='Field to sort by')
@click.option('--ascending/--descending', default=True, help='Sort order')
@click.option('--active', type=bool, help='Filter by active status')
@click.option('--model', multiple=True, help='Filter by model (can specify multiple)')
@click.option('--name', multiple=True, help='Filter by name (can specify multiple)')
@click.option('--filter', 'filters', multiple=True, help='Advanced filter: property:operator:value (e.g., name:contains:Arista)')
@click.option('--filter-operator', type=click.Choice(['AND', 'OR']), default='AND', help='Logical operator for filters')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'compact']), default='json', help='Output format')
@pass_context
def list_aps(ctx, pagesize, startindex, total_count, sortby, ascending, active, model, name, filters, filter_operator, output):
    """List managed devices (Access Points)."""
    try:
        with CVCueClient() as client:
            # Ensure session is active
            if not client.is_session_active():
                if ctx.verbose:
                    click.echo("Session not active, logging in...")
                client.login()

            # Build advanced filters if provided
            fb = None
            if filters:
                fb = FilterBuilder(filter_operator)
                for filter_str in filters:
                    try:
                        property_name, operator, value = filter_str.split(':', 2)
                        fb.add(property_name, operator, value)
                    except ValueError:
                        click.echo(f"Invalid filter format: {filter_str}", err=True)
                        click.echo("Expected format: property:operator:value", err=True)
                        sys.exit(1)

            # Build kwargs for simple filters
            kwargs = {}
            if active is not None:
                kwargs['active'] = active
            if model:
                kwargs['model'] = list(model)
            if name:
                kwargs['name'] = list(name)

            # Make API call
            response = client.managed_devices.list_aps(
                pagesize=pagesize,
                startindex=startindex,
                totalcountrequired=total_count,
                sortby=sortby,
                ascending=ascending,
                filters=fb,
                **kwargs
            )

            # Output results
            if output == 'json':
                click.echo(json.dumps(response, indent=2))
            elif output == 'table':
                devices = response.get('managedDevices', [])
                if devices:
                    click.echo(f"\nFound {len(devices)} devices:")
                    click.echo("-" * 80)
                    click.echo(f"{'Name':<30} {'Model':<15} {'MAC Address':<20} {'Active'}")
                    click.echo("-" * 80)
                    for device in devices:
                        name = device.get('name', 'N/A')[:29]
                        model = device.get('model', 'N/A')[:14]
                        mac = device.get('macaddress', 'N/A')
                        active = '✓' if device.get('active') else '✗'
                        click.echo(f"{name:<30} {model:<15} {mac:<20} {active}")
                    if total_count:
                        click.echo("-" * 80)
                        click.echo(f"Total: {response.get('totalCount', 'N/A')}")
                else:
                    click.echo("No devices found")
            elif output == 'compact':
                devices = response.get('managedDevices', [])
                for device in devices:
                    click.echo(f"{device.get('name', 'N/A')} - {device.get('macaddress', 'N/A')}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@managed_devices.command(name='get-all-aps')
@click.option('--pagesize', default=100, help='Number of results per page')
@click.option('--active', type=bool, help='Filter by active status')
@click.option('--model', multiple=True, help='Filter by model (can specify multiple)')
@click.option('--filter', 'filters', multiple=True, help='Advanced filter: property:operator:value')
@click.option('--filter-operator', type=click.Choice(['AND', 'OR']), default='AND', help='Logical operator for filters')
@click.option('--output', '-o', type=click.Choice(['json', 'count']), default='json', help='Output format')
@pass_context
def get_all_aps(ctx, pagesize, active, model, filters, filter_operator, output):
    """Get all managed devices across all pages."""
    try:
        with CVCueClient() as client:
            # Ensure session is active
            if not client.is_session_active():
                if ctx.verbose:
                    click.echo("Session not active, logging in...")
                client.login()

            # Build filters
            fb = None
            if filters:
                fb = FilterBuilder(filter_operator)
                for filter_str in filters:
                    try:
                        property_name, operator, value = filter_str.split(':', 2)
                        fb.add(property_name, operator, value)
                    except ValueError:
                        click.echo(f"Invalid filter format: {filter_str}", err=True)
                        sys.exit(1)

            # Build kwargs
            kwargs = {}
            if active is not None:
                kwargs['active'] = active
            if model:
                kwargs['model'] = list(model)

            if ctx.verbose:
                click.echo("Fetching all devices (this may take a while)...")

            # Make API call
            devices = client.managed_devices.get_all_aps(
                pagesize=pagesize,
                filters=fb,
                **kwargs
            )

            # Output results
            if output == 'json':
                click.echo(json.dumps(devices, indent=2))
            elif output == 'count':
                click.echo(f"Total devices: {len(devices)}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(click.style(f"✗ Unexpected error: {e}", fg="red"), err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
