# Clean DWG
A 3dsMax script that will clean up `Block/Style Parent` dummy objects in imported DWGs.

Install by copying the cleanDWG folder to your 3ds Max scripts directory.
Run in 3ds Max using with the MaxScript snippet:
`python.ExecuteFile @"C:\path\to\cleanDWG\cleanDWG.py"`

-----

This script will operate only on selected objects.  In the future, 
I'd like to expand it to search for relatives (parents and children) of
the current selection, but for now you ***must make sure*** that you have
all objects in a hierarchy selected.  The recommended way to do this is
by selecting top-level objects in the `Scene Explorer`, and then using the
`Select Children` option.

To use, run the script and then select the objects (remember, Parents *and* Children,)
that you want to clean up.  Then, simply press the `Clean Block Parents`.
Depending on the number of objects you have selected this may take a while,
but should be fairly fast for selections with less than 10,000 objects.
This operation *is* undoable, but don't be surprised if Max hangs up while
undoing / redoing.

In this release, the script will not delete the old `Block/Style Parent`
objects, and instead sort them into a layer.  After that, it's
up to the user to delete them.  This will likely be changed in a future
release.