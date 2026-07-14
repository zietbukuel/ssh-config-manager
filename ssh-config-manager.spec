Name:           ssh-config-manager
Version:        2.0.0
Release:        1%{?dist}
Summary:        Modern CLI tool to manage SSH config entries with safety and validation

License:        MIT
URL:            https://github.com/zietbukuel/ssh-config-manager
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  python3-build
BuildRequires:  python3-installer
BuildRequires:  python3-pytest
Requires:       python3-rich
Requires:       python3-sshconf
Recommends:     python3-argcomplete

%description
SSH Config Manager is a modern CLI tool built with Python to simplify the
management of your SSH configuration file (~/.ssh/config).

Features:
* Add, list, search, edit, and delete SSH entries
* Automatic timestamped backups before writes
* Hostname/IP, port, and identity file validation
* Include directive support (~/.ssh/config.d/)
* Shell completion (Bash, Zsh, Fish)
* Rich formatted output
* Modern Python packaging (pyproject.toml)
* Comprehensive test suite

%prep
%autosetup -n %{name}-%{version}

%build
python3 -m build --wheel --no-isolation

%install
python3 -m installer --destdir=%{buildroot} dist/*.whl

%check
pytest tests/ -v

%files
%license LICENSE
%doc README.md
%{_bindir}/ssh-manager
%{python3_sitelib}/ssh_config_manager-*.dist-info/

%changelog
* Mon Jul 06 2026 Juan Timaná <juan@timana.net> - 2.0.0-1
- New upstream release v2.0.0
- Modernized packaging with pyproject.toml
- Added automatic backup functionality
- Added input validation (hostname, port, identity file)
- Added Include directive support (~/.ssh/config.d/)
- Added shell completion (Bash, Zsh, Fish)
- Comprehensive test suite (40 tests)