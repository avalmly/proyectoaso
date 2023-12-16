#------------------------------------------------------------------------------------------
# Autor: Alberto Valero Mlynaricova
# Fecha: 16/12/2023
#
# Descripción:  script con el siguiente formato:
#                   $ sudo installSamba host5 prueba.com administrator Departamento1!
#
#               Cambiará el nombre de la máquina a host5, instalará todo lo necesario para   
#               disponer de samba, kerberos. Modificará el fichero smb.conf, krb5.conf, 
#               nsswitch. Después unirá la máquina al dominio indicado (prueba.com) con las 
#               credenciales indicadas.
#------------------------------------------------------------------------------------------

import os
import sys
import subprocess
import re                 # Para usar expresiones regulares
#import netifaces
import importlib_metadata # Paquete setuptools
#import winrm   # Paquete: pywinrm
from def_conf_files import hosts_file, resolv_file, krb5_file, samba_file


def pkg_ready(paquetes):
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'    #Hace que el trabaje en modo no interactivo, es decir, que no pedirá confirmaciones
    for paquete in paquetes:
        # Verificar si el paquete está instalado
        resultado = subprocess.run(f"dpkg -l | grep {paquete}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Si no se encuentra ninguna coincidencia, instalar el paquete
        if not resultado.stdout.strip():
            print(f"Instalando {paquete}...")
            #subprocess.run(f"apt install -qq {paquete} > /dev/null", shell=True) # La opción -qq a parte de forzar el sí hace que sea más silencioso con el output
            subprocess.run(f"apt install -y {paquete}", shell=True) # La opción -qq a parte de forzar el sí hace que sea más silencioso con el output

        else:
            print(f"{paquete} ya está instalado.")

def obtener_ip(interfaz):
    try:
        resultado = subprocess.run(['ip', 'a', 'show', interfaz], capture_output=True, text=True)
        
        for linea in resultado.stdout.split('\n'):
            if 'inet' in linea:
                # Obtener la dirección IP de la línea
                ip = linea.split()[1].split('/')[0]
                return ip
            
    except (KeyError, IndexError) as e:
        print(f"No se pudo obtener la IP de la interfaz {interfaz}. Error: {e}")
        return None

"""def info_ad(ip_host): #Obtenemos info del directorio activo con nslookup srv o algo asi para sacar la IP, nombre
    servidores_ad = []

    if ip_host:
        # Bucle para buscar servidores en la red
        red = ".".join(ip_host.split('.')[:3])
        rango_inicio = 1
        rango_fin = 254
        for i in range(rango_inicio, rango_fin + 1):
            ip = f"{red}.{i}"
            try:
                resultado = subprocess.run(["nslookup", ip], capture_output=True, text=True)
                salida = resultado.stdout

                # Buscar la información del servidor DNS en la salida de nslookup
                match_ip = re.search(r"Address:\s+(\S+)", salida)
                match_hostname = re.search(r"Name:\s+(\S+)", salida)

                if match_ip and match_hostname:
                    ip_servidor = match_ip.group(1)
                    hostname_servidor = match_hostname.group(1)
                    servidores_ad.append({'hostname': hostname_servidor, 'ip': ip_servidor})
                    break               # Termina de buscar una

            except Exception as e:
                print(f"Error al ejecutar nslookup para {ip}: {e}")

    return servidores_ad
"""     

paquetes = ["samba", "smbclient", "winbind", "krb5-user", "krb5-config", "realmd", "libpam-winbind", "libnss-winbind"]
pkg_ready(paquetes)

netbios = sys.argv[1]
dominio = sys.argv[2]
usuario = sys.argv[3]
password = sys.argv[4]

rutas_conf = ["/etc/hosts", "/etc/resolv.conf", "/etc/samba/smb.conf", "./smb-default.conf", "/etc/krb5.conf", "./krb5-default.conf", "/etc/nsswitch.conf"]
ip_host = obtener_ip("enp0s3")

# Configuración de ficheros
hosts_file(netbios, dominio, ip_host, rutas_conf[0])
resolv_file(dominio, rutas_conf[1])
samba_file(netbios, dominio, rutas_conf[2], rutas_conf[3])
krb5_file(netbios, dominio, rutas_conf[4], rutas_conf[5])

os.system("systemctl restart smbd nmbd networking")
os.system(f"net ads join -U {usuario}%{password}")
os.system("systemctl restart winbind")