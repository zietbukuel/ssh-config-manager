# Maintainer: Juan Timaná <juan@timana.net>
pkgname=ssh-config-manager
pkgver=1.0
pkgrel=1
pkgdesc="A CLI tool to manage SSH config entries"
arch=('any')
url="https://github.com/zietbukuel/ssh-config-manager"
license=('MIT')
depends=('python' 'python-rich' 'python-sshconf-git')
source=("https://github.com/zietbukuel/ssh-config-manager/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

package() {
    # Install the script to /usr/bin
    install -Dm755 "${srcdir}/ssh-config-manager-${pkgver}/ssh_manager.py" "${pkgdir}/usr/bin/ssh-manager"

    # Install the README.md file as documentation
    install -Dm644 "${srcdir}/ssh-config-manager-${pkgver}/README.md" "${pkgdir}/usr/share/doc/${pkgname}/README.md"
}