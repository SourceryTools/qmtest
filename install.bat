rem This batch file takes in two arguments. The first is the path to your
rem python. The second is the path that you unzipped the windows files for
rem qm into (essentially, your QM install directory). For example, you 
rem run this file like so:
rem C:\> install.bat C:\PROGRA~1\PYTHON C:\QM
rem It creates the batch files to run qmtrack and qmtest and places them
rem in the bin directory. These batch files set the QM_INSTALL_PATH that
rem is used by setup_path.py to find the files associated with the
rem installation.

@echo off
echo set QM_INSTALL_PATH=%2 > BIN\QMTRACK.BAT
echo %1\PYTHON.EXE %2\BIN\QMTRACK %%1 %%2 %%3 %%4 %%5 %%6 %%7 %%8 %%9 >> BIN\QMTRACK.BAT
echo set QM_INSTALL_PATH=%2 > BIN\QMTEST.BAT
echo %1\PYTHON.EXE %2\BIN\QMTRACK %%1 %%2 %%3 %%4 %%5 %%6 %%7 %%8 %%9 >> BIN\QMTEST.BAT
