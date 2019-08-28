# Clean DWG
##### v1.2.0

A 3dsMax script that will clean up `Block/Style Parent` dummy objects in imported DWGs and
convert 'VIZBlock' and 'Linked Geometry' objects into Editable Meshes, preserving instances.

Install by copying the cleanDWG folder to your 3ds Max scripts directory.
Run in 3ds Max using with the MaxScript snippet:
`python.ExecuteFile @"C:\path\to\cleanDWG\cleanDWG.py"`

-----

**Please note that while this operation *is* undoable, to prevent freezing
it flushes the undo cache just before running.  You will not be able
to undo previous work after cleaning up.**

This script operates on selected objects, optionally expanding that selection to include
their entire hierarchy of parents, children, etc.  You may also choose to run the script
on every object in the scene, which in the case of large numbers of objects can be faster
than trying to expand a selection.  While the script doesn't enforce this, it's
recommended that you select entire object hierarchies, rather than individual objects.

To use, run the script, select any options you want, select the objects
that you want to clean up, and then press the `Clean Block/Style Parents` button.
Depending on the number of objects you have selected this may take a while,
but should be fairly fast for selections with less than 10,000 objects.
Note that the "Expand Selection" option will greatly slow down the script
when large numbers of object are selected.