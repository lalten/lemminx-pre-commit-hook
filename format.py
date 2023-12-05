import contextlib
import json
import os
import typing
import pylspclient
import subprocess
import threading
import pathlib
import click


class ReadPipe(threading.Thread):
    def __init__(self, pipe) -> None:
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self) -> None:
        line = self.pipe.readline().decode("utf-8")
        while line:
            print(line)
            line = self.pipe.readline().decode("utf-8")


class Registration(object):
    def __init__(self, id: str, method: str) -> None:
        self.id = id
        self.method = method


class RegistrationParams(object):
    def __init__(self, registrations: list[Registration]) -> None:
        self.registrations = registrations


def make_server() -> subprocess.Popen:
    cmd = [os.getenv("LEMMINX_BIN", "/usr/local/bin/lemminx")]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def make_lsp_client(proc: subprocess.Popen) -> pylspclient.LspClient:
    read_pipe = ReadPipe(proc.stderr)
    read_pipe.start()
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(proc.stdin, proc.stdout)

    lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)
    lsp_endpoint.method_callbacks["client/registerCapability"] = lambda _: None
    lsp_endpoint.notify_callbacks["textDocument/publishDiagnostics"] = print

    return pylspclient.LspClient(lsp_endpoint)


def apply_textedits(text: str, textedits: list[dict[str, typing.Any]]) -> str:
    """textedits is a dict of the form list[pylspclient.lsp_structs.TextEdit].

    [
        {
            'range': {
                'start': {
                    'line': 0,
                    'character': 68
                },
                'end': {
                    'line': 0,
                    'character': 69
                }
            },
            'newText': '\n '
        },
        ...
        {
            'range': {
                'start': {
                    'line': 35,
                    'character': 0
                },
                'end': {
                    'line': 38,
                    'character': 0
                }
            },
            'newText': ''
        }
    ]
    """
    linestarts = [0]
    for line in text.splitlines():
        linestarts.append(linestarts[-1] + len(line) + 1)

    for textedit in reversed(textedits):
        start = textedit["range"]["start"]
        end = textedit["range"]["end"]
        startpos = linestarts[start["line"]] + start["character"]
        endpos = linestarts[end["line"]] + end["character"]
        text = text[:startpos] + textedit["newText"] + text[endpos:]

    return text


@contextlib.contextmanager
def lsp_client(initialization_options: dict[str, typing.Any]) -> typing.Iterator[pylspclient.LspClient]:
    proc = make_server()
    try:
        lsp_client = make_lsp_client(proc)
        lsp_client.initialize(
            processId=proc.pid,
            rootPath=None,
            rootUri="file:///",
            initializationOptions=initialization_options,
            capabilities={},
            trace="off",
            workspaceFolders=None,
        )
        lsp_client.initialized()
        yield lsp_client
    finally:
        proc.kill()


def format(
    client: pylspclient.LspClient,
    path: pathlib.Path,
    format_settings: dict[str, typing.Any],
) -> bool:
    """Ask lemminx to format a file. Returns True if the file had changes."""
    text = path.read_text()
    if not text:
        # skip empty files
        return False

    td_item = pylspclient.lsp_structs.TextDocumentItem(
        uri=f"file://{path}", languageId=pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.XML, version=1, text=text
    )
    client.didOpen(td_item)

    td_id = pylspclient.lsp_structs.TextDocumentIdentifier(td_item.uri)
    textedits = client.lsp_endpoint.call_method("textDocument/formatting", textDocument=td_id, options=format_settings)

    if textedits:
        text = apply_textedits(text, textedits)
        path.write_text(text)

    return bool(textedits)


@click.command()
@click.option("--settings", type=click.Path(path_type=pathlib.Path, exists=True))
@click.argument("filenames", nargs=-1, type=click.Path(path_type=pathlib.Path, exists=True))
def cli(settings: typing.Optional[pathlib.Path], filenames: tuple[pathlib.Path, ...]) -> None:
    initialization_options = json.loads(settings.read_text()) if settings else {}
    try:
        format_options = initialization_options["settings"]["xml"]["format"]
    except KeyError:
        format_options = {}

    with lsp_client(initialization_options) as client:
        did_edit = False
        for file in filenames:
            did_edit |= format(client, file, format_options)
    if did_edit:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
