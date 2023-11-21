import ltk  # Load early on MicroPython, before logging

import examples
from pyscript import window as js # type: ignore
import logging

logger = logging.getLogger("kitchensink")


def cleanup(src):
    return "\n".join([
        line
        for line in src.split("\n")
        if not "# example" in line
    ])


def getsource(file):
    def setsource(src):
        src = "\n".join(src.split("\n")[2:])
        ltk.find(f'code[file="{file}"]').empty().text(src)

    ltk.get(file, setsource, "html")
    return f"Loading {file}..."


ltk.find("#progress").remove()
ltk.find("#title").append(f" took {js.startTime() / 1000}s to load")


tabs = ltk.Tabs(
    ltk.HBox(
        ltk.Container(
            example
        )
        .addClass("example")
        .css("width", "40%")
        .resizable(ltk.to_js({ "handles": "e" })),
        ltk.VBox(
            ltk.Preformatted(
                ltk.Code("python", getsource(file))
                    .attr("file", file)
                    .css("width", "95%")
            )
            .css("padding-bottom", 16)
            .css("height", 770)
        )
        .css("overflow", "hidden")
        .css("width", "60%")
        .css("padding-left", 24)
        .css("border-left", "2px solid lightgray"),
    ).attr("name", example.attr("name"))
    for file, example in examples.items
)


@ltk.callback
def activate_tab(event, ui=None):
    index = tabs.active()
    ltk.set_url_parameter("tab", index, False)
    logger.info("Switched to tab %s", index)

tabs.activate(ltk.get_url_parameter("tab") or 0)

ltk.body.append(
    ltk.Logger().element,
    ltk.Div(
        tabs.css("margin-bottom", 24)
            .attr("id", "examples")
            .on("tabsactivate", activate_tab),
        ltk.Link(
            "https://github.com/laffra/ltk",
            ltk.HBox(
                ltk.Image("https://github.com/favicon.ico").width(20),
                ltk.Text("See the LTK project at Github")
            )
        ).attr("target", "_blank")
    )
    .css("width", 1300)
    .css("margin", "auto")
)

logger.info("Kitchensink Ready")