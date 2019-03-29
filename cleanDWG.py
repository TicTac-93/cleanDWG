# -----------------------
#   Clean DWG Dev Build
# -----------------------

# Destroys instances of the dialog before recreating it
# This has to go first, before modules are reloaded or the ui var is re-declared.
try:
    ui.close()
except:
    pass

# --------------------
#       Modules
# --------------------

# PySide 2
from PySide2.QtUiTools import QUiLoader
import PySide2.QtWidgets as QtW
from PySide2.QtCore import QFile

# Import PyMXS, MaxPlus, and set up shorthand vars
import pymxs
import MaxPlus

maxscript = MaxPlus.Core.EvalMAXScript

# Misc
import os


# --------------------
#      UI Class
# --------------------


class cleanDWGUI(QtW.QDialog):

    def __init__(self, ui_file, pymxs, parent=MaxPlus.GetQMaxMainWindow()):
        """
        The Initialization of the main UI class
        :param ui_file: The path to the .UI file from QDesigner
        :param pymxs: The pymxs library
        :param parent: The main Max Window
        """
        # Init QtW.QDialog
        super(cleanDWGUI, self).__init__(parent)

        # ---------------------------------------------------
        #                    Variables
        # ---------------------------------------------------

        self._ui_file_string = ui_file
        self._pymxs = pymxs
        self._parent = parent
        self._rt = pymxs.runtime

        # ---------------------------------------------------
        #                     Main Init
        # ---------------------------------------------------

        # UI Loader

        ui_file = QFile(self._ui_file_string)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self._widget = loader.load(ui_file)

        ui_file.close()

        # Attaches loaded UI to the dialog box

        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self._widget)

        self.setLayout(main_layout)

        # Titling

        self._window_title = 'Clean DWG - DEV BUILD'
        self.setWindowTitle(self._window_title)

        # ---------------------------------------------------
        #                   Widget Setup
        # ---------------------------------------------------

        self._btn_clean = self.findChild(QtW.QPushButton, 'btn_clean')
        self._bar_progress = self.findChild(QtW.QProgressBar, 'bar_progress')
        self._lbl_status = self.findChild(QtW.QLabel, 'lbl_status')

        # ---------------------------------------------------
        #                Function Connections
        # ---------------------------------------------------
        self._btn_clean.clicked.connect(self.clean)

        # ---------------------------------------------------
        #                  Parameter Setup
        # ---------------------------------------------------
        # Label color vars
        self._err = '<font color=#e82309>Error:</font>'
        self._wrn = '<font color=#f7bd0e>Warning:</font>'
        self._grn = '<font color=#3cc103>Status:</font>'

        # Status label modes
        self._status = ['',
                        '[1/4] Building list of objects...',
                        '[2/4] Building list of Parents / Children...',
                        '[3/4] Making Transform Controllers unique...',
                        '[4/4] Cleaning up Parents...',
                        'Done.']
        # Set initial status label
        self._lbl_status.setText(self._status[0])

        # ---------------------------------------------------
        #                   End of Init

    # ---------------------------------------------------
    #                  Private Methods
    # ---------------------------------------------------

    # ---------------------------------------------------
    #                  Public Methods
    # ---------------------------------------------------

    def clean(self):
        rt = self._pymxs.runtime
        selection = []
        parents = []
        children = []

        with self._pymxs.undo(True, 'Clean DWG'), self._pymxs.redraw(False):
            # Build list of selected objects
            self._lbl_status.setText(self._status[1])
            selection = rt.getCurrentSelection()

            # Build Parent / Child lists
            self._lbl_status.setText(self._status[2])
            self._bar_progress.setMaximum(len(selection))
            progress = 0
            self._bar_progress.setValue(progress)
            for obj in selection:
                if rt.classOf(obj) == rt.LinkComposite:
                    parents.append(obj)
                elif rt.classOf(obj.parent) == rt.LinkComposite:
                    children.append(obj)

                progress += 1
                self._bar_progress.setValue(progress)

            # Give each object unique transform controllers
            self._lbl_status.setText(self._status[3])
            progress = 0
            for obj in selection:
                rt.getSubAnim(obj, 3).controller = rt.prs()

                progress += 1
                self._bar_progress.setValue(progress)

            # Unparent children and delete parent objects
            self._lbl_status.setText(self._status[4])
            self._bar_progress.setMaximum(len(children) + len(parents))
            progress = 0
            for child in children:
                child.name = child.parent.name
                child.parent = None

                progress += 1
                self._bar_progress.setValue(progress)

            for parent in parents:
                rt.delete(parent)

                progress += 1
                self._bar_progress.setValue(progress)


            self._lbl_status.setText(self._status[5])
            self._bar_progress.setValue(self._bar_progress.maximum())


# --------------------
#    Dialog Setup
# --------------------

# Path to UI file
_uif = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + "\\cleandwg.ui"
_app = MaxPlus.GetQMaxMainWindow()
ui = cleanDWGUI(_uif, pymxs, _app)

# Punch it
ui.show()

# DEBUG
print "\rTest Version 1"
