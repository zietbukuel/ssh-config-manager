# Maintainer: Juan Timaná <juan@timana.net>
pkgname=ssh-config-manager
pkgver=2.0.0
pkgrel=1
pkgdesc="Modern CLI tool to manage SSH config entries with safety, validation, and Include support"
arch=('any')
url="https://github.com/zietbukuel/ssh-config-manager"
license=('MIT')
depends=('python' 'python-rich' 'python-sshconf')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
optdepends=(
    'python-argcomplete: shell completion support'
    'pipx: isolated installation (recommended)'
)
source=("$pkgname-$pkgver.tar.gz::https://github.com/zietbukuel/ssh-config-manager/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')  # Replace with actual sha256sum when tagging release

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Install documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}

# vim:set ts=2 sw=2 et: