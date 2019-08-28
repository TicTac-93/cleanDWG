# ----------------------
#   Clean DWG - v1.2.0
# ----------------------

# Cleans up CAD imports by removing Block/Style Parent objects and converting CAD objects into Editable Meshes,
# while preserving transforms and instancing.

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
import traceback


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

        self._window_title = 'Clean DWG v1.2.0'
        self.setWindowTitle(self._window_title)

        # ---------------------------------------------------
        #                   Widget Setup
        # ---------------------------------------------------

        self._chk_layer = self.findChild(QtW.QCheckBox, 'chk_layer')
        self._chk_expand = self.findChild(QtW.QCheckBox, 'chk_expand')
        self._chk_full_scene = self.findChild(QtW.QCheckBox, 'chk_fullScene')

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
                        '[1/5] Building list of objects...',
                        '[2/5] Building list of Parents / Children...',
                        '[3/5] Making Transform Controllers unique...',
                        '[4/5] Converting CAD Objects to Meshes...',
                        '[5/5] Cleaning up Parents...',
                        'Waiting for 3ds Max to un-freeze...',
                        'Done.',
                        '%s Cleanup failed!  Check the Max Listener for details.' % self._err]
        # Set initial status label
        self._lbl_status.setText(self._status[0])

        # ---------------------------------------------------
        #                   End of Init

    # ---------------------------------------------------
    #                  Private Methods
    # ---------------------------------------------------
    def _get_children(self, obj, input_list):
        children = obj.children
        for child in children:
            # Note that since we're calling this from a list of unique hierarchy roots, we don't have to worry about
            # checking for duplicate objects.  Crawling down the trees will only yield each object one time.
            input_list.append(child)
            input_list = self._get_children(child, input_list)
        return input_list

    # ---------------------------------------------------
    #                  Public Methods
    # ---------------------------------------------------
    def clean(self):
        # UI Options
        layer = self._chk_layer.isChecked()
        expand = self._chk_expand.isChecked()
        scene = self._chk_full_scene.isChecked()

        # Misc Variables
        rt = self._pymxs.runtime

        # Run 3ds Max garbage cleanup before we start.  This will wipe the Undo/Redo cache, too.
        # Clearing the Undo cache prevents Max from hanging up when the script is used multiple times.
        rt.gc()

        with self._pymxs.undo(True, 'Clean DWG'), self._pymxs.redraw(False):
            try:
                # 1/5
                # Build list of selected objects, optionally including their entire hierarchy.
                self._lbl_status.setText(self._status[1])
                selection = rt.getCurrentSelection()
                rt.clearSelection()

                # Clean up selected objects ONLY
                if not expand and not scene:
                    pass

                # Expand selection to the full hierarchy of the selected objects
                elif expand and not scene:
                    # Expand up to roots of selected objects
                    selection_roots = []
                    self._bar_progress.setMaximum(len(selection)*2)
                    self._bar_progress.setValue(0)
                    progress = 0
                    for x in selection:
                        progress += 1
                        x_root = x
                        x_parent = x.parent
                        while x_parent is not None:
                            x_root = x_parent
                            x_parent = x_root.parent
                        if x_root not in selection_roots:
                            selection_roots.append(x_root)

                        self._bar_progress.setValue(progress)

                    # Expand down to children of roots
                    selection_ex = list(selection_roots)  # the list(...) format prevents us passing by reference
                    progress = len(selection_roots)
                    self._bar_progress.setMaximum(progress*2)
                    self._bar_progress.setValue(progress)
                    for x in selection_roots:
                        progress += 1
                        selection_ex = self._get_children(x, selection_ex)
                        self._bar_progress.setValue(progress)

                    selection = list(selection_ex)

                # Expand selection to entire scene
                elif scene:
                    selection = rt.objects

                # Something fishy's going on...
                else:
                    self._lbl_status.setText(self._status[6])
                    print "Unknown error, please re-run the Clean DWG script."
                    return

                # 2/5
                # Build Parent / Child lists
                self._lbl_status.setText(self._status[2])
                self._bar_progress.setMaximum(len(selection))
                self._bar_progress.setValue(0)
                progress = 0

                parents = []
                children = []
                for obj in selection:
                    # By converting the objects into strings, we can inspect otherwise inaccessible information.
                    # Specifically, the beginning of the string provides the object type
                    if str(obj)[:19] == "$Block_Style_Parent":
                        parents.append(obj)
                    elif str(obj.parent)[:19] == "$Block_Style_Parent":
                        children.append(obj)

                    progress += 1
                    self._bar_progress.setValue(progress)

                # 3/5
                # Give each object unique transform controllers
                self._lbl_status.setText(self._status[3])
                progress = 0
                for obj in selection:
                    # in pymxs, obj.controller is the same as MAXScript obj.transform.controller
                    # More confusingly, this seems to be the only way to actually set a new controller in pymxs without
                    # using rt.refs.replaceReference()
                    obj.controller = rt.prs()

                    progress += 1
                    self._bar_progress.setValue(progress)

                # 4/5
                # Convert all VIZBlocks and Linked Geometry to Edit Meshes, preserve instancing
                self._lbl_status.setText(self._status[4])
                self._bar_progress.setMaximum(len(selection))
                self._bar_progress.setValue(0)
                progress = 0

                cad_objs = 0
                for obj in selection:
                    # Similarly to parent/child detection, we'll search for CAD objects that need conversion
                    obj_s = str(obj)
                    if obj_s[:9] == "$VIZBlock" or obj_s[:16] == "$Linked_Geometry":
                        rt.addModifier(obj, rt.Edit_Mesh())
                        rt.maxOps.CollapseNodeTo(obj, 1, True)
                        cad_objs += 1

                    # DEBUG
                    # elif obj_s[:14] != "$Editable_Mesh" and obj_s[:19] != "$Block_Style_Parent":
                    #     print obj_s

                    progress += 1
                    self._bar_progress.setValue(progress)

                # 5/5
                # Unparent children, then delete old parents.  Optionally move children to current layer.
                self._lbl_status.setText(self._status[5])
                if layer:
                    self._bar_progress.setMaximum(len(children)*2)
                else:
                    self._bar_progress.setMaximum(len(children))
                progress = 0
                for child in children:
                    child.name = child.parent.name
                    child.parent = None

                    progress += 1
                    self._bar_progress.setValue(progress)

                if layer:
                    # Convert the full selection and list of parents to sets, so we can exclude parents from the for-loop
                    set_selection = set(selection)
                    set_parents = set(parents)
                    set_selection = set_selection.difference(set_parents)
                    current_layer = rt.LayerManager.current

                    progress = len(set_selection)
                    self._bar_progress.setMaximum(progress*2)
                    self._bar_progress.setValue(progress)
                    for x in set_selection:
                        progress += 1
                        current_layer.addNode(x)

                        self._bar_progress.setValue(progress)

                rt.delete(parents)

                # Done.
                self._lbl_status.setText(self._status[6])
                self._bar_progress.setMaximum(1)
                self._bar_progress.setValue(1)

                # Print some info
                print "Cleaned up %d Block/Style Parents" % len(parents)
                print "Converted %d CAD Objects into Meshes" % cad_objs

            except Exception:
                traceback.print_exc()
                self._lbl_status.setText(self._status[8])
                self._bar_progress.setMaximum(100)
                self._bar_progress.setValue(0)

                return

        # This should run after Max un-freezes
        self._lbl_status.setText(self._status[7])

        return


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
# print "\rTest Version 7"
