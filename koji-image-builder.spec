%global forgeurl https://github.com/osbuild/koji-image-builder

Version:        4

%forgemeta

Name:           koji-image-builder
Release:        1%{?dist}
License:        Apache-2.0

URL:            %{forgeurl}

Source0:        %{forgesource}
BuildArch:      noarch

Summary:        Koji integration plugins for image-builder

BuildRequires:  python3-devel
BuildRequires:  python3dist(koji)
BuildRequires:  python3dist(pytest) python3dist(pytest-mock)

%description
Koji integration plugins for image-builder.

%package        hub
Summary:        Koji hub plugin for image-builder integration
Requires:       %{name} = %{version}-%{release}
Requires:       koji-hub koji-hub-plugins
Requires:       python3-jsonschema

%description    hub
Koji hub plugin for image-builder integration.

%package        builder
Summary:        Koji builder plugin for image-builder integration
Requires:       %{name} = %{version}-%{release}
Requires:       koji-builder koji-builder-plugins

%description    builder
Koji builder plugin for image-builder integration.

%package        cli
Summary:        Koji cli plugin for image-cli integration
Requires:       %{name} = %{version}-%{release}
Requires:       koji python3-koji-cli-plugins

%description    cli
Koji cli plugin for image-cli integration.

%prep
%forgesetup

%build
# nothing to do

%check
%pytest test/unit

%install
install -d %{buildroot}/%{_prefix}/lib/koji-hub-plugins
install -p -m 0755 plugin/hub/image_builder.py %{buildroot}/%{_prefix}/lib/koji-hub-plugins/
%py_byte_compile %{python3} %{buildroot}/%{_prefix}/lib/koji-hub-plugins/image_builder.py

install -d %{buildroot}/%{_prefix}/lib/koji-builder-plugins
install -p -m 0755 plugin/builder/image_builder.py %{buildroot}/%{_prefix}/lib/koji-builder-plugins/
%py_byte_compile %{python3} %{buildroot}/%{_prefix}/lib/koji-builder-plugins/image_builder.py

install -d %{buildroot}/%{python3_sitelib}/koji_cli_plugins
install -p -m 0644 plugin/cli/image_builder.py %{buildroot}%{python3_sitelib}/koji_cli_plugins/image_builder.py

%files
%license LICENSE
%doc README.md

%files hub
%{_prefix}/lib/koji-hub-plugins/image_builder.py
%{_prefix}/lib/koji-hub-plugins/__pycache__/image_builder.*

%files builder
%{_prefix}/lib/koji-builder-plugins/image_builder.py
%{_prefix}/lib/koji-builder-plugins/__pycache__/image_builder.*

%files cli
%pycached %{python3_sitelib}/koji_cli_plugins/image_builder.py

%changelog
# the changelog is distribution-specific, therefore there's just one entry
# to make rpmlint happy.

* Mon Mar 17 2025 Simon de Vlieger <supakeen@redhat.com> - 1-1
- On this day, this project was born.
