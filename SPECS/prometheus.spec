Name:           prometheus
Version:        %{pkg_version}
Release:        %{rpm_release}%{?dist}
Summary:        The Prometheus monitoring system and time series database.
License:        ASL 2.0
URL:            https://prometheus.io

Source0:        %{name}-%{pkg_version}.linux-amd64.tar.gz
Source1:        %{name}.service
Source2:        logrotate.conf
Source3:        rsyslog.conf
Source4:        environment.conf
Source5:        %{name}.yml

BuildRoot:      %{buildroot}
BuildArch:      x86_64
BuildRequires:  systemd-units
Requires:       systemd, logrotate, rsyslog > 7.2
Requires(pre):  shadow-utils

%description

Prometheus is a systems and service monitoring system. It collects metrics from
configured targets at given intervals, evaluates rule expressions, displays the
results, and can trigger alerts if some condition is observed to be true.

%prep
%setup -q -n %{name}-%{version}.linux-amd64

%install
# Data storage directory
# Rationale: http://www.pathname.com/fhs/pub/fhs-2.3.html#SRVDATAFORSERVICESPROVIDEDBYSYSTEM
mkdir -p %{buildroot}/srv/%{name}

# Home directory of the user
mkdir -p %{buildroot}/home/%{name}

# Directory for storing log files.
mkdir -p %{buildroot}/%{_localstatedir}/log/%{name}

# Logrotate config
mkdir -p %{buildroot}/%{_sysconfdir}/logrotate.d/
install -m 644 %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}.conf

# RSyslog config to enable writing to a file.
mkdir -p %{buildroot}/%{_sysconfdir}/rsyslog.d/
install -m 644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/rsyslog.d/%{name}.conf

# SystemD unit definition and environment settings to go alongside unit file.
mkdir -p %{buildroot}/%{_unitdir}/%{name}.service.d
install -m 644 %{SOURCE1} %{buildroot}/%{_unitdir}/%{name}.service
install -m 644 %{SOURCE4} %{buildroot}/%{_unitdir}/%{name}.service.d/environment.conf

# Binaries
mkdir -p %{buildroot}/%{_bindir}
install -m 755 prometheus %{buildroot}/%{_bindir}/prometheus
install -m 755 promtool %{buildroot}/%{_bindir}/promtool

# Web UI directories and files
mkdir -p %{buildroot}/usr/share/prometheus/console_libraries
mkdir -p %{buildroot}/usr/share/prometheus/consoles
for dir in console_libraries consoles; do
  for file in ${dir}/*; do
    install -m 644 ${file} %{buildroot}/usr/share/prometheus/${file}
  done
done
# Copy over License and notice too
install -m 644 LICENSE %{buildroot}/usr/share/prometheus/LICENSE
install -m 644 NOTICE %{buildroot}/usr/share/prometheus/NOTICE

# Configuration file
mkdir -p %{buildroot}/%{_sysconfdir}/%{name}
install -m 644 %{SOURCE5} %{buildroot}/%{_sysconfdir}/%{name}/%{name}.yml

%pre
getent group prometheus >/dev/null || groupadd -r prometheus
getent passwd prometheus >/dev/null || \
  useradd -r -g prometheus -d /home/%{name} -s /sbin/nologin \
          -c "Prometheus services" prometheus

%post
%systemd_post %{name}.service

echo
echo "NOTES ############################################################################"
echo "Please restart RSyslog so that logs are written to %{_localstatedir}/log/%{name}:"
echo "    systemctl restart rsyslog.service"
echo "To have %{name} start automatically on boot:"
echo "    systemctl enable %{name}.service"
echo "Start %{name}:"
echo "    systemctl daemon-reload"
echo "    systemctl start %{name}.service"
echo "##################################################################################"
echo

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service

%files
%defattr(-,prometheus,prometheus,-)
%attr(755, root, root) %{_bindir}/prometheus
%attr(755, root, root) %{_bindir}/promtool
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.yml
%config(noreplace) %attr(644, root, root) %{_sysconfdir}/logrotate.d/%{name}.conf
%config(noreplace) %attr(644, root, root) %{_sysconfdir}/rsyslog.d/%{name}.conf
%config(noreplace) %{_unitdir}/%{name}.service
%config(noreplace) %{_unitdir}/%{name}.service.d/environment.conf
# Log directory
%dir %attr(755, prometheus, prometheus) %{_localstatedir}/log/%{name}
%dir %attr(700, prometheus, prometheus) /home/%{name}

/srv/%{name}
/usr/share/prometheus
/usr/share/prometheus/NOTICE
/usr/share/prometheus/LICENSE
