import os
import pathlib

import pdoc
import pdoc.doc
from pdoc import render, render_helpers, web

from schemaspec.__version__ import __version__


def serve_docs(*modules: str, host: str = "localhost"):
    httpd = web.DocServer((host, 8080), [*modules])
    with httpd:
        url = f"http://{host}:{httpd.server_port}"
        web.open_browser(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()


def _get_doc_output(project_root: pathlib.Path) -> pathlib.Path:
    version = __version__
    root = project_root.joinpath(f"docs/api/{version}").resolve()
    if root.exists():
        raise ValueError(f"Directory already exists '{root}'")
    return root


def _configure(project_path: pathlib.Path):
    render_helpers.markdown_extensions["admonitions"] = None
    render.configure(
        docformat="restructuredtext",
        template_directory=project_path.joinpath("templates").resolve(),
    )


def make_docs():
    project_path = pathlib.Path(os.environ["PDM_PROJECT_ROOT"])
    _configure(project_path)
    doc_output = _get_doc_output(project_root=project_path)
    # # doc = pdoc.doc.Module.from_name("schemaspec.adapters")
    modules = "schemaspec"
    pdoc.pdoc(modules, output_directory=doc_output)
    serve_docs(modules)


if __name__ == "__main__":
    make_docs()
