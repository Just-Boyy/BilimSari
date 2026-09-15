#!/bin/bash
# Oracle Cloud Ubuntu 22.04 VM'ni birinchi marta sozlash uchun.
# Foydalanish: VM'ga SSH orqali ulanib, shu skriptni ishga tushiring:
#   curl -fsSL https://raw.githubusercontent.com/<your-repo>/main/scripts/setup-server.sh | bash
# yoki repo'ni clone qilib, ./scripts/setup-server.sh

set -e

echo "== Docker o'rnatilmoqda =="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
else
    echo "Docker allaqachon o'rnatilgan."
fi

echo "== Oracle Ubuntu image'ning standart iptables qoidalarida 80/443 portlarini ochish =="
sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || \
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || \
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

if command -v netfilter-persistent &> /dev/null; then
    sudo netfilter-persistent save
elif [ -d /etc/iptables ]; then
    sudo sh -c "iptables-save > /etc/iptables/rules.v4"
fi

echo ""
echo "== Tayyor =="
echo "Docker guruhi ta'siri uchun qayta login qiling yoki: newgrp docker"
echo "Eslatma: Oracle Cloud konsolida ham 80 va 443 portlar Security List'da ochilganiga ishonch hosil qiling."
