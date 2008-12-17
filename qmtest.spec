%define name qmtest
%define version 2.4.1
%define release 1
%define py_sitedir %(%{__python} -c "from distutils.sysconfig  import get_python_lib; print get_python_lib()")
%define py_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")
%define url http://www.codesourcery.com/qmtest

Summary: QMTest is an automated software test execution tool
Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
Source0: %{url}/download/%{name}-%{version}.tar.gz
License: GPLv2 and Open Publication
Group: Development/Tools
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Url: %{url}
BuildRequires: python-devel

%description
QMTest is an automated software test execution tool.

%prep

%setup -q -n %{name}-%{version}

%build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
%{_bindir}/*
%{py_sitearch}/*.egg-info
%{py_sitearch}/qm
%{_datadir}/qmtest
%{_docdir}/qmtest
%{_mandir}/man1/*

%changelog
* Tue Dec 16 2008 Stefan Seefeld <stefan@codesourcery.com> 2.4.1-1
- initial package.
