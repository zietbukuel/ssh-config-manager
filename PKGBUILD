# Maintainer: Juan Timaná <juan@timana.net>
pkgname=ssh-config-manager
pkgver=2.0.0
pkgrel=1
pkgdesc="Modern CLI tool to manage SSH config entries with safety, validation, and Include support"
arch=('any')
url="https://github.com/zietbukuel/ssh-config-manager"
license=('MIT')
depends=('python' 'python-rich' 'python-sshconf-git')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
optdepends=(
    'python-argcomplete: shell completion support'
    'python-pipx: recommended for isolated installation'
)

build() {
    cd "$startdir"
    python -m build --wheel --no-isolation --outdir "$srcdir"
}

package() {
    python -m installer --destdir="$pkgdir" "$srcdir"/*.whl
    
    # Install license
    install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Install documentation
    install -Dm644 "$startdir/README.md" "$pkgdir/usr/share/doc/$pkgname/README.md"
}

# vim:set ts=2 sw=2 et: