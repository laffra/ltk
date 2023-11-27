# LTK - Copyright 2023 - All Rights Reserved - chrislaffra.com - See LICENSE 

import json
import logging
import ltk
from pyscript import window

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)


class Logger(ltk.Div):
    classes = [ "ltk-log-list" ]
    level = logging.INFO
    messages = []
    icons = { 
        logging.CRITICAL : '💥',
        logging.ERROR    : '🔥️',
        logging.WARNING  : '🤔',
        logging.INFO     : 'ⓘ',
        logging.DEBUG    : '🐞',
    }
    levels = dict((value, key) for key, value in icons.items())
    last_width = 0

    def __init__(self):
        self.log_ui = ltk.VBox(ltk.Div().height(28)).attr("id", "ltk-log-ui")
        self.sequence_ui = _SequenceDiagram()
        ltk.Div.__init__(self,
            ltk.VerticalSplitPane(
                self.sequence_ui,
                self.log_ui,
            )
        )
        self.element.resizable(ltk.to_js({ "handles": "n" }))
        self.on("resize", lambda event, ui: self.resize())
        self.height(getattr(ltk.local_storage, "log-list-height", None) or 300)
        self._add_table()
        self._setup_logger()
        self._setup_console()
        self._setup_py_error()
        self._filter_rows()
        
    def resize(self):
        setattr(ltk.local_storage, "log-list-height", self.css("height"))

    def _add_table(self):
        self.selector = ltk.find('#ltk-log-level')
        self.opacity(0)
        ltk.VBox(
            ltk.HBox(
                ltk.Text().text("When"),
                ltk.Text().text("Level"),
                ltk.Text().text("Message"),
            ).width("100vw"),
            ltk.Container(
                ltk.Select(
                    [ name for name, level in sorted(self.levels.items(), key = lambda item: item[1]) ],
                    self.icons[self.level],
                    lambda _, option: self._set_level(option.text()),
                ).attr("id", "ltk-log-level"),
                ltk.Input("")
                    .attr("placeholder", "Filter")
                    .attr("id", "ltk-log-filter")
                    .on("keyup", lambda event: self._apply_filter()),
                ltk.Button("clear", lambda event: self._clear()),
                ltk.Button("x", lambda event: self.element.remove()),
            ).addClass("ltk-log-buttons")
        ).addClass("ltk-log-header").appendTo(self.log_ui)
        ltk.observe(self.element, self._changed)
        self.last_width = self.element.width()

    def _changed(self, element=None):
        if self.element.width() != self.last_width:
            ltk.find(".ltk-log-header").width(self.width())
            ltk.find(".ltk-log-buttons").css("right", 10)
            self.last_width = self.element.width()

    def _set_level(self, selected):
        self.level = self.levels[selected]
        self._filter_rows()

    def _apply_filter(self):
        self._filter_rows()
        self.sequence_ui.filter_messages()

    def _filter_rows(self):
        filter_text = ltk.find("#ltk-log-filter").val()
        height = 26
        rows = ltk.find_list(".ltk-log-row")
        for row in rows:
            message = row.find(".ltk-text:nth-child(3)").text()
            visible = int(row.attr("level")) >= self.level and (not filter_text or filter_text in message)
            row.css("display", "block" if visible else "none")
            if visible:
                height += 25

    def _clear(self):
        ltk.find(".ltk-log-row").animate(
            ltk.to_js({ "opacity": 0}),
            lambda: ltk.find(".ltk-log-row").remove()
        )
        self._filter_rows()
        self.sequence_ui.clear()

    def _setup_logger(self):
        logger_widget = self

        class Handler(logging.StreamHandler):
            level = Logger.level
            formatter = logging.Formatter(fmt=' %(name)s :: %(levelname)-8s :: %(message)s')

            def emit(self, record):
                message = getattr(record, "msg", getattr(record, "message", "???"))
                logger_widget._add(record.levelno, message)

        logger.addHandler(Handler())

    def _add(self, level, *args, **argv):
        try:
            message = " ".join(map(str, args))
            if message.startswith("js_callable_proxy"):
                return
            self.messages.append(message)
            ltk.find(".ltk-log-header").after(
                ltk.HBox(
                    ltk.Text().text(f"{ltk.get_time():.2f}"),
                    ltk.Text().text(Logger.icons[level]),
                    ltk.Text().text(message.replace("\n", "\\n")),
                )
                .addClass("ltk-log-row")
                .attr("level", level)
                .animate(ltk.to_js({ "height": 24  }), 700)
            )
            if level == logging.ERROR:
                window.console.orig_error(*args)
            else:
                window.console.orig_log(*args)
            self._filter_rows()
            self.element.animate(ltk.to_js({"opacity": 1}), 1300)
            self._check_pubsub(message)
            self._check_network(message)
            self._check_events(message)
        except Exception as e:
            print("Log error:", e)
                
    def _check_pubsub(self, message):
        if message.startswith("[Pubsub]"):
            self.sequence_ui.log(*json.loads(message[9:]))

    def _check_network(self, message):
        if message.startswith("[Network]"):
            kind, type, encodedSize, decodedSize, duration, name = json.loads(message[10:])
            post = "POST:" if "?_=p&" in name else ""
            sender = "Application" if post else "Network"
            receiver = "Network" if post else "Application"
            io = "POST" if post else "GET"
            if type == "Xmlhttprequest":
                self.sequence_ui.log(io, sender, receiver, name, f"{decodedSize}")

    def _check_events(self, message):
        print(message)

    def _setup_console(self):
        window.console.orig_log = window.console.log
        window.console.orig_warn = window.console.warn
        window.console.orig_error = window.console.error
        window.console.log = self._console_log
        window.console.warn = self._console_log
        window.console.error = self._console_log
        try:
            import warnings
            warnings.warn = self._console_log
        except:
            pass # Micropython

    def _setup_py_error(self):
        def find_errors():
            py_error = ltk.find(".py-error")
            if py_error.length > 0:
                lines = py_error.text().strip().split("\n")
                self._add(logging.ERROR, f"{lines[-1]}: {py_error.text()}")
                py_error.remove()
        ltk.repeat(find_errors, 1)

    def _console_log(self, *args, **argv):
        try:
            if not args:
                return

            def format(arg):
                if arg.__class__.__name__ == "jsobj":
                    try:
                        return json.dumps(to_py(arg))
                    except:
                        pass
                return str(arg)

            message = " ".join(filter(None, [format(arg) for arg in args]))
            level = self._get_level(message)
            self._add(level, message)
        except Exception as e:
            print(e)

    def _get_level(self, message):
        level = logging.INFO
        if "Traceback" in message or "Error" in message:
            level = logging.ERROR
        if "Debug" in message or "js_callable_proxy" in message or message.startswith("💀🔒 - Possible deadlock"):
            level = logging.DEBUG
        return level


