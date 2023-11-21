# LTK - Copyrights Reserved 2023 - chrislaffra.com - See LICENSE 

import logging
import ltk
from pyscript import window as js # type: ignore

search = js.URLSearchParams.new(js.location.search)
runtime = search.get("runtime") or "mpy"

logger = logging.getLogger()

def create():
    def feedback(text, color):
        ltk.find("#feedback") \
            .html(text) \
            .css("text-align", "left") \
            .css("color", color)
        logger.info(text)

    def number_chosen(event, option):
        feedback(f"You chose {option.text()}", "green")
        
    @ltk.callback
    def key_down(event):
        feedback(f"keydown: {event.keyCode}, {event.key}", "blue")

    @ltk.callback
    def button_clicked(event):
        feedback("You clicked the button", "red")

    @ltk.callback
    def loveit(event):
        feedback(f"checkbox: {ltk.find('#love').prop('checked')}", "black")

    @ltk.callback
    def change(event):
        element = ltk.jQuery(event.target)
        kind = element.prop("type")
        feedback(f"Changed {kind}: {element.val()}", "purple")

    @ltk.callback
    def set_runtime(event):
        chosen = ltk.jQuery(event.target).attr("value")
        if chosen != runtime:
            js.setSearchParameter("runtime", chosen)

    widgets = [
        ltk.VBox(
            ltk.Text("Choose your favorite runtime:"),
            ltk.RadioGroup(
                ltk.Span(
                    ltk.RadioButton(runtime == "mpy")
                        .attr("name", "runtime")
                        .attr("id", "mpy")
                        .attr("value", "mpy"),
                    ltk.Label("MicroPython").attr("for", "mpy")
                ),
                ltk.Label("PyOdide",
                    ltk.RadioButton(runtime == "py")
                        .attr("name", "runtime")
                        .attr("value", "py")
                ),
            ).on("change", set_runtime)
        ),
        ltk.Button("Click me!", button_clicked, {
            "color": "white",
            "background-color": "red",
            "padding": 6,
        }),
        ltk.Select(["One", "Two", "Three" ], "Two", number_chosen, {
            "padding": 6,
            "color": "white",
            "background-color": "green",
        }),
        ltk.TextArea("This is a text area.\n\nChange me!", {
            "height": 120
        }).on("keydown", key_down),
        ltk.Span(
            ltk.Checkbox(True).attr("id", "love").on("change", loveit),
            ltk.Label("I love LTK")
        ),
        ltk.File().on("change", change),
        ltk.ColorPicker().on("change", change),
        ltk.DatePicker().on("change", change),
        ltk.Input("This is an input. Change me!", {
            "width": 180,
            "padding": 10,
            "background-color": "pink",
        })
        .on("keydown", key_down)
        .on("change", change),
    ]

    def get_widgets():
        for widget in widgets:
            yield widget
            yield ltk.P()

    return (
        ltk.VBox(
            ltk.H1(f"Widgets on {runtime}")
                .css("text-align", "left")
                .css("height", 50)
                .attr("id", "feedback"),
            ltk.Container(get_widgets()), {
                "padding": 50,
                "background-color": "lightyellow",
            }
        )
        .css("height", 710)
        .attr("name", "Inputs")
    )