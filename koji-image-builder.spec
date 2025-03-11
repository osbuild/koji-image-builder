Name:           koji-image-builder
Version:
Release:        %autorelease
Summary:

License:
URL:
Source0:

BuildRequires:
Requires: python3-jsonschema

%description


%prep
%autosetup


%build
%configure
%make_build


%install
%make_install


%check


%files
%license
%doc


%changelog
%autochangelog

