import logging
import sys
import time

import click

from paperless_ai_tagger import __version__
from paperless_ai_tagger.classifier import Classifier
from paperless_ai_tagger.client import PaperlessClient
from paperless_ai_tagger.config import Settings
from paperless_ai_tagger.processor import process_documents


def _setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option(version=__version__)
def main():
    """Automatically classify Paperless-ngx documents using the Claude CLI."""


@main.command()
@click.option("--document-id", type=int, default=None, help="Process a single document by ID")
@click.option("--limit", type=int, default=0, help="Max number of documents to process")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying")
@click.option("--watch", is_flag=True, default=False, help="Continuously poll for new documents")
def process(document_id, limit, dry_run, watch):
    """Process untagged documents."""
    settings = Settings()
    if dry_run:
        settings.dry_run = True

    _setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    client = PaperlessClient(settings.paperless_url, settings.paperless_api_token)
    classifier = Classifier(model=settings.claude_model)

    try:
        if watch:
            logger.info("Watching for new documents every %d seconds", settings.poll_interval)
            while True:
                process_documents(
                    client, classifier, settings, document_id=document_id, limit=limit
                )
                time.sleep(settings.poll_interval)
        else:
            stats = process_documents(
                client, classifier, settings, document_id=document_id, limit=limit
            )
            if stats.failed > 0:
                sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        client.close()


@main.command("list-tags")
def list_tags():
    """List all tags in Paperless-ngx."""
    settings = Settings()
    _setup_logging(settings.log_level)
    client = PaperlessClient(settings.paperless_url, settings.paperless_api_token)
    try:
        client.load_taxonomy()
        for name, tag in sorted(client.tags.items()):
            click.echo(f"{tag.id:>5}  {tag.name}")
    finally:
        client.close()


@main.command("list-correspondents")
def list_correspondents():
    """List all correspondents in Paperless-ngx."""
    settings = Settings()
    _setup_logging(settings.log_level)
    client = PaperlessClient(settings.paperless_url, settings.paperless_api_token)
    try:
        client.load_taxonomy()
        for name, corr in sorted(client.correspondents.items()):
            click.echo(f"{corr.id:>5}  {corr.name}")
    finally:
        client.close()


@main.command("list-types")
def list_types():
    """List all document types in Paperless-ngx."""
    settings = Settings()
    _setup_logging(settings.log_level)
    client = PaperlessClient(settings.paperless_url, settings.paperless_api_token)
    try:
        client.load_taxonomy()
        for name, dt in sorted(client.document_types.items()):
            click.echo(f"{dt.id:>5}  {dt.name}")
    finally:
        client.close()
