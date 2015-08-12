# -*- mode: ruby -*-
# vi: set ft=ruby :
# wget https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.deb
# dpkg -i vagrant*
# vagrant plugin install vagrant-lxc
# vagrant up

groups = {
  "zabbix-server" => ["zabbix-server"],
  "zabbix-proxy" => ["zabbix-proxy"],
  "consul-master" => ["consul-master"],
  "cdh-worker" => ["cdh-worker"],
  "cdh-master" => ["cdh-master"],
  "cdh-manager" => ["cdh-manager"],
  "cdh-all:children" => ["cdh-master", "cdh-manager", "cdh-worker"],
  "cdh-all-nodes:children" => ["cdh-master", "cdh-worker"]
}

Vagrant.configure(2) do |config|
  if Vagrant.has_plugin?("vagrant-proxyconf")
    config.proxy.http     = "http://proxy-chain.intel.com:911"
    config.proxy.https    = "http://proxy-chain.intel.com:911"
    config.proxy.no_proxy = "intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,127.0.0.0/8,134.134.0.0/16"
  end
  config.vm.box = "fgrehm/centos-6-64-lxc"
  config.vm.box_check_update = false
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y apache2
  # SHELL
  config.vm.provision "ansible" do |ansible|
    ansible.sudo = true
    ansible.groups = groups
    ansible.verbose = "v"
    ansible.playbook = "site.yml"
    ansible.vault_password_file = "Vault"
    ansible.skip_tags = "skip_on_vagrant"
  end

  %w(cdh-manager cdh-worker cdh-master consul-master zabbix-proxy zabbix-web zabbix-server).each do |vmname|
    config.vm.define vmname 
  end
end
