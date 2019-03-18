Summary: Opencode orchestrator for managing docker containers
Name: ocorchestrator
Version: 1.1.1
Release: 5%{?dist}%{?ocrel}
BuildArch: noarch
URL: http://www.opencode.com
License: Commercial
Group: opencode
Source: ocorchestrator-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: petar.kolev@opencode.com
Requires: python34, python34-paramiko, docker-ce, python34-docker, python34-docker-pycreds, ocpytools, python34-cffi, python34-chardet, python34-cryptography, python34-idna, python34-ply, python34-pyasn1,  python34-pycparser, python34-requests, python34-setuptools, python34-websocket-client


%description
Opencode orchestrator for managing containers

GIT commit

Contact: petar.kolev@opencode.com

%prep
%setup -q

%clean
rm -rf $RPM_BUILD_ROOT

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/aux0/customer/containers/orchestrator/bin/
mkdir -p $RPM_BUILD_ROOT/aux0/customer/containers/orchestrator/etc/
mkdir -p $RPM_BUILD_ROOT/aux0/customer/containers/orchestrator/lib/
mkdir -p $RPM_BUILD_ROOT/aux0/customer/containers/orchestrator/run/
mkdir -p $RPM_BUILD_ROOT/usr/local/bin/
mkdir -p $RPM_BUILD_ROOT/aux1/ocorchestrator/

cp -fr bin/ lib/ $RPM_BUILD_ROOT/aux0/customer/containers/orchestrator/ 


ln -sf /aux0/customer/containers/orchestrator/bin/orchestrator_adm $RPM_BUILD_ROOT/usr/local/bin/orchestrator_adm
ln -sf /aux0/customer/containers/orchestrator/bin/stats_adm $RPM_BUILD_ROOT/usr/local/bin/stats_adm
ln -sf /aux0/customer/containers/orchestrator/bin/list_networks $RPM_BUILD_ROOT/usr/local/bin/list_networks



%files
%defattr(-,root,root)
%dir /aux0/customer/containers/orchestrator/
/aux0/customer/containers/orchestrator/bin/
/aux0/customer/containers/orchestrator/etc/
/aux0/customer/containers/orchestrator/lib/
/aux0/customer/containers/orchestrator/run/
/aux1/ocorchestrator/

%attr(755,root,root) /usr/local/bin/orchestrator_adm
%attr(755,root,root) /usr/local/bin/stats_adm
%attr(755,root,root) /usr/local/bin/list_networks

%changelog
