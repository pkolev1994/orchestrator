Summary: Opencode orchestrator for managing docker containers
Name: ocorchestrator
Version: 1.1.1
Release: 14%{?dist}%{?ocrel}
BuildArch: noarch
URL: http://www.opencode.com
License: Commercial
Group: opencode
Source: ocorchestrator-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: petar.kolev@opencode.com
Requires: python36,python36-paramiko, docker-ce, python36-docker, python36-docker-pycreds, ocpytools, python36-cffi, python36-chardet, python36-cryptography, python36-idna, python36-ply, python36-pyasn1,  python36-pycparser, python36-requests, python36u-setuptools, python36-websocket-client


%description
Opencode orchestrator tool for managing containers

GIT commit

Contact: petar.kolev@opencode.com

%prep
%setup -q

%clean
rm -rf $RPM_BUILD_ROOT

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/opt/containers/orchestrator/bin/
mkdir -p $RPM_BUILD_ROOT/opt/containers/orchestrator/etc/
mkdir -p $RPM_BUILD_ROOT/opt/containers/orchestrator/lib/
mkdir -p $RPM_BUILD_ROOT/opt/containers/orchestrator/run/
mkdir -p $RPM_BUILD_ROOT/usr/local/bin/
mkdir -p $RPM_BUILD_ROOT/aux1/ocorchestrator/

cp -fr bin/ lib/ $RPM_BUILD_ROOT/opt/containers/orchestrator/ 


ln -sf /opt/containers/orchestrator/bin/orchestrator_adm $RPM_BUILD_ROOT/usr/local/bin/orchestrator_adm
ln -sf /opt/containers/orchestrator/bin/stats_adm $RPM_BUILD_ROOT/usr/local/bin/stats_adm
ln -sf /opt/containers/orchestrator/bin/list_networks $RPM_BUILD_ROOT/usr/local/bin/list_networks



%files
%defattr(-,root,root)
%dir /opt/containers/orchestrator/
/opt/containers/orchestrator/bin/
/opt/containers/orchestrator/etc/
/opt/containers/orchestrator/lib/
/opt/containers/orchestrator/run/
/aux1/ocorchestrator/

%attr(755,root,root) /usr/local/bin/orchestrator_adm
%attr(755,root,root) /usr/local/bin/stats_adm
%attr(755,root,root) /usr/local/bin/list_networks

%changelog