class _Component(ltk.VBox):
    classes = [ "ltk-sequence-component ltk-vbox" ]

    def __init__(self, name):
        self.title = ltk.Text(name).addClass("ltk-sequence-component-title")
        self.line = ltk.Div().addClass("ltk-sequence-component-line")
        ltk.VBox.__init__(self, self.title, self.line)

class _Call(ltk.Div):
    classes = [ "ltk-sequence-call" ]

    def __init__(self, sender, receiver, topic, data, index):
        self.when = ltk.Span(f"{ltk.get_time():.2f}s").addClass("ltk-sequence-when")
        self.label = ltk.Span(f"{topic[:18]}: {data}").addClass("ltk-sequence-label")
        ltk.Div.__init__(self, self.label, self.when)
        self.sender = sender
        self.receiver = receiver
        self.topic = topic
        self.data = data
        self.dot = _Dot(
            sender, receiver, topic, data, self,
            sender.title.position().left > receiver.title.position().left
        )
        self.element.append(self.dot.element)
        self.set_index(index)
    
    def set_index(self, index):
        self.index = index
        self.display("block")
        ltk.schedule(self.set_position)
    
    def set_position(self):
        left = min(self.sender.title.position().left, self.receiver.title.position().left)
        right = max(self.sender.title.position().left, self.receiver.title.position().left)
        top = self.sender.title.position().top
        width = self.sender.title.width()
        height = self.sender.title.height()
        
        self.width(right - left)
        self.left(round(left + width / 2 + 8))
        self.top(round(top + height * 2 + 26 + self.index * 32))
        self.label.css("opacity", 0).width(self.width())
        self.label.animate(ltk.to_js({ "opacity": 1 }), 1500)
        self.dot.set_position()


