Summary: The CodeSourcery QM (Quality Management) tools.
Name: qm
Version: @version@
Release: @release@
Copyright: Copyright (C) CodeSourcery LLC.
Group: Development/Tools
Source0: qm-@version@.tgz
Url: http://www.codesourcery.com/qm
Provides: qm

%description
QM contains CodeSourcery's testing tool (QMTest) and 
bug-tracking tool (QMTrack).

%prep
%setup

%build
./configure
make

%install
make install

%clean
rm -rf qm-@version@

%files
/usr/local/lib/qm/*
/usr/local/share/qm/*
/usr/local/bin/qmtest
/usr/local/bin/qmtest-remote
/usr/local/bin/qmtrack
/usr/local/share/doc/qm/*
