from PySide6.QtCore import (
    Qt,
    QUrl,
)
from PySide6.QtGui import (
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QSplitter,
    QLabel,
    QComboBox,
    QToolButton,
    QLineEdit,
    QListView,
    QFrame,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.tooltips import ToolTips


class CustomFileDialog(QFileDialog):

    def __init__(self, parent: QWidget | None = None, f: Qt.WindowType | None = None):
        """
        Initialize a custom file dialog with simplified UI and modified behavior.

        Creates a file dialog that doesn't use the native dialog and customizes various
        elements to better suit the application's needs. Removes standard buttons,
        rearranges the layout, and adds tooltips to help users navigate the dialog.

        Parameters
        ----------
        parent : QWidget or None, optional
            The parent widget. Default is None.
        f : Qt.WindowType or None, optional
            Window flags for the dialog. Default is None.

        Methods
        -------
        set_sidebar_directories(dirs)
            Set the directories to initially appear in the sidebar.
        accept()
            Overrides superclass' `accept()` to handle acceptances without closing the dialog.
        reject()
            Overrides superclass' `reject()` to handle rejections without closing the dialog.
        """
        super(CustomFileDialog, self).__init__(parent, f)
        self.setOptions(QFileDialog.DontUseNativeDialog)

        # remove accept and reject buttons
        button_box = self.findChild(QDialogButtonBox)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        open_button = button_box.button(QDialogButtonBox.Open)
        button_box.removeButton(cancel_button)
        button_box.removeButton(open_button)

        # repurpose look_in_label
        look_in_label = self.findChild(QLabel, "lookInLabel")
        look_in_label.setText("Favorites:")
        look_in_label.setToolTip(ToolTips.FileDialog.favorite_directories_window())

        # make splitter vertical to conserve space
        splitter = self.findChild(QSplitter)
        splitter.setOrientation(Qt.Vertical)
        splitter.findChild(QListView).setToolTip(
            ToolTips.FileDialog.favorite_directories_window()
        )

        # label directory contents section
        lower_splitter_frame = splitter.findChild(QFrame)
        directory_browser_vbox = lower_splitter_frame.findChild(QVBoxLayout)
        current_directory_label = QLabel("Current Directory")
        current_directory_label.setObjectName("current_directory_label")
        directory_browser_vbox.insertWidget(0, QLabel("Current Directory Contents:"))
        lower_splitter_frame.setToolTip(ToolTips.FileDialog.directory_contents_window())

        # get rid of fileName label
        file_name_label = self.findChild(QLabel, "fileNameLabel")
        file_name_label.hide()

        # get rid of directory selector
        directory_drop_down = self.findChild(QComboBox)
        directory_drop_down.hide()

        # get rid of tool buttons
        tool_buttons = self.findChildren(QToolButton)
        for button in tool_buttons:
            button.hide()

        # get rid of file selector
        file_name_line = self.findChild(QLineEdit)
        file_name_line.hide()

        # add tooltips to filetype filter
        self.findChild(QComboBox, "fileTypeCombo").setToolTip(
            ToolTips.FileDialog.file_type_filter()
        )
        self.findChild(QLabel, "fileTypeLabel").setToolTip(
            ToolTips.FileDialog.file_type_filter()
        )

    def set_sidebar_directories(self, dirs: list[str]) -> None:
        """
        Set the sidebar directories of the file dialog.

        Converts a list of directory paths to QUrl objects and sets them as the
        sidebar URLs in the file dialog.

        Parameters
        ----------
        dirs : list[str]
            List of directory paths to display in the sidebar.
        """
        urls = []
        for x in dirs:
            urls.append(QUrl.fromLocalFile(x))
        self.setSidebarUrls(urls)

    def accept(self) -> None:
        """
        Handle the accept action for the dialog.

        Emits the accepted signal when the dialog is accepted, but does not close
        the dialog as the standard implementation would.
        """
        self.accepted.emit()

    def reject(self) -> None:
        """
        Handle the reject action for the dialog.

        Emits the rejected signal when the dialog is rejected, but does not close
        the dialog as the standard implementation would.
        """
        self.rejected.emit()


class CustomMessageBox(QMessageBox):
    """
    Creates a message box with a fixed size.

    Methods
    -------
    resizeEvent(event)
        Overrides superclass' `resizeEvent` to enforce a a fixed size for the message box.
    """

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle resize events for the message box.

        Overrides the default resize behavior to enforce a fixed size for the
        message box, ensuring a consistent and compact appearance.

        Parameters
        ----------
        event : QResizeEvent
            The resize event.
        """
        QMessageBox.resizeEvent(self, event)
        self.setFixedHeight(5)
        self.setFixedWidth(250)
