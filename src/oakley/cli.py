"""Oakley CLI."""

from __future__ import annotations

import sys

import click

from oakley.config import get_settings
from oakley.ingest.manifest import clean_processed, load_latest_manifest, load_manifest
from oakley.ingest.parse import count_pdfs, parse_corpus
from oakley.vector.store import clean_index, collection_count, index_manifest


@click.group()
def main() -> None:
    """Oakley — RAG assistant for HOA and county regulations."""


@main.command()
def status() -> None:
    """Show corpus, manifest, and index state."""
    settings = get_settings()
    pdf_counts = count_pdfs()
    click.echo("Oakley status")
    click.echo(f"  Root: {settings.root}")
    click.echo(f"  Gemini configured: {'yes' if settings.gemini_configured else 'no'}")
    click.echo(f"  Model: {settings.gemini_model}")
    click.echo(
        f"  Corpus: hoa={pdf_counts.get('hoa', 0)} "
        f"(pdf={pdf_counts.get('pdf', 0)}, md={pdf_counts.get('markdown', 0)}), "
        f"county={pdf_counts.get('county', 0)}"
    )

    latest = load_latest_manifest()
    if latest:
        click.echo(f"  Latest manifest: {latest.manifest_id}")
        click.echo(f"    Created: {latest.created_at}")
        click.echo(f"    Chunks: {latest.stats.get('total_chunks', 0)}")
    else:
        click.echo("  Latest manifest: (none — run oakley parse)")

    count = collection_count()
    if count is not None:
        click.echo(f"  Chroma collection: {count} vectors")
    else:
        click.echo("  Chroma collection: (not indexed)")


@main.command()
@click.option("--source", type=click.Choice(["all", "hoa", "bylaws", "county"]), default="all")
@click.option("--force", is_flag=True, help="Re-parse even if files unchanged.")
@click.option("--dry-run", is_flag=True, help="Report new/reused/changed counts per file.")
def parse(source: str, force: bool, dry_run: bool) -> None:
    """Parse corpus files into a chunk manifest."""
    try:
        result = parse_corpus(source=source, force=force, dry_run=dry_run)
        click.echo(result.message)
        if result.dry_run_counts:
            for path, n in result.dry_run_counts.items():
                click.echo(f"  {path}: {n} chunks")
        if result.skipped and not dry_run:
            sys.exit(0)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option("--manifest", "manifest_id", default=None, help="Manifest ID (default: latest).")
@click.option("--no-prune-orphans", is_flag=True, help="Do not delete vectors missing from manifest.")
def index(manifest_id: str | None, no_prune_orphans: bool) -> None:
    """Embed manifest chunks into Chroma."""
    try:
        manifest = load_manifest(manifest_id) if manifest_id else load_latest_manifest()
        if not manifest:
            click.echo("No manifest found. Run oakley parse first.", err=True)
            sys.exit(1)
        stats = index_manifest(manifest, prune_orphans=not no_prune_orphans)
        click.echo(
            f"Indexed {stats['indexed']} chunks "
            f"(skipped {stats.get('skipped', 0)} unchanged, pruned {stats['pruned']} orphans). "
            f"Collection size: {stats['total_in_collection']}"
        )
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option("--source", type=click.Choice(["all", "hoa", "bylaws", "county"]), default="all")
@click.option("--force", is_flag=True, help="Force re-parse before indexing.")
@click.option("--no-prune-orphans", is_flag=True, help="Do not prune orphan vectors on index.")
def ingest(source: str, force: bool, no_prune_orphans: bool) -> None:
    """Parse PDFs and index into Chroma (convenience)."""
    parse_result = parse_corpus(source=source, force=force)
    click.echo(parse_result.message)
    manifest = parse_result.manifest or load_latest_manifest()
    if not manifest:
        click.echo("No manifest available after parse.", err=True)
        sys.exit(1)
    try:
        stats = index_manifest(manifest, prune_orphans=not no_prune_orphans)
        click.echo(
            f"Indexed {stats['indexed']} chunks "
            f"(skipped {stats.get('skipped', 0)} unchanged, pruned {stats['pruned']} orphans). "
            f"Collection size: {stats['total_in_collection']}"
        )
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)


@main.command("ask")
@click.argument("question")
@click.option("--source-type", type=click.Choice(["hoa_bylaw", "county_regulation"]), default=None)
@click.option("--json", "as_json", is_flag=True, help="Output full answer JSON.")
@click.option("--top-k", type=int, default=None)
def ask_cmd(question: str, source_type: str | None, as_json: bool, top_k: int | None) -> None:
    """Ask a question about the regulations corpus."""
    from oakley.rag.answer import ask_question, format_answer_json, format_answer_pretty

    try:
        result = ask_question(question, source_type=source_type, top_k=top_k)
        click.echo(format_answer_json(result) if as_json else format_answer_pretty(result))
        if result.get("refused"):
            sys.exit(1)
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.group()
def clean() -> None:
    """Remove processed data or vector index."""


@clean.command("manifest")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation.")
def clean_manifest(yes: bool) -> None:
    """Delete all processed manifests."""
    if not yes and not click.confirm("Delete all files in data/processed/?"):
        click.echo("Aborted.")
        return
    removed = clean_processed()
    click.echo(f"Removed processed data ({removed} files).")


@clean.command("index")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation.")
def clean_index_cmd(yes: bool) -> None:
    """Delete Chroma vector index."""
    if not yes and not click.confirm("Delete Chroma index in data/chroma/?"):
        click.echo("Aborted.")
        return
    if clean_index():
        click.echo("Removed Chroma index.")
    else:
        click.echo("No Chroma index found.")


@clean.command("all")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation.")
def clean_all(yes: bool) -> None:
    """Delete processed manifests and Chroma index."""
    if not yes and not click.confirm("Delete all processed data AND Chroma index?"):
        click.echo("Aborted.")
        return
    m = clean_processed()
    i = clean_index()
    click.echo(f"Clean complete (manifest files: {m}, index removed: {i}).")


@main.command()
@click.option("--host", default=None, help="Bind host (default from OAKLEY_HOST or 127.0.0.1).")
@click.option("--port", default=None, type=int, help="Bind port (default from OAKLEY_PORT or 8080).")
def serve(host: str | None, port: int | None) -> None:
    """Start the Oakley web chat UI."""
    import uvicorn

    settings = get_settings()
    bind_host = host or settings.host
    bind_port = port or settings.port
    click.echo(f"Oakley chat UI → http://{bind_host}:{bind_port}")
    uvicorn.run("oakley.api.app:app", host=bind_host, port=bind_port, reload=False)


if __name__ == "__main__":
    main()
