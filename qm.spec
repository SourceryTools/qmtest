Summary: The Software Carpentry QM (Quality Management) tool suite.
Name: qm
Version: @version@
Release: @release@
Copyright: Copyright (C) CodeSourcery LLC.
Group: Development/Tools
Source0: qm-@version@.tgz
Url: http://www.software-carpentry.com
Provides: qm

%description
QM is a suite of support tools for software developers produced by the
Software Carpentry project.  The suite includes a software testing tool
(QMTest) and a bug-tracking tool (QMTrack).

%prep
%setup

%build
./configure
make setup
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
