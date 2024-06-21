from netmiko import ConnectHandler

def read_credentials_from_file(filename):
    with open(filename) as f:
        return f.readline().strip(), f.readline().strip()

def read_hosts_from_file(filename):
    with open(filename) as f:
        return [line.strip() for line in f.readlines()]

#--- файл с логином и паролем от коммутатора
#--- File containing login and password for the switch
login_file = "/Enter-directory/login"

#--- файл со списком ip адресов коммутаторов
#--- File with a list of switch IP addresses
hosts_file = "/Enter-directory/hosts"

username, password = read_credentials_from_file(login_file)
hosts = read_hosts_from_file(hosts_file)

for host in hosts:
    try:
        #--- ip адрес и учетные данные коммутатора подставляются из файлов "login" и "hosts"
        #--- IP address and credentials of the switch are sourced from the 'login' and 'hosts' files
        device = {
            'device_type': 'aruba_procurve',
            'ip': host,
            'username': username,
            'password': password
        }

        #--- Подключение к коммутатору по ssh
        #--- SSH connection to the switch
        with ConnectHandler(**device) as ssh:

            #--- Проверка наличия VLAN, для примера 100
            #--- Checking the existence of VLAN, for example, VLAN 100
            vlan_check = ssh.send_command("show run vlan 100")

            #--- Создание VLAN 100 если его нет на коммутаторе
            #--- Creating VLAN 100 if it does not exist on the switch
            if "VLAN configuration is not available" in vlan_check:
                ssh.send_config_set(["vlan 100", "name 100"])
                print(f"VLAN 100 has been created on the switch {host}")
            else:
                print(f"VLAN 100 already exists on switch {host}")
                continue

            #--- Отправка команды на устройство и получение вывода
            #--- Sending a command to the device and receiving the output
            vlan_config = ssh.send_command("show run vlan 200")

            #--- Разбиение вывода на строки и поиск строки с tagged портами
            #--- Splitting the output into lines and searching for lines with tagged ports
            for line in vlan_config.splitlines():
                if "tagged" in line:
                    #--- Получение списка портов из строки
                    #--- Extracting a list of ports from a string
                    ports = line.split("tagged")[1].strip().split(",")
                    #--- Обработка и применение команды к каждому порту
                    #--- Processing and applying the command to each port
                    for port in ports:
                        if "-" in port:
                            start, end = port.split("-")
                            for p in range(int(start), int(end)+1):
                                output_config = ssh.send_config_set([f"interface {p}", "tagged vlan 100"])
                                print(f"The port {p} is configured on host {host}")
                        else:
                            output_config = ssh.send_config_set([f"interface {port}", "tagged vlan 100"])
                            print(f"The port {port} is configured on host {host}")
    except Exception as e:
        print(f"Failed to connect to the switch {host}: {e}")
        continue  # Moving on to the next switch from the list

