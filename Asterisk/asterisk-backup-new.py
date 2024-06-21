import os
import ftplib
import paramiko
import socket

def get_remote_hostname(ssh):
    #--- Функция для получения имени хоста удаленного сервера
    #--- Function to retrieve the hostname of the remote server
    stdin, stdout, stderr = ssh.exec_command('hostname')
    return stdout.read().strip()

def upload_file(ftp, file_path):
    #--- Функция для загрузки файла на FTP-сервер
    #--- Function for uploading a file to an FTP server
    with open(file_path, 'rb') as fh:
        ftp.storbinary('STOR %s' % os.path.basename(file_path), fh)

def main():
    #--- Учетные данные FTP-сервера
    #--- FTP server credentials
    ftp_server = 'ip-address'
    ftp_username = 'login'
    ftp_password = 'password'


    #--- Чтение учетных данных SSH из файла
    #--- Reading SSH credentials from a file
    login_file = '/enter_directory/login'
    with open(login_file) as f:
        lines = f.readlines()
        ssh_username = lines[0].strip()
        ssh_password = lines[1].strip()

    #--- Чтение списка хостов из файла
    #--- Reading a list of hosts from a file
    hosts_file = '/enter_directory/hosts'
    with open(hosts_file) as f:
        remote_servers = [line.split('#')[0].strip() for line in f if line.strip() and not line.strip().startswith('#')]

    #--- Файлы на удаленных серверах для копирования
    #--- Files on remote servers for copying
    remote_files = ['/etc/asterisk/sip.conf',
                    '/etc/asterisk/extensions.conf']

    #--- Подключение к FTP-серверу
    #--- Connecting to an FTP server
    ftp_connection = ftplib.FTP(ftp_server, ftp_username, ftp_password)

    #--- Подключение по SSH и копирование файлов
    #--- SSH connection and file copying
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        for server in remote_servers:
            try:
                #--- Подключение по SSH
                #--- SSH connection
                ssh.connect(server, username=ssh_username, password=ssh_password)
            except paramiko.ssh_exception.SSHException as e:
                print(f"Error connecting to {server} via SSH: {e}")
                continue
            except socket.timeout as e:
                print(f"Connection timeout to {server} expired: {e}")
                continue
            
            #--- Успешное подключение по SSH, с продолжаем копирования файлов
            #--- Successful SSH connection, proceeding with file copying
            hostname = get_remote_hostname(ssh).decode('utf-8')
            print(f"Hostname of the server {server}: {hostname}")
            for remote_file in remote_files:
                #--- Цикл по каждому удаленному файлу и его копирование с каждого сервера
                #--- Loop through each remote file and copy it from each server
                try:
                    sftp = ssh.open_sftp()
                    sftp.get(remote_file, os.path.basename(remote_file))
                    sftp.close()
                    
                    #--- Создание каталога на FTP-сервере, если его нет
                    #--- Creating a directory on the FTP server if it does not exist
                    ftp_remote_dir = f'/enter_directory/{hostname}/'
                    try:
                        ftp_connection.mkd(ftp_remote_dir)
                    except ftplib.error_perm:
                        pass  #--- Каталог уже существует The directory already exists
                    
                    #--- Подключение обратно к FTP для загрузки файла
                    #--- Connecting back to FTP for file upload
                    ftp_connection.cwd(ftp_remote_dir)
                    upload_file(ftp_connection, os.path.basename(remote_file))
                    os.remove(os.path.basename(remote_file))
                except (paramiko.ssh_exception.SSHException, IOError, OSError, ftplib.error_perm) as e:
                    print(f"Error copying file {remote_file} from {server}: {e}")
                    continue  # Продолжаем копирование следующего файла в случае ошибки Continuing copying the next file in case of an error
    finally:
        ftp_connection.quit()

if __name__ == "__main__":
    main()

