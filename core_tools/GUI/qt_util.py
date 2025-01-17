import logging
import os
import threading
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

try:
    import IPython.lib.guisupport as gs
    from IPython import get_ipython
except Exception:
    get_ipython = lambda: None


logger = logging.getLogger(__name__)


is_wrapped = threading.local()
is_wrapped.val = False


def qt_log_exception(func):
    ''' Decorator to log exceptions.
    Exceptions are logged and raised again.
    Decorator is designed to be used around functions being called as
    QT event handlers, because QT doesn't report the exceptions.
    Note:
        The decorated method/function cannot be used with
        functools.partial.
    '''

    def wrapped(*args, **kwargs):
        if is_wrapped.val:
            return func(*args, **kwargs)
        else:
            is_wrapped.val = True
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.error('Exception in GUI', exc_info=True)
                raise
            finally:
                is_wrapped.val = False

    return wrapped


_qt_app = None


def qt_init(style: str | None = None) -> bool:
    '''Starts the QT application if not yet started.
    Most of the cases the QT backend is already started
    by IPython, but sometimes it is not.
    '''
    # application reference must be held in global scope
    global _qt_app

    if _qt_app is None:
    #    print(QtCore.QCoreApplication.testAttribute(QtCore.Qt.AA_EnableHighDpiScaling))
    #    print(QtCore.QCoreApplication.testAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough))

        # Set attributes for proper scaling when display scaling is not equal to 100%
        # This should be done before QApplication is started.
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        ipython = get_ipython()

        if ipython:
            if not gs.is_event_loop_running_qt4():
                if any('SPYDER' in name for name in os.environ):
                    logger.error("Qt5 not configured in Spyder")
                    raise Exception('Configure Qt5 in Spyder -> Preferences -> IPython Console -> Graphics -> Backend')
                else:
                    logger.warning("Qt5 not configured for IPython console. Activating it now")
                    print('Warning Qt5 not configured for IPython console. Activating it now.')
                    ipython.run_line_magic('gui', 'qt5')

            _qt_app = QtCore.QCoreApplication.instance()
            if _qt_app is None:
                logger.info('Create Qt application event processor')
                _qt_app = QtWidgets.QApplication([])
            else:
                logger.debug('Qt application already created')
        else:
            _qt_app = QtCore.QCoreApplication.instance()
            logger.debug(f"No IPython. QtApplication running = {_qt_app is not None}")

    if style == "dark":
        qt_set_darkstyle()

    return _qt_app is not None


def qt_set_darkstyle():
    import qdarkstyle
    import pyqtgraph as pg

    qt_app = QtCore.QCoreApplication.instance()
    if qt_app is None:
        return
    dark_stylesheet = qdarkstyle.load_stylesheet()
    # patch qdarkstyle for cropped x-label on 2D graphics.
    dark_stylesheet +=r'''
QGraphicsView {
    padding: 0px;
}
'''
    qt_app.setStyleSheet(dark_stylesheet)
    pg.setConfigOption('background', 'k')
    pg.setConfigOption('foreground', 'gray')


_qt_message_handler_installed = False


def _qt_message_handler(level, context, message):
    if message.startswith('QSocketNotifier: Multiple socket notifiers for same socket'):
        # ignore ipython warning
        return
    if level == QtCore.QtInfoMsg:
        log_level = logging.INFO
    elif level == QtCore.QtWarningMsg:
        log_level = logging.WARNING
    elif level == QtCore.QtCriticalMsg:
        log_level = logging.CRITICAL
    elif level == QtCore.QtFatalMsg:
        log_level = logging.FATAL
    else:
        log_level = logging.DEBUG
    logger.log(log_level, message)


def install_qt_message_handler():
    global _qt_message_handler_installed

    if not _qt_message_handler_installed:
        QtCore.qInstallMessageHandler(_qt_message_handler)
        _qt_message_handler_installed = True


def qt_show_exception(message: str, ex: Exception, extra_line: str = None):
    # logger.error(message, exc_info=ex)
    text = message
    if extra_line:
        text += "\n" + extra_line
    text += f"\n{type(ex).__name__}: {ex}"
    msg = QMessageBox(
        QMessageBox.Critical,
        message,
        text,
        QMessageBox.Ok,
        )
    msg.setDetailedText("\n".join(traceback.format_exception(ex)))
    msg.setStyleSheet("QTextEdit{min-width:600px}")
    msg.exec_()


def qt_show_error(title: str, message: str):
    # logger.error(message)
    msg = QMessageBox(
        QMessageBox.Critical,
        title,
        message,
        QMessageBox.Ok,
        )
    msg.exec_()

def qt_create_app() -> QtCore.QCoreApplication:
    logger.info("Create Qt application")
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication([])
    return app


def qt_run_app(app):
    logger.info("Run Qt Application")
    app.exec()
    logger.info("Qt Application event loop exited")