class _Dot(ltk.Div):
    classes = [ "ltk-sequence-dot" ]
    animated = False

    def __init__(self, sender, receiver, topic, data, line, reverse):
        ltk.Div.__init__(self)
        self.attr("title", f"{sender.text()} => {receiver.text()} - {topic}: {data}")
        self.reverse = reverse
        if reverse:
            self.left("").css("right", 0)
        self.addClass("ltk-arrow ltk-arrow-left" if reverse else "ltk-arrow ltk-arrow-right")
        self.line = line
    
    def get_start(self):
        return self.line.width() - 5 if self.reverse else -5

    def get_stop(self):
        return -5 if self.reverse else self.line.width() - 5

    def set_position(self):
        self.left(self.get_start())
        if self.animated:
            self.left(self.get_stop())
        else:
            self.animated = True
            self.animate(ltk.to_js({ "left": self.get_stop() }), 1000)


class _SequenceDiagram(ltk.HBox):
    classes = [ "ltk-sequence-ui", "ltk-hbox" ]
    components = {}
    calls = []
    last_width = 0

    def __init__(self):
        ltk.HBox.__init__(self,
            ltk.Div(
                ltk.Text("State Sequence Diagram").css("margin", 3)
            ).addClass("ltk-sequence-header"),
        )
        self.element.attr("id", "ltk-sequence-ui")
        ltk.observe(self.element, self.changed)
        self.last_width = self.element.width()
        self.on("resize", lambda event, ui: self.resize())
        self.set_width()
        
    def set_width(self):
        self.width(getattr(ltk.local_storage, "log-sequence-width", None) or 300)

    def resize(self):
        setattr(ltk.local_storage, "log-sequence-width", self.css("width"))

    def changed(self, element=None, force=False):
        if force or self.element.width() != self.last_width:
            ltk.find(".ltk-sequence-header").width(self.width())
            self.closest("td").width(self.width())
            self.last_width = self.element.width()
            for call in self.calls:
                call.set_position()

    def log(self, type, sender_name, receiver_name, topic, data):
        self.element.width("100%")
        sender = self.get_component(sender_name)
        receiver = self.get_component(receiver_name)
        call = _Call(sender, receiver, f"{type}:{topic}", data, len(self.calls))
        self.calls.append(call)
        self.append(call.element)
        self.filter_messages()
        self.set_width()
        ltk.schedule(lambda: self.changed(force=True), 1.5)

    def clear(self):
        ltk.find(".ltk-sequence-call").animate(
            ltk.to_js({ "opacity": 0}),
            lambda: ltk.find(".ltk-sequence-call").remove()
        )
        self.calls = []

    def filter_messages(self):
        filter = ltk.find("#ltk-log-filter").val()
        ltk.find(".ltk-sequence-call").css("display", "none")
        index = len(self.calls) - 1
        for n, call in enumerate(self.calls):
            if filter in call.text():
                call.set_index(index)
                index -= 1

    def get_component(self, name):
        if not name in self.components:
            component = _Component(name)
            self.components[name] = component
            component.appendTo(self.element)
        return self.components[name]

